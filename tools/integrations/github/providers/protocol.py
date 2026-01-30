"""
Git Provider Protocol
=====================

Protocol definition for Git provider integrations (GitHub, GitLab, etc.).
Based on Auto-Claude's provider pattern.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ProviderType(Enum):
    """Supported Git providers."""

    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class PRState(Enum):
    """Pull request states."""

    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"
    DRAFT = "draft"


class IssueState(Enum):
    """Issue states."""

    OPEN = "open"
    CLOSED = "closed"


class ReviewEvent(Enum):
    """Review events."""

    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    COMMENT = "comment"


# -------------------------------------------------------------------------
# Data Classes
# -------------------------------------------------------------------------


@dataclass
class LabelData:
    """Label data."""

    name: str
    color: str = ""
    description: str = ""


@dataclass
class IssueData:
    """Issue data."""

    number: int
    title: str
    body: str
    author: str
    state: IssueState
    labels: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    url: str = ""
    assignees: list[str] = field(default_factory=list)
    milestone: str | None = None
    provider: ProviderType = ProviderType.GITHUB
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class IssueFilters:
    """Filters for fetching issues."""

    state: IssueState = IssueState.OPEN
    limit: int = 100
    author: str | None = None
    labels: list[str] = field(default_factory=list)
    include_prs: bool = False


@dataclass
class PRData:
    """Pull request data."""

    number: int
    title: str
    body: str
    author: str
    state: PRState
    source_branch: str
    target_branch: str
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    files: list[dict[str, Any]] = field(default_factory=list)
    diff: str = ""
    url: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    labels: list[str] = field(default_factory=list)
    reviewers: list[str] = field(default_factory=list)
    is_draft: bool = False
    mergeable: bool = True
    provider: ProviderType = ProviderType.GITHUB
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class PRFilters:
    """Filters for fetching PRs."""

    state: PRState = PRState.OPEN
    limit: int = 100
    author: str | None = None
    base_branch: str | None = None
    head_branch: str | None = None
    labels: list[str] = field(default_factory=list)


@dataclass
class ReviewData:
    """Review data."""

    body: str
    event: ReviewEvent = ReviewEvent.COMMENT
    comments: list[dict[str, Any]] = field(default_factory=list)


# -------------------------------------------------------------------------
# Protocol
# -------------------------------------------------------------------------


class GitProvider:
    """Protocol for Git provider integrations."""

    def __init__(self, repo: str):
        """Initialize provider with repository."""
        self.repo = repo

    @property
    def provider_type(self) -> ProviderType:
        """Get provider type."""
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Pull Request Operations
    # -------------------------------------------------------------------------

    async def fetch_pr(self, number: int) -> PRData:
        """Fetch a pull request by number."""
        raise NotImplementedError

    async def fetch_prs(self, filters: PRFilters | None = None) -> list[PRData]:
        """Fetch pull requests with optional filters."""
        raise NotImplementedError

    async def fetch_pr_diff(self, number: int) -> str:
        """Fetch the diff for a pull request."""
        raise NotImplementedError

    async def post_review(self, pr_number: int, review: ReviewData) -> int:
        """Post a review to a pull request."""
        raise NotImplementedError

    async def merge_pr(
        self,
        pr_number: int,
        merge_method: str = "merge",
        commit_title: str | None = None,
    ) -> bool:
        """Merge a pull request."""
        raise NotImplementedError

    async def close_pr(
        self,
        pr_number: int,
        comment: str | None = None,
    ) -> bool:
        """Close a pull request without merging."""
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Issue Operations
    # -------------------------------------------------------------------------

    async def fetch_issue(self, number: int) -> IssueData:
        """Fetch an issue by number."""
        raise NotImplementedError

    async def fetch_issues(
        self, filters: IssueFilters | None = None
    ) -> list[IssueData]:
        """Fetch issues with optional filters."""
        raise NotImplementedError

    async def create_issue(
        self,
        title: str,
        body: str,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> IssueData:
        """Create a new issue."""
        raise NotImplementedError

    async def close_issue(
        self,
        number: int,
        comment: str | None = None,
    ) -> bool:
        """Close an issue."""
        raise NotImplementedError

    async def add_comment(
        self,
        issue_or_pr_number: int,
        body: str,
    ) -> int:
        """Add a comment to an issue or PR."""
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Label Operations
    # -------------------------------------------------------------------------

    async def apply_labels(
        self,
        issue_or_pr_number: int,
        labels: list[str],
    ) -> None:
        """Apply labels to an issue or PR."""
        raise NotImplementedError

    async def remove_labels(
        self,
        issue_or_pr_number: int,
        labels: list[str],
    ) -> None:
        """Remove labels from an issue or PR."""
        raise NotImplementedError

    async def create_label(self, label: LabelData) -> None:
        """Create a label in the repository."""
        raise NotImplementedError

    async def list_labels(self) -> list[LabelData]:
        """List all labels in the repository."""
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Repository Operations
    # -------------------------------------------------------------------------

    async def get_repository_info(self) -> dict[str, Any]:
        """Get repository information."""
        raise NotImplementedError

    async def get_default_branch(self) -> str:
        """Get the default branch name."""
        raise NotImplementedError

    async def check_permissions(self, username: str) -> str:
        """Check a user's permission level on the repository."""
        raise NotImplementedError
