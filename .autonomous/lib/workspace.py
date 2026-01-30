#!/usr/bin/env python3
"""
Workspace Factory

Creates and manages per-task workspaces for isolated execution.
Adapted from Blackbox5 Task Registry.
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Union, Optional, Dict, Any
import json


class WorkspaceFactory:
    """Creates and manages per-task workspaces."""

    def __init__(self, base_path: Union[str, Path] = ".Autonomous/workspaces"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_workspace(self, task_id: str, task_title: str, context_files: Optional[list] = None) -> Path:
        """
        Create a new workspace for a task.

        Args:
            task_id: Task identifier
            task_title: Human-readable task title
            context_files: List of files to copy to context/

        Returns:
            Path to the created workspace
        """
        workspace_path = self.base_path / task_id
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Create directory structure
        (workspace_path / "timeline").mkdir(exist_ok=True)
        (workspace_path / "thoughts").mkdir(exist_ok=True)
        (workspace_path / "context").mkdir(exist_ok=True)
        (workspace_path / "work").mkdir(exist_ok=True)

        # Create initial timeline entry
        self._add_timeline_entry(
            workspace_path,
            "created",
            {"task_id": task_id, "task_title": task_title}
        )

        # Copy context files if provided
        if context_files:
            for file_path in context_files:
                src = Path(file_path)
                if src.exists():
                    dst = workspace_path / "context" / src.name
                    dst.write_text(src.read_text())

        # Create empty result.json
        result_path = workspace_path / "result.json"
        result_path.write_text(json.dumps({
            "task_id": task_id,
            "task_title": task_title,
            "status": "created",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "deliverables": [],
            "notes": ""
        }, indent=2))

        # Create README in workspace
        readme_path = workspace_path / "README.md"
        readme_path.write_text(f"""# Workspace: {task_id}

## Task: {task_title}

## Directory Structure

- **timeline/**: State transition history
- **thoughts/**: Agent thought dumps and analysis
- **context/**: Task context materials (PRDs, requirements, etc.)
- **work/**: Work in progress (code, drafts, etc.)
- **result.json**: Final output when task is complete

## Workflow

1. Review context materials in `context/`
2. Add analysis to `thoughts/` as you work
3. Place work in progress in `work/`
4. When complete, update `result.json` with final output
5. Mark task as complete via CLI

## Timeline

See `timeline/` for state transition history.
""")

        return workspace_path

    def get_workspace_path(self, task_id: str) -> Path:
        """Get the path to a task's workspace."""
        return self.base_path / task_id

    def workspace_exists(self, task_id: str) -> bool:
        """Check if a workspace exists for a task."""
        return (self.base_path / task_id).exists()

    def update_result(self, task_id: str, result_data: Dict[str, Any]) -> None:
        """Update the result.json for a task."""
        result_path = self.base_path / task_id / "result.json"
        if result_path.exists():
            current = json.loads(result_path.read_text())
            current.update(result_data)
            current["updated_at"] = datetime.now(timezone.utc).isoformat()
            result_path.write_text(json.dumps(current, indent=2))

    def add_thought(self, task_id: str, thought: str, category: str = "analysis") -> Path:
        """Add a thought to the workspace."""
        thoughts_dir = self.base_path / task_id / "thoughts"
        thoughts_dir.mkdir(exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        thought_file = thoughts_dir / f"{category}_{timestamp}.md"

        thought_file.write_text(f"""# {category.title()} Thought

**Time:** {datetime.now(timezone.utc).isoformat()}
**Task:** {task_id}

---

{thought}
""")

        return thought_file

    def _add_timeline_entry(self, workspace_path: Path, event: str, data: Dict[str, Any]) -> None:
        """Add an entry to the workspace timeline."""
        timeline_dir = workspace_path / "timeline"
        timeline_dir.mkdir(exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        entry_file = timeline_dir / f"{timestamp}_{event}.json"

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "data": data
        }

        entry_file.write_text(json.dumps(entry, indent=2))


def create_workspace_for_task(task_id: str, task_title: str, autonomous_root: Optional[Path] = None) -> Path:
    """Convenience function to create workspace for a task."""
    if autonomous_root is None:
        autonomous_root = Path(__file__).parent.parent

    factory = WorkspaceFactory(autonomous_root / "workspaces")
    return factory.create_workspace(task_id, task_title)


if __name__ == "__main__":
    # Test
    factory = WorkspaceFactory("./test-workspaces")

    workspace = factory.create_workspace(
        "TASK-TEST-001",
        "Test task for workspace factory"
    )

    print(f"Created workspace: {workspace}")
    print(f"Contents:")
    for item in workspace.rglob("*"):
        if item.is_file():
            print(f"  {item.relative_to(workspace)}")

    # Add a thought
    thought_file = factory.add_thought("TASK-TEST-001", "This is a test thought about the task.")
    print(f"\nAdded thought: {thought_file}")

    # Update result
    factory.update_result("TASK-TEST-001", {
        "status": "in_progress",
        "notes": "Making good progress"
    })
    print("\nUpdated result.json")
