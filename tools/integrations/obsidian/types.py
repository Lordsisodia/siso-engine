"""
Data types and enums for Obsidian integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# =============================================================================
# Enums
# =============================================================================


class NoteType(str, Enum):
    """Types of notes that can be exported to Obsidian."""

    SESSION = "session"
    INSIGHT = "insight"
    CONTEXT = "context"
    PLAN = "plan"


class NoteStatus(str, Enum):
    """Note statuses."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class SessionData:
    """Data for an agent session note."""

    agent_id: str
    agent_name: str
    session_id: str
    start_time: datetime
    end_time: datetime | None = None
    goal: str | None = None
    outcome: str | None = None
    steps: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    related_notes: list[str] = field(default_factory=list)  # Wikilinks to related notes


@dataclass
class InsightData:
    """Data for an insight note."""

    title: str
    content: str
    category: str | None = None
    source_session: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)
    related_notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextData:
    """Data for an agent context note."""

    agent_id: str
    agent_name: str
    context_type: str  # e.g., "working", "extended", "archival"
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    related_notes: list[str] = field(default_factory=list)


@dataclass
class PlanData:
    """Data for a plan note."""

    title: str
    description: str | None = None
    steps: list[dict[str, Any]] = field(default_factory=list)
    status: str = "planning"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    related_notes: list[str] = field(default_factory=list)


@dataclass
class ExportResult:
    """Result of an export operation."""

    success: bool
    file_path: str | None = None
    note_type: NoteType | None = None
    message: str | None = None
    error: str | None = None


@dataclass
class Wikilink:
    """Represents a wikilink to another note."""

    title: str
    alias: str | None = None
    section: str | None = None  # For linking to specific sections

    def to_markdown(self) -> str:
        """Convert wikilink to Markdown format."""
        if self.section:
            base = f"{self.title}#{self.section}"
        else:
            base = self.title

        if self.alias:
            return f"[[{base}|{self.alias}]]"
        return f"[[{base}]]"
