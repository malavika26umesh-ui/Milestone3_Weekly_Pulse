import os
import json
import base64
from mcp.server.fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText

import sys

# If modifying these SCOPES, delete the file token_gmail.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

mcp = FastMCP("Gmail")

def get_gmail_service():
    if not os.path.exists('credentials.json') and not os.path.exists('token_gmail.json'):
        sys.stderr.write("WARNING: credentials.json not found. Running Gmail MCP in MOCK MODE.\n")
        return None

    creds = None
    if os.path.exists('token_gmail.json'):
        creds = Credentials.from_authorized_user_file('token_gmail.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token_gmail.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

@mcp.tool()
def create_pulse_draft(to_email: str, subject: str, body_html: str) -> str:
    """
    Creates a Gmail draft for a Product Pulse report.
    """
    service = get_gmail_service()
    
    if not service:
        return f"[MOCK MODE] Would have created Gmail draft for {to_email} with subject: {subject}"

    try:
        message = MIMEText(body_html, 'html')
        message['to'] = to_email
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        draft = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw_message}}
        ).execute()
        
        return f"Successfully created Gmail draft (ID: {draft['id']}) for {to_email}."
    except Exception as e:
        return f"Error creating Gmail draft: {str(e)}"

if __name__ == "__main__":
    mcp.run()
