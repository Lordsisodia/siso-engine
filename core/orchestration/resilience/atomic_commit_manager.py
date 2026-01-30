"""
Atomic Commit Manager - Auto-commits after task completion
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

try:
    from ..operations.tools.git_ops import GitOps, CommitInfo
except ImportError:
    # Fallback to absolute import
    try:
        from git.git_ops import GitOps, CommitInfo
    except ImportError:
        # Last resort - direct import
        import sys
        from pathlib import Path
        # Add the git tools directory to path
        tools_path = Path(__file__).parent.parent.parent.parent / "05-tools" / "git"
        sys.path.insert(0, str(tools_path))
        from git_ops import GitOps, CommitInfo


logger = logging.getLogger(__name__)


@dataclass
class TaskCommitInfo:
    """Information about a task's commit."""
    task_id: str
    commit_hash: str
    commit_type: str  # feat, fix, test, etc.
    scope: str
    description: str
    files: List[str]
    timestamp: datetime
    wave_id: Optional[int] = None
    rollback_commit: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "commit_hash": self.commit_hash,
            "commit_type": self.commit_type,
            "scope": self.scope,
            "description": self.description,
            "files": self.files,
            "timestamp": self.timestamp.isoformat(),
            "wave_id": self.wave_id,
            "rollback_commit": self.rollback_commit
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskCommitInfo":
        """Create from dictionary."""
        return cls(
            task_id=data["task_id"],
            commit_hash=data["commit_hash"],
            commit_type=data["commit_type"],
            scope=data["scope"],
            description=data["description"],
            files=data["files"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            wave_id=data.get("wave_id"),
            rollback_commit=data.get("rollback_commit")
        )


class AtomicCommitManager:
    """
    Manages atomic commits for task execution.

    Automatically creates commits after tasks complete,
    enabling granular rollback and never losing work.

    Key Features:
    - Auto-detect modified files after task execution
    - Create conventional commits for each task
    - Track commit history with task metadata
    - Rollback specific tasks with revert commits
    - Persistent history storage
    """

    def __init__(
        self,
        git_ops: Optional[GitOps] = None,
        history_path: Optional[Path] = None
    ):
        """
        Initialize atomic commit manager.

        Args:
            git_ops: GitOps instance (creates default if None)
            history_path: Path to store commit history
        """
        self.git_ops = git_ops or GitOps()
        self.history_path = history_path or Path(
            "blackbox5/data/atomic_commit_history.json"
        )
        self.commit_history: List[TaskCommitInfo] = []

        # Ensure parent directory exists
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing history
        self._load_history()

        logger.info(
            f"AtomicCommitManager initialized with {len(self.commit_history)} "
            f"historical commits"
        )

    def _load_history(self) -> None:
        """Load commit history from disk."""
        if not self.history_path.exists():
            return

        try:
            with open(self.history_path, 'r') as f:
                data = json.load(f)
                self.commit_history = [
                    TaskCommitInfo.from_dict(item) for item in data
                ]
            logger.debug(f"Loaded {len(self.commit_history)} commit records")
        except Exception as e:
            logger.warning(f"Failed to load commit history: {e}")
            self.commit_history = []

    def _save_history(self) -> None:
        """Save commit history to disk."""
        try:
            with open(self.history_path, 'w') as f:
                json.dump(
                    [c.to_dict() for c in self.commit_history],
                    f,
                    indent=2
                )
            logger.debug(f"Saved {len(self.commit_history)} commit records")
        except Exception as e:
            logger.error(f"Failed to save commit history: {e}")

    def detect_task_changes(
        self,
        task_id: str,
        before_snapshot: List[str]
    ) -> List[str]:
        """
        Detect files changed during task execution.

        Args:
            task_id: Task identifier
            before_snapshot: Git status snapshot before task

        Returns:
            List of modified file paths
        """
        # Get current git status
        current_status = self.git_ops.get_modified_files()

        # Find new/modified files
        before_set = set(before_snapshot)
        current_set = set(current_status)

        # Files that are different from before
        changed_files = list(current_set - before_set)

        # Also include files that were in before_snapshot but are now modified
        for file in before_snapshot:
            if file in current_set and file not in changed_files:
                # File still modified, include it
                changed_files.append(file)

        logger.debug(
            f"Task {task_id}: Detected {len(changed_files)} changed files"
        )

        return changed_files

    def create_snapshot(self) -> List[str]:
        """
        Capture current git state as snapshot.

        Returns:
            List of currently modified files
        """
        return self.git_ops.get_modified_files()

    def commit_task_result(
        self,
        task_id: str,
        task_type: str,
        scope: str,
        description: str,
        files: List[str],
        body: Optional[str] = None,
        wave_id: Optional[int] = None
    ) -> TaskCommitInfo:
        """
        Create atomic commit for completed task.

        Args:
            task_id: Task identifier
            task_type: Conventional commit type (feat, fix, test, etc.)
            scope: Task scope (e.g., "auth", "database")
            description: Commit description
            files: List of files to commit
            body: Optional commit body
            wave_id: Optional wave ID for tracking

        Returns:
            TaskCommitInfo with commit details

        Raises:
            ValueError: If invalid commit type
        """
        # Validate commit type
        valid_types = ["feat", "fix", "test", "refactor", "perf", "docs", "style", "chore"]
        if task_type not in valid_types:
            raise ValueError(
                f"Invalid type '{task_type}'. Must be one of: {valid_types}"
            )

        # Filter out empty files
        files = [f for f in files if f]
        if not files:
            logger.warning(f"No files to commit for task {task_id}")
            return None

        # Truncate description if too long
        if len(description) > 72:
            description = description[:69] + "..."

        # Build commit body with task metadata
        if body is None:
            body = f"Task ID: {task_id}"
            if wave_id is not None:
                body += f"\nWave ID: {wave_id}"
            body += f"\nFiles: {len(files)}"

        # Stage and commit files
        try:
            commit_hash = self.git_ops.commit_task(
                task_type=task_type,
                scope=scope,
                description=description,
                files=files,
                body=body
            )
        except Exception as e:
            logger.error(f"Failed to commit task {task_id}: {e}")
            raise

        # Record commit info
        commit_info = TaskCommitInfo(
            task_id=task_id,
            commit_hash=commit_hash,
            commit_type=task_type,
            scope=scope,
            description=description,
            files=files,
            timestamp=datetime.now(),
            wave_id=wave_id
        )

        self.commit_history.append(commit_info)
        self._save_history()

        logger.info(
            f"Committed task {task_id}: {commit_hash} - "
            f"{task_type}({scope}): {description}"
        )

        return commit_info

    def rollback_task(self, task_id: str) -> str:
        """
        Rollback commit for specific task.

        Creates a revert commit that undoes the task's changes.

        Args:
            task_id: Task to rollback

        Returns:
            Rollback commit hash

        Raises:
            ValueError: If no commit found for task
        """
        # Find commit for this task
        commit_info = next(
            (c for c in self.commit_history if c.task_id == task_id),
            None
        )

        if not commit_info:
            raise ValueError(f"No commit found for task {task_id}")

        # Create rollback commit
        try:
            rollback_hash = self.git_ops.create_rollback_commit(
                commit_info.commit_hash
            )
        except Exception as e:
            logger.error(f"Failed to rollback task {task_id}: {e}")
            raise

        # Update commit info with rollback
        commit_info.rollback_commit = rollback_hash
        self._save_history()

        logger.info(
            f"Rolled back task {task_id}: {commit_info.commit_hash} -> "
            f"{rollback_hash}"
        )

        return rollback_hash

    def get_commit_history(
        self,
        task_id: Optional[str] = None,
        wave_id: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[TaskCommitInfo]:
        """
        Get history of task commits.

        Args:
            task_id: Optional filter by task ID
            wave_id: Optional filter by wave ID
            limit: Optional limit on number of results

        Returns:
            List of TaskCommitInfo matching filters
        """
        history = self.commit_history

        # Apply filters
        if task_id:
            history = [c for c in history if c.task_id == task_id]
        if wave_id is not None:
            history = [c for c in history if c.wave_id == wave_id]

        # Apply limit
        if limit:
            history = history[-limit:]

        return history

    def get_task_commit(self, task_id: str) -> Optional[TaskCommitInfo]:
        """
        Get commit info for specific task.

        Args:
            task_id: Task identifier

        Returns:
            TaskCommitInfo or None if not found
        """
        return next(
            (c for c in self.commit_history if c.task_id == task_id),
            None
        )

    def infer_commit_type(
        self,
        task_description: str,
        task_category: str = ""
    ) -> str:
        """
        Infer conventional commit type from task.

        Rules (checked in order, first match wins):
        - "test*" or "testing" -> "test"
        - "style" or "format" -> "style"  (check before fix!)
        - "fix*" or "bug*" -> "fix"
        - "refactor*" or "clean*" -> "refactor"
        - "perform*" or "optimi*" -> "perf"
        - "doc*" or "readme" -> "docs"
        - "chore" or "maint*" -> "chore"
        - Otherwise -> "feat"

        Args:
            task_description: Task description text
            task_category: Optional task category

        Returns:
            Inferred commit type
        """
        import re
        desc_lower = task_description.lower()
        category_lower = task_category.lower()

        # Check both description and category
        combined = f"{desc_lower} {category_lower}"

        # Check for specific patterns (order matters!)
        # Use word boundaries where appropriate to avoid false matches
        if "test" in combined or "testing" in combined:
            return "test"
        elif "style" in combined or "format" in combined:
            return "style"
        elif re.search(r'\bfix', combined) or "bug" in combined:
            return "fix"
        elif "refactor" in combined or "clean" in combined or "reorganize" in combined:
            return "refactor"
        elif "perform" in combined or "optim" in combined:
            return "perf"
        elif "doc" in combined or "readme" in combined:
            return "docs"
        elif "chore" in combined or "maint" in combined:
            return "chore"
        else:
            return "feat"

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about commits.

        Returns:
            Dictionary with commit statistics
        """
        if not self.commit_history:
            return {
                "total_commits": 0,
                "by_type": {},
                "by_scope": {},
                "with_rollback": 0,
                "latest_commit": None
            }

        # Count by type
        by_type = {}
        for commit in self.commit_history:
            by_type[commit.commit_type] = by_type.get(commit.commit_type, 0) + 1

        # Count by scope
        by_scope = {}
        for commit in self.commit_history:
            by_scope[commit.scope] = by_scope.get(commit.scope, 0) + 1

        # Count rollbacks
        with_rollback = sum(
            1 for c in self.commit_history if c.rollback_commit
        )

        return {
            "total_commits": len(self.commit_history),
            "by_type": by_type,
            "by_scope": by_scope,
            "with_rollback": with_rollback,
            "latest_commit": self.commit_history[-1].to_dict() if self.commit_history else None
        }

    def clear_history(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear commit history.

        Args:
            older_than_days: Only clear commits older than this many days.
                           If None, clears all history.

        Returns:
            Number of commits removed
        """
        if older_than_days is None:
            count = len(self.commit_history)
            self.commit_history = []
        else:
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=older_than_days)
            old_count = len(self.commit_history)
            self.commit_history = [
                c for c in self.commit_history if c.timestamp > cutoff
            ]
            count = old_count - len(self.commit_history)

        self._save_history()
        return count


def create_atomic_commit_manager(
    git_ops: Optional[GitOps] = None,
    history_path: Optional[Path] = None
) -> AtomicCommitManager:
    """
    Create an AtomicCommitManager with sensible defaults.

    Args:
        git_ops: Optional GitOps instance
        history_path: Optional history path

    Returns:
        Configured AtomicCommitManager
    """
    return AtomicCommitManager(
        git_ops=git_ops,
        history_path=history_path
    )
