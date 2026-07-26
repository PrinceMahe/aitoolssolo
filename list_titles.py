import glob, re, os
posts = sorted(glob.glob('content/posts/*.md'))
print(f"Total post files: {len(posts)}")
long = []
all_titles = []
for f in posts:
    t = open(f, encoding='utf-8', errors='replace').read()
    m = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', t, re.M)
    if m:
        title = m.group(1)
        n = len(title)
        all_titles.append((os.path.basename(f), title, n))
        if n > 60:
            long.append((os.path.basename(f), title, n))
print(f"Titles > 60 chars: {len(long)}  (total posts: {len(all_titles)})")
print("--- LONG TITLES ---")
for fn, title, n in long:
    print(f"{n:3d} | {title}")
