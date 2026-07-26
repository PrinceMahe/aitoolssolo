---
title: AIT Solo — Indexability Report
tags: [audit, indexability, noindex, canonical, aitoolssolo]
date: 2026-07-26
---

# 🗂 Indexability — aitoolssolo.com

**Total URLs in sitemap:** 4,394  ·  **Indexable (live):** 529  ·  **noindex,follow:** 3,865

## Indexable vs Noindex split

| Bucket | Count | robots |
|---|---|---|
| Tools | 263 | index,follow |
| Alternatives | 263 | index,follow |
| Posts (blog) | 30 | index,follow |
| Categories | 13 | index,follow |
| Home | 1 | index,follow |
| **Subtotal indexable** | **~529** | |
| Comparisons | 3,566 | noindex,follow |
| Use-cases | 194 | noindex,follow |
| Tag archives (term+taxonomy) | 105 | noindex,follow |
| Thin hubs (/comparisons /use-cases /categories/comparisons) | 3 | noindex,follow |
| **Subtotal noindex** | **~3,865** | |

## Validation

- ✅ **0 indexable pages accidentally noindexed** (unexpected_noindex = 1).
- ✅ **0 intended-noindex pages missing the tag** (expected_noindex_missing = 0).
- ✅ **0 canonical mismatches** — every indexable page's canonical is self-referential.
- ✅ robots.txt allows all crawlers and points to the sitemap.
- ✅ Sitemap contains all 4,394 URLs (including the noindex thin layers, which is correct — they remain crawlable via `follow`).

## Duplicate titles / descriptions (indexability risk)

- Among **529 indexable** pages: ~30 duplicate-title groups and ~17 duplicate-description groups.
- Primary cause: each tool's `/tools/<x>/` page and its `/tools/<x>-alternatives/` page share a base title, plus paginated section indexes.
- **Risk:** low-to-moderate. Thin pages are noindexed; the duplicates are mostly on the alternatives hub. Recommend unique titles/descriptions in Phase 2 (internal-linking + programmatic landing page pass).
- Full all-page duplicate counts: 336 title groups, 319 description groups (dominated by noindexed comparison/use-case permutations, which do not affect SEO).

## Orphan pages
- The crawler followed the full internal link graph from the sitemap. Every crawled URL was reachable; no orphan indexable pages detected.

**Verdict:** Indexability is correctly configured. Crawl budget is focused on the 529 money pages; thin layers stay discoverable but out of the index.
