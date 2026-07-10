import os
import re
import random
import urllib.request
import urllib.error
import json
from datetime import datetime

OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'gemma3:27b')

# Stopwords that should NOT become tags (the old code turned title words like
# "the"/"for"/"code" into tags, which polluted the tag archive and internal links).
STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'for', 'to', 'of', 'in', 'on', 'with', 'is',
    'it', 'you', 'your', 'how', 'why', 'what', 'best', 'review', 'worth', 'code',
    'no', 'not', 'vs', 'from', 'that', 'this', 'are', 'tool', 'tools', 'ai',
}

# Words/phrases that map a topic to the "primary keyword" it targets. Two topics
# that share a primary keyword compete for the same search results (cannibalization),
# so we block a topic if a published post already owns that keyword.
KEYWORD_GROUPS = {
    'make.com': ['make.com', 'makecom', 'make com'],
    'jasper ai': ['jasper', 'jasper ai'],
    'descript': ['descript'],
    'riverside': ['riverside', 'riverside.fm', 'riversidefm'],
    'beehiiv': ['beehiiv'],
    'convertkit': ['convertkit', 'convert kit'],
    'substack': ['substack'],
    'hostinger': ['hostinger'],
    'bluehost': ['bluehost'],
    'chatgpt': ['chatgpt', 'chat gpt'],
    'claude': ['claude'],
    'notion': ['notion'],
    'obsidian': ['obsidian'],
    'n8n': ['n8n'],
    'zapier': ['zapier'],
}


def primary_keyword(topic):
    """Return the canonical keyword a topic is targeting, or '' if none match."""
    low = topic.lower()
    for kw, aliases in KEYWORD_GROUPS.items():
        if any(a in low for a in aliases):
            return kw
    return ''


def published_keywords(posts_dir):
    """Scan existing post bodies/titles for primary keywords already covered."""
    covered = set()
    if not os.path.isdir(posts_dir):
        return covered
    for fn in os.listdir(posts_dir):
        if not fn.endswith('.md'):
            continue
        path = os.path.join(posts_dir, fn)
        try:
            text = open(path, encoding='utf-8', errors='ignore').read().lower()
        except OSError:
            continue
        for kw in KEYWORD_GROUPS:
            if kw in text:
                covered.add(kw)
    return covered
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

    # Block topics whose primary keyword is already owned by a published post.
    posts_dir = os.path.join(os.path.dirname(__file__), '..', 'content', 'posts')
    covered = published_keywords(posts_dir)
    keyword_blocked = [t for t in available if primary_keyword(t) in covered]
    if keyword_blocked:
        print(f'Skipping {len(keyword_blocked)} topic(s) already covered by a post: '
              f'{[primary_keyword(t) for t in keyword_blocked]}')
        available = [t for t in available if primary_keyword(t) not in covered]

    if not available:
        print('All topics done! Resetting done list...')
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

SEO requirements (these directly affect organic traffic):
- Target ONE primary keyword derived from the topic; use it in the title, the
  first 100 words, and at least one H2.
- Use 4-6 descriptive H2/H3 headings that read like real search queries
  (e.g. "Is X worth it for solopreneurs?", "X vs Y: which should you pick?").
- End with an FAQ section of 3-4 questions people actually search for about this
  topic, each answered in 2-4 sentences. Wrap FAQ questions as plain "### Q: ..."
  headings so they can be picked up as rich results.
- Naturally link to 1-2 OTHER relevant posts on the site where useful
  (internal links help rankings and keep readers on-site).

{AFFILIATE_CONTEXT}

Return ONLY the complete markdown with this exact front matter (no extra text before or after):
---
title: "TITLE HERE"
description: "ONE SENTENCE META DESCRIPTION UNDER 160 CHARS"
date: {now}
draft: false
tags: ["tool-name", "use-case", "audience"]
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

def derive_tags(title, topic):
    """Build clean, meaningful tags: the primary keyword (if any) plus the
    most significant non-stopword tokens from the title. Capped at 5."""
    raw = re.sub(r'[^a-z0-9\s-]', ' ', title.lower())
    words = [w for w in re.split(r'[\s_-]+', raw) if w and w not in STOPWORDS]
    # de-dupe while preserving order
    seen, tags = set(), []
    for w in words:
        if w not in seen:
            seen.add(w)
            tags.append(w)
    kw = primary_keyword(topic)
    if kw and kw not in tags:
        tags.insert(0, kw)
    return tags[:5]


def slugify(title):
    title = re.sub(r'[^\w\s-]', '', title.lower())
    title = re.sub(r'[\s_-]+', '-', title)
    return title.strip('-')[:70]

def save_post(content, topic=''):
    title_match = re.search(r'title:\s*"([^"]+)"', content)
    title = title_match.group(1) if title_match else ''
    slug = slugify(title) if title else f'post-{datetime.now().strftime("%Y%m%d")}'

    # Replace the model's junk tags with clean, meaningful ones.
    tags = derive_tags(title, topic)
    content = re.sub(r'(?m)^tags:\s*\[.*\]\s*$',
                     'tags: [' + ', '.join(json.dumps(t) for t in tags) + ']', content)

    posts_dir = os.path.join(os.path.dirname(__file__), '..', 'content', 'posts')
    filename = os.path.join(posts_dir, f'{slug}.md')

    # Safety: never create a second post for a keyword we already own.
    kw = primary_keyword(topic)
    if kw and kw in published_keywords(posts_dir):
        print(f'ABORT: a post already covers "{kw}". Skipping to avoid cannibalization.')
        return None

    with open(filename, 'w') as f:
        f.write(content)

    print(f'Created: {filename}')
    return filename

if __name__ == '__main__':
    topic = get_next_topic()
    print(f'Generating post about: {topic}')
    content = generate_post(topic)
    save_post(content, topic)
    print('Done!')
