import os
import re
import random
import urllib.request
import urllib.error
import json
from datetime import datetime

OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'gemma3:27b')

AFFILIATE_CONTEXT = """
When recommending tools, use these affiliate links naturally in the text where relevant:
- Make.com: https://www.make.com/en/register?pc=aitoolssolo
- Beehiiv: https://www.beehiiv.com/?via=Prince-Maheshwari
- Hostinger: https://www.hostinger.com/ca?REFERRALCODE=ZT3PRINCEOCI
Only include a link if the tool is genuinely relevant to the post topic. Never force them.
"""

def get_next_topic():
    topics_file = os.path.join(os.path.dirname(__file__), 'topics.txt')
    done_file = os.path.join(os.path.dirname(__file__), 'topics_done.txt')

    with open(topics_file, 'r') as f:
        topics = [l.strip() for l in f if l.strip() and not l.startswith('#')]

    done = set()
    if os.path.exists(done_file):
        with open(done_file, 'r') as f:
            done = {l.strip() for l in f if l.strip()}

    available = [t for t in topics if t not in done]
    if not available:
        print('All topics done! Resetting...')
        open(done_file, 'w').close()
        available = topics

    topic = random.choice(available)

    with open(done_file, 'a') as f:
        f.write(topic + '\n')

    return topic

def generate_post(topic):
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S-04:00')

    prompt = f"""You are writing a blog post for AI Tools Solo (aitoolssolo.com), a site that reviews AI tools for solopreneurs with real hands-on experience.

Write a comprehensive, SEO-optimized blog post about: {topic}

Style guide:
- First-person voice, like a real solopreneur who has tested these tools
- 1200-1600 words
- Specific, actionable advice — no fluff
- Honest pros/cons
- Natural, conversational tone
- Include 2-3 relevant affiliate links where genuinely useful (do not force them)

{AFFILIATE_CONTEXT}

Return ONLY the complete markdown with this exact frontmatter (no extra text before or after):
---
title: "TITLE HERE"
description: "ONE SENTENCE META DESCRIPTION UNDER 160 CHARS"
date: {now}
draft: false
tags: ["tag1", "tag2", "tag3"]
categories: ["AI Tools", "Automation"]
ShowToc: true
TocOpen: false
---

Then the full post body in markdown."""

    payload = json.dumps({
        'model': OLLAMA_MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'stream': False,
        'options': {'num_predict': 4096, 'temperature': 0.7}
    }).encode()

    req = urllib.request.Request(
        f'{OLLAMA_HOST}/api/chat',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    print(f'Calling Ollama ({OLLAMA_MODEL}) — this takes a few minutes for gemma3:27b...')
    with urllib.request.urlopen(req, timeout=600) as resp:
        result = json.loads(resp.read())

    return result['message']['content']

def slugify(title):
    title = re.sub(r'[^\w\s-]', '', title.lower())
    title = re.sub(r'[\s_-]+', '-', title)
    return title.strip('-')[:70]

def save_post(content):
    title_match = re.search(r'title:\s*"([^"]+)"', content)
    slug = slugify(title_match.group(1)) if title_match else f'post-{datetime.now().strftime("%Y%m%d")}'

    posts_dir = os.path.join(os.path.dirname(__file__), '..', 'content', 'posts')
    filename = os.path.join(posts_dir, f'{slug}.md')

    with open(filename, 'w') as f:
        f.write(content)

    print(f'Created: {filename}')
    return filename

if __name__ == '__main__':
    topic = get_next_topic()
    print(f'Generating post about: {topic}')
    content = generate_post(topic)
    save_post(content)
    print('Done!')
