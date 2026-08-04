#!/usr/bin/env python3
"""Full GSC export — paginate ALL query+page rows (up to 25k), not just top 100.
Outputs:
  - scripts/gsc_full_export.json  (all rows, raw)
  - scripts/gsc_full_export.csv   (same, CSV)

GSC API v3: rowLimit=25000, paginate with startRow.
"""
import os, json, csv, datetime
from gsc_auth_raw import get_session, SITE

svc = get_session()

# Last 28 full days (gives enough volume for signal)
end = datetime.date.today() - datetime.timedelta(days=3)
start = end - datetime.timedelta(days=28)

all_rows = []
batch_no = 0
start_row = 0
LIMIT = 25000  # GSC API max per call

while True:
    body = {
        'startDate': start.isoformat(),
        'endDate': end.isoformat(),
        'dimensions': ['query', 'page'],
        'rowLimit': LIMIT,
        'startRow': start_row,
        'aggregation': 'byProperty',
    }
    api = "https://searchconsole.googleapis.com/webmasters/v3/sites/" + SITE.rstrip('/') + "/searchAnalytics/query"
    res = svc.post(api, json=body).json()
    rows = res.get('rows', [])
    if not rows:
        break
    batch_no += 1
    for r in rows:
        all_rows.append({
            'query': r['keys'][0],
            'page': r['keys'][1],
            'clicks': r.get('clicks', 0),
            'impressions': r.get('impressions', 0),
            'position': round(r.get('position', 0.0), 1),
            'ctr': round(100 * r.get('clicks', 0) / max(r.get('impressions', 1), 1), 2),
        })
    print(f"Batch {batch_no}: fetched {len(rows)} rows (startRow={start_row}) — total so far: {len(all_rows)}")
    if len(rows) < LIMIT:
        break
    start_row += LIMIT

print(f"\nTotal rows (query×page): {len(all_rows)}")

# Aggregate to query-level (the same query on different pages)
from collections import defaultdict
q_agg = defaultdict(lambda: {'clicks':0, 'impr':0, 'pos_w':0.0, 'pages':[]})
for r in all_rows:
    q = r['query']
    a = q_agg[q]
    a['clicks'] += r['clicks']
    a['impr'] += r['impressions']
    a['pos_w'] += r['position'] * r['impressions']
    a['pages'].append({'page': r['page'], 'clicks': r['clicks'], 'impr': r['impressions'], 'pos': r['position']})

queries = []
for q, a in q_agg.items():
    avg_pos = round(a['pos_w'] / a['impr'], 1) if a['impr'] else 0
    ctr = round(100 * a['clicks'] / a['impr'], 2) if a['impr'] else 0
    top_page = sorted(a['pages'], key=lambda x: -x['impr'])[0]
    queries.append({
        'query': q,
        'clicks': a['clicks'],
        'impressions': a['impr'],
        'ctr': ctr,
        'position': avg_pos,
        'top_page': top_page['page'],
        'pages_count': len(a['pages']),
    })

# Sort by position (best first) — reveals hidden ceiling-breakers
queries.sort(key=lambda x: x['position'])

outfile = os.path.join(os.path.dirname(__file__), 'gsc_full_export.json')
with open(outfile, 'w') as f:
    json.dump({
        'start': start.isoformat(),
        'end': end.isoformat(),
        'total_query_page_rows': len(all_rows),
        'distinct_queries': len(queries),
        'total_clicks': sum(q['clicks'] for q in queries),
        'total_impressions': sum(q['impressions'] for q in queries),
        'queries': queries,
    }, f, indent=2)
print(f"Wrote {outfile} ({len(queries)} queries)")

csvfile = os.path.join(os.path.dirname(__file__), 'gsc_full_export.csv')
with open(csvfile, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['query', 'clicks', 'impressions', 'ctr', 'position', 'top_page', 'pages_count'])
    for q in queries:
        w.writerow([q['query'], q['clicks'], q['impressions'], q['ctr'], q['position'], q['top_page'], q['pages_count']])
print(f"Wrote {csvfile}")

# The real finder: queries where position < 30 but we got 0 clicks
# These are the "almost breaking through" set
ceiling = [q for q in queries if q['position'] < 30 and q['clicks'] == 0]
print(f"\n=== CEILING BREAKERS: {len(ceiling)} queries at position < 30 with 0 clicks ===")
for q in sorted(ceiling, key=lambda x: -x['impressions'])[:30]:
    print(f"  pos={q['position']:5.1f}  impr={q['impressions']:>5d}  \"{q['query'][:60]:60s}\"  →  {q['top_page'].split('/')[-2][:40]}")

# Also: total available that weren't in the old top100
print(f"\nTotal distinct queries: {len(queries)}")
print(f"Previously visible (top100): 100")
print(f"Newly visible: {len(queries) - 100}")