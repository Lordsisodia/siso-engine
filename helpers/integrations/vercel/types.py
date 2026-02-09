"""
Data types and enums for Vercel integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


# =============================================================================
# Enums
# =============================================================================


class DeploymentState(str, Enum):
    """Deployment states from Vercel API."""

    READY = "READY"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    ERROR = "ERROR"
    BUILDING = "BUILDING"
    DEPLOYING = "DEPLOYING"
    QUEUED = "QUEUED"


class ReadyState(str, Enum):
    """Ready state for deployments."""

    READY = "READY"
    ERROR = "ERROR"
    CANCELED = "CANCELED"
    FAILED = "FAILED"


class DeploymentTarget(str, Enum):
    """Deployment target environment."""

    PRODUCTION = "production"
    PREVIEW = "preview"


class EnvironmentType(str, Enum):
    """Environment types for environment variables."""

    PRODUCTION = "production"
    PREVIEW = "preview"
    DEVELOPMENT = "development"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class DeploymentStatus:
    """
    Status of a Vercel deployment.

    Attributes:
        id: Deployment ID
        status: Current deployment status
        url: Deployment URL
        ready_state: Ready state (READY, ERROR, etc.)
        created_at: Creation timestamp
        project_id: Project ID
        build_id: Build ID
        meta: Additional metadata
    """

    id: str
    status: str
    url: str
    ready_state: str
    created_at: datetime
    project_id: str = ""
    build_id: str = ""
    meta: dict[str, Any] | None = None

    @property
    def is_ready(self) -> bool:
        """Check if deployment is ready."""
        return self.ready_state == ReadyState.READY.value

    @property
    def is_failed(self) -> bool:
        """Check if deployment failed."""
        return self.ready_state in (
            ReadyState.FAILED.value,
            ReadyState.ERROR.value,
        )

    @property
    def is_building(self) -> bool:
        """Check if deployment is building."""
        return self.status in (
            DeploymentState.BUILDING.value,
            DeploymentState.QUEUED.value,
            DeploymentState.DEPLOYING.value,
        )


@dataclass
class DeploymentSpec:
    """
    Specification for creating a deployment.

    Attributes:
        project_name: Name of the Vercel project
        git_repo: Git repository URL
        ref: Git branch/tag/ref to deploy
        target: Production or preview environment
        metadata: Optional deployment metadata
    """

    project_name: str
    git_repo: str
    ref: str = "main"
    target: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class ProjectInfo:
    """
    Information about a Vercel project.

    Attributes:
        id: Project ID
        name: Project name
        framework: Framework detected
        link: Project URL
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: str
    name: str
    framework: str | None = None
    link: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class EnvironmentVariable:
    """
    Environment variable configuration.

    Attributes:
        id: Environment variable ID
        key: Variable name
        value: Variable value (not returned by API for security)
        type: Type (encrypted, plain, etc.)
        environment: Environments it applies to
        target: Targets it applies to
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: str
    key: str
    type: str
    environment: list[str]
    target: list[str]
    created_at: datetime | None = None
    updated_at: datetime | None = None
    value: str | None = None


@dataclass
class DeploymentResult:
    """
    Result of a deployment operation.

    Attributes:
        success: Whether deployment succeeded
        deployment_id: Deployment ID
        url: Deployment URL
        error: Error message if failed
    """

    success: bool
    deployment_id: str | None = None
    url: str | None = None
    error: str | None = None
