import glob, re, json

# The 5 grandfathered posts (had FAQs before Phase 1.5 Task 2)
grand = [
 "best-ai-tools-for-freelance-writers-who-want-to-10x-output",
 "hostinger-vs-bluehost-for-beginners-a-builders-field-report-after-11-deployments",
 "how-to-build-a-one-person-content-agency-with-ai-a-solopreneurs-guide",
 "the-best-email-platform-for-paid-newsletter-isnt-what-you-think-a-builders-field",
 "the-best-no-code-automation-tool-for-ecommerce-isnt-what-reddit-told-you",
]

out = []
for slug in grand:
    fn = f"content/posts/{slug}.md"
    raw = open(fn, encoding="utf-8", errors="replace").read()
    # extract FAQ section
    m = re.search(r'## FAQ.*?(?=\n## |\Z)', raw, re.S)
    if not m:
        print("NO FAQ in", slug); continue
    sec = m.group(0)
    # split into Q/A: ### Q: question \n answer
    blocks = re.split(r'### Q:\s*', sec)
    for b in blocks[1:]:
        lines = b.strip().split("\n")
        q = lines[0].strip()
        a = "\n".join(lines[1:]).strip()
        w = len(a.split())
        if not (40 <= w <= 80):
            out.append({"slug": slug, "q": q, "words": w, "answer": a})

print(f"Out-of-range grandfathered answers: {len(out)}")
for o in out:
    print(f"\n[{o['slug'][:40]}] ({o['words']}w) Q: {o['q'][:50]}")
    print(f"  A: {o['answer'][:120]}...")
json.dump(out, open("oob_grand.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
