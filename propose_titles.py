import re, os, glob

# slug/title -> new title. Only change posts >60 chars (and tidy a couple near-limit).
new_titles = {
    "are-makecom-pricing-plans-worth-it-a-12k-field-report-from-someone-who-actually-":
        "Is Make.com Worth It? Pricing After a $12K Spend (2026)",
    "beehiiv-free-plan-limitations-why-theyre-a-death-knell-for-newsletter-gigs-and-h":
        "Beehiiv Free Plan Limits: What They Don't Tell You (2026)",
    "beehiiv-vs-convertkit-the-solo-founders-brutal-truth-no-fluff-just-wins":
        "Beehiiv vs ConvertKit: Which Is Better for Solopreneurs?",
    "beehiiv-vs-substack-which-paid-newsletter-platform-actually-pays-more":
        "Beehiiv vs Substack: Which Pays Creators More in 2026?",
    "descript-review-for-youtube-creators-i-edit-12-videos-a-month-with-it-heres-what":
        "Descript Review: Editing 12 YouTube Videos a Month (2026)",
    "descript-vs-riverside-for-podcast-editing-a-builders-field-report-after-200-epis":
        "Descript vs Riverside: Best for Podcast Editing? (2026)",
    "hostinger-vs-bluehost-for-beginners-a-builders-field-report-after-11-deployments":
        "Hostinger vs Bluehost: Best for Beginners in 2026?",
    "how-to-analyze-any-web-page-locally-for-two-cents-with-apify-and-ollama":
        "Analyze Any Web Page Locally for $0.02 (Apify + Ollama)",
    "how-to-build-a-one-person-content-agency-with-ai-a-solopreneurs-guide":
        "How to Start a One-Person Content Agency With AI",
    "jasper-ai-for-product-descriptions-review-a-solo-founders-unfiltered-take-spoile":
        "Jasper AI for Product Descriptions: Honest Review (2026)",
    "jasper-ai-review-for-blog-writing-a-solo-builders-guide-to-avoiding-ai-fluff-and":
        "Jasper AI Review for Blog Writing: Does It Deliver? (2026)",
    "jasper-ai-vs-chatgpt-for-blog-writing":
        "Jasper AI vs ChatGPT for Blog Writing (2026)",
    "makecom-review-is-it-worth-it-for-automation-answer-it-depends-but-not-how-you-t":
        "Make.com Review: Is It Worth It for Automation? (2026)",
    "makecom-vs-n8n-self-hosted-which-kills-your-workflow-fatigue":
        "Make.com vs n8n: Which Kills Workflow Fatigue? (2026)",
    "riversidefm-review-after-100-remote-podcast-episodes-is-it-worth-the-h":
        "Riverside.fm Review: 100+ Podcast Episodes Later (2026)",
    "the-best-ai-tools-for-one-person-business-from-someone-who-replaced-a-5-person-t":
        "Best AI Tools for a One-Person Business (2026)",
    "the-best-ai-writing-tool-for-affiliate-content-a-practical-guide-for-2025":
        "Best AI Writing Tool for Affiliate Content (2026)",
    "the-best-ai-writing-tool-for-solopreneurs-why-jasper-ai-is-the-one-youll-actuall":
        "Best AI Writing Tool for Solopreneurs: Jasper (2026)",
    "the-best-email-platform-for-paid-newsletter-isnt-what-you-think-a-builders-field":
        "Best Email Platform for Paid Newsletters (2026)",
    "the-best-no-code-automation-tool-2025-5-tools-that-actually-work-without-making-":
        "5 Best No-Code Automation Tools That Actually Work (2026)",
    "the-best-no-code-automation-tool-for-ecommerce-isnt-what-reddit-told-you":
        "Best No-Code Automation Tool for Ecommerce (2026)",
    "the-unshackled-truth-hosting-for-one-person-businesses-without-losing-your-mind":
        "Best Hosting for a One-Person Business (2026)",
    "why-descript-pricing-in-2025-is-a-bait-and-switch-for-indie-creators-but-heres-t":
        "Is Descript Pricing a Bait-and-Switch? (2026)",
    "why-hosting-speed-makes-or-breaks-your-affiliate-marketing-site-and-how-to-pick-":
        "Why Hosting Speed Makes or Breaks Affiliate Sites",
    "why-your-workflow-is-dying-in-2025-and-how-to-fix-it-with-the-best-no-code-autom":
        "Your Workflow Is Dying in 2025: Fix It With Automation",
    "youre-12-hours-a-week-away-from-building-the-app-that-makes-you-a-six-figure-fou":
        "Build a Six-Figure App by Automating Workflows (No Code)",
}

# verify lengths
print("=== proposed title lengths ===")
bad=[]
for slug,nt in new_titles.items():
    n=len(nt)
    flag="" if 50<=n<=60 else "  <-- OUT OF RANGE"
    if flag: bad.append((slug,n))
    print(f"{n:3d}{flag} | {nt}")
print(f"\nOut of 50-60 range: {len(bad)}")
PYEOF
