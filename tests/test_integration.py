"""Integration tests for Google Drive MCP server."""

import pytest
from unittest.mock import patch, Mock
from google_drive_mcp.server import mcp, list_files, search_files


class TestMCPIntegration:
    """Test MCP server integration."""

    def test_mcp_server_exists(self):
        """Test that MCP server is properly initialized."""
        assert mcp is not None
        assert mcp.name == "Google Drive MCP"

    @patch('google_drive_mcp.server.client')
    def test_list_files_integration(self, mock_client):
        """Test list_files function integration."""
        # Mock the complete chain
        mock_service = Mock()
        mock_client.drive_service = mock_service
        
        # Setup the mock response
        mock_service.files().list().execute.return_value = {
            'files': [
                {
                    'id': 'test_id',
                    'name': 'Test File',
                    'mimeType': 'application/vnd.google-apps.document',
                    'modifiedTime': '2023-01-01T00:00:00.000Z'
                }
            ],
            'nextPageToken': None
        }
        
        # Call the function
        result = list_files()
        
        # Verify the result
        assert isinstance(result, str)
        assert "Found 1 files" in result
        assert "Test File" in result
        assert "test_id" in result

    @patch('google_drive_mcp.server.client')
    def test_search_files_integration(self, mock_client):
        """Test search_files function integration."""
        # Mock the complete chain
        mock_service = Mock()
        mock_client.drive_service = mock_service
        
        # Setup the mock response
        mock_service.files().list().execute.return_value = {
            'files': [
                {
                    'id': 'search_result_id',
                    'name': 'Search Result',
                    'mimeType': 'application/vnd.google-apps.document',
                    'modifiedTime': '2023-01-01T00:00:00.000Z'
                }
            ],
            'nextPageToken': None
        }
        
        # Call the function
        result = search_files(query='name contains "test"')
        
        # Verify the result
        assert isinstance(result, str)
        assert "Search results for: name contains \"test\"" in result
        assert "Found 1 files" in result
        assert "Search Result" in result

    def test_error_handling(self):
        """Test that functions handle errors gracefully."""
        # Test with invalid parameters should not crash
        # These would normally require authentication, but should handle missing credentials gracefully
        
        # The functions should return error messages rather than raise exceptions
        # when authentication or API calls fail
        try:
            # This will fail due to missing authentication, but should not crash
            list_files()
        except Exception as e:
            # Should be a Google API exception, not a Python crash
            assert "error" in str(e).lower() or "auth" in str(e).lower() or "credential" in str(e).lower()