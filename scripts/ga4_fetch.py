#!/usr/bin/env python3
"""Pull GA4 site analytics for aitoolssolo.com"""
import os, sys, json, datetime

os.environ["GA4_PROPERTY_ID"] = "537308820"
os.environ["GA4_CLIENT_SECRET"] = os.path.expanduser("~/.secrets_bak_20260727/ga4_client_secret.json")

PROPERTY_ID = os.environ["GA4_PROPERTY_ID"]
CREDS_PATH = os.environ.get("GA4_CREDENTIALS")
CLIENT_SECRET = os.environ.get("GA4_CLIENT_SECRET")
TOKEN_PATH = os.path.join(os.path.dirname(__file__), ".ga4_token.json")
DAYS = int(os.environ.get("GA4_DAYS", "7"))

def get_client():
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    if CREDS_PATH and os.path.exists(CREDS_PATH):
        from google.oauth2 import service_account
        return BetaAnalyticsDataClient.from_service_account_json(CREDS_PATH)
    if CLIENT_SECRET and os.path.exists(CLIENT_SECRET):
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
        creds = None
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(open_browser=False)
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
        return BetaAnalyticsDataClient(credentials=creds)
    raise SystemExit("No GA4 credentials found.")

def run():
    from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
    client = get_client()
    prop = f"properties/{PROPERTY_ID}"
    today = datetime.date.today()
    end = today - datetime.timedelta(days=1)
    start = end - datetime.timedelta(days=DAYS - 1)

    reports = {}

    # 1) Overview: sessions, users, pageviews
    req = RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
        metrics=[Metric(name="sessions"), Metric(name="totalUsers"), Metric(name="screenPageViews"), Metric(name="newUsers")],
    )
    resp = client.run_report(req)
    for row in resp.rows:
        reports["overview"] = {
            "sessions": row.metric_values[0].value,
            "users": row.metric_values[1].value,
            "pageviews": row.metric_values[2].value,
            "new_users": row.metric_values[3].value,
        }

    # 2) Top pages
    req = RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
        dimensions=[Dimension(name="pagePathPlusQueryString")],
        metrics=[Metric(name="screenPageViews")],
        order_bys=[{"metric": {"metric_name": "screenPageViews"}, "desc": True}],
        limit=10,
    )
    resp = client.run_report(req)
    pages = []
    for row in resp.rows:
        pages.append({"page": row.dimension_values[0].value, "views": row.metric_values[0].value})
    reports["top_pages"] = pages

    # 3) Traffic sources (channel groups)
    req = RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[Metric(name="sessions")],
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
    )
    resp = client.run_report(req)
    channels = []
    for row in resp.rows:
        channels.append({"channel": row.dimension_values[0].value, "sessions": row.metric_values[0].value})
    reports["channels"] = channels

    # 4) Countries
    req = RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
        dimensions=[Dimension(name="country")],
        metrics=[Metric(name="sessions")],
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        limit=10,
    )
    resp = client.run_report(req)
    countries = []
    for row in resp.rows:
        countries.append({"country": row.dimension_values[0].value, "sessions": row.metric_values[0].value})
    reports["countries"] = countries

    # 5) Device category
    req = RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
        dimensions=[Dimension(name="deviceCategory")],
        metrics=[Metric(name="sessions")],
    )
    resp = client.run_report(req)
    devices = []
    for row in resp.rows:
        devices.append({"device": row.dimension_values[0].value, "sessions": row.metric_values[0].value})
    reports["devices"] = devices

    print(json.dumps(reports, indent=2))

if __name__ == "__main__":
    run()
