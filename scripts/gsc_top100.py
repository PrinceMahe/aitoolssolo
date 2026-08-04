import os, json, datetime
from gsc_auth_raw import get_session, SITE

svc = get_session()

# GSC has 2-3 day latency; query last 28 days ending 3 days ago for breadth
end = datetime.date.today() - datetime.timedelta(days=3)
start = end - datetime.timedelta(days=28)

# Query by query+page to get landing page per query
body = {
    'startDate': start.isoformat(),
    'endDate': end.isoformat(),
    'dimensions': ['query', 'page'],
    'rowLimit': 1000,
    'aggregation': 'byProperty',
}
api = "https://searchconsole.googleapis.com/webmasters/v3/sites/" + SITE.rstrip('/') + "/searchAnalytics/query"
res = svc.post(api, json=body).json()
rows = res.get('rows', [])
print(f"Raw query+page rows: {len(rows)}")

# Aggregate per query (sum clicks/impr across pages, weight position by impressions)
from collections import defaultdict
q_agg = defaultdict(lambda: {'clicks':0,'impr':0,'pos_w':0.0,'pages':[]})
for r in rows:
    q, p = r['keys'][0], r['keys'][1]
    c = r.get('clicks',0); i = r.get('impressions',0); pos = r.get('position',0.0)
    a = q_agg[q]
    a['clicks'] += c
    a['impr'] += i
    a['pos_w'] += pos * i  # impression-weighted position
    a['pages'].append((p, c, i, pos))

data = []
for q, a in q_agg.items():
    avg_pos = round(a['pos_w']/a['impr'], 1) if a['impr'] else 0
    ctr = round(100*a['clicks']/a['impr'], 2) if a['impr'] else 0
    # primary landing page = the one with most impressions for this query
    top_page = sorted(a['pages'], key=lambda x:-x[2])[0][0]
    data.append({
        'query': q,
        'clicks': a['clicks'],
        'impr': a['impr'],
        'ctr': ctr,
        'pos': avg_pos,
        'page': top_page,
    })

# Sort by impressions desc (proxy for opportunity/volume) then clicks
data.sort(key=lambda x: (-x['impr'], -x['clicks']))
top100 = data[:100]

print(f"\nDistinct queries: {len(data)}, Top100 captured.")
out = {
    'start': start.isoformat(),
    'end': end.isoformat(),
    'total_queries': len(data),
    'top100': top100,
}
with open(r'C:\Users\prin-win\aitoolssolo\scripts\gsc_top100.json','w') as f:
    json.dump(out, f, indent=2)
print("Wrote scripts/gsc_top100.json")

# Print quick bucket preview
for label,(lo,hi) in [('A 8-15',(8,15.999)),('B 16-30',(16,30.999)),('C >30',(31,999))]:
    n = sum(1 for d in top100 if lo <= d['pos'] <= hi)
    print(f"  {label}: {n} queries in top100")
