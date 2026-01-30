"""
Git Client - Wrapper for git operations
"""

import subprocess
import logging
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class GitClient:
    """
    Simple wrapper for git operations.

    Provides a clean interface for common git commands.
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

    def _run(self, args: List[str]) -> str:
        """Run a git command."""
        result = subprocess.run(
            ["git"] + args,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    def status(self) -> str:
        """Get git status."""
        return self._run(["status", "--short"])

    def add(self, files: List[str]):
        """Stage files."""
        return self._run(["add"] + files)

    def commit(self, message: str, allow_empty: bool = False) -> str:
        """Create a commit."""
        args = ["commit", "-m", message]
        if allow_empty:
            args.append("--allow-empty")
        return self._run(args)

    def get_current_branch(self) -> str:
        """Get current branch name."""
        return self._run(["rev-parse", "--abbrev-ref", "HEAD"])

    def get_head_commit(self) -> str:
        """Get HEAD commit hash."""
        return self._run(["rev-parse", "HEAD"])

    def is_dirty(self) -> bool:
        """Check if working directory is dirty."""
        return bool(self.status())
