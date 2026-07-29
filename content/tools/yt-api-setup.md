# YouTube Data API v3 Setup

1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Go to APIs & Services → Library
4. Search "YouTube Data API v3" → Enable
5. Go to Credentials → Create Credentials → API Key
6. Copy the key
7. Add it to Cloudflare Pages:
   - Dashboard → Pages → aitoolssolo → Settings → Environment variables
   - Add: `YOUTUBE_API_KEY` = your key
