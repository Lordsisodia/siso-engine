"""
GitHub Actions Manager for BlackBox5
=====================================

Main integration class for GitHub Actions service.

Features:
- List and manage workflows
- Trigger workflow_dispatch events
- Monitor workflow runs
- Download logs and artifacts
- Wait for deployment completion

Usage:
    >>> manager = GitHubActionsManager(owner="owner", repo="repo")
    >>> result = await manager.list_workflows()
"""

from __future__ import annotations

import asyncio
import logging
import os
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests

from .types import (
    Artifact,
    Workflow,
    WorkflowDispatchInput,
    WorkflowRun,
    WorkflowRunConclusion,
    WorkflowRunStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Rate Limit Tracker
# =============================================================================


@dataclass
class RateLimitInfo:
    """GitHub API rate limit information."""

    remaining: int
    limit: int
    reset_at: datetime
    used: int


# =============================================================================
# Main Manager Class
# =============================================================================


class GitHubActionsManager:
    """
    Main manager class for GitHub Actions integration.

    Authentication:
        Uses Personal Access Token (PAT) from environment variable.

    Rate Limits:
        - 5,000 requests per hour for authenticated requests
        - Rate limit headers are tracked automatically

    Example:
        >>> manager = GitHubActionsManager(owner="myorg", repo="myrepo")
        >>> workflows = await manager.list_workflows()
        >>> await manager.trigger_workflow(workflow_id, "main", inputs)
    """

    API_BASE = "https://api.github.com"
    API_VERSION = "2022-11-28"

    def __init__(
        self,
        owner: str,
        repo: str,
        token: Optional[str] = None,
        base_url: str = "https://api.github.com",
        timeout: int = 30,
    ):
        """
        Initialize GitHub Actions manager.

        Args:
            owner: Repository owner/organization
            repo: Repository name
            token: GitHub Personal Access Token (default: from GITHUB_TOKEN env var)
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        self.owner = owner
        self.repo = repo
        self.token = token or os.environ.get("GITHUB_TOKEN")

        if not self.token:
            raise ValueError(
                "GitHub token required. Set GITHUB_TOKEN "
                "environment variable or pass token parameter."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.rate_limit: Optional[RateLimitInfo] = None

        # Configure session
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": self.API_VERSION,
                "User-Agent": "BlackBox5/1.0",
            }
        )

        logger.info(f"Initialized GitHubActionsManager for {owner}/{repo}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Close HTTP session."""
        self.session.close()
        logger.debug("Closed HTTP session")

    def _update_rate_limit(self, response: requests.Response) -> None:
        """Update rate limit info from response headers."""
        try:
            remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
            limit = int(response.headers.get("X-RateLimit-Limit", 5000))
            reset = int(response.headers.get("X-RateLimit-Reset", 0))

            self.rate_limit = RateLimitInfo(
                remaining=remaining,
                limit=limit,
                reset_at=datetime.fromtimestamp(reset, tz=timezone.utc),
                used=limit - remaining,
            )

            logger.debug(
                f"Rate limit: {remaining}/{limit} remaining, "
                f"resets at {self.rate_limit.reset_at}"
            )

            if remaining < 100:
                logger.warning(f"Rate limit running low: {remaining} remaining")

        except (ValueError, TypeError) as e:
            logger.debug(f"Could not parse rate limit headers: {e}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
    ) -> requests.Response:
        """
        Make HTTP request to GitHub API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON body

        Returns:
            Response object

        Raises:
            requests.HTTPError: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            timeout=self.timeout,
        )

        self._update_rate_limit(response)
        response.raise_for_status()

        return response

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 datetime string."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except ValueError:
            logger.debug(f"Could not parse datetime: {dt_str}")
            return None

    # -------------------------------------------------------------------------
    # Workflow Operations
    # -------------------------------------------------------------------------

    def list_workflows(
        self,
        per_page: int = 100,
        page: int = 1,
    ) -> list[Workflow]:
        """
        List all workflows in the repository.

        Args:
            per_page: Results per page (max 100)
            page: Page number

        Returns:
            List of workflows

        Raises:
            requests.HTTPError: If API request fails
        """
        logger.debug(f"Listing workflows: page={page}, per_page={per_page}")

        response = self._make_request(
            "GET",
            f"/repos/{self.owner}/{self.repo}/actions/workflows",
            params={"per_page": per_page, "page": page},
        )

        data = response.json()
        workflows = [
            Workflow(
                id=item["id"],
                name=item["name"],
                path=item["path"],
                state=item["state"],
                created_at=self._parse_datetime(item["created_at"]) or datetime.now(timezone.utc),
                updated_at=self._parse_datetime(item["updated_at"]) or datetime.now(timezone.utc),
                url=item["url"],
                html_url=item["html_url"],
                badge_url=item.get("badge_url"),
                workflow_dispatch="workflow_dispatch" in item.get("state", ""),
                metadata={"total_count": data.get("total_count", 0)},
            )
            for item in data.get("workflows", [])
        ]

        logger.info(f"✅ Listed {len(workflows)} workflows")
        return workflows

    def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """
        Get a specific workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow data or None if not found
        """
        logger.debug(f"Getting workflow: {workflow_id}")

        try:
            response = self._make_request(
                "GET",
                f"/repos/{self.owner}/{self.repo}/actions/workflows/{workflow_id}",
            )

            item = response.json()
            workflow = Workflow(
                id=item["id"],
                name=item["name"],
                path=item["path"],
                state=item["state"],
                created_at=self._parse_datetime(item["created_at"]) or datetime.now(timezone.utc),
                updated_at=self._parse_datetime(item["updated_at"]) or datetime.now(timezone.utc),
                url=item["url"],
                html_url=item["html_url"],
                badge_url=item.get("badge_url"),
                workflow_dispatch="workflow_dispatch" in item.get("state", ""),
                metadata=item.get("metadata"),
            )

            logger.info(f"✅ Got workflow: {workflow.name}")
            return workflow

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Workflow not found: {workflow_id}")
                return None
            raise

    def trigger_workflow(
        self,
        workflow_id: int,
        ref: str,
        inputs: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Trigger a workflow_dispatch event.

        Args:
            workflow_id: Workflow ID
            ref: Branch or tag to run against (e.g., "main", "v1.0")
            inputs: Workflow inputs (must match workflow definition)

        Returns:
            True if triggered successfully

        Raises:
            requests.HTTPError: If workflow doesn't support dispatch or request fails

        Note:
            Workflow must have `workflow_dispatch` event configured.
            Returns 204 status on success (no content).
        """
        logger.info(f"Triggering workflow {workflow_id} on {ref}")

        payload = {"ref": ref}
        if inputs:
            payload["inputs"] = inputs

        response = self._make_request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/actions/workflows/{workflow_id}/dispatches",
            json_data=payload,
        )

        # 204 No Content = success
        if response.status_code == 204:
            logger.info(f"✅ Triggered workflow {workflow_id} on {ref}")
            return True

        return False

    # -------------------------------------------------------------------------
    # Workflow Run Operations
    # -------------------------------------------------------------------------

    def list_workflow_runs(
        self,
        status: Optional[WorkflowRunStatus | str] = None,
        branch: Optional[str] = None,
        workflow_id: Optional[int] = None,
        per_page: int = 100,
        page: int = 1,
    ) -> list[WorkflowRun]:
        """
        List workflow runs.

        Args:
            status: Filter by status (queued, in_progress, completed)
            branch: Filter by branch name
            workflow_id: Filter by workflow ID
            per_page: Results per page (max 100)
            page: Page number

        Returns:
            List of workflow runs
        """
        logger.debug(
            f"Listing workflow runs: status={status}, branch={branch}, "
            f"workflow_id={workflow_id}"
        )

        params = {"per_page": per_page, "page": page}

        if status:
            params["status"] = str(status)
        if branch:
            params["branch"] = branch
        if workflow_id:
            endpoint = f"/repos/{self.owner}/{self.repo}/actions/workflows/{workflow_id}/runs"
        else:
            endpoint = f"/repos/{self.owner}/{self.repo}/actions/runs"

        response = self._make_request("GET", endpoint, params=params)
        data = response.json()

        runs = [
            WorkflowRun(
                id=item["id"],
                name=item["name"],
                run_number=item["run_number"],
                status=WorkflowRunStatus(item["status"]),
                conclusion=WorkflowRunConclusion(item["conclusion"])
                if item.get("conclusion")
                else None,
                head_branch=item["head_branch"],
                head_sha=item["head_sha"],
                created_at=self._parse_datetime(item["created_at"])
                or datetime.now(timezone.utc),
                updated_at=self._parse_datetime(item["updated_at"])
                or datetime.now(timezone.utc),
                url=item["url"],
                html_url=item["html_url"],
                event=item["event"],
                actor=item["actor"],
                workflow_id=item["workflow_id"],
                run_started_at=self._parse_datetime(item.get("run_started_at")),
                cancelled_at=self._parse_datetime(item.get("cancelled_at")),
                metadata={"total_count": data.get("total_count", 0)},
            )
            for item in data.get("workflow_runs", [])
        ]

        logger.info(f"✅ Listed {len(runs)} workflow runs")
        return runs

    def get_workflow_run(self, run_id: int) -> Optional[WorkflowRun]:
        """
        Get a specific workflow run.

        Args:
            run_id: Run ID

        Returns:
            Workflow run data or None if not found
        """
        logger.debug(f"Getting workflow run: {run_id}")

        try:
            response = self._make_request(
                "GET",
                f"/repos/{self.owner}/{self.repo}/actions/runs/{run_id}",
            )

            item = response.json()
            run = WorkflowRun(
                id=item["id"],
                name=item["name"],
                run_number=item["run_number"],
                status=WorkflowRunStatus(item["status"]),
                conclusion=WorkflowRunConclusion(item["conclusion"])
                if item.get("conclusion")
                else None,
                head_branch=item["head_branch"],
                head_sha=item["head_sha"],
                created_at=self._parse_datetime(item["created_at"])
                or datetime.now(timezone.utc),
                updated_at=self._parse_datetime(item["updated_at"])
                or datetime.now(timezone.utc),
                url=item["url"],
                html_url=item["html_url"],
                event=item["event"],
                actor=item["actor"],
                workflow_id=item["workflow_id"],
                run_started_at=self._parse_datetime(item.get("run_started_at")),
                cancelled_at=self._parse_datetime(item.get("cancelled_at")),
                metadata=item.get("metadata"),
            )

            logger.info(f"✅ Got workflow run: {run.name} (status: {run.status})")
            return run

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Workflow run not found: {run_id}")
                return None
            raise

    async def wait_for_deployment(
        self,
        run_id: int,
        timeout: int = 1800,
        poll_interval: int = 10,
    ) -> WorkflowRun:
        """
        Wait for workflow run to complete.

        Args:
            run_id: Run ID to wait for
            timeout: Maximum wait time in seconds (default: 30 minutes)
            poll_interval: Poll interval in seconds (default: 10)

        Returns:
            Completed workflow run

        Raises:
            TimeoutError: If run doesn't complete within timeout
            requests.HTTPError: If API request fails
        """
        logger.info(f"Waiting for deployment {run_id} (timeout: {timeout}s)")

        start_time = datetime.now(timezone.utc)

        while True:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

            if elapsed > timeout:
                raise TimeoutError(
                    f"Workflow run {run_id} did not complete within {timeout}s"
                )

            run = self.get_workflow_run(run_id)
            if not run:
                raise ValueError(f"Workflow run {run_id} not found")

            if run.status == WorkflowRunStatus.COMPLETED:
                logger.info(
                    f"✅ Deployment {run_id} completed: {run.conclusion}"
                )
                return run

            logger.debug(
                f"Run {run_id} status: {run.status} "
                f"({elapsed:.0f}s elapsed)"
            )

            await asyncio.sleep(poll_interval)

    def download_logs(
        self,
        run_id: int,
        output_path: str | Path,
    ) -> str:
        """
        Download workflow run logs.

        Args:
            run_id: Run ID
            output_path: Directory to save logs

        Returns:
            Path to downloaded zip file

        Note:
            Log download URLs expire after 1 minute.
            Logs are returned as a ZIP archive.
        """
        logger.info(f"Downloading logs for run {run_id}")

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        # Get logs URL (creates an archive)
        response = self._make_request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/actions/runs/{run_id}/logs",
        )

        # Download the archive immediately (URL expires in 1 minute)
        download_url = response.url
        log_response = self.session.get(download_url, timeout=self.timeout)

        zip_path = output_path / f"run-{run_id}-logs.zip"

        with open(zip_path, "wb") as f:
            f.write(log_response.content)

        logger.info(f"✅ Downloaded logs to {zip_path}")
        return str(zip_path)

    # -------------------------------------------------------------------------
    # Artifact Operations
    # -------------------------------------------------------------------------

    def list_artifacts(
        self,
        run_id: Optional[int] = None,
        per_page: int = 100,
        page: int = 1,
    ) -> list[Artifact]:
        """
        List workflow artifacts.

        Args:
            run_id: Filter by run ID (optional)
            per_page: Results per page (max 100)
            page: Page number

        Returns:
            List of artifacts
        """
        logger.debug(f"Listing artifacts: run_id={run_id}")

        params = {"per_page": per_page, "page": page}

        if run_id:
            endpoint = f"/repos/{self.owner}/{self.repo}/actions/runs/{run_id}/artifacts"
        else:
            endpoint = f"/repos/{self.owner}/{self.repo}/actions/artifacts"

        response = self._make_request("GET", endpoint, params=params)
        data = response.json()

        artifacts = [
            Artifact(
                id=item["id"],
                name=item["name"],
                size_in_bytes=item["size_in_bytes"],
                expired=item["expired"],
                created_at=self._parse_datetime(item["created_at"])
                or datetime.now(timezone.utc),
                updated_at=self._parse_datetime(item["updated_at"])
                or datetime.now(timezone.utc),
                download_url=item["archive_download_url"],
                archive_download_url=item["archive_download_url"],
                workflow_run_id=item.get("workflow_run", {}).get("id")
                if item.get("workflow_run")
                else None,
                metadata={"total_count": data.get("total_count", 0)},
            )
            for item in data.get("artifacts", [])
        ]

        logger.info(f"✅ Listed {len(artifacts)} artifacts")
        return artifacts

    def download_artifact(
        self,
        artifact_id: int,
        output_path: str | Path,
        run_id: Optional[int] = None,
    ) -> str:
        """
        Download workflow artifact.

        Args:
            artifact_id: Artifact ID
            output_path: Directory to save artifact
            run_id: Optional run ID for filename

        Returns:
            Path to downloaded artifact

        Note:
            Artifact download URLs expire after 1 minute.
            Artifacts are returned as ZIP archives.
        """
        logger.info(f"Downloading artifact {artifact_id}")

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        # Get artifact to find name
        response = self._make_request(
            "GET",
            f"/repos/{self.owner}/{self.repo}/actions/artifacts/{artifact_id}",
        )

        data = response.json()
        artifact_name = data["name"]
        download_url = data["archive_download_url"]

        # Download immediately (URL expires in 1 minute)
        artifact_response = self.session.get(download_url, timeout=self.timeout)

        filename = f"{artifact_name}.zip" if not run_id else f"run-{run_id}-{artifact_name}.zip"
        artifact_path = output_path / filename

        with open(artifact_path, "wb") as f:
            f.write(artifact_response.content)

        logger.info(f"✅ Downloaded artifact to {artifact_path}")
        return str(artifact_path)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def get_rate_limit(self) -> Optional[RateLimitInfo]:
        """
        Get current rate limit information.

        Returns:
            Rate limit info or None if not available
        """
        return self.rate_limit

    def check_connection(self) -> bool:
        """
        Check GitHub API connection.

        Returns:
            True if connection successful
        """
        try:
            response = self._make_request(
                "GET",
                f"/repos/{self.owner}/{self.repo}",
            )
            logger.info("✅ Connection check successful")
            return True
        except Exception as e:
            logger.error(f"❌ Connection check failed: {e}")
            return False
