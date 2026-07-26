import glob, os, re, json

posts = sorted(glob.glob('content/posts/*.md'))
have_faq = []
need_faq = []
for f in posts:
    t = open(f, encoding='utf-8', errors='replace').read()
    slug = os.path.basename(f).replace('.md','')
    if slug == '_index':
        continue
    if re.search(r'^##\s+FAQ', t, re.M) or '### Q:' in t or re.search(r'^\*\*[0-9]+\.', t, re.M):
        have_faq.append(slug)
    else:
        need_faq.append(slug)

print(f"Posts WITH faq: {len(have_faq)}")
for s in have_faq: print("  +", s)
print(f"\nPosts NEEDING faq: {len(need_faq)}")
for s in need_faq: print("  -", s)

json.dump({'have': have_faq, 'need': need_faq}, open('faq_status.json','w'), indent=2)
