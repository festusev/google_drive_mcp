"""Tests for authentication module."""

from unittest.mock import Mock, patch

import pytest

from google_drive_mcp.auth import GoogleDriveClient


class TestGoogleDriveClient:
    """Test GoogleDriveClient authentication."""

    def test_init(self):
        """Test client initialization."""
        client = GoogleDriveClient()
        assert client.credentials_path == "service-account-key.json"
        assert client._drive_service is None
        assert client._docs_service is None
        assert client._creds is None

    def test_init_custom_paths(self):
        """Test client initialization with custom paths."""
        client = GoogleDriveClient("custom_service_account.json")
        assert client.credentials_path == "custom_service_account.json"

    @patch("google_drive_mcp.auth.Credentials.from_service_account_file")
    @patch("os.path.exists")
    def test_authenticate_service_account(
        self, mock_exists, mock_from_file
    ):
        """Test authentication with service account."""
        mock_exists.return_value = True
        mock_creds = Mock()
        mock_from_file.return_value = mock_creds

        client = GoogleDriveClient()
        result = client.authenticate()

        assert result is True
        assert client._creds == mock_creds
        mock_from_file.assert_called_once_with(
            "service-account-key.json",
            scopes=[
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/documents",
            ],
        )

    @patch("os.path.exists")
    def test_authenticate_missing_credentials(self, mock_exists):
        """Test authentication fails when credentials file is missing."""

        def exists_side_effect(path):
            return False

        mock_exists.side_effect = exists_side_effect

        client = GoogleDriveClient()

        with pytest.raises(
            FileNotFoundError, match="Service account key file not found"
        ):
            client.authenticate()

    @patch("google_drive_mcp.auth.build")
    def test_drive_service_property(self, mock_build, mock_google_client):
        """Test drive service property."""
        mock_service = Mock()
        mock_build.return_value = mock_service

        # Clear the cached service
        mock_google_client._drive_service = None

        service = mock_google_client.drive_service

        assert service == mock_service
        mock_build.assert_called_once_with(
            "drive", "v3", credentials=mock_google_client._creds
        )

    @patch("google_drive_mcp.auth.build")
    def test_docs_service_property(self, mock_build, mock_google_client):
        """Test docs service property."""
        mock_service = Mock()
        mock_build.return_value = mock_service

        # Clear the cached service
        mock_google_client._docs_service = None

        service = mock_google_client.docs_service

        assert service == mock_service
        mock_build.assert_called_once_with(
            "docs", "v1", credentials=mock_google_client._creds
        )
