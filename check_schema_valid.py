import json, re, glob

def check_schema_validity():
    fs = glob.glob("public/**/*.html", recursive=True)
    types_checked = {"FAQPage":0,"SoftwareApplication":0,"BreadcrumbList":0,"invalid":0}
    samples = {"FAQPage":None,"SoftwareApplication":None,"BreadcrumbList":None}
    # crawl a manageable sample across types
    targets = []
    # FAQ: grab 5 FAQ posts
    faq = [f for f in fs if re.search(r"public/posts/[^/]+/index.html", f)]
    targets += sorted(faq)[:5]
    # tool pages
    tools = [f for f in fs if re.search(r"public/tools/[^/]+/index.html", f)]
    targets += tools[:5]
    # comparison pages
    comp = [f for f in fs if re.search(r"public/comparisons/[^/]+/index.html", f)]
    targets += comp[:5]
    for f in targets:
        html = open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r'<script type=application/ld\+json>(.*?)</script>', html, re.S):
            raw = m.group(1)
            try:
                d = json.loads(raw)
                def walk(o):
                    if isinstance(o, dict):
                        t = o.get("@type")
                        if t in types_checked:
                            types_checked[t]+=1
                            if samples[t] is None: samples[t]=f
                        for v in o.values(): walk(v)
                    elif isinstance(o, list):
                        for v in o: walk(v)
                walk(d)
            except Exception as e:
                types_checked["invalid"]+=1
    return types_checked, samples

tc, sm = check_schema_validity()
print("Schema JSON-LD validity (sampled):", json.dumps(tc, indent=2))
for k,v in sm.items():
    print(f"  sample {k}: {v}")
