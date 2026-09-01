import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Token refresh failed ({e}). Re-authenticating...")
                creds = None

        if not creds:
            creds_file = 'credentials.json' if os.path.exists('credentials.json') else ('new_credentials.json' if os.path.exists('new_credentials.json') else None)
            if not creds_file:
                print("No token or credentials.json found. Please put credentials.json in this folder.")
                return
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            print("Successfully authenticated and generated token.json!")

if __name__ == "__main__":
    main()
