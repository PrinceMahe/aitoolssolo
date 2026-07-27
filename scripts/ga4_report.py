#!/usr/bin/env python3
"""
GA4 organic-search reporting harness for aitoolssolo.com.

Two ways to authenticate (set ONE):

1) Service-account JSON  (recommended, no browser prompt at runtime)
   - env GA4_CREDENTIALS=/path/to/sa.json
   - the SA email must be granted "Viewer" on the GA4 property
     (GA4 Admin -> Property -> Property Access Management -> Add user)

2) OAuth device flow  (interactive: opens a Google approve screen once)
   - env GA4_CLIENT_SECRET=/path/to/client_secret.json
     (Cloud Console -> APIs & Services -> Credentials -> OAuth client ID
      of type "Desktop app")
   - a token.json is cached after first approval

Required: env GA4_PROPERTY_ID = numeric property id, e.g. "123456789" (NOT G-JLXF62ZN4).
  Find it: GA4 Admin -> Property Details -> "Property ID".

Output: top countries by sessions + organic-search share for the last N days.
"""
import os, sys, json, datetime
from dotenv import load_dotenv
load_dotenv()

PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID")
CREDS_PATH = os.environ.get("GA4_CREDENTIALS")
CLIENT_SECRET = os.environ.get("GA4_CLIENT_SECRET")
TOKEN_PATH = os.environ.get("GA4_TOKEN", os.path.join(os.path.dirname(__file__), ".ga4_token.json"))
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
            creds = flow.run_local_server(open_browser=False)  # device/console flow -> user approves in browser
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
        return BetaAnalyticsDataClient(credentials=creds)
    raise SystemExit("No GA4 credentials found. Set GA4_CREDENTIALS or GA4_CLIENT_SECRET.")


def run():
    if not PROPERTY_ID:
        raise SystemExit("Set GA4_PROPERTY_ID (numeric, e.g. 123456789).")
    from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
    client = get_client()
    prop = f"properties/{PROPERTY_ID}"
    end = datetime.date.today() - datetime.timedelta(days=1)
    start = end - datetime.timedelta(days=DAYS - 1)

    # 1) countries by sessions
    req = RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
        dimensions=[Dimension(name="country")],
        metrics=[Metric(name="sessions")],
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        limit=10,
    )
    countries = client.run_report(req)

    # 2) channel group -> sessions (organic search share)
    req2 = RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[Metric(name="sessions")],
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
    )
    channels = client.run_report(req2)

    total_sessions = sum(int(r.metric_values[0].value) for r in channels.rows) or 1
    print(f"GA4 property {PROPERTY_ID} | last {DAYS}d ({start} -> {end})")
    print(f"\n{'COUNTRY':18}{'SESSIONS':>11}{'%':>8}")
    for r in countries.rows:
        c = r.dimension_values[0].value or "(unknown)"
        v = int(r.metric_values[0].value)
        print(f"{c:18}{v:>11}{100*v/total_sessions:>7.1f}%")
    print(f"\n{'CHANNEL GROUP':26}{'SESSIONS':>11}{'%':>8}")
    organic = 0
    for r in channels.rows:
        ch = r.dimension_values[0].value or "(unknown)"
        v = int(r.metric_values[0].value)
        if ch.lower() in ("organic search", "organic", "search"):
            organic += v
        print(f"{ch:26}{v:>11}{100*v/total_sessions:>7.1f}%")
    print(f"\nORGANIC SEARCH SHARE = {100*organic/total_sessions:.1f}%  ({organic} of {total_sessions} sessions)")


if __name__ == "__main__":
    run()
