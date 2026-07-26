import re, glob, json, os
fs = sorted(glob.glob('public/posts/*/index.html'))
oob = 0
checked = 0
posts_with = 0
for f in fs:
    data = open(f, encoding='utf-8', errors='replace').read()
    found = False
    for m in re.finditer(r'<script type=application/ld\+json>(.*?)</script>', data, re.S):
        try:
            d = json.loads(m.group(1))
        except Exception:
            continue
        if d.get('@type') != 'FAQPage':
            continue
        found = True
        for q in d['mainEntity']:
            checked += 1
            w = len(q['acceptedAnswer']['text'].split())
            if not (40 <= w <= 80):
                oob += 1
                print("OOB", w, q['name'][:35])
    if found:
        posts_with += 1
print(f"Posts with FAQPage: {posts_with} | Questions checked: {checked} | out of 40-80 range: {oob}")
