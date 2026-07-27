import os, sys
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding, CreateAccessBindingRequest

SCOPES = ["https://www.googleapis.com/auth/analytics.manage.users"]
CLIENT_SECRET = r"C:\Users\prin-win\aitoolssolo\scripts\ga4_client_secret.json"
TOKEN_PATH = r"C:\Users\prin-win\aitoolssolo\.ga4_manage_token.json"
PROPERTY_ID = "537308820"
SA_EMAIL = "ga4-reader@aitoolssolo-ga4.iam.gserviceaccount.com"

def main():
    creds = None
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception as e:
            print(f"Error loading token: {e}", flush=True)
            
    if not creds or not creds.valid:
        print("Starting OAuth flow. Please visit the URL printed below to authorize this application.", flush=True)
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
        # run_local_server with open_browser=False prints the link and waits for authorization
        creds = flow.run_local_server(open_browser=False)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        print("OAuth token successfully saved.", flush=True)
            
    client = AnalyticsAdminServiceClient(credentials=creds)
    
    # Define binding
    access_binding = AccessBinding(
        user=SA_EMAIL,
        roles=["predefinedRoles/viewer"]
    )
    
    request = CreateAccessBindingRequest(
        parent=f"properties/{PROPERTY_ID}",
        access_binding=access_binding
    )
    
    print(f"Creating access binding for {SA_EMAIL} on properties/{PROPERTY_ID}...", flush=True)
    try:
        response = client.create_access_binding(request=request)
        print(f"Success! Created access binding: {response.name}", flush=True)
    except Exception as e:
        print(f"Error creating access binding: {e}", flush=True)

if __name__ == "__main__":
    main()
