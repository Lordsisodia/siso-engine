"""
Data types and enums for Notion integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Literal


# =============================================================================
# Enums
# =============================================================================


class BlockType(str, Enum):
    """Notion block types."""

    PARAGRAPH = "paragraph"
    HEADING_1 = "heading_1"
    HEADING_2 = "heading_2"
    HEADING_3 = "heading_3"
    BULLETED_LIST = "bulleted_list_item"
    NUMBERED_LIST = "numbered_list_item"
    TO_DO = "to_do"
    TOGGLE = "toggle"
    QUOTE = "quote"
    DIVIDER = "divider"
    CALLOUT = "callout"
    CODE = "code"
    TABLE = "table"
    TABLE_ROW = "table_row"
    EMBED = "embed"
    IMAGE = "image"
    VIDEO = "video"
    FILE = "file"
    PDF = "pdf"
    BOOKMARK = "bookmark"
    EQUATION = "equation"
    SYNCHRONIZED_BLOCK = "synchronized_block"


class PropertyType(str, Enum):
    """Notion property types."""

    TITLE = "title"
    RICH_TEXT = "rich_text"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    PEOPLE = "people"
    FILES = "files"
    CHECKBOX = "checkbox"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    FORMULA = "formula"
    RELATION = "relation"
    ROLLUP = "rollup"
    CREATED_TIME = "created_time"
    CREATED_BY = "created_by"
    LAST_EDITED_TIME = "last_edited_time"
    LAST_EDITED_BY = "last_edited_by"


class ParentType(str, Enum):
    """Parent types for pages and databases."""

    PAGE = "page_id"
    DATABASE = "database_id"
    WORKSPACE = "workspace"


class Color(str, Enum):
    """Text and background colors in Notion."""

    DEFAULT = "default"
    GRAY = "gray"
    BROWN = "brown"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"
    PINK = "pink"
    RED = "red"
    GRAY_BACKGROUND = "gray_background"
    BROWN_BACKGROUND = "brown_background"
    ORANGE_BACKGROUND = "orange_background"
    YELLOW_BACKGROUND = "yellow_background"
    GREEN_BACKGROUND = "green_background"
    BLUE_BACKGROUND = "blue_background"
    PURPLE_BACKGROUND = "purple_background"
    PINK_BACKGROUND = "pink_background"
    RED_BACKGROUND = "red_background"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RichText:
    """Rich text object for Notion blocks."""

    content: str
    type: Literal["text"] = "text"
    annotations: dict[str, Any] | None = None
    href: str | None = None
    plain_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to Notion API format."""
        return {
            "type": self.type,
            "text": {"content": self.content, "link": {"url": self.href} if self.href else None},
            "annotations": self.annotations or {},
            "plain_text": self.plain_text or self.content,
        }


@dataclass
class Block:
    """Notion block data class."""

    type: BlockType
    content: str | list[RichText] | dict[str, Any]
    children: list[Block] | None = None
    checked: bool | None = None
    color: Color = Color.DEFAULT
    language: str | None = None  # For code blocks

    def to_dict(self) -> dict[str, Any]:
        """Convert to Notion API format."""
        block_dict = {
            "object": "block",
            "type": self.type.value,
            "id": (
                "pending"
            ),  # Placeholder ID for new blocks
        }

        if self.type == BlockType.PARAGRAPH:
            text_content = self._prepare_text_content()
            block_dict[self.type.value] = {"rich_text": text_content, "color": self.color.value}

        elif self.type in (BlockType.HEADING_1, BlockType.HEADING_2, BlockType.HEADING_3):
            text_content = self._prepare_text_content()
            block_dict[self.type.value] = {
                "rich_text": text_content,
                "color": self.color.value,
                "is_toggleable": False,
            }

        elif self.type == BlockType.BULLETED_LIST:
            text_content = self._prepare_text_content()
            block_dict[self.type.value] = {"rich_text": text_content, "color": self.color.value}

        elif self.type == BlockType.NUMBERED_LIST:
            text_content = self._prepare_text_content()
            block_dict[self.type.value] = {"rich_text": text_content, "color": self.color.value}

        elif self.type == BlockType.TO_DO:
            text_content = self._prepare_text_content()
            block_dict[self.type.value] = {
                "rich_text": text_content,
                "checked": self.checked or False,
                "color": self.color.value,
            }

        elif self.type == BlockType.TOGGLE:
            text_content = self._prepare_text_content()
            block_dict[self.type.value] = {"rich_text": text_content, "color": self.color.value}

        elif self.type == BlockType.QUOTE:
            text_content = self._prepare_text_content()
            block_dict[self.type.value] = {"rich_text": text_content, "color": self.color.value}

        elif self.type == BlockType.DIVIDER:
            block_dict[self.type.value] = {}

        elif self.type == BlockType.CALLOUT:
            text_content = self._prepare_text_content()
            block_dict[self.type.value] = {
                "rich_text": text_content,
                "icon": {"emoji": "ℹ️"},
                "color": self.color.value,
            }

        elif self.type == BlockType.CODE:
            text_content = self._prepare_text_content()
            block_dict[self.type.value] = {
                "rich_text": text_content,
                "language": self.language or "plain text",
                "caption": [],
            }

        else:
            # Generic block type
            block_dict[self.type.value] = {}

        return block_dict

    def _prepare_text_content(self) -> list[dict[str, Any]]:
        """Prepare rich text content from various input formats."""
        if isinstance(self.content, str):
            return [{"type": "text", "text": {"content": self.content}}]
        elif isinstance(self.content, list):
            return [item.to_dict() if isinstance(item, RichText) else item for item in self.content]
        elif isinstance(self.content, dict):
            return [self.content]
        return []


@dataclass
class PageSpec:
    """Specification for creating/updating pages."""

    title: str
    parent_id: str
    parent_type: ParentType = ParentType.PAGE
    icon: str | None = None  # Emoji or icon URL
    cover: str | None = None  # Image URL
    properties: dict[str, Any] | None = None
    children: list[Block] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to Notion API format."""
        page_dict = {
            "parent": {self.parent_type.value: self.parent_id},
            "properties": {
                "title": {
                    "title": [{"type": "text", "text": {"content": self.title}}]
                }
            },
        }

        if self.icon:
            if self.icon.startswith("http"):
                page_dict["icon"] = {"external": {"url": self.icon}}
            else:
                page_dict["icon"] = {"emoji": self.icon}

        if self.cover:
            page_dict["cover"] = {"external": {"url": self.cover}}

        if self.properties:
            page_dict["properties"].update(self.properties)

        return page_dict


@dataclass
class DatabaseSpec:
    """Specification for creating databases."""

    title: str
    parent_id: str
    parent_type: ParentType = ParentType.PAGE
    properties: dict[str, dict[str, Any]] | None = None
    description: str | None = None
    icon: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to Notion API format."""
        db_dict = {
            "parent": {self.parent_type.value: self.parent_id},
            "properties": {
                "Name": {
                    "title": {}
                }
            },
        }

        if self.description:
            db_dict["description"] = [{"type": "text", "text": {"content": self.description}}]

        if self.icon:
            if self.icon.startswith("http"):
                db_dict["icon"] = {"external": {"url": self.icon}}
            else:
                db_dict["icon"] = {"emoji": self.icon}

        if self.properties:
            db_dict["properties"].update(self.properties)

        return db_dict


@dataclass
class DatabaseQuery:
    """Specification for querying databases."""

    database_id: str
    filter: dict[str, Any] | None = None
    sorts: list[dict[str, Any]] | None = None
    start_cursor: str | None = None
    page_size: int = 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to Notion API format."""
        query_dict: dict[str, Any] = {}

        if self.filter:
            query_dict["filter"] = self.filter

        if self.sorts:
            query_dict["sorts"] = self.sorts

        if self.start_cursor:
            query_dict["start_cursor"] = self.start_cursor

        query_dict["page_size"] = self.page_size

        return query_dict


@dataclass
class SearchResult:
    """Result from Notion search."""

    object_type: str  # "page" or "database"
    id: str
    title: str
    url: str
    icon: str | None = None
    parent_id: str | None = None


@dataclass
class Page:
    """Notion page data class."""

    id: str
    title: str
    url: str
    icon: str | None = None
    cover: str | None = None
    parent_id: str | None = None
    parent_type: ParentType | None = None
    created_at: datetime | None = None
    last_edited: datetime | None = None
    archived: bool = False
    properties: dict[str, Any] | None = None


@dataclass
class Database:
    """Notion database data class."""

    id: str
    title: str
    url: str
    description: str | None = None
    icon: str | None = None
    parent_id: str | None = None
    created_at: datetime | None = None
    last_edited: datetime | None = None
    properties: dict[str, Any] | None = None
