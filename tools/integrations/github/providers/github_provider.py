"""
GitHub Provider Implementation
==============================

Implements the GitProvider protocol for GitHub using the gh CLI.
Based on Auto-Claude's production-ready implementation.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .protocol import (
    GitProvider,
    IssueData,
    IssueFilters,
    IssueState,
    LabelData,
    PRData,
    PRFilters,
    PRState,
    ProviderType,
    ReviewData,
    ReviewEvent,
)


@dataclass
class GitHubProvider(GitProvider):
    """
    GitHub implementation of the GitProvider protocol.

    Uses the gh CLI for all operations.

    Usage:
        provider = GitHubProvider(repo="owner/repo")
        issue = await provider.create_issue("Title", "Body")
        await provider.add_comment(issue.number, "Comment")
    """

    enable_rate_limiting: bool = True
    project_dir: Path | None = None

    def __post_init__(self):
        """Validate gh CLI is available."""
        try:
            subprocess.run(
                ["gh", "--version"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError(
                "GitHub CLI (gh) not found. Install from https://cli.github.com/"
            ) from e

    @property
    def provider_type(self) -> ProviderType:
        """Get provider type."""
        return ProviderType.GITHUB

    # -------------------------------------------------------------------------
    # Pull Request Operations
    # -------------------------------------------------------------------------

    async def fetch_pr(self, number: int) -> PRData:
        """Fetch a pull request by number."""
        fields = [
            "number",
            "title",
            "body",
            "author",
            "state",
            "headRefName",
            "baseRefName",
            "additions",
            "deletions",
            "changedFiles",
            "files",
            "url",
            "createdAt",
            "updatedAt",
            "labels",
            "reviewRequests",
            "isDraft",
            "mergeable",
        ]

        pr_data = self._run_gh_json(
            ["pr", "view", str(number), "--json", ",".join(fields)]
        )
        diff = self._run_gh_text(["pr", "diff", str(number)])

        return self._parse_pr_data(pr_data, diff)

    async def fetch_prs(self, filters: PRFilters | None = None) -> list[PRData]:
        """Fetch pull requests with optional filters."""
        filters = filters or PRFilters()

        prs = self._run_gh_json(
            [
                "pr",
                "list",
                "--state",
                filters.state.value,
                "--limit",
                str(filters.limit),
                "--json",
                ",".join(
                    [
                        "number",
                        "title",
                        "author",
                        "state",
                        "headRefName",
                        "baseRefName",
                        "labels",
                        "url",
                        "createdAt",
                        "updatedAt",
                    ]
                ),
            ]
        )

        result = []
        for pr_data in prs:
            # Apply additional filters
            if (
                filters.author
                and pr_data.get("author", {}).get("login") != filters.author
            ):
                continue
            if (
                filters.base_branch
                and pr_data.get("baseRefName") != filters.base_branch
            ):
                continue
            if (
                filters.head_branch
                and pr_data.get("headRefName") != filters.head_branch
            ):
                continue
            if filters.labels:
                pr_labels = [label.get("name") for label in pr_data.get("labels", [])]
                if not all(label in pr_labels for label in filters.labels):
                    continue

            # Parse to PRData (lightweight, no diff)
            result.append(self._parse_pr_data(pr_data, ""))

        return result

    async def fetch_pr_diff(self, number: int) -> str:
        """Fetch the diff for a pull request."""
        return self._run_gh_text(["pr", "diff", str(number)])

    async def post_review(self, pr_number: int, review: ReviewData) -> int:
        """Post a review to a pull request."""
        event_map = {
            ReviewEvent.APPROVE: "approve",
            ReviewEvent.REQUEST_CHANGES: "request-changes",
            ReviewEvent.COMMENT: "comment",
        }

        self._run_gh_text(
            [
                "pr",
                "review",
                str(pr_number),
                "--body",
                review.body,
                "--event",
                event_map[review.event],
            ]
        )
        # gh CLI doesn't return comment ID
        return 0

    async def merge_pr(
        self,
        pr_number: int,
        merge_method: str = "merge",
        commit_title: str | None = None,
    ) -> bool:
        """Merge a pull request."""
        cmd = ["pr", "merge", str(pr_number)]

        if merge_method == "squash":
            cmd.append("--squash")
        elif merge_method == "rebase":
            cmd.append("--rebase")
        else:
            cmd.append("--merge")

        if commit_title:
            cmd.extend(["--subject", commit_title])

        cmd.append("--yes")

        try:
            self._run_gh_text(cmd)
            return True
        except Exception:
            return False

    async def close_pr(
        self,
        pr_number: int,
        comment: str | None = None,
    ) -> bool:
        """Close a pull request without merging."""
        try:
            if comment:
                await self.add_comment(pr_number, comment)
            self._run_gh_text(["pr", "close", str(pr_number)])
            return True
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Issue Operations
    # -------------------------------------------------------------------------

    async def fetch_issue(self, number: int) -> IssueData:
        """Fetch an issue by number."""
        fields = [
            "number",
            "title",
            "body",
            "author",
            "state",
            "labels",
            "createdAt",
            "updatedAt",
            "url",
            "assignees",
            "milestone",
        ]

        issue_data = self._run_gh_json(
            ["issue", "view", str(number), "--json", ",".join(fields)]
        )
        return self._parse_issue_data(issue_data)

    async def fetch_issues(
        self, filters: IssueFilters | None = None
    ) -> list[IssueData]:
        """Fetch issues with optional filters."""
        filters = filters or IssueFilters()

        issues = self._run_gh_json(
            [
                "issue",
                "list",
                "--state",
                filters.state.value,
                "--limit",
                str(filters.limit),
                "--json",
                ",".join(
                    [
                        "number",
                        "title",
                        "body",
                        "author",
                        "state",
                        "labels",
                        "createdAt",
                        "updatedAt",
                        "url",
                        "assignees",
                        "milestone",
                    ]
                ),
            ]
        )

        result = []
        for issue_data in issues:
            # Filter out PRs if requested
            if not filters.include_prs and "pullRequest" in issue_data:
                continue

            # Apply filters
            if (
                filters.author
                and issue_data.get("author", {}).get("login") != filters.author
            ):
                continue
            if filters.labels:
                issue_labels = [
                    label.get("name") for label in issue_data.get("labels", [])
                ]
                if not all(label in issue_labels for label in filters.labels):
                    continue

            result.append(self._parse_issue_data(issue_data))

        return result

    async def create_issue(
        self,
        title: str,
        body: str,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> IssueData:
        """Create a new issue."""
        cmd = ["issue", "create", "--title", title, "--body", body]

        if labels:
            for label in labels:
                cmd.extend(["--label", label])

        if assignees:
            for assignee in assignees:
                cmd.extend(["--assignee", assignee])

        # Add repo flag to ensure we create in the right repo
        cmd.extend(["--repo", self.repo])

        result = self._run_gh_text(cmd)

        # Parse the issue URL to get the number
        # gh issue create outputs the URL
        url = result.strip()
        number = int(url.split("/")[-1])

        return await self.fetch_issue(number)

    async def close_issue(
        self,
        number: int,
        comment: str | None = None,
    ) -> bool:
        """Close an issue."""
        try:
            if comment:
                await self.add_comment(number, comment)
            self._run_gh_text(["issue", "close", str(number)])
            return True
        except Exception:
            return False

    async def add_comment(
        self,
        issue_or_pr_number: int,
        body: str,
    ) -> int:
        """Add a comment to an issue or PR."""
        self._run_gh_text(["issue", "comment", str(issue_or_pr_number), "--body", body])
        # gh CLI doesn't return comment ID
        return 0

    # -------------------------------------------------------------------------
    # Label Operations
    # -------------------------------------------------------------------------

    async def apply_labels(
        self,
        issue_or_pr_number: int,
        labels: list[str],
    ) -> None:
        """Apply labels to an issue or PR."""
        self._run_gh_text(["issue", "edit", str(issue_or_pr_number), "--add-label", ",".join(labels)])

    async def remove_labels(
        self,
        issue_or_pr_number: int,
        labels: list[str],
    ) -> None:
        """Remove labels from an issue or PR."""
        self._run_gh_text(["issue", "edit", str(issue_or_pr_number), "--remove-label", ",".join(labels)])

    async def create_label(self, label: LabelData) -> None:
        """Create a label in the repository."""
        cmd = ["label", "create", label.name, "--color", label.color]
        if label.description:
            cmd.extend(["--description", label.description])
        cmd.append("--force")  # Update if exists

        self._run_gh_text(cmd)

    async def list_labels(self) -> list[LabelData]:
        """List all labels in the repository."""
        result = self._run_gh_json(
            ["label", "list", "--json", "name,color,description"]
        )

        return [
            LabelData(
                name=label["name"],
                color=label.get("color", ""),
                description=label.get("description", ""),
            )
            for label in result
        ]

    # -------------------------------------------------------------------------
    # Sub-Issue & Hierarchy Operations
    # -------------------------------------------------------------------------

    async def create_sub_issue(
        self,
        parent_issue_number: int,
        title: str,
        body: str,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> IssueData:
        """
        Create a sub-issue linked to a parent issue.

        Args:
            parent_issue_number: Parent issue number
            title: Sub-issue title
            body: Sub-issue body
            labels: Optional labels
            assignees: Optional assignees

        Returns:
            Created sub-issue data
        """
        # Add parent reference to body
        parent_ref = f"\n\n**Parent Issue**: #{parent_issue_number}"
        body = body + parent_ref

        # Create the issue
        issue = await self.create_issue(title, body, labels, assignees)

        # Add comment to parent issue linking to sub-issue
        comment = f"🔗 **Sub-issue created**: #{issue.number} - {title}"
        await self.add_comment(parent_issue_number, comment)

        return issue

    async def link_epic(
        self,
        issue_number: int,
        epic_number: int,
        epic_title: str | None = None,
    ) -> None:
        """
        Link an issue to an epic issue.

        Args:
            issue_number: Issue number to link
            epic_number: Epic issue number
            epic_title: Optional epic title for reference
        """
        epic_link = f"#{epic_number}"
        if epic_title:
            epic_link = f"{epic_link} - {epic_title}"

        # Add epic link to issue body
        issue = await self.fetch_issue(issue_number)
        epic_section = "\n\n**Epic**: " + epic_link

        if "**Epic**" not in issue.body:
            # Add epic section
            new_body = issue.body + epic_section
            await self._update_issue_body(issue_number, new_body)
        else:
            # Add comment instead
            comment = f"🔗 **Linked to Epic**: {epic_link}"
            await self.add_comment(issue_number, comment)

        # Add comment to epic linking back to issue
        comment = f"🔗 **Sub-issue**: #{issue_number} - {issue.title}"
        await self.add_comment(epic_number, comment)

    async def bulk_create_issues(
        self,
        issues: list[dict[str, Any]],
    ) -> list[IssueData]:
        """
        Create multiple issues in bulk.

        Args:
            issues: List of issue dicts with keys:
                - title (str): Issue title
                - body (str): Issue body
                - labels (list[str], optional): Labels
                - assignees (list[str], optional): Assignees

        Returns:
            List of created issue data
        """
        created_issues = []

        for issue_spec in issues:
            try:
                issue = await self.create_issue(
                    title=issue_spec.get("title", "Untitled"),
                    body=issue_spec.get("body", ""),
                    labels=issue_spec.get("labels"),
                    assignees=issue_spec.get("assignees"),
                )
                created_issues.append(issue)
            except Exception as e:
                # Log error but continue with other issues
                print(f"Failed to create issue '{issue_spec.get('title')}': {e}")

        return created_issues

    async def create_epic_with_subtasks(
        self,
        epic_title: str,
        epic_description: str,
        subtasks: list[dict[str, Any]],
        epic_labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create an epic issue with multiple sub-issues.

        Args:
            epic_title: Epic issue title
            epic_description: Epic description
            subtasks: List of subtask dicts with keys:
                - title (str): Subtask title
                - body (str): Subtask body
                - labels (list[str], optional): Subtask labels
                - assignees (list[str], optional): Subtask assignees
            epic_labels: Optional labels for epic issue

        Returns:
            Dict with epic_issue and sub_issues
        """
        # Create epic issue
        epic_body = epic_description + "\n\n## Sub-issues\n"
        epic_issue = await self.create_issue(
            title=epic_title,
            body=epic_body,
            labels=epic_labels,
        )

        # Create sub-issues
        sub_issues = []
        for i, subtask in enumerate(subtasks, 1):
            # Add subtask reference to epic body
            sub_issue = await self.create_sub_issue(
                parent_issue_number=epic_issue.number,
                title=subtask.get("title", f"Subtask {i}"),
                body=subtask.get("body", ""),
                labels=subtask.get("labels"),
                assignees=subtask.get("assignees"),
            )
            sub_issues.append(sub_issue)

        # Update epic body with sub-issue links
        epic_body = epic_description + "\n\n## Sub-issues\n"
        for sub_issue in sub_issues:
            epic_body += f"- #{sub_issue.number} - {sub_issue.title}\n"
        await self._update_issue_body(epic_issue.number, epic_body)

        return {
            "epic_issue": epic_issue,
            "sub_issues": sub_issues,
        }

    async def _update_issue_body(self, issue_number: int, new_body: str) -> None:
        """
        Update an issue's body.

        Args:
            issue_number: Issue number
            new_body: New issue body
        """
        # gh issue edit doesn't support --body directly, so we use API
        import json

        # Get current issue data
        issue = await self.fetch_issue(issue_number)

        # Build update command
        cmd = [
            "api",
            "repos/{repo}/issues/{issue_number}".format(
                repo=self.repo,
                issue_number=issue_number,
            ),
            "--method",
            "PATCH",
            "-f",
            f"body={new_body}",
        ]

        try:
            self._run_gh_text(cmd)
        except Exception as e:
            # Fallback: add comment with updated body
            comment = f"📝 **Updated Body**:\n\n{new_body}"
            await self.add_comment(issue_number, comment)

    # -------------------------------------------------------------------------
    # Repository Operations
    # -------------------------------------------------------------------------

    async def get_repository_info(self) -> dict[str, Any]:
        """Get repository information."""
        return self._run_gh_json(["repo", "view", "--json", "name,owner,defaultBranchRef"])

    async def get_default_branch(self) -> str:
        """Get the default branch name."""
        repo_info = await self.get_repository_info()
        return (
            repo_info.get("defaultBranchRef", {})
            .get("name", "main")
        )

    async def check_permissions(self, username: str) -> str:
        """Check a user's permission level on the repository."""
        try:
            result = self._run_gh_text(
                ["repo", "view", "--json", "viewerPermission"],
                stderr=subprocess.DEVNULL,
            )
            data = json.loads(result)
            return data.get("viewerPermission", "none")
        except Exception:
            return "none"

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _run_gh_json(self, cmd: list[str]) -> Any:
        """Run gh CLI command and parse JSON output."""
        cmd = ["gh", "--repo", self.repo] + cmd
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def _run_gh_text(
        self,
        cmd: list[str],
        stderr: int = subprocess.PIPE,
    ) -> str:
        """Run gh CLI command and get text output."""
        cmd = ["gh", "--repo", self.repo] + cmd
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            stderr=stderr,
        )
        return result.stdout.strip()

    def _parse_pr_data(self, data: dict[str, Any], diff: str) -> PRData:
        """Parse GitHub PR data into PRData."""
        author = data.get("author", {})
        if isinstance(author, dict):
            author_login = author.get("login", "unknown")
        else:
            author_login = str(author) if author else "unknown"

        labels = []
        for label in data.get("labels", []):
            if isinstance(label, dict):
                labels.append(label.get("name", ""))
            else:
                labels.append(str(label))

        files = data.get("files", [])
        if files is None:
            files = []

        return PRData(
            number=data.get("number", 0),
            title=data.get("title", ""),
            body=data.get("body", "") or "",
            author=author_login,
            state=PRState(data.get("state", "open")),
            source_branch=data.get("headRefName", ""),
            target_branch=data.get("baseRefName", ""),
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0),
            changed_files=data.get("changedFiles", len(files)),
            files=files,
            diff=diff,
            url=data.get("url", ""),
            created_at=self._parse_datetime(data.get("createdAt")),
            updated_at=self._parse_datetime(data.get("updatedAt")),
            labels=labels,
            reviewers=self._parse_reviewers(data.get("reviewRequests", [])),
            is_draft=data.get("isDraft", False),
            mergeable=data.get("mergeable") != "CONFLICTING",
            provider=ProviderType.GITHUB,
            raw_data=data,
        )

    def _parse_issue_data(self, data: dict[str, Any]) -> IssueData:
        """Parse GitHub issue data into IssueData."""
        author = data.get("author", {})
        if isinstance(author, dict):
            author_login = author.get("login", "unknown")
        else:
            author_login = str(author) if author else "unknown"

        labels = []
        for label in data.get("labels", []):
            if isinstance(label, dict):
                labels.append(label.get("name", ""))
            else:
                labels.append(str(label))

        assignees = []
        for assignee in data.get("assignees", []):
            if isinstance(assignee, dict):
                assignees.append(assignee.get("login", ""))
            else:
                assignees.append(str(assignee))

        milestone = data.get("milestone")
        if isinstance(milestone, dict):
            milestone = milestone.get("title")

        return IssueData(
            number=data.get("number", 0),
            title=data.get("title", ""),
            body=data.get("body", "") or "",
            author=author_login,
            state=IssueState(data.get("state", "open")),
            labels=labels,
            created_at=self._parse_datetime(data.get("createdAt")),
            updated_at=self._parse_datetime(data.get("updatedAt")),
            url=data.get("url", ""),
            assignees=assignees,
            milestone=milestone,
            provider=ProviderType.GITHUB,
            raw_data=data,
        )

    def _parse_datetime(self, dt_str: str | None) -> datetime | None:
        """Parse ISO datetime string."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    def _parse_reviewers(self, review_requests: list | None) -> list[str]:
        """Parse review requests into list of usernames."""
        if not review_requests:
            return []
        reviewers = []
        for req in review_requests:
            if isinstance(req, dict):
                if "requestedReviewer" in req:
                    reviewer = req["requestedReviewer"]
                    if isinstance(reviewer, dict):
                        reviewers.append(reviewer.get("login", ""))
        return reviewers
