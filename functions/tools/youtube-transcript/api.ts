interface TranscriptSegment {
  text: string;
  start: number;
  duration: number;
  lang: string;
}

export async function onRequest(context: { request: Request }): Promise<Response> {
  const url = new URL(context.request.url);
  const videoId = url.searchParams.get('videoId');
  const lang = url.searchParams.get('lang') || 'en';

  if (!videoId || !/^[A-Za-z0-9_-]{11}$/.test(videoId)) {
    return new Response(JSON.stringify({ error: 'Invalid videoId' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    });
  }

  try {
    // Try InnerTube API first (Android client — works from CF edge)
    let segments = await fetchViaInnerTube(videoId, lang);

    // Fallback: parse from web page HTML
    if (!segments || segments.length === 0) {
      segments = await fetchViaWebPage(videoId, lang);
    }

    if (!segments || segments.length === 0) {
      return new Response(JSON.stringify({ error: 'No captions available for this video' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      });
    }

    return new Response(
      JSON.stringify({
        videoId,
        language: segments[0].lang || lang,
        segments: segments.map((s) => ({
          text: s.text,
          start: s.start,
          duration: s.duration,
        })),
        totalSegments: segments.length,
      }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'public, max-age=3600, s-maxage=3600',
        },
      }
    );
  } catch (err: any) {
    return new Response(
      JSON.stringify({
        error: err?.message || 'Unknown error fetching transcript',
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      }
    );
  }
}

/**
 * Fetch transcript via InnerTube API (Android client context)
 * This is the preferred method — YouTube's own apps use this endpoint.
 */
async function fetchViaInnerTube(videoId: string, lang: string): Promise<TranscriptSegment[] | null> {
  try {
    const resp = await fetch('https://www.youtube.com/youtubei/v1/player?prettyPrint=false', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'com.google.android.youtube/20.10.38 (Linux; U; Android 14)',
      },
      body: JSON.stringify({
        context: {
          client: {
            clientName: 'ANDROID',
            clientVersion: '20.10.38',
          },
        },
        videoId,
      }),
    });

    if (!resp.ok) return null;

    const data: any = await resp.json();
    const captionTracks: any[] | undefined =
      data?.captions?.playerCaptionsTracklistRenderer?.captionTracks;

    if (!captionTracks || captionTracks.length === 0) return null;

    // Select best track
    let track = captionTracks.find((t) => t.languageCode === lang);
    if (!track) track = captionTracks.find((t) => t.languageCode?.startsWith(lang.split('-')[0]));
    if (!track) track = captionTracks[0];

    const trackLang = track.languageCode;
    let transcriptUrl = track.baseUrl;
    // Fix YouTube's escaped unicode in URL
    transcriptUrl = transcriptUrl.replace(/\\u0026/g, '&');

    // Fetch the transcript
    const transcriptRes = await fetch(transcriptUrl, {
      headers: {
        'User-Agent': 'com.google.android.youtube/20.10.38 (Linux; U; Android 14)',
        'Accept-Language': 'en-US,en;q=0.9',
      },
    });

    if (!transcriptRes.ok) return null;
    const xml = await transcriptRes.text();
    if (!xml || xml.trim().length === 0) return null;

    return parseTranscriptXml(xml, trackLang);
  } catch {
    return null;
  }
}

/**
 * Fallback: fetch transcript by scraping the web page HTML
 */
async function fetchViaWebPage(videoId: string, lang: string): Promise<TranscriptSegment[] | null> {
  try {
    const pageRes = await fetch(`https://www.youtube.com/watch?v=${videoId}`, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
      },
    });

    const html = await pageRes.text();

    // Extract ytInitialPlayerResponse via brace counting
    const playerResponse = parseInlineJson(html, 'ytInitialPlayerResponse');
    if (!playerResponse) return null;

    const captionTracks: any[] | undefined =
      playerResponse?.captions?.playerCaptionsTracklistRenderer?.captionTracks;

    if (!captionTracks || captionTracks.length === 0) return null;

    let track = captionTracks.find((t) => t.languageCode === lang);
    if (!track) track = captionTracks.find((t) => t.languageCode?.startsWith(lang.split('-')[0]));
    if (!track) track = captionTracks[0];

    const trackLang = track.languageCode;
    let transcriptUrl = track.baseUrl;
    transcriptUrl = transcriptUrl.replace(/\\u0026/g, '&');

    // Collect cookies from the page response
    const cookies: string[] = [];
    pageRes.headers.forEach((value: string, key: string) => {
      if (key.toLowerCase() === 'set-cookie') {
        cookies.push(value.split(';')[0]);
      }
    });

    const transcriptRes = await fetch(transcriptUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': `https://www.youtube.com/watch?v=${videoId}`,
        ...(cookies.length > 0 ? { 'Cookie': cookies.join('; ') } : {}),
      },
    });

    if (!transcriptRes.ok) return null;
    const xml = await transcriptRes.text();
    if (!xml || xml.trim().length === 0) return null;

    return parseTranscriptXml(xml, trackLang);
  } catch {
    return null;
  }
}

/**
 * Parse transcript XML. Supports both:
 * - srv3 format: <p t="ms" d="ms"><s>word</s></p>
 * - classic format: <text start="s" dur="s">content</text>
 */
function parseTranscriptXml(xml: string, lang: string): TranscriptSegment[] {
  const results: TranscriptSegment[] = [];

  // Try srv3 format first
  const pRegex = /<p\s+t="(\d+)"\s+d="(\d+)"[^>]*>([\s\S]*?)<\/p>/g;
  let match;
  while ((match = pRegex.exec(xml)) !== null) {
    const startMs = parseInt(match[1], 10);
    const durMs = parseInt(match[2], 10);
    const inner = match[3];
    let text = '';
    const sRegex = /<s[^>]*>([^<]*)<\/s>/g;
    let sMatch;
    while ((sMatch = sRegex.exec(inner)) !== null) {
      text += sMatch[1];
    }
    if (!text) {
      text = inner.replace(/<[^>]+>/g, '');
    }
    text = decodeEntities(text).trim();
    if (text) {
      results.push({
        text,
        duration: durMs / 1000,
        start: startMs / 1000,
        lang,
      });
    }
  }

  if (results.length > 0) return results;

  // Fall back to classic format: <text start="s" dur="s">content</text>
  const classicRegex = /<text start="([^"]*)" dur="([^"]*)">([^<]*)<\/text>/g;
  while ((match = classicRegex.exec(xml)) !== null) {
    let text = decodeEntities(match[3]).trim();
    if (text) {
      results.push({
        text,
        start: parseFloat(match[1]),
        duration: parseFloat(match[2]),
        lang,
      });
    }
  }

  return results;
}

/**
 * Extract a JSON object assigned to a global variable in inline script tags
 */
function parseInlineJson(html: string, globalName: string): any {
  const startToken = `var ${globalName} = `;
  const startIndex = html.indexOf(startToken);
  if (startIndex === -1) return null;

  const jsonStart = startIndex + startToken.length;
  let depth = 0;
  for (let i = jsonStart; i < html.length; i++) {
    if (html[i] === '{') depth++;
    else if (html[i] === '}') {
      depth--;
      if (depth === 0) {
        try {
          return JSON.parse(html.slice(jsonStart, i + 1));
        } catch {
          return null;
        }
      }
    }
  }
  return null;
}

/**
 * Decode common HTML entities
 */
function decodeEntities(text: string): string {
  return text
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&apos;/g, "'")
    .replace(/&#x([0-9a-fA-F]+);/g, (_, hex) => String.fromCodePoint(parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, dec) => String.fromCodePoint(parseInt(dec, 10)));
}
