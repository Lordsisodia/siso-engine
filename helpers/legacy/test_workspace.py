#!/usr/bin/env python3
"""
Unit tests for Workspace Factory

Tests the per-task workspace creation and management system.
Run with: python3 -m unittest test_workspace -v
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from workspace import WorkspaceFactory, create_workspace_for_task


class TestWorkspaceFactory(unittest.TestCase):
    """Test cases for WorkspaceFactory class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.factory = WorkspaceFactory(base_path=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_init_creates_base_directory(self):
        """Test that initialization creates base directory."""
        self.assertTrue(Path(self.temp_dir).exists())

    def test_init_with_default_path(self):
        """Test initialization with default path."""
        factory = WorkspaceFactory()
        self.assertIsNotNone(factory.base_path)
        self.assertTrue(factory.base_path.exists())

    def test_create_workspace(self):
        """Test creating a workspace."""
        workspace_path = self.factory.create_workspace(
            task_id="TASK-001",
            task_title="Test Task"
        )

        self.assertTrue(workspace_path.exists())
        self.assertEqual(workspace_path.name, "TASK-001")

    def test_workspace_directory_structure(self):
        """Test that workspace has correct directory structure."""
        workspace_path = self.factory.create_workspace(
            task_id="TASK-001",
            task_title="Test Task"
        )

        self.assertTrue((workspace_path / "timeline").exists())
        self.assertTrue((workspace_path / "thoughts").exists())
        self.assertTrue((workspace_path / "context").exists())
        self.assertTrue((workspace_path / "work").exists())

    def test_workspace_creates_result_json(self):
        """Test that result.json is created."""
        workspace_path = self.factory.create_workspace(
            task_id="TASK-001",
            task_title="Test Task"
        )

        result_path = workspace_path / "result.json"
        self.assertTrue(result_path.exists())

        data = json.loads(result_path.read_text())
        self.assertEqual(data["task_id"], "TASK-001")
        self.assertEqual(data["task_title"], "Test Task")
        self.assertEqual(data["status"], "created")
        self.assertIsNotNone(data["created_at"])

    def test_workspace_creates_readme(self):
        """Test that README.md is created."""
        workspace_path = self.factory.create_workspace(
            task_id="TASK-001",
            task_title="Test Task"
        )

        readme_path = workspace_path / "README.md"
        self.assertTrue(readme_path.exists())

        content = readme_path.read_text()
        self.assertIn("TASK-001", content)
        self.assertIn("Test Task", content)

    def test_workspace_with_context_files(self):
        """Test creating workspace with context files."""
        # Create a temp context file
        context_file = Path(self.temp_dir) / "context.md"
        context_file.write_text("# Context\n\nSome context")

        workspace_path = self.factory.create_workspace(
            task_id="TASK-001",
            task_title="Test Task",
            context_files=[str(context_file)]
        )

        copied_file = workspace_path / "context" / "context.md"
        self.assertTrue(copied_file.exists())
        self.assertEqual(copied_file.read_text(), "# Context\n\nSome context")

    def test_get_workspace_path(self):
        """Test getting workspace path."""
        self.factory.create_workspace("TASK-001", "Test")

        path = self.factory.get_workspace_path("TASK-001")
        self.assertEqual(path.name, "TASK-001")

    def test_workspace_exists(self):
        """Test checking if workspace exists."""
        self.assertFalse(self.factory.workspace_exists("TASK-001"))

        self.factory.create_workspace("TASK-001", "Test")

        self.assertTrue(self.factory.workspace_exists("TASK-001"))

    def test_update_result(self):
        """Test updating result.json."""
        self.factory.create_workspace("TASK-001", "Test")

        self.factory.update_result("TASK-001", {
            "status": "in_progress",
            "notes": "Making progress"
        })

        result_path = Path(self.temp_dir) / "TASK-001" / "result.json"
        data = json.loads(result_path.read_text())

        self.assertEqual(data["status"], "in_progress")
        self.assertEqual(data["notes"], "Making progress")
        self.assertIsNotNone(data.get("updated_at"))

    def test_update_result_nonexistent_workspace(self):
        """Test updating result for nonexistent workspace."""
        # Should not raise error, just do nothing
        self.factory.update_result("TASK-999", {"status": "done"})

    def test_add_thought(self):
        """Test adding a thought to workspace."""
        self.factory.create_workspace("TASK-001", "Test")

        thought_file = self.factory.add_thought(
            "TASK-001",
            "This is an important thought",
            category="analysis"
        )

        self.assertTrue(thought_file.exists())
        self.assertTrue(thought_file.name.startswith("analysis_"))
        self.assertTrue(thought_file.suffix == ".md")

        content = thought_file.read_text()
        self.assertIn("Analysis Thought", content)
        self.assertIn("This is an important thought", content)
        self.assertIn("TASK-001", content)

    def test_add_thought_creates_thoughts_dir(self):
        """Test that add_thought creates thoughts directory if needed."""
        # Create workspace but manually delete thoughts directory
        workspace = Path(self.temp_dir) / "TASK-001"
        workspace.mkdir(exist_ok=True)
        thoughts_dir = workspace / "thoughts"
        if thoughts_dir.exists():
            shutil.rmtree(thought_dir)

        # Should recreate directory
        thought_file = self.factory.add_thought("TASK-001", "Test")
        self.assertTrue(thought_file.exists())
        self.assertTrue(thought_file.parent.exists())

    def test_add_multiple_thoughts(self):
        """Test adding multiple thoughts."""
        self.factory.create_workspace("TASK-001", "Test")

        self.factory.add_thought("TASK-001", "First thought", category="idea")
        self.factory.add_thought("TASK-001", "Second thought", category="analysis")

        thoughts_dir = Path(self.temp_dir) / "TASK-001" / "thoughts"
        files = list(thoughts_dir.glob("*.md"))

        self.assertGreaterEqual(len(files), 2)

    def test_timeline_entry_created(self):
        """Test that timeline entry is created on workspace creation."""
        workspace_path = self.factory.create_workspace(
            task_id="TASK-001",
            task_title="Test Task"
        )

        timeline_dir = workspace_path / "timeline"
        timeline_files = list(timeline_dir.glob("*.json"))

        self.assertGreater(len(timeline_files), 0)

        entry = json.loads(timeline_files[0].read_text())
        self.assertEqual(entry["event"], "created")
        self.assertIn("task_id", entry["data"])

    def test_workspace_isolation(self):
        """Test that workspaces are isolated from each other."""
        self.factory.create_workspace("TASK-001", "First")
        self.factory.create_workspace("TASK-002", "Second")

        task1_result = Path(self.temp_dir) / "TASK-001" / "result.json"
        task2_result = Path(self.temp_dir) / "TASK-002" / "result.json"

        data1 = json.loads(task1_result.read_text())
        data2 = json.loads(task2_result.read_text())

        self.assertEqual(data1["task_id"], "TASK-001")
        self.assertEqual(data2["task_id"], "TASK-002")

    def test_result_json_initial_structure(self):
        """Test that result.json has correct initial structure."""
        workspace_path = self.factory.create_workspace("TASK-001", "Test")
        result_path = workspace_path / "result.json"
        data = json.loads(result_path.read_text())

        self.assertIn("task_id", data)
        self.assertIn("task_title", data)
        self.assertIn("status", data)
        self.assertIn("created_at", data)
        self.assertIn("completed_at", data)
        self.assertIn("deliverables", data)
        self.assertIn("notes", data)

        # Initial values
        self.assertIsNone(data["completed_at"])
        self.assertEqual(data["deliverables"], [])
        self.assertEqual(data["notes"], "")


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_create_workspace_for_task(self):
        """Test create_workspace_for_task convenience function."""
        workspace = create_workspace_for_task(
            task_id="TASK-001",
            task_title="Test Task",
            autonomous_root=Path(self.temp_dir)
        )

        self.assertTrue(workspace.exists())
        self.assertEqual(workspace.name, "TASK-001")
        self.assertTrue((workspace / "result.json").exists())


class TestWorkspaceEdgeCases(unittest.TestCase):
    """Test edge cases for workspace operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.factory = WorkspaceFactory(base_path=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_create_workspace_with_special_chars_in_title(self):
        """Test creating workspace with special characters in title."""
        workspace_path = self.factory.create_workspace(
            task_id="TASK-001",
            task_title="Test: Task with 'quotes' and \"double quotes\""
        )

        readme = workspace_path / "README.md"
        self.assertTrue(readme.exists())
        content = readme.read_text()
        self.assertIn("Test: Task with", content)

    def test_update_result_preserves_existing_fields(self):
        """Test that update preserves fields not being updated."""
        self.factory.create_workspace("TASK-001", "Original Title")

        # First update
        self.factory.update_result("TASK-001", {"status": "in_progress"})

        # Second update - should preserve status
        self.factory.update_result("TASK-001", {"notes": "New note"})

        result_path = Path(self.temp_dir) / "TASK-001" / "result.json"
        data = json.loads(result_path.read_text())

        self.assertEqual(data["status"], "in_progress")
        self.assertEqual(data["notes"], "New note")
        self.assertEqual(data["task_title"], "Original Title")

    def test_thought_content_escaping(self):
        """Test that special characters in thoughts are handled."""
        self.factory.create_workspace("TASK-001", "Test")

        thought_content = "Thought with <html> & \"quotes\" and 'apostrophes'"
        thought_file = self.factory.add_thought("TASK-001", thought_content)

        content = thought_file.read_text()
        self.assertIn(thought_content, content)


if __name__ == "__main__":
    unittest.main()
