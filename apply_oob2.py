# Replacements for the 6 remaining out-of-range grandfathered answers (slug, question-substring) -> new answer
repl = {
 ("hostinger-vs-bluehost-for-beginners-a-builders-field-report-after-11-deployments",
  "What’s the biggest difference between Hostinger and Bluehost in terms of speed?"):
  "Performance tests consistently show Hostinger is about twice as fast. In my side-by-side deployments, Hostinger posted a Time to First Byte of 189ms against Bluehost’s 467ms. That gap shows up as quicker page loads, better Core Web Vitals, and higher conversion rates. For a new site trying to rank and earn trust, the speed advantage alone makes Hostinger the safer pick for most beginners.",

 ("hostinger-vs-bluehost-for-beginners-a-builders-field-report-after-11-deployments",
  "Are the upsells on Bluehost really that bad?"):
  "Yes, noticeably. Bluehost is known for pre-checking paid add-ons like SiteLock and CodeGuard at checkout, and agents often pitch more during support chats. Hostinger keeps pricing flatter and more transparent, so you see the real cost up front. For a solo founder watching every dollar, avoiding surprise renewals and bundled extras is a meaningful reason to prefer Hostinger.",

 ("hostinger-vs-bluehost-for-beginners-a-builders-field-report-after-11-deployments",
  "Is Bluehost ever a better choice?"):
  "Rarely, but it happens. If you specifically need phone support rather than chat, Bluehost offers it, while Hostinger is chat-only. In my experience Hostinger’s chat is faster and resolves issues quicker, so the gap is small. Unless phone support is a hard requirement for your workflow, Hostinger remains the stronger long-term investment for speed, panel, and pricing.",

 ("the-best-email-platform-for-paid-newsletter-isnt-what-you-think-a-builders-field",
  "Does the quality of my web hosting matter for my newsletter?"):
  "If you self-host a platform like Ghost, hosting quality is decisive: speed and uptime directly affect signup conversion and deliverability. A slow site bleeds subscribers at the form. I use a fast, affordable VPS host for Ghost so the storefront stays snappy while the newsletter runs. On a fully managed platform like Beehiiv, hosting is their problem, not yours, so it matters far less day to day.",

 ("the-best-no-code-automation-tool-for-ecommerce-isnt-what-reddit-told-you",
  "Does the speed of my hosting affect my automations?"):
  "Indirectly, yes. A slow storefront lowers conversion, which means fewer orders and less event data for your workflows to act on, so automations have less to do. On WooCommerce especially, a fast host keeps the storefront responsive while background automations run. The host does not speed up Make.com or Zapier itself, but it protects the traffic that feeds them.",
}

import re, os
for slug, qsub in repl:
    fn = f"content/posts/{slug}.md"
    raw = open(fn, encoding="utf-8", errors="replace").read()
    newans = repl[(slug, qsub)]
    # Find the FAQ bold-question block containing qsub and replace the answer paragraph(s) until next **N. or --- 
    # Strategy: locate the question line, then replace following non-empty answer lines up to next ** or blank-then-** or '---'
    lines = raw.split("\n")
    out = []
    i = 0
    replaced = False
    while i < len(lines):
        line = lines[i]
        if not replaced and re.search(re.escape(qsub), line):
            out.append(line)
            i += 1
            # skip blank lines
            while i < len(lines) and lines[i].strip() == "":
                out.append(lines[i]); i += 1
            # collect answer lines until next '**' bullet or '---' or blank+structural
            ans_start = i
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip().startswith("**") or nxt.strip().startswith("---") or nxt.strip().startswith("###"):
                    break
                i += 1
            # replace answer lines [ans_start:i) with new answer
            out.append("")
            out.append(newans)
            out.append("")
            replaced = True
            continue
        out.append(line)
        i += 1
    open(fn, "w", encoding="utf-8").write("\n".join(out))
    print(f"Updated: {slug[-40:]} / {qsub[:35]} -> {len(newans.split())}w")

print("Done. Verifying all 6...")
for (slug, qsub), ans in repl.items():
    w=len(ans.split())
    print(f"  {'OK' if 40<=w<=80 else 'OOB'} {w}w")
