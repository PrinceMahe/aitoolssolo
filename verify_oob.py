import glob, re

fs = sorted(glob.glob('content/posts/*.md'))
oob = 0
checked = 0
for f in fs:
    raw = open(f, encoding='utf-8', errors='replace').read()
    m = re.search(r'## FAQ.*?(?=\n## |\Z)', raw, re.S)
    if not m: continue
    sec = m.group(0)
    blocks = re.split(r'### Q:\s*', sec)
    for b in blocks[1:]:
        lines = b.strip().split("\n")
        a = "\n".join(lines[1:]).strip()
        if not a: continue
        w = len(a.split())
        checked += 1
        if not (40 <= w <= 80):
            oob += 1
            print("OOB", w, lines[0][:40])
print(f"FAQ answers checked (source): {checked} | out of 40-80: {oob}")
