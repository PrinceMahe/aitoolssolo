import json, os, re

faqs = json.load(open("faq_content.json", encoding="utf-8"))

def wordcount(s):
    return len(s.split())

report = []
for slug, items in faqs.items():
    fn = f"content/posts/{slug}.md"
    if not os.path.exists(fn):
        print(f"MISSING {fn}")
        continue
    raw = open(fn, encoding="utf-8", errors="replace").read()
    # Build FAQ section
    lines = ["", "## FAQ", ""]
    for q, a in items:
        wc = wordcount(a)
        if not (40 <= wc <= 80):
            print(f"WARN {slug}: answer {wc} words (target 40-80): {q[:40]}")
        lines.append(f"### Q: {q}")
        lines.append("")
        lines.append(a)
        lines.append("")
    section = "\n".join(lines).rstrip() + "\n"
    # Append before any existing closing; just append at end
    if raw.endswith("\n"):
        new_raw = raw.rstrip("\n") + "\n" + section
    else:
        new_raw = raw + "\n" + section
    open(fn, "w", encoding="utf-8").write(new_raw)
    report.append({"slug": slug, "qs": len(items), "avg_words": sum(wordcount(a) for _,a in items)//len(items)})

print(f"Appended FAQ to {len(report)} posts")
avg = sum(r['avg_words'] for r in report)//len(report)
print(f"Average answer length: {avg} words (target 40-80)")
json.dump(report, open("faq_applied.json","w"), indent=2)
