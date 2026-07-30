#!/usr/bin/env python3
"""GA4 OAuth Desktop Flow — runs a local HTTP server, opens the browser for
consent, captures the redirect, exchanges code for tokens, and saves them.

Usage: python scripts/ga4_oauth_flow.py
After approval, tokens saved to scripts/.ga4_user_token.json
"""
import os, sys, json, socket, urllib.parse, urllib.request, threading, time, webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8989
CLIENT_SECRET = r'scripts/ga4_client_secret.json'
TOKEN_FILE = r'scripts/.ga4_user_token.json'
SCOPE = 'https://www.googleapis.com/auth/analytics.readonly'

with open(CLIENT_SECRET) as f:
    cfg = json.load(f)['installed']

AUTH_URL = (f"{cfg['auth_uri']}?client_id={cfg['client_id']}"
            f"&redirect_uri=http://localhost:{PORT}"
            f"&response_type=code&scope={urllib.parse.quote(SCOPE)}"
            f"&access_type=offline&prompt=consent")

auth_code = None
server = None

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        qs = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(qs)
        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Authorized!</h1><p>You can close this tab.</p></body></html>')
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Missing code</h1>')
        # Shutdown in a thread to avoid deadlock
        threading.Thread(target=self.server.shutdown, daemon=True).start()
    def log_message(self, *a):
        pass  # quiet

print("=== GA4 OAuth Desktop Flow ===")
print(f"Starting local server on http://localhost:{PORT} ...")

server = HTTPServer(('127.0.0.1', PORT), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
time.sleep(0.5)

print(f"Opening browser to Google OAuth consent...")
print(f"\nURL: {AUTH_URL}\n")
try:
    webbrowser.open(AUTH_URL)
except:
    print("(could not auto-open browser — see URL above)")

# Wait up to 120s for the redirect
deadline = time.time() + 120
while auth_code is None and time.time() < deadline:
    time.sleep(0.5)
server.server_close()

if not auth_code:
    print("❌ Timed out waiting for OAuth consent (120s).")
    sys.exit(1)

print(f"✅ Auth code received. Exchanging for tokens...")

# Exchange code for tokens
data = urllib.parse.urlencode({
    'code': auth_code,
    'client_id': cfg['client_id'],
    'client_secret': cfg['client_secret'],
    'redirect_uri': f'http://localhost:{PORT}',
    'grant_type': 'authorization_code',
}).encode()
req = urllib.request.Request(cfg['token_uri'], data=data,
    headers={'Content-Type': 'application/x-www-form-urlencoded'})
resp = urllib.request.urlopen(req)
token_data = json.loads(resp.read())

# Save
token_data['client_id'] = cfg['client_id']
token_data['client_secret'] = cfg['client_secret']
token_data['token_uri'] = cfg['token_uri']
os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
with open(TOKEN_FILE, 'w') as f:
    json.dump(token_data, f, indent=2)
print(f"✅ Token saved to {TOKEN_FILE}")
print(f"   Scopes: {token_data.get('scope', 'N/A')}")
print(f"   Refresh token: {'✅' if token_data.get('refresh_token') else '❌ (will expire hourly)'}")
print(f"\nDONE — GA4 access ready. Run scripts/ga4_snapshot.py to test.")