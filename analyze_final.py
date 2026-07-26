import json, re
from collections import Counter
from urllib.parse import urlparse

data = json.load(open("final_crawl.json", encoding="utf-8"))
total = len(data)
ok = [d for d in data if d.get("status") == 200]
not200 = [d for d in data if d.get("status") != 200]

# 1. status codes
status_counts = Counter(d.get("status") for d in data)

# 2. noindex check (intended: comparison/usecase/tags noindex, rest indexable)
def intended_noindex(url):
    p = urlparse(url).path
    if "/comparisons/" in p or "/use-cases/" in p:
        return True
    if re.search(r"/tags/", p) or re.search(r"/tags$", p):
        return True
    return False

unexpected_noindex = []
expected_noindex_missing = []
for d in ok:
    rb = d.get("robots")
    if rb and "noindex" in rb:
        if not intended_noindex(d["url"]):
            unexpected_noindex.append(d["url"])
    else:
        if intended_noindex(d["url"]):
            expected_noindex_missing.append(d["url"])

# 3. canonical correctness (canonical should point to self)
canon_mismatch = []
for d in ok:
    c = d.get("canonical")
    if c and d["url"] not in c and c.rstrip("/") != d["url"].rstrip("/"):
        # allow trailing slash differences / www
        if urlparse(c).path.rstrip("/") != urlparse(d["url"]).path.rstrip("/"):
            canon_mismatch.append((d["url"], c))

# 4. titles/descriptions
titles = Counter(d.get("title") for d in ok if d.get("title"))
dup_titles = {t: c for t, c in titles.items() if c > 1 and t}
descs = Counter(d.get("description") for d in ok if d.get("description"))
dup_descs = {t: c for t, c in descs.items() if c > 1 and t}
missing_title = [d["url"] for d in ok if not d.get("title")]
missing_desc = [d["url"] for d in ok if not d.get("description")]

# 5. schema validity proxies
faq_pages = [d for d in ok if d.get("has_faq")]
sa_pages = [d for d in ok if d.get("has_sa")]
bc_pages = [d for d in ok if d.get("has_breadcrumb")]

# 6. OG / twitter
og_missing = [d["url"] for d in ok if not d.get("og_image")]
tw_missing = [d["url"] for d in ok if not d.get("twitter_card")]
og_load_fail = [(d["url"], d.get("og_image_status")) for d in ok if d.get("og_image_status") not in (200, None)]

# 7. broken internal links (from crawl subset: a link whose target we crawled and got !=200)
crawled_set = {d["url"] for d in data}
broken_internal = []
for d in ok:
    for l in d.get("internal_links", []):
        absl = l if l.startswith("http") else ("https://www.aitoolssolo.com" + (l if l.startswith("/") else "/" + l))
        absl = absl.split("#")[0].rstrip("/")
        # only check links that should be in sitemap (same host)
        if "aitoolssolo.com" in absl:
            # we only have status for crawled URLs; mark those not 200 in our crawl
            pass
# Better: cross-reference internal links against crawl results for known URLs
status_map = {d["url"]: d.get("status") for d in data}
for d in ok:
    for l in d.get("internal_links", []):
        if l.startswith("/"):
            absl = "https://www.aitoolssolo.com" + l
        elif "aitoolssolo.com" in l:
            absl = l
        else:
            continue
        absl = absl.split("#")[0]
        if absl in status_map and status_map[absl] != 200:
            broken_internal.append((d["url"], absl, status_map[absl]))

# 8. H1
multi_h1 = [d["url"] for d in ok if d.get("h1_count", 0) > 1]
zero_h1 = [d["url"] for d in ok if d.get("h1_count", 0) == 0]

summary = {
    "total": total, "ok200": len(ok), "not200": len(not200),
    "status_counts": dict(status_counts),
    "unexpected_noindex": len(unexpected_noindex),
    "expected_noindex_missing": len(expected_noindex_missing),
    "canon_mismatch": len(canon_mismatch),
    "dup_titles": len(dup_titles), "dup_descs": len(dup_descs),
    "missing_title": len(missing_title), "missing_desc": len(missing_desc),
    "faq_pages": len(faq_pages), "sa_pages": len(sa_pages), "bc_pages": len(bc_pages),
    "og_missing": len(og_missing), "tw_missing": len(tw_missing), "og_load_fail": len(og_load_fail),
    "broken_internal": len(broken_internal),
    "multi_h1": len(multi_h1), "zero_h1": len(zero_h1),
}
json.dump({"summary": summary,
           "unexpected_noindex": unexpected_noindex[:50],
           "expected_noindex_missing": expected_noindex_missing[:50],
           "canon_mismatch": canon_mismatch[:50],
           "dup_titles": dup_titles, "dup_descs": dup_descs,
           "broken_internal": broken_internal[:100],
           "og_load_fail": og_load_fail[:50],
           "not200": [(d["url"], d.get("status")) for d in not200][:100]},
          open("final_analysis.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(summary, indent=2))
