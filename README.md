# Google Drive MCP Server

A Model Context Protocol (MCP) server for Google Drive integration, built with FastMCP. Provides tools for reading, writing, searching, and listing Google Drive files with a focus on Google Docs operations.

## Features

- **File Operations**: List and search files in Google Drive with pagination
- **Document Reading**: Read Google Docs content with pagination and tab selection
- **Document Writing**: Write to Google Docs with tab selection and range operations
- **Authentication**: Service account authentication for Google Drive API access
- **Pagination**: Handle large documents and file lists efficiently

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Google API Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API and Google Docs API
4. Create a service account and generate a key
5. Download the service account key file and save it as `service-account-key.json` in the project root
6. Share any Google Drive files/folders you want to access with the service account email

### 3. Running the Server

```bash
python -m google_drive_mcp.server
```

No authentication flow is required - the service account will authenticate automatically using the key file.

## Available Tools

### `list_files`
List files in Google Drive with optional filtering and pagination.

**Parameters:**
- `folder_id` (optional): Folder ID to list files from (default: root)
- `page_size` (optional): Number of files per page (default: 50, max: 100)
- `page_token` (optional): Token for pagination
- `mime_type` (optional): Filter by MIME type (e.g., 'application/vnd.google-apps.document')

### `search_files`
Search for files in Google Drive using query syntax.

**Parameters:**
- `query`: Search query (e.g., 'name contains "report"')
- `page_size` (optional): Number of files per page (default: 50, max: 100)
- `page_token` (optional): Token for pagination

### `read_document`
Read content from a Google Docs document with pagination.

**Parameters:**
- `document_id`: Google Docs document ID
- `tab_id` (optional): Specific tab ID to read from
- `start_index` (optional): Starting character index (default: 0)
- `length` (optional): Number of characters to read (default: 5000, max: 10000)

### `write_document`
Write content to a Google Docs document.

**Parameters:**
- `document_id`: Google Docs document ID
- `content`: Content to write
- `tab_id` (optional): Specific tab ID to write to
- `insert_index` (optional): Index where to insert content (default: end)
- `replace_start` (optional): Start index for content replacement
- `replace_end` (optional): End index for content replacement

## Usage Examples

### Search for Google Docs
```python
# Search for documents containing "report"
search_files(query='name contains "report" and mimeType="application/vnd.google-apps.document"')
```

### Read a Document with Pagination
```python
# Read first 5000 characters
read_document(document_id="your_doc_id")

# Read next 5000 characters
read_document(document_id="your_doc_id", start_index=5000)
```

### Write to a Specific Tab
```python
# Write to a specific tab in a document
write_document(
    document_id="your_doc_id",
    content="Hello, World!",
    tab_id="your_tab_id"
)
```

## Development

### Project Structure
```
google_drive_mcp/
├── __init__.py
├── auth.py          # Google Drive authentication
└── server.py        # FastMCP server implementation
```

### Running in Development
```bash
# Install in development mode
uv pip install -e .

# Run the server
python -m google_drive_mcp.server
```

## License

This project is licensed under the MIT License.
