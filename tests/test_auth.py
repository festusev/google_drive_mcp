"""Tests for authentication module."""

from unittest.mock import Mock, mock_open, patch

import pytest

from google_drive_mcp.auth import GoogleDriveClient


class TestGoogleDriveClient:
    """Test GoogleDriveClient authentication."""

    def test_init(self):
        """Test client initialization."""
        client = GoogleDriveClient()
        assert client.credentials_path == "credentials.json"
        assert client.token_path == "token.json"
        assert client._drive_service is None
        assert client._docs_service is None
        assert client._creds is None

    def test_init_custom_paths(self):
        """Test client initialization with custom paths."""
        client = GoogleDriveClient("custom_creds.json", "custom_token.json")
        assert client.credentials_path == "custom_creds.json"
        assert client.token_path == "custom_token.json"

    @patch("google_drive_mcp.auth.Credentials.from_authorized_user_file")
    @patch("os.path.exists")
    def test_authenticate_existing_valid_token(
        self, mock_exists, mock_from_file, mock_credentials
    ):
        """Test authentication with existing valid token."""
        mock_exists.return_value = True
        mock_from_file.return_value = mock_credentials

        client = GoogleDriveClient()
        result = client.authenticate()

        assert result is True
        assert client._creds == mock_credentials
        mock_from_file.assert_called_once_with(
            "token.json",
            [
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/documents",
            ],
        )

    @patch("google_drive_mcp.auth.Credentials.from_authorized_user_file")
    @patch("google_drive_mcp.auth.Request")
    @patch("os.path.exists")
    def test_authenticate_expired_token_refresh(
        self, mock_exists, mock_request, mock_from_file
    ):
        """Test authentication with expired token that can be refreshed."""
        mock_exists.return_value = True

        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token"
        mock_creds.to_json.return_value = '{"mock": "credentials"}'
        mock_from_file.return_value = mock_creds

        with patch("builtins.open", mock_open()):
            client = GoogleDriveClient()
            result = client.authenticate()

        assert result is True
        assert client._creds == mock_creds
        mock_creds.refresh.assert_called_once()

    @patch("google_drive_mcp.auth.InstalledAppFlow.from_client_secrets_file")
    @patch("os.path.exists")
    def test_authenticate_new_flow(self, mock_exists, mock_flow):
        """Test authentication with new OAuth flow."""

        def exists_side_effect(path):
            if path == "token.json":
                return False
            elif path == "credentials.json":
                return True
            return False

        mock_exists.side_effect = exists_side_effect

        mock_creds = Mock()
        mock_creds.to_json.return_value = '{"mock": "credentials"}'

        mock_flow_instance = Mock()
        mock_flow_instance.run_local_server.return_value = mock_creds
        mock_flow.return_value = mock_flow_instance

        with patch("builtins.open", mock_open()):
            client = GoogleDriveClient()
            result = client.authenticate()

        assert result is True
        assert client._creds == mock_creds
        mock_flow.assert_called_once_with(
            "credentials.json",
            [
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/documents",
            ],
        )
        mock_flow_instance.run_local_server.assert_called_once_with(port=0)

    @patch("os.path.exists")
    def test_authenticate_missing_credentials(self, mock_exists):
        """Test authentication fails when credentials file is missing."""

        def exists_side_effect(path):
            return False

        mock_exists.side_effect = exists_side_effect

        client = GoogleDriveClient()

        with pytest.raises(FileNotFoundError, match="Credentials file not found"):
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
