"""Google Drive authentication and API client setup."""

import json
import os
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents'
]


class GoogleDriveClient:
    """Google Drive API client with authentication."""
    
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._drive_service = None
        self._docs_service = None
        self._creds = None
    
    def authenticate(self) -> bool:
        """Authenticate with Google Drive API."""
        creds = None
        
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found at {self.credentials_path}. "
                        "Please download it from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        self._creds = creds
        return True
    
    @property
    def drive_service(self):
        """Get Google Drive service."""
        if not self._drive_service:
            if not self._creds:
                self.authenticate()
            self._drive_service = build('drive', 'v3', credentials=self._creds)
        return self._drive_service
    
    @property
    def docs_service(self):
        """Get Google Docs service."""
        if not self._docs_service:
            if not self._creds:
                self.authenticate()
            self._docs_service = build('docs', 'v1', credentials=self._creds)
        return self._docs_service