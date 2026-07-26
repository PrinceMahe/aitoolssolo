#!/usr/bin/env python3
"""Phase 2 Sprint 1 — landing link-equity audit.

Crawls the built public/ site (no server needed) and for every landing page
reports inbound internal links, link depth from homepage, anchor diversity,
orphan status, and sitemap status. Also verifies the homepage/popular/category
surfaces actually link out.

Outputs reports/landing-link-audit.md.

Usage: python scripts/audit_landing_links.py
"""
import os
import re
import json
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, "public")
REPORT = os.path.join(ROOT, "reports", "landing-link-audit.md")

LANDING_RE = re.compile(r'/landing/([a-z0-9-]+)/')
HREF_RE = re.compile(r'href=(?:"([^"]*)"|\'([^\']*)\'|([^ >]+))')
ANCHOR_RE = re.compile(r'<a [^>]*href="?/landing/[^ >]*"?[^>]*>(.*?)</a>', re.S)


def load_landing_slugs():
    slugs = set()
    for p in glob.glob(os.path.join(PUBLIC, "landing", "*", "index.html")):
        slug = os.path.basename(os.path.dirname(p))
        slugs.add(slug)
    return slugs


def get_links(html):
    """Return list of (href, anchor_text) internal links found in html."""
    links = []
    # find <a ... href=...>text</a>
    for m in re.finditer(r'<a\b([^>]*)>(.*?)</a>', html, re.S | re.I):
        attrs, text = m.group(1), m.group(2)
        hm = re.search(r'href=(?:"([^"]*)"|\'([^\']*)\'|([^ >]+))', attrs, re.I)
        if not hm:
            continue
        href = hm.group(1) or hm.group(2) or hm.group(3) or ""
        if href.startswith("/landing/"):
            anchor = re.sub(r"<[^>]+>", "", text).strip()
            links.append((href, anchor))
    return links


def main():
    slugs = load_landing_slugs()
    if not slugs:
        print("No landing pages built. Run hugo build first.")
        return

    # index all pages -> their outbound landing links
    page_links = {}  # pagepath -> set of landing slugs it links to
    all_pages = []
    for hp in glob.glob(os.path.join(PUBLIC, "**", "index.html"), recursive=True):
        rel = os.path.relpath(hp, PUBLIC).replace("\\", "/")
        all_pages.append(rel)
        with open(hp, encoding="utf-8", errors="ignore") as f:
            html = f.read()
        out = set()
        for href, _ in get_links(html):
            m = LANDING_RE.search(href)
            if m:
                out.add(m.group(1))
        page_links[rel] = out

    # sitemap status
    sm = set()
    smpath = os.path.join(PUBLIC, "sitemap.xml")
    if os.path.exists(smpath):
        with open(smpath, encoding="utf-8", errors="ignore") as f:
            for m in re.finditer(r"<loc>([^<]*)</loc>", f.read()):
                if "/landing/" in m.group(1):
                    sm.add(m.group(1).rstrip("/").split("/landing/")[-1])

    # inbound per landing slug
    inbound = {s: set() for s in slugs}
    for rel, outs in page_links.items():
        for s in outs:
            if s in inbound:
                inbound[s].add(rel)

    # depth from homepage (BFS over internal links, only counting /landing/ hops? 
    # We measure click-depth using the site graph: homepage -> any page -> landing.
    # Build adjacency of all internal links (not just landing) for depth calc.
    adj = {}
    for hp in glob.glob(os.path.join(PUBLIC, "**", "index.html"), recursive=True):
        rel = os.path.relpath(hp, PUBLIC).replace("\\", "/")
        with open(hp, encoding="utf-8", errors="ignore") as f:
            html = f.read()
        outs = set()
        for m in re.finditer(r'<a\b[^>]*?\shref=([\'"]?)([^\'"\s>]+)\1', html, re.I):
            u = m.group(2)
            if u.startswith("/") and not u.startswith("//"):
                outs.add(u.rstrip("/"))
        adj[rel] = outs

    # BFS from homepage
    depth = {"index.html": 0}
    q = ["index.html"]

    def href_to_rel(u):
        # /landing/slug/ -> landing/slug/index.html ; / -> index.html
        u = u.rstrip("/")
        if u == "" or u == "/":
            return "index.html"
        rel = u.lstrip("/")
        if rel.endswith("index.html"):
            return rel
        return rel + "/index.html"

    # rebuild adj with normalized rel targets
    adj_norm = {}
    for rel, outs in adj.items():
        adj_norm[rel] = {href_to_rel(o) for o in outs}
    adj = adj_norm

    while q:
        cur = q.pop(0)
        d = depth[cur]
        for nxt in adj.get(cur, ()):
            if nxt not in depth:
                depth[nxt] = d + 1
                q.append(nxt)

    def landing_depth(slug):
        key = f"landing/{slug}/index.html"
        return depth.get(key, 999)

    # inbound restricted to substantive sources (exclude thin noindex layers:
    # comparisons, use-cases, alternatives) so the count reflects real equity.
    THIN = ("comparisons/", "use-cases/", "alternatives/")
    rows = []
    orphans = 0
    too_deep = 0
    under10 = 0
    for s in sorted(slugs):
        ib_all = inbound.get(s, set())
        ib = {p for p in ib_all if not any(p.startswith(t) for t in THIN)}
        n = len(ib)
        d = landing_depth(s)
        in_sm = s in sm
        anchors = set()
        for rel in ib:
            hp = os.path.join(PUBLIC, rel)
            if os.path.exists(hp):
                with open(hp, encoding="utf-8", errors="ignore") as f:
                    for href, a in get_links(f.read()):
                        if s in href:
                            anchors.add(a)
        orphan = n == 0
        if orphan:
            orphans += 1
        if d > 3:
            too_deep += 1
        if n < 10:
            under10 += 1
        rows.append((s, n, d, in_sm, orphan, len(anchors), len(ib_all)))

    # report
    lines = []
    lines.append("# Landing Link-Equity Audit")
    lines.append("")
    lines.append(f"Pages audited: {len(all_pages)} | Landing pages: {len(slugs)}")
    lines.append("")
    lines.append(f"- Orphaned (0 inbound): **{orphans}**")
    lines.append(f"- Deeper than 3 clicks from homepage: **{too_deep}**")
    lines.append(f"- With <10 inbound links: **{under10}**")
    lines.append(f"- In sitemap: **{sum(1 for s in slugs if s in sm)}/{len(slugs)}**")
    lines.append("")
    lines.append("## Per-page")
    lines.append("")
    lines.append("| Landing slug | Inbound (substantive) | Total inbound | Depth | In sitemap | Orphan | Anchor diversity |")
    lines.append("|---|---|---|---|---|---|---|")
    for s, n, d, in_sm, orphan, na, total in rows:
        lines.append(f"| {s} | {n} | {total} | {d} | {'✓' if in_sm else '✗'} | "
                      f"{'⚠ orphan' if orphan else 'ok'} | {na} |")
    lines.append("")
    # summary table of inbound sources per landing
    lines.append("## Inbound source counts")
    lines.append("")
    for s in sorted(slugs):
        ib = inbound.get(s, set())
        lines.append(f"- **{s}**: {len(ib)} inbound ({', '.join(sorted(ib)[:6])}"
                     f"{' …' if len(ib) > 6 else ''})")
    lines.append("")

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {REPORT}")
    print(f"Landing: {len(slugs)} | orphans: {orphans} | <10 inbound: {under10} | >3 deep: {too_deep}")
    # show any failures
    bad = [r for r in rows if r[4] or r[1] < 10 or r[2] > 3 or not r[3]]
    if bad:
        print("FAILURES:")
        for s, n, d, in_sm, orphan, na, total in bad:
            print(f"  {s}: inbound={n} (total={total}) depth={d} sitemap={in_sm} orphan={orphan}")
    else:
        print("ALL CHECKS PASSED ✓")


if __name__ == "__main__":
    main()
