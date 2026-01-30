#!/usr/bin/env python3
"""
Tests for Obsidian Integration
===============================

Unit tests for the Obsidian exporter functionality.

Usage:
    python test_obsidian.py
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from integration.obsidian import ObsidianExporter
from integration.obsidian.types import (
    ContextData,
    InsightData,
    NoteType,
    PlanData,
    SessionData,
    Wikilink,
)


def test_folder_creation():
    """Test that folders are created correctly."""
    print("Testing folder creation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        exporter = ObsidianExporter(
            vault_path=temp_dir,
            create_folders=True,
        )

        base_path = Path(temp_dir) / "blackbox5"
        assert base_path.exists(), "Base folder should exist"

        for note_type in NoteType:
            folder = base_path / exporter.SUBFOLDERS[note_type]
            assert folder.exists(), f"{note_type} folder should exist"

    print("  PASSED: Folders created correctly")


def test_session_export():
    """Test exporting a session."""
    print("Testing session export...")

    with tempfile.TemporaryDirectory() as temp_dir:
        exporter = ObsidianExporter(vault_path=temp_dir)

        session_data = SessionData(
            agent_id="test_agent",
            agent_name="TestAgent",
            session_id="test_session",
            start_time=datetime.now(),
            goal="Test goal",
            outcome="Test outcome",
            tags=["test"],
        )

        result = exporter.export_session(session_data)

        assert result.success, "Export should succeed"
        assert result.file_path, "Should have file path"
        assert result.note_type == NoteType.SESSION, "Should be session type"

        # Check file exists
        assert os.path.exists(result.file_path), "File should exist"

        # Check file content
        with open(result.file_path, "r") as f:
            content = f.read()
            assert "TestAgent" in content, "Agent name should be in content"
            assert "test goal" in content.lower(), "Goal should be in content"

    print("  PASSED: Session export works")


def test_insight_export():
    """Test exporting an insight."""
    print("Testing insight export...")

    with tempfile.TemporaryDirectory() as temp_dir:
        exporter = ObsidianExporter(vault_path=temp_dir)

        insight_data = InsightData(
            title="Test Insight",
            content="This is a test insight",
            category="Test",
            tags=["test", "insight"],
        )

        result = exporter.export_insight(insight_data)

        assert result.success, "Export should succeed"
        assert result.file_path, "Should have file path"
        assert result.note_type == NoteType.INSIGHT, "Should be insight type"

        # Check file exists
        assert os.path.exists(result.file_path), "File should exist"

        # Check file content
        with open(result.file_path, "r") as f:
            content = f.read()
            assert "Test Insight" in content, "Title should be in content"
            assert "test insight" in content, "Content should be in file"

    print("  PASSED: Insight export works")


def test_context_export():
    """Test exporting context."""
    print("Testing context export...")

    with tempfile.TemporaryDirectory() as temp_dir:
        exporter = ObsidianExporter(vault_path=temp_dir)

        context_data = ContextData(
            agent_id="test_agent",
            agent_name="TestAgent",
            context_type="working",
            content="Test context content",
            tags=["test", "context"],
        )

        result = exporter.export_context(context_data)

        assert result.success, "Export should succeed"
        assert result.file_path, "Should have file path"
        assert result.note_type == NoteType.CONTEXT, "Should be context type"

        # Check file exists
        assert os.path.exists(result.file_path), "File should exist"

    print("  PASSED: Context export works")


def test_plan_export():
    """Test exporting a plan."""
    print("Testing plan export...")

    with tempfile.TemporaryDirectory() as temp_dir:
        exporter = ObsidianExporter(vault_path=temp_dir)

        plan_data = PlanData(
            title="Test Plan",
            description="A test plan",
            steps=[
                {"title": "Step 1", "description": "First step", "status": "pending"},
                {"title": "Step 2", "description": "Second step", "status": "pending"},
            ],
            tags=["test", "plan"],
        )

        result = exporter.export_plan(plan_data)

        assert result.success, "Export should succeed"
        assert result.file_path, "Should have file path"
        assert result.note_type == NoteType.PLAN, "Should be plan type"

        # Check file exists
        assert os.path.exists(result.file_path), "File should exist"

        # Check steps are in content
        with open(result.file_path, "r") as f:
            content = f.read()
            assert "Step 1" in content, "Step 1 should be in content"
            assert "Step 2" in content, "Step 2 should be in content"

    print("  PASSED: Plan export works")


def test_index_generation():
    """Test index generation."""
    print("Testing index generation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        exporter = ObsidianExporter(vault_path=temp_dir)

        # Export some notes first
        session = SessionData(
            agent_id="test",
            agent_name="Test",
            session_id="test1",
            start_time=datetime.now(),
            goal="Test",
        )
        exporter.export_session(session)

        insight = InsightData(title="Test Insight", content="Content")
        exporter.export_insight(insight)

        # Generate index
        result = exporter.generate_index()

        assert result.success, "Index generation should succeed"
        assert result.file_path, "Should have file path"
        assert os.path.exists(result.file_path), "Index file should exist"

        # Check index content
        with open(result.file_path, "r") as f:
            content = f.read()
            assert "BlackBox5 Notes Index" in content, "Should have title"
            assert "Sessions" in content or "session" in content.lower(), "Should mention sessions"

    print("  PASSED: Index generation works")


def test_wikilinks():
    """Test wikilink generation."""
    print("Testing wikilinks...")

    # Simple link
    link1 = Wikilink(title="My Note")
    assert link1.to_markdown() == "[[My Note]]", "Simple link should work"

    # Link with alias
    link2 = Wikilink(title="My Note", alias="Short")
    assert link2.to_markdown() == "[[My Note|Short]]", "Link with alias should work"

    # Link with section
    link3 = Wikilink(title="My Note", section="Summary")
    assert link3.to_markdown() == "[[My Note#Summary]]", "Link with section should work"

    # Link with alias and section
    link4 = Wikilink(title="My Note", alias="Short", section="Summary")
    assert link4.to_markdown() == "[[My Note#Summary|Short]]", "Full link should work"

    print("  PASSED: Wikilinks work correctly")


def test_related_notes():
    """Test that related notes are included."""
    print("Testing related notes...")

    with tempfile.TemporaryDirectory() as temp_dir:
        exporter = ObsidianExporter(vault_path=temp_dir)

        insight = InsightData(
            title="Test Insight",
            content="Content",
            related_notes=["Related Note", "Another Note"],
        )

        result = exporter.export_insight(insight)

        assert result.success, "Export should succeed"

        with open(result.file_path, "r") as f:
            content = f.read()
            assert "[[Related Note]]" in content, "Should have wikilink"
            assert "[[Another Note]]" in content, "Should have second wikilink"
            assert "Related Notes" in content, "Should have section header"

    print("  PASSED: Related notes are included")


def test_filename_generation():
    """Test that filenames are generated correctly."""
    print("Testing filename generation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        exporter = ObsidianExporter(vault_path=temp_dir)

        # Export with specific date
        test_date = datetime(2025, 1, 19, 10, 30)
        insight = InsightData(
            title="Test Insight with Special Characters!@#",
            content="Content",
            created_at=test_date,
        )

        result = exporter.export_insight(insight)
        filename = os.path.basename(result.file_path)

        # Check format: insight-YYYY-MM-DD-title.md
        assert filename.startswith("insight-2025-01-19-"), "Should have correct date format"
        assert filename.endswith(".md"), "Should be markdown file"
        assert "test-insight-with-special-characters" in filename.lower(), "Should have sanitized title"

    print("  PASSED: Filenames generated correctly")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Obsidian Integration Test Suite")
    print("=" * 60)
    print()

    try:
        test_folder_creation()
        test_session_export()
        test_insight_export()
        test_context_export()
        test_plan_export()
        test_index_generation()
        test_wikilinks()
        test_related_notes()
        test_filename_generation()

        print()
        print("=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
        return True

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"TEST FAILED: {e}")
        print("=" * 60)
        return False
    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
