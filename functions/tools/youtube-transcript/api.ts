interface TranscriptSegment {
  text: string;
  start: number;
  duration: number;
}

interface CaptionTrack {
  baseUrl: string;
  languageCode: string;
  name?: { simpleText?: string };
  kind?: string;
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
    // 1. Fetch YouTube video page
    const pageRes = await fetch(`https://www.youtube.com/watch?v=${videoId}`, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
      },
    });
    const html = await pageRes.text();

    // 2. Extract ytInitialPlayerResponse from HTML using brace counting
    let playerResponse: any = null;

    const playerVar = 'ytInitialPlayerResponse = ';
    const startIdx = html.indexOf(playerVar);
    if (startIdx !== -1) {
      const jsonStart = startIdx + playerVar.length;
      let depth = 0;
      let endIdx = jsonStart;

      for (let i = jsonStart; i < html.length; i++) {
        const ch = html[i];
        if (ch === '{') depth++;
        else if (ch === '}') {
          depth--;
          if (depth === 0) {
            endIdx = i + 1;
            break;
          }
        }
      }

      if (depth === 0) {
        try {
          playerResponse = JSON.parse(html.substring(jsonStart, endIdx));
        } catch {
          // fall through
        }
      }
    }

    // Fallback: try ytInitialData
    if (!playerResponse?.captions?.playerCaptionsTracklistRenderer) {
      const dataMatch = html.match(/ytInitialData\s*=\s*({[\s\S]+?});\s*\n/);
      if (dataMatch) {
        try {
          const data = JSON.parse(dataMatch[1]);
          const engagementPanels = data?.engagementPanels ?? [];
          for (const panel of engagementPanels) {
            const panelRenderer = panel?.engagementPanelSectionListRenderer;
            if (panelRenderer?.content?.structuredDescriptionContent?.items) {
              for (const item of panelRenderer.content.structuredDescriptionContent.items) {
                const video = item?.videoDescriptionHeaderRenderer;
                if (video?.captions?.captionTracks?.length) {
                  playerResponse = { captions: { playerCaptionsTracklistRenderer: { captionTracks: video.captions.captionTracks } } };
                  break;
                }
              }
            }
          }
        } catch {
          // fall through
        }
      }
    }

    // 3. Extract caption tracks
    const captionTracks: CaptionTrack[] | undefined =
      playerResponse?.captions?.playerCaptionsTracklistRenderer?.captionTracks;

    if (!captionTracks || captionTracks.length === 0) {
      return new Response(JSON.stringify({ error: 'No captions available for this video' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      });
    }

    // 4. Find best matching track — prefer requested language, then auto-generated, then first
    let track = captionTracks.find((t: CaptionTrack) => t.languageCode === lang);
    if (!track) track = captionTracks.find((t: CaptionTrack) => t.languageCode?.startsWith(lang.split('-')[0]));
    if (!track) track = captionTracks[0];

    // 5. Fetch the transcript XML
    const transcriptUrl = track.baseUrl;
    const transcriptRes = await fetch(transcriptUrl);
    const transcriptXml = await transcriptRes.text();

    // 6. Parse XML to segments
    const segments = parseTranscriptXml(transcriptXml);

    // 7. Return as JSON
    return new Response(
      JSON.stringify({
        videoId,
        language: track.languageCode,
        languageName: track.name?.simpleText || track.languageCode,
        segments,
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
  } catch (err) {
    return new Response(
      JSON.stringify({
        error: err instanceof Error ? err.message : 'Unknown error fetching transcript',
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      }
    );
  }
}

function parseTranscriptXml(xml: string): TranscriptSegment[] {
  const segments: TranscriptSegment[] = [];

  // Match <text start="..." dur="...">content</text>
  const regex = /<text\s+start="([\d.]+)"(?:\s+dur="([\d.]+)")?\s*>([\s\S]*?)<\/text>/g;
  let match;

  while ((match = regex.exec(xml)) !== null) {
    const start = parseFloat(match[1]);
    const duration = match[2] ? parseFloat(match[2]) : 0;
    let text = match[3]
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/<[^>]*>/g, '') // strip any remaining XML tags
      .replace(/\s+/g, ' ')
      .trim();

    if (text) {
      segments.push({ text, start, duration });
    }
  }

  return segments;
}

function formatTimestamp(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}
