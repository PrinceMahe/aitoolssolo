#!/usr/bin/env python3
"""Phase 2 Sprint 1 — landing-page engine + link-equity data.

Builds content/landing/*.md (type=landing, indexable) AND emits data/landing.yaml
so every template can resolve tool/category/tag -> landing slug deterministically.

Also computes sibling cross-links (tag landings within the same primary category)
so no landing page ends up with <10 inbound internal links and none are orphaned.

Output:
  content/landing/<slug>.md     front matter + cluster of tool slugs
  data/landing.yaml             lookup maps for templates + audit script

Usage:
  python scripts/build_landing.py
  python scripts/build_landing.py --dry-run
"""
import os
import glob
import yaml
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "content", "landing")
LAND_YAML = os.path.join(DATA, "landing.yaml")
LAND_JSON = os.path.join(DATA, "landing.json")

MIN_TAG_TOOLS = 5
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
    by_cat, by_tag = {}, {}
    for slug, t in tools.items():
        by_cat.setdefault(t.get("category", ""), []).append(slug)
    for slug, t in tools.items():
        for tag in (t.get("tags") or []):
            by_tag.setdefault(tag, []).append(slug)

    cat_landing, tag_landing = {}, {}
    # category landings
    for cat, slugs in by_cat.items():
        if not cat or len(slugs) < 3:
            continue
        name = CAT_NAME.get(cat, cat.title())
        cat_landing[cat] = {
            "slug": f"ai-tools-for-{slugify(name)}",
            "name": name,
            "tools": slugs,
        }
    # tag landings
    for tag, slugs in sorted(by_tag.items(), key=lambda kv: -len(kv[1])):
        if tag in STOP_TAGS or len(slugs) < MIN_TAG_TOOLS:
            continue
        tag_landing[tag] = {
            "slug": f"best-ai-tools-for-{tag}",
            "tools": slugs,
            # primary category = category of the first tool carrying this tag
            "category": tools[slugs[0]].get("category", ""),
        }
    return cat_landing, tag_landing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tools = load_tools()
    cat_landing, tag_landing = build_clusters(tools)

    # sibling tags: other tag landings sharing the same primary category
    cat_to_tags = {}
    for tag, info in tag_landing.items():
        cat_to_tags.setdefault(info["category"], []).append(tag)
    tag_siblings = {}
    for tag, info in tag_landing.items():
        sibs = [t for t in cat_to_tags.get(info["category"], []) if t != tag]
        tag_siblings[tag] = sibs

    # popular = top 12 tag landings by tool count (store full slugs)
    popular = [tag_landing[t]["slug"] for t, _ in sorted(
        tag_landing.items(), key=lambda kv: -len(kv[1]["tools"]))[:12]]

    print(f"Tools: {len(tools)}  Categories: {len(cat_landing)}  "
          f"Tags: {len(tag_landing)}  Popular: {len(popular)}")

    if args.dry_run:
        for c, i in cat_landing.items():
            print(f"  [cat ] {i['slug']:40} {i['name']} ({len(i['tools'])} tools)")
        for t, i in tag_landing.items():
            print(f"  [tag ] {i['slug']:40} {t} ({len(i['tools'])} tools, "
                  f"sibs={len(tag_siblings[t])})")
        return

    # write landing content pages
    os.makedirs(OUT, exist_ok=True)
    written = 0
    for c, i in cat_landing.items():
        desc = (f"The best AI tools for {c.replace('-', ' ')} — curated for "
                f"solopreneurs. Compare features, pricing, and ratings in one place.")
        text = FM.format(title=f"Best AI Tools for {i['name']}", desc=desc,
                         slug=i["slug"], tools=", ".join(i["tools"]), kind="category")
        with open(os.path.join(OUT, f"{i['slug']}.md"), "w", encoding="utf-8") as f:
            f.write(text)
        written += 1
    for t, i in tag_landing.items():
        label = t.replace("-", " ").title()
        desc = (f"The best AI tools for {t.replace('-', ' ')} — curated for "
                f"solopreneurs. Compare features, pricing, and ratings in one place.")
        text = FM.format(title=f"Best AI Tools for {label}", desc=desc,
                         slug=i["slug"], tools=", ".join(i["tools"]), kind="tag")
        with open(os.path.join(OUT, f"{i['slug']}.md"), "w", encoding="utf-8") as f:
            f.write(text)
        written += 1

    # emit data/landing.json for templates + audit.
    # JSON (not YAML) because Hugo's YAML loader silently returns nil for some
    # list-valued keys (observed: popular_landings) while Python parses fine.
    landing_data = {
        "cat_landing": {c: i["slug"] for c, i in cat_landing.items()},
        "tag_landing": {t: i["slug"] for t, i in tag_landing.items()},
        "tag_category": {t: i["category"] for t, i in tag_landing.items()},
        "tag_siblings": tag_siblings,
        "all_cat_landings": [i["slug"] for i in cat_landing.values()],
        "all_tag_landings": [i["slug"] for i in tag_landing.values()],
        "popular_landings": popular,
        "cat_tags": {c: cat_to_tags.get(c, []) for c in cat_landing},
    }
    import json
    with open(LAND_JSON, "w", encoding="utf-8") as f:
        json.dump(landing_data, f, indent=2, ensure_ascii=False)

    print(f"Wrote {written} landing pages + data/landing.json")


if __name__ == "__main__":
    main()
