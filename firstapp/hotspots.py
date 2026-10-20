"""
Crime hotspot analysis for the dashboard map.

Reads the complaints stored in the database, groups complaints that are within
EPS_KM of each other (DBSCAN with haversine distance), and colours each area by
how many complaints it has (see RISK_LEVELS). Standard library only.
"""
import math
from collections import Counter, defaultdict

from .models import Complaint

EPS_KM = 0.5
EARTH_RADIUS_KM = 6371.0

# Colour an area by its number of complaints: (level, minimum complaints).
RISK_LEVELS = [('High', 6), ('Medium', 3), ('Low', 1)]

# Complaints that should not count as crimes on the map.
EXCLUDED_STATUSES = ['Duplicate / Ignored', 'Closed / Rejected']


def _haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def dbscan(points, eps_km=EPS_KM, min_samples=1):
    """Return a cluster label per point (-1 = noise). Uses a grid so only nearby cells are compared."""
    cell = eps_km / 111.0  # degrees of latitude per eps; longitude cells are never narrower in TN
    grid = defaultdict(list)
    for i, (lat, lon) in enumerate(points):
        grid[(int(lat // cell), int(lon // cell))].append(i)

    def neighbours(i):
        lat, lon = points[i]
        cx, cy = int(lat // cell), int(lon // cell)
        return [j for dx in (-1, 0, 1) for dy in (-1, 0, 1) for j in grid.get((cx + dx, cy + dy), ())
                if _haversine_km(lat, lon, *points[j]) <= eps_km]

    labels = [None] * len(points)
    cluster = -1
    for i in range(len(points)):
        if labels[i] is not None:
            continue
        seeds = neighbours(i)
        if len(seeds) < min_samples:
            labels[i] = -1
            continue
        cluster += 1
        labels[i] = cluster
        while seeds:
            j = seeds.pop()
            if labels[j] == -1:
                labels[j] = cluster  # border point
            if labels[j] is not None:
                continue
            labels[j] = cluster
            nbrs = neighbours(j)
            if len(nbrs) >= min_samples:
                seeds.extend(nbrs)
    return labels


def risk_level(count):
    return next(level for level, minimum in RISK_LEVELS if count >= minimum)


def _complaint_rows():
    rows = []
    qs = Complaint.objects.exclude(status__in=EXCLUDED_STATUSES).values(
        'category', 'area', 'city', 'latitude', 'longitude', 'incident_date', 'status')
    for c in qs:
        try:
            lat, lon = float(c['latitude']), float(c['longitude'])
        except (TypeError, ValueError):
            continue  # no usable coordinates
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        area, city = (c['area'] or '').strip(), (c['city'] or '').strip()
        if area and city and city.lower() not in area.lower():
            area = f'{area}, {city}'
        rows.append({
            'lat': lat, 'lon': lon,
            'type': (c['category'] or 'Other').strip().title(),
            'location': area or city or 'Unknown area',
            'date': c['incident_date'] or '',
            'status': c['status'],
        })
    return rows


def get_hotspots(crime_type='', year=''):
    """Hotspot analysis of stored complaints as a JSON-serialisable dict."""
    rows = _complaint_rows()
    all_types = sorted({r['type'] for r in rows})
    all_years = sorted({r['date'][:4] for r in rows if r['date'][:4].isdigit()})
    if crime_type:
        rows = [r for r in rows if r['type'] == crime_type]
    if year:
        rows = [r for r in rows if r['date'].startswith(year)]

    labels = dbscan([(r['lat'], r['lon']) for r in rows])
    members = defaultdict(list)
    for r, label in zip(rows, labels):
        members[label].append(r)

    clusters = []
    for label, group in members.items():
        lat = sum(r['lat'] for r in group) / len(group)
        lon = sum(r['lon'] for r in group) / len(group)
        types = Counter(r['type'] for r in group)
        clusters.append({
            'lat': round(lat, 6),
            'lon': round(lon, 6),
            'count': len(group),
            'area': Counter(r['location'] for r in group).most_common(1)[0][0],
            'primary_crime': types.most_common(1)[0][0],
            'crime_breakdown': dict(types.most_common()),
            'radius_m': round(max(max(_haversine_km(lat, lon, r['lat'], r['lon']) for r in group) * 1000, 200)),
            'latest': max(r['date'] for r in group),
            'risk': risk_level(len(group)),
            'label': label,
        })
    clusters.sort(key=lambda c: c['count'], reverse=True)
    cluster_ids = {}
    for i, c in enumerate(clusters, 1):
        c['id'] = i
        cluster_ids[c.pop('label')] = i

    return {
        'source': 'Complaints stored in the database',
        'algorithm': f'complaints within {EPS_KM} km grouped by DBSCAN (haversine)',
        'risk_levels': [{'level': level, 'min': minimum} for level, minimum in RISK_LEVELS],
        'filters': {'crime_type': crime_type, 'year': year},
        'crime_types': all_types,
        'years': all_years,
        'total_incidents': len(rows),
        'clusters': clusters,
        'points': [{'lat': r['lat'], 'lon': r['lon'], 'type': r['type'], 'location': r['location'],
                    'date': r['date'], 'status': r['status'], 'cluster': cluster_ids[label]}
                   for r, label in zip(rows, labels)],
    }
