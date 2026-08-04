#!/usr/bin/env python3
"""Pre-deploy guard for the Bucket A index allowlist.

Fails (exit 1) if any slug in params.bucketA.list in hugo.toml:
  (a) has no corresponding content/comparisons/<slug>.md file, or
  (b) the file is thinner than MIN_LINES (would be a thin page going indexable)

Run in CI before `hugo` build, or as a git pre-push hook.

Usage: python scripts/check_bucket_a_guard.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HUGO = os.path.join(ROOT, "hugo.toml")
COMPARISONS = os.path.join(ROOT, "content", "comparisons")

MIN_LINES = 40  # below this = thin; shouldn't be indexable

# Parse params.bucketA.list from hugo.toml (TOML array under [params.bucketA])
text = open(HUGO, encoding="utf-8").read()
m = re.search(r"\[params\.bucketA\]\s*list\s*=\s*\[(.*?)\]", text, re.S)
if not m:
    print("ERROR: could not find params.bucketA.list in hugo.toml")
    sys.exit(1)

slugs = re.findall(r'"([^"]+)"', m.group(1))
if not slugs:
    print("ERROR: bucketA.list is empty")
    sys.exit(1)

errors = []
for slug in slugs:
    path = os.path.join(COMPARISONS, f"{slug}.md")
    if not os.path.isfile(path):
        errors.append(f"MISSING FILE: comparisons/{slug}.md (allowlisted but no content)")
        continue
    n = sum(1 for _ in open(path, encoding="utf-8"))
    if n < MIN_LINES:
        errors.append(f"THIN PAGE ({n}L < {MIN_LINES}L): comparisons/{slug}.md — would go indexable as thin")

print(f"Bucket A allowlist: {len(slugs)} slugs")
if errors:
    print("\n❌ GUARD FAILED — do NOT deploy until fixed:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"✅ All {len(slugs)} allowlisted pages exist and meet the {MIN_LINES}-line minimum.")
print("Safe to deploy (noindex guard will index only these).")
