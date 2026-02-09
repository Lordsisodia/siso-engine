"""
Notion Manager for BlackBox5
=============================

Main integration class for Notion service.

Features:
- Create pages with rich content blocks
- Query and search databases
- Append blocks to existing pages
- Markdown to Notion blocks conversion
- Full CRUD operations on pages and databases

Usage:
    >>> manager = NotionManager(token="your_token")
    >>> page = await manager.create_page(parent_id, properties, children)
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from .types import (
    Block,
    BlockType,
    Color,
    Database,
    DatabaseQuery,
    DatabaseSpec,
    Page,
    PageSpec,
    ParentType,
    PropertyType,
    RichText,
    SearchResult,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Main Manager Class
# =============================================================================


class NotionManager:
    """
    Main manager class for Notion integration.

    Authentication:
        Uses API token from environment variable or parameter.

    Rate Limits:
        - 3 requests per second (recommended)
        - 2,700 requests per 15 minutes (hard limit)

    API Version:
        - 2025-09-03

    Example:
        >>> manager = NotionManager(token="your_token")
        >>> page = await manager.create_page(parent_id, properties, children)
        >>> print(page.url)
    """

    API_BASE = "https://api.notion.com"
    API_VERSION = "2025-09-03"
    NOTION_VERSION = "2022-06-28"  # Notion-Version header

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = "https://api.notion.com",
        timeout: int = 30,
    ):
        """
        Initialize Notion manager.

        Args:
            token: API token (default: from NOTION_TOKEN env var)
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        import os

        self.token = token or os.environ.get("NOTION_TOKEN")
        if not self.token:
            raise ValueError(
                "API token required. Set NOTION_TOKEN "
                "environment variable or pass token parameter."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Notion-Version": self.NOTION_VERSION,
                "Content-Type": "application/json",
                "User-Agent": "BlackBox5/1.0",
            },
            timeout=timeout,
        )

        logger.info(f"Initialized NotionManager for {self.base_url}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
        logger.debug("Closed HTTP client")

    # -------------------------------------------------------------------------
    # Core Operations
    # -------------------------------------------------------------------------

    async def create_page(
        self,
        parent_id: str,
        properties: dict[str, Any],
        children: Optional[list[dict[str, Any]]] = None,
        icon: Optional[str] = None,
        cover: Optional[str] = None,
    ) -> Page:
        """
        Create a new page.

        Args:
            parent_id: Parent page or database ID
            properties: Page properties (must include title)
            children: Block children to add to page
            icon: Page icon (emoji or URL)
            cover: Page cover image URL

        Returns:
            Created page data

        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.info(f"Creating page in parent: {parent_id}")

        # Determine parent type
        parent = {}
        if parent_id.startswith("page_"):
            parent["type"] = "page_id"
            parent["page_id"] = parent_id
        else:
            parent["type"] = "database_id"
            parent["database_id"] = parent_id

        page_data: dict[str, Any] = {"parent": parent, "properties": properties}

        if icon:
            if icon.startswith("http"):
                page_data["icon"] = {"external": {"url": icon}}
            else:
                page_data["icon"] = {"emoji": icon}

        if cover:
            page_data["cover"] = {"external": {"url": cover}}

        if children:
            page_data["children"] = children

        response = await self.client.post("/v1/pages", json=page_data)
        response.raise_for_status()

        data = response.json()
        page = self._parse_page(data)

        logger.info(f"✅ Created page: {page.id}")
        return page

    async def get_page(self, page_id: str) -> Optional[Page]:
        """
        Get page by ID.

        Args:
            page_id: Page ID

        Returns:
            Page data or None if not found
        """
        logger.debug(f"Getting page: {page_id}")

        try:
            response = await self.client.get(f"/v1/pages/{page_id}")
            response.raise_for_status()

            data = response.json()
            return self._parse_page(data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Page not found: {page_id}")
                return None
            raise

    async def update_page(
        self,
        page_id: str,
        properties: dict[str, Any],
        archived: bool = False,
    ) -> Optional[Page]:
        """
        Update page properties.

        Args:
            page_id: Page ID
            properties: Properties to update
            archived: Whether to archive the page

        Returns:
            Updated page or None if not found
        """
        logger.info(f"Updating page: {page_id}")

        try:
            page_data: dict[str, Any] = {"properties": properties, "archived": archived}

            response = await self.client.patch(f"/v1/pages/{page_id}", json=page_data)
            response.raise_for_status()

            data = response.json()
            page = self._parse_page(data)

            logger.info(f"✅ Updated page: {page_id}")
            return page

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Page not found: {page_id}")
                return None
            raise

    async def delete_page(self, page_id: str) -> bool:
        """
        Delete (archive) a page.

        Args:
            page_id: Page ID

        Returns:
            True if successful, False if not found
        """
        logger.info(f"Archiving page: {page_id}")

        try:
            response = await self.client.patch(
                f"/v1/pages/{page_id}", json={"archived": True}
            )
            response.raise_for_status()

            logger.info(f"✅ Archived page: {page_id}")
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Page not found: {page_id}")
                return False
            raise

    async def append_blocks(
        self,
        block_id: str,
        blocks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Append blocks to a page or block.

        Args:
            block_id: Block or page ID
            blocks: Blocks to append

        Returns:
            List of created blocks
        """
        logger.info(f"Appending {len(blocks)} blocks to {block_id}")

        response = await self.client.patch(
            f"/v1/blocks/{block_id}/children",
            json={"children": blocks},
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        logger.info(f"✅ Appended {len(results)} blocks")
        return results

    async def get_block_children(
        self,
        block_id: str,
        page_size: int = 100,
        start_cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get children of a block.

        Args:
            block_id: Block ID
            page_size: Number of results per page
            start_cursor: Cursor for pagination

        Returns:
            Dictionary with results and pagination info
        """
        logger.debug(f"Getting children of block: {block_id}")

        params = {"page_size": page_size}
        if start_cursor:
            params["start_cursor"] = start_cursor

        response = await self.client.get(f"/v1/blocks/{block_id}/children", params=params)
        response.raise_for_status()

        data = response.json()
        logger.debug(f"Found {len(data.get('results', []))} children")

        return data

    # -------------------------------------------------------------------------
    # Database Operations
    # -------------------------------------------------------------------------

    async def create_database(
        self,
        parent_id: str,
        title: str,
        properties: dict[str, dict[str, Any]],
        description: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> Database:
        """
        Create a new database.

        Args:
            parent_id: Parent page ID
            title: Database title
            properties: Database property schema
            description: Database description
            icon: Database icon (emoji or URL)

        Returns:
            Created database data
        """
        logger.info(f"Creating database: {title}")

        db_data: dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": parent_id},
            "properties": properties,
            "title": [{"type": "text", "text": {"content": title}}],
        }

        if description:
            db_data["description"] = [
                {"type": "text", "text": {"content": description}}
            ]

        if icon:
            if icon.startswith("http"):
                db_data["icon"] = {"external": {"url": icon}}
            else:
                db_data["icon"] = {"emoji": icon}

        response = await self.client.post("/v1/databases", json=db_data)
        response.raise_for_status()

        data = response.json()
        database = self._parse_database(data)

        logger.info(f"✅ Created database: {database.id}")
        return database

    async def get_database(self, database_id: str) -> Optional[Database]:
        """
        Get database by ID.

        Args:
            database_id: Database ID

        Returns:
            Database data or None if not found
        """
        logger.debug(f"Getting database: {database_id}")

        try:
            response = await self.client.get(f"/v1/databases/{database_id}")
            response.raise_for_status()

            data = response.json()
            return self._parse_database(data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Database not found: {database_id}")
                return None
            raise

    async def query_database(
        self,
        database_id: str,
        filter: Optional[dict[str, Any]] = None,
        sorts: Optional[list[dict[str, Any]]] = None,
        start_cursor: Optional[str] = None,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """
        Query a database.

        Args:
            database_id: Database ID
            filter: Query filter (Notion filter format)
            sorts: Sort configuration
            start_cursor: Pagination cursor
            page_size: Results per page (max 100)

        Returns:
            Query results with pagination info
        """
        logger.debug(f"Querying database: {database_id}")

        payload: dict[str, Any] = {"page_size": page_size}

        if filter:
            payload["filter"] = filter

        if sorts:
            payload["sorts"] = sorts

        if start_cursor:
            payload["start_cursor"] = start_cursor

        response = await self.client.post(
            f"/v1/databases/{database_id}/query", json=payload
        )
        response.raise_for_status()

        data = response.json()
        logger.debug(f"Found {len(data.get('results', []))} results")

        return data

    async def update_database(
        self,
        database_id: str,
        title: Optional[str] = None,
        properties: Optional[dict[str, dict[str, Any]]] = None,
        archived: bool = False,
    ) -> Optional[Database]:
        """
        Update database properties or title.

        Args:
            database_id: Database ID
            title: New title
            properties: New properties schema (partial update not supported)
            archived: Whether to archive

        Returns:
            Updated database or None if not found
        """
        logger.info(f"Updating database: {database_id}")

        try:
            db_data: dict[str, Any] = {"archived": archived}

            if title:
                db_data["title"] = [{"type": "text", "text": {"content": title}}]

            if properties:
                db_data["properties"] = properties

            response = await self.client.patch(f"/v1/databases/{database_id}", json=db_data)
            response.raise_for_status()

            data = response.json()
            database = self._parse_database(data)

            logger.info(f"✅ Updated database: {database_id}")
            return database

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Database not found: {database_id}")
                return None
            raise

    # -------------------------------------------------------------------------
    # Search Operations
    # -------------------------------------------------------------------------

    async def search(
        self,
        query: Optional[str] = None,
        filter: Optional[dict[str, str]] = None,
        sort: Optional[dict[str, str]] = None,
        start_cursor: Optional[str] = None,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """
        Search workspace for pages and databases.

        Args:
            query: Search query text
            filter: Filter by object type ("page" or "database")
            sort: Sort direction ("ascending" or "descending")
            start_cursor: Pagination cursor
            page_size: Results per page (max 100)

        Returns:
            Search results with pagination info
        """
        logger.debug(f"Searching: {query}")

        payload: dict[str, Any] = {"page_size": page_size}

        if query:
            payload["query"] = query

        if filter:
            payload["filter"] = filter

        if sort:
            payload["sort"] = sort

        if start_cursor:
            payload["start_cursor"] = start_cursor

        response = await self.client.post("/v1/search", json=payload)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])
        logger.debug(f"Found {len(results)} results")

        return data

    async def search_pages(
        self,
        query: str,
        page_size: int = 100,
    ) -> list[SearchResult]:
        """
        Search for pages only.

        Args:
            query: Search query
            page_size: Max results

        Returns:
            List of search results
        """
        data = await self.search(
            query=query,
            filter={"property": "object", "value": "page"},
            page_size=page_size,
        )

        results = []
        for item in data.get("results", []):
            results.append(self._parse_search_result(item))

        return results

    async def search_databases(
        self,
        query: str,
        page_size: int = 100,
    ) -> list[SearchResult]:
        """
        Search for databases only.

        Args:
            query: Search query
            page_size: Max results

        Returns:
            List of search results
        """
        data = await self.search(
            query=query,
            filter={"property": "object", "value": "database"},
            page_size=page_size,
        )

        results = []
        for item in data.get("results", []):
            results.append(self._parse_search_result(item))

        return results

    # -------------------------------------------------------------------------
    # Markdown Conversion
    # -------------------------------------------------------------------------

    def markdown_to_blocks(self, markdown_text: str) -> list[dict[str, Any]]:
        """
        Convert markdown text to Notion blocks.

        Args:
            markdown_text: Markdown formatted text

        Returns:
            List of Notion block dictionaries
        """
        blocks = []
        lines = markdown_text.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].rstrip()

            # Empty line
            if not line:
                i += 1
                continue

            # Code blocks
            if line.startswith("```"):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    code_lines.append(lines[i])
                    i += 1

                language = line[3:].strip() or "plain text"
                blocks.append(
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{"type": "text", "text": {"content": "\n".join(code_lines)}}],
                            "language": language,
                        },
                    }
                )
                i += 1
                continue

            # Headings
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                content = line[level:].strip()
                heading_type = f"heading_{min(level, 3)}"

                blocks.append(
                    {
                        "object": "block",
                        "type": heading_type,
                        heading_type: {
                            "rich_text": [{"type": "text", "text": {"content": content}}]
                        },
                    }
                )
                i += 1
                continue

            # Bullet lists
            if line.startswith(("-", "*")) and line[1] in (" ", "\t"):
                content = line[1:].strip()
                blocks.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": content}}]
                        },
                    }
                )
                i += 1
                continue

            # Numbered lists
            if re.match(r"^\d+\.", line):
                content = re.sub(r"^\d+\.\s*", "", line)
                blocks.append(
                    {
                        "object": "block",
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": content}}]
                        },
                    }
                )
                i += 1
                continue

            # Todo/checkbox
            if line.startswith(("[ ]", "[x]")):
                checked = line.startswith("[x]")
                content = line[3:].strip()
                blocks.append(
                    {
                        "object": "block",
                        "type": "to_do",
                        "to_do": {
                            "rich_text": [{"type": "text", "text": {"content": content}}],
                            "checked": checked,
                        },
                    }
                )
                i += 1
                continue

            # Quote
            if line.startswith(">"):
                content = line[1:].strip()
                blocks.append(
                    {
                        "object": "block",
                        "type": "quote",
                        "quote": {
                            "rich_text": [{"type": "text", "text": {"content": content}}]
                        },
                    }
                )
                i += 1
                continue

            # Divider
            if line.startswith("---"):
                blocks.append(
                    {
                        "object": "block",
                        "type": "divider",
                        "divider": {},
                    }
                )
                i += 1
                continue

            # Default: paragraph
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": line}}]
                    },
                }
            )
            i += 1

        return blocks

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    async def check_connection(self) -> bool:
        """
        Check API connection by searching workspace.

        Returns:
            True if connection successful
        """
        try:
            response = await self.client.post("/v1/search", json={"page_size": 1})
            response.raise_for_status()
            logger.info("✅ Connection check successful")
            return True
        except Exception as e:
            logger.error(f"❌ Connection check failed: {e}")
            return False

    async def get_user_info(self) -> dict[str, Any]:
        """
        Get information about the authorized user.

        Returns:
            User information
        """
        logger.debug("Getting user info")

        response = await self.client.get("/v1/users/me")
        response.raise_for_status()

        data = response.json()
        return data

    def _parse_page(self, data: dict[str, Any]) -> Page:
        """Parse page data from API response."""
        page_id = data.get("id", "")

        # Extract title from properties
        title = ""
        properties = data.get("properties", {})
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                title_array = prop_data.get("title", [])
                if title_array:
                    title = title_array[0].get("plain_text", "")
                break

        # Get icon
        icon = None
        if icon_data := data.get("icon"):
            if icon_data.get("type") == "emoji":
                icon = icon_data.get("emoji")
            elif icon_data.get("type") == "external":
                icon = icon_data.get("external", {}).get("url")

        # Get cover
        cover = None
        if cover_data := data.get("cover"):
            if cover_data.get("type") == "external":
                cover = cover_data.get("external", {}).get("url")

        # Get parent
        parent = data.get("parent", {})
        parent_id = parent.get("page_id") or parent.get("database_id")
        parent_type = None
        if "page_id" in parent:
            parent_type = ParentType.PAGE
        elif "database_id" in parent:
            parent_type = ParentType.DATABASE

        # Parse dates
        created_at = None
        if created_time := data.get("created_time"):
            created_at = datetime.fromisoformat(created_time.replace("Z", "+00:00"))

        last_edited = None
        if edited_time := data.get("last_edited_time"):
            last_edited = datetime.fromisoformat(edited_time.replace("Z", "+00:00"))

        return Page(
            id=page_id,
            title=title,
            url=data.get("url", ""),
            icon=icon,
            cover=cover,
            parent_id=parent_id,
            parent_type=parent_type,
            created_at=created_at,
            last_edited=last_edited,
            archived=data.get("archived", False),
            properties=properties,
        )

    def _parse_database(self, data: dict[str, Any]) -> Database:
        """Parse database data from API response."""
        db_id = data.get("id", "")

        # Extract title
        title = ""
        title_array = data.get("title", [])
        if title_array:
            title = title_array[0].get("plain_text", "")

        # Extract description
        description = None
        desc_array = data.get("description", [])
        if desc_array:
            description = desc_array[0].get("plain_text")

        # Get icon
        icon = None
        if icon_data := data.get("icon"):
            if icon_data.get("type") == "emoji":
                icon = icon_data.get("emoji")
            elif icon_data.get("type") == "external":
                icon = icon_data.get("external", {}).get("url")

        # Get parent
        parent = data.get("parent", {})
        parent_id = parent.get("page_id") or parent.get("workspace")

        # Parse dates
        created_at = None
        if created_time := data.get("created_time"):
            created_at = datetime.fromisoformat(created_time.replace("Z", "+00:00"))

        last_edited = None
        if edited_time := data.get("last_edited_time"):
            last_edited = datetime.fromisoformat(edited_time.replace("Z", "+00:00"))

        return Database(
            id=db_id,
            title=title,
            url=data.get("url", ""),
            description=description,
            icon=icon,
            parent_id=parent_id,
            created_at=created_at,
            last_edited=last_edited,
            properties=data.get("properties", {}),
        )

    def _parse_search_result(self, item: dict[str, Any]) -> SearchResult:
        """Parse search result item."""
        object_type = item.get("object", "")
        item_id = item.get("id", "")

        # Extract title
        title = ""
        if object_type == "page":
            properties = item.get("properties", {})
            for prop_name, prop_data in properties.items():
                if prop_data.get("type") == "title":
                    title_array = prop_data.get("title", [])
                    if title_array:
                        title = title_array[0].get("plain_text", "")
                    break
        elif object_type == "database":
            title_array = item.get("title", [])
            if title_array:
                title = title_array[0].get("plain_text", "")

        # Get icon
        icon = None
        if icon_data := item.get("icon"):
            if icon_data.get("type") == "emoji":
                icon = icon_data.get("emoji")

        # Get parent
        parent = item.get("parent", {})
        parent_id = parent.get("page_id") or parent.get("database_id") or parent.get("workspace")

        return SearchResult(
            object_type=object_type,
            id=item_id,
            title=title,
            url=item.get("url", ""),
            icon=icon,
            parent_id=parent_id,
        )


# =============================================================================
# Rate Limiting Helper
# =============================================================================


class RateLimiter:
    """Simple rate limiter for Notion API (3 req/sec)."""

    def __init__(self, calls: int = 3, period: float = 1.0):
        """Initialize rate limiter.

        Args:
            calls: Number of calls allowed
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
        self.timestamps = []

    async def acquire(self):
        """Wait if rate limit would be exceeded."""
        import asyncio
        import time

        now = time.time()

        # Remove old timestamps
        self.timestamps = [t for t in self.timestamps if now - t < self.period]

        # Wait if at limit
        if len(self.timestamps) >= self.calls:
            sleep_time = self.period - (now - self.timestamps[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self.timestamps.append(now)
