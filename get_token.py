import os
from google_auth_oauthlib.flow import InstalledAppFlow
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

# The scopes required to create calendar events
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def main():
    # You can temporarily hardcode your credentials here just to get the token
    client_config = {
        "installed": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=8080)
    
    print("\nSUCCESS! Add this line to your .env file:\n")
    print(f"GOOGLE_REFRESH_TOKEN=\"{creds.refresh_token}\"")

if __name__ == '__main__':
    main()