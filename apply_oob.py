import json, re, os

# Replacements for the 7 out-of-range grandfathered FAQ answers.
# Keyed by (slug, question) -> new answer (45-65 words).
repl = {
 ("best-ai-tools-for-freelance-writers-who-want-to-10x-output",
  "What are the best AI tools for freelance writers?"):
  "The best stack depends on your work, but most freelance writers I know rely on Jasper for draft generation, Surfer SEO for briefs and optimization, and Make.com to automate client handoffs. Grammarly catches polish issues, and Notion AI organizes research. Start with one tool, prove it saves billable time, then add the next only when a real bottleneck appears in your weekly workflow.",

 ("best-ai-tools-for-freelance-writers-who-want-to-10x-output",
  "Can AI tools replace human writers?"):
  "No, and they should not. AI handles repetitive drafting, research summaries, and outlines, but the creativity, judgment, and client-specific voice that win repeat work still come from you. Treat the model as a fast junior assistant that never tires, not a replacement. The freelancers earning more today are the ones pairing their expertise with AI, not the ones worried it will take their seat.",

 ("best-ai-tools-for-freelance-writers-who-want-to-10x-output",
  "How do I integrate AI tools into my workflow?"):
  "Start with one tool at a time so the habit sticks. Use it for a single task, like turning a brief into an outline, for a full week before adding another. Most tools integrate via browser or Make.com, so connecting them to your editor and inbox is quick. Layer automation slowly; the goal is a smoother process, not a sprawling stack you abandon after a month of friction.",

 ("best-ai-tools-for-freelance-writers-who-want-to-10x-output",
  "Are AI tools worth the cost for solopreneurs?"):
  "Yes, when used consistently. A single writing subscription often pays for itself in the hours you reclaim from drafting and editing, and automation tools return even more by removing repetitive admin. The waste is paying for five tools and using one. Pick the cheapest plan that removes your biggest bottleneck, then upgrade only after the saved time clearly shows up in your invoices and your week.",

 ("how-to-build-a-one-person-content-agency-with-ai-a-solopreneurs-guide",
  "What are the best AI tools for a one-person content agency?"):
  "For a solo content agency, Jasper produces premium drafts, Copy.ai handles quick social and ad variants, and Beehiiv manages client newsletters end to end. Make.com or n8n ties intake, drafts, and delivery into one pipeline so you touch each job once. Start free, then pay only for the tool that removes your clearest bottleneck. The stack is leverage, not a status symbol, so keep it lean and ruthless about unused subscriptions.",

 ("how-to-build-a-one-person-content-agency-with-ai-a-solopreneurs-guide",
  "How can I find clients as a solopreneur?"):
  "Use LinkedIn to pitch specific outcomes, not generic services, and share short case studies that show the result you delivered. Offer a free template or audit in exchange for a testimonial, which builds social proof fast. Warm referrals from past clients beat cold outreach every time, so ask for introductions the moment a project lands well. Consistent, useful posting compounds into a steady inbound pipeline within a few months.",

 ("how-to-build-a-one-person-content-agency-with-ai-a-solopreneurs-guide",
  "What are the challenges of using AI in content creation?"):
  "AI drafts need real editing, because raw output reads generic and can drift from the client's voice. Some clients are wary of machine-generated work, so disclose its use and keep a human final pass. The bigger risk is over-reliance: letting the model make claims you have not verified. Set a rule that every fact and promise is checked before delivery, and your AI-assisted work will stay both fast and trustworthy.",
}

# Apply: for each grandfathered post, replace the answer under each matched question.
grand = list({k[0] for k in repl})
for slug in grand:
    fn = f"content/posts/{slug}.md"
    raw = open(fn, encoding="utf-8", errors="replace").read()
    # find FAQ section and rewrite matched Q/A answers
    def repl_qa(m):
        sec = m.group(0)
        # split by ### Q:
        parts = re.split(r'(### Q:\s*)', sec)
        # parts: [pre, '### Q: ', block, '### Q: ', block, ...]
        out = parts[0]
        i = 1
        while i < len(parts):
            marker = parts[i]
            block = parts[i+1] if i+1 < len(parts) else ""
            # block: question line + answer lines
            blines = block.split("\n")
            q = blines[0].strip()
            key = (slug, q)
            if key in repl:
                newans = repl[key]
                # keep trailing structure: question line + blank + new answer
                rest = "\n".join(blines[1:])  # original answer (unused)
                block_new = q + "\n\n" + newans + ("\n" if not rest.endswith("\n") else "") 
                # preserve any lines after answer? answer is until next ### Q: which split handles
                out += marker + block_new
            else:
                out += marker + block
            i += 2
        return out
    raw2 = re.sub(r'## FAQ.*?(?=\n## |\Z)', repl_qa, raw, flags=re.S)
    open(fn, "w", encoding="utf-8").write(raw2)

# verify
print("Applied replacements. Verifying word counts...")
for (slug, q), ans in repl.items():
    w = len(ans.split())
    status = "OK" if 40 <= w <= 80 else "OOB"
    print(f"  {status} {w}w  {q[:45]}")
