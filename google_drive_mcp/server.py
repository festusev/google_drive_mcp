"""Google Drive MCP Server implementation using FastMCP."""

import logging
from typing import Any

from fastmcp import FastMCP

from .auth import GoogleDriveClient

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

mcp: FastMCP = FastMCP("Google Drive MCP")
client = GoogleDriveClient()


@mcp.tool()
def list_files(
    folder_id: str | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    page_token: str | None = None,
    mime_type: str | None = None,
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

    result = (
        client.drive_service.files()
        .list(
            q=query,
            pageSize=page_size,
            pageToken=page_token,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)",
        )
        .execute()
    )

    files = result.get("files", [])
    next_page_token = result.get("nextPageToken")

    output = []
    output.append(f"Found {len(files)} files")
    if next_page_token:
        output.append(f"Next page token: {next_page_token}")
    output.append("")

    for file in files:
        size_str = f" ({file.get('size', 'N/A')} bytes)" if "size" in file else ""
        output.append(f"- {file['name']} (ID: {file['id']})")
        output.append(f"  Type: {file.get('mimeType', 'Unknown')}{size_str}")
        output.append(f"  Modified: {file.get('modifiedTime', 'Unknown')}")
        output.append("")

    return "\n".join(output)


@mcp.tool()
def search_files(
    query: str, page_size: int = DEFAULT_PAGE_SIZE, page_token: str | None = None
) -> str:
    """Search for files in Google Drive with pagination.

    Args:
        query: Search query (e.g., 'name contains "report"')
        page_size: Number of files per page (default: 50, max: 100)
        page_token: Token for pagination (from previous response)
    """
    page_size = min(page_size, MAX_PAGE_SIZE)

    full_query = f"({query}) and trashed=false"

    result = (
        client.drive_service.files()
        .list(
            q=full_query,
            pageSize=page_size,
            pageToken=page_token,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)",
        )
        .execute()
    )

    files = result.get("files", [])
    next_page_token = result.get("nextPageToken")

    output = []
    output.append(f"Search results for: {query}")
    output.append(f"Found {len(files)} files")
    if next_page_token:
        output.append(f"Next page token: {next_page_token}")
    output.append("")

    for file in files:
        size_str = f" ({file.get('size', 'N/A')} bytes)" if "size" in file else ""
        output.append(f"- {file['name']} (ID: {file['id']})")
        output.append(f"  Type: {file.get('mimeType', 'Unknown')}{size_str}")
        output.append(f"  Modified: {file.get('modifiedTime', 'Unknown')}")
        output.append("")

    return "\n".join(output)


@mcp.tool()
def read_document(
    document_id: str,
    tab_id: str | None = None,
    start_index: int = 0,
    length: int = 5000,
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
            tabs = doc.get("tabs", [])
            selected_tab = None
            for tab in tabs:
                if tab.get("tabId") == tab_id:
                    selected_tab = tab
                    break

            if not selected_tab:
                available_tabs = [tab.get("tabId", "main") for tab in tabs]
                return f"Tab '{tab_id}' not found. Available tabs: {available_tabs}"

            content = selected_tab.get("documentTab", {}).get("body", {})
        else:
            content = doc.get("body", {})

        text_content = _extract_text_from_content(content)

        if start_index >= len(text_content):
            return f"Start index {start_index} is beyond document length ({len(text_content)} characters)"

        end_index = min(start_index + length, len(text_content))
        page_content = text_content[start_index:end_index]

        output = []
        output.append(f"Document: {doc.get('title', 'Untitled')}")
        if tab_id:
            output.append(f"Tab: {tab_id}")
        output.append(
            f"Content ({start_index}-{end_index} of {len(text_content)} characters):"
        )
        output.append("=" * 50)
        output.append(page_content)

        if end_index < len(text_content):
            output.append("=" * 50)
            output.append(
                f"More content available. Use start_index={end_index} to continue."
            )

        return "\n".join(output)

    except Exception as e:
        return f"Error reading document: {str(e)}"


@mcp.tool()
def write_document(
    document_id: str,
    content: str,
    tab_id: str | None = None,
    insert_index: int | None = None,
    replace_start: int | None = None,
    replace_end: int | None = None,
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

        # Get the content to calculate smart chip adjustments
        if tab_id:
            tabs = doc.get("tabs", [])
            selected_tab = None
            for tab in tabs:
                if tab.get("tabId") == tab_id:
                    selected_tab = tab
                    break
            if not selected_tab:
                return f"Tab '{tab_id}' not found"
            content_body = selected_tab.get("documentTab", {}).get("body", {})
        else:
            content_body = doc.get("body", {})

        # Extract text to calculate index adjustments
        extracted_text = _extract_text_from_content(content_body)

        # Adjust indices for smart chips
        if insert_index is not None:
            insert_index = _adjust_index_for_smart_chips(extracted_text, insert_index)
        if replace_start is not None:
            replace_start = _adjust_index_for_smart_chips(extracted_text, replace_start)
        if replace_end is not None:
            replace_end = _adjust_index_for_smart_chips(extracted_text, replace_end)

        requests: list[dict[str, Any]] = []

        if replace_start is not None and replace_end is not None:
            requests.append(
                {
                    "deleteContentRange": {
                        "range": {"startIndex": replace_start, "endIndex": replace_end}
                    }
                }
            )

            requests.append(
                {"insertText": {"location": {"index": replace_start}, "text": content}}
            )

            operation = f"Replaced content from index {replace_start} to {replace_end}"

        else:
            if insert_index is None:
                if tab_id:
                    tabs = doc.get("tabs", [])
                    for tab in tabs:
                        if tab.get("tabId") == tab_id:
                            tab_content = tab.get("documentTab", {}).get("body", {})
                            insert_index = tab_content.get("content", [{}])[-1].get(
                                "endIndex", 1
                            )
                            break
                    else:
                        return f"Tab '{tab_id}' not found"
                else:
                    body = doc.get("body", {})
                    insert_index = body.get("content", [{}])[-1].get("endIndex", 1)

            requests.append(
                {"insertText": {"location": {"index": insert_index}, "text": content}}
            )

            operation = f"Inserted content at index {insert_index}"

        client.docs_service.documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()

        return f"Successfully wrote to document '{doc.get('title', 'Untitled')}'. {operation}. {len(content)} characters written."

    except Exception as e:
        return f"Error writing to document: {str(e)}"


def _adjust_index_for_smart_chips(text: str, index: int) -> int:
    """Adjust index to account for smart chip placeholder expansion.

    Smart chips appear as single Unicode characters in the document but are
    replaced with '@[smart-chip]' (13 chars) in our extracted text. This function
    converts from the extracted text index to the actual document index.
    """
    # Count smart chips before the given index
    smart_chip_placeholder = "@[smart-chip]"
    placeholder_len = len(smart_chip_placeholder)

    # Track the actual document position
    doc_pos = 0
    text_pos = 0

    while text_pos < index and text_pos < len(text):
        if text[text_pos : text_pos + placeholder_len] == smart_chip_placeholder:
            # This is a smart chip - it's only 1 character in the document
            doc_pos += 1
            text_pos += placeholder_len
        else:
            # Regular character
            doc_pos += 1
            text_pos += 1

    return doc_pos


def _extract_text_from_content(content: dict[str, Any]) -> str:
    """Extract text from Google Docs content structure with formatting preserved.

    Note: Smart chips (like @today, @date) appear as Unicode characters (\ue907 or \ufffc)
    in the API response and are replaced with @[smart-chip] placeholders.
    For full smart chip values, use Google Drive's files.export API with text/plain.
    """
    text_parts = []
    list_counters: dict[str, dict[int, int]] = {}  # Track counters for numbered lists

    def extract_from_elements(
        elements: list[dict[str, Any]], indent_level: int = 0
    ) -> None:
        for element in elements:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                bullet = paragraph.get("bullet")

                # Handle bullet points and lists
                prefix = ""
                if bullet:
                    list_id = bullet.get("listId", "")
                    nesting_level = bullet.get("nestingLevel", 0)

                    # Add indentation based on nesting level
                    indent = "  " * nesting_level

                    # Check if this is an ordered (numbered) list
                    # The bullet object doesn't directly indicate ordered vs unordered,
                    # but we can check the list properties from the document
                    is_ordered = False

                    # For now, check if the text starts with a number pattern
                    # In a full implementation, you'd check the list properties
                    if list_id:
                        if list_id not in list_counters:
                            list_counters[list_id] = {}
                        if nesting_level not in list_counters[list_id]:
                            list_counters[list_id][nesting_level] = 0

                        # Increment counter for this level
                        list_counters[list_id][nesting_level] += 1

                        # Reset deeper level counters
                        for level in list(list_counters[list_id].keys()):
                            if level > nesting_level:
                                list_counters[list_id][level] = 0

                        # Try to detect if it's ordered by checking glyph properties
                        # This is a simplified approach - in reality you'd check list properties
                        if any(
                            elem.get("textRun", {})
                            .get("content", "")
                            .strip()
                            .split(".")[0]
                            .isdigit()
                            for elem in paragraph.get("elements", [])
                        ):
                            is_ordered = True

                    if is_ordered and list_id in list_counters:
                        # Numbered list
                        number = list_counters[list_id][nesting_level]
                        prefix = f"{indent}{number}. "
                    else:
                        # Bullet list
                        bullet_chars = ["•", "◦", "▪", "▫", "‣", "⁃", "⁌", "⁍", "→"]
                        char_index = min(nesting_level, len(bullet_chars) - 1)
                        prefix = f"{indent}{bullet_chars[char_index]} "

                # Extract paragraph text
                paragraph_text = []
                for elem in paragraph.get("elements", []):
                    if "textRun" in elem:
                        text = elem["textRun"].get("content", "")
                        # Handle special formatting
                        text_style = elem["textRun"].get("textStyle", {})

                        # Handle @mentions or links
                        if text_style.get("link"):
                            url = text_style["link"].get("url", "")
                            if url.startswith("https://"):
                                text = f"[{text}]({url})"

                        # Handle smart chips (they appear as Unicode character \ue907)
                        # Replace with a readable placeholder
                        text = text.replace("\ue907", "@[smart-chip]")
                        # Also handle the object replacement character (U+FFFC)
                        text = text.replace("\ufffc", "@[smart-chip]")

                        paragraph_text.append(text)
                    elif "person" in elem:
                        # Handle @mentions
                        person = elem["person"]
                        person_id = person.get("personId", "")
                        # Google Docs uses special person elements for @mentions
                        paragraph_text.append(f"@{person_id}")
                    elif "richLink" in elem:
                        # Handle rich links
                        rich_link = elem["richLink"]
                        url = rich_link.get("richLinkProperties", {}).get("uri", "")
                        title = rich_link.get("richLinkProperties", {}).get(
                            "title", url
                        )
                        paragraph_text.append(f"[{title}]({url})")
                    elif "inlineObjectElement" in elem:
                        # Handle inline objects (images, drawings, etc.)
                        inline_obj = elem["inlineObjectElement"]
                        obj_id = inline_obj.get("inlineObjectId", "")
                        paragraph_text.append(f"[INLINE_OBJECT:{obj_id}]")
                    elif "equation" in elem:
                        # Handle equations
                        paragraph_text.append("[EQUATION]")
                    elif "footnoteReference" in elem:
                        # Handle footnotes
                        footnote = elem["footnoteReference"]
                        footnote_id = footnote.get("footnoteId", "")
                        paragraph_text.append(f"[^{footnote_id}]")

                # Combine prefix and text
                full_text = prefix + "".join(paragraph_text)
                text_parts.append(full_text)

            elif "table" in element:
                table = element["table"]
                text_parts.append("\n[TABLE]\n")
                for _i, row in enumerate(table.get("tableRows", [])):
                    row_texts = []
                    for cell in row.get("tableCells", []):
                        # Extract cell content separately
                        cell_content_parts = []
                        for cell_element in cell.get("content", []):
                            if "paragraph" in cell_element:
                                cell_paragraph = cell_element["paragraph"]
                                for elem in cell_paragraph.get("elements", []):
                                    if "textRun" in elem:
                                        cell_content_parts.append(
                                            elem["textRun"].get("content", "")
                                        )
                        cell_text = "".join(cell_content_parts).strip()
                        row_texts.append(cell_text)
                    text_parts.append(" | ".join(row_texts) + "\n")
                text_parts.append("[/TABLE]\n")

            elif "tableOfContents" in element:
                toc = element["tableOfContents"]
                text_parts.append("\n[TABLE OF CONTENTS]\n")
                extract_from_elements(toc.get("content", []), indent_level)
                text_parts.append("[/TABLE OF CONTENTS]\n")

            elif "sectionBreak" in element:
                text_parts.append("\n---\n")

            elif "pageBreak" in element:
                text_parts.append("\n[PAGE BREAK]\n")

            elif "horizontalRule" in element:
                text_parts.append("\n___\n")

    extract_from_elements(content.get("content", []))
    return "".join(text_parts)


def main() -> None:
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
