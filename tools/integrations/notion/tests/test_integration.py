"""
Tests for Notion integration.
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from integration.notion import NotionManager
from integration.notion.types import (
    Block,
    BlockType,
    Page,
    Database,
    ParentType,
    SearchResult,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_token():
    """Mock Notion token for testing."""
    return "test_token_secret_123"


@pytest.fixture
def mock_config(mock_token):
    """Mock configuration."""
    return {
        "token": mock_token,
        "base_url": "https://api.notion.com",
        "timeout": 30,
    }


@pytest.fixture
def mock_page_response():
    """Mock page API response."""
    return {
        "object": "page",
        "id": "page_12345",
        "created_time": "2025-01-19T00:00:00.000Z",
        "last_edited_time": "2025-01-19T00:00:00.000Z",
        "archived": False,
        "url": "https://notion.so/page_12345",
        "properties": {
            "title": {
                "type": "title",
                "title": [
                    {
                        "type": "text",
                        "text": {"content": "Test Page"},
                        "plain_text": "Test Page",
                    }
                ],
            }
        },
        "parent": {"type": "page_id", "page_id": "page_parent"},
    }


@pytest.fixture
def mock_database_response():
    """Mock database API response."""
    return {
        "object": "database",
        "id": "database_12345",
        "created_time": "2025-01-19T00:00:00.000Z",
        "last_edited_time": "2025-01-19T00:00:00.000Z",
        "title": [
            {"type": "text", "text": {"content": "Test Database"}, "plain_text": "Test Database"}
        ],
        "url": "https://notion.so/database_12345",
        "properties": {
            "Name": {"type": "title", "title": {}},
            "Status": {
                "type": "select",
                "select": {
                    "options": [{"name": "Todo", "color": "gray"}],
                },
            },
        },
        "parent": {"type": "page_id", "page_id": "page_parent"},
    }


@pytest.fixture
def mock_search_response():
    """Mock search API response."""
    return {
        "object": "list",
        "results": [
            {
                "object": "page",
                "id": "page_123",
                "url": "https://notion.so/page_123",
                "properties": {
                    "title": {
                        "type": "title",
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": "Search Result"},
                            }
                        ],
                    }
                },
                "parent": {"type": "page_id", "page_id": "page_parent"},
            }
        ],
        "next_cursor": None,
        "has_more": False,
    }


# =============================================================================
# Test Cases
# =============================================================================


class TestNotionManager:
    """Test NotionManager class."""

    def test_init_with_token(self, mock_token):
        """Test initialization with token parameter."""
        with patch.dict(os.environ, {}, clear=True):
            manager = NotionManager(token=mock_token)
            assert manager.token == mock_token
            assert manager.base_url == "https://api.notion.com"

    def test_init_from_env(self, mock_token):
        """Test initialization from environment variable."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            manager = NotionManager()
            assert manager.token == mock_token

    def test_init_missing_token(self):
        """Test initialization fails without token."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API token required"):
                NotionManager()

    @pytest.mark.asyncio
    async def test_check_connection_success(self, mock_token):
        """Test successful connection check."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            manager = NotionManager()

            # Mock successful response
            manager.client.post = AsyncMock(
                return_value=MagicMock(
                    json=lambda: {"results": []},
                    raise_for_status=lambda: None,
                )
            )

            result = await manager.check_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_check_connection_failure(self, mock_token):
        """Test failed connection check."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            manager = NotionManager()

            # Mock failed response
            manager.client.post = AsyncMock(side_effect=httpx.RequestError("Connection error"))

            result = await manager.check_connection()
            assert result is False

    @pytest.mark.asyncio
    async def test_create_page(self, mock_token, mock_page_response):
        """Test creating a page."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            manager = NotionManager()

            manager.client.post = AsyncMock(
                return_value=MagicMock(
                    json=lambda: mock_page_response,
                    raise_for_status=lambda: None,
                )
            )

            properties = {
                "title": {
                    "title": [
                        {"type": "text", "text": {"content": "Test Page"}}
                    ]
                }
            }

            page = await manager.create_page(
                parent_id="page_parent",
                properties=properties,
            )

            assert page.id == "page_12345"
            assert page.title == "Test Page"
            assert page.url == "https://notion.so/page_12345"

    @pytest.mark.asyncio
    async def test_get_page(self, mock_token, mock_page_response):
        """Test getting a page."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            manager = NotionManager()

            manager.client.get = AsyncMock(
                return_value=MagicMock(
                    json=lambda: mock_page_response,
                    raise_for_status=lambda: None,
                )
            )

            page = await manager.get_page("page_12345")

            assert page is not None
            assert page.id == "page_12345"
            assert page.title == "Test Page"

    @pytest.mark.asyncio
    async def test_get_page_not_found(self, mock_token):
        """Test getting a non-existent page."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            manager = NotionManager()

            manager.client.get = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Not found",
                    request=MagicMock(),
                    response=MagicMock(status_code=404),
                )
            )

            page = await manager.get_page("page_invalid")
            assert page is None

    @pytest.mark.asyncio
    async def test_update_page(self, mock_token, mock_page_response):
        """Test updating a page."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            manager = NotionManager()

            manager.client.patch = AsyncMock(
                return_value=MagicMock(
                    json=lambda: mock_page_response,
                    raise_for_status=lambda: None,
                )
            )

            properties = {
                "title": {
                    "title": [
                        {"type": "text", "text": {"content": "Updated Title"}}
                    ]
                }
            }

            page = await manager.update_page("page_12345", properties)

            assert page is not None
            assert page.id == "page_12345"

    @pytest.mark.asyncio
    async def test_delete_page(self, mock_token):
        """Test deleting (archiving) a page."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            manager = NotionManager()

            manager.client.patch = AsyncMock(
                return_value=MagicMock(
                    json=lambda: {"object": "page", "id": "page_12345"},
                    raise_for_status=lambda: None,
                )
            )

            result = await manager.delete_page("page_12345")
            assert result is True

    @pytest.mark.asyncio
    async def test_search(self, mock_token, mock_search_response):
        """Test searching workspace."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            manager = NotionManager()

            manager.client.post = AsyncMock(
                return_value=MagicMock(
                    json=lambda: mock_search_response,
                    raise_for_status=lambda: None,
                )
            )

            results = await manager.search(query="test")

            assert "results" in results
            assert len(results["results"]) == 1

    @pytest.mark.asyncio
    async def test_search_pages(self, mock_token, mock_search_response):
        """Test searching pages only."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            manager = NotionManager()

            manager.client.post = AsyncMock(
                return_value=MagicMock(
                    json=lambda: mock_search_response,
                    raise_for_status=lambda: None,
                )
            )

            pages = await manager.search_pages(query="test")

            assert len(pages) == 1
            assert pages[0].object_type == "page"
            assert pages[0].title == "Search Result"

    @pytest.mark.asyncio
    async def test_create_database(self, mock_token, mock_database_response):
        """Test creating a database."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            manager = NotionManager()

            manager.client.post = AsyncMock(
                return_value=MagicMock(
                    json=lambda: mock_database_response,
                    raise_for_status=lambda: None,
                )
            )

            properties = {
                "Name": {"title": {}},
                "Status": {
                    "select": {
                        "options": [{"name": "Todo", "color": "gray"}]
                    }
                },
            }

            database = await manager.create_database(
                parent_id="page_parent",
                title="Test Database",
                properties=properties,
            )

            assert database.id == "database_12345"
            assert database.title == "Test Database"

    @pytest.mark.asyncio
    async def test_query_database(self, mock_token):
        """Test querying a database."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            manager = NotionManager()

            manager.client.post = AsyncMock(
                return_value=MagicMock(
                    json=lambda: {
                        "object": "list",
                        "results": [
                            {
                                "object": "page",
                                "id": "page_1",
                                "url": "https://notion.so/page_1",
                                "properties": {
                                    "Name": {
                                        "type": "title",
                                        "title": [
                                            {
                                                "type": "text",
                                                "text": {"content": "Item 1"},
                                            }
                                        ],
                                    }
                                },
                            }
                        ],
                        "next_cursor": None,
                        "has_more": False,
                    },
                    raise_for_status=lambda: None,
                )
            )

            results = await manager.query_database("database_12345", page_size=10)

            assert "results" in results
            assert len(results["results"]) == 1

    @pytest.mark.asyncio
    async def test_append_blocks(self, mock_token):
        """Test appending blocks to a page."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            manager = NotionManager()

            manager.client.patch = AsyncMock(
                return_value=MagicMock(
                    json=lambda: {
                        "object": "list",
                        "results": [
                            {
                                "object": "block",
                                "id": "block_1",
                                "type": "paragraph",
                            }
                        ],
                    },
                    raise_for_status=lambda: None,
                )
            )

            blocks = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "Test"}}
                        ]
                    },
                }
            ]

            results = await manager.append_blocks("page_12345", blocks)

            assert len(results) == 1


class TestMarkdownConversion:
    """Test markdown to blocks conversion."""

    def test_paragraph(self, mock_token):
        """Test converting markdown paragraph."""
        with patch.dict(os.environ, {"NOTION_TOKEN": "test_token"}):
            manager = NotionManager()

            markdown = "This is a paragraph"
            blocks = manager.markdown_to_blocks(markdown)

            assert len(blocks) == 1
            assert blocks[0]["type"] == "paragraph"

    def test_heading(self, mock_token):
        """Test converting markdown headings."""
        with patch.dict(os.environ, {"NOTION_TOKEN": "test_token"}):
            manager = NotionManager()

            markdown = "# Heading 1\n## Heading 2\n### Heading 3"
            blocks = manager.markdown_to_blocks(markdown)

            assert len(blocks) == 3
            assert blocks[0]["type"] == "heading_1"
            assert blocks[1]["type"] == "heading_2"
            assert blocks[2]["type"] == "heading_3"

    def test_bullets(self, mock_token):
        """Test converting markdown bullet lists."""
        with patch.dict(os.environ, {"NOTION_TOKEN": "test_token"}):
            manager = NotionManager()

            markdown = "- Item 1\n- Item 2\n* Item 3"
            blocks = manager.markdown_to_blocks(markdown)

            assert len(blocks) == 3
            assert all(b["type"] == "bulleted_list_item" for b in blocks)

    def test_code_block(self, mock_token):
        """Test converting markdown code blocks."""
        with patch.dict(os.environ, {"NOTION_TOKEN": "test_token"}):
            manager = NotionManager()

            markdown = "```python\ndef hello():\n    pass\n```"
            blocks = manager.markdown_to_blocks(markdown)

            assert len(blocks) == 1
            assert blocks[0]["type"] == "code"
            assert blocks[0]["code"]["language"] == "python"

    def test_todo(self, mock_token):
        """Test converting markdown todo items."""
        with patch.dict(os.environ, {"NOTION_TOKEN": "test_token"}):
            manager = NotionManager()

            markdown = "- [ ] Task 1\n- [x] Task 2"
            blocks = manager.markdown_to_blocks(markdown)

            assert len(blocks) == 2
            assert blocks[0]["type"] == "to_do"
            assert blocks[0]["to_do"]["checked"] is False
            assert blocks[1]["to_do"]["checked"] is True

    def test_divider(self, mock_token):
        """Test converting markdown divider."""
        with patch.dict(os.environ, {"NOTION_TOKEN": "test_token"}):
            manager = NotionManager()

            markdown = "---"
            blocks = manager.markdown_to_blocks(markdown)

            assert len(blocks) == 1
            assert blocks[0]["type"] == "divider"

    def test_quote(self, mock_token):
        """Test converting markdown quote."""
        with patch.dict(os.environ, {"NOTION_TOKEN": "test_token"}):
            manager = NotionManager()

            markdown = "> This is a quote"
            blocks = manager.markdown_to_blocks(markdown)

            assert len(blocks) == 1
            assert blocks[0]["type"] == "quote"


class TestContextManager:
    """Test async context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token):
        """Test using manager as context manager."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            async with NotionManager() as manager:
                assert manager is not None
                assert manager.token == mock_token

    @pytest.mark.asyncio
    async def test_close(self, mock_token):
        """Test closing HTTP client."""
        with patch.dict(os.environ, {"NOTION_TOKEN": mock_token}):
            manager = NotionManager()

            # Mock the close method
            manager.client.aclose = AsyncMock()

            await manager.close()

            manager.client.aclose.assert_called_once()


# =============================================================================
# Run Tests
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
