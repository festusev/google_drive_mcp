"""Google Drive MCP Server implementation using FastMCP."""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .auth import GoogleDriveClient

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

mcp = FastMCP("Google Drive MCP")
client = GoogleDriveClient()


@mcp.tool()
def list_files(
    folder_id: Optional[str] = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    page_token: Optional[str] = None,
    mime_type: Optional[str] = None
) -> str:
    """List files in Google Drive with optional folder filtering and pagination.
    
    Args:
        folder_id: Optional folder ID to list files from (default: root)
        page_size: Number of files per page (default: 50, max: 100)
        page_token: Token for pagination (from previous response)
        mime_type: Filter by MIME type (e.g., 'application/vnd.google-apps.document')
    """
    page_size = min(page_size, MAX_PAGE_SIZE)
    
    query_parts = []
    if folder_id:
        query_parts.append(f"'{folder_id}' in parents")
    else:
        query_parts.append("'root' in parents")
    
    if mime_type:
        query_parts.append(f"mimeType='{mime_type}'")
    
    query_parts.append("trashed=false")
    query = " and ".join(query_parts)
    
    result = client.drive_service.files().list(
        q=query,
        pageSize=page_size,
        pageToken=page_token,
        fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)"
    ).execute()
    
    files = result.get('files', [])
    next_page_token = result.get('nextPageToken')
    
    output = []
    output.append(f"Found {len(files)} files")
    if next_page_token:
        output.append(f"Next page token: {next_page_token}")
    output.append("")
    
    for file in files:
        size_str = f" ({file.get('size', 'N/A')} bytes)" if 'size' in file else ""
        output.append(f"- {file['name']} (ID: {file['id']})")
        output.append(f"  Type: {file.get('mimeType', 'Unknown')}{size_str}")
        output.append(f"  Modified: {file.get('modifiedTime', 'Unknown')}")
        output.append("")
    
    return "\n".join(output)


@mcp.tool()
def search_files(
    query: str,
    page_size: int = DEFAULT_PAGE_SIZE,
    page_token: Optional[str] = None
) -> str:
    """Search for files in Google Drive with pagination.
    
    Args:
        query: Search query (e.g., 'name contains "report"')
        page_size: Number of files per page (default: 50, max: 100)
        page_token: Token for pagination (from previous response)
    """
    page_size = min(page_size, MAX_PAGE_SIZE)
    
    full_query = f"({query}) and trashed=false"
    
    result = client.drive_service.files().list(
        q=full_query,
        pageSize=page_size,
        pageToken=page_token,
        fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)"
    ).execute()
    
    files = result.get('files', [])
    next_page_token = result.get('nextPageToken')
    
    output = []
    output.append(f"Search results for: {query}")
    output.append(f"Found {len(files)} files")
    if next_page_token:
        output.append(f"Next page token: {next_page_token}")
    output.append("")
    
    for file in files:
        size_str = f" ({file.get('size', 'N/A')} bytes)" if 'size' in file else ""
        output.append(f"- {file['name']} (ID: {file['id']})")
        output.append(f"  Type: {file.get('mimeType', 'Unknown')}{size_str}")
        output.append(f"  Modified: {file.get('modifiedTime', 'Unknown')}")
        output.append("")
    
    return "\n".join(output)


@mcp.tool()
def read_document(
    document_id: str,
    tab_id: Optional[str] = None,
    start_index: int = 0,
    length: int = 5000
) -> str:
    """Read content from a Google Docs document with pagination and tab selection.
    
    Args:
        document_id: Google Docs document ID
        tab_id: Specific tab ID to read from (optional, defaults to main document)
        start_index: Starting character index for pagination
        length: Number of characters to read (default: 5000, max: 10000)
    """
    length = min(length, 10000)
    
    try:
        doc = client.docs_service.documents().get(documentId=document_id).execute()
        
        if tab_id:
            tabs = doc.get('tabs', [])
            selected_tab = None
            for tab in tabs:
                if tab.get('tabId') == tab_id:
                    selected_tab = tab
                    break
            
            if not selected_tab:
                available_tabs = [tab.get('tabId', 'main') for tab in tabs]
                return f"Tab '{tab_id}' not found. Available tabs: {available_tabs}"
            
            content = selected_tab.get('documentTab', {}).get('body', {})
        else:
            content = doc.get('body', {})
        
        text_content = _extract_text_from_content(content)
        
        if start_index >= len(text_content):
            return f"Start index {start_index} is beyond document length ({len(text_content)} characters)"
        
        end_index = min(start_index + length, len(text_content))
        page_content = text_content[start_index:end_index]
        
        output = []
        output.append(f"Document: {doc.get('title', 'Untitled')}")
        if tab_id:
            output.append(f"Tab: {tab_id}")
        output.append(f"Content ({start_index}-{end_index} of {len(text_content)} characters):")
        output.append("=" * 50)
        output.append(page_content)
        
        if end_index < len(text_content):
            output.append("=" * 50)
            output.append(f"More content available. Use start_index={end_index} to continue.")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Error reading document: {str(e)}"


@mcp.tool()
def write_document(
    document_id: str,
    content: str,
    tab_id: Optional[str] = None,
    insert_index: Optional[int] = None,
    replace_start: Optional[int] = None,
    replace_end: Optional[int] = None
) -> str:
    """Write content to a Google Docs document with tab selection.
    
    Args:
        document_id: Google Docs document ID
        content: Content to write
        tab_id: Specific tab ID to write to (optional, defaults to main document)
        insert_index: Index where to insert content (default: end of document)
        replace_start: Start index for content replacement (requires replace_end)
        replace_end: End index for content replacement (requires replace_start)
    """
    try:
        doc = client.docs_service.documents().get(documentId=document_id).execute()
        
        requests = []
        
        if replace_start is not None and replace_end is not None:
            requests.append({
                'deleteContentRange': {
                    'range': {
                        'startIndex': replace_start,
                        'endIndex': replace_end
                    }
                }
            })
            
            requests.append({
                'insertText': {
                    'location': {'index': replace_start},
                    'text': content
                }
            })
            
            operation = f"Replaced content from index {replace_start} to {replace_end}"
            
        else:
            if insert_index is None:
                if tab_id:
                    tabs = doc.get('tabs', [])
                    for tab in tabs:
                        if tab.get('tabId') == tab_id:
                            tab_content = tab.get('documentTab', {}).get('body', {})
                            insert_index = tab_content.get('content', [{}])[-1].get('endIndex', 1)
                            break
                    else:
                        return f"Tab '{tab_id}' not found"
                else:
                    body = doc.get('body', {})
                    insert_index = body.get('content', [{}])[-1].get('endIndex', 1)
            
            requests.append({
                'insertText': {
                    'location': {'index': insert_index},
                    'text': content
                }
            })
            
            operation = f"Inserted content at index {insert_index}"
        
        result = client.docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return f"Successfully wrote to document '{doc.get('title', 'Untitled')}'. {operation}. {len(content)} characters written."
        
    except Exception as e:
        return f"Error writing to document: {str(e)}"


def _extract_text_from_content(content: Dict[str, Any]) -> str:
    """Extract plain text from Google Docs content structure."""
    text_parts = []
    
    def extract_from_elements(elements):
        for element in elements:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for elem in paragraph.get('elements', []):
                    if 'textRun' in elem:
                        text_parts.append(elem['textRun'].get('content', ''))
            elif 'table' in element:
                table = element['table']
                for row in table.get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        extract_from_elements(cell.get('content', []))
            elif 'sectionBreak' in element:
                text_parts.append('\n')
    
    extract_from_elements(content.get('content', []))
    return ''.join(text_parts)


def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        client.authenticate()
        mcp.run()
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()