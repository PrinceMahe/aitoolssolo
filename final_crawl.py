#!/usr/bin/env python3
"""Final production crawl of aitoolssolo.com (live). Collects validation data per URL."""
import json, re, gzip, urllib.request, urllib.error, concurrent.futures, time
from urllib.parse import urljoin, urlparse

BASE = "https://www.aitoolssolo.com"
SITEMAP = BASE + "/sitemap.xml"

UA = "Mozilla/5.0 (compatible; HermesAudit/1.0)"

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
            return r.status, dict(r.getheaders()), data
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read() if e.fp else b""
    except Exception as e:
        return None, {}, b""

def get_urls_from_sitemap():
    status, hdr, data = fetch(SITEMAP)
    urls = []
    if status != 200:
        return urls
    try:
        xml = data.decode("utf-8", "replace")
    except Exception:
        xml = data.decode("utf-8", "replace")
    # collect <loc> entries; handle sitemap index
    locs = re.findall(r"<loc>(.*?)</loc>", xml)
    sub = [l for l in locs if l.endswith(".xml") or "sitemap" in l.lower()]
    if sub:
        for s in sub:
            st, _, sd = fetch(s)
            if st == 200:
                urls += re.findall(r"<loc>(.*?)</loc>", sd.decode("utf-8", "replace"))
    else:
        urls = locs
    # filter out sitemap files
    urls = [u for u in urls if not u.endswith(".xml")]
    return urls

def parse_head(html):
    out = {}
    out["canonical"] = re.search(r'<link[^>]*rel=["\']?canonical["\']?[^>]*href=["\']?([^"\'\s>]+)', html)
    out["canonical"] = out["canonical"].group(1) if out["canonical"] else None
    rm = re.search(r'<meta[^>]*name=["\']?robots["\']?[^>]*content=["\']?([^"\'\s>]+)', html)
    out["robots"] = rm.group(1) if rm else None
    ti = re.search(r"<title>(.*?)</title>", html, re.S)
    out["title"] = ti.group(1).strip() if ti else None
    # description: name=description (quoted or unquoted)
    dm = re.search(r'<meta[^>]*name=["\']?description["\']?[^>]*content=["\']([^"\']*)["\']', html)
    if not dm:
        dm = re.search(r'<meta[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']?description', html)
    out["description"] = dm.group(1) if dm else None
    og_img = re.search(r'<meta[^>]*property=["\']?og:image["\']?[^>]*content=["\']?([^"\'\s>]+)', html)
    out["og_image"] = og_img.group(1) if og_img else None
    tw_card = re.search(r'<meta[^>]*name=["\']?twitter:card["\']?[^>]*content=["\']?([^"\'\s>]+)', html)
    out["twitter_card"] = tw_card.group(1) if tw_card else None
    out["h1_count"] = len(re.findall(r"<h1[\s>]", html))
    types = re.findall(r'"@type"\s*:\s*"([^"]+)"', html)
    out["schema_types"] = types
    out["has_faq"] = "FAQPage" in types
    out["has_sa"] = "SoftwareApplication" in types
    out["has_breadcrumb"] = "BreadcrumbList" in types
    return out

def check_og_image_loads(url):
    if not url:
        return None
    if url.startswith("/"):
        url = urljoin(BASE, url)
    st, _, _ = fetch(url, timeout=15)
    return st

def main():
    urls = get_urls_from_sitemap()
    print(f"Discovered {len(urls)} URLs from sitemap")
    results = []
    def work(u):
        st, hdr, data = fetch(u)
        rec = {"url": u, "status": st}
        if st == 200 and data:
            try:
                html = data.decode("utf-8", "replace")
            except Exception:
                html = ""
            head = parse_head(html)
            rec.update(head)
            # internal links
            links = re.findall(r'href=["\']([^"\']+)', html)
            internal = []
            for l in links:
                if l.startswith("/") or l.startswith(BASE):
                    internal.append(l)
            rec["internal_links"] = internal
            # og image load check (sample to avoid hammering)
            rec["og_image_status"] = check_og_image_loads(head.get("og_image")) if head.get("og_image") else None
        return rec
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        results = list(ex.map(work, urls))
    json.dump(results, open("final_crawl.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Crawled {len(results)} pages; wrote final_crawl.json")

if __name__ == "__main__":
    main()
