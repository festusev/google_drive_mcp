"""Google Drive authentication and API client setup."""

import os
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]


class GoogleDriveClient:
    """Google Drive API client with service account authentication."""

    def __init__(self, credentials_path: str = "service-account-key.json"):
        self.credentials_path = credentials_path
        self._drive_service = None
        self._docs_service = None
        self._creds = None

    def authenticate(self) -> bool:
        """Authenticate with Google Drive API using service account."""
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(
                f"Service account key file not found at {self.credentials_path}. "
                "Please download it from Google Cloud Console."
            )

        self._creds = Credentials.from_service_account_file(
            self.credentials_path, scopes=SCOPES
        )
        return True

    @property
    def drive_service(self) -> Any:
        """Get Google Drive service."""
        if not self._drive_service:
            if not self._creds:
                self.authenticate()
            self._drive_service = build("drive", "v3", credentials=self._creds)
        return self._drive_service

    @property
    def docs_service(self) -> Any:
        """Get Google Docs service."""
        if not self._docs_service:
            if not self._creds:
                self.authenticate()
            self._docs_service = build("docs", "v1", credentials=self._creds)
        return self._docs_service
