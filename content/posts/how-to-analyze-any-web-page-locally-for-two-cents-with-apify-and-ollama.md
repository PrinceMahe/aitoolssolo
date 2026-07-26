---
title: "Analyze Any Web Page Locally for $0.02 (Apify + Ollama)"
description: "Stop wasting money on expensive LLM APIs. Learn how to crawl any website with Apify and analyze pages locally on your own GPU for just two cents."
date: 2026-07-04T16:20:00-04:00
lastmod: 2026-07-04T16:20:00-04:00
draft: false
tags: ["analyze", "any", "web", "page", "locally"]
categories: ["AI Tools", "Automation"]
ShowToc: true
TocOpen: false
---

If you’ve ever tried to build an automated web scraping and content analysis pipeline, you know the billing shock that follows. Crawling 1,000 pages and feeding them into OpenAI's GPT-4o or Claude 3.5 Sonnet to extract key data can easily cost you $50 to $100. Doing this daily or at scale quickly turns a neat side project into a financial black hole.

But what if you could scrape any website using a robust cloud-based crawler, clean up the clutter, and feed it into a powerful local LLM running on your own hardware? 

I built a setup that does exactly this, reducing my cost to **$0.02 per page analyzed**. 

Here is the exact blueprint of how I integrated an **Apify Cloud Actor** with my local **Ollama** setup to analyze web pages locally for pennies.

---

## The $0.02 Pay-Per-Event (PPE) Math

When running web analysis at scale, your costs break down into two categories:
1. **Scrape Cost:** The cloud infrastructure, proxies, and headless browsers required to bypass bot detection.
2. **LLM Cost:** The token-based cost of analyzing the scraped content.

By using **Apify**, I pay a flat Pay-Per-Event fee of **$0.02 USD** per page analyzed. Apify handles the heavy lifting of crawling, cleaning the HTML, and handling IP rotation. 

Instead of sending that cleaned content to an expensive OpenAI endpoint, the Apify Actor tunnels the text directly to my local workstation (equipped with an RTX 5080). Ollama runs the inference locally on a custom 32K context `qwen3-hermes` model. 

Since local inference is essentially free (only costing a tiny fraction of a cent in electricity), my profit margin is **~99%**. If I scale to 100,000 monthly page analyses, I pay $2,000 to Apify (handling the scraping infrastructure), but avoid over $10,000 in OpenAI API fees.

---

## The Architecture: How It Works

Here is how the data flows from the cloud to your local GPU and back:

1. **Apify Cloud Actor:** Crawls the target URLs, extracts the raw HTML, and runs cleaning routines (removing scripts, styles, header, footer, and navigation elements) to minimize context token usage.
2. **Network Tunnel:** The Actor forwards the cleaned content via a secure tunnel (using LocalTunnel or a permanent Cloudflare Tunnel) to your local workstation.
3. **Local Node.js Proxy:** A lightweight Node.js proxy server running on your workstation (port `11437`) receives the payload, verifies a secret security token, forces the prompt template, and routes it to Ollama.
4. **Local LLM (Ollama):** Ollama runs inference on the RTX 5080 GPU, processing the page content with a 14B parameter model in seconds.
5. **Apify Dataset:** The structured response is streamed back to the Apify Actor and stored in the Apify Dataset for easy download (JSON, CSV, etc.).

---

## Step 1: Setting Up the Local Proxy (`apify_llm_proxy.js`)

On your local workstation, you need a proxy that listens for incoming scraping requests, verifies they are authorized, and sends them to Ollama. 

Create a file named `apify_llm_proxy.js` on your workstation:

```javascript
const http = require('http');
const { URL } = require('url');

const PORT = 11437;
const OLLAMA_URL = 'http://localhost:11434/api/chat';
const APIFY_SECRET_TOKEN = process.env.APIFY_SECRET_TOKEN || 'your-super-secure-token';

const server = http.createServer((req, res) => {
    const reqUrl = new URL(req.url, `http://${req.headers.host}`);
    
    // Health check endpoint
    if (reqUrl.pathname === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'ok', uptime: process.uptime() }));
        return;
    }

    if (req.method !== 'POST') {
        res.writeHead(405, { 'Content-Type': 'text/plain' });
        res.end('Method Not Allowed');
        return;
    }

    // Validate authorization token
    const authHeader = req.headers['authorization'];
    if (!authHeader || authHeader !== `Bearer ${APIFY_SECRET_TOKEN}`) {
        res.writeHead(401, { 'Content-Type': 'text/plain' });
        res.end('Unauthorized');
        return;
    }

    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
        try {
            const data = JSON.parse(body);
            
            // Forward request to local Ollama instance
            const ollamaPayload = {
                model: 'qwen3-hermes', // Force our custom 32K model
                messages: data.messages,
                stream: false,
                options: data.options || { num_ctx: 32768, temperature: 0.2 }
            };

            const response = await fetch(OLLAMA_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(ollamaPayload)
            });

            const ollamaData = await response.json();
            
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(ollamaData));
        } catch (error) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: error.message }));
        }
    });
});

server.listen(PORT, () => {
    console.log(`Local Proxy running on port ${PORT}`);
});
```

---

## Step 2: Creating a Launcher Script (`run_apify_proxy.bat`)

To make starting this service effortless on your Windows workstation, create a `.bat` launcher file:

```batch
@echo off
title Apify Ollama Proxy
set APIFY_SECRET_TOKEN=your-super-secure-token
node C:\Users\princ\apify_llm_proxy.js
pause
```

To expose this local proxy to the internet so the Apify Cloud Actor can access it, run a local tunnel in a separate terminal:

```bash
npx -y localtunnel --port 11437
```
*(Note: For production, setting up a permanent, secure Cloudflare Tunnel using `cloudflared` is highly recommended to avoid random URL changes).*

---

## Step 3: Setting Up the Apify Actor

Your Apify Actor acts as the web scraper. It visits pages, extracts text, and communicates with your tunnel. 

In your Apify Actor route handler (`routes.js`), add a cleaning step and execute the LLM request:

```javascript
// Clean HTML to save precious tokens
const cleanHtml = (html) => {
    return html
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
        .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '')
        .replace(/<header\b[^<]*(?:(?!<\/header>)<[^<]*)*<\/header>/gi, '')
        .replace(/<footer\b[^<]*(?:(?!<\/footer>)<[^<]*)*<\/footer>/gi, '')
        .replace(/<nav\b[^<]*(?:(?!<\/nav>)<[^<]*)*<\/nav>/gi, '')
        .replace(/<\/?[^>]+(>|$)/g, "") // Strip remaining HTML tags
        .replace(/\s+/g, ' ')            // Collapse extra spacing
        .trim();
};

// Send content to local Ollama via the proxy tunnel
const analyzeWithLocalLLM = async (text, tunnelUrl, secretToken) => {
    const response = await fetch(`${tunnelUrl}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${secretToken}`,
            'Bypass-Tunnel-Reminder': 'true' // Bypass localtunnel warning page
        },
        body: JSON.stringify({
            messages: [
                {
                    role: 'user',
                    content: `Analyze the following webpage content and extract key features, pricing, and pros/cons:\n\n${text}`
                }
            ]
        })
    });
    return response.json();
};
```

---

## Verdict & Optimization Tips

If you're running this setup on a consumer workstation, keep these optimizations in mind:

1. **Parallelism:** If Apify crawls multiple pages simultaneously, Ollama might queue the requests and slow down the crawl. Set `OLLAMA_NUM_PARALLEL=4` (or higher depending on your GPU VRAM) in your local environment variables to process multiple streams at once.
2. **Model Selection:** The Qwen3 14B model (`qwen3:14b`) is the sweet spot for web analysis on a 16GB GPU (like the RTX 5080). It provides excellent logic reasoning while running fast enough to prevent crawler timeouts.
3. **Reliability:** Since your local workstation might go to sleep or lose internet connection, add a watchdog script on a lightweight node (like a Raspberry Pi 5) to monitor the proxy health (`/health`) and send a Telegram notification if it goes offline.

This setup takes less than an hour to implement, saves thousands in API fees, and keeps your crawled data entirely private. 

*What are you building with local LLMs? Let me know in the comments!*
