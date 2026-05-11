import os
import json
from mcp.server.fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from typing import List, Dict

import sys

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents']

mcp = FastMCP("Google Docs")

def get_docs_service():
    if not os.path.exists('credentials.json') and not os.path.exists('token.json'):
        sys.stderr.write("WARNING: credentials.json not found. Running Google Docs MCP in MOCK MODE.\n")
        return None

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('docs', 'v1', credentials=creds)

@mcp.tool()
def append_to_document(document_id: str, heading_text: str, content_markdown: str) -> str:
    """
    Appends a new section to a Google Doc with a heading and formatted content.
    """
    service = get_docs_service()
    
    if not service:
        mock_result = {
            "document_id": document_id,
            "status": "mock_success",
            "message": f"[MOCK MODE] Would have appended section '{heading_text}' to Doc ID {document_id}"
        }
        return json.dumps(mock_result)
    
    # 1. Get current document length to append at the end
    doc = service.documents().get(documentId=document_id).execute()
    index = doc.get('body').get('content')[-1].get('endIndex') - 1

    requests = [
        # Insert Heading
        {
            'insertText': {
                'location': {'index': index},
                'text': f"\n{heading_text}\n"
            }
        },
        # Format Heading as HEADING_2
        {
            'updateParagraphStyle': {
                'range': {'startIndex': index + 1, 'endIndex': index + len(heading_text) + 1},
                'paragraphStyle': {'namedStyleType': 'HEADING_2'},
                'fields': 'namedStyleType'
            }
        },
        # Insert Content
        {
            'insertText': {
                'location': {'index': index + len(heading_text) + 2},
                'text': f"{content_markdown}\n"
            }
        }
    ]

    service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
    
    result = {
        "document_id": document_id,
        "status": "success",
        "message": f"Successfully appended section '{heading_text}' to document {document_id}."
    }
    return json.dumps(result)

if __name__ == "__main__":
    mcp.run()
