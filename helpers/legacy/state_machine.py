#!/usr/bin/env python3
"""
Task State Machine

Validates task state transitions and dependency resolution.
Adapted from Blackbox5 Task Registry.
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime


class TaskState(Enum):
    """Valid task states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


@dataclass
class Task:
    """Simple task representation."""
    id: str
    title: str
    state: TaskState
    dependencies: List[str]
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class TaskStateMachine:
    """
    Manages task state transitions.

    Valid transitions:
        PENDING -> IN_PROGRESS (if deps met)
        PENDING -> BLOCKED
        IN_PROGRESS -> COMPLETED
        IN_PROGRESS -> BLOCKED
        BLOCKED -> PENDING (when unblocked)
    """

    # Valid state transitions
    VALID_TRANSITIONS = {
        TaskState.PENDING: [TaskState.IN_PROGRESS, TaskState.BLOCKED],
        TaskState.IN_PROGRESS: [TaskState.COMPLETED, TaskState.BLOCKED],
        TaskState.BLOCKED: [TaskState.PENDING],
        TaskState.COMPLETED: []  # Terminal state
    }

    def __init__(self, tasks: Optional[Dict[str, Task]] = None):
        """
        Initialize state machine.

        Args:
            tasks: Dictionary of task_id -> Task
        """
        self.tasks = tasks or {}

    def can_transition(
        self,
        task_id: str,
        new_state: TaskState
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a state transition is valid.

        Args:
            task_id: Task to transition
            new_state: Desired new state

        Returns:
            (can_transition, reason_if_not)
        """
        task = self.tasks.get(task_id)
        if not task:
            return False, f"Task {task_id} not found"

        current_state = task.state

        # Check if transition is valid
        if new_state not in self.VALID_TRANSITIONS.get(current_state, []):
            return False, f"Cannot transition from {current_state.value} to {new_state.value}"

        # Additional checks for specific transitions
        if new_state == TaskState.IN_PROGRESS:
            # Check dependencies
            deps_met, reason = self._check_dependencies(task)
            if not deps_met:
                return False, reason

        return True, None

    def transition(
        self,
        task_id: str,
        new_state: TaskState,
        force: bool = False
    ) -> Task:
        """
        Execute a state transition.

        Args:
            task_id: Task to transition
            new_state: New state
            force: Skip validation (use with caution)

        Returns:
            Updated Task

        Raises:
            StateTransitionError: If transition is invalid
        """
        if not force:
            can_transition, reason = self.can_transition(task_id, new_state)
            if not can_transition:
                raise StateTransitionError(reason)

        task = self.tasks[task_id]
        old_state = task.state
        task.state = new_state

        # Update timestamps
        timestamp = datetime.now().isoformat()
        if new_state == TaskState.IN_PROGRESS:
            task.started_at = timestamp
        elif new_state == TaskState.COMPLETED:
            task.completed_at = timestamp

        # Update dependent tasks
        if new_state == TaskState.COMPLETED:
            self._notify_dependents(task_id)

        return task

    def _check_dependencies(self, task: Task) -> Tuple[bool, Optional[str]]:
        """Check if all dependencies are completed."""
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task:
                return False, f"Dependency {dep_id} not found"
            if dep_task.state != TaskState.COMPLETED:
                return False, f"Blocked by {dep_id} ({dep_task.state.value})"
        return True, None

    def _notify_dependents(self, completed_task_id: str) -> None:
        """Notify tasks that depend on the completed task."""
        for task in self.tasks.values():
            if completed_task_id in task.dependencies:
                if task.state == TaskState.BLOCKED:
                    # Check if now unblocked
                    can_start, _ = self._check_dependencies(task)
                    if can_start:
                        task.state = TaskState.PENDING

    def get_available_tasks(self) -> List[Task]:
        """Get tasks that can be started (pending, deps met)."""
        available = []
        for task in self.tasks.values():
            if task.state == TaskState.PENDING:
                deps_met, _ = self._check_dependencies(task)
                if deps_met:
                    available.append(task)
        return available

    def get_blocked_tasks(self) -> List[Tuple[Task, str]]:
        """Get blocked tasks with reasons."""
        blocked = []
        for task in self.tasks.values():
            if task.state == TaskState.BLOCKED:
                _, reason = self._check_dependencies(task)
                blocked.append((task, reason or "Unknown blocker"))
        return blocked

    def load_from_yaml(self, tasks_yaml: List[Dict[str, Any]]) -> None:
        """Load tasks from our YAML format."""
        for task_data in tasks_yaml:
            task = Task(
                id=task_data["id"],
                title=task_data.get("name", "Untitled"),
                state=TaskState(task_data.get("status", "pending")),
                dependencies=task_data.get("dependencies", {}).get("requires", []),
                created_at=task_data.get("created_at")
            )
            self.tasks[task.id] = task


# Convenience functions for single-task operations
def can_start_task(task_id: str, all_tasks: List[Dict]) -> Tuple[bool, str]:
    """Check if a task can be started."""
    sm = TaskStateMachine()
    sm.load_from_yaml(all_tasks)
    return sm.can_transition(task_id, TaskState.IN_PROGRESS)


def get_next_available_task(all_tasks: List[Dict]) -> Optional[Dict]:
    """Get the next task that can be started."""
    sm = TaskStateMachine()
    sm.load_from_yaml(all_tasks)

    available = sm.get_available_tasks()
    if not available:
        return None

    # Return first available (could add priority sorting here)
    task = available[0]
    return {
        "id": task.id,
        "name": task.title,
        "status": task.state.value
    }


if __name__ == "__main__":
    # Test
    tasks = [
        {"id": "TASK-001", "name": "First task", "status": "completed"},
        {"id": "TASK-002", "name": "Second task", "status": "pending",
         "dependencies": {"requires": ["TASK-001"]}},
        {"id": "TASK-003", "name": "Third task", "status": "pending",
         "dependencies": {"requires": ["TASK-002"]}},
    ]

    sm = TaskStateMachine()
    sm.load_from_yaml(tasks)

    print("Available tasks:", [t.id for t in sm.get_available_tasks()])
    # Should show TASK-002

    can_start, reason = sm.can_transition("TASK-002", TaskState.IN_PROGRESS)
    print(f"Can start TASK-002: {can_start}")

    can_start, reason = sm.can_transition("TASK-003", TaskState.IN_PROGRESS)
    print(f"Can start TASK-003: {can_start}, reason: {reason}")
    # Should be blocked by TASK-002
