"""
CCPM-Style Sync Logic
====================

Implements bidirectional sync between local memory and GitHub Issues.
Based on CCPM's proven sync patterns with incremental update detection.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..providers.protocol import IssueData, IssueState


@dataclass
class TaskProgress:
    """Task progress data."""

    completed: list[str] = field(default_factory=list)
    in_progress: list[str] = field(default_factory=list)
    technical_notes: list[str] = field(default_factory=list)
    acceptance_criteria: dict[str, str] = field(default_factory=dict)
    commits: list[dict[str, str]] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    completion: int = 0
    last_sync: datetime | None = None


@dataclass
class TaskOutcome:
    """Task completion outcome."""

    success: bool
    patterns: list[str] = field(default_factory=list)
    gotchas: list[str] = field(default_factory=list)
    deliverables: list[str] = field(default_factory=list)
    unit_test_status: str = "pending"
    integration_test_status: str = "pending"
    manual_test_status: str = "pending"
    documentation_status: str = "pending"


class CCPMSyncManager:
    """
    Manages bidirectional sync between local memory and GitHub Issues.

    Features:
    - Incremental update detection (prevents duplicate comments)
    - Structured progress comments
    - Frontmatter tracking for audit trail
    - Repository protection checks
    """

    def __init__(self, memory_path: Path, repo: str | None = None):
        """Initialize sync manager.

        Args:
            memory_path: Path to working memory directory
            repo: GitHub repo (e.g., "owner/repo"). Auto-detected if None.
        """
        self.memory_path = memory_path
        self.repo = repo or self._detect_repo()

    # -------------------------------------------------------------------------
    # Repository Detection & Protection
    # -------------------------------------------------------------------------

    def _detect_repo(self) -> str:
        """Detect GitHub repo from git remote."""
        try:
            remote_url = subprocess.check_output(
                ["git", "remote", "get-url", "origin"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()

            # Convert SSH to HTTPS format
            if remote_url.startswith("git@"):
                remote_url = remote_url.replace(":", "/").replace("git@", "https://")

            # Extract owner/repo
            repo = remote_url.split("github.com/")[-1].replace(".git", "")
            return repo
        except Exception:
            raise RuntimeError(
                "Could not detect GitHub repository. "
                "Ensure you're in a git repo with GitHub origin."
            )

    def check_repository_safe(self) -> bool:
        """
        Check if it's safe to write to the repository.

        Prevents writing to template repositories.

        Returns:
            True if safe, raises ValueError if not
        """
        blocked_repos = [
            "automazeio/ccpm",
            "Lordsisodia/blackbox4",
            "Lordsisodia/blackbox5",
            # Add other template repos as needed
        ]

        for blocked in blocked_repos:
            if blocked.lower() in self.repo.lower():
                raise ValueError(
                    f"❌ ERROR: Cannot write to template repository: {blocked}\n"
                    f"This repository is a template for others to use.\n"
                    f"Update your remote: git remote set-url origin <your-repo>"
                )

        return True

    # -------------------------------------------------------------------------
    # Sync Detection
    # -------------------------------------------------------------------------

    def has_new_content(self, task_id: int, progress: TaskProgress) -> bool:
        """
        Check if there's new content to sync since last sync.

        Args:
            task_id: GitHub issue number
            progress: Current task progress

        Returns:
            True if there's new content to sync
        """
        # Get last sync timestamp
        last_sync = self._get_last_sync(task_id)
        if last_sync is None:
            return True  # First sync, always has content

        # Check if progress has been updated since last sync
        progress_file = self.memory_path / f"tasks/{task_id}/progress.md"
        if not progress_file.exists():
            return False

        # Simple check: if file modified after last sync
        file_mtime = datetime.fromtimestamp(progress_file.stat().st_mtime, tz=timezone.utc)
        return file_mtime > last_sync

    def _get_last_sync(self, task_id: int) -> datetime | None:
        """Get last sync timestamp for a task."""
        sync_marker = self.memory_path / f"tasks/{task_id}/.last_sync"
        if not sync_marker.exists():
            return None

        try:
            timestamp_str = sync_marker.read_text().strip()
            return datetime.fromisoformat(timestamp_str)
        except Exception:
            return None

    def _update_sync_marker(self, task_id: int) -> None:
        """Update sync marker for a task."""
        sync_marker = self.memory_path / f"tasks/{task_id}/.last_sync"
        sync_marker.parent.mkdir(parents=True, exist_ok=True)
        sync_marker.write_text(datetime.now(timezone.utc).isoformat())

    # -------------------------------------------------------------------------
    # Comment Formatting
    # -------------------------------------------------------------------------

    def format_progress_comment(self, progress: TaskProgress) -> str:
        """Format progress update comment (CCPM style)."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        sections = []
        sections.append(f"## 🔄 Progress Update - {timestamp}\n")

        # Completed Work
        if progress.completed:
            sections.append("### ✅ Completed Work")
            for item in progress.completed:
                sections.append(f"- {item}")
            sections.append("")

        # In Progress
        if progress.in_progress:
            sections.append("### 🔄 In Progress")
            for item in progress.in_progress:
                sections.append(f"- {item}")
            sections.append("")

        # Technical Notes
        if progress.technical_notes:
            sections.append("### 📝 Technical Notes")
            for note in progress.technical_notes:
                sections.append(f"- {note}")
            sections.append("")

        # Acceptance Criteria Status
        if progress.acceptance_criteria:
            sections.append("### 📊 Acceptance Criteria Status")
            for criterion, status in progress.acceptance_criteria.items():
                icon = "✅" if status == "completed" else "🔄" if status == "in-progress" else "□"
                sections.append(f"- {icon} {criterion}")
            sections.append("")

        # Recent Commits
        if progress.commits:
            sections.append("### 💻 Recent Commits")
            for commit in progress.commits:
                msg = commit.get("message", "").split("\n")[0]  # First line only
                sections.append(f"- `{commit.get('sha', '')[:7]}` {msg}")
            sections.append("")

        # Next Steps
        if progress.next_steps:
            sections.append("### 🚀 Next Steps")
            for step in progress.next_steps:
                sections.append(f"- {step}")
            sections.append("")

        # Blockers
        if progress.blockers:
            sections.append("### ⚠️ Blockers")
            for blocker in progress.blockers:
                sections.append(f"- {blocker}")
            sections.append("")

        # Footer
        sections.append(
            f"---\n*Progress: {progress.completion}% | "
            f"Synced from BlackBox5 memory at {timestamp}*"
        )

        return "\n".join(sections)

    def format_completion_comment(self, outcome: TaskOutcome) -> str:
        """Format task completion comment (CCPM style)."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        sections = []
        sections.append(f"## ✅ Task Completed - {timestamp}\n")

        # All Acceptance Criteria Met
        sections.append("### 🎯 All Acceptance Criteria Met")
        sections.append("- ✅ All criteria verified and complete\n")

        # Deliverables
        if outcome.deliverables:
            sections.append("### 📦 Deliverables")
            for deliverable in outcome.deliverables:
                sections.append(f"- {deliverable}")
            sections.append("")

        # Testing
        sections.append("### 🧪 Testing")
        sections.append(f"- Unit tests: {self._status_icon(outcome.unit_test_status)}")
        sections.append(f"- Integration tests: {self._status_icon(outcome.integration_test_status)}")
        sections.append(f"- Manual testing: {self._status_icon(outcome.manual_test_status)}")
        sections.append("")

        # Documentation
        sections.append("### 📚 Documentation")
        sections.append(f"- Code documentation: {self._status_icon(outcome.documentation_status)}")
        sections.append("")

        # Key Learnings
        if outcome.patterns or outcome.gotchas:
            sections.append("### 💡 Key Learnings")

            if outcome.patterns:
                sections.append("**Patterns Discovered:**")
                for pattern in outcome.patterns:
                    sections.append(f"- {pattern}")
                sections.append("")

            if outcome.gotchas:
                sections.append("**Gotchas:**")
                for gotcha in outcome.gotchas:
                    sections.append(f"- {gotcha}")
                sections.append("")

        # Footer
        sections.append("This task is ready for review.")
        sections.append("")
        sections.append(f"---\n*Task completed: 100% | Synced from BlackBox5 at {timestamp}*")

        return "\n".join(sections)

    def _status_icon(self, status: str) -> str:
        """Get icon for status."""
        status_icons = {
            "passing": "✅ Passing",
            "passed": "✅ Passed",
            "complete": "✅ Complete",
            "completed": "✅ Completed",
            "pending": "⏸️ Pending",
            "failed": "❌ Failed",
            "skipped": "⊘ Skipped",
        }
        return status_icons.get(status.lower(), f"⏸️ {status}")

    # -------------------------------------------------------------------------
    # Issue Body Formatting
    # -------------------------------------------------------------------------

    def format_issue_body(
        self,
        title: str,
        description: str,
        acceptance_criteria: list[str] | None = None,
        epic_link: str | None = None,
        spec_link: str | None = None,
        related_issues: list[str] | None = None,
    ) -> str:
        """Format GitHub issue body."""
        sections = []
        sections.append(f"## 🎯 {title}\n")
        sections.append("### 📋 Description")
        sections.append(f"{description}\n")

        if acceptance_criteria:
            sections.append("### ✅ Acceptance Criteria")
            for i, criterion in enumerate(acceptance_criteria, 1):
                sections.append(f"{i}. {criterion}")
            sections.append("")

        if epic_link or spec_link or related_issues:
            sections.append("### 🔗 Context")
            if epic_link:
                sections.append(f"- **Epic**: {epic_link}")
            if spec_link:
                sections.append(f"- **Spec**: {spec_link}")
            if related_issues:
                sections.append(f"- **Related**: {', '.join(related_issues)}")
            sections.append("")

        sections.append(f"---\n*Created by BlackBox5 • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")

        return "\n".join(sections)

    # -------------------------------------------------------------------------
    # Local Memory Operations
    # -------------------------------------------------------------------------

    def get_task_progress(self, task_id: int) -> TaskProgress:
        """Load task progress from local memory."""
        progress_file = self.memory_path / f"tasks/{task_id}/progress.md"

        if not progress_file.exists():
            return TaskProgress()

        # Parse frontmatter and content
        content = progress_file.read_text()

        # Extract completion from frontmatter if present
        completion = 0
        if "---" in content:
            frontmatter_end = content.find("---", 3)  # Second ---
            frontmatter = content[:frontmatter_end]
            for line in frontmatter.split("\n"):
                if line.startswith("completion:"):
                    try:
                        completion = int(line.split(":")[1].strip().rstrip("%"))
                    except (ValueError, IndexError):
                        pass

        return TaskProgress(completion=completion)

    def update_task_progress(self, task_id: int, progress: TaskProgress) -> None:
        """Update task progress in local memory."""
        task_dir = self.memory_path / f"tasks/{task_id}"
        task_dir.mkdir(parents=True, exist_ok=True)

        progress_file = task_dir / "progress.md"

        # Write progress with frontmatter
        frontmatter = f"""---
issue: {task_id}
last_sync: {datetime.now(timezone.utc).isoformat()}
completion: {progress.completion}%
---

"""
        # Write progress sections
        sections = [frontmatter]

        if progress.completed:
            sections.append("## Completed Work\n")
            for item in progress.completed:
                sections.append(f"- [x] {item}")
            sections.append("")

        if progress.in_progress:
            sections.append("## In Progress\n")
            for item in progress.in_progress:
                sections.append(f"- [ ] {item}")
            sections.append("")

        if progress.technical_notes:
            sections.append("## Technical Notes\n")
            for note in progress.technical_notes:
                sections.append(f"- {note}")
            sections.append("")

        progress_file.write_text("\n".join(sections))

        # Update sync marker
        self._update_sync_marker(task_id)
