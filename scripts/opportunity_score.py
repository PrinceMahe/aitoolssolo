#!/usr/bin/env python3
"""Opportunity Score — rank GSC queries by how much they can move the needle.

Formula (per the 2026-07-27 ranking strategy):

    Opportunity Score = impressions x ctr_gap x position_potential

    ctr_gap          = expected_ctr(target_pos) - current_ctr   (fractional, >=0)
    target_pos       = 10 if pos > 10 else max(1, pos - 2)      (realistic next milestone)
    position_potential = clamp((18 - pos) / 18, 0, 1)            (zero at pos >= 18)

Why these constants:
  - Multiplicative on impressions => high-volume queries dominate (correct: a
    page with 12k impr is worth 100x a page with 120 impr at the same position).
  - ctr_gap rewards pages with room to improve CTR (deep position => low CTR).
  - position_potential zeroes at pos >=18 => anything that can't realistically
    reach page 1 soon scores 0 and should NOT consume your time.

Worked example (user's spec): pos 11, 12,000 impr, 0.3% CTR
    target_pos=10, expected_ctr(10)=0.024, ctr_gap=0.021
    position_potential=(18-11)/18=0.389
    Score = 12000 * 0.021 * 0.389 = 98.0   <-- matches the spec exactly

Loads scripts/gsc_top100.json (produced by scripts/gsc_top100.py) and writes a
ranked report to the Obsidian vault.
"""
import os, json, datetime

ROOT = r'C:\Users\prin-win\aitoolssolo'
SRC = os.path.join(ROOT, 'scripts', 'gsc_top100.json')
VAULT_REPORT = r'D:\Local Cloud\Obsidian\01 - Projects\AIT Solo\reports\opportunity-score.md'
JSON_OUT = os.path.join(ROOT, 'scripts', 'opportunity_score.json')
NOW = datetime.datetime.now()

# Organic CTR by position (reasonable averages; tune to taste).
CTR_CURVE = [
    (1, 0.300), (2, 0.155), (3, 0.100), (4, 0.075), (5, 0.058),
    (6, 0.047), (7, 0.039), (8, 0.033), (9, 0.028), (10, 0.024),
    (11, 0.020), (12, 0.017), (13, 0.015), (14, 0.013), (15, 0.012),
    (20, 0.008), (25, 0.006), (30, 0.0045), (40, 0.0030), (50, 0.0020),
    (75, 0.0012), (100, 0.0010),
]


def expected_ctr(pos):
    if pos <= CTR_CURVE[0][0]:
        return CTR_CURVE[0][1]
    if pos >= CTR_CURVE[-1][0]:
        return CTR_CURVE[-1][1]
    for i in range(len(CTR_CURVE) - 1):
        p0, c0 = CTR_CURVE[i]
        p1, c1 = CTR_CURVE[i + 1]
        if p0 <= pos <= p1:
            t = (pos - p0) / (p1 - p0)
            return c0 + t * (c1 - c0)
    return CTR_CURVE[-1][1]


def position_potential(pos):
    return max(0.0, min(1.0, (18.0 - pos) / 18.0))


def score(impr, ctr, pos):
    target_pos = 10.0 if pos > 10 else max(1.0, pos - 2.0)
    ctr_gap = max(0.0, expected_ctr(target_pos) - ctr)
    pp = position_potential(pos)
    return impr * ctr_gap * pp, ctr_gap, pp


def main():
    with open(SRC, encoding='utf-8') as f:
        data = json.load(f)
    rows = data['top100']

    # Drop GSC operator-junk (quoted phrases, -site: exclusions, site: and
    # other search operators are query artifacts, not real search intent).
    def is_junk(q):
        ql = q.lower()
        return ('site:' in ql) or ('-' in ql and ' -' in (' ' + ql)) or ql.count('"') >= 2
    clean = [r for r in rows if not is_junk(r['query'])]

    # Score each clean query
    scored = []
    for r in clean:
        s, gap, pp = score(r['impr'], r['ctr'], r['pos'])
        scored.append({**r, 'score': round(s, 3), 'ctr_gap': round(gap, 4),
                       'pos_potential': round(pp, 3)})
    scored.sort(key=lambda x: -x['score'])

    # Aggregate by landing page (many query variants hit one page).
    by_page = {}
    for r in scored:
        p = r['page']
        if p not in by_page:
            by_page[p] = {'page': p, 'impr': 0, 'clicks': 0,
                          'best_pos': 100, 'queries': []}
        agg = by_page[p]
        agg['impr'] += r['impr']
        agg['clicks'] += r['clicks']
        agg['best_pos'] = min(agg['best_pos'], r['pos'])
        agg['queries'].append(r['query'])
    page_scores = []
    for p, agg in by_page.items():
        # Page-level score uses best position (closest to page 1) and summed impressions.
        s, gap, pp = score(agg['impr'], 0.0, agg['best_pos'])
        page_scores.append({**agg, 'score': round(s, 3), 'ctr_gap': round(gap, 4),
                            'pos_potential': round(pp, 3)})
    page_scores.sort(key=lambda x: -x['score'])

    ex_s, ex_gap, ex_pp = score(12000, 0.003, 11.0)

    lines = []
    lines.append(f"---\ntitle: AIT Solo - Opportunity Score\ntags: [seo, opportunity, aitoolssolo]\n"
                 f"date: {NOW.strftime('%Y-%m-%d')}\nsource: scripts/opportunity_score.py\n---\n")
    lines.append(f"# Opportunity Score - ranked by needle-moving potential\n")
    lines.append(f"Generated {NOW.strftime('%Y-%m-%d %H:%M')} from GSC window "
                 f"{data.get('start')} -> {data.get('end')} ({data.get('total_queries')} distinct queries; "
                 f"{len(clean)} after junk-query filter).\n")
    lines.append("\n## Formula\n")
    lines.append("```\nOpportunity Score = impressions x ctr_gap x position_potential\n"
                 "  ctr_gap           = expected_ctr(target_pos) - current_ctr   (>=0)\n"
                 "  target_pos        = 10 if pos>10 else max(1, pos-2)\n"
                 "  position_potential= clamp((18-pos)/18, 0, 1)   (0 at pos>=18)\n"
                 "```\n")
    lines.append(f"\n**Worked example (spec):** pos 11, 12,000 impr, 0.3% CTR "
                 f"-> Score = **{ex_s:.1f}** (ctr_gap={ex_gap:.3f}, pos_potential={ex_pp:.3f}). "
                 f"Matches the target of ~98.\n")
    lines.append("\n> Note: this site currently has only ~2,146 impressions/week site-wide, so "
                 "absolute scores are small. The **relative ranking** is what matters - it tells you "
                 "which page to touch first when you do have a moment, and the scores will grow as "
                 "impressions grow.\n")
    lines.append("\n## Priority #1 (page level)\n")
    tp = page_scores[0]
    lines.append(f"> **`{tp['page'].replace('https://www.aitoolssolo.com','')}`** "
                 f"\n> Best position {tp['best_pos']} | {tp['impr']} impr (summed) | "
                 f"**Score {tp['score']}**\n> Queries: {', '.join(q[:30] for q in tp['queries'][:5])}\n")
    lines.append("\n## Top 15 pages by Opportunity Score\n")
    lines.append("| # | Score | Page | Best Pos | Impr | Pos pot |\n|---|---:|---|---:|---:|---:|")
    for i, r in enumerate(page_scores[:15], 1):
        page = r['page'].replace('https://www.aitoolssolo.com', '')
        lines.append(f"| {i} | {r['score']} | {page} | {r['best_pos']} | {r['impr']} | {r['pos_potential']} |")
    lines.append("\n## Top 15 queries by Opportunity Score\n")
    lines.append("| # | Score | Query | Pos | Impr | Page |\n|---|---:|---|---:|---:|---|")
    for i, r in enumerate(scored[:15], 1):
        page = r['page'].replace('https://www.aitoolssolo.com', '')
        lines.append(f"| {i} | {r['score']} | {r['query'][:40]} | {r['pos']} | {r['impr']} | {page} |")
    lines.append("\n## How to read this\n")
    lines.append("- **High score + best pos 8-18** = do it now (push onto page 1 with internal links + on-page tweaks).")
    lines.append("- **Score 0** (best pos >=18 or no CTR gap) = ignore for now, no matter how many impressions.")
    lines.append("- A page at pos 45 with 20 impr scores **0** - it cannot reach page 1 soon, so it should not consume your time.")
    lines.append("- Scores scale with traffic; what matters is the **relative ranking**, not the absolute number.")
    lines.append("\n> Regenerate weekly: `python scripts/gsc_top100.py && python scripts/opportunity_score.py`")
    open(VAULT_REPORT, 'w', encoding='utf-8').write('\n'.join(lines))
    json.dump({'queries': scored, 'pages': page_scores}, open(JSON_OUT, 'w'), indent=2)
    print(f"Opportunity Score: {len(scored)} queries, {len(page_scores)} pages -> {VAULT_REPORT}")
    print(f"Priority #1 page: {tp['page']} (best pos {tp['best_pos']}, {tp['impr']} impr, score {tp['score']})")
    print(f"Worked example score: {ex_s:.1f} (spec target ~98)")
    return page_scores


if __name__ == '__main__':
    main()
