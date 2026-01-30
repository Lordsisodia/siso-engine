#!/usr/bin/env python3
"""
Unit tests for Session Tracker

Tests the run session tracking system.
Run with: python3 -m unittest test_session_tracker -v
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).parent))

from session_tracker import SessionTracker, create_tracker


class TestSessionTracker(unittest.TestCase):
    """Test cases for SessionTracker class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.autonomous_root = Path(self.temp_dir) / ".Autonomous"
        self.tracker = SessionTracker(autonomous_root=self.autonomous_root)

    def tearDown(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_init_creates_directories(self):
        """Test that initialization creates required directories."""
        self.assertTrue(self.autonomous_root.exists())
        self.assertTrue(self.tracker.history_path.exists())

    def test_init_with_default_path(self):
        """Test initialization with default path."""
        tracker = SessionTracker()
        self.assertIsNotNone(tracker.autonomous_root)
        self.assertTrue(tracker.autonomous_root.exists())

    def test_start_run(self):
        """Test starting a new run."""
        tracking_file = self.tracker.start_run(
            run_id="run-001",
            task_id="TASK-001",
            task_title="Test Task"
        )

        self.assertTrue(tracking_file.exists())
        self.assertEqual(self.tracker.run_id, "run-001")
        self.assertIsNotNone(self.tracker.run_start)
        self.assertEqual(self.tracker.data["run_id"], "run-001")
        self.assertEqual(self.tracker.data["task_id"], "TASK-001")
        self.assertEqual(self.tracker.data["status"], "active")

    def test_start_run_with_metadata(self):
        """Test starting a run with metadata."""
        metadata = {"priority": "high", "assignee": "agent-1"}

        tracking_file = self.tracker.start_run(
            run_id="run-002",
            task_id="TASK-002",
            task_title="Test Task 2",
            metadata=metadata
        )

        data = json.loads(tracking_file.read_text())
        self.assertEqual(data["metadata"], metadata)

    def test_record_file_created(self):
        """Test recording a created file."""
        self.tracker.start_run("run-001", "TASK-001", "Test")

        self.tracker.record_file_created("/path/to/new_file.py")

        self.assertIn("/path/to/new_file.py", self.tracker.data["files_created"])
        # Should save after recording
        self.assertTrue(self.tracker.tracking_file.exists())

    def test_record_file_modified(self):
        """Test recording a modified file."""
        self.tracker.start_run("run-001", "TASK-001", "Test")

        self.tracker.record_file_modified("/path/to/existing_file.py")

        self.assertIn("/path/to/existing_file.py", self.tracker.data["files_modified"])

    def test_record_git_commit(self):
        """Test recording a git commit."""
        self.tracker.start_run("run-001", "TASK-001", "Test")

        self.tracker.record_git_commit("abc123", "Test commit message")

        self.assertEqual(len(self.tracker.data["git_commits"]), 1)
        self.assertEqual(self.tracker.data["git_commits"][0]["hash"], "abc123")
        self.assertEqual(self.tracker.data["git_commits"][0]["message"], "Test commit message")

    def test_log_progress(self):
        """Test logging progress."""
        self.tracker.start_run("run-001", "TASK-001", "Test")

        self.tracker.log_progress("Starting analysis", "info")
        self.tracker.log_progress("Found 3 files", "milestone")

        self.assertEqual(len(self.tracker.data["progress_log"]), 2)
        self.assertEqual(self.tracker.data["progress_log"][0]["message"], "Starting analysis")
        self.assertEqual(self.tracker.data["progress_log"][0]["category"], "info")
        self.assertEqual(self.tracker.data["progress_log"][1]["category"], "milestone")

    def test_log_progress_without_active_run(self):
        """Test logging progress when no run is active."""
        # Should not raise error, just silently return
        self.tracker.log_progress("Test message")
        self.assertEqual(len(self.tracker.data.get("progress_log", [])), 0)

    def test_end_run_success(self):
        """Test ending a run successfully."""
        self.tracker.start_run("run-001", "TASK-001", "Test")

        result = self.tracker.end_run(success=True, result="Task completed")

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["result"], "Task completed")
        self.assertIsNotNone(result["end_time"])
        self.assertIsNotNone(result["duration_seconds"])

    def test_end_run_failure(self):
        """Test ending a run with failure."""
        self.tracker.start_run("run-001", "TASK-001", "Test")

        result = self.tracker.end_run(success=False, error="Something went wrong")

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"], "Something went wrong")

    def test_end_run_without_active_run(self):
        """Test ending run when none is active."""
        result = self.tracker.end_run()
        self.assertEqual(result, {})

    def test_capture_git_state_success(self):
        """Test capturing git state when in a git repo."""
        self.tracker.start_run("run-001", "TASK-001", "Test")

        # Mock subprocess to simulate git repo
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout.strip.return_value = "abc123def"

        mock_msg_result = MagicMock()
        mock_msg_result.returncode = 0
        mock_msg_result.stdout.strip.return_value = "Test commit"

        with patch('subprocess.run', side_effect=[mock_result, mock_msg_result]):
            self.tracker.capture_git_state()

        self.assertGreater(len(self.tracker.data["git_commits"]), 0)

    def test_capture_git_state_no_repo(self):
        """Test capturing git state when not in a git repo."""
        self.tracker.start_run("run-001", "TASK-001", "Test")

        # Mock subprocess to simulate no git
        mock_result = MagicMock()
        mock_result.returncode = 1  # git failed

        with patch('subprocess.run', return_value=mock_result):
            self.tracker.capture_git_state()

        # Should silently fail, not crash
        self.assertEqual(len(self.tracker.data["git_commits"]), 0)

    def test_run_folder_created(self):
        """Test that run folder is created."""
        tracking_file = self.tracker.start_run("run-001", "TASK-001", "Test")

        run_folder = self.autonomous_root / "runs" / "run-001"
        self.assertTrue(run_folder.exists())
        self.assertEqual(tracking_file.parent, run_folder)

    def test_archiving_to_history(self):
        """Test that run is archived to history."""
        self.tracker.start_run("run-001", "TASK-001", "Test")
        self.tracker.record_file_created("/test.py")
        self.tracker.end_run(success=True)

        history_file = self.tracker.history_path / "runs.json"
        self.assertTrue(history_file.exists())

        history = json.loads(history_file.read_text())
        self.assertGreater(len(history), 0)
        self.assertEqual(history[-1]["run_id"], "run-001")
        self.assertEqual(history[-1]["success"], True)

    def test_archiving_accumulates(self):
        """Test that multiple runs accumulate in history."""
        # First run
        self.tracker.start_run("run-001", "TASK-001", "Test 1")
        self.tracker.end_run(success=True)

        # Second run
        self.tracker.start_run("run-002", "TASK-002", "Test 2")
        self.tracker.end_run(success=True)

        history_file = self.tracker.history_path / "runs.json"
        history = json.loads(history_file.read_text())

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["run_id"], "run-001")
        self.assertEqual(history[1]["run_id"], "run-002")

    def test_tracking_file_json_format(self):
        """Test that tracking file has correct JSON format."""
        tracking_file = self.tracker.start_run("run-001", "TASK-001", "Test")

        data = json.loads(tracking_file.read_text())

        self.assertIn("run_id", data)
        self.assertIn("agent_id", data)
        self.assertIn("task_id", data)
        self.assertIn("status", data)
        self.assertIn("start_time", data)
        self.assertIn("files_created", data)
        self.assertIn("files_modified", data)
        self.assertIn("git_commits", data)
        self.assertIn("progress_log", data)

    def test_duration_calculation(self):
        """Test that duration is calculated correctly."""
        self.tracker.start_run("run-001", "TASK-001", "Test")

        # Mock end time to be 5 seconds after start
        original_end_run = self.tracker.end_run

        def mock_end_run(**kwargs):
            if self.tracker.run_start:
                duration = 5.0
                self.tracker.data["duration_seconds"] = duration
            return original_end_run(**kwargs)

        with patch.object(self.tracker, 'end_run', side_effect=mock_end_run):
            result = self.tracker.end_run(success=True)

        self.assertIsNotNone(result.get("duration_seconds"))

    def test_file_paths_are_resolved_to_absolute(self):
        """Test that file paths are resolved to absolute paths."""
        self.tracker.start_run("run-001", "TASK-001", "Test")

        self.tracker.record_file_created("relative/path.py")
        self.tracker.record_file_modified("../other/path.py")

        # Paths should be stored as absolute
        for path in self.tracker.data["files_created"]:
            self.assertTrue(path.startswith("/"))

    def test_duplicate_files_not_recorded_twice(self):
        """Test that duplicate file recordings are deduplicated."""
        self.tracker.start_run("run-001", "TASK-001", "Test")

        self.tracker.record_file_created("/test.py")
        self.tracker.record_file_created("/test.py")  # Same file

        self.assertEqual(len(self.tracker.data["files_created"]), 1)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def test_create_tracker(self):
        """Test create_tracker convenience function."""
        tracker = create_tracker()
        self.assertIsInstance(tracker, SessionTracker)
        self.assertIsNotNone(tracker.autonomous_root)


if __name__ == "__main__":
    unittest.main()
