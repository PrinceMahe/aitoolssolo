"""GA4 OAuth helper - opens browser, catches redirect, saves token."""
import os, sys, threading, webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
CLIENT_SECRET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ga4_client_secret.json")
TOKEN_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".ga4_token.json")
REDIRECT_URI = "http://localhost"

class RedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if "code=" in self.path:
            # Extract code from query string
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            code = qs.get("code", [None])[0]
            if code:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Authorization successful!</h1><p>You may close this window.</p></body></html>")
                # Signal the main thread
                global auth_code
                auth_code = code
                return
        self.send_response(400)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Authorization failed</h1></body></html>")

    def log_message(self, format, *args):
        pass  # suppress server logs

def main():
    global auth_code
    auth_code = None

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, state = flow.authorization_url(prompt="consent", access_type="offline")

    print(f"Opening browser for authorization...")
    print(f"URL: {auth_url}")

    # Start a temporary server to catch the redirect
    server = HTTPServer(("localhost", 80), RedirectHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Open browser
    webbrowser.open(auth_url)

    # Wait for the redirect
    import time
    for _ in range(120):
        if auth_code:
            break
        time.sleep(0.5)

    server.shutdown()

    if not auth_code:
        print("ERROR: No authorization code received")
        sys.exit(1)

    print(f"Got authorization code: {auth_code[:20]}...")
    creds = flow.fetch_token(code=auth_code, redirect_uri=REDIRECT_URI)
    print(f"Got token: {creds.token[:20]}...")

    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())
    print(f"Token saved to {TOKEN_PATH}")

if __name__ == "__main__":
    main()
