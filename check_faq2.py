import re, glob, json, os
fs = sorted(glob.glob('public/posts/*/index.html'))
oob = []
for f in fs:
    slug = os.path.basename(os.path.dirname(f))
    h = open(f, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'<script type=application/ld\+json>(.*?)</script>', h, re.S):
        try:
            d = json.loads(m.group(1))
        except Exception:
            continue
        if d.get('@type') != 'FAQPage':
            continue
        for q in d['mainEntity']:
            w = len(q['acceptedAnswer']['text'].split())
            if not (40 <= w <= 80):
                oob.append((slug, w, q['name'][:40]))
for s, w, n in oob:
    print(f"{w:3d}w  {s[-45:]}  Q:{n}")
print(f"\nTotal OOB: {len(oob)}")
