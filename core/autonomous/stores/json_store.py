"""
JSON file-based task store for development and testing.

Simple, git-tracked task persistence.
Ideal for development and small-scale deployments (<1K tasks).
"""

import json
import os
from pathlib import Path
from typing import List, Optional
from ..schemas.task import Task


class JSONTaskStore:
    """JSON file-based task storage"""

    def __init__(self, storage_path: str = "tasks/data"):
        """
        Initialize JSON task store.

        Args:
            storage_path: Directory to store task files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Index file for fast lookups
        self.index_file = self.storage_path / "index.json"
        self._index = self._load_index()

    def _load_index(self) -> dict:
        """Load task index"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_index(self):
        """Save task index"""
        with open(self.index_file, 'w') as f:
            json.dump(self._index, f, indent=2)

    def _get_task_path(self, task_id: str) -> Path:
        """Get file path for task"""
        return self.storage_path / f"{task_id}.json"

    def save(self, task: Task):
        """
        Save task to JSON file.

        Args:
            task: Task object to save
        """
        task_path = self._get_task_path(task.id)

        # Save task data
        with open(task_path, 'w') as f:
            json.dump(task.to_dict(), f, indent=2)

        # Update index
        self._index[task.id] = {
            "id": task.id,
            "title": task.title,
            "state": task.state.value,
            "type": task.type,
            "priority": task.priority,
            "assignee": task.assignee,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }
        self._save_index()

    def load(self, task_id: str) -> Optional[Task]:
        """
        Load task from JSON file.

        Args:
            task_id: Task ID to load

        Returns:
            Task object or None if not found
        """
        task_path = self._get_task_path(task_id)

        if not task_path.exists():
            return None

        with open(task_path, 'r') as f:
            data = json.load(f)

        return Task.from_dict(data)

    def load_all(self) -> List[Task]:
        """
        Load all tasks from storage.

        Returns:
            List of all tasks
        """
        tasks = []

        for task_id in self._index.keys():
            task = self.load(task_id)
            if task:
                tasks.append(task)

        return tasks

    def delete(self, task_id: str):
        """
        Delete task from storage.

        Args:
            task_id: Task ID to delete
        """
        # Remove task file
        task_path = self._get_task_path(task_id)
        if task_path.exists():
            task_path.unlink()

        # Remove from index
        if task_id in self._index:
            del self._index[task_id]
            self._save_index()

    def query(self, **filters) -> List[Task]:
        """
        Query tasks by filters.

        Args:
            **filters: Field=value pairs to filter by

        Returns:
            List of matching tasks
        """
        tasks = self.load_all()
        results = []

        for task in tasks:
            match = True
            task_dict = task.to_dict()

            for key, value in filters.items():
                if key not in task_dict:
                    match = False
                    break

                if task_dict[key] != value:
                    match = False
                    break

            if match:
                results.append(task)

        return results

    def get_by_state(self, state: str) -> List[Task]:
        """
        Get all tasks in a specific state.

        Args:
            state: Task state value

        Returns:
            List of tasks in the given state
        """
        return self.query(state=state)

    def get_by_assignee(self, assignee: str) -> List[Task]:
        """
        Get all tasks assigned to an agent.

        Args:
            assignee: Agent ID

        Returns:
            List of tasks assigned to the agent
        """
        return self.query(assignee=assignee)

    def get_by_type(self, task_type: str) -> List[Task]:
        """
        Get all tasks of a specific type.

        Args:
            task_type: Task type

        Returns:
            List of tasks of the given type
        """
        return self.query(type=task_type)
