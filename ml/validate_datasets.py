"""
Validate the SYNTHETIC datasets produced by generate_datasets.py.

Checks: record/column counts, missing values, duplicates, coordinate validity
(range, inside Tamil Nadu, consistent with the stated location), crime_type
consistency, and dates. It also runs two quick fitness checks with the standard
library only:
  * DBSCAN (haversine, eps=0.5 km, min_samples=5) on the hotspot dataset
  * TF-IDF + cosine similarity on the complaint dataset, scored against the
    ground-truth incident groups

Usage:  python ml/validate_datasets.py      (exit code 1 if any check fails)
"""
import csv
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date

from tn_localities import TN_BOUNDS, HOTSPOT_CRIME_TYPES, COMPLAINT_CRIME_TYPES, anchor_lookup

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset')
CRIME_CSV = os.path.join(DATA_DIR, 'crime_hotspot_dataset.csv')
COMPLAINT_CSV = os.path.join(DATA_DIR, 'complaint_similarity_dataset.csv')
GROUNDTRUTH_CSV = os.path.join(DATA_DIR, 'complaint_similarity_groundtruth.csv')

DATE_MIN, DATE_MAX = date(2024, 1, 1), date(2026, 12, 31)
MAX_KM_FROM_LOCALITY = 3.0

failures = []


def check(ok, label, detail=''):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' - ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)


def load(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def haversine_km(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def common_checks(fields, rows, expected_fields, id_field, allowed_types):
    print(f"  Records: {len(rows)}   Columns: {len(fields)} {fields}")
    check(fields == expected_fields, 'columns match specification')
    check(len(rows) == 1000, '1,000 records', str(len(rows)))

    missing = {f: sum(1 for r in rows if not (r.get(f) or '').strip()) for f in fields}
    check(sum(missing.values()) == 0, 'no missing values',
          ', '.join(f'{k}={v}' for k, v in missing.items() if v) or 'none')

    ids = Counter(r[id_field] for r in rows)
    check(all(c == 1 for c in ids.values()), f'{id_field} unique')
    check(all(r[id_field].startswith('SYN-') for r in rows), f'{id_field} carries SYN- (synthetic) prefix')
    body = Counter(tuple(r[f] for f in fields if f != id_field) for r in rows)
    check(all(c == 1 for c in body.values()), 'no duplicate records (ignoring id)',
          f'{sum(c - 1 for c in body.values())} duplicates')

    types = Counter(r['crime_type'] for r in rows)
    unexpected = set(types) - set(allowed_types)
    check(not unexpected, 'crime_type values are from the allowed set',
          f'unexpected: {sorted(unexpected)}' if unexpected else '')
    check(set(types) == set(allowed_types), 'every crime_type category is present')
    print('  crime_type counts: ' + ', '.join(f'{t}={types[t]}' for t in allowed_types))

    bad_dates, years = 0, Counter()
    for r in rows:
        try:
            d = date.fromisoformat(r['date'])
            years[d.year] += 1
            bad_dates += not (DATE_MIN <= d <= DATE_MAX)
        except ValueError:
            bad_dates += 1
    check(bad_dates == 0, 'dates are valid ISO dates within 2024-2026', f'{bad_dates} bad')
    check(set(years) == {2024, 2025, 2026}, 'dates span 2024, 2025 and 2026', dict(sorted(years.items())).__repr__())


def dbscan(points, eps_km, min_samples):
    n = len(points)
    neighbours = [[j for j in range(n) if haversine_km(points[i], points[j]) <= eps_km] for i in range(n)]
    labels = [None] * n
    cluster = -1
    for i in range(n):
        if labels[i] is not None:
            continue
        if len(neighbours[i]) < min_samples:
            labels[i] = -1
            continue
        cluster += 1
        labels[i] = cluster
        queue = list(neighbours[i])
        while queue:
            j = queue.pop()
            if labels[j] == -1:
                labels[j] = cluster
            if labels[j] is not None:
                continue
            labels[j] = cluster
            if len(neighbours[j]) >= min_samples:
                queue.extend(neighbours[j])
    return labels


def validate_crime():
    print(f"\n=== Crime hotspot dataset: {os.path.basename(CRIME_CSV)} ===")
    fields, rows = load(CRIME_CSV)
    common_checks(fields, rows, ['crime_id', 'crime_type', 'location', 'latitude', 'longitude', 'date'],
                  'crime_id', HOTSPOT_CRIME_TYPES)

    anchors = anchor_lookup()
    points, bad_num, bad_range, outside_tn, unknown_loc, far = [], 0, 0, 0, 0, []
    for r in rows:
        try:
            lat, lon = float(r['latitude']), float(r['longitude'])
        except ValueError:
            bad_num += 1
            continue
        points.append((lat, lon))
        bad_range += not (-90 <= lat <= 90 and -180 <= lon <= 180)
        outside_tn += not (TN_BOUNDS['lat_min'] <= lat <= TN_BOUNDS['lat_max']
                           and TN_BOUNDS['lon_min'] <= lon <= TN_BOUNDS['lon_max'])
        if r['location'] not in anchors:
            unknown_loc += 1
        else:
            d = haversine_km((lat, lon), anchors[r['location']])
            if d > MAX_KM_FROM_LOCALITY:
                far.append((r['crime_id'], r['location'], round(d, 2)))
    check(bad_num == 0, 'latitude/longitude are numeric', f'{bad_num} bad')
    check(bad_range == 0, 'latitude in [-90, 90] and longitude in [-180, 180]')
    check(outside_tn == 0, 'all coordinates inside the Tamil Nadu bounding box', f'{outside_tn} outside')
    check(unknown_loc == 0, 'every location is a known Tamil Nadu locality', f'{unknown_loc} unknown')
    check(not far, f'every point within {MAX_KM_FROM_LOCALITY} km of its stated locality',
          f'{len(far)} too far, e.g. {far[:3]}' if far else '')
    coords = Counter(points)
    check(all(c == 1 for c in coords.values()), 'no duplicate coordinate pairs')
    print(f"  Distinct locations: {len({r['location'] for r in rows})}")

    labels = dbscan(points, eps_km=0.5, min_samples=5)
    sizes = Counter(l for l in labels if l != -1)
    noise = labels.count(-1)
    print(f"  DBSCAN (eps=0.5 km, min_samples=5): {len(sizes)} clusters, "
          f"{len(labels) - noise} clustered points, {noise} noise points")
    for cid, size in sizes.most_common(5):
        locs = Counter(rows[i]['location'] for i, l in enumerate(labels) if l == cid)
        print(f"    cluster {cid:>2}: {size:>3} incidents, mostly {locs.most_common(1)[0][0]}")
    check(len(sizes) >= 10, 'DBSCAN finds at least 10 hotspots')
    check(0.03 <= noise / len(labels) <= 0.30, 'noise share between 3% and 30%', f'{noise / len(labels):.1%}')


STOPWORDS = set("""a an the and or but of to in on at by for from with near around close about is was were
be been am are i my me we our us it its this that he she his her they them their has have had
who which when while as after before so very please kindly sir madam dear officer hello""".split())


def tokenize(text):
    return [t for t in re.findall(r'[a-z0-9]+', text.lower()) if t not in STOPWORDS and len(t) > 1]


def tfidf_vectors(texts):
    docs = [Counter(tokenize(t)) for t in texts]
    df = Counter(term for d in docs for term in d)
    n = len(docs)
    idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}  # same as scikit-learn smooth_idf
    vectors = []
    for d in docs:
        v = {t: tf * idf[t] for t, tf in d.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vectors.append({t: x / norm for t, x in v.items()})
    return vectors


def cosine_matrix(vectors):
    postings = defaultdict(list)
    for i, v in enumerate(vectors):
        for t, w in v.items():
            postings[t].append((i, w))
    sims = []
    for i, v in enumerate(vectors):
        acc = defaultdict(float)
        for t, w in v.items():
            for j, w2 in postings[t]:
                if j != i:
                    acc[j] += w * w2
        sims.append(acc)
    return sims


def validate_complaints():
    print(f"\n=== Complaint similarity dataset: {os.path.basename(COMPLAINT_CSV)} ===")
    fields, rows = load(COMPLAINT_CSV)
    common_checks(fields, rows, ['complaint_id', 'complaint_text', 'crime_type', 'location', 'date'],
                  'complaint_id', COMPLAINT_CRIME_TYPES)

    norm = Counter(' '.join(re.findall(r'[a-z0-9]+', r['complaint_text'].lower())) for r in rows)
    check(all(c == 1 for c in norm.values()), 'no duplicate complaint texts (ignoring case/punctuation)')
    lengths = [len(r['complaint_text'].split()) for r in rows]
    print(f"  Words per complaint: min {min(lengths)}, mean {sum(lengths) / len(lengths):.1f}, max {max(lengths)}")
    anchors = anchor_lookup()
    check(all(r['location'] in anchors for r in rows), 'every location is a known Tamil Nadu locality')

    _, truth = load(GROUNDTRUTH_CSV)
    incident = {t['complaint_id']: t['incident_id'] for t in truth}
    check(set(incident) == {r['complaint_id'] for r in rows}, 'ground-truth file covers every complaint_id')
    group_sizes = Counter(incident.values())
    grouped = sum(1 for r in rows if group_sizes[incident[r['complaint_id']]] > 1)
    print(f"  Related complaints (same incident, different wording): {grouped} in "
          f"{sum(1 for c in group_sizes.values() if c > 1)} incident groups; unrelated singletons: {len(rows) - grouped}")

    vectors = tfidf_vectors([r['complaint_text'] for r in rows])
    sims = cosine_matrix(vectors)
    ids = [r['complaint_id'] for r in rows]
    related, unrelated_sum, unrelated_n = [], 0.0, 0
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            s = sims[i].get(j, 0.0)
            if incident[ids[i]] == incident[ids[j]]:
                related.append(s)
            else:
                unrelated_sum += s
                unrelated_n += 1
    mean_rel, mean_unrel = sum(related) / len(related), unrelated_sum / unrelated_n
    print(f"  TF-IDF cosine: related pairs mean {mean_rel:.3f} (min {min(related):.3f}), "
          f"unrelated pairs mean {mean_unrel:.3f}")

    hits = total = 0
    for i, cid in enumerate(ids):
        if group_sizes[incident[cid]] > 1:
            total += 1
            best = max(sims[i].items(), key=lambda kv: kv[1])[0]
            hits += incident[ids[best]] == incident[cid]
    print(f"  Top-1 most similar complaint is from the same incident: {hits}/{total} ({hits / total:.1%})")

    best = None
    for k in range(10, 90, 5):
        t = k / 100
        tp = sum(1 for s in related if s >= t)
        fp = sum(1 for i in range(len(rows)) for j, s in sims[i].items()
                 if j > i and s >= t and incident[ids[i]] != incident[ids[j]])
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / len(related)
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        if not best or f1 > best[3]:
            best = (t, p, r, f1)
    print(f"  Best duplicate threshold: cosine >= {best[0]:.2f} -> precision {best[1]:.2f}, "
          f"recall {best[2]:.2f}, F1 {best[3]:.2f}")

    check(mean_rel >= 3 * mean_unrel, 'related pairs are far more similar than unrelated pairs')
    check(hits / total >= 0.80, 'top-1 retrieval finds the related complaint for >= 80%')
    check(0.30 <= mean_rel <= 0.90, 'related pairs are similar but not near-copies (mean cosine 0.30-0.90)')


def main():
    print('Validating SYNTHETIC datasets in', DATA_DIR)
    validate_crime()
    validate_complaints()
    print(f"\n{'ALL CHECKS PASSED' if not failures else f'{len(failures)} CHECK(S) FAILED: {failures}'}")
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
