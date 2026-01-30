#!/usr/bin/env python3
"""
Unit tests for Task State Machine

Tests the task state transition and dependency management system.
Run with: python3 -m unittest test_state_machine -v
"""

import unittest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from state_machine import (
    TaskState, StateTransitionError, Task, TaskStateMachine,
    can_start_task, get_next_available_task
)


class TestTaskState(unittest.TestCase):
    """Test TaskState enum."""

    def test_state_values(self):
        """Test state enum values."""
        self.assertEqual(TaskState.PENDING.value, "pending")
        self.assertEqual(TaskState.IN_PROGRESS.value, "in_progress")
        self.assertEqual(TaskState.COMPLETED.value, "completed")
        self.assertEqual(TaskState.BLOCKED.value, "blocked")


class TestTask(unittest.TestCase):
    """Test Task dataclass."""

    def test_task_creation(self):
        """Test creating a task."""
        task = Task(
            id="TASK-001",
            title="Test Task",
            state=TaskState.PENDING,
            dependencies=["TASK-000"]
        )

        self.assertEqual(task.id, "TASK-001")
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.state, TaskState.PENDING)
        self.assertEqual(task.dependencies, ["TASK-000"])

    def test_task_with_timestamps(self):
        """Test task with timestamps."""
        now = datetime.now().isoformat()

        task = Task(
            id="TASK-001",
            title="Test",
            state=TaskState.COMPLETED,
            dependencies=[],
            created_at=now,
            started_at=now,
            completed_at=now
        )

        self.assertEqual(task.created_at, now)
        self.assertEqual(task.started_at, now)
        self.assertEqual(task.completed_at, now)


class TestTaskStateMachine(unittest.TestCase):
    """Test TaskStateMachine class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create some test tasks
        self.tasks = {
            "TASK-001": Task("TASK-001", "First Task", TaskState.PENDING, []),
            "TASK-002": Task("TASK-002", "Second Task", TaskState.PENDING, ["TASK-001"]),
            "TASK-003": Task("TASK-003", "Third Task", TaskState.PENDING, ["TASK-001", "TASK-002"]),
            "TASK-004": Task("TASK-004", "Blocked Task", TaskState.BLOCKED, ["TASK-005"]),
        }
        self.sm = TaskStateMachine(self.tasks)

    def test_init_with_tasks(self):
        """Test initialization with tasks."""
        self.assertEqual(len(self.sm.tasks), 4)
        self.assertIn("TASK-001", self.sm.tasks)

    def test_init_empty(self):
        """Test initialization with empty tasks."""
        sm = TaskStateMachine()
        self.assertEqual(len(sm.tasks), 0)

    def test_can_transition_valid(self):
        """Test valid state transition."""
        can, reason = self.sm.can_transition("TASK-001", TaskState.IN_PROGRESS)
        self.assertTrue(can)
        self.assertIsNone(reason)

    def test_can_transition_invalid(self):
        """Test invalid state transition."""
        # Can't go from PENDING to COMPLETED directly
        can, reason = self.sm.can_transition("TASK-001", TaskState.COMPLETED)
        self.assertFalse(can)
        self.assertIn("Cannot transition", reason)

    def test_can_transition_nonexistent_task(self):
        """Test transition for non-existent task."""
        can, reason = self.sm.can_transition("TASK-999", TaskState.IN_PROGRESS)
        self.assertFalse(can)
        self.assertIn("not found", reason)

    def test_can_transition_blocked_by_dependencies(self):
        """Test that blocked task can't start."""
        can, reason = self.sm.can_transition("TASK-002", TaskState.IN_PROGRESS)
        self.assertFalse(can)
        self.assertIn("TASK-001", reason)

    def test_transition_success(self):
        """Test successful state transition."""
        task = self.sm.transition("TASK-001", TaskState.IN_PROGRESS)
        self.assertEqual(task.state, TaskState.IN_PROGRESS)
        self.assertIsNotNone(task.started_at)

    def test_transition_with_force(self):
        """Test forced transition bypassing validation."""
        # Force transition even though dependencies not met
        task = self.sm.transition("TASK-002", TaskState.IN_PROGRESS, force=True)
        self.assertEqual(task.state, TaskState.IN_PROGRESS)

    def test_transition_invalid_raises_error(self):
        """Test that invalid transition raises error."""
        with self.assertRaises(StateTransitionError) as cm:
            self.sm.transition("TASK-001", TaskState.COMPLETED)
        self.assertIn("Cannot transition", str(cm.exception))

    def test_transition_updates_timestamps(self):
        """Test that transitions update timestamps."""
        task = self.sm.transition("TASK-001", TaskState.IN_PROGRESS)
        self.assertIsNotNone(task.started_at)

        task = self.sm.transition("TASK-001", TaskState.COMPLETED)
        self.assertIsNotNone(task.completed_at)

    def test_transition_to_completed_notifies_dependents(self):
        """Test that completing a task unblocks dependents."""
        # Create a proper test scenario
        tasks = {
            "TASK-001": Task("TASK-001", "T1", TaskState.PENDING, []),
            "TASK-002": Task("TASK-002", "T2", TaskState.BLOCKED, ["TASK-001"]),
        }
        sm = TaskStateMachine(tasks)

        # Complete TASK-001 (need to go through IN_PROGRESS)
        sm.transition("TASK-001", TaskState.IN_PROGRESS, force=True)
        sm.transition("TASK-001", TaskState.COMPLETED)

        # TASK-002 should now be PENDING (unblocked)
        self.assertEqual(sm.tasks["TASK-002"].state, TaskState.PENDING)

    def test_get_available_tasks(self):
        """Test getting tasks that can be started."""
        available = self.sm.get_available_tasks()
        # Only TASK-001 has no dependencies
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0].id, "TASK-001")

    def test_get_available_tasks_after_completion(self):
        """Test available tasks after dependency is completed."""
        # Complete TASK-001
        self.sm.tasks["TASK-001"].state = TaskState.COMPLETED

        available = self.sm.get_available_tasks()
        # Now TASK-002 should be available
        available_ids = [t.id for t in available]
        self.assertIn("TASK-002", available_ids)

    def test_get_blocked_tasks(self):
        """Test getting blocked tasks with reasons."""
        blocked = self.sm.get_blocked_tasks()
        # TASK-002, TASK-003, TASK-004 are all blocked
        self.assertGreaterEqual(len(blocked), 1)

        # Check that we get reasons
        for task, reason in blocked:
            self.assertIsNotNone(task)
            self.assertIsNotNone(reason)

    def test_load_from_yaml(self):
        """Test loading tasks from YAML format."""
        yaml_tasks = [
            {
                "id": "TASK-001",
                "name": "First",
                "status": "completed",
                "dependencies": {"requires": []}
            },
            {
                "id": "TASK-002",
                "name": "Second",
                "status": "pending",
                "dependencies": {"requires": ["TASK-001"]}
            }
        ]

        sm = TaskStateMachine()
        sm.load_from_yaml(yaml_tasks)

        self.assertEqual(len(sm.tasks), 2)
        self.assertEqual(sm.tasks["TASK-001"].state, TaskState.COMPLETED)
        self.assertEqual(sm.tasks["TASK-002"].state, TaskState.PENDING)
        self.assertEqual(sm.tasks["TASK-002"].dependencies, ["TASK-001"])

    def test_completed_is_terminal(self):
        """Test that COMPLETED state has no outgoing transitions."""
        # This is implicit in VALID_TRANSITIONS
        self.assertEqual(TaskStateMachine.VALID_TRANSITIONS[TaskState.COMPLETED], [])

    def test_blocked_to_pending_transition(self):
        """Test BLOCKED can transition to PENDING."""
        # A blocked task can become pending when unblocked
        can, reason = self.sm.can_transition("TASK-004", TaskState.PENDING)
        self.assertTrue(can)

    def test_in_progress_to_blocked(self):
        """Test IN_PROGRESS can transition to BLOCKED."""
        # Create a task in progress
        self.sm.tasks["TASK-001"].state = TaskState.IN_PROGRESS

        # Can block it if needed
        can, reason = self.sm.can_transition("TASK-001", TaskState.BLOCKED)
        self.assertTrue(can)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def test_can_start_task(self):
        """Test can_start_task convenience function."""
        tasks = [
            {"id": "TASK-001", "name": "First", "status": "completed", "dependencies": {"requires": []}},
            {"id": "TASK-002", "name": "Second", "status": "pending", "dependencies": {"requires": ["TASK-001"]}}
        ]

        can, reason = can_start_task("TASK-002", tasks)
        self.assertTrue(can)
        self.assertIsNone(reason)

    def test_can_start_task_blocked(self):
        """Test can_start_task for blocked task."""
        tasks = [
            {"id": "TASK-001", "name": "First", "status": "pending", "dependencies": {"requires": []}},
            {"id": "TASK-002", "name": "Second", "status": "pending", "dependencies": {"requires": ["TASK-001"]}}
        ]

        can, reason = can_start_task("TASK-002", tasks)
        self.assertFalse(can)
        self.assertIn("TASK-001", reason)

    def test_get_next_available_task(self):
        """Test get_next_available_task convenience function."""
        tasks = [
            {"id": "TASK-001", "name": "First", "status": "pending", "dependencies": {"requires": []}},
            {"id": "TASK-002", "name": "Second", "status": "pending", "dependencies": {"requires": ["TASK-001"]}}
        ]

        next_task = get_next_available_task(tasks)
        self.assertIsNotNone(next_task)
        self.assertEqual(next_task["id"], "TASK-001")

    def test_get_next_available_task_none(self):
        """Test get_next_available_task when none available."""
        tasks = [
            {"id": "TASK-001", "name": "First", "status": "pending", "dependencies": {"requires": ["TASK-002"]}},
            {"id": "TASK-002", "name": "Second", "status": "pending", "dependencies": {"requires": ["TASK-001"]}}
        ]

        next_task = get_next_available_task(tasks)
        self.assertIsNone(next_task)


class TestStateTransitionEdgeCases(unittest.TestCase):
    """Test edge cases for state transitions."""

    def test_circular_dependencies(self):
        """Test handling of circular dependencies."""
        tasks = {
            "TASK-001": Task("TASK-001", "T1", TaskState.PENDING, ["TASK-002"]),
            "TASK-002": Task("TASK-002", "T2", TaskState.PENDING, ["TASK-001"]),
        }
        sm = TaskStateMachine(tasks)

        # Neither should be available due to circular dependency
        available = sm.get_available_tasks()
        self.assertEqual(len(available), 0)

    def test_self_dependency(self):
        """Test handling of self-dependency."""
        tasks = {
            "TASK-001": Task("TASK-001", "T1", TaskState.PENDING, ["TASK-001"]),
        }
        sm = TaskStateMachine(tasks)

        can, reason = sm.can_transition("TASK-001", TaskState.IN_PROGRESS)
        self.assertFalse(can)

    def test_missing_dependency(self):
        """Test handling of missing dependency."""
        tasks = {
            "TASK-001": Task("TASK-001", "T1", TaskState.PENDING, ["TASK-999"]),
        }
        sm = TaskStateMachine(tasks)

        can, reason = sm.can_transition("TASK-001", TaskState.IN_PROGRESS)
        self.assertFalse(can)
        self.assertIn("not found", reason)


if __name__ == "__main__":
    unittest.main()
