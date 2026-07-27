#!/usr/bin/env python3
"""Inject `bucket_a:` front-matter into each AIT Solo post, mapping the post
to its most relevant Bucket A (GSC pos 8-15) comparison pages.

Bucket A pages (slug -> /comparisons/<slug>/):
  mem-vs-memair, claude-vs-jenni, bonsai-vs-indy, expensify-vs-float,
  chatgpt-vs-clickup, canva-vs-vectorizer, luma-vs-playground,
  freshbooks-vs-square, luma-dream-vs-submagic, browserbear-vs-relay
Plus 2 posts that ARE bucket A targets themselves (makecom-scam, affiliate-2025).

Mapping is keyword-based on filename + topic. Conservative: 1-3 links each.
"""
import os, re, glob

POSTS = r'C:\Users\prin-win\aitoolssolo\content\posts'

# Bucket A comparison slugs
A = {
    'mem-vs-memair': 'AI note/memory tools',
    'claude-vs-jenni': 'AI writing assistants',
    'bonsai-vs-indy': 'freelance/invocing CRM',
    'expensify-vs-float': 'expense/finance tracking',
    'chatgpt-vs-clickup': 'AI chat vs project mgmt',
    'canva-vs-vectorizer': 'design/vector tools',
    'luma-vs-playground': 'AI image generation',
    'freshbooks-vs-square': 'accounting/payments',
    'luma-dream-vs-submagic': 'AI video/subtitles',
    'browserbear-vs-relay': 'browser automation',
}

# (post filename fragment) -> [bucket A slugs]
MAP = {
    'jasper-ai-vs-chatgpt-for-blog-writing': ['claude-vs-jenni', 'chatgpt-vs-clickup'],
    'the-best-ai-writing-tool-for-affiliate-content': ['claude-vs-jenni', 'canva-vs-vectorizer'],
    'the-best-ai-writing-tool-for-solopreneurs': ['claude-vs-jenni'],
    'the-best-ai-tools-for-one-person-business': ['claude-vs-jenni', 'expensify-vs-float', 'freshbooks-vs-square'],
    'best-ai-tools-for-solopreneurs': ['claude-vs-jenni', 'chatgpt-vs-clickup', 'luma-vs-playground'],
    'best-ai-tools-for-freelance-writers': ['claude-vs-jenni', 'bonsai-vs-indy'],
    'how-to-build-a-one-person-content-agency': ['claude-vs-jenni', 'chatgpt-vs-clickup'],
    'beehiiv-vs-substack': ['bonsai-vs-indy'],
    'beehiiv-vs-convertkit': ['bonsai-vs-indy'],
    'the-best-email-platform': ['bonsai-vs-indy'],
    'beehiiv-free-plan': ['bonsai-vs-indy'],
    'descript-vs-riverside': ['luma-dream-vs-submagic', 'luma-vs-playground'],
    'riversidefm-review': ['luma-dream-vs-submagic'],
    'descript-review': ['luma-dream-vs-submagic'],
    'why-descript-pricing': ['luma-dream-vs-submagic'],
    'why-your-3am-youtube-video': ['luma-dream-vs-submagic'],
    'hostinger-vs-bluehost': ['freshbooks-vs-square'],
    'the-20month-hosting': ['freshbooks-vs-square'],
    'the-unshackled-truth-hosting': ['freshbooks-vs-square'],
    'why-hosting-speed': ['freshbooks-vs-square'],
    'makecom-review-is-it-worth-it': ['chatgpt-vs-clickup', 'expensify-vs-float'],
    'makecom-vs-n8n': ['chatgpt-vs-clickup'],
    'are-makecom-pricing': ['expensify-vs-float'],
    'the-best-no-code-automation-tool-2025': ['chatgpt-vs-clickup', 'browserbear-vs-relay'],
    'the-best-no-code-automation-tool-for-ecommerce': ['chatgpt-vs-clickup', 'browserbear-vs-relay'],
    'why-your-workflow-is-dying': ['chatgpt-vs-clickup', 'browserbear-vs-relay'],
    'how-to-analyze-any-web-page': ['browserbear-vs-relay'],
    'jasper-ai-for-product-descriptions': ['claude-vs-jenni', 'canva-vs-vectorizer'],
    'jasper-ai-review-for-blog-writing': ['claude-vs-jenni'],
    'youre-12-hours-away': ['chatgpt-vs-clickup', 'claude-vs-jenni'],
    'best-ai-tools-for-freelance-writers-who-want': ['bonsai-vs-indy', 'claude-vs-jenni'],
}

def links_for(fname):
    base = os.path.basename(fname)
    for frag, slugs in MAP.items():
        if frag in base:
            return ['/comparisons/%s/' % s for s in slugs]
    return []

count = 0
for f in glob.glob(os.path.join(POSTS, '*.md')):
    base = os.path.basename(f)
    if base == '_index.md':
        continue
    links = links_for(f)
    if not links:
        continue
    with open(f, encoding='utf-8') as fh:
        txt = fh.read()
    # Only inject if not already present
    if 'bucket_a:' in txt:
        print(f"skip (exists): {base}")
        continue
    # YAML front matter is between first --- and second ---
    m = re.match(r'^(---\n)(.*?)(\n---\n)', txt, re.DOTALL)
    if not m:
        print(f"no FM: {base}")
        continue
    fm = m.group(2)
    # Append bucket_a as a list
    lines = ['bucket_a:']
    for l in links:
        lines.append(f'  - "{l}"')
    new_fm = fm + '\n' + '\n'.join(lines) + '\n'
    new_txt = txt[:m.start(2)] + new_fm + txt[m.end(2):]
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(new_txt)
    count += 1
    print(f"added {len(links)} links -> {base}")

print(f"\nDone. Modified {count} posts.")
