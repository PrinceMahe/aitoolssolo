---
title: Phase 2 — Authority & Scale (Plan)
tags: [phase2, plan, authority, scale, aitoolssolo]
date: 2026-07-26
---

# 🚀 Phase 2 — Authority & Scale

**Objective:** Grow organic traffic from the current run-rate to **100k–250k monthly visits** while building topical authority and preparing for long-term monetization.
**Window:** 2–4 weeks (aggressive content + internal-linking sprint).
**Status:** 🟢 Set up — executing.

---

## 📊 Real Baseline (measured 2026-07-19 → 07-25, Cloudflare Analytics)

> ⚠️ The objective said "~20k weekly" — actual current run-rate is **~40k/week** (Phase 1's 30-post expansion already lifted it). The honest target is lifting this toward 250k/month while smoothing daily variance (currently 3.5k–12.2k/day, high spike dependency).

| Metric | Value |
|---|---|
| Weekly visits (last 7d) | **39,704** |
| Daily avg | ~5,670 |
| Daily range | 1,057 – 12,204 (Jul 23 spike) |
| Monthly run-rate (×4.3) | **~171k** |
| Indexable pages | 529 |
| Posts live | 31 |
| Tools / Alternatives | 263 + 263 |
| Comparisons (noindexed) | 3,566 |
| Use-cases (noindexed) | 194 |
| FAQ answers | 180 (all 40–80w) |

**Interpretation:** The site already sits at the *floor* of the objective (100k/mo). The job is to (a) remove spike-dependence, (b) push the steady-state baseline up 1.5–5×, and (c) unlock the 3,566 comparison pages as indexable surface.

---

## 🎯 Strategy — 4 Workstreams

### WS1 — Content Velocity (programmatic + authored)  ← biggest lever
- **Programmatic "Best AI Tools for [Use-Case]" hubs** generated from the 263-tool + 30-post dataset. ~50–100 indexable pages, each interlinked. *This is the scale engine.*
- **Surface top comparisons:** promote ~200 high-value comparison pages from `noindex` → `index` with unique programmatic intros (kills the wasted 3,566 surface).
- **Authored posts:** keep Monday cadence; work through the 33 queued topics (high-intent clusters: Make vs Zapier, n8n vs Make, Beehiiv vs Substack, etc.).
- **Target:** +150–250 net new indexable pages in 2–4 weeks.

### WS2 — Internal Linking (highest ROI, fastest)
- Systematic contextual inline links between related posts/tools/comparisons.
- Build hub pages (Tool categories × Use-cases) that aggregate + link out.
- Resolves the ~30 dup-title groups among indexable pages and distributes PageRank.
- **Target:** every indexable money page links to ≥3 related indexable pages.

### WS3 — Topical Authority / Entity Coverage
- Cover the full "AI tools for solopreneurs" cluster: tools (done), use-cases (surface), comparisons (surface top), posts (scale to 60+).
- Expand FAQ/PAA where gaps remain.
- Consolidate the 263 `/alternatives/` and 3,566 comparison pages into navigable hubs.

### WS4 — Monetization Prep
- Add **Privacy Policy / About / Contact** pages (AdSense policy compliance + trust).
- Keep noindex discipline on thin layers.
- Affiliate cleanup **deferred per ROI decision** (Phase 1) — revisit only if AdSense/application demands it.

---

## 🛡 Guardrails
- Preserve canonical/robots behavior. Thin permutations stay `noindex,follow`.
- No keyword cannibalization — reuse the existing `KEYWORD_GROUPS` guard in `generate_post.py`.
- FAQ answers stay 40–80 words.
- Every new indexable page must link out + be linked to (WS2).

## 📏 Measurement (weekly)
- CF Analytics visits (daily pull, 2 zones).
- Indexable page count (`crawl` script).
- GA4 engaged sessions / top landing pages.
- Search Console: impressions, clicks, avg position for target keywords.
- Lighthouse (install Chrome on prin-win for real numbers).

## 🗂 Deliverables this setup
- [x] This plan
- [x] Obsidian Phase 2 board
- [x] Programmatic landing-page generator scaffold (builds clean)
- [ ] WS1: generate first wave of use-case hubs
- [ ] WS2: internal-linking pass on 31 posts
- [ ] WS4: policy/about/contact pages

→ Tracking: `Phase2_Tasks.md`
