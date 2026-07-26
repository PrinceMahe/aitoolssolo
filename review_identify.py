import glob, os, re

# Posts that are tool reviews / comparisons -> deserve a feature comparison table.
# Map slug -> (Tool, Competitor) for the table header.
review_posts = {
"jasper-ai-for-product-descriptions-review-a-solo-founders-unfiltered-take-spoile": ("Jasper AI", "ChatGPT"),
"jasper-ai-review-for-blog-writing-a-solo-builders-guide-to-avoiding-ai-fluff-and": ("Jasper AI", "ChatGPT"),
"jasper-ai-vs-chatgpt-for-blog-writing": ("Jasper AI", "ChatGPT"),
"descript-review-for-youtube-creators-i-edit-12-videos-a-month-with-it-heres-what": ("Descript", "Riverside"),
"descript-vs-riverside-for-podcast-editing-a-builders-field-report-after-200-epis": ("Descript", "Riverside"),
"riversidefm-review-after-100-remote-podcast-episodes-is-it-worth-the-h": ("Riverside.fm", "Descript"),
"makecom-review-is-it-worth-it-for-automation-answer-it-depends-but-not-how-you-t": ("Make.com", "Zapier"),
"makecom-vs-n8n-self-hosted-which-kills-your-workflow-fatigue": ("Make.com", "n8n"),
"beehiiv-vs-convertkit-the-solo-founders-brutal-truth-no-fluff-just-wins": ("Beehiiv", "ConvertKit"),
"beehiiv-vs-substack-which-paid-newsletter-platform-actually-pays-more": ("Beehiiv", "Substack"),
"beehiiv-free-plan-limitations-why-theyre-a-death-knell-for-newsletter-gigs-and-h": ("Beehiiv", "Substack"),
"hostinger-vs-bluehost-for-beginners-a-builders-field-report-after-11-deployments": ("Hostinger", "Bluehost"),
"the-best-ai-writing-tool-for-solopreneurs-why-jasper-ai-is-the-one-youll-actuall": ("Jasper AI", "ChatGPT"),
"the-best-ai-writing-tool-for-affiliate-content-a-practical-guide-for-2025": ("Jasper AI", "ChatGPT"),
"the-best-email-platform-for-paid-newsletter-isnt-what-you-think-a-builders-field": ("Beehiiv", "ConvertKit"),
"the-best-no-code-automation-tool-2025-5-tools-that-actually-work-without-making-": ("Make.com", "Zapier"),
"the-best-no-code-automation-tool-for-ecommerce-isnt-what-reddit-told-you": ("Make.com", "Zapier"),
"why-descript-pricing-in-2025-is-a-bait-and-switch-for-indie-creators-but-heres-t": ("Descript", "Riverside"),
"are-makecom-pricing-plans-worth-it-a-12k-field-report-from-someone-who-actually-": ("Make.com", "Zapier"),
"the-best-ai-tools-for-one-person-business-from-someone-who-replaced-a-5-person-t": ("Jasper AI", "ChatGPT"),
"best-ai-tools-for-solopreneurs-in-2026-the-actual-stack-that-ships": ("Jasper AI", "ChatGPT"),
}

present = []
for slug in review_posts:
    fn = f"content/posts/{slug}.md"
    if os.path.exists(fn):
        present.append(slug)
    else:
        print("MISSING", slug)

print(f"Review/comparison posts identified: {len(present)}")
import json
json.dump(review_posts, open("review_posts.json","w"), indent=2)
