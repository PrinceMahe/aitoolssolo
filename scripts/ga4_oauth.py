#!/usr/bin/env python3
"""OAuth flow - prints URL for user to approve"""
import os, sys, socket
from google_auth_oauthlib.flow import InstalledAppFlow

# Find a free port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 0))
port = s.getsockname()[1]
s.close()

client_secret = os.path.expanduser('~/.secrets_bak_20260727/ga4_client_secret.json')
SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']

flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
creds = flow.run_local_server(
    open_browser=False,
    port=port,
    success_message='Auth complete! You can close this tab.'
)

print('AUTH_OK')
# Save token
token_path = os.path.expanduser('~/.ga4_token.json')
with open(token_path, 'w') as f:
    f.write(creds.to_json())
print(f'Token saved to {token_path}')
