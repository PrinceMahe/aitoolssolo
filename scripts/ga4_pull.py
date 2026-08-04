#!/usr/bin/env python3
"""Minimal GA4 report puller — uses requests + raw OAuth token, no google-auth
dependency (the Hermes venv's cryptography package is currently broken).

Refresh logic: if access_token is missing/expired, POST to Google's token
endpoint with the refresh_token (raw, no crypto needed).
"""
import json, time, urllib.parse, urllib.request
import requests

TOKEN_FILE = r'C:\Users\prin-win\aitoolssolo\scripts\.ga4_user_token.json'
PROPERTY_ID = '537308820'
PID = f'properties/{PROPERTY_ID}'

def load_token():
    return json.load(open(TOKEN_FILE))

def save_token(tok):
    json.dump(tok, open(TOKEN_FILE, 'w'), indent=2)

def refresh_access_token(tok):
    """Exchange refresh_token for a new access_token via raw HTTP POST."""
    client_id = tok['client_id']
    client_secret = tok['client_secret']
    refresh = tok['refresh_token']
    body = urllib.parse.urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh,
        'grant_type': 'refresh_token',
    }).encode()
    req = urllib.request.Request(
        'https://oauth2.googleapis.com/token',
        data=body,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        new = json.loads(resp.read().decode())
    tok['access_token'] = new['access_token']
    tok['expires_in'] = new.get('expires_in', 3600)
    tok['_fetched_at'] = int(time.time())
    # refresh_token not returned on refresh — keep the old one
    save_token(tok)
    return tok['access_token']

def get_access_token(tok):
    now = int(time.time())
    fetched = tok.get('_fetched_at', 0)
    if tok.get('access_token') and (now - fetched) < int(tok.get('expires_in', 3600)) - 60:
        return tok['access_token']
    return refresh_access_token(tok)

def run_report(access_token, start, end, dimensions, metrics, limit=10, offset=0):
    url = f'https://analyticsdata.googleapis.com/v1beta/{PID}:runReport'
    payload = {
        'dateRanges': [{'startDate': start, 'endDate': end}],
        'dimensions': [{'name': d} for d in dimensions],
        'metrics': [{'name': m} for m in metrics],
        'limit': limit,
        'offset': offset,
        'orderBys': [{'metric': {'metricName': metrics[0]}, 'desc': True}],
    }
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    r = requests.post(url, json=payload, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()

def today():
    return time.strftime('%Y-%m-%d', time.localtime())

def days_ago(n):
    import datetime
    d = datetime.date.today() - datetime.timedelta(days=n)
    return d.isoformat()

if __name__ == '__main__':
    tok = load_token()
    at = get_access_token(tok)

    print(f"GA4 Report — Property {PROPERTY_ID}")
    print(f"Generated: {today()}\n")

    # 1. 30-day totals
    print("=== 30-DAY OVERVIEW (Jul 3 → Aug 1) ===")
    res = run_report(at, days_ago(30), today(), ['date'],
                     ['sessions', 'totalUsers', 'engagedSessions', 'screenPageViews', 'bounceRate'],
                     limit=30)
    rows = res.get('rows', [])
    tot_sessions = tot_users = tot_engaged = tot_pv = 0
    for row in rows:
        dims = [d['value'] for d in row['dimensionValues']]
        mets = [float(m['value']) for m in row['metricValues']]
        tot_sessions += mets[0]
        tot_users += mets[1]
        tot_engaged += mets[2]
        tot_pv += mets[3]
    print(f"  Sessions:     {int(tot_sessions)}")
    print(f"  Users:        {int(tot_users)}")
    print(f"  Engaged:      {int(tot_engaged)} ({100*tot_engaged/max(tot_sessions,1):.0f}%)")
    print(f"  Pageviews:    {int(tot_pv)}")

    # 2. Last 7 days by day
    print("\n=== LAST 7 DAYS BY DAY ===")
    res = run_report(at, days_ago(7), today(), ['date'],
                     ['sessions', 'totalUsers', 'engagedSessions'], limit=7)
    for row in res.get('rows', []):
        dims = [d['value'] for d in row['dimensionValues']]
        mets = [int(float(m['value'])) for m in row['metricValues']]
        print(f"  {dims[0]}:  {mets[0]:>3d} sessions  {mets[1]:>3d} users  engaged={mets[2]}")

    # 3. Channels
    print("\n=== ACQUISITION CHANNELS (30d) ===")
    res = run_report(at, days_ago(30), today(), ['sessionDefaultChannelGroup'],
                     ['sessions', 'engagedSessions', 'bounceRate'], limit=10)
    for row in res.get('rows', []):
        dims = [d['value'] for d in row['dimensionValues']]
        mets = [int(float(m['value'])) for m in row['metricValues']]
        print(f"  {dims[0]:20s}  {mets[0]:>3d} sessions  engaged={mets[1]}  bounce={100*mets[2]:.0f}%")

    # 4. Top landing pages (7d)
    print("\n=== TOP LANDING PAGES (7d) ===")
    res = run_report(at, days_ago(7), today(), ['landingPage'],
                     ['sessions', 'averageSessionDuration', 'engagedSessions'], limit=10)
    for row in res.get('rows', []):
        dims = [d['value'] for d in row['dimensionValues']]
        mets = [float(m['value']) for m in row['metricValues']]
        print(f"  {dims[0]:55s}  {int(mets[0]):>3d} sessions  {mets[1]:.0f}s avg")

    # 5. Countries
    print("\n=== TOP COUNTRIES (7d) ===")
    res = run_report(at, days_ago(7), today(), ['country'],
                     ['sessions'], limit=8)
    for row in res.get('rows', []):
        dims = [d['value'] for d in row['dimensionValues']]
        mets = [int(float(m['value'])) for m in row['metricValues']]
        print(f"  {dims[0]:15s}  {mets[0]} sessions")

    # 6. Device
    print("\n=== DEVICE CATEGORY (30d) ===")
    res = run_report(at, days_ago(30), today(), ['deviceCategory'],
                     ['sessions'], limit=5)
    for row in res.get('rows', []):
        dims = [d['value'] for d in row['dimensionValues']]
        mets = [int(float(m['value'])) for m in row['metricValues']]
        print(f"  {dims[0]:10s}  {mets[0]} sessions")
