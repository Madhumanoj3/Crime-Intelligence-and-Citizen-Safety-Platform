"""
Build the clean Madurai location datasets.

Inputs:
    ml/dataset/export.geojson   OpenStreetMap export (Overpass Turbo) for Madurai district
    firstapp/templates/firstapp/dataset/madurai_police_stations (1).csv   police stations and offices
    firstapp/templates/firstapp/dataset/madurai_locations.csv             old list, only used to report what is missing

Outputs (firstapp/templates/firstapp/dataset/):
    madurai_areas.csv                 towns, suburbs, neighbourhoods, villages  (what the citizen picks as "area").
                                      Verified=Yes: coordinates from OpenStreetMap. Verified=No: from the old list
                                      (rounded to 2 decimals), kept so older complaints and users still match.
    madurai_landmarks.csv             hospitals, schools, temples, bus stops...  (what the citizen picks as "nearby landmark")
    madurai_police_stations_clean.csv police stations and offices, with the area each one is in
    madurai_areas_to_verify.csv       what happened to every name from the old list (added, or skipped and why)

Every landmark and police station carries the nearest area and the distance to it.

Usage (from the project folder):
    .venv\\Scripts\\python.exe ml\\build_locations_dataset.py
"""
import csv
import difflib
import json
import math
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'firstapp', 'templates', 'firstapp', 'dataset')
GEOJSON = os.path.join(BASE, 'ml', 'dataset', 'export.geojson')
POLICE_CSV = os.path.join(DATA_DIR, 'madurai_police_stations (1).csv')
OLD_LOCATIONS_CSV = os.path.join(DATA_DIR, 'madurai_locations.csv')

TAMIL = re.compile(r'[஀-௿]')

# OSM place=* values kept as areas -> label used in the dataset
AREA_TYPES = {'city': 'City', 'town': 'Town', 'suburb': 'Suburb', 'neighbourhood': 'Neighbourhood',
              'village': 'Village', 'hamlet': 'Hamlet'}

# Which OSM objects count as landmarks a citizen can name. Edit here to add or remove kinds.
# Each rule: (OSM key, value, landmark type)
LANDMARK_RULES = [
    ('amenity', 'hospital', 'Hospital'),
    ('amenity', 'school', 'School'),
    ('amenity', 'college', 'College'),
    ('amenity', 'university', 'College'),
    ('amenity', 'bus_station', 'Bus Stand'),
    ('highway', 'bus_stop', 'Bus Stop'),
    ('railway', 'station', 'Railway Station'),
    ('aeroway', 'aerodrome', 'Airport'),
    ('amenity', 'courthouse', 'Court'),
    ('amenity', 'townhall', 'Government Office'),
    ('amenity', 'fire_station', 'Fire Station'),
    ('amenity', 'post_office', 'Post Office'),
    ('amenity', 'bank', 'Bank'),
    ('amenity', 'fuel', 'Fuel Station'),
    ('amenity', 'marketplace', 'Market'),
    ('amenity', 'cinema', 'Theatre'),
    ('amenity', 'theatre', 'Theatre'),
    ('amenity', 'community_centre', 'Community Hall'),
    ('amenity', 'library', 'Library'),
    ('shop', 'mall', 'Mall'),
    ('shop', 'department_store', 'Mall'),
    ('tourism', 'hotel', 'Hotel'),
    ('tourism', 'attraction', 'Tourist Place'),
    ('tourism', 'museum', 'Tourist Place'),
    ('tourism', 'theme_park', 'Tourist Place'),
]
WORSHIP = {'hindu': 'Temple', 'muslim': 'Mosque', 'christian': 'Church'}

# Dropped even though they match a rule above
SKIP_NAMES = re.compile(r'shelter', re.I)


def km(a, b):
    return math.hypot((a['lat'] - b['lat']) * 111.0, (a['lon'] - b['lon']) * 109.5)


def tidy(name):
    name = re.sub(r'\s+', ' ', name).strip()
    name = re.sub(r',(?=\S)', ', ', name)
    name = re.sub(r'\s+,', ',', name)
    name = re.sub(r'\s*[,-]\s*Madurai$', '', name, flags=re.I)  # the city is not part of a name
    return name


def english_name(p):
    """The OSM `name`, or the English tag when `name` is Tamil script."""
    name = (p.get('name') or '').strip()
    if TAMIL.search(name) or not name:
        name = (p.get('name:en') or name).strip()
    return tidy(name)


def load_points():
    out = []
    for f in json.load(open(GEOJSON, encoding='utf-8'))['features']:
        if f['geometry']['type'] != 'Point':
            continue
        lon, lat = f['geometry']['coordinates'][:2]
        p = dict(f['properties'])
        p['lat'], p['lon'] = lat, lon
        out.append(p)
    return out


def landmark_type(p):
    if p.get('amenity') == 'place_of_worship':
        return WORSHIP.get(p.get('religion'), 'Place of Worship')
    for key, value, label in LANDMARK_RULES:
        if p.get(key) == value:
            return label
    return ''


def norm(name):
    return re.sub(r'[^a-z0-9஀-௿]', '', name.lower())


def hospital_key(name):
    return norm(re.sub(r'\b(hospitals?|madurai|pvt|ltd|and|the)\b', '', name.lower()))


def write_csv(path, header, rows):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main():
    points = load_points()
    log = {'areas_renamed': [], 'landmarks_dropped': {}, 'landmarks_merged': []}

    # ---- Areas --------------------------------------------------------------
    areas = []
    for p in points:
        if p.get('place') in AREA_TYPES and (p.get('name') or p.get('name:en')):
            name = english_name(p)
            if name:
                areas.append({'name': name, 'type': AREA_TYPES[p['place']], 'lat': p['lat'], 'lon': p['lon'],
                              'osm_id': p.get('@id', ''), 'notes': ''})
    # Two different villages can share a name: add the nearest differently named place to tell them apart
    by_name = {}
    for a in areas:
        by_name.setdefault(a['name'].lower(), []).append(a)
    for group in by_name.values():
        if len(group) > 1:
            plain = [x['name'] for x in areas]  # original names, so a suffix never points at another suffixed name
            for a in group:
                near = min((x for x in areas if x['name'].lower() != a['name'].lower() and x['name'] in plain),
                           key=lambda x: km(a, x))
                a['name'] = f"{a['name']} (near {near['name']})"
                a['notes'] = 'same name as another place, so the nearest place was added'
                log['areas_renamed'].append(a['name'])
    seen_names = {}
    for a in areas:  # the nearest place can be the same for both, so number what is still repeated
        seen_names[a['name'].lower()] = seen_names.get(a['name'].lower(), 0) + 1
        if seen_names[a['name'].lower()] > 1:
            a['name'] += f" #{seen_names[a['name'].lower()]}"
    areas.sort(key=lambda a: (a['type'] != 'City', a['name'].lower()))
    for i, a in enumerate(areas, 1):
        a['id'] = f'AREA-{i:03d}'

    def nearest_area(item):
        a = min(areas, key=lambda x: km(x, item))
        return a['name'], km(a, item)

    # ---- Landmarks ----------------------------------------------------------
    cands = []
    for p in points:
        if p.get('place') or p.get('amenity') == 'police':
            continue  # areas are handled above, police comes from the police CSV
        ltype = landmark_type(p)
        if not ltype:
            continue
        name = english_name(p)
        if not name or SKIP_NAMES.search(name):
            reason = 'no name' if not name else 'not a useful landmark'
            log['landmarks_dropped'][reason] = log['landmarks_dropped'].get(reason, 0) + 1
            continue
        cands.append({'name': name, 'type': ltype, 'lat': p['lat'], 'lon': p['lon'],
                      'address': p.get('addr:full') or p.get('addr:street') or '', 'osm_id': p.get('@id', ''),
                      'notes': 'only has a Tamil name in OpenStreetMap' if TAMIL.search(name) else ''})

    kept = []
    for c in cands:
        dup = None
        for k in kept:
            if k['type'] != c['type']:
                continue
            d = km(k, c)
            if c['type'] == 'Hospital':
                a, b = hospital_key(k['name']), hospital_key(c['name'])
                contained = a in b or b in a
                similar = contained and min(len(a), len(b)) / max(len(a), len(b)) >= 0.75
                same = (d < 0.25 and (a == b or similar)) or (d < 0.06 and contained)
            elif c['type'] == 'Court':
                same = d < 0.5
            elif c['type'] in ('Bus Stand', 'Railway Station'):
                same = d < 0.15
            else:
                same = d < 0.15 and norm(k['name']) == norm(c['name'])
            if same:
                dup = k
                break
        if dup:
            log['landmarks_merged'].append(f"{c['name']} -> {dup['name']}")
        else:
            kept.append(c)

    # unique names (the same shop or bus stop name can appear in many places)
    counts = {}
    for k in kept:
        counts[k['name'].lower()] = counts.get(k['name'].lower(), 0) + 1
    for k in kept:
        k['area'], k['dist'] = nearest_area(k)
        if counts[k['name'].lower()] > 1:
            k['name'] = f"{k['name']} ({k['area']})"
            k['notes'] = 'same name as another landmark, so the area was added'
    seen = {}
    for k in sorted(kept, key=lambda r: (r['type'], r['name'].lower())):
        key = k['name'].lower()
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 1:
            k['name'] = f"{k['name']} #{seen[key]}"
    order = ['Hospital', 'Bus Stand', 'Bus Stop', 'Railway Station', 'Airport', 'Court', 'Government Office',
             'Fire Station', 'Post Office', 'School', 'College', 'Library', 'Temple', 'Mosque', 'Church',
             'Place of Worship', 'Market', 'Mall', 'Bank', 'Fuel Station', 'Hotel', 'Theatre', 'Community Hall',
             'Tourist Place']
    kept.sort(key=lambda r: (order.index(r['type']), r['name'].lower()))

    # ---- Police stations ---------------------------------------------------
    police, seen_phone = [], {}
    with open(POLICE_CSV, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            name = tidy(r['StationName'])
            notes = ['coordinates are rounded in the source file']
            if name == 'Police Station':
                name = re.sub(r',.*$', '', r['Address']) + ' Police Station'
                notes.insert(0, 'source name was just "Police Station"; named after its street')
            lat, lon = float(r['Latitude']), float(r['Longitude'])
            phone = r['PhoneNumber'].strip()
            digits = re.sub(r'\D', '', phone)
            twin = seen_phone.get(digits)
            if twin and km(twin, {'lat': lat, 'lon': lon}) < 0.5:  # same phone and within 500 m: listed twice
                continue
            row = {'name': name, 'type': r['Type'].strip(), 'address': r['Address'].strip(), 'phone': phone,
                   'lat': lat, 'lon': lon}
            row['area'], row['dist'] = nearest_area(row)
            if row['dist'] > 5:
                notes.append(f"far from the nearest area ({row['dist']:.1f} km)")
            row['notes'] = '; '.join(notes)
            if digits:
                seen_phone[digits] = row
            police.append(row)

    # ---- Old list: add what OpenStreetMap does not have ----------------------
    # Spelling variants of an existing area are skipped; roads and landmarks are not areas.
    not_area = re.compile(r'temple|college|university|junction|court|airport|hospital|school|bus stand|collector|'
                          r'corporation|museum|cathedral|bench|\broad\b|salai|street|\bhill\b', re.I)
    suffix = re.compile(r'\s+(town|area|village|madurai)$|^madurai\s+', re.I)
    area_full = {norm(a['name']): a['name'] for a in areas}
    verify, added = [], []

    def phonetic(name):
        """Tamil place names are spelled many ways (Thiru/Tiru, Uttangudi/Uthangudi): reduce to one sound key."""
        k = re.sub(r'(nagar|colony)', '', name.lower())
        k = re.sub(r'[^a-z]', '', k)
        for old, new in (('th', 't'), ('dh', 'd'), ('ph', 'p'), ('w', 'v'), ('y', ''), ('z', 'l'), ('ee', 'i'),
                         ('oo', 'u'), ('ai', 'i')):
            k = k.replace(old, new)
        return re.sub(r'(.)+', r'', k)

    def similar_area(name, pool):
        key = phonetic(name)
        for pname in pool.values():
            pkey = phonetic(pname)
            if key == pkey or (key[:1] == pkey[:1] and difflib.SequenceMatcher(None, key, pkey).ratio() >= 0.92):
                return pname
            # "Pudur" and "K. Pudur": one name is the other with an initial in front
            has_initial = re.match(r'^[a-z](\. ?| )[a-z]', name.lower()) or re.match(r'^[a-z](\. ?| )[a-z]', pname.lower())
            if has_initial and min(len(key), len(pkey)) >= 5 and (key == pkey[1:] or pkey == key[1:]):
                return pname
        return None

    with open(OLD_LOCATIONS_CSV, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            raw_name, otype = r['Location'].strip(), r['Type'].strip()
            name = raw_name
            while suffix.search(name) and suffix.sub('', name).strip():
                name = suffix.sub('', name).strip()
            row = [raw_name, otype, r['Latitude'], r['Longitude']]
            if otype in ('Landmark', 'City Center') or not_area.search(raw_name):
                verify.append(row + ['Skipped - a landmark or road, not an area (see madurai_landmarks.csv)'])
                continue
            match = similar_area(name, area_full)
            if match:
                verify.append(row + [f'Skipped - same place as "{match}"'])
                continue
            twin = similar_area(name, {norm(x['name']): x['name'] for x in added})
            if twin:
                verify.append(row + [f'Skipped - duplicate of "{twin}" in the old list'])
                continue
            added.append({'name': name, 'type': otype or 'Area', 'lat': float(r['Latitude']),
                          'lon': float(r['Longitude']), 'lat_s': r['Latitude'], 'lon_s': r['Longitude'],
                          'osm_id': '', 'verified': 'No',
                          'notes': 'not in OpenStreetMap; coordinates from the old list, rounded to 2 decimals - check on a map'})
            verify.append(row + [f'Added as "{name}" - coordinates need checking'])
    added.sort(key=lambda x: x['name'].lower())
    for i, a in enumerate(added, len(areas) + 1):
        a['id'] = f'AREA-{i:03d}'
    for a in areas:
        a['verified'] = 'Yes'
    areas = areas + added

    # ---- Write ---------------------------------------------------------------
    write_csv(os.path.join(DATA_DIR, 'madurai_areas.csv'),
              ['Area_ID', 'Area', 'Type', 'Latitude', 'Longitude', 'Verified', 'OSM_ID', 'Notes'],
              [[a['id'], a['name'], a['type'], a.get('lat_s') or f"{a['lat']:.5f}", a.get('lon_s') or f"{a['lon']:.5f}",
                a['verified'], a['osm_id'], a['notes']] for a in areas])
    write_csv(os.path.join(DATA_DIR, 'madurai_landmarks.csv'),
              ['Landmark_ID', 'Landmark', 'Type', 'Latitude', 'Longitude', 'Area', 'Distance_To_Area_km',
               'Address', 'OSM_ID', 'Notes'],
              [[f'LM-{i:04d}', k['name'], k['type'], f"{k['lat']:.5f}", f"{k['lon']:.5f}", k['area'],
                f"{k['dist']:.2f}", k['address'], k['osm_id'], k['notes']] for i, k in enumerate(kept, 1)])
    write_csv(os.path.join(DATA_DIR, 'madurai_police_stations_clean.csv'),
              ['Station_Name', 'Type', 'Address', 'Phone', 'Latitude', 'Longitude', 'Area', 'Distance_To_Area_km',
               'Notes'],
              [[p['name'], p['type'], p['address'], p['phone'], f"{p['lat']:.5f}", f"{p['lon']:.5f}", p['area'],
                f"{p['dist']:.2f}", p['notes']] for p in police])
    write_csv(os.path.join(DATA_DIR, 'madurai_areas_to_verify.csv'),
              ['Old_Name', 'Old_Type', 'Old_Latitude', 'Old_Longitude', 'What_Happened'], verify)

    # ---- Summary -----------------------------------------------------------
    print(f'Areas: {len(areas)} ({len(areas) - len(added)} verified from OpenStreetMap)')
    for t in sorted({a['type'] for a in areas}):
        print(f'  {t:14} {sum(1 for a in areas if a["type"] == t)}')
    print(f'Landmarks: {len(kept)}')
    for t in order:
        n = sum(1 for k in kept if k['type'] == t)
        if n:
            print(f'  {t:18} {n}')
    print(f'Police stations/offices: {len(police)}')
    print(f'Old-list areas added (unverified coordinates): {len(added)}; old names skipped: {len(verify) - len(added)}')
    print('Dropped landmarks:', log['landmarks_dropped'])
    print(f"Merged duplicate landmarks: {len(log['landmarks_merged'])}")
    print(f"Areas given a '(near X)' suffix: {log['areas_renamed']}")


if __name__ == '__main__':
    main()
