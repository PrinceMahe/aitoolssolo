interface TranscriptSegment {
  text: string;
  start: number;
  duration: number;
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
    // Try InnerTube Android API to get caption tracks
    const tracks = await getCaptionTracks(videoId);
    if (!tracks || tracks.length === 0) {
      return new Response(JSON.stringify({ error: 'No captions available for this video' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      });
    }

    // Select best track
    let track = tracks.find((t: any) => t.languageCode === lang);
    if (!track) track = tracks.find((t: any) => t.languageCode?.startsWith(lang.split('-')[0]));
    if (!track) track = tracks[0];

    let transcriptUrl = track.baseUrl;
    // YouTube's JSON may have \\u0026 instead of &
    transcriptUrl = transcriptUrl.replace(/\\u0026/g, '&');

    // Try to fetch the transcript via YouTube's timedtext API
    const segments = await tryFetchTranscript(transcriptUrl, videoId);

    // Even if segments are empty, return track info + the download URL
    // so the browser can retry directly
    return new Response(
      JSON.stringify({
        videoId,
        language: track.languageCode,
        languageName: track.name?.simpleText || track.languageCode,
        segments: segments || [],
        totalSegments: segments?.length || 0,
        // Include the raw timedtext URL so the browser can retry
        _timedtextUrl: transcriptUrl,
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
 * Get caption tracks via InnerTube Android API (works from CF edge)
 */
async function getCaptionTracks(videoId: string): Promise<any[] | null> {
  try {
    const resp = await fetch('https://www.youtube.com/youtubei/v1/player?prettyPrint=false', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'com.google.android.youtube/20.10.38 (Linux; U; Android 14)',
      },
      body: JSON.stringify({
        context: { client: { clientName: 'ANDROID', clientVersion: '20.10.38' } },
        videoId,
      }),
    });
    if (!resp.ok) return null;
    const data: any = await resp.json();
    return data?.captions?.playerCaptionsTracklistRenderer?.captionTracks || null;
  } catch {
    return null;
  }
}

/**
 * Try to fetch transcript from YouTube's timedtext endpoint
 */
async function tryFetchTranscript(url: string, videoId: string): Promise<TranscriptSegment[] | null> {
  try {
    const resp = await fetch(url, {
      headers: {
        'User-Agent': 'com.google.android.youtube/20.10.38 (Linux; U; Android 14)',
        'Accept-Language': 'en-US,en;q=0.9',
      },
    });
    if (!resp.ok) return null;
    const xml = await resp.text();
    if (!xml || xml.trim().length < 20) return null;
    return parseTranscriptXml(xml);
  } catch {
    return null;
  }
}

/**
 * Parse transcript XML (srv3 + classic formats)
 */
function parseTranscriptXml(xml: string): TranscriptSegment[] {
  const results: TranscriptSegment[] = [];

  // Try srv3 format: <p t="ms" d="ms"><s>word</s></p>
  const pRegex = /<p\s+t="(\d+)"\s+d="(\d+)"[^>]*>([\s\S]*?)<\/p>/g;
  let match;
  while ((match = pRegex.exec(xml)) !== null) {
    const startMs = parseInt(match[1], 10);
    const durMs = parseInt(match[2], 10);
    const inner = match[3];
    let text = '';
    const sRegex = /<s[^>]*>([^<]*)<\/s>/g;
    let sMatch;
    while ((sMatch = sRegex.exec(inner)) !== null) text += sMatch[1];
    if (!text) text = inner.replace(/<[^>]+>/g, '');
    text = decodeEntities(text).trim();
    if (text) results.push({ text, duration: durMs / 1000, start: startMs / 1000 });
  }

  if (results.length > 0) return results;

  // Classic format: <text start="s" dur="s">content</text>
  const classicRegex = /<text start="([^"]*)" dur="([^"]*)">([^<]*)<\/text>/g;
  while ((match = classicRegex.exec(xml)) !== null) {
    let text = decodeEntities(match[3]).trim();
    if (text) results.push({ text, start: parseFloat(match[1]), duration: parseFloat(match[2]) });
  }

  return results;
}

function decodeEntities(text: string): string {
  return text
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&apos;/g, "'")
    .replace(/&#x([0-9a-fA-F]+);/g, (_, hex: string) => String.fromCodePoint(parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, dec: string) => String.fromCodePoint(parseInt(dec, 10)));
}
