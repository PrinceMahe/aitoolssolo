import os, sys, datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
CLIENT_SECRET = r"C:\Users\prin-win\aitoolssolo\scripts\ga4_client_secret.json"
TOKEN_PATH = r"C:\Users\prin-win\aitoolssolo\.gsc_token.json"

def main():
    creds = None
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception as e:
            print(f"Error loading token: {e}", flush=True)

    if not creds or not creds.valid:
        print("Starting OAuth flow. Please visit the URL printed below to authorize GSC access.", flush=True)
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
        creds = flow.run_local_server(open_browser=False)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        print("OAuth token successfully saved.", flush=True)

    service = build('webmasters', 'v3', credentials=creds)
    
    # List sites
    print("Fetching verified sites...", flush=True)
    try:
        sites_res = service.sites().list().execute()
        sites = [s['siteUrl'] for s in sites_res.get('siteEntry', [])]
        print(f"Verified sites in your GSC: {sites}", flush=True)
    except Exception as e:
        print(f"Error fetching sites: {e}", flush=True)
        sys.exit(1)
    
    target_site = None
    for s in sites:
        if "aitoolssolo" in s:
            target_site = s
            break
            
    if not target_site:
        print("No verified site containing 'aitoolssolo' was found in your Google Search Console.", flush=True)
        sys.exit(1)
        
    print(f"Querying performance for: {target_site}...", flush=True)
    
    # Performance query for last 7 days
    # GSC has a 2-3 day data latency. End date = 3 days ago.
    end_date = datetime.date.today() - datetime.timedelta(days=3)
    start_date = end_date - datetime.timedelta(days=7)
    
    # 1. Overall stats
    body_overall = {
        'startDate': start_date.isoformat(),
        'endDate': end_date.isoformat(),
    }
    res_overall = service.searchanalytics().query(siteUrl=target_site, body=body_overall).execute()
    
    clicks = 0
    impressions = 0
    ctr = 0.0
    position = 0.0
    if 'rows' in res_overall and len(res_overall['rows']) > 0:
        row = res_overall['rows'][0]
        clicks = row.get('clicks', 0)
        impressions = row.get('impressions', 0)
        ctr = row.get('ctr', 0.0) * 100
        position = row.get('position', 0.0)
        
    print(f"\n--- GSC Performance Last 7 Days ({start_date} -> {end_date}) ---", flush=True)
    print(f"Total Clicks: {clicks}", flush=True)
    print(f"Total Impressions: {impressions}", flush=True)
    print(f"Average CTR: {ctr:.2f}%", flush=True)
    print(f"Average Position: {position:.1f}", flush=True)
    
    # 2. Top queries
    body_queries = {
        'startDate': start_date.isoformat(),
        'endDate': end_date.isoformat(),
        'dimensions': ['query'],
        'rowLimit': 10
    }
    res_queries = service.searchanalytics().query(siteUrl=target_site, body=body_queries).execute()
    print("\n--- Top Queries ---", flush=True)
    if 'rows' in res_queries:
        for idx, row in enumerate(res_queries['rows'], 1):
            query = row['keys'][0]
            q_clicks = row.get('clicks', 0)
            q_imp = row.get('impressions', 0)
            print(f"{idx}. '{query}' | Clicks: {q_clicks} | Impressions: {q_imp}", flush=True)
    else:
        print("No queries recorded.", flush=True)
        
    # 3. Top pages
    body_pages = {
        'startDate': start_date.isoformat(),
        'endDate': end_date.isoformat(),
        'dimensions': ['page'],
        'rowLimit': 10
    }
    res_pages = service.searchanalytics().query(siteUrl=target_site, body=body_pages).execute()
    print("\n--- Top Pages ---", flush=True)
    if 'rows' in res_pages:
        for idx, row in enumerate(res_pages['rows'], 1):
            page = row['keys'][0]
            p_clicks = row.get('clicks', 0)
            p_imp = row.get('impressions', 0)
            print(f"{idx}. {page} | Clicks: {p_clicks} | Impressions: {p_imp}", flush=True)
    else:
        print("No page visits recorded.", flush=True)

if __name__ == "__main__":
    main()
