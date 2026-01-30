#!/usr/bin/env python3
import subprocess
import sys
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


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


class GitOps:
    """
    Implements GSD "Atomic Commits" protocol.
    Enforces format: type(phase-plan): description
    """

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

    @staticmethod
    def status() -> str:
        """Get git status in short format."""
        return GitOps.run_cmd(["git", "status", "--short"])

    @staticmethod
    def check_clean_state() -> bool:
        """Check if working directory is clean."""
        status = GitOps.status()
        return status == ""

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

        return CommitInfo(
            hash=short_hash,
            short_hash=short_hash,
            full_hash=full_hash,
            author=author,
            date=commit_date,
            message=message,
            files_changed=files_changed
        )

    @staticmethod
    def get_current_head() -> str:
        """
        Get the current HEAD commit hash.

        Returns:
            Short commit hash of current HEAD
        """
        return GitOps.run_cmd(["git", "rev-parse", "--short", "HEAD"])

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

            commits.append(CommitInfo(
                hash=short_hash,
                short_hash=short_hash,
                full_hash=full_hash,
                author=author,
                date=commit_date,
                message=message,
                files_changed=files_changed
            ))

        return commits


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
