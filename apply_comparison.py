import json, os, re

tables = json.load(open("comparison_tables.json", encoding="utf-8"))

def build_table(tool, comp, rows):
    lines = ["", f"## Comparison Table: {tool} vs {comp}", ""]
    lines.append("| Feature | " + tool + " | " + comp + " |")
    lines.append("|---|---|---|")
    for feat, tv, cv in rows:
        lines.append(f"| {feat} | {tv} | {cv} |")
    lines.append("")
    return "\n".join(lines)

report = []
for slug, (tool, comp, rows) in tables.items():
    fn = f"content/posts/{slug}.md"
    if not os.path.exists(fn):
        print("MISSING", fn); continue
    raw = open(fn, encoding="utf-8", errors="replace").read()
    # If a comparison table already exists, skip (idempotent)
    if re.search(r'^##\s+Comparison Table', raw, re.M):
        print("SKIP (exists)", slug); continue
    section = build_table(tool, comp, rows)
    # Insert before "## FAQ" if present, else append at end
    m = re.search(r'^##\s+FAQ(\s|:|$)', raw, re.M)
    if m:
        pos = m.start()
        new_raw = raw[:pos] + section + "\n" + raw[pos:]
    else:
        new_raw = raw.rstrip("\n") + "\n" + section
    open(fn, "w", encoding="utf-8").write(new_raw)
    report.append(slug)

print(f"Added comparison tables to {len(report)} posts")
json.dump(report, open("comparison_applied.json","w"), indent=2)
