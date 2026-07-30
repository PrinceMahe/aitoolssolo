#!/usr/bin/env python3
"""GA4 snapshot using user OAuth token (from OAuth desktop flow).
Handles auto-refresh of expired tokens.
"""
import os, datetime, urllib.request, json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Metric, Dimension, OrderBy,
)

PROPERTY = "properties/537308820"
TOKEN_FILE = r'scripts/.ga4_user_token.json'

# Load and refresh token if needed
with open(TOKEN_FILE) as f:
    tok = json.load(f)
creds = Credentials(
    token=tok.get('access_token'),
    refresh_token=tok.get('refresh_token'),
    token_uri=tok['token_uri'],
    client_id=tok['client_id'],
    client_secret=tok['client_secret'],
    scopes=[tok['scope']],
)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    # Save refreshed token
    tok['access_token'] = creds.token
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tok, f, indent=2)

client = BetaAnalyticsDataClient(credentials=creds)
today = datetime.date.today()

for label, days in [("7d", 7), ("30d", 30)]:
    start = today - datetime.timedelta(days=days)
    print(f"=== {label} ({start} → {today}) ===")
    req = RunReportRequest(
        property=PROPERTY,
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=today.isoformat())],
        metrics=[Metric(name="sessions"), Metric(name="totalUsers"),
                 Metric(name="engagedSessions"), Metric(name="screenPageViews"),
                 Metric(name="engagementRate")],
    )
    r = client.run_report(req)
    for row in r.rows:
        print(f"  Sessions: {row.metric_values[0].value}")
        print(f"  Users: {row.metric_values[1].value}")
        print(f"  Engaged: {row.metric_values[2].value}")
        print(f"  Pageviews: {row.metric_values[3].value}")
        print(f"  Engagement: {float(row.metric_values[4].value)*100:.1f}%")

print(f"\n=== Top pages (7d) ===")
req_p = RunReportRequest(
    property=PROPERTY,
    date_ranges=[DateRange(start_date=(today-datetime.timedelta(days=7)).isoformat(), end_date=today.isoformat())],
    dimensions=[Dimension(name="pagePath")],
    metrics=[Metric(name="screenPageViews"), Metric(name="sessions")],
    order_bys=[OrderBy(metric=dict(metric_name="screenPageViews"), desc=True)],
    limit=10,
)
for row in client.run_report(req_p).rows:
    print(f"  {row.dimension_values[0].value}: {row.metric_values[0].value} views / {row.metric_values[1].value} ses")

print(f"\n=== Channels (7d) ===")
req_c = RunReportRequest(
    property=PROPERTY,
    date_ranges=[DateRange(start_date=(today-datetime.timedelta(days=7)).isoformat(), end_date=today.isoformat())],
    dimensions=[Dimension(name="sessionDefaultChannelGroup")],
    metrics=[Metric(name="sessions")],
)
for row in client.run_report(req_c).rows:
    print(f"  {row.dimension_values[0].value}: {row.metric_values[0].value} sessions")

print(f"\n=== Countries (7d) ===")
req_g = RunReportRequest(
    property=PROPERTY,
    date_ranges=[DateRange(start_date=(today-datetime.timedelta(days=7)).isoformat(), end_date=today.isoformat())],
    dimensions=[Dimension(name="country")],
    metrics=[Metric(name="sessions")],
    order_bys=[OrderBy(metric=dict(metric_name="sessions"), desc=True)],
    limit=5,
)
for row in client.run_report(req_g).rows:
    print(f"  {row.dimension_values[0].value}: {row.metric_values[0].value} sessions")