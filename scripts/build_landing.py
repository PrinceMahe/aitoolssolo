#!/usr/bin/env python3
"""Phase 2 — Authority & Scale: build indexable "Best AI Tools for [X]" landing hubs.

The site already has 239 tool pages, 194 use-cases (noindex) and 3,566 comparisons
(noindex). Those thin layers stay noindex,follow per the proven Phase 1 discipline.

This script adds a NEW indexable content type (`landing`) that clusters the existing
239-tool dataset into high-intent hubs:
  - one hub per category  (e.g. "Best AI Tools for Writing & Content")
  - one hub per top tag    (e.g. "Best AI Tools for SEO", "Best AI Tools for Video")
Each hub:
  - is type=landing  -> NOT in the noindex list (layouts/partials/head.html) -> indexable
  - links out to every tool in the cluster (internal-linking / WS2) and to the
    /tools/ index + its category page
  - is generated deterministically (re-runnable, idempotent)

Outputs: content/landing/<slug>.md

Usage:
  python scripts/build_landing.py            # write files
  python scripts/build_landing.py --dry-run  # count only
"""
import os
import sys
import glob
import yaml
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "content", "landing")

# Tags below this frequency make thin hubs -> skip (keep indexable set quality).
MIN_TAG_TOOLS = 5
# Tags that are too generic / not a real "use case" intent.
STOP_TAGS = {"ai", "api", "generator", "tool", "tools", "app", "apps"}

CAT_NAME = {
    "writing": "Writing & Content",
    "image": "Image & Design",
    "video": "Video & Audio",
    "automation": "Automation & Workflow",
    "productivity": "Productivity & Research",
    "coding": "Coding & Build",
    "marketing": "Marketing & Growth",
    "business": "Business & Operations",
}


def load_tools():
    tools = {}
    for p in sorted(glob.glob(os.path.join(DATA, "tools", "*.yaml"))):
        with open(p, encoding="utf-8") as f:
            t = yaml.safe_load(f)
        tools[t["slug"]] = t
    return tools


def slugify(s):
    return s.strip().lower().replace(" & ", "-").replace(" ", "-").replace("/", "-")


def build_clusters(tools):
    # category clusters
    by_cat = {}
    for slug, t in tools.items():
        by_cat.setdefault(t.get("category", ""), []).append(slug)
    # tag clusters
    by_tag = {}
    for slug, t in tools.items():
        for tag in (t.get("tags") or []):
            by_tag.setdefault(tag, []).append(slug)

    clusters = []
    seen = set()
    # categories first (always strong intent)
    for cat, slugs in by_cat.items():
        if not cat or len(slugs) < 3:
            continue
        name = CAT_NAME.get(cat, cat.title())
        clusters.append((f"cat-{cat}", f"Best AI Tools for {name}",
                         f"ai-tools-for-{slugify(name)}", slugs, "category"))
    # top tags
    for tag, slugs in sorted(by_tag.items(), key=lambda kv: -len(kv[1])):
        if tag in STOP_TAGS or len(slugs) < MIN_TAG_TOOLS:
            continue
        key = f"tag-{tag}"
        if key in seen:
            continue
        seen.add(key)
        label = tag.replace("-", " ").title()
        clusters.append((key, f"Best AI Tools for {label}",
                         f"best-ai-tools-for-{tag}", slugs, "tag"))
    return clusters


FM = """---
title: "{title}"
description: "{desc}"
type: "landing"
slug: "{slug}"
landing_tools: [{tools}]
landing_kind: "{kind}"
draft: false
---
# {title}

{desc}

Browse the full stack of vetted AI tools and pick the ones that fit your one-person
business. Every tool links to a deep-dive page with pricing, features, and ratings.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tools = load_tools()
    clusters = build_clusters(tools)
    print(f"Tools: {len(tools)}  Clusters: {len(clusters)}")

    if args.dry_run:
        for key, title, slug, slugs, kind in clusters:
            print(f"  [{kind:8}] {slug:40} {title}  ({len(slugs)} tools)")
        return

    os.makedirs(OUT, exist_ok=True)
    written = 0
    for key, title, slug, slugs, kind in clusters:
        desc = (f"The best AI tools for {title.replace('Best AI Tools for ', '').lower()} "
                f"— curated for solopreneurs. Compare features, pricing, and ratings "
                f"in one place.")
        text = FM.format(
            title=title,
            desc=desc,
            slug=slug,
            tools=", ".join(slugs),
            kind=kind,
        )
        path = os.path.join(OUT, f"{slug}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        written += 1
    print(f"Wrote {written} landing pages to content/landing/")


if __name__ == "__main__":
    main()
