"""
Data types and enums for {SERVICE_NAME} integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


# =============================================================================
# Enums
# =============================================================================


class EntityType(str, Enum):
    """Types of entities."""

    TYPE_A = "type_a"
    TYPE_B = "type_b"
    TYPE_C = "type_c"


class EntityStatus(str, Enum):
    """Entity statuses."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class Entity:
    """Base entity data class."""

    id: str
    name: str
    type: EntityType
    status: EntityStatus
    created_at: datetime
    updated_at: datetime | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class EntitySpec:
    """Specification for creating/updating entities."""

    name: str
    type: EntityType
    description: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class OperationResult:
    """Result of an operation."""

    success: bool
    entity_id: str | None = None
    message: str | None = None
    data: dict[str, Any] | None = None
    error: str | None = None
