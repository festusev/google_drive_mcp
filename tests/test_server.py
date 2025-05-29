"""Tests for server module."""

from unittest.mock import patch

from google_drive_mcp.server import (
    _extract_text_from_content,
    list_files,
    read_document,
    search_files,
    write_document,
)


@patch("google_drive_mcp.server.client")
class TestListFiles:
    """Test list_files function."""

    def test_list_files_default_params(self, mock_client, mock_drive_service):
        """Test list_files with default parameters."""
        mock_client.drive_service = mock_drive_service

        result = list_files()

        # Verify the API call
        mock_drive_service.files().list.assert_called_once_with(
            q="'root' in parents and trashed=false",
            pageSize=50,
            pageToken=None,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)",
        )

        # Verify the result format
        assert "Found 2 files" in result
        assert "Next page token: next_page_token" in result
        assert "Test Document 1" in result
        assert "Test Document 2" in result

    def test_list_files_with_folder_id(self, mock_client, mock_drive_service):
        """Test list_files with folder ID."""
        mock_client.drive_service = mock_drive_service

        list_files(folder_id="folder_123")

        mock_drive_service.files().list.assert_called_once_with(
            q="'folder_123' in parents and trashed=false",
            pageSize=50,
            pageToken=None,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)",
        )

    def test_list_files_with_mime_type(self, mock_client, mock_drive_service):
        """Test list_files with MIME type filter."""
        mock_client.drive_service = mock_drive_service

        list_files(mime_type="application/vnd.google-apps.document")

        mock_drive_service.files().list.assert_called_once_with(
            q="'root' in parents and mimeType='application/vnd.google-apps.document' and trashed=false",
            pageSize=50,
            pageToken=None,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)",
        )

    def test_list_files_page_size_limit(self, mock_client, mock_drive_service):
        """Test list_files respects maximum page size."""
        mock_client.drive_service = mock_drive_service

        list_files(page_size=150)  # Above max of 100

        mock_drive_service.files().list.assert_called_once_with(
            q="'root' in parents and trashed=false",
            pageSize=100,  # Should be capped at 100
            pageToken=None,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)",
        )


@patch("google_drive_mcp.server.client")
class TestSearchFiles:
    """Test search_files function."""

    def test_search_files_basic(self, mock_client, mock_drive_service):
        """Test search_files with basic query."""
        mock_client.drive_service = mock_drive_service

        result = search_files(query='name contains "test"')

        mock_drive_service.files().list.assert_called_once_with(
            q='(name contains "test") and trashed=false',
            pageSize=50,
            pageToken=None,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)",
        )

        assert 'Search results for: name contains "test"' in result
        assert "Found 2 files" in result

    def test_search_files_with_pagination(self, mock_client, mock_drive_service):
        """Test search_files with pagination."""
        mock_client.drive_service = mock_drive_service

        search_files(
            query='mimeType="application/vnd.google-apps.document"',
            page_size=25,
            page_token="page_token_123",
        )

        mock_drive_service.files().list.assert_called_once_with(
            q='(mimeType="application/vnd.google-apps.document") and trashed=false',
            pageSize=25,
            pageToken="page_token_123",
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)",
        )


@patch("google_drive_mcp.server.client")
class TestReadDocument:
    """Test read_document function."""

    def test_read_document_basic(self, mock_client, mock_docs_service):
        """Test read_document with basic parameters."""
        mock_client.docs_service = mock_docs_service

        result = read_document(document_id="doc_123")

        mock_docs_service.documents().get.assert_called_once_with(documentId="doc_123")

        assert "Document: Test Document" in result
        assert "Hello, World! This is a test document." in result
        assert "Content (0-" in result

    def test_read_document_with_tab_id(self, mock_client, mock_docs_service):
        """Test read_document with tab selection."""
        mock_client.docs_service = mock_docs_service

        result = read_document(document_id="doc_123", tab_id="tab_1")

        assert "Tab: tab_1" in result
        assert "Tab content here." in result

    def test_read_document_invalid_tab(self, mock_client, mock_docs_service):
        """Test read_document with invalid tab ID."""
        mock_client.docs_service = mock_docs_service

        result = read_document(document_id="doc_123", tab_id="invalid_tab")

        assert "Tab 'invalid_tab' not found" in result
        assert "Available tabs: ['tab_1']" in result

    def test_read_document_with_pagination(self, mock_client, mock_docs_service):
        """Test read_document with pagination parameters."""
        mock_client.docs_service = mock_docs_service

        result = read_document(document_id="doc_123", start_index=10, length=20)

        assert "Content (10-" in result

    def test_read_document_start_index_beyond_length(
        self, mock_client, mock_docs_service
    ):
        """Test read_document with start index beyond document length."""
        mock_client.docs_service = mock_docs_service

        result = read_document(
            document_id="doc_123",
            start_index=1000,  # Beyond document length
            length=100,
        )

        assert "Start index 1000 is beyond document length" in result

    def test_read_document_length_limit(self, mock_client, mock_docs_service):
        """Test read_document respects length limit."""
        mock_client.docs_service = mock_docs_service

        # Test that length is capped at 10000
        result = read_document(
            document_id="doc_123",
            length=15000,  # Above max of 10000
        )

        # Should not raise an error and should work normally
        assert "Document: Test Document" in result

    def test_read_document_api_error(self, mock_client, mock_docs_service):
        """Test read_document handles API errors."""
        mock_client.docs_service = mock_docs_service
        mock_docs_service.documents().get().execute.side_effect = Exception("API Error")

        result = read_document(document_id="doc_123")

        assert "Error reading document: API Error" in result


@patch("google_drive_mcp.server.client")
class TestWriteDocument:
    """Test write_document function."""

    def test_write_document_basic_insert(self, mock_client, mock_docs_service):
        """Test write_document with basic insertion."""
        mock_client.docs_service = mock_docs_service

        result = write_document(document_id="doc_123", content="Hello, World!")

        mock_docs_service.documents().get.assert_called_once_with(documentId="doc_123")
        mock_docs_service.documents().batchUpdate.assert_called_once()

        # Check the batchUpdate call
        call_args = mock_docs_service.documents().batchUpdate.call_args
        requests = call_args[1]["body"]["requests"]

        assert len(requests) == 1
        assert "insertText" in requests[0]
        assert requests[0]["insertText"]["text"] == "Hello, World!"

        assert "Successfully wrote to document 'Test Document'" in result
        assert "13 characters written" in result

    def test_write_document_with_insert_index(self, mock_client, mock_docs_service):
        """Test write_document with specific insert index."""
        mock_client.docs_service = mock_docs_service

        write_document(document_id="doc_123", content="Inserted text", insert_index=50)

        call_args = mock_docs_service.documents().batchUpdate.call_args
        requests = call_args[1]["body"]["requests"]

        assert requests[0]["insertText"]["location"]["index"] == 50

    def test_write_document_with_tab_id(self, mock_client, mock_docs_service):
        """Test write_document with tab selection."""
        mock_client.docs_service = mock_docs_service

        result = write_document(
            document_id="doc_123", content="Tab content", tab_id="tab_1"
        )

        assert "Successfully wrote to document" in result

    def test_write_document_invalid_tab(self, mock_client, mock_docs_service):
        """Test write_document with invalid tab ID."""
        mock_client.docs_service = mock_docs_service

        result = write_document(
            document_id="doc_123", content="Content", tab_id="invalid_tab"
        )

        assert "Tab 'invalid_tab' not found" in result

    def test_write_document_replace_range(self, mock_client, mock_docs_service):
        """Test write_document with content replacement."""
        mock_client.docs_service = mock_docs_service

        write_document(
            document_id="doc_123",
            content="Replacement text",
            replace_start=10,
            replace_end=20,
        )

        call_args = mock_docs_service.documents().batchUpdate.call_args
        requests = call_args[1]["body"]["requests"]

        assert len(requests) == 2
        assert "deleteContentRange" in requests[0]
        assert requests[0]["deleteContentRange"]["range"]["startIndex"] == 10
        assert requests[0]["deleteContentRange"]["range"]["endIndex"] == 20
        assert "insertText" in requests[1]
        assert requests[1]["insertText"]["location"]["index"] == 10

    def test_write_document_api_error(self, mock_client, mock_docs_service):
        """Test write_document handles API errors."""
        mock_client.docs_service = mock_docs_service
        mock_docs_service.documents().get().execute.side_effect = Exception("API Error")

        result = write_document(document_id="doc_123", content="Content")

        assert "Error writing to document: API Error" in result


class TestExtractTextFromContent:
    """Test _extract_text_from_content function."""

    def test_extract_simple_paragraphs(self, sample_document_content):
        """Test extracting text from simple paragraphs."""
        result = _extract_text_from_content(sample_document_content)

        expected = (
            "This is the first paragraph. "
            "This is the second paragraph with more content. "
            "Table cell content. "
        )
        assert result == expected

    def test_extract_empty_content(self):
        """Test extracting text from empty content."""
        content = {"content": []}
        result = _extract_text_from_content(content)
        assert result == ""

    def test_extract_with_section_break(self):
        """Test extracting text with section breaks."""
        content = {
            "content": [
                {"paragraph": {"elements": [{"textRun": {"content": "Before break"}}]}},
                {"sectionBreak": {}},
                {"paragraph": {"elements": [{"textRun": {"content": "After break"}}]}},
            ]
        }

        result = _extract_text_from_content(content)
        assert result == "Before break\nAfter break"

    def test_extract_missing_content(self):
        """Test extracting text when content key is missing."""
        content = {}
        result = _extract_text_from_content(content)
        assert result == ""
