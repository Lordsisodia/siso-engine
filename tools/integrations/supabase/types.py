"""
Data types and enums for Supabase integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable


# =============================================================================
# Enums
# =============================================================================


class StorageEventType(str, Enum):
    """Types of storage events."""

    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class FileContentType(str, Enum):
    """Common file content types."""

    TEXT_PLAIN = "text/plain"
    APPLICATION_JSON = "application/json"
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    IMAGE_GIF = "image/gif"
    APPLICATION_PDF = "application/pdf"
    TEXT_CSV = "text/csv"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class TableSpec:
    """Specification for a table query."""

    name: str
    filters: dict[str, Any] | None = None
    columns: str | list[str] | None = None
    limit: int | None = None
    offset: int | None = None
    order_by: str | None = None
    ascending: bool = True


@dataclass
class QueryFilter:
    """Query filter specification."""

    column: str
    operator: str  # eq, gt, lt, gte, lte, neq, like, ilike, in, is
    value: Any


@dataclass
class InsertResult:
    """Result of an insert operation."""

    data: list[dict[str, Any]]
    count: int | None = None
    error: str | None = None


@dataclass
class UpdateResult:
    """Result of an update operation."""

    data: list[dict[str, Any]]
    count: int | None = None
    error: str | None = None


@dataclass
class DeleteResult:
    """Result of a delete operation."""

    count: int | None = None
    error: str | None = None


@dataclass
class StorageUploadSpec:
    """Specification for uploading to storage."""

    bucket: str
    path: str
    content: bytes | str
    content_type: str | None = None
    upsert: bool = False


@dataclass
class StorageDownloadSpec:
    """Specification for downloading from storage."""

    bucket: str
    path: str


@dataclass
class StorageFile:
    """Storage file information."""

    name: str
    bucket: str
    path: str
    size: int
    content_type: str
    updated_at: datetime
    metadata: dict[str, Any] | None = None


@dataclass
class EdgeFunctionSpec:
    """Specification for invoking an Edge Function."""

    name: str
    body: dict[str, Any] | None = None
    headers: dict[str, str] | None = None


@dataclass
class EdgeFunctionResult:
    """Result from Edge Function invocation."""

    data: dict[str, Any]
    status_code: int
    headers: dict[str, str]
    error: str | None = None


@dataclass
class SubscriptionSpec:
    """Specification for subscribing to changes."""

    table: str
    event: StorageEventType
    callback: Callable[[dict[str, Any]], None]
    schema: str = "public"
    filter: str | None = None


# =============================================================================
# Type Aliases
# =============================================================================


ChangeCallback = Callable[[dict[str, Any]], None]
