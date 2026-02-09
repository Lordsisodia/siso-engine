"""
Data types and enums for GitHub Actions integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


# =============================================================================
# Enums
# =============================================================================


class WorkflowRunStatus(str, Enum):
    """Workflow run statuses."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ACTION_REQUIRED = "action_required"
    WAITING = "waiting"
    PENDING = "pending"
    RUNNING = "running"


class WorkflowRunConclusion(str, Enum):
    """Workflow run conclusions."""

    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    SKIPPED = "skipped"
    STARTUP_FAILURE = "startup_failure"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class Workflow:
    """GitHub Actions workflow."""

    id: int
    name: str
    path: str
    state: str
    created_at: datetime
    updated_at: datetime
    url: str
    html_url: str
    badge_url: str | None = None
    workflow_dispatch: bool = False
    metadata: dict[str, Any] | None = None


@dataclass
class WorkflowRun:
    """GitHub Actions workflow run."""

    id: int
    name: str
    run_number: int
    status: WorkflowRunStatus
    conclusion: WorkflowRunConclusion | None
    head_branch: str
    head_sha: str
    created_at: datetime
    updated_at: datetime
    url: str
    html_url: str
    event: str
    actor: dict[str, Any]
    workflow_id: int
    run_started_at: datetime | None = None
    cancelled_at: datetime | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class Artifact:
    """GitHub Actions artifact."""

    id: int
    name: str
    size_in_bytes: int
    expired: bool
    created_at: datetime
    updated_at: datetime
    download_url: str
    archive_download_url: str
    workflow_run_id: int | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class WorkflowDispatchInput:
    """Specification for triggering workflow_dispatch."""

    ref: str
    inputs: dict[str, Any] | None = None


@dataclass
class LogDownload:
    """Specification for downloading workflow logs."""

    run_id: int
    output_path: str


@dataclass
class ArtifactDownload:
    """Specification for downloading artifact."""

    artifact_id: int
    output_path: str
    run_id: int | None = None
