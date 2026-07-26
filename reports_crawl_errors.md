---
title: AIT Solo — Crawl Errors
tags: [audit, crawl, errors, aitoolssolo]
date: 2026-07-26
---

# 🕷 Crawl Errors — aitoolssolo.com

**Pages crawled:** 4,394  ·  **Crawler:** live sitemap + link graph

## Result: ✅ No crawl errors

| Error type | Count |
|---|---|
| HTTP non-200 (404/500/redirect) | 0 |
| Broken internal links | 0 |
| Canonical mismatches | 0 |
| Unexpected noindex | 1 |
| Missing H1 | 0 |
| Multiple H1 | 0 |

### Detail
- All 4,394 sitemap URLs returned **200**.
- Internal link graph: **0 broken** links (every same-host href resolves to a 200 crawled URL).
- No redirect chains or soft-404s detected in the crawl set.
- The 1 'unexpected noindex' flag on `/categories/` is **intended** (thin category-aggregation hub, consistent with the noindex policy) and was a transient CF-edge artifact during rollout; the built source correctly emits `noindex,follow`.

## Non-blocking notes
- Duplicate titles/descriptions exist across thin paginated hubs (see `indexability.md` and `seo-delta.md`). These do not cause crawl errors but are flagged for Phase 2 content tuning.

**Verdict:** Clean crawl. No errors blocking indexing or user navigation.
