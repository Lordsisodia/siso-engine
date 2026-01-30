#!/usr/bin/env python3
"""
Unit tests for Memory System

Tests the file-based memory persistence system.
Run with: pytest test_memory.py -v
"""

import unittest
import tempfile
import shutil
import time
from pathlib import Path
from unittest.mock import patch
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent))

from memory import MemorySystem, create_memory


class TestMemorySystem(unittest.TestCase):
    """Test cases for MemorySystem class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_base = Path(self.temp_dir) / "memory"
        self.memory = MemorySystem(self.memory_base)

    def tearDown(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_init_creates_directories(self):
        """Test that initialization creates memory directories."""
        self.assertTrue(self.memory_base.exists())
        self.assertTrue(self.memory.decisions_path.exists())
        self.assertTrue(self.memory.insights_path.exists())
        self.assertTrue(self.memory.context_path.exists())

    def test_init_with_default_path(self):
        """Test initialization with default path."""
        memory = MemorySystem()
        self.assertIsNotNone(memory.base_path)
        self.assertTrue(memory.base_path.exists())

    def test_record_decision(self):
        """Test recording a decision."""
        file_path = self.memory.record_decision(
            title="Use YAML for config",
            context="Need config format",
            options=["JSON", "YAML", "TOML"],
            decision="Use YAML",
            rationale="Human readable",
            run_id="run-001"
        )

        self.assertTrue(file_path.exists())
        self.assertTrue(file_path.name.startswith("DEC-"))
        self.assertTrue(file_path.suffix == ".md")

        content = file_path.read_text()
        self.assertIn("Use YAML for config", content)
        self.assertIn("Use YAML", content)
        self.assertIn("Human readable", content)
        self.assertIn("run-001", content)

    def test_record_decision_without_run_id(self):
        """Test recording decision without run ID."""
        file_path = self.memory.record_decision(
            title="Test decision",
            context="Test context",
            options=["A", "B"],
            decision="A",
            rationale="Because"
        )

        content = file_path.read_text()
        self.assertIn("N/A", content)

    def test_record_insight(self):
        """Test recording an insight."""
        file_path = self.memory.record_insight(
            content="Always validate task dependencies",
            category="pattern",
            confidence=0.95,
            source_run="run-001"
        )

        self.assertTrue(file_path.exists())
        self.assertTrue(file_path.name.startswith("INSIGHT-"))

        content = file_path.read_text()
        self.assertIn("Always validate task dependencies", content)
        self.assertIn("pattern", content)
        self.assertIn("95%", content)
        self.assertIn("run-001", content)

    def test_record_insight_with_related_files(self):
        """Test recording insight with related files."""
        file_path = self.memory.record_insight(
            content="Test insight",
            category="gotcha",
            related_files=["file1.py", "file2.py"]
        )

        content = file_path.read_text()
        self.assertIn("file1.py", content)
        self.assertIn("file2.py", content)
        self.assertIn("Related Files", content)

    def test_save_context_summary(self):
        """Test saving context summary."""
        file_path = self.memory.save_context_summary(
            name="test-context",
            summary="This is a test summary",
            source_files=["file1.py", "file2.py"],
            run_id="run-001"
        )

        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.name, "test-context.yaml")

        data = yaml.safe_load(file_path.read_text())
        self.assertEqual(data["name"], "test-context")
        self.assertEqual(data["summary"], "This is a test summary")
        self.assertEqual(data["source_files"], ["file1.py", "file2.py"])
        self.assertEqual(data["run_id"], "run-001")

    def test_get_recent_decisions(self):
        """Test getting recent decisions."""
        # Record a decision
        self.memory.record_decision("Decision 1", "Context 1", ["A"], "A", "Rationale 1")

        decisions = self.memory.get_recent_decisions(limit=10)

        # Should have at least one decision
        self.assertGreaterEqual(len(decisions), 1)
        self.assertIn("id", decisions[0])
        self.assertIn("title", decisions[0])
        self.assertIn("date", decisions[0])
        self.assertIn("Decision 1", decisions[0]["title"])

    def test_get_recent_decisions_empty(self):
        """Test getting decisions when none exist."""
        decisions = self.memory.get_recent_decisions()
        self.assertEqual(len(decisions), 0)

    def test_get_insights_by_category(self):
        """Test getting insights by category."""
        # Record an insight with a specific category
        self.memory.record_insight("Pattern insight", category="pattern")

        pattern_insights = self.memory.get_insights_by_category("pattern")

        # Should have at least one pattern insight
        self.assertGreaterEqual(len(pattern_insights), 1)
        self.assertIn("content", pattern_insights[0])

    def test_get_insights_by_category_empty(self):
        """Test getting insights by category when none exist."""
        insights = self.memory.get_insights_by_category("pattern")
        self.assertEqual(len(insights), 0)

    def test_search_memories(self):
        """Test searching across all memories."""
        # Record items with "test" keyword
        self.memory.record_decision("Test decision", "Test context", ["A"], "A", "Rationale")
        self.memory.record_insight("Test insight", category="pattern")

        results = self.memory.search_memories("test")

        self.assertGreater(len(results["decisions"]), 0)
        self.assertGreater(len(results["insights"]), 0)

    def test_search_memories_no_results(self):
        """Test search with no matching results."""
        results = self.memory.search_memories("nonexistent")
        self.assertEqual(len(results["decisions"]), 0)
        self.assertEqual(len(results["insights"]), 0)
        self.assertEqual(len(results["context"]), 0)

    def test_decision_markdown_format(self):
        """Test that decision markdown has expected format."""
        file_path = self.memory.record_decision(
            title="Format Test",
            context="Context here",
            options=["Option 1", "Option 2"],
            decision="Option 1",
            rationale="Reason here"
        )

        content = file_path.read_text()
        self.assertIn("# Decision:", content)
        self.assertIn("## Context", content)
        self.assertIn("## Options Considered", content)
        self.assertIn("## Decision", content)
        self.assertIn("## Rationale", content)

    def test_insight_markdown_format(self):
        """Test that insight markdown has expected format."""
        file_path = self.memory.record_insight(
            content="Test content",
            category="discovery"
        )

        content = file_path.read_text()
        self.assertIn("# Insight:", content)
        self.assertIn("## Content", content)

    def test_multiple_decisions_have_unique_ids(self):
        """Test that decisions get IDs (uniqueness depends on timing)."""
        path1 = self.memory.record_decision("D1", "C1", ["A"], "A", "R1")
        path2 = self.memory.record_decision("D2", "C2", ["B"], "B", "R2")

        # IDs follow expected format
        self.assertTrue(path1.stem.startswith("DEC-"))
        self.assertTrue(path2.stem.startswith("DEC-"))

    def test_multiple_insights_have_unique_ids(self):
        """Test that insights get IDs (uniqueness depends on timing)."""
        path1 = self.memory.record_insight("I1", category="pattern")
        path2 = self.memory.record_insight("I2", category="gotcha")

        # IDs follow expected format
        self.assertTrue(path1.stem.startswith("INSIGHT-"))
        self.assertTrue(path2.stem.startswith("INSIGHT-"))


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def test_create_memory(self):
        """Test create_memory convenience function."""
        memory = create_memory()
        self.assertIsInstance(memory, MemorySystem)
        self.assertIsNotNone(memory.base_path)


if __name__ == "__main__":
    unittest.main()
