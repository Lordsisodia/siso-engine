"""
Obsidian Exporter - Main manager class for exporting notes to Obsidian.
"""

from __future__ import annotations

import frontmatter
from datetime import datetime
from pathlib import Path
from typing import Any

from .types import (
    ContextData,
    ExportResult,
    InsightData,
    NoteStatus,
    NoteType,
    PlanData,
    SessionData,
    Wikilink,
)


class ObsidianExporter:
    """
    Export BlackBox5 data to Obsidian vault.

    This exporter writes Markdown files with YAML frontmatter directly
    to the file system in your Obsidian vault.

    Example:
        >>> exporter = ObsidianExporter(vault_path="~/Documents/ObsidianVault")
        >>> result = exporter.export_session(session_data)
        >>> print(result.file_path)
    """

    # Default folder structure within the vault
    DEFAULT_FOLDER = "blackbox5"
    SUBFOLDERS = {
        NoteType.SESSION: "sessions",
        NoteType.INSIGHT: "insights",
        NoteType.CONTEXT: "context",
        NoteType.PLAN: "plans",
    }

    def __init__(
        self,
        vault_path: str | Path,
        base_folder: str = DEFAULT_FOLDER,
        create_folders: bool = True,
    ):
        """
        Initialize the Obsidian exporter.

        Args:
            vault_path: Path to Obsidian vault root
            base_folder: Base folder within vault for BlackBox5 notes
            create_folders: Whether to create folder structure if it doesn't exist
        """
        self.vault_path = Path(vault_path).expanduser().resolve()
        self.base_folder = base_folder
        self.create_folders = create_folders

        if create_folders:
            self._ensure_folder_structure()

    def _ensure_folder_structure(self) -> None:
        """Create the folder structure if it doesn't exist."""
        base = self.vault_path / self.base_folder
        base.mkdir(parents=True, exist_ok=True)

        for subfolder in self.SUBFOLDERS.values():
            (base / subfolder).mkdir(parents=True, exist_ok=True)

    def _get_folder_path(self, note_type: NoteType) -> Path:
        """Get the full path for a note type folder."""
        return self.vault_path / self.base_folder / self.SUBFOLDERS[note_type]

    def _generate_frontmatter(self, data: dict[str, Any]) -> frontmatter.Post:
        """
        Generate YAML frontmatter from data dictionary.

        Args:
            data: Dictionary of metadata

        Returns:
            frontmatter.Post object with metadata
        """
        # Filter out None values and convert datetime objects
        clean_data = {}
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, datetime):
                clean_data[key] = value.isoformat()
            elif isinstance(value, list):
                # Clean list items
                clean_list = [
                    v.isoformat() if isinstance(v, datetime) else v
                    for v in value
                    if v is not None
                ]
                if clean_list:
                    clean_data[key] = clean_list
            else:
                clean_data[key] = value

        return frontmatter.Post(content="", **clean_data)

    def _generate_wikilinks(self, links: list[str | Wikilink]) -> str:
        """
        Generate wikilinks section from list of links.

        Args:
            links: List of link titles or Wikilink objects

        Returns:
            Markdown string with wikilinks section
        """
        if not links:
            return ""

        markdown_links = []
        for link in links:
            if isinstance(link, Wikilink):
                markdown_links.append(link.to_markdown())
            elif isinstance(link, str):
                markdown_links.append(f"[[{link}]]")

        if not markdown_links:
            return ""

        return "\n## Related Notes\n\n" + "\n".join(f"- {link}" for link in markdown_links)

    def _generate_filename(
        self,
        note_type: NoteType,
        title: str,
        date: datetime | None = None,
    ) -> str:
        """
        Generate a filename for a note.

        Format: {type}-{YYYY-MM-DD}-{sanitized_title}.md

        Args:
            note_type: Type of note
            title: Note title or topic
            date: Date for filename (defaults to today)

        Returns:
            Filename string
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")
        # Sanitize title: replace spaces with hyphens, remove special chars
        safe_title = title.lower()[:50]  # Limit length
        safe_title = "".join(c if c.isalnum() or c in "-_" else "-" for c in safe_title)
        safe_title = safe_title.strip("-")

        return f"{note_type.value}-{date_str}-{safe_title}.md"

    def export_session(self, session_data: SessionData) -> ExportResult:
        """
        Export an agent session to Obsidian.

        Args:
            session_data: Session data to export

        Returns:
            ExportResult with file path and status
        """
        try:
            # Generate filename
            title = session_data.goal or session_data.session_id
            filename = self._generate_filename(
                NoteType.SESSION,
                title,
                session_data.start_time,
            )

            # Build frontmatter metadata
            metadata = {
                "type": NoteType.SESSION.value,
                "agent_id": session_data.agent_id,
                "agent_name": session_data.agent_name,
                "session_id": session_data.session_id,
                "start_time": session_data.start_time,
                "end_time": session_data.end_time,
                "created": datetime.now().isoformat(),
                "tags": session_data.tags + ["session", "agent"],
                "status": NoteStatus.ACTIVE.value if not session_data.end_time else "completed",
                **session_data.metadata,
            }

            post = self._generate_frontmatter(metadata)

            # Build content
            content_parts = []

            if session_data.goal:
                content_parts.append(f"# Goal\n\n{session_data.goal}\n")

            if session_data.outcome:
                content_parts.append(f"# Outcome\n\n{session_data.outcome}\n")

            if session_data.steps:
                content_parts.append("# Steps\n\n")
                for i, step in enumerate(session_data.steps, 1):
                    step_text = step.get("text", str(step))
                    content_parts.append(f"## Step {i}\n\n{step_text}\n")

            # Add wikilinks
            if session_data.related_notes:
                content_parts.append(self._generate_wikilinks(session_data.related_notes))

            # Combine content
            post.content = "\n".join(content_parts)

            # Write to file
            folder_path = self._get_folder_path(NoteType.SESSION)
            file_path = folder_path / filename

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(post))

            return ExportResult(
                success=True,
                file_path=str(file_path),
                note_type=NoteType.SESSION,
                message=f"Session exported successfully to {filename}",
            )

        except Exception as e:
            return ExportResult(
                success=False,
                note_type=NoteType.SESSION,
                error=str(e),
            )

    def export_insight(self, insight_data: InsightData) -> ExportResult:
        """
        Export an insight to Obsidian.

        Args:
            insight_data: Insight data to export

        Returns:
            ExportResult with file path and status
        """
        try:
            # Generate filename
            filename = self._generate_filename(
                NoteType.INSIGHT,
                insight_data.title,
                insight_data.created_at,
            )

            # Build frontmatter metadata
            metadata = {
                "type": NoteType.INSIGHT.value,
                "title": insight_data.title,
                "category": insight_data.category,
                "source_session": insight_data.source_session,
                "created_at": insight_data.created_at,
                "created": datetime.now().isoformat(),
                "tags": insight_data.tags + ["insight", "knowledge"],
                **insight_data.metadata,
            }

            post = self._generate_frontmatter(metadata)

            # Build content
            content_parts = [f"# {insight_data.title}\n\n", insight_data.content]

            # Add wikilinks
            if insight_data.related_notes:
                content_parts.append(self._generate_wikilinks(insight_data.related_notes))

            post.content = "\n".join(content_parts)

            # Write to file
            folder_path = self._get_folder_path(NoteType.INSIGHT)
            file_path = folder_path / filename

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(post))

            return ExportResult(
                success=True,
                file_path=str(file_path),
                note_type=NoteType.INSIGHT,
                message=f"Insight exported successfully to {filename}",
            )

        except Exception as e:
            return ExportResult(
                success=False,
                note_type=NoteType.INSIGHT,
                error=str(e),
            )

    def export_context(self, context_data: ContextData) -> ExportResult:
        """
        Export agent context to Obsidian.

        Args:
            context_data: Context data to export

        Returns:
            ExportResult with file path and status
        """
        try:
            # Generate filename
            title = f"{context_data.agent_name}-{context_data.context_type}"
            filename = self._generate_filename(
                NoteType.CONTEXT,
                title,
                context_data.created_at,
            )

            # Build frontmatter metadata
            metadata = {
                "type": NoteType.CONTEXT.value,
                "agent_id": context_data.agent_id,
                "agent_name": context_data.agent_name,
                "context_type": context_data.context_type,
                "created_at": context_data.created_at,
                "created": datetime.now().isoformat(),
                "tags": context_data.tags + ["context", "agent"],
                **context_data.metadata,
            }

            post = self._generate_frontmatter(metadata)

            # Build content
            content_parts = [
                f"# Context: {context_data.agent_name}\n",
                f"**Type**: {context_data.context_type}\n",
                f"**Agent ID**: {context_data.agent_id}\n",
                f"\n---\n\n",
                context_data.content,
            ]

            # Add wikilinks
            if context_data.related_notes:
                content_parts.append(self._generate_wikilinks(context_data.related_notes))

            post.content = "\n".join(content_parts)

            # Write to file
            folder_path = self._get_folder_path(NoteType.CONTEXT)
            file_path = folder_path / filename

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(post))

            return ExportResult(
                success=True,
                file_path=str(file_path),
                note_type=NoteType.CONTEXT,
                message=f"Context exported successfully to {filename}",
            )

        except Exception as e:
            return ExportResult(
                success=False,
                note_type=NoteType.CONTEXT,
                error=str(e),
            )

    def export_plan(self, plan_data: PlanData) -> ExportResult:
        """
        Export a plan to Obsidian.

        Args:
            plan_data: Plan data to export

        Returns:
            ExportResult with file path and status
        """
        try:
            # Generate filename
            filename = self._generate_filename(
                NoteType.PLAN,
                plan_data.title,
                plan_data.created_at,
            )

            # Build frontmatter metadata
            metadata = {
                "type": NoteType.PLAN.value,
                "title": plan_data.title,
                "description": plan_data.description,
                "status": plan_data.status,
                "created_at": plan_data.created_at,
                "updated_at": plan_data.updated_at or datetime.now(),
                "created": datetime.now().isoformat(),
                "tags": plan_data.tags + ["plan", "task"],
                **plan_data.metadata,
            }

            post = self._generate_frontmatter(metadata)

            # Build content
            content_parts = [f"# {plan_data.title}\n\n"]

            if plan_data.description:
                content_parts.append(f"**Description**: {plan_data.description}\n")

            content_parts.append(f"**Status**: {plan_data.status}\n")

            if plan_data.steps:
                content_parts.append("\n## Steps\n\n")
                for i, step in enumerate(plan_data.steps, 1):
                    step_title = step.get("title", f"Step {i}")
                    step_desc = step.get("description", "")
                    step_status = step.get("status", "pending")

                    content_parts.append(
                        f"### {i}. {step_title}\n"
                        f"**Status**: {step_status}\n\n"
                        f"{step_desc}\n"
                    )

            # Add wikilinks
            if plan_data.related_notes:
                content_parts.append(self._generate_wikilinks(plan_data.related_notes))

            post.content = "\n".join(content_parts)

            # Write to file
            folder_path = self._get_folder_path(NoteType.PLAN)
            file_path = folder_path / filename

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(post))

            return ExportResult(
                success=True,
                file_path=str(file_path),
                note_type=NoteType.PLAN,
                message=f"Plan exported successfully to {filename}",
            )

        except Exception as e:
            return ExportResult(
                success=False,
                note_type=NoteType.PLAN,
                error=str(e),
            )

    def generate_index(self) -> ExportResult:
        """
        Generate an index note listing all exported notes.

        Creates a main index file with links to all exported notes
        organized by type.

        Returns:
            ExportResult with index file path
        """
        try:
            base_path = self.vault_path / self.base_folder
            content_parts = ["# BlackBox5 Notes Index\n\n"]

            for note_type, subfolder in self.SUBFOLDERS.items():
                folder_path = base_path / subfolder
                if not folder_path.exists():
                    continue

                # Get all markdown files in the folder
                md_files = sorted(folder_path.glob("*.md"))

                if md_files:
                    content_parts.append(f"## {note_type.title()}s\n\n")

                    for md_file in md_files:
                        # Parse frontmatter to get title
                        with open(md_file, "r", encoding="utf-8") as f:
                            post = frontmatter.load(f)

                        # Use title from frontmatter or filename
                        title = post.get("title", md_file.stem)
                        rel_path = md_file.relative_to(base_path)

                        # Create wikilink path (relative to base_folder)
                        wikilink_path = str(rel_path.parent / rel_path.stem)

                        content_parts.append(f"- [[{wikilink_path}|{title}]]\n")

                    content_parts.append("\n")

            # Add metadata
            index_metadata = {
                "type": "index",
                "created": datetime.now().isoformat(),
                "tags": ["index", "blackbox5"],
            }

            post = frontmatter.Post(content="".join(content_parts), **index_metadata)

            # Write index file
            index_path = base_path / "_index.md"
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(post))

            return ExportResult(
                success=True,
                file_path=str(index_path),
                message="Index generated successfully",
            )

        except Exception as e:
            return ExportResult(
                success=False,
                error=str(e),
            )
