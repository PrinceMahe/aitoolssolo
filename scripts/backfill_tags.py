#!/usr/bin/env python3
"""Backfill clean, meaningful tags on existing posts using the same logic as
scripts/generate_post.py::derive_tags. Run once to fix the legacy junk tags
(e.g. ["the","best","tools","for","one"]) so related-posts matching works."""
import os, re, json, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
import generate_post as g

posts_dir = os.path.join(os.path.dirname(__file__), '..', 'content', 'posts')
changed = 0
for fn in sorted(os.listdir(posts_dir)):
    if not fn.endswith('.md'):
        continue
    path = os.path.join(posts_dir, fn)
    text = open(path, encoding='utf-8').read()
    m = re.search(r'title:\s*"([^"]+)"', text)
    if not m:
        continue
    title = m.group(1)
    # Infer the primary keyword from the title itself for backfill.
    kw = g.primary_keyword(title)
    tags = g.derive_tags(title, kw)
    new_line = 'tags: [' + ', '.join(json.dumps(t) for t in tags) + ']'
    new_text, n = re.subn(r'(?m)^tags:\s*\[.*\]\s*$', new_line, text, count=1)
    if n:
        open(path, 'w', encoding='utf-8').write(new_text)
        changed += 1
        print(f'{fn}: {new_line}')
print(f'\nBackfilled tags on {changed} posts.')
