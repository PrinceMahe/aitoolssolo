// Debug endpoint - returns HTML snippet to verify YouTube page is reachable
export async function onRequest(context) {
  const url = new URL(context.request.url);
  const videoId = url.searchParams.get('videoId') || 'jNQXAC9IVRw';

  try {
    const pageRes = await fetch(`https://www.youtube.com/watch?v=${videoId}`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
      },
    });

    const html = await pageRes.text();
    const hasPlayerResp = html.includes('ytInitialPlayerResponse');
    const hasCaptions = html.includes('captionTracks');

    // Extract a snippet around the player response
    let snippet = '';
    const marker = 'ytInitialPlayerResponse = ';
    const start = html.indexOf(marker);
    if (start !== -1) {
      snippet = html.substring(start, start + 200);
    }

    return new Response(JSON.stringify({
      status: pageRes.status,
      size: html.length,
      hasPlayerResp,
      hasCaptions,
      snippet,
      markerFound: start !== -1,
    }), {
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
    });
  } catch (err) {
    return new Response(JSON.stringify({
      error: err instanceof Error ? err.message : String(err),
    }), {
      status: 500,
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
    });
  }
}
