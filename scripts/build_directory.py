#!/usr/bin/env python3
"""Build the AI Tools Solo directory from data/ (programmatic SEO engine).

Reads data/tools/*.yaml and data/categories.yaml, then writes content pages:
  content/tools/<slug>.md          type=tool
  content/categories/<slug>.md     type=category
  content/alternatives/<slug>.md   type=alternatives

Layouts render the actual HTML from .Site.Data, so these content files are
just front-matter stubs + a tiny rendered hint. Re-run after editing data.
"""
import os
import sys
import glob
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "content")

FM = """---
title: "{title}"
description: "{desc}"
type: "{ctype}"
slug: "{slug}"
tool: "{slug}"
draft: false
---
"""


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", os.path.relpath(path, ROOT))


def main():
    tools = {}
    for p in sorted(glob.glob(os.path.join(DATA, "tools", "*.yaml"))):
        t = load_yaml(p)
        tools[t["slug"]] = t
    cats = {c["slug"]: c for c in load_yaml(os.path.join(DATA, "categories.yaml"))}

    # Tools
    for slug, t in tools.items():
        title = t["name"]
        desc = t.get("summary", "")
        body = (
            f"# {title}\n\n{desc}\n"
        )
        write(
            os.path.join(OUT, "tools", f"{slug}.md"),
            FM.format(title=title, desc=desc, ctype="tool", slug=slug) + body,
        )

    # Categories (aggregator)
    for slug, c in cats.items():
        title = c["name"]
        desc = c.get("description", "")
        body = f"# {title}\n\n{desc}\n"
        write(
            os.path.join(OUT, "categories", f"{slug}.md"),
            FM.format(title=title, desc=desc, ctype="category", slug=slug) + body,
        )

    # Alternatives ("X alternatives" — high-volume programmatic pages)
    for slug, t in tools.items():
        title = f"{t['name']} Alternatives"
        desc = f"Best {t['name']} alternatives for solopreneurs: compare features, pricing, and use cases."
        body = f"# {title}\n\n{desc}\n"
        write(
            os.path.join(OUT, "alternatives", f"{slug}.md"),
            FM.format(title=title, desc=desc, ctype="alternatives", slug=slug) + body,
        )

    # Comparisons ("X vs Y" — same-category pairs; high-intent programmatic pages)
    # Group tools by category, then emit every within-category pair once
    # (slug order sorted so chatgpt-vs-claude == claude-vs-chatgpt).
    by_cat = {}
    for slug, t in tools.items():
        by_cat.setdefault(t.get("category", ""), []).append(slug)
    pair_n = 0
    for cat, slugs in by_cat.items():
        slugs = sorted(slugs)
        for i in range(len(slugs)):
            for j in range(i + 1, len(slugs)):
                a, b = tools[slugs[i]], tools[slugs[j]]
                cslug = f"{a['slug']}-vs-{b['slug']}"
                title = f"{a['name']} vs {b['name']}"
                desc = (f"{a['name']} vs {b['name']}: compare pricing, features, "
                        f"ratings, and best use cases to pick the right tool for your "
                        f"one-person business.")
                body = f"# {title}\n\n{desc}\n"
                comp_fm = (
                    f'---\n'
                    f'title: "{title}"\n'
                    f'description: "{desc}"\n'
                    f'type: "comparison"\n'
                    f'slug: "{cslug}"\n'
                    f'tool_a: "{a["slug"]}"\n'
                    f'tool_b: "{b["slug"]}"\n'
                    f'draft: false\n'
                    f'---\n'
                )
                write(
                    os.path.join(OUT, "comparisons", f"{cslug}.md"),
                    comp_fm + body,
                )
                pair_n += 1

    # Use cases ("There's an AI for X") — the TAIAF core: tag-driven hubs.
    # Each tag becomes /use-cases/<tag>/ listing every tool carrying it.
    tags = {}
    for slug, t in tools.items():
        for tag in (t.get("tags") or []):
            tags.setdefault(tag, []).append(slug)
    for tag, slugs in sorted(tags.items()):
        title = f"AI for {tag.title()}"
        desc = (f"The best AI tools for {tag.replace('-', ' ')} — curated for "
                f"solopreneurs. Compare features, pricing, and ratings in one place.")
        uc_fm = (
            f'---\n'
            f'title: "{title}"\n'
            f'description: "{desc}"\n'
            f'type: "usecase"\n'
            f'slug: "{tag}"\n'
            f'draft: false\n'
            f'---\n'
        )
        write(
            os.path.join(OUT, "use-cases", f"{tag}.md"),
            uc_fm + f"# {title}\n\n{desc}\n",
        )

    # Section indexes so /tools/, /categories/, /alternatives/, /use-cases/ render & sitemap
    for sect, title in [
        ("tools", "AI Tools"),
        ("categories", "Tool Categories"),
        ("alternatives", "Alternatives"),
        ("comparisons", "Comparisons"),
        ("use-cases", "Use Cases"),
    ]:
        idx = os.path.join(OUT, sect, "_index.md")
        write(
            idx,
            f'---\ntitle: "{title}"\ndescription: "{title} on AI Tools Solo"\ndraft: false\n---\n',
        )

    print(f"\nDone. {len(tools)} tools, {len(cats)} categories, "
          f"{len(tools)} alternatives pages, {pair_n} comparison pages, "
          f"{len(tags)} use-case pages.")


if __name__ == "__main__":
    main()
