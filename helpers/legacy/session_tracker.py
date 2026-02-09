#!/usr/bin/env python3
"""
Legacy Session Tracker

Tracks Legacy run execution data:
- Files created/modified
- Git commits made
- Duration
- Progress milestones

Adapted from Blackbox5 Ralphy integration.
"""

import json
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# Add lib to path for importing paths module
sys.path.insert(0, str(Path(__file__).parent))
from paths import get_path_resolver


class SessionTracker:
    """
    Track Legacy run sessions.

    Stores tracking data in run folder as tracking.json
    and archives to .autonomous/history/
    """

    def __init__(
        self,
        agent_id: str = "legacy",
        autonomous_root: Optional[Path] = None
    ):
        """
        Initialize session tracker.

        Args:
            agent_id: Agent identifier (default: "legacy")
            autonomous_root: Path to .autonomous folder
        """
        self.agent_id = agent_id

        # Determine .autonomous root
        if autonomous_root is None:
            # Use path resolver for consistent path resolution
            resolver = get_path_resolver()
            autonomous_root = resolver.engine_path / '.autonomous'

        self.autonomous_root = autonomous_root
        self.history_path = autonomous_root / "history"
        self.history_path.mkdir(parents=True, exist_ok=True)

        # Session tracking
        self.run_id: Optional[str] = None
        self.run_start: Optional[datetime] = None
        self.tracking_file: Optional[Path] = None
        self.data: Dict[str, Any] = {}

    def start_run(
        self,
        run_id: str,
        task_id: str,
        task_title: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Start tracking a new Legacy run.

        Args:
            run_id: Run identifier (e.g., "run-0017")
            task_id: Task being executed
            task_title: Task title
            metadata: Additional metadata

        Returns:
            Path to tracking.json file
        """
        self.run_id = run_id
        self.run_start = datetime.now(timezone.utc)

        # Create tracking file in run folder
        run_folder = self.autonomous_root / "runs" / run_id
        run_folder.mkdir(parents=True, exist_ok=True)

        self.tracking_file = run_folder / "tracking.json"

        # Initialize tracking data
        self.data = {
            "run_id": run_id,
            "agent_id": self.agent_id,
            "task_id": task_id,
            "task_title": task_title,
            "status": "active",
            "start_time": self.run_start.isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "files_created": [],
            "files_modified": [],
            "git_commits": [],
            "progress_log": [],
            "metadata": metadata or {}
        }

        self._save()
        print(f"[Tracker] Started run: {run_id}", file=sys.stderr)

        return self.tracking_file

    def record_file_created(self, filepath: str) -> None:
        """Record a file created during the run."""
        if not self.run_id:
            return

        abs_path = str(Path(filepath).resolve())
        if abs_path not in self.data["files_created"]:
            self.data["files_created"].append(abs_path)
            self._save()

    def record_file_modified(self, filepath: str) -> None:
        """Record a file modified during the run."""
        if not self.run_id:
            return

        abs_path = str(Path(filepath).resolve())
        if abs_path not in self.data["files_modified"]:
            self.data["files_modified"].append(abs_path)
            self._save()

    def record_git_commit(self, commit_hash: str, message: str = "") -> None:
        """Record a git commit made during the run."""
        if not self.run_id:
            return

        self.data["git_commits"].append({
            "hash": commit_hash,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._save()

    def capture_git_state(self) -> None:
        """Capture current git commit if in a git repo."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.autonomous_root
            )
            if result.returncode == 0:
                commit_hash = result.stdout.strip()

                # Get commit message
                msg_result = subprocess.run(
                    ["git", "log", "-1", "--pretty=%B"],
                    capture_output=True,
                    text=True,
                    cwd=self.autonomous_root
                )
                message = msg_result.stdout.strip() if msg_result.returncode == 0 else ""

                self.record_git_commit(commit_hash, message)
        except Exception:
            pass  # Not a git repo or git not available

    def log_progress(self, message: str, category: str = "info") -> None:
        """
        Log a progress milestone.

        Args:
            message: Progress message
            category: Category (info, warning, error, milestone, decision)
        """
        if not self.run_id:
            return

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "message": message
        }

        self.data["progress_log"].append(log_entry)
        self._save()

    def end_run(
        self,
        success: bool = True,
        result: str = "",
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        End the run and finalize tracking.

        Args:
            success: Whether the run was successful
            result: Result description
            error: Error message if failed

        Returns:
            Complete tracking data
        """
        if not self.run_id:
            print("Warning: No active run to end", file=sys.stderr)
            return {}

        # Calculate duration
        end_time = datetime.now(timezone.utc)
        duration = None
        if self.run_start:
            duration = (end_time - self.run_start).total_seconds()

        # Update data
        self.data["status"] = "completed" if success else "failed"
        self.data["end_time"] = end_time.isoformat()
        self.data["duration_seconds"] = duration
        self.data["result"] = result
        if error:
            self.data["error"] = error

        self._save()

        # Archive to history
        self._archive_run()

        print(f"[Tracker] Ended run: {self.run_id} ({duration:.1f}s)", file=sys.stderr)

        return self.data

    def _save(self) -> None:
        """Save tracking data to file."""
        if self.tracking_file:
            try:
                with open(self.tracking_file, 'w') as f:
                    json.dump(self.data, f, indent=2)
            except Exception as e:
                print(f"Warning: Failed to save tracking: {e}", file=sys.stderr)

    def _archive_run(self) -> None:
        """Archive run to history."""
        if not self.run_id:
            return

        history_file = self.history_path / "runs.json"

        # Load existing history
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except Exception:
                history = []

        # Add run summary
        summary = {
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "task_id": self.data.get("task_id"),
            "task_title": self.data.get("task_title"),
            "start_time": self.data.get("start_time"),
            "end_time": self.data.get("end_time"),
            "duration_seconds": self.data.get("duration_seconds"),
            "success": self.data.get("status") == "completed",
            "files_count": len(self.data.get("files_created", [])),
            "commits_count": len(self.data.get("git_commits", []))
        }

        history.append(summary)

        # Save history
        try:
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to archive run: {e}", file=sys.stderr)


def create_tracker() -> SessionTracker:
    """Create a session tracker instance."""
    return SessionTracker()


if __name__ == "__main__":
    # Test the tracker
    tracker = create_tracker()

    tracking_file = tracker.start_run(
        run_id="run-test-001",
        task_id="TASK-TEST-001",
        task_title="Test task"
    )

    print(f"Tracking file: {tracking_file}")

    tracker.log_progress("Starting analysis", "info")
    tracker.log_progress("Found 3 files to modify", "milestone")

    tracker.record_file_modified("/path/to/file1.py")
    tracker.record_file_created("/path/to/file2.py")

    tracker.capture_git_state()

    tracker.log_progress("Completed successfully", "milestone")

    data = tracker.end_run(
        success=True,
        result="Task completed successfully"
    )

    print("\nTracking data:")
    print(json.dumps(data, indent=2))
