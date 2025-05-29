"""Test configuration and fixtures."""

import pytest
from unittest.mock import Mock, MagicMock
from google_drive_mcp.auth import GoogleDriveClient


@pytest.fixture
def mock_credentials():
    """Mock Google credentials."""
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_creds.refresh_token = "mock_refresh_token"
    mock_creds.to_json.return_value = '{"mock": "credentials"}'
    return mock_creds


@pytest.fixture
def mock_drive_service():
    """Mock Google Drive service."""
    service = Mock()
    
    # Mock files().list() chain
    files_mock = Mock()
    list_mock = Mock()
    execute_mock = Mock()
    
    execute_mock.return_value = {
        'files': [
            {
                'id': 'file_1',
                'name': 'Test Document 1',
                'mimeType': 'application/vnd.google-apps.document',
                'modifiedTime': '2023-01-01T00:00:00.000Z',
                'size': '1024'
            },
            {
                'id': 'file_2', 
                'name': 'Test Document 2',
                'mimeType': 'application/vnd.google-apps.document',
                'modifiedTime': '2023-01-02T00:00:00.000Z'
            }
        ],
        'nextPageToken': 'next_page_token'
    }
    
    list_mock.execute = execute_mock
    files_mock.list.return_value = list_mock
    service.files.return_value = files_mock
    
    return service


@pytest.fixture
def mock_docs_service():
    """Mock Google Docs service."""
    service = Mock()
    
    # Mock documents().get() chain
    docs_mock = Mock()
    get_mock = Mock()
    execute_mock = Mock()
    
    execute_mock.return_value = {
        'title': 'Test Document',
        'body': {
            'content': [
                {
                    'paragraph': {
                        'elements': [
                            {
                                'textRun': {
                                    'content': 'Hello, World! This is a test document.'
                                }
                            }
                        ]
                    }
                },
                {
                    'endIndex': 100
                }
            ]
        },
        'tabs': [
            {
                'tabId': 'tab_1',
                'documentTab': {
                    'body': {
                        'content': [
                            {
                                'paragraph': {
                                    'elements': [
                                        {
                                            'textRun': {
                                                'content': 'Tab content here.'
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        ]
    }
    
    get_mock.execute = execute_mock
    docs_mock.get.return_value = get_mock
    
    # Mock documents().batchUpdate() chain
    batch_update_mock = Mock()
    batch_execute_mock = Mock()
    batch_execute_mock.return_value = {'replies': []}
    batch_update_mock.execute = batch_execute_mock
    docs_mock.batchUpdate.return_value = batch_update_mock
    
    service.documents.return_value = docs_mock
    
    return service


@pytest.fixture
def mock_google_client(mock_credentials, mock_drive_service, mock_docs_service):
    """Mock GoogleDriveClient with services."""
    client = GoogleDriveClient()
    client._creds = mock_credentials
    client._drive_service = mock_drive_service
    client._docs_service = mock_docs_service
    return client


@pytest.fixture
def sample_document_content():
    """Sample document content for testing."""
    return {
        'content': [
            {
                'paragraph': {
                    'elements': [
                        {
                            'textRun': {
                                'content': 'This is the first paragraph. '
                            }
                        }
                    ]
                }
            },
            {
                'paragraph': {
                    'elements': [
                        {
                            'textRun': {
                                'content': 'This is the second paragraph with more content. '
                            }
                        }
                    ]
                }
            },
            {
                'table': {
                    'tableRows': [
                        {
                            'tableCells': [
                                {
                                    'content': [
                                        {
                                            'paragraph': {
                                                'elements': [
                                                    {
                                                        'textRun': {
                                                            'content': 'Table cell content. '
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }