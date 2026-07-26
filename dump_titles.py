import glob, re, os, json
posts = sorted(glob.glob('content/posts/*.md'))
data = []
for f in posts:
    t = open(f, encoding='utf-8', errors='replace').read()
    m = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', t, re.M)
    slug_m = re.search(r'^slug:\s*["\']?(.*?)["\']?\s*$', t, re.M)
    if m:
        title = m.group(1)
        slug = slug_m.group(1) if slug_m else os.path.basename(f).replace('.md','')
        data.append({'file': os.path.basename(f), 'slug': slug, 'title': title, 'len': len(title)})
print(json.dumps(data, ensure_ascii=False, indent=2))
print(f"\nTotal: {len(data)}")
over = [d for d in data if d['len']>60]
print(f"Over 60: {len(over)}")
PYEOF
