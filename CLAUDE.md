# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project called "google-drive-mcp" (version 0.1.0) that implements a Model Context Protocol (MCP) server for Google Drive integration, with a focus on Google Docs operations. The server is built using FastMCP and provides tools for reading, writing, searching, and listing Google Drive files.

## Development Commands

This project uses uv for Python package management. Standard development commands:

- **Install dependencies**: `uv sync`
- **Install test dependencies**: `uv sync --all-extras`
- **Install in development mode**: `uv pip install -e .`
- **Run the server**: `python -m google_drive_mcp.server`
- **Run tests**: `uv run pytest`
- **Run tests with coverage**: `uv run pytest --cov=google_drive_mcp --cov-report=html`
- **Type checking**: `uv run mypy .` (once mypy is configured)
- **Linting**: `uv run ruff check .` (once ruff is added)

## Architecture

The project implements a FastMCP server with the following components:

### Core Modules
- `google_drive_mcp/auth.py` - Google Drive API authentication and client setup
- `google_drive_mcp/server.py` - FastMCP server implementation with tool definitions

### MCP Tools
- **list_files** - List files in Google Drive with pagination and filtering
- **search_files** - Search for files using Google Drive query syntax
- **read_document** - Read Google Docs content with pagination and tab selection
- **write_document** - Write to Google Docs with tab selection and range operations

### Key Features
- OAuth2 authentication flow for Google Drive API
- Pagination support for large result sets (default 50 items, max 100)
- Document tab selection for multi-tab Google Docs
- Content replacement and insertion operations
- Comprehensive error handling and validation

## Setup Requirements

1. **Google API Credentials**: Obtain `credentials.json` from Google Cloud Console
2. **API Scopes**: Requires Google Drive and Google Docs API access
3. **Authentication**: First run will trigger OAuth flow and create `token.json`

## Testing

The project includes comprehensive pytest test suite with:

- **Unit tests** for authentication (`test_auth.py`)
- **Function tests** for all MCP tools (`test_server.py`) 
- **Integration tests** for MCP server functionality (`test_integration.py`)
- **Mocked Google APIs** to avoid requiring real credentials during testing
- **Coverage reporting** with pytest-cov
- **GitHub Actions** workflow for automated testing on Python 3.11 and 3.12

### Running Tests Locally

```bash
# Install test dependencies
uv sync --all-extras

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=google_drive_mcp --cov-report=html

# Run specific test file
uv run pytest tests/test_server.py -v
```

## Usage Patterns

The server is designed to be used as an MCP server that provides Google Drive operations to MCP clients. All tools return formatted text responses with proper pagination tokens and error messages.