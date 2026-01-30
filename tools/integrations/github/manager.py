#!/usr/bin/env python3
"""
GitHub Manager for BlackBox5
============================

A simplified GitHub integration using Python requests library for direct GitHub API calls.

Based on CCPM's GitHub sync patterns, adapted for BlackBox5's architecture.

Features:
- Create issues with labels
- Create pull requests
- Add comments to issues
- Update issue status
- Simple HTTP-based authentication

Usage:
    manager = GitHubManager(token="ghp_xxx", repo="owner/repo")
    issue = manager.create_issue("Title", "Body", ["bug", "high-priority"])
    pr = manager.create_pr("branch", "PR title", "Description", "main")
    manager.add_comment(issue_number, "Comment text")
    manager.update_status(issue_number, "closed")
"""

import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

try:
    import requests
except ImportError:
    raise ImportError(
        "requests library required. Install with: pip install requests"
    )

logger = logging.getLogger(__name__)


@dataclass
class GitHubIssue:
    """Data class for GitHub issue."""
    number: int
    title: str
    body: str
    state: str
    html_url: str
    labels: List[str]
    created_at: str
    updated_at: str


@dataclass
class GitHubPR:
    """Data class for GitHub pull request."""
    number: int
    title: str
    body: str
    state: str
    html_url: str
    head_ref: str
    base_ref: str
    created_at: str
    updated_at: str


class GitHubManager:
    """
    Simple GitHub API client using requests library.

    Inspired by CCPM's GitHub sync patterns:
    - Creates issues with proper labels
    - Supports pull request creation
    - Adds comments for progress tracking
    - Updates issue state

    Authentication:
        Uses GitHub Personal Access Token (PAT).
        Create at: https://github.com/settings/tokens
        Required scopes: repo, issues, pull_requests

    Example:
        >>> manager = GitHubManager(
        ...     token="ghp_xxxxxxxxxxxx",
        ...     repo="owner/repo"
        ... )
        >>> issue = manager.create_issue(
        ...     title="Fix authentication bug",
        ...     body="Users cannot login with SAML",
        ...     labels=["bug", "critical"]
        ... )
        >>> print(f"Created issue #{issue.number}")
    """

    # GitHub API base URL
    API_BASE = "https://api.github.com"

    def __init__(
        self,
        token: Optional[str] = None,
        repo: Optional[str] = None,
        base_url: str = "https://api.github.com"
    ):
        """
        Initialize GitHubManager.

        Args:
            token: GitHub Personal Access Token (PAT). If None, reads from
                   GITHUB_TOKEN environment variable.
            repo: Repository in format "owner/repo". If None, attempts to
                   auto-detect from git config.
            base_url: GitHub API base URL (for GitHub Enterprise)

        Raises:
            ValueError: If token cannot be determined
            RuntimeError: If repo cannot be determined
        """
        # Get token from parameter or environment
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token required. Pass as parameter or set GITHUB_TOKEN env var. "
                "Create PAT at: https://github.com/settings/tokens"
            )

        # Get repository
        self.repo = repo or self._detect_repository()
        if not self.repo:
            raise RuntimeError(
                "Repository required. Pass as 'owner/repo' or run from git repository."
            )

        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "BlackBox5-GitHubManager/1.0"
        })

        logger.info(f"GitHubManager initialized for repo: {self.repo}")

    def _detect_repository(self) -> Optional[str]:
        """
        Auto-detect repository from git config.

        Returns:
            Repository string in "owner/repo" format, or None if not found
        """
        try:
            import subprocess

            # Get remote URL from git config
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0 or not result.stdout.strip():
                return None

            remote_url = result.stdout.strip()

            # Parse GitHub URL
            # Supports both HTTPS and SSH URLs
            # HTTPS: https://github.com/owner/repo.git
            # SSH:   git@github.com:owner/repo.git

            if "github.com" not in remote_url:
                return None

            # Remove protocol and .git suffix
            if remote_url.startswith("https://"):
                repo_path = remote_url.replace("https://github.com/", "").replace(".git", "")
            elif remote_url.startswith("git@"):
                repo_path = remote_url.replace("git@github.com:", "").replace(".git", "")
            else:
                return None

            logger.debug(f"Auto-detected repository: {repo_path}")
            return repo_path

        except (subprocess.SubprocessError, FileNotFoundError):
            return None

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to GitHub API.

        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: URL query parameters

        Returns:
            Response JSON data

        Raises:
            requests.HTTPError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"{method} {url}")

        response = self.session.request(
            method=method,
            url=url,
            json=data,
            params=params
        )

        # Check for errors
        if response.status_code >= 400:
            error_msg = f"GitHub API error {response.status_code}"
            try:
                error_detail = response.json().get("message", "")
                error_msg += f": {error_detail}"
            except:
                error_msg += f": {response.text}"
            logger.error(error_msg)
            response.raise_for_status()

        return response.json()

    # -------------------------------------------------------------------------
    # Issue Operations
    # -------------------------------------------------------------------------

    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> GitHubIssue:
        """
        Create a GitHub issue.

        Args:
            title: Issue title
            body: Issue body (supports markdown)
            labels: List of label names to apply
            assignees: List of usernames to assign

        Returns:
            GitHubIssue object with created issue details

        Raises:
            requests.HTTPError: If creation fails

        Example:
            >>> issue = manager.create_issue(
            ...     title="Add user authentication",
            ...     body="Implement OAuth2 login flow",
            ...     labels=["feature", "authentication"]
            ... )
            >>> print(f"Created issue #{issue.number}: {issue.html_url}")
        """
        logger.info(f"Creating issue: {title}")

        data = {"title": title, "body": body}

        if labels:
            data["labels"] = labels

        if assignees:
            data["assignees"] = assignees

        endpoint = f"/repos/{self.repo}/issues"
        response = self._make_request("POST", endpoint, data=data)

        issue = GitHubIssue(
            number=response["number"],
            title=response["title"],
            body=response.get("body", ""),
            state=response["state"],
            html_url=response["html_url"],
            labels=[label["name"] for label in response.get("labels", [])],
            created_at=response["created_at"],
            updated_at=response["updated_at"]
        )

        logger.info(f"✅ Created issue #{issue.number}: {issue.html_url}")
        return issue

    def get_issue(self, issue_number: int) -> GitHubIssue:
        """
        Get issue details.

        Args:
            issue_number: Issue number

        Returns:
            GitHubIssue object
        """
        endpoint = f"/repos/{self.repo}/issues/{issue_number}"
        response = self._make_request("GET", endpoint)

        return GitHubIssue(
            number=response["number"],
            title=response["title"],
            body=response.get("body", ""),
            state=response["state"],
            html_url=response["html_url"],
            labels=[label["name"] for label in response.get("labels", [])],
            created_at=response["created_at"],
            updated_at=response["updated_at"]
        )

    def update_issue(
        self,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> GitHubIssue:
        """
        Update an existing issue.

        Args:
            issue_number: Issue number
            title: New title (optional)
            body: New body (optional)
            state: New state: "open" or "closed" (optional)
            labels: New list of labels (replaces existing) (optional)

        Returns:
            Updated GitHubIssue object
        """
        logger.info(f"Updating issue #{issue_number}")

        data = {}
        if title is not None:
            data["title"] = title
        if body is not None:
            data["body"] = body
        if state is not None:
            data["state"] = state
        if labels is not None:
            data["labels"] = labels

        endpoint = f"/repos/{self.repo}/issues/{issue_number}"
        response = self._make_request("PATCH", endpoint, data=data)

        logger.info(f"✅ Updated issue #{issue_number}")
        return self.get_issue(issue_number)

    def update_status(self, issue_number: int, status: str) -> GitHubIssue:
        """
        Update issue status (open/closed).

        Convenience method for update_issue() focused on state changes.

        Args:
            issue_number: Issue number
            status: "open" or "closed"

        Returns:
            Updated GitHubIssue object

        Raises:
            ValueError: If status is not "open" or "closed"
        """
        if status not in ["open", "closed"]:
            raise ValueError(f"Invalid status: {status}. Must be 'open' or 'closed'.")

        logger.info(f"Setting issue #{issue_number} to '{status}'")
        return self.update_issue(issue_number, state=status)

    def add_comment(self, issue_number: int, comment: str) -> Dict[str, Any]:
        """
        Add a comment to an issue.

        Args:
            issue_number: Issue number
            comment: Comment text (supports markdown)

        Returns:
            Response data with comment details

        Example:
            >>> manager.add_comment(123, "Progress update: Completed API endpoint")
            {'id': 456789, 'body': 'Progress update: ...', ...}
        """
        logger.info(f"Adding comment to issue #{issue_number}")

        data = {"body": comment}
        endpoint = f"/repos/{self.repo}/issues/{issue_number}/comments"
        response = self._make_request("POST", endpoint, data=data)

        logger.info(f"✅ Added comment to issue #{issue_number}")
        return response

    def list_comments(self, issue_number: int) -> List[Dict[str, Any]]:
        """
        List all comments on an issue.

        Args:
            issue_number: Issue number

        Returns:
            List of comment data
        """
        endpoint = f"/repos/{self.repo}/issues/{issue_number}/comments"
        return self._make_request("GET", endpoint)

    # -------------------------------------------------------------------------
    # Pull Request Operations
    # -------------------------------------------------------------------------

    def create_pr(
        self,
        branch: str,
        title: str,
        body: str,
        base: Optional[str] = None,
        draft: bool = False,
        labels: Optional[List[str]] = None
    ) -> GitHubPR:
        """
        Create a pull request.

        Args:
            branch: Head branch name (your branch with changes)
            title: PR title
            body: PR description (supports markdown)
            base: Base branch to merge into (default: repository default)
            draft: Whether to create as draft PR
            labels: List of labels to apply

        Returns:
            GitHubPR object with created PR details

        Example:
            >>> pr = manager.create_pr(
            ...     branch="feature/add-auth",
            ...     title="Add user authentication",
            ...     body="Implements OAuth2 login flow",
            ...     base="main"
            ... )
            >>> print(f"Created PR #{pr.number}: {pr.html_url}")
        """
        logger.info(f"Creating PR from {branch} to {base or 'default'}")

        # Get default branch if not specified
        if base is None:
            base = self._get_default_branch()

        data = {
            "title": title,
            "body": body,
            "head": branch,
            "base": base,
            "draft": draft
        }

        endpoint = f"/repos/{self.repo}/pulls"
        response = self._make_request("POST", endpoint, data=data)

        pr = GitHubPR(
            number=response["number"],
            title=response["title"],
            body=response.get("body", ""),
            state=response["state"],
            html_url=response["html_url"],
            head_ref=response["head"]["ref"],
            base_ref=response["base"]["ref"],
            created_at=response["created_at"],
            updated_at=response["updated_at"]
        )

        # Apply labels if provided
        if labels:
            self._apply_pr_labels(pr.number, labels)
            pr.labels = labels

        logger.info(f"✅ Created PR #{pr.number}: {pr.html_url}")
        return pr

    def get_pr(self, pr_number: int) -> GitHubPR:
        """
        Get pull request details.

        Args:
            pr_number: Pull request number

        Returns:
            GitHubPR object
        """
        endpoint = f"/repos/{self.repo}/pulls/{pr_number}"
        response = self._make_request("GET", endpoint)

        return GitHubPR(
            number=response["number"],
            title=response["title"],
            body=response.get("body", ""),
            state=response["state"],
            html_url=response["html_url"],
            head_ref=response["head"]["ref"],
            base_ref=response["base"]["ref"],
            created_at=response["created_at"],
            updated_at=response["updated_at"]
        )

    def list_prs(
        self,
        state: str = "open",
        head: Optional[str] = None,
        base: Optional[str] = None
    ) -> List[GitHubPR]:
        """
        List pull requests.

        Args:
            state: "open", "closed", or "all"
            head: Filter by head branch
            base: Filter by base branch

        Returns:
            List of GitHubPR objects
        """
        params = {"state": state}
        if head:
            params["head"] = f"{self.repo.split('/')[0]}:{head}"
        if base:
            params["base"] = base

        endpoint = f"/repos/{self.repo}/pulls"
        response_list = self._make_request("GET", endpoint, params=params)

        prs = []
        for response in response_list:
            prs.append(GitHubPR(
                number=response["number"],
                title=response["title"],
                body=response.get("body", ""),
                state=response["state"],
                html_url=response["html_url"],
                head_ref=response["head"]["ref"],
                base_ref=response["base"]["ref"],
                created_at=response["created_at"],
                updated_at=response["updated_at"]
            ))

        return prs

    def add_pr_comment(self, pr_number: int, comment: str) -> Dict[str, Any]:
        """
        Add a comment to a pull request.

        Args:
            pr_number: Pull request number
            comment: Comment text

        Returns:
            Response data with comment details
        """
        # PR comments use the same endpoint as issues
        return self.add_comment(pr_number, comment)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _get_default_branch(self) -> str:
        """Get repository default branch."""
        endpoint = f"/repos/{self.repo}"
        response = self._make_request("GET", endpoint)
        return response.get("default_branch", "main")

    def _apply_pr_labels(self, pr_number: int, labels: List[str]) -> None:
        """Apply labels to a pull request."""
        endpoint = f"/repos/{self.repo}/issues/{pr_number}/labels"
        for label in labels:
            try:
                self._make_request("POST", endpoint, data={"labels": [label]})
            except Exception as e:
                logger.warning(f"Failed to apply label '{label}': {e}")

    def check_repository_safe(self) -> bool:
        """
        Check if repository is safe for modifications.

        Prevents accidental modifications to template repositories.
        Based on CCPM's repository protection pattern.

        Returns:
            True if repository is safe for modifications

        Example:
            >>> if not manager.check_repository_safe():
            ...     print("⚠️ Cannot modify this repository")
            ...     return
        """
        try:
            endpoint = f"/repos/{self.repo}"
            response = self._make_request("GET", endpoint)

            # Check if it's a fork or template
            is_fork = response.get("fork", False)
            is_template = response.get("is_template", False)

            # Check permissions
            permissions = response.get("permissions", {})
            can_push = permissions.get("push", False)
            can_admin = permissions.get("admin", False)

            # Warn if likely a template repository
            if not (can_push or can_admin):
                logger.warning(
                    f"⚠️ Insufficient permissions on {self.repo}. "
                    "You may not be able to create issues or PRs."
                )
                return False

            logger.info(f"✅ Repository {self.repo} is safe for modifications")
            return True

        except Exception as e:
            logger.error(f"Failed to check repository safety: {e}")
            return False


# -------------------------------------------------------------------------
# Convenience Functions
# -------------------------------------------------------------------------

def create_manager_from_env() -> GitHubManager:
    """
    Create GitHubManager from environment variables.

    Environment variables:
        GITHUB_TOKEN: GitHub Personal Access Token (required)
        GITHUB_REPO: Repository in "owner/repo" format (optional, auto-detected)

    Returns:
        Configured GitHubManager instance

    Raises:
        ValueError: If GITHUB_TOKEN not set
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError(
            "GITHUB_TOKEN environment variable not set. "
            "Create a PAT at: https://github.com/settings/tokens"
        )

    repo = os.environ.get("GITHUB_REPO")

    return GitHubManager(token=token, repo=repo)


def main():
    """CLI interface for testing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="BlackBox5 GitHub Manager - Simple GitHub API client"
    )
    parser.add_argument(
        "--token",
        help="GitHub token (or set GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--repo",
        help="Repository (owner/repo)"
    )
    parser.add_argument(
        "--create-issue",
        nargs=2,
        metavar=("TITLE", "BODY"),
        help="Create an issue"
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        help="Issue labels"
    )

    args = parser.parse_args()

    # Create manager
    manager = GitHubManager(token=args.token, repo=args.repo)

    # Handle commands
    if args.create_issue:
        title, body = args.create_issue
        issue = manager.create_issue(
            title=title,
            body=body,
            labels=args.labels
        )
        print(f"✅ Created issue #{issue.number}: {issue.html_url}")
    else:
        print("No command specified. Use --help for usage information.")


if __name__ == "__main__":
    main()
