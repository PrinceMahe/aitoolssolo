#!/usr/bin/env python3
"""Check GSC URL Inspection for last crawl dates of recently updated pages.
Runs Monday mornings to see if Google has recrawled the content changes.

Usage: python scripts/gsc_recrawl_check.py
Output: Prints a table of URLs + last crawl timestamps + any index warnings.
"""
import os, json, datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CRED = os.path.join(os.path.dirname(__file__), '..', '.gsc_token.json')
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
SITE = 'https://www.aitoolssolo.com/'

creds = Credentials.from_authorized_user_file(CRED, SCOPES)
svc = build('webmasters', 'v3', credentials=creds)

# Pages modified in the Aug 1 content push (from git log)
PAGES = [
    '/comparisons/bonsai-vs-indy/',
    '/comparisons/canva-vs-vectorizer/',
    '/comparisons/chatgpt-vs-clickup/',
    '/comparisons/claude-vs-jenni/',
    '/comparisons/clearscope-vs-writer/',
    '/comparisons/freshbooks-vs-square/',
    '/comparisons/krea-vs-vectorizer/',
    '/comparisons/luma-dream-vs-submagic/',
    '/comparisons/luma-vs-playground/',
    '/posts/the-best-ai-writing-tool-for-affiliate-content-a-practical-guide-for-2025/',
    '/use-cases/podcast/',
    '/use-cases/seo/',
]

def check_url(url_path):
    """Inspect a single URL via GSC API."""
    full_url = SITE.rstrip('/') + url_path
    try:
        res = svc.urlInspection().index(inspectionUrl=full_url, siteUrl=SITE).execute()
        insp = res.get('inspectionResult', {})
        idx = insp.get('indexStatusResult', {})
        crawl = insp.get('indexStatusResult', {}).get('lastCrawlTimeMs', None)
        verdict = idx.get('verdict', 'UNKNOWN')
        coverage = idx.get('coverageState', 'UNKNOWN')
        # Convert epoch ms to readable
        if crawl and crawl > 0:
            crawled = datetime.datetime.fromtimestamp(crawl / 1000, tz=datetime.timezone.utc)
            crawl_str = crawled.strftime('%Y-%m-%d %H:%M UTC')
        else:
            crawl_str = 'NEVER'
        return {
            'url': url_path,
            'verdict': verdict,
            'coverage': coverage,
            'last_crawl': crawl_str,
            'error': None,
        }
    except Exception as e:
        return {'url': url_path, 'verdict': 'ERROR', 'coverage': 'ERROR', 'last_crawl': 'ERROR', 'error': str(e)[:120]}

print(f"GSC Recrawl Check — {datetime.date.today().isoformat()}")
print(f"Checking {len(PAGES)} recently modified pages...\n")
print(f"{'URL':50s} {'Crawl':22s} {'Verdict':15s} {'Coverage':25s}")
print("-" * 115)

recrawled_after = 0
not_recrawled = 0
errors = 0
cutoff = datetime.datetime(2026, 8, 1, tzinfo=datetime.timezone.utc)  # Aug 1 = content change date

for url_path in PAGES:
    r = check_url(url_path)
    crawl = r['last_crawl']
    verdict = r['verdict']
    coverage = r['coverage']
    err = r.get('error')

    # Check if crawled after Aug 1
    if crawl != 'NEVER' and crawl != 'ERROR':
        try:
            ct = datetime.datetime.strptime(crawl, '%Y-%m-%d %H:%M UTC').replace(tzinfo=datetime.timezone.utc)
            if ct > cutoff:
                recrawled_after += 1
            else:
                not_recrawled += 1
        except:
            pass

    if err:
        crawl = f'ERR: {err[:30]}'
        errors += 1

    print(f"{url_path:50s} {crawl:22s} {verdict:15s} {coverage:25s}")

print(f"\n--- Summary ---")
print(f"Recrawled since Aug 1 content push: {recrawled_after}/{len(PAGES)}")
print(f"Not yet recrawled: {not_recrawled}/{len(PAGES)}")
print(f"Errors: {errors}")
if recrawled_after == 0:
    print("⚠️  No pages recrawled yet — Google hasn't picked up the changes. This is normal for a low-authority domain; expect 1-4 weeks.")
elif recrawled_after == len(PAGES):
    print("✅ All pages recrawled — Google has seen the content changes. Position movement may follow.")
else:
    print("🔄 Mixed — some pages recrawled, some waiting.")
print(f"\nNext check: Monday {datetime.date.today() + datetime.timedelta(days=(0- datetime.date.today().weekday() + 7) % 7 or 7)}")