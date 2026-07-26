import json, os, re

faqs = json.load(open("faq_content.json", encoding="utf-8"))

def wordcount(s):
    return len(s.split())

def strip_existing_faq(raw):
    # Remove an existing "## FAQ" section (everything from a line starting "## FAQ" to EOF)
    lines = raw.split("\n")
    out = []
    in_faq = False
    for ln in lines:
        if re.match(r'^##\s+FAQ(\s|:|$)', ln):
            in_faq = True
            continue
        if in_faq:
            # stop if a new H2 appears (shouldn't happen since FAQ is last, but be safe)
            if re.match(r'^##\s+', ln) and not re.match(r'^###\s+', ln):
                in_faq = False
                out.append(ln)
                continue
            continue
        out.append(ln)
    return "\n".join(out).rstrip() + "\n"

report = []
for slug, items in faqs.items():
    fn = f"content/posts/{slug}.md"
    if not os.path.exists(fn):
        print(f"MISSING {fn}")
        continue
    raw = open(fn, encoding="utf-8", errors="replace").read()
    raw = strip_existing_faq(raw)
    lines = ["", "## FAQ", ""]
    for q, a in items:
        wc = wordcount(a)
        if not (40 <= wc <= 80):
            print(f"WARN {slug}: {wc} words: {q[:38]}")
        lines.append(f"### Q: {q}")
        lines.append("")
        lines.append(a)
        lines.append("")
    section = "\n".join(lines).rstrip() + "\n"
    open(fn, "w", encoding="utf-8").write(raw + section)
    report.append({"slug": slug, "qs": len(items), "avg": sum(wordcount(a) for _,a in items)//len(items)})

print(f"Re-applied expanded FAQ to {len(report)} posts; avg {sum(r['avg'] for r in report)//len(report)} words")
json.dump(report, open("faq_applied.json","w"), indent=2)
