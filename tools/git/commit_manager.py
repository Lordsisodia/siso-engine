"""
Commit Manager - Manage atomic commits
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from .git_client import GitClient

logger = logging.getLogger(__name__)


@dataclass
class CommitInfo:
    """Information about a commit."""
    commit_hash: str
    commit_type: str  # feat, fix, test, etc.
    scope: Optional[str]
    description: str
    files: List[str]
    timestamp: datetime


class CommitManager:
    """
    Manages atomic commits with conventional commit format.

    Automatically creates commits after task completion with
    standardized commit messages.
    """

    def __init__(self, repo_path: str = "."):
        self.git = GitClient(repo_path)
        self._pending_files: List[str] = []

    def stage_files(self, files: List[str]):
        """Stage files for commit."""
        self._pending_files.extend(files)
        self.git.add(files)

    def create_commit(self, message: str, type_: str = "feat", scope: Optional[str] = None) -> str:
        """
        Create a conventional commit.

        Args:
            message: Commit message
            type_: Commit type (feat, fix, docs, etc.)
            scope: Optional scope

        Returns:
            Commit hash
        """
        # Format: type(scope): message
        if scope:
            formatted = f"{type_}({scope}): {message}"
        else:
            formatted = f"{type_}: {message}"

        result = self.git.commit(formatted)
        self._pending_files.clear()
        return result

    def rollback(self, commits: int = 1):
        """Rollback commits."""
        # TODO: Implement rollback
        pass

    def get_pending_files(self) -> List[str]:
        """Get list of pending files."""
        return self._pending_files.copy()
