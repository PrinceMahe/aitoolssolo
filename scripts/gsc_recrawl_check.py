#!/usr/bin/env python3
"""Check GSC URL Inspection for last crawl dates of recently updated pages.
Runs Monday mornings to see if Google has recrawled the content changes.

Uses raw requests (no google-auth) via gsc_auth_raw helper.

Usage: python scripts/gsc_recrawl_check.py
Output: Prints a table of URLs + last crawl timestamps + any index warnings.
"""
import os
import json
import datetime
import requests
from gsc_auth_raw import get_session, SITE

CHANGE_DATE = datetime.datetime(2026, 8, 1, tzinfo=datetime.timezone.utc)

# Pages modified in the Aug 1 content push + Aug 4 allowlist expansion
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
    '/comparisons/chatgpt-vs-claude/',
    '/comparisons/firefly-vs-topaz/',
    '/comparisons/obsidian-copilot-vs-rewind/',
    '/comparisons/riverside-vs-veed/',
    '/comparisons/ramp-vs-wave/',
    '/comparisons/adobe-firefly-vs-nightcafe/',
    '/comparisons/riverside-vs-wondershare-filmora/',
    '/posts/the-best-ai-writing-tool-for-affiliate-content-a-practical-guide-for-2025/',
    '/use-cases/podcast/',
    '/use-cases/seo/',
]


def check_url(svc, url_path):
    """Inspect a single URL via GSC URL Inspection API (raw requests)."""
    full_url = SITE.rstrip('/') + url_path
    api = (f"https://searchconsole.googleapis.com/v1/urlInspection/index:"
           f"inspect?siteUrl={SITE.rstrip('/')}")
    try:
        r = svc.post(api, json={"inspectionUrl": full_url, "siteUrl": SITE.rstrip('/')}, timeout=30)
        r.raise_for_status()
        res = r.json()
        idx = res.get('inspectionResult', {}).get('indexStatusResult', {})
        crawl_ms = idx.get('lastCrawlTimeMs', None)
        verdict = idx.get('verdict', 'UNKNOWN')
        coverage = idx.get('coverageState', 'UNKNOWN')
        if crawl_ms and crawl_ms > 0:
            crawled = datetime.datetime.fromtimestamp(crawl_ms / 1000, tz=datetime.timezone.utc)
            crawl_str = crawled.strftime('%Y-%m-%d %H:%M UTC')
        else:
            crawl_str = 'NEVER'
        return {'url': url_path, 'verdict': verdict, 'coverage': coverage,
                'last_crawl': crawl_str, 'error': None}
    except Exception as e:
        return {'url': url_path, 'verdict': 'ERROR', 'coverage': 'ERROR',
                'last_crawl': 'ERROR', 'error': str(e)[:120]}


def main():
    svc = get_session()
    print(f"GSC Recrawl Check — {datetime.date.today().isoformat()}")
    print(f"Checking {len(PAGES)} recently modified pages...\n")
    print(f"{'URL':52s} {'Crawl':22s} {'Verdict':15s} {'Coverage':25s}")
    print("-" * 117)

    recrawled_after = not_recrawled = errors = 0
    for url_path in PAGES:
        r = check_url(svc, url_path)
        crawl, verdict, coverage, err = r['last_crawl'], r['verdict'], r['coverage'], r.get('error')
        if crawl not in ('NEVER', 'ERROR'):
            try:
                ct = datetime.datetime.strptime(crawl, '%Y-%m-%d %H:%M UTC').replace(tzinfo=datetime.timezone.utc)
                (recrawled_after if ct > CHANGE_DATE else not_recrawled) + 1
                if ct > CHANGE_DATE:
                    recrawled_after += 1
                else:
                    not_recrawled += 1
            except Exception:
                pass
        if err:
            crawl = f'ERR: {err[:30]}'
            errors += 1
        print(f"{url_path:52s} {crawl:22s} {verdict:15s} {coverage:25s}")

    print(f"\n--- Summary ---")
    print(f"Recrawled since content push: {recrawled_after}/{len(PAGES)}")
    print(f"Not yet recrawled: {not_recrawled}/{len(PAGES)}")
    print(f"Errors: {errors}")
    if recrawled_after == 0:
        print("⚠️  No pages recrawled yet — normal for low-authority domain; expect 1-4 weeks.")
    elif recrawled_after == len(PAGES):
        print("✅ All pages recrawled — Google has seen the changes. Position movement may follow.")
    else:
        print("🔄 Mixed — some pages recrawled, some waiting.")


if __name__ == "__main__":
    main()
