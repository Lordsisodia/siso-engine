#!/usr/bin/env python3
"""
Git Operations - Git utilities for atomic commits

Consolidated module providing comprehensive git operations including:
- Basic git commands (status, add, commit)
- Atomic commit protocol with conventional commit format
- Commit history and information retrieval
- Branch operations
- Rollback functionality
"""

import subprocess
import sys
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class CommitInfo:
    """Information about a git commit."""
    hash: str
    short_hash: str
    author: str
    date: datetime
    message: str
    files_changed: List[str]
    full_hash: Optional[str] = None
    commit_type: Optional[str] = None  # feat, fix, test, etc.
    scope: Optional[str] = None
    description: Optional[str] = None


class GitOps:
    """
    Implements GSD "Atomic Commits" protocol.
    Enforces format: type(phase-plan): description
    """

    def __init__(self, repo_path: str = "."):
        """
        Initialize GitOps with optional repo path.

        Args:
            repo_path: Path to the git repository (default: current directory)
        """
        self.repo_path = Path(repo_path).resolve()
        self._pending_files: List[str] = []

    @staticmethod
    def run_cmd(cmd: List[str], cwd: Optional[str] = None) -> str:
        """Run a git command and return output."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=cwd
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}"

    def _run(self, args: List[str]) -> str:
        """Run a git command in the repo path (instance method)."""
        return GitOps.run_cmd(["git"] + args, cwd=str(self.repo_path))

    @staticmethod
    def status() -> str:
        """Get git status in short format."""
        return GitOps.run_cmd(["git", "status", "--short"])

    def get_status(self) -> str:
        """Get git status in short format (instance method)."""
        return self._run(["status", "--short"])

    @staticmethod
    def check_clean_state() -> bool:
        """Check if working directory is clean."""
        status = GitOps.status()
        return status == ""

    def is_dirty(self) -> bool:
        """Check if working directory is dirty (has uncommitted changes)."""
        return bool(self.get_status())

    def is_clean(self) -> bool:
        """Check if working directory is clean (no uncommitted changes)."""
        return not self.is_dirty()

    @staticmethod
    def get_modified_files() -> List[str]:
        """
        Get list of modified files using git status.

        Returns:
            List of file paths that have been modified/added/deleted

        Format parsed: "M path/to/file" or "A path/to/file" or "D path/to/file"
        """
        status_output = GitOps.run_cmd(["git", "status", "--short"])

        if "Error" in status_output or not status_output:
            return []

        files = []
        for line in status_output.split('\n'):
            if line.strip():
                # Parse status line: XY filename
                # X = staged status, Y = working tree status
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    status_code, filepath = parts
                    # Include all modified, added, deleted, or renamed files
                    if status_code in ['M', 'A', 'D', 'R', 'C', '??', 'AM', 'MM']:
                        files.append(filepath)

        return files

    def stage_files(self, files: List[str]):
        """
        Stage files for commit and track them as pending.

        Args:
            files: List of file paths to stage
        """
        self._pending_files.extend(files)
        self._run(["add"] + files)

    def get_pending_files(self) -> List[str]:
        """Get list of pending files that have been staged."""
        return self._pending_files.copy()

    def clear_pending_files(self):
        """Clear the list of pending files."""
        self._pending_files.clear()

    @staticmethod
    def add(files: List[str]) -> str:
        """Stage files (static method)."""
        return GitOps.run_cmd(["git", "add"] + files)

    @staticmethod
    def commit_task(
        task_type: str,
        scope: str,
        description: str,
        files: List[str],
        body: Optional[str] = None
    ) -> str:
        """
        Executes a GSD atomic commit.

        Args:
            task_type: Conventional commit type (feat, fix, test, etc.)
            scope: Commit scope (e.g., "auth", "database")
            description: Commit description
            files: List of files to stage and commit
            body: Optional commit body

        Returns:
            Short commit hash

        Raises:
            ValueError: If invalid task type provided
        """
        # 1. Validate inputs
        valid_types = ["feat", "fix", "test", "refactor", "perf", "docs", "style", "chore"]
        if task_type not in valid_types:
            raise ValueError(
                f"Invalid type '{task_type}'. Must be one of: {valid_types}"
            )

        # 2. Stage files
        for file in files:
            result = GitOps.run_cmd(["git", "add", file])
            if "Error" in result:
                raise RuntimeError(f"Failed to stage {file}: {result}")

        # 3. Construct message
        header = f"{task_type}({scope}): {description}"
        message = header
        if body:
            message += f"\n\n{body}"

        # 4. Commit
        result = GitOps.run_cmd(["git", "commit", "-m", message])

        if "Error" in result:
            raise RuntimeError(f"Commit failed: {result}")

        # 5. Return hash
        return GitOps.run_cmd(["git", "rev-parse", "--short", "HEAD"])

    def create_commit(
        self,
        message: str,
        type_: str = "feat",
        scope: Optional[str] = None,
        allow_empty: bool = False
    ) -> str:
        """
        Create a conventional commit (instance method).

        Args:
            message: Commit message/description
            type_: Commit type (feat, fix, docs, etc.)
            scope: Optional scope
            allow_empty: Whether to allow empty commits

        Returns:
            Commit hash
        """
        # Format: type(scope): message
        if scope:
            formatted = f"{type_}({scope}): {message}"
        else:
            formatted = f"{type_}: {message}"

        args = ["commit", "-m", formatted]
        if allow_empty:
            args.append("--allow-empty")

        result = self._run(args)
        self._pending_files.clear()
        return result

    @staticmethod
    def create_rollback_commit(commit_hash: str) -> str:
        """
        Create a rollback commit that reverts the specified commit.

        This creates a new commit that undoes the changes from the specified commit,
        preserving git history.

        Args:
            commit_hash: The commit hash to revert

        Returns:
            New commit hash for the revert commit

        Raises:
            RuntimeError: If revert fails
        """
        # Revert without committing
        revert_result = GitOps.run_cmd(
            ["git", "revert", "--no-commit", commit_hash]
        )

        if "Error" in revert_result and "error:" in revert_result.lower():
            raise RuntimeError(f"Revert failed: {revert_result}")

        # Get short hash for message
        short_hash = GitOps.run_cmd(["git", "rev-parse", "--short", commit_hash])

        # Create commit with revert message
        commit_message = f"revert: rollback of {short_hash}\n\nThis reverts commit {commit_hash}"

        commit_result = GitOps.run_cmd(["git", "commit", "-m", commit_message])

        if "Error" in commit_result:
            raise RuntimeError(f"Rollback commit failed: {commit_result}")

        return GitOps.run_cmd(["git", "rev-parse", "--short", "HEAD"])

    def rollback(self, commits: int = 1) -> str:
        """
        Rollback the last N commits.

        Args:
            commits: Number of commits to rollback (default: 1)

        Returns:
            Result of the reset command
        """
        return self._run(["reset", "--soft", f"HEAD~{commits}"])

    @staticmethod
    def get_commit_info(commit_hash: str) -> CommitInfo:
        """
        Get information about a commit.

        Args:
            commit_hash: Commit hash (can be short or full)

        Returns:
            CommitInfo with hash, author, date, message, files_changed

        Raises:
            RuntimeError: If commit not found
        """
        # Get full hash
        full_hash = GitOps.run_cmd(["git", "rev-parse", commit_hash])
        if "Error" in full_hash:
            raise RuntimeError(f"Commit {commit_hash} not found")

        # Get short hash
        short_hash = GitOps.run_cmd(["git", "rev-parse", "--short", commit_hash])

        # Get commit info in pretty format
        format_str = "%H|%an|%ad|%s"
        info_line = GitOps.run_cmd([
            "git", "log",
            "-1",
            f"--format={format_str}",
            commit_hash
        ])

        if "Error" in info_line or not info_line:
            raise RuntimeError(f"Failed to get commit info for {commit_hash}")

        parts = info_line.split('|')
        if len(parts) != 4:
            raise RuntimeError(f"Unexpected commit info format: {info_line}")

        _, author, date_str, message = parts

        # Parse date (git outputs ISO 8601 format with --date=iso)
        try:
            commit_date = datetime.fromisoformat(date_str)
        except ValueError:
            # Fallback parsing
            commit_date = datetime.now()

        # Get files changed in this commit
        files_output = GitOps.run_cmd([
            "git", "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            commit_hash
        ])

        files_changed = []
        if "Error" not in files_output and files_output:
            files_changed = files_output.split('\n')

        # Try to parse conventional commit format
        commit_type = None
        scope = None
        description = message
        if ':' in message and '(' in message.split(':')[0]:
            header = message.split(':')[0]
            description = message.split(':', 1)[1].strip()
            if '(' in header:
                commit_type = header.split('(')[0]
                scope = header.split('(')[1].rstrip(')')

        return CommitInfo(
            hash=short_hash,
            short_hash=short_hash,
            full_hash=full_hash,
            author=author,
            date=commit_date,
            message=message,
            files_changed=files_changed,
            commit_type=commit_type,
            scope=scope,
            description=description
        )

    @staticmethod
    def get_current_head() -> str:
        """
        Get the current HEAD commit hash.

        Returns:
            Short commit hash of current HEAD
        """
        return GitOps.run_cmd(["git", "rev-parse", "--short", "HEAD"])

    def get_head_commit(self) -> str:
        """
        Get the HEAD commit hash (full).

        Returns:
            Full commit hash of current HEAD
        """
        return self._run(["rev-parse", "HEAD"])

    def get_current_branch(self) -> str:
        """
        Get the current branch name.

        Returns:
            Name of the current branch
        """
        return self._run(["rev-parse", "--abbrev-ref", "HEAD"])

    @staticmethod
    def get_commit_history(count: int = 10) -> List[CommitInfo]:
        """
        Get recent commit history.

        Args:
            count: Number of commits to retrieve

        Returns:
            List of CommitInfo objects
        """
        format_str = "%H|%an|%ad|%s"
        history_output = GitOps.run_cmd([
            "git", "log",
            f"-{count}",
            f"--format={format_str}"
        ])

        commits = []
        if "Error" in history_output or not history_output:
            return commits

        for line in history_output.split('\n'):
            if not line.strip():
                continue

            parts = line.split('|')
            if len(parts) != 4:
                continue

            full_hash, author, date_str, message = parts

            # Get short hash
            short_hash = GitOps.run_cmd(["git", "rev-parse", "--short", full_hash])

            # Parse date
            try:
                commit_date = datetime.fromisoformat(date_str)
            except ValueError:
                commit_date = datetime.now()

            # Get files changed
            files_output = GitOps.run_cmd([
                "git", "diff-tree",
                "--no-commit-id",
                "--name-only",
                "-r",
                full_hash
            ])

            files_changed = []
            if "Error" not in files_output and files_output:
                files_changed = files_output.split('\n')

            # Try to parse conventional commit format
            commit_type = None
            scope = None
            description = message
            if ':' in message and '(' in message.split(':')[0]:
                header = message.split(':')[0]
                description = message.split(':', 1)[1].strip()
                if '(' in header:
                    commit_type = header.split('(')[0]
                    scope = header.split('(')[1].rstrip(')')

            commits.append(CommitInfo(
                hash=short_hash,
                short_hash=short_hash,
                full_hash=full_hash,
                author=author,
                date=commit_date,
                message=message,
                files_changed=files_changed,
                commit_type=commit_type,
                scope=scope,
                description=description
            ))

        return commits


# Backwards compatibility aliases
GitClient = GitOps
CommitManager = GitOps


if __name__ == "__main__":
    # Test execution
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        print(f"Clean State: {GitOps.check_clean_state()}")
        print(f"Modified Files: {GitOps.get_modified_files()}")
        print(f"Current HEAD: {GitOps.get_current_head()}")
    elif len(sys.argv) > 1 and sys.argv[1] == "history":
        history = GitOps.get_commit_history(5)
        for commit in history:
            print(f"{commit.short_hash} - {commit.message}")
    else:
        print("GitOps Tool Ready. Use via import.")
