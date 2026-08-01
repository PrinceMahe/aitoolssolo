#!/usr/bin/env python3
"""Pull Google Search Console data"""
import json, os, sys

TOKEN = os.path.expanduser("~/.secrets_bak_20260727/gsc_token.json")
SITE_URL = "sc-domain:aitoolssolo.com"

# Load & refresh token
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file(TOKEN, ["https://www.googleapis.com/auth/webmasters.readonly"])
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    with open(TOKEN, "w") as f:
        f.write(creds.to_json())

service = build("webmasters", "v3", credentials=creds)

# Pull last 28 days
from datetime import date, timedelta
end = date.today() - timedelta(days=1)
start = end - timedelta(days=27)

request = {
    "startDate": start.isoformat(),
    "endDate": end.isoformat(),
    "dimensions": ["query", "page"],
    "rowLimit": 100,
}
response = service.searchanalytics().query(siteUrl=SITE_URL, body=request).execute()

rows = response.get("rows", [])
print(f"=== Search Console: {SITE_URL} ===")
print(f"Period: {start} to {end}")
print(f"Total rows: {len(rows)}")

total_clicks = sum(r.get("clicks", 0) for r in rows)
total_impressions = sum(r.get("impressions", 0) for r in rows)
if rows:
    avg_pos = sum(r.get("position", 0) * r.get("impressions", 0) for r in rows) / max(total_impressions, 1)
    print(f"Total clicks: {total_clicks}")
    print(f"Total impressions: {total_impressions}")
    print(f"Avg position: {avg_pos:.1f}")
    print(f"CTR: {total_clicks/max(total_impressions,1)*100:.2f}%")

# Bucket by position
buckets = {"1-3": [], "4-7": [], "8-15": [], "16-30": [], "30+": []}
for r in rows:
    pos = r.get("position", 100)
    if pos <= 3: buckets["1-3"].append(r)
    elif pos <= 7: buckets["4-7"].append(r)
    elif pos <= 15: buckets["8-15"].append(r)
    elif pos <= 30: buckets["16-30"].append(r)
    else: buckets["30+"].append(r)

print("\n=== Position Buckets ===")
for bucket, items in buckets.items():
    if items:
        c = sum(i["clicks"] for i in items)
        im = sum(i["impressions"] for i in items)
        print(f"{bucket}: {len(items)} queries, {c} clicks, {im} impressions")

# Top pages
page_stats = {}
for r in rows:
    pg = r["keys"][1]
    if pg not in page_stats:
        page_stats[pg] = {"clicks": 0, "impressions": 0, "queries": set()}
    page_stats[pg]["clicks"] += r.get("clicks", 0)
    page_stats[pg]["impressions"] += r.get("impressions", 0)
    page_stats[pg]["queries"].add(r["keys"][0])

print("\n=== Top Pages by Impressions ===")
sorted_pages = sorted(page_stats.items(), key=lambda x: -x[1]["impressions"])[:15]
for pg, stats in sorted_pages:
    print(f"{pg}")
    print(f"  {stats['clicks']} clicks, {stats['impressions']} impressions, {len(stats['queries'])} unique queries")

# Top queries
query_stats = {}
for r in rows:
    q = r["keys"][0]
    if q not in query_stats:
        query_stats[q] = {"clicks": 0, "impressions": 0}
    query_stats[q]["clicks"] += r.get("clicks", 0)
    query_stats[q]["impressions"] += r.get("impressions", 0)

print("\n=== Top Queries by Impressions ===")
sorted_queries = sorted(query_stats.items(), key=lambda x: -x[1]["impressions"])[:20]
avg_pos_map = {}
for r in rows:
    q = r["keys"][0]
    if q not in avg_pos_map:
        avg_pos_map[q] = {"pos_sum": 0, "count": 0}
    avg_pos_map[q]["pos_sum"] += r.get("position", 0) * r.get("impressions", 0)
    avg_pos_map[q]["count"] += r.get("impressions", 0)

for q, stats in sorted_queries:
    avg = avg_pos_map[q]["pos_sum"] / max(avg_pos_map[q]["count"], 1)
    print(f"  {q}: {stats['clicks']} clicks, {stats['impressions']} impr, pos {avg:.1f}")
