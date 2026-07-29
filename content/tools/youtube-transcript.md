---
title: "YouTube Transcript — Get Any Video Transcript Free"
description: "Free YouTube transcript extractor. Paste any YouTube video link and get the full transcript with timestamps. Copy, export as TXT/SRT/Markdown."
type: "tool"
slug: "youtube-transcript"
tool: "youtube-transcript"
draft: false
---

<style>
.yt-transcript-tool {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  max-width: 800px;
  margin: 2rem auto;
  padding: 1.5rem;
  border-radius: 12px;
  background: var(--entry);
  border: 1px solid var(--border);
}

.yt-transcript-tool h2 {
  margin-top: 0;
  font-size: 1.4rem;
  color: var(--primary);
}

.yt-transcript-tool .input-row {
  display: flex;
  gap: 8px;
  align-items: stretch;
}

.yt-transcript-tool .input-row input {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid var(--border);
  border-radius: 8px;
  font-size: 1rem;
  background: var(--theme);
  color: var(--content);
}

.yt-transcript-tool .input-row input:focus {
  outline: none;
  border-color: var(--primary);
}

.yt-transcript-tool .input-row button {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  background: var(--primary);
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: opacity 0.2s;
}

.yt-transcript-tool .input-row button:hover { opacity: 0.85; }
.yt-transcript-tool .input-row button:disabled { opacity: 0.5; cursor: not-allowed; }

.yt-transcript-tool .metadata {
  margin-top: 1rem;
  padding: 12px 16px;
  background: var(--code-bg);
  border-radius: 8px;
  font-size: 0.9rem;
  color: var(--secondary);
  display: none;
}

.yt-transcript-tool .metadata.show { display: block; }

.yt-transcript-tool .action-bar {
  display: flex;
  gap: 8px;
  margin: 1rem 0;
  flex-wrap: wrap;
}

.yt-transcript-tool .action-bar button {
  padding: 6px 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--theme);
  color: var(--content);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.15s;
}

.yt-transcript-tool .action-bar button:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.yt-transcript-tool .transcript-container {
  max-height: 65vh;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--code-bg);
  display: none;
}

.yt-transcript-tool .transcript-container.show { display: block; }

.yt-transcript-tool .segment {
  display: flex;
  gap: 12px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  line-height: 1.5;
  cursor: pointer;
  transition: background 0.1s;
}

.yt-transcript-tool .segment:last-child { border-bottom: none; }
.yt-transcript-tool .segment:hover { background: var(--theme); }

.yt-transcript-tool .segment .timestamp {
  min-width: 55px;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.82rem;
  color: var(--primary);
  font-weight: 500;
  flex-shrink: 0;
}

.yt-transcript-tool .segment .text {
  color: var(--content);
  font-size: 0.95rem;
}

.yt-transcript-tool .error-msg {
  padding: 16px;
  color: #dc3545;
  background: rgba(220, 53, 69, 0.08);
  border-radius: 8px;
  display: none;
  margin-top: 1rem;
}

.yt-transcript-tool .error-msg.show { display: block; }

.yt-transcript-tool .loading {
  display: none;
  text-align: center;
  padding: 2rem;
  color: var(--secondary);
}

.yt-transcript-tool .loading.show { display: block; }

.yt-transcript-tool .spinner {
  display: inline-block;
  width: 24px;
  height: 24px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: yt-spin 0.8s linear infinite;
  margin-right: 8px;
  vertical-align: middle;
}

@keyframes yt-spin { to { transform: rotate(360deg); } }

.yt-transcript-tool .copied-toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--primary);
  color: #fff;
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 0.85rem;
  opacity: 0;
  transition: opacity 0.3s;
  z-index: 999;
  pointer-events: none;
}

.yt-transcript-tool .copied-toast.show { opacity: 1; }

.yt-transcript-tool .examples {
  margin-top: 0.8rem;
  font-size: 0.85rem;
  color: var(--secondary);
}

.yt-transcript-tool .examples a {
  color: var(--primary);
  text-decoration: underline;
  cursor: pointer;
}

.yt-transcript-tool .examples a:hover { opacity: 0.8; }
</style>

<div class="yt-transcript-tool">
  <h2>🎬 YouTube Transcript Extractor</h2>
  <p style="margin-top:0;color:var(--secondary);font-size:0.92rem;">
    Paste any YouTube link and get the full transcript with timestamps. Free, no sign-up.
  </p>

  <div class="input-row">
    <input type="text" id="yt-url-input" placeholder="Paste YouTube link here (e.g. https://youtu.be/dQw4w9WgXcQ)" />
    <button id="yt-fetch-btn" onclick="fetchTranscript()">Get Transcript</button>
  </div>

  <div class="examples">
    Try: <a onclick="document.getElementById('yt-url-input').value='https://www.youtube.com/watch?v=jNQXAC9IVRw';fetchTranscript();">Me at the zoo</a> ·
    <a onclick="document.getElementById('yt-url-input').value='https://youtu.be/9bZkp7q19f0';fetchTranscript();">Gangnam Style</a>
  </div>

  <div class="loading" id="yt-loading"><span class="spinner"></span> Fetching transcript...</div>
  <div class="error-msg" id="yt-error"></div>

  <div class="metadata" id="yt-metadata"></div>

  <div class="action-bar" id="yt-actions" style="display:none;">
    <button onclick="copyTranscript('text')">📋 Copy Text</button>
    <button onclick="copyTranscript('timestamps')">⏱ Copy with Timestamps</button>
    <button onclick="exportTranscript('srt')">📄 Export SRT</button>
    <button onclick="exportTranscript('md')">📝 Export Markdown</button>
    <button onclick="exportTranscript('txt')">📃 Export TXT</button>
  </div>

  <div class="transcript-container" id="yt-transcript-container"></div>

  <div class="copied-toast" id="yt-toast">Copied!</div>
</div>

<script>
let lastSegments = [];

function extractVideoId(url) {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([A-Za-z0-9_-]{11})/,
    /^([A-Za-z0-9_-]{11})$/
  ];
  for (const p of patterns) {
    const m = url.trim().match(p);
    if (m) return m[1];
  }
  return null;
}

async function fetchTranscript() {
  const input = document.getElementById('yt-url-input');
  const btn = document.getElementById('yt-fetch-btn');
  const loading = document.getElementById('yt-loading');
  const error = document.getElementById('yt-error');
  const container = document.getElementById('yt-transcript-container');
  const metadata = document.getElementById('yt-metadata');
  const actions = document.getElementById('yt-actions');
  const toast = document.getElementById('yt-toast');

  // Reset
  error.classList.remove('show');
  error.textContent = '';
  container.classList.remove('show');
  metadata.classList.remove('show');
  actions.style.display = 'none';
  toast.classList.remove('show');

  const videoId = extractVideoId(input.value);
  if (!videoId) {
    error.textContent = '❌ Could not extract video ID from that link. Try a standard YouTube URL like youtube.com/watch?v=...';
    error.classList.add('show');
    return;
  }

  loading.classList.add('show');
  btn.disabled = true;

  try {
    const res = await fetch(`/tools/youtube-transcript/api?videoId=${videoId}`);
    const data = await res.json();

    if (!res.ok || data.error) {
      throw new Error(data.error || `Server returned ${res.status}`);
    }

    lastSegments = data.segments;

    // Metadata
    metadata.innerHTML = `
      <strong>Video:</strong> ${videoId}
      · <strong>Language:</strong> ${data.languageName || data.language}
      · <strong>${data.totalSegments}</strong> segments
    `;
    metadata.classList.add('show');

    // If segments came back empty, try browser-side fetch from timedtext URL
    if (data.segments.length === 0 && data._timedtextUrl) {
      loading.textContent = '⏳ Fetching transcript (browser fallback)...';
      loading.classList.add('show');
      try {
        const fallbackRes = await fetch(data._timedtextUrl);
        const fallbackXml = await fallbackRes.text();
        const parsed = parseTimedtextXml(fallbackXml);
        if (parsed.length > 0) {
          lastSegments = parseTimedtextXml(fallbackXml, data.language);
          metadata.innerHTML = `
            <strong>Video:</strong> ${videoId}
            · <strong>Language:</strong> ${data.languageName || data.language}
            · <strong>${lastSegments.length}</strong> segments
          `;
          data.segments = lastSegments;
        }
      } catch (e) {
        // Fallback failed too, show the CF response
      }
      loading.classList.remove('show');
    }

    // Render segments
    container.innerHTML = data.segments.map((seg, i) => {
      const ts = formatTime(seg.start);
      return `<div class="segment" onclick="copySegment(${i})" title="Click to copy this line">
        <span class="timestamp">${ts}</span>
        <span class="text">${escapeHtml(seg.text)}</span>
      </div>`;
    }).join('');

    container.classList.add('show');
    actions.style.display = 'flex';
  } catch (err) {
    error.textContent = `❌ ${err.message}. The video may not have captions available.`;
    error.classList.add('show');
  } finally {
    loading.classList.remove('show');
    btn.disabled = false;
  }
}

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

// Browser-side XML parser for timedtext fallback
function parseTimedtextXml(xml, lang) {
  const segments = [];
  const parser = new DOMParser();
  const doc = parser.parseFromString(xml, 'text/xml');
  const texts = doc.querySelectorAll('text');
  texts.forEach(el => {
    const text = decodeXmlEntities(el.textContent).trim();
    if (text) {
      segments.push({
        text,
        start: parseFloat(el.getAttribute('start')) || 0,
        duration: parseFloat(el.getAttribute('dur')) || 0,
      });
    }
  });
  if (segments.length > 0) return segments;
  // Try srv3 format
  const pEls = doc.querySelectorAll('p');
  pEls.forEach(p => {
    const t = p.getAttribute('t');
    const d = p.getAttribute('d');
    const text = p.textContent.trim();
    if (text && t) {
      segments.push({ text, start: parseInt(t) / 1000, duration: d ? parseInt(d) / 1000 : 0 });
    }
  });
  return segments;
}

function decodeXmlEntities(text) {
  const d = document.createElement('div');
  d.innerHTML = text;
  return d.textContent || d.innerText || '';
}

function showToast(msg) {
  const t = document.getElementById('yt-toast');
  t.textContent = msg || 'Copied!';
  t.classList.remove('show');
  void t.offsetWidth; // reflow
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 1800);
}

function copySegment(index) {
  const seg = lastSegments[index];
  if (!seg) return;
  const text = `${formatTime(seg.start)}  ${seg.text}`;
  navigator.clipboard.writeText(text).then(() => showToast('Copied line!'));
}

async function copyTranscript(mode) {
  if (!lastSegments.length) return;
  const text = lastSegments.map(s => {
    if (mode === 'timestamps') return `${formatTime(s.start)}  ${s.text}`;
    return s.text;
  }).join('\n');
  try {
    await navigator.clipboard.writeText(text);
    showToast(mode === 'timestamps' ? 'Copied with timestamps!' : 'Copied text!');
  } catch {
    // Fallback
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
    showToast('Copied!');
  }
}

function exportTranscript(format) {
  if (!lastSegments.length) return;
  let content = '';
  let filename = '';

  switch (format) {
    case 'srt': {
      filename = 'transcript.srt';
      content = lastSegments.map((s, i) => {
        const end = s.start + (s.duration || 3);
        return `${i + 1}\n${srtTime(s.start)} --> ${srtTime(end)}\n${s.text}\n`;
      }).join('\n');
      break;
    }
    case 'md': {
      filename = 'transcript.md';
      content = `# YouTube Transcript\n\n`;
      content += lastSegments.map(s =>
        `**${formatTime(s.start)}** ${s.text}`
      ).join('\n\n');
      break;
    }
    case 'txt': {
      filename = 'transcript.txt';
      content = lastSegments.map(s =>
        `${formatTime(s.start)}  ${s.text}`
      ).join('\n');
      break;
    }
  }

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
  showToast(`Downloaded ${filename}`);
}

function srtTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 1000);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(ms).padStart(3, '0')}`;
}
</script>

---

Looking for a quick way to get the text from any YouTube video? This free **YouTube transcript extractor** pulls captions from any video that has them — whether manually uploaded or auto-generated by YouTube. No sign-up, no limits, no ads.

Researchers use it to quote video sources. Students grab lecture transcripts for notes. Content creators repurpose their own videos into blog posts and social threads. Podcasters extract interviews for show notes.

## How it works

1. **Paste** any YouTube link into the box above — `youtube.com/watch?v=...`, `youtu.be/...`, or even just the raw 11-character video ID
2. **Click** "Get Transcript" — the tool fetches caption tracks via Cloudflare's edge network
3. **Read, copy, or export** the full transcript with timestamps

The tool works on any video with captions enabled — including auto-generated captions available on the vast majority of English YouTube videos.

### Export options

| Format | What you get | Best for |
|--------|-------------|----------|
| **Copy Text** | Plain text, no timestamps | Pasting into a document or notes app |
| **Copy with Timestamps** | Timestamp + text per line | Citing specific parts of a video |
| **Export SRT** | Subtitle format | Importing into a video editor like [Descript](/tools/descript/) or Premiere |
| **Export Markdown** | Timestamps as headings | Note-taking in Obsidian, Notion, or Markdown editors |
| **Export TXT** | Timestamped plain text file | Archiving or processing with other tools |

## Who needs a YouTube transcript extractor?

**Students & researchers** — Grab lecture transcripts, interview quotes, or conference talk text without rewatching. Click any timestamped line to jump-reference it later.

**Content creators** — Repurpose your own YouTube videos into blog posts, Twitter threads, or newsletter content. Paste the transcript into [Claude](/tools/claude/) or ChatGPT to generate summaries, social copy, or SEO-optimized articles.

**Podcasters & video editors** — Export transcripts as SRT files and import them directly into editing software for subtitle overlays. Combine with [Descript](/tools/descript/) for AI-powered editing.

**Non-native speakers** — Read along with the transcript while watching to improve comprehension. Translate segments with any online translator.

**Marketers & SEO writers** — Mine competitor videos for topic ideas, quotes, and structure. Transcripts reveal exactly what keywords and questions a video targets.

## Related tools on AI Tools Solo

If you work with video and audio content, these tools pair well with a transcript extractor:

- [**Descript**](/tools/descript/) — AI-powered video/audio editor that also generates transcripts and lets you edit by deleting text
- [**Captions**](/tools/captions/) — Add AI-generated captions to your videos for social media
- [**Otter.ai**](/tools/otter/) — Real-time meeting transcription and note-taking
- [**VEED**](/tools/veed/) — Online video editor with automatic subtitles
- [**Submagic**](/tools/submagic/) — AI-powered short-form video captions for TikTok, Reels, and Shorts
- [**Opus Clip**](/tools/opus-clip/) — Clip and repurpose long videos into shorts with AI

## FAQ

### Q: Does every YouTube video have a transcript available?

No. Only videos with captions enabled — either manually uploaded by the creator or auto-generated by YouTube. Most English-language videos with clear audio have auto-generated captions, but some older or music-only videos may not.

### Q: Is this tool free?

Yes, completely free. No sign-up, no API keys, no usage limits. You can extract as many transcripts as you want.

### Q: What languages are supported?

Any language that YouTube provides captions for. The tool detects the available caption tracks and returns the best match for your preferred language (English by default).

### Q: Can I download the transcript as a subtitle file?

Yes. Click **Export SRT** to download a standard `.srt` subtitle file compatible with Premiere Pro, DaVinci Resolve, Final Cut Pro, and most video editors. You can also export as Markdown or plain text.

### Q: How accurate are the transcripts?

Auto-generated captions (marked as "English (auto-generated)") are typically 80–95% accurate depending on audio quality, accent, and background noise. Manually uploaded captions are 100% accurate. For critical work, verify against the original audio.

### Q: What's the difference between "Copy Text" and "Copy with Timestamps"?

**Copy Text** gives you just the spoken words — useful for getting the gist or pasting into a summary tool. **Copy with Timestamps** includes the time code before each line (e.g., `1:23  This is what was said`) — useful for citing specific moments in the video.

### Q: Can I use the transcript for commercial purposes?

Yes. The transcript text itself is not copyrighted (it's a factual rendering of spoken content). Use it for research, content creation, subtitling, or any other purpose.

