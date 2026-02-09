"""
Vercel Manager for BlackBox5
============================

Main integration class for Vercel deployment service.

Features:
- Create and manage deployments
- Monitor deployment status
- Retrieve deployment logs
- Manage environment variables
- List and manage projects

Usage:
    >>> manager = VercelManager(token="your_token")
    >>> deployment = await manager.create_deployment(...)
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import httpx

from .types import DeploymentSpec, DeploymentStatus

logger = logging.getLogger(__name__)


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


# =============================================================================
# Main Manager Class
# =============================================================================


class VercelManager:
    """
    Main manager class for Vercel integration.

    Authentication:
        Uses API token from environment variable or parameter.
        Get your token at: https://vercel.com/account/tokens

    Rate Limits:
        - 100 deployments per day
        - Monitor X-RateLimit-* headers for quota

    Team Support:
        If using team accounts, set VERCEL_TEAM_ID environment variable
        or pass team_id parameter.

    Example:
        >>> manager = VercelManager(token="your_token")
        >>> deployment = await manager.create_deployment(
        ...     project_name="my-app",
        ...     git_repo="https://github.com/user/repo",
        ...     ref="main"
        ... )
        >>> await manager.wait_for_deployment(deployment.id)
    """

    API_BASE = "https://api.vercel.com"
    API_VERSION = "v13"

    def __init__(
        self,
        token: Optional[str] = None,
        team_id: Optional[str] = None,
        base_url: str = "https://api.vercel.com",
        timeout: int = 30,
    ):
        """
        Initialize Vercel manager.

        Args:
            token: API token (default: from VERCEL_TOKEN env var)
            team_id: Team ID for team deployments (from VERCEL_TEAM_ID env var)
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        self.token = token or os.environ.get("VERCEL_TOKEN")
        if not self.token:
            raise ValueError(
                "API token required. Set VERCEL_TOKEN "
                "environment variable or pass token parameter. "
                "Get your token at: https://vercel.com/account/tokens"
            )

        self.team_id = team_id or os.environ.get("VERCEL_TEAM_ID")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Initialize HTTP client
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "BlackBox5/1.0",
        }

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
        )

        logger.info(f"Initialized VercelManager for {self.base_url}")
        if self.team_id:
            logger.info(f"Using team ID: {self.team_id}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
        logger.debug("Closed HTTP client")

    def _get_team_param(self) -> dict[str, str]:
        """Get team_id query parameter if applicable."""
        if self.team_id:
            return {"teamId": self.team_id}
        return {}

    def _log_rate_limit(self, response: httpx.Response):
        """Log rate limit information from response headers."""
        remaining = response.headers.get("X-RateLimit-Remaining")
        limit = response.headers.get("X-RateLimit-Limit")
        reset = response.headers.get("X-RateLimit-Reset")

        if remaining or limit:
            logger.debug(f"Rate Limit: {remaining}/{limit} requests remaining")
            if reset:
                reset_time = datetime.fromtimestamp(int(reset), tz=timezone.utc)
                logger.debug(f"Rate limit resets at: {reset_time}")

    # -------------------------------------------------------------------------
    # Deployment Operations
    # -------------------------------------------------------------------------

    async def create_deployment(
        self,
        project_name: str,
        git_repo: str,
        ref: str = "main",
        target: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> DeploymentStatus:
        """
        Create a new deployment.

        Args:
            project_name: Name of the Vercel project
            git_repo: Git repository URL
            ref: Git branch/tag/ref to deploy (default: "main")
            target: Production or preview environment (default: None for preview)
            metadata: Optional deployment metadata

        Returns:
            DeploymentStatus object with deployment details

        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.info(f"Creating deployment for {project_name}:{ref}")

        payload = {
            "name": project_name,
            "git": {
                "repo": git_repo,
                "ref": ref,
            },
        }

        if target:
            payload["target"] = target

        if metadata:
            payload["metadata"] = metadata

        params = self._get_team_param()

        response = await self.client.post(
            f"/{self.API_VERSION}/deployments",
            json=payload,
            params=params,
        )

        self._log_rate_limit(response)
        response.raise_for_status()

        data = response.json()

        deployment = DeploymentStatus(
            id=data["id"],
            status=data.get("readyState", "QUEUED"),
            url=data.get("url", ""),
            ready_state=data.get("readyState", ""),
            created_at=datetime.fromisoformat(
                data["createdAt"].replace("Z", "+00:00")
            ),
            project_id=data.get("projectId", ""),
            build_id=data.get("buildId", ""),
            meta=data.get("meta", {}),
        )

        logger.info(f"✅ Created deployment: {deployment.id}")
        logger.info(f"   URL: {deployment.url}")

        return deployment

    async def get_deployment(self, deployment_id: str) -> Optional[DeploymentStatus]:
        """
        Get deployment details by ID.

        Args:
            deployment_id: Deployment ID

        Returns:
            DeploymentStatus object or None if not found
        """
        logger.debug(f"Getting deployment: {deployment_id}")

        try:
            params = self._get_team_param()
            response = await self.client.get(
                f"/{self.API_VERSION}/deployments/{deployment_id}",
                params=params,
            )

            self._log_rate_limit(response)
            response.raise_for_status()

            data = response.json()

            return DeploymentStatus(
                id=data["id"],
                status=data.get("readyState", "QUEUED"),
                url=data.get("url", ""),
                ready_state=data.get("readyState", ""),
                created_at=datetime.fromisoformat(
                    data["createdAt"].replace("Z", "+00:00")
                ),
                project_id=data.get("projectId", ""),
                build_id=data.get("buildId", ""),
                meta=data.get("meta", {}),
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Deployment not found: {deployment_id}")
                return None
            raise

    async def list_deployments(
        self,
        project_id: Optional[str] = None,
        limit: int = 20,
    ) -> list[DeploymentStatus]:
        """
        List deployments.

        Args:
            project_id: Optional project ID to filter by
            limit: Max results to return

        Returns:
            List of DeploymentStatus objects
        """
        logger.debug(f"Listing deployments: project={project_id}, limit={limit}")

        params = {"limit": limit}
        params.update(self._get_team_param())

        if project_id:
            params["projectId"] = project_id

        response = await self.client.get(
            f"/{self.API_VERSION}/deployments",
            params=params,
        )

        self._log_rate_limit(response)
        response.raise_for_status()

        data = response.json()
        deployments = [
            DeploymentStatus(
                id=item["id"],
                status=item.get("readyState", "QUEUED"),
                url=item.get("url", ""),
                ready_state=item.get("readyState", ""),
                created_at=datetime.fromisoformat(
                    item["createdAt"].replace("Z", "+00:00")
                ),
                project_id=item.get("projectId", ""),
                build_id=item.get("buildId", ""),
                meta=item.get("meta", {}),
            )
            for item in data.get("deployments", [])
        ]

        logger.debug(f"Listed {len(deployments)} deployments")
        return deployments

    async def wait_for_deployment(
        self,
        deployment_id: str,
        timeout: int = 600,
        interval: int = 5,
    ) -> DeploymentStatus:
        """
        Wait for deployment to complete.

        Args:
            deployment_id: Deployment ID to monitor
            timeout: Maximum wait time in seconds (default: 10 minutes)
            interval: Polling interval in seconds (default: 5)

        Returns:
            Final DeploymentStatus object

        Raises:
            TimeoutError: If deployment doesn't complete within timeout
        """
        logger.info(f"Waiting for deployment {deployment_id} (timeout: {timeout}s)")

        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Deployment {deployment_id} did not complete within {timeout}s"
                )

            deployment = await self.get_deployment(deployment_id)
            if not deployment:
                raise ValueError(f"Deployment {deployment_id} not found")

            logger.debug(
                f"Deployment status: {deployment.ready_state} "
                f"({int(time.time() - start_time)}s elapsed)"
            )

            if deployment.ready_state in (
                ReadyState.READY,
                ReadyState.ERROR,
                ReadyState.CANCELED,
                ReadyState.FAILED,
            ):
                if deployment.ready_state == ReadyState.READY:
                    logger.info(f"✅ Deployment ready: {deployment.url}")
                else:
                    logger.warning(f"⚠️ Deployment {deployment.ready_state}")

                return deployment

            await asyncio.sleep(interval)

    async def get_deployment_logs(
        self,
        deployment_id: str,
        build_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Get deployment logs.

        Note: Log download URLs expire after 1 minute.

        Args:
            deployment_id: Deployment ID
            build_id: Optional build ID for specific build logs

        Returns:
            List of log entries
        """
        logger.debug(f"Getting logs for deployment: {deployment_id}")

        if not build_id:
            deployment = await self.get_deployment(deployment_id)
            if deployment:
                build_id = deployment.build_id

        if not build_id:
            logger.warning("No build ID available for logs")
            return []

        params = self._get_team_param()
        response = await self.client.get(
            f"/{self.API_VERSION}/deployments/{deployment_id}/logs",
            params=params,
        )

        self._log_rate_limit(response)
        response.raise_for_status()

        data = response.json()
        logs = data.get("logs", [])

        logger.debug(f"Retrieved {len(logs)} log entries")
        return logs

    async def cancel_deployment(self, deployment_id: str) -> bool:
        """
        Cancel a deployment.

        Args:
            deployment_id: Deployment ID to cancel

        Returns:
            True if successful, False if not found
        """
        logger.info(f"Cancelling deployment: {deployment_id}")

        try:
            params = self._get_team_param()
            response = await self.client.patch(
                f"/{self.API_VERSION}/deployments/{deployment_id}/cancel",
                params=params,
            )

            self._log_rate_limit(response)
            response.raise_for_status()

            logger.info(f"✅ Cancelled deployment: {deployment_id}")
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Deployment not found: {deployment_id}")
                return False
            raise

    # -------------------------------------------------------------------------
    # Project Operations
    # -------------------------------------------------------------------------

    async def list_projects(
        self,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        List all projects.

        Args:
            limit: Max results to return

        Returns:
            List of project dictionaries
        """
        logger.debug(f"Listing projects: limit={limit}")

        params = {"limit": limit}
        params.update(self._get_team_param())

        response = await self.client.get(
            f"/{self.API_VERSION}/projects",
            params=params,
        )

        self._log_rate_limit(response)
        response.raise_for_status()

        data = response.json()
        projects = data.get("projects", [])

        logger.debug(f"Listed {len(projects)} projects")
        return projects

    async def get_project(self, project_id: str) -> Optional[dict[str, Any]]:
        """
        Get project details.

        Args:
            project_id: Project ID or name

        Returns:
            Project dictionary or None if not found
        """
        logger.debug(f"Getting project: {project_id}")

        try:
            params = self._get_team_param()
            response = await self.client.get(
                f"/{self.API_VERSION}/projects/{project_id}",
                params=params,
            )

            self._log_rate_limit(response)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Project not found: {project_id}")
                return None
            raise

    # -------------------------------------------------------------------------
    # Environment Variable Operations
    # -------------------------------------------------------------------------

    async def get_env_variables(
        self,
        project_id: str,
    ) -> list[dict[str, Any]]:
        """
        Get environment variables for a project.

        Args:
            project_id: Project ID

        Returns:
            List of environment variable dictionaries
        """
        logger.debug(f"Getting env variables for project: {project_id}")

        params = self._get_team_param()
        response = await self.client.get(
            f"/{self.API_VERSION}/projects/{project_id}/env",
            params=params,
        )

        self._log_rate_limit(response)
        response.raise_for_status()

        data = response.json()
        env_vars = data.get("envs", [])

        logger.debug(f"Retrieved {len(env_vars)} environment variables")
        return env_vars

    async def create_env_variable(
        self,
        project_id: str,
        key: str,
        value: str,
        environment: list[str] | None = None,
        target: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create an environment variable for a project.

        Args:
            project_id: Project ID
            key: Environment variable name
            value: Environment variable value
            environment: Environment(s) to apply to (production, preview, development)
            target: Target(s) to apply to (production, preview)

        Returns:
            Created environment variable dictionary
        """
        logger.info(f"Creating env variable for project {project_id}: {key}")

        if environment is None:
            environment = ["preview", "production"]

        if target is None:
            target = ["preview", "production"]

        payload = {
            "key": key,
            "value": value,
            "type": "encrypted",
            "environments": environment,
            "target": target,
        }

        params = self._get_team_param()
        response = await self.client.post(
            f"/{self.API_VERSION}/projects/{project_id}/env",
            json=payload,
            params=params,
        )

        self._log_rate_limit(response)
        response.raise_for_status()

        data = response.json()
        created = data.get("created", [])

        logger.info(f"✅ Created env variable: {key}")
        return created[0] if created else {}

    async def delete_env_variable(
        self,
        project_id: str,
        env_id: str,
    ) -> bool:
        """
        Delete an environment variable.

        Args:
            project_id: Project ID
            env_id: Environment variable ID

        Returns:
            True if successful
        """
        logger.info(f"Deleting env variable: {env_id}")

        params = self._get_team_param()
        response = await self.client.delete(
            f"/{self.API_VERSION}/projects/{project_id}/env/{env_id}",
            params=params,
        )

        self._log_rate_limit(response)
        response.raise_for_status()

        logger.info(f"✅ Deleted env variable: {env_id}")
        return True

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    async def check_connection(self) -> bool:
        """
        Check API connection and authentication.

        Returns:
            True if connection successful
        """
        try:
            # Try to list projects to verify auth
            await self.list_projects(limit=1)
            logger.info("✅ Connection check successful")
            return True
        except Exception as e:
            logger.error(f"❌ Connection check failed: {e}")
            return False
