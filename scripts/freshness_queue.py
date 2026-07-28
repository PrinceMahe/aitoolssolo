#!/usr/bin/env python3
"""Freshness Queue generator for AIT Solo.

Scans all content posts/tools/comparisons/use-cases and builds a weekly
"freshness queue" of items that need review. Signals:

  1. >90 days since lastmod verification
  2. Pricing likely changed (heuristic: post mentions a $ price AND is old)
  3. Features changed (heuristic: post older than 180 days)
  4. New competitor may have appeared (heuristic: old comparison post)
  5. Broken affiliate link (heuristic: link whose host is in a known-dead list)

Outputs a Markdown report to reports/freshness-queue.md and a JSON sidecar.
Run weekly (cron). No network calls; affiliate check is heuristic.
"""
import os, re, glob, datetime, json

ROOT = r'C:\Users\prin-win\aitoolssolo'
CONTENT = os.path.join(ROOT, 'content')
REPORT = r'D:\Local Cloud\Obsidian\01 - Projects\AIT Solo\reports\freshness-queue.md'
NOW = datetime.datetime.now()

SUSPECT_AFFILIATE_HOSTS = [
    'shareasale.com', 'awin1.com', 'clkmg.com', 'getcommissionjunction.com',
    'clickbank.net', 'partnerstack.biz',
]


def parse_fm(path):
    raw = open(path, 'rb').read()
    try:
        txt = raw.decode('utf-8')
    except UnicodeDecodeError:
        txt = raw.decode('cp1252', errors='replace')
    m = re.match(r'^---\r?\n(.*?)\r?\n---\r?\n', txt, re.DOTALL)
    if not m:
        return {}, txt
    fm = {}
    last_key = None
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        mm = re.match(r'^([A-Za-z0-9_]+):\s*(.*)$', line)
        if mm:
            last_key = mm.group(1)
            val = mm.group(2).strip().strip('"').strip("'")
            fm[last_key] = val
            continue
        if line.startswith('  -') or line.startswith('    -'):
            if last_key:
                cur = fm.get(last_key)
                if isinstance(cur, str):
                    fm[last_key] = [cur]
                fm.setdefault(last_key, []).append(
                    line.strip()[2:].strip().strip('"').strip("'"))
            continue
    return fm, txt


def days_since(date_str):
    if not date_str:
        return 9999
    try:
        dt = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        return (NOW - dt).days
    except Exception:
        return 9999


def main():
    items = []
    # Scope to human-written content only: posts/ (30 hand-written reviews) plus
    # the 11 Bucket A comparison pages. Auto-generated tool/alternative/comparison
    # stubs (thousands of files) are noindexed and not worth manual review.
    scan_paths = [os.path.join(CONTENT, 'posts')]
    for slug in [
        'mem-vs-memair', 'claude-vs-jenni', 'bonsai-vs-indy', 'expensify-vs-float',
        'chatgpt-vs-clickup', 'canva-vs-vectorizer', 'luma-vs-playground',
        'freshbooks-vs-square', 'luma-dream-vs-submagic', 'browserbear-vs-relay',
    ]:
        p = os.path.join(CONTENT, 'comparisons', slug + '.md')
        if os.path.exists(p):
            scan_paths.append(p)
    for d in scan_paths:
        if os.path.isfile(d):
            paths = [d]
        else:
            paths = glob.glob(os.path.join(d, '**', '*.md'), recursive=True)
        for path in paths:
            base = os.path.basename(path)
            if base == '_index.md':
                continue
            fm, txt = parse_fm(path)
            if not fm:
                continue
            lastmod = fm.get('lastmod') or fm.get('date')
            title = fm.get('title') or base
            age = days_since(lastmod)
            unverified = (age >= 9999)
            reasons = []
            rel = path.replace(ROOT, '').replace('\\', '/')
            if unverified:
                reasons.append("never verified (no date/lastmod in front matter)")
            elif age > 90:
                reasons.append(f">90d since last verification ({age}d)")
            if age > 90 and re.search(r'\$\s?\d', txt):
                reasons.append("pricing mentioned - likely changed, re-verify vs vendor")
            if age > 180:
                reasons.append("features may have changed (>180d)")
            if age > 120 and '/comparisons/' in rel:
                reasons.append("new competitor may have appeared - re-check landscape")
            for m in re.finditer(r'href="(https?://[^"]+)"', txt):
                host = re.sub(r'^https?://', '', m.group(1)).split('/')[0].lower()
                if any(s in host for s in SUSPECT_AFFILIATE_HOSTS):
                    reasons.append(f"suspect affiliate host: {host}")
            if reasons:
                items.append({'title': title, 'path': rel, 'age': age,
                              'reasons': reasons})

    items.sort(key=lambda x: -x['age'])
    total = len(items)
    lines = []
    lines.append(f"---\ntitle: AIT Solo - Freshness Queue\ntags: [freshness, maintenance, aitoolssolo]\n"
                 f"date: {NOW.strftime('%Y-%m-%d')}\nsource: scripts/freshness_queue.py\n---\n")
    lines.append(f"# Freshness Queue - generated {NOW.strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"**{total} items need review.** Sorted oldest first. Run weekly.\n")
    lines.append("\n## Queue\n")
    for it in items:
        age_label = f"{it['age']}d old" if it['age'] < 9999 else 'unverified'
        lines.append(f"\n### {it['title']}  _({age_label})_")
        lines.append(f"- Path: `{it['path']}`")
        for r in it['reasons']:
            lines.append(f"  - [ ] {r}")
    open(REPORT, 'w', encoding='utf-8').write('\n'.join(lines))
    json.dump(items, open(os.path.join(ROOT, 'scripts', 'freshness_queue.json'), 'w'), indent=2)
    print(f"Freshness queue: {total} items -> {REPORT}")
    return total


if __name__ == '__main__':
    main()
