"""
Vibe Kanban Integration for BlackBox5
======================================

Manager class for Vibe Kanban operations, adapted from CCPM's GitHub patterns.
Provides a unified interface for creating and managing Kanban cards.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================


class CardStatus(str, Enum):
    """Card status values."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"
    ABORTED = "aborted"


class Column(str, Enum):
    """Kanban column names."""

    BACKLOG = "backlog"
    TODO = "todo"
    DOING = "doing"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"


# Status to Column mapping
STATUS_TO_COLUMN = {
    CardStatus.TODO: Column.BACKLOG,
    CardStatus.IN_PROGRESS: Column.DOING,
    CardStatus.IN_REVIEW: Column.IN_REVIEW,
    CardStatus.DONE: Column.DONE,
    CardStatus.BLOCKED: Column.BLOCKED,
    CardStatus.ABORTED: Column.BACKLOG,
}


@dataclass
class CardData:
    """Kanban card data."""

    id: int
    title: str
    description: str
    status: CardStatus
    column: Column
    position: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    project_id: int | None = None
    repo_id: int | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class CardSpec:
    """Specification for creating a new card."""

    title: str
    description: str
    acceptance_criteria: list[str] | None = None
    epic_link: str | None = None
    spec_link: str | None = None
    related_cards: list[int] | None = None
    labels: list[str] | None = None
    position: int = 0
    project_id: int | None = None
    repo_id: int | None = None


@dataclass
class CommentData:
    """Comment data for cards."""

    body: str
    author: str = "BlackBox5"
    created_at: datetime | None = None


# =============================================================================
# Vibe Kanban Manager
# =============================================================================


class VibeKanbanManager:
    """
    Main manager class for Vibe Kanban operations.

    Follows the same patterns as GitHub's GitHubManager but adapted for
    Vibe Kanban's card-based workflow system.

    Features:
    - Create cards in different columns
    - Move cards between columns
    - Update card status with automatic column mapping
    - Add comments to cards
    - Query cards with filters
    - Sync with local memory (CCPM-style)

    Usage:
        manager = VibeKanbanManager(
            api_url="http://localhost:3001",
            memory_path="./memory/working"
        )

        # Create card
        card = await manager.create_card(
            title="Fix authentication bug",
            description="Users cannot login",
            column=Column.DOING
        )

        # Move card
        await manager.move_card(card.id, Column.DONE)

        # Update status (automatically moves to correct column)
        await manager.update_card_status(card.id, CardStatus.DONE)
    """

    def __init__(
        self,
        api_url: str = "http://localhost:3001",
        api_token: str | None = None,
        memory_path: str | Path = "./memory/working",
        repo: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize Vibe Kanban manager.

        Args:
            api_url: Vibe Kanban API base URL (default: localhost:3001)
            api_token: Optional API token for authentication
            memory_path: Path to working memory directory
            repo: Repository identifier (for tracking)
            timeout: HTTP request timeout in seconds
        """
        self.api_url = api_url.rstrip("/")
        self.api_token = api_token
        self.memory_path = Path(memory_path)
        self.repo = repo
        self.timeout = timeout

        # Create memory directory
        self.memory_path.mkdir(parents=True, exist_ok=True)

        # Configure HTTP client
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"

            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    # -------------------------------------------------------------------------
    # Card Management
    # -------------------------------------------------------------------------

    async def create_card(
        self,
        title: str,
        description: str,
        column: Column = Column.BACKLOG,
        position: int = 0,
        project_id: int | None = None,
        repo_id: int | None = None,
    ) -> CardData:
        """
        Create a new Kanban card.

        Args:
            title: Card title
            description: Card description
            column: Target column (default: backlog)
            position: Position within column (0 = top)
            project_id: Optional project ID
            repo_id: Optional repository ID

        Returns:
            Created card data

        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.info(f"Creating card: {title} in column {column}")

        # Map column to status
        status = self._column_to_status(column)

        # Prepare payload
        payload = {
            "title": title,
            "description": description,
            "status": status.value,
            "position": position,
        }

        if project_id:
            payload["project_id"] = project_id
        if repo_id:
            payload["repo_id"] = repo_id

        # Create card via API
        response = await self.client.post("/api/cards", json=payload)
        response.raise_for_status()

        data = response.json()

        # Create card data
        card = CardData(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            status=CardStatus(data["status"]),
            column=column,
            position=data.get("position", 0),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
            project_id=data.get("project_id"),
            repo_id=data.get("repo_id"),
            raw_data=data,
        )

        # Store in local memory
        self._store_card_context(card)

        logger.info(f"✅ Created card #{card.id}: {card.title}")
        return card

    async def create_card_from_spec(self, spec: CardSpec) -> CardData:
        """
        Create a card from specification.

        Formats the description with acceptance criteria and context links.

        Args:
            spec: Card specification

        Returns:
            Created card data
        """
        # Format description with CCPM-style structure
        description = self._format_card_description(spec)

        # Map labels to column if priority label present
        column = Column.BACKLOG
        if spec.labels:
            for label in spec.labels:
                if "critical" in label.lower() or "urgent" in label.lower():
                    column = Column.DOING
                    break

        return await self.create_card(
            title=spec.title,
            description=description,
            column=column,
            position=spec.position,
            project_id=spec.project_id,
            repo_id=spec.repo_id,
        )

    async def move_card(self, card_id: int, column: Column) -> CardData:
        """
        Move a card to a different column.

        Args:
            card_id: Card ID
            column: Target column

        Returns:
            Updated card data

        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.info(f"Moving card #{card_id} to {column}")

        # Map column to status
        status = self._column_to_status(column)

        # Update via API
        payload = {"status": status.value}
        response = await self.client.patch(f"/api/cards/{card_id}", json=payload)
        response.raise_for_status()

        data = response.json()

        card = CardData(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            status=CardStatus(data["status"]),
            column=column,
            position=data.get("position", 0),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
            project_id=data.get("project_id"),
            repo_id=data.get("repo_id"),
            raw_data=data,
        )

        # Update local memory
        self._update_card_context(card)

        logger.info(f"✅ Moved card #{card_id} to {column}")
        return card

    async def update_card_status(
        self,
        card_id: int,
        status: CardStatus,
    ) -> CardData:
        """
        Update card status (automatically moves to correct column).

        This is the preferred method for status updates as it maintains
        the status-to-column mapping.

        Args:
            card_id: Card ID
            status: New status

        Returns:
            Updated card data

        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.info(f"Updating card #{card_id} status to {status.value}")

        # Map status to column
        column = STATUS_TO_COLUMN.get(status, Column.BACKLOG)

        # Update via API
        payload = {"status": status.value}
        response = await self.client.patch(f"/api/cards/{card_id}", json=payload)
        response.raise_for_status()

        data = response.json()

        card = CardData(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            status=CardStatus(data["status"]),
            column=column,
            position=data.get("position", 0),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
            project_id=data.get("project_id"),
            repo_id=data.get("repo_id"),
            raw_data=data,
        )

        # Update local memory
        self._update_card_context(card)

        logger.info(f"✅ Updated card #{card_id} to {status.value} (column: {column})")
        return card

    async def get_card(self, card_id: int) -> CardData:
        """
        Fetch a card by ID.

        Args:
            card_id: Card ID

        Returns:
            Card data

        Raises:
            httpx.HTTPError: If card not found
        """
        response = await self.client.get(f"/api/cards/{card_id}")
        response.raise_for_status()

        data = response.json()
        status = CardStatus(data["status"])
        column = STATUS_TO_COLUMN.get(status, Column.BACKLOG)

        return CardData(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            status=status,
            column=column,
            position=data.get("position", 0),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
            project_id=data.get("project_id"),
            repo_id=data.get("repo_id"),
            raw_data=data,
        )

    async def list_cards(
        self,
        status: CardStatus | None = None,
        column: Column | None = None,
        project_id: int | None = None,
        repo_id: int | None = None,
        limit: int = 100,
    ) -> list[CardData]:
        """
        List cards with optional filters.

        Args:
            status: Filter by status
            column: Filter by column
            project_id: Filter by project
            repo_id: Filter by repository
            limit: Maximum number of cards to return

        Returns:
            List of card data
        """
        params = {"limit": limit}

        if status:
            params["status"] = status.value
        if project_id:
            params["project_id"] = project_id
        if repo_id:
            params["repo_id"] = repo_id

        response = await self.client.get("/api/cards", params=params)
        response.raise_for_status()

        data = response.json()
        cards = []

        for card_data in data.get("cards", []):
            status = CardStatus(card_data["status"])
            column = STATUS_TO_COLUMN.get(status, Column.BACKLOG)

            # Filter by column if specified
            if column and STATUS_TO_COLUMN.get(status) != column:
                continue

            cards.append(
                CardData(
                    id=card_data["id"],
                    title=card_data["title"],
                    description=card_data["description"],
                    status=status,
                    column=column,
                    position=card_data.get("position", 0),
                    created_at=self._parse_datetime(card_data.get("created_at")),
                    updated_at=self._parse_datetime(card_data.get("updated_at")),
                    project_id=card_data.get("project_id"),
                    repo_id=card_data.get("repo_id"),
                    raw_data=card_data,
                )
            )

        return cards

    async def add_comment(
        self,
        card_id: int,
        comment: str,
    ) -> dict[str, Any]:
        """
        Add a comment to a card.

        Args:
            card_id: Card ID
            comment: Comment text

        Returns:
            Comment data
        """
        logger.info(f"Adding comment to card #{card_id}")

        payload = {"body": comment}
        response = await self.client.post(f"/api/cards/{card_id}/comments", json=payload)
        response.raise_for_status()

        data = response.json()
        logger.info(f"✅ Added comment to card #{card_id}")
        return data

    # -------------------------------------------------------------------------
    # Sync Operations (CCPM-style)
    # -------------------------------------------------------------------------

    async def sync_progress(self, card_id: int) -> bool:
        """
        Sync local progress to card comment.

        Only posts if there's new content (incremental sync).

        Args:
            card_id: Card ID

        Returns:
            True if sync was performed, False if no new content
        """
        progress = self._get_card_progress(card_id)

        if not self._has_new_content(card_id, progress):
            logger.info(f"No new updates to sync for card #{card_id}")
            return False

        comment = self._format_progress_comment(progress)
        await self.add_comment(card_id, comment)

        self._update_sync_marker(card_id)
        logger.info(f"✅ Synced progress to card #{card_id}")
        return True

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    def _column_to_status(self, column: Column) -> CardStatus:
        """Map column to status."""
        mapping = {
            Column.BACKLOG: CardStatus.TODO,
            Column.TODO: CardStatus.TODO,
            Column.DOING: CardStatus.IN_PROGRESS,
            Column.IN_REVIEW: CardStatus.IN_REVIEW,
            Column.DONE: CardStatus.DONE,
            Column.BLOCKED: CardStatus.BLOCKED,
        }
        return mapping.get(column, CardStatus.TODO)

    def _format_card_description(self, spec: CardSpec) -> str:
        """Format card description with CCPM-style structure."""
        sections = []
        sections.append(f"## 🎯 {spec.title}\n")
        sections.append("### 📋 Description")
        sections.append(f"{spec.description}\n")

        if spec.acceptance_criteria:
            sections.append("### ✅ Acceptance Criteria")
            for i, criterion in enumerate(spec.acceptance_criteria, 1):
                sections.append(f"{i}. {criterion}")
            sections.append("")

        if spec.epic_link or spec.spec_link or spec.related_cards:
            sections.append("### 🔗 Context")
            if spec.epic_link:
                sections.append(f"- **Epic**: {spec.epic_link}")
            if spec.spec_link:
                sections.append(f"- **Spec**: {spec.spec_link}")
            if spec.related_cards:
                sections.append(f"- **Related Cards**: {', '.join(map(str, spec.related_cards))}")
            sections.append("")

        sections.append(f"---\n*Created by BlackBox5 • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")

        return "\n".join(sections)

    def _format_progress_comment(self, progress: dict[str, Any]) -> str:
        """Format progress update comment (CCPM style)."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        sections = []
        sections.append(f"## 🔄 Progress Update - {timestamp}\n")

        if progress.get("completed"):
            sections.append("### ✅ Completed Work")
            for item in progress["completed"]:
                sections.append(f"- {item}")
            sections.append("")

        if progress.get("in_progress"):
            sections.append("### 🔄 In Progress")
            for item in progress["in_progress"]:
                sections.append(f"- {item}")
            sections.append("")

        if progress.get("notes"):
            sections.append("### 📝 Notes")
            for note in progress["notes"]:
                sections.append(f"- {note}")
            sections.append("")

        sections.append(f"---\n*Synced from BlackBox5 memory at {timestamp}*")
        return "\n".join(sections)

    def _store_card_context(self, card: CardData) -> None:
        """Store card context in local memory."""
        card_dir = self.memory_path / f"cards/{card.id}"
        card_dir.mkdir(parents=True, exist_ok=True)

        metadata = f"""---
id: {card.id}
title: {card.title}
status: {card.status.value}
column: {card.column.value}
created: {card.created_at or datetime.now(timezone.utc).isoformat()}
---

# {card.title}

{card.description}

## Status
**Current Status:** {card.status.value}
**Column:** {card.column.value}

---

*Created by BlackBox5 VibeKanbanManager*
"""

        (card_dir / "card.md").write_text(metadata)
        logger.info(f"Stored card context at {card_dir}")

    def _update_card_context(self, card: CardData) -> None:
        """Update card context in local memory."""
        card_file = self.memory_path / f"cards/{card.id}/card.md"

        if card_file.exists():
            content = card_file.read_text()

            # Update status section
            if "**Current Status:**" in content:
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "**Current Status:**" in line:
                        lines[i] = f"**Current Status:** {card.status.value}"
                    if "**Column:**" in line:
                        lines[i] = f"**Column:** {card.column.value}"

                content = "\n".join(lines)
                card_file.write_text(content)

    def _get_card_progress(self, card_id: int) -> dict[str, Any]:
        """Load card progress from local memory."""
        progress_file = self.memory_path / f"cards/{card_id}/progress.md"

        if not progress_file.exists():
            return {"completed": [], "in_progress": [], "notes": []}

        # Parse progress file
        content = progress_file.read_text()
        progress = {"completed": [], "in_progress": [], "notes": []}

        for line in content.split("\n"):
            if line.startswith("- [x] "):
                progress["completed"].append(line[6:])
            elif line.startswith("- [ ] "):
                progress["in_progress"].append(line[6:])
            elif line.startswith("- "):
                progress["notes"].append(line[2:])

        return progress

    def _has_new_content(self, card_id: int, progress: dict[str, Any]) -> bool:
        """Check if there's new content to sync."""
        sync_marker = self.memory_path / f"cards/{card_id}/.last_sync"

        if not sync_marker.exists():
            return True

        progress_file = self.memory_path / f"cards/{card_id}/progress.md"
        if not progress_file.exists():
            return False

        # Check if progress file modified after last sync
        try:
            last_sync = datetime.fromisoformat(sync_marker.read_text().strip())
            file_mtime = datetime.fromtimestamp(progress_file.stat().st_mtime, tz=timezone.utc)
            return file_mtime > last_sync
        except Exception:
            return True

    def _update_sync_marker(self, card_id: int) -> None:
        """Update sync marker for a card."""
        sync_marker = self.memory_path / f"cards/{card_id}/.last_sync"
        sync_marker.parent.mkdir(parents=True, exist_ok=True)
        sync_marker.write_text(datetime.now(timezone.utc).isoformat())

    def _parse_datetime(self, dt_str: str | None) -> datetime | None:
        """Parse datetime string."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception:
            return None


# =============================================================================
# Default Labels (CCPM-style)
# =============================================================================

DEFAULT_CARD_LABELS = [
    "priority:critical",
    "priority:high",
    "priority:medium",
    "priority:low",
    "type:feature",
    "type:bug",
    "type:refactor",
    "type:docs",
    "type:test",
    "type:chore",
]
