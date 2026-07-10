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

    # Section indexes so /tools/, /categories/, /alternatives/ render & sitemap
    for sect, title in [
        ("tools", "AI Tools"),
        ("categories", "Tool Categories"),
        ("alternatives", "Alternatives"),
    ]:
        idx = os.path.join(OUT, sect, "_index.md")
        write(
            idx,
            f'---\ntitle: "{title}"\ndescription: "{title} on AI Tools Solo"\ndraft: false\n---\n',
        )

    print(f"\nDone. {len(tools)} tools, {len(cats)} categories, "
          f"{len(tools)} alternatives pages.")


if __name__ == "__main__":
    main()
