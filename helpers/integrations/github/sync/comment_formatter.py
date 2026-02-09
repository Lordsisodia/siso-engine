"""
CCPM-Style Comment Formatter
============================

Template-based comment formatting for progress updates and completion comments.
Provides flexible, customizable comment templates with variable substitution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CommentTemplate:
    """Comment template configuration."""

    name: str
    path: Path
    variables: dict[str, str]

    def render(self, **kwargs) -> str:
        """Render template with variables."""
        content = self.path.read_text()

        # Replace variables
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            content = content.replace(placeholder, str(value))

        return content


class FormatProgressComment:
    """
    Format progress update comments using templates.

    Supports both template-based and programmatic formatting.
    """

    def __init__(self, template_path: Path | None = None):
        """Initialize progress comment formatter.

        Args:
            template_path: Optional path to template file
        """
        self.template_path = template_path

    def format(
        self,
        completed: list[str] | None = None,
        in_progress: list[str] | None = None,
        technical_notes: list[str] | None = None,
        acceptance_criteria: dict[str, str] | None = None,
        commits: list[dict[str, str]] | None = None,
        next_steps: list[str] | None = None,
        blockers: list[str] | None = None,
        completion: int = 0,
    ) -> str:
        """Format progress comment.

        Args:
            completed: List of completed items
            in_progress: List of in-progress items
            technical_notes: List of technical notes
            acceptance_criteria: Dict of criteria to status
            commits: List of commit dicts with 'sha' and 'message'
            next_steps: List of next steps
            blockers: List of blockers
            completion: Completion percentage

        Returns:
            Formatted progress comment
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # Use template if available
        if self.template_path and self.template_path.exists():
            template = CommentTemplate(
                name="progress",
                path=self.template_path,
                variables={},
            )
            return template.render(
                timestamp=timestamp,
                completed_items=self._format_list(completed),
                in_progress_items=self._format_list(in_progress),
                technical_notes=self._format_list(technical_notes),
                criteria_status=self._format_criteria(acceptance_criteria),
                commits=self._format_commits(commits),
                next_steps=self._format_list(next_steps),
                blockers=self._format_list(blockers),
                completion=completion,
            )

        # Default programmatic formatting
        return self._format_default(
            timestamp=timestamp,
            completed=completed or [],
            in_progress=in_progress or [],
            technical_notes=technical_notes or [],
            acceptance_criteria=acceptance_criteria or {},
            commits=commits or [],
            next_steps=next_steps or [],
            blockers=blockers or [],
            completion=completion,
        )

    def _format_default(
        self,
        timestamp: str,
        completed: list[str],
        in_progress: list[str],
        technical_notes: list[str],
        acceptance_criteria: dict[str, str],
        commits: list[dict[str, str]],
        next_steps: list[str],
        blockers: list[str],
        completion: int,
    ) -> str:
        """Format progress comment with default structure."""
        sections = []
        sections.append(f"## 🔄 Progress Update - {timestamp}\n")

        # Completed Work
        if completed:
            sections.append("### ✅ Completed Work")
            for item in completed:
                sections.append(f"- {item}")
            sections.append("")

        # In Progress
        if in_progress:
            sections.append("### 🔄 In Progress")
            for item in in_progress:
                sections.append(f"- {item}")
            sections.append("")

        # Technical Notes
        if technical_notes:
            sections.append("### 📝 Technical Notes")
            for note in technical_notes:
                sections.append(f"- {note}")
            sections.append("")

        # Acceptance Criteria Status
        if acceptance_criteria:
            sections.append("### 📊 Acceptance Criteria Status")
            for criterion, status in acceptance_criteria.items():
                icon = (
                    "✅"
                    if status == "completed"
                    else "🔄" if status == "in-progress" else "□"
                )
                sections.append(f"- {icon} {criterion}")
            sections.append("")

        # Recent Commits
        if commits:
            sections.append("### 💻 Recent Commits")
            for commit in commits:
                msg = commit.get("message", "").split("\n")[0]  # First line only
                sections.append(f"- `{commit.get('sha', '')[:7]}` {msg}")
            sections.append("")

        # Next Steps
        if next_steps:
            sections.append("### 🚀 Next Steps")
            for step in next_steps:
                sections.append(f"- {step}")
            sections.append("")

        # Blockers
        if blockers:
            sections.append("### ⚠️ Blockers")
            for blocker in blockers:
                sections.append(f"- {blocker}")
            sections.append("")

        # Footer
        sections.append(
            f"---\n*Progress: {completion}% | "
            f"Synced from BlackBox5 memory at {timestamp}*"
        )

        return "\n".join(sections)

    def _format_list(self, items: list[str] | None) -> str:
        """Format list items."""
        if not items:
            return ""
        return "\n".join(f"- {item}" for item in items)

    def _format_criteria(self, criteria: dict[str, str] | None) -> str:
        """Format acceptance criteria."""
        if not criteria:
            return ""
        lines = []
        for criterion, status in criteria.items():
            icon = (
                "✅"
                if status == "completed"
                else "🔄" if status == "in-progress" else "□"
            )
            lines.append(f"- {icon} {criterion}")
        return "\n".join(lines)

    def _format_commits(self, commits: list[dict[str, str]] | None) -> str:
        """Format commit list."""
        if not commits:
            return ""
        lines = []
        for commit in commits:
            msg = commit.get("message", "").split("\n")[0]
            lines.append(f"- `{commit.get('sha', '')[:7]}` {msg}")
        return "\n".join(lines)


class FormatCompletionComment:
    """
    Format task completion comments using templates.

    Supports both template-based and programmatic formatting.
    """

    def __init__(self, template_path: Path | None = None):
        """Initialize completion comment formatter.

        Args:
            template_path: Optional path to template file
        """
        self.template_path = template_path

    def format(
        self,
        success: bool,
        deliverables: list[str] | None = None,
        patterns: list[str] | None = None,
        gotchas: list[str] | None = None,
        unit_test_status: str = "pending",
        integration_test_status: str = "pending",
        manual_test_status: str = "pending",
        documentation_status: str = "pending",
        duration: str | None = None,
    ) -> str:
        """Format completion comment.

        Args:
            success: Whether task was successful
            deliverables: List of deliverables
            patterns: List of patterns discovered
            gotchas: List of gotchas/pitfalls
            unit_test_status: Unit test status
            integration_test_status: Integration test status
            manual_test_status: Manual test status
            documentation_status: Documentation status
            duration: Optional duration string

        Returns:
            Formatted completion comment
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # Use template if available
        if self.template_path and self.template_path.exists():
            template = CommentTemplate(
                name="completion",
                path=self.template_path,
                variables={},
            )
            return template.render(
                timestamp=timestamp,
                criteria_met="All criteria verified and complete",
                deliverables=self._format_list(deliverables),
                unit_test_status=self._status_icon(unit_test_status),
                integration_test_status=self._status_icon(integration_test_status),
                manual_test_status=self._status_icon(manual_test_status),
                documentation_status=self._status_icon(documentation_status),
                patterns=self._format_list(patterns),
                gotchas=self._format_list(gotchas),
                duration=duration or "N/A",
            )

        # Default programmatic formatting
        return self._format_default(
            timestamp=timestamp,
            success=success,
            deliverables=deliverables or [],
            patterns=patterns or [],
            gotchas=gotchas or [],
            unit_test_status=unit_test_status,
            integration_test_status=integration_test_status,
            manual_test_status=manual_test_status,
            documentation_status=documentation_status,
            duration=duration,
        )

    def _format_default(
        self,
        timestamp: str,
        success: bool,
        deliverables: list[str],
        patterns: list[str],
        gotchas: list[str],
        unit_test_status: str,
        integration_test_status: str,
        manual_test_status: str,
        documentation_status: str,
        duration: str | None,
    ) -> str:
        """Format completion comment with default structure."""
        sections = []
        sections.append(f"## ✅ Task Completed - {timestamp}\n")

        # All Acceptance Criteria Met
        sections.append("### 🎯 All Acceptance Criteria Met")
        sections.append("- ✅ All criteria verified and complete\n")

        # Deliverables
        if deliverables:
            sections.append("### 📦 Deliverables")
            for deliverable in deliverables:
                sections.append(f"- {deliverable}")
            sections.append("")

        # Testing
        sections.append("### 🧪 Testing")
        sections.append(f"- Unit tests: {self._status_icon(unit_test_status)}")
        sections.append(
            f"- Integration tests: {self._status_icon(integration_test_status)}"
        )
        sections.append(f"- Manual testing: {self._status_icon(manual_test_status)}")
        sections.append("")

        # Documentation
        sections.append("### 📚 Documentation")
        sections.append(f"- Code documentation: {self._status_icon(documentation_status)}")
        sections.append("")

        # Key Learnings
        if patterns or gotchas:
            sections.append("### 💡 Key Learnings")

            if patterns:
                sections.append("**Patterns Discovered:**")
                for pattern in patterns:
                    sections.append(f"- {pattern}")
                sections.append("")

            if gotchas:
                sections.append("**Gotchas:**")
                for gotcha in gotchas:
                    sections.append(f"- {gotcha}")
                sections.append("")

        # Footer
        sections.append("This task is ready for review.")
        sections.append("")
        duration_str = duration or "N/A"
        sections.append(f"---\n*Task completed: 100% | Duration: {duration_str}*")

        return "\n".join(sections)

    def _format_list(self, items: list[str] | None) -> str:
        """Format list items."""
        if not items:
            return ""
        return "\n".join(f"- {item}" for item in items)

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


class FormatIssueBody:
    """
    Format GitHub issue bodies using templates.

    Supports both template-based and programmatic formatting.
    """

    def __init__(self, template_path: Path | None = None):
        """Initialize issue body formatter.

        Args:
            template_path: Optional path to template file
        """
        self.template_path = template_path

    def format(
        self,
        title: str,
        description: str,
        acceptance_criteria: list[str] | None = None,
        epic_link: str | None = None,
        spec_link: str | None = None,
        related_issues: list[str] | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> str:
        """Format issue body.

        Args:
            title: Issue title
            description: Issue description
            acceptance_criteria: List of acceptance criteria
            epic_link: Optional epic link
            spec_link: Optional spec link
            related_issues: Optional related issue links
            labels: Optional labels
            assignees: Optional assignees

        Returns:
            Formatted issue body
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # Use template if available
        if self.template_path and self.template_path.exists():
            template = CommentTemplate(
                name="issue",
                path=self.template_path,
                variables={},
            )
            return template.render(
                timestamp=timestamp,
                title=title,
                description=description,
                criteria_list=self._format_criteria(acceptance_criteria),
                epic_link=epic_link or "N/A",
                spec_link=spec_link or "N/A",
                related_issues=", ".join(related_issues) if related_issues else "None",
                labels=", ".join(labels) if labels else "None",
                assignees=", ".join(assignees) if assignees else "None",
            )

        # Default programmatic formatting
        return self._format_default(
            timestamp=timestamp,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria or [],
            epic_link=epic_link,
            spec_link=spec_link,
            related_issues=related_issues,
        )

    def _format_default(
        self,
        timestamp: str,
        title: str,
        description: str,
        acceptance_criteria: list[str],
        epic_link: str | None,
        spec_link: str | None,
        related_issues: list[str] | None,
    ) -> str:
        """Format issue body with default structure."""
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

        sections.append(
            f"---\n*Created by BlackBox5 • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*"
        )

        return "\n".join(sections)

    def _format_criteria(self, criteria: list[str] | None) -> str:
        """Format acceptance criteria."""
        if not criteria:
            return ""
        lines = []
        for i, criterion in enumerate(criteria, 1):
            lines.append(f"{i}. {criterion}")
        return "\n".join(lines)
