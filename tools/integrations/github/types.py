"""
GitHub Integration Type Definitions

This module contains all data types used by the GitHub integration.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class GitHubIssue:
    """Represents a GitHub issue."""
    number: int
    title: str
    body: str
    state: str
    html_url: str
    labels: List[str]
    created_at: str
    updated_at: str
    assignees: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GitHubPR:
    """Represents a GitHub pull request."""
    number: int
    title: str
    body: str
    state: str
    html_url: str
    head_ref: str
    base_ref: str
    created_at: str
    updated_at: str
    labels: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GitHubComment:
    """Represents a GitHub comment."""
    id: int
    body: str
    user: str
    created_at: str
    updated_at: str
    html_url: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GitHubRepository:
    """Represents a GitHub repository."""
    name: str
    full_name: str
    owner: str
    description: Optional[str]
    private: bool
    html_url: str
    clone_url: str
    default_branch: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GitHubLabel:
    """Represents a GitHub label."""
    name: str
    color: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GitHubUser:
    """Represents a GitHub user."""
    login: str
    id: int
    html_url: str
    type: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GitHubError:
    """Represents a GitHub API error."""
    message: str
    documentation_url: Optional[str] = None
    status_code: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GitHubRateLimit:
    """Represents GitHub API rate limit info."""
    limit: int
    remaining: int
    reset: int
    reset_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


__all__ = [
    'GitHubIssue',
    'GitHubPR',
    'GitHubComment',
    'GitHubRepository',
    'GitHubLabel',
    'GitHubUser',
    'GitHubError',
    'GitHubRateLimit',
]
