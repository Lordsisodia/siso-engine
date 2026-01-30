import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Constants
MEMORY_ROOT = "~/.blackbox5/5-project-memory/blackbox5/tasks"

@dataclass
class SubTask:
    id: str
    title: str
    description: str
    status: str  # pending, in_progress, completed, failed
    complexity: str
    created_at: str
    subtasks: List[str]  # IDs of children

@dataclass
class FractalTask:
    id: str
    objective: str
    root_path: str
    created_at: str
    status: str
    current_depth: int
    max_depth: int
    subtasks: List[SubTask]
    history: List[Dict[str, Any]]

class TaskStorage:
    def __init__(self, root_path: str = MEMORY_ROOT):
        self.root_path = Path(root_path)
        self.root_path.mkdir(parents=True, exist_ok=True)

    def _get_task_dir(self, task_id: str) -> Path:
        return self.root_path / task_id

    def create_task(self, task_id: str, objective: str, max_depth: int = 3) -> FractalTask:
        task_dir = self._get_task_dir(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        
        task = FractalTask(
            id=task_id,
            objective=objective,
            root_path=str(task_dir),
            created_at=datetime.utcnow().isoformat(),
            status="initialized",
            current_depth=0,
            max_depth=max_depth,
            subtasks=[],
            history=[]
        )
        self.save_task(task)
        return task

    def save_task(self, task: FractalTask):
        task_dir = Path(task.root_path)
        file_path = task_dir / "state.json"
        with open(file_path, "w") as f:
            json.dump(asdict(task), f, indent=2)

    def load_task(self, task_id: str) -> Optional[FractalTask]:
        task_dir = self._get_task_dir(task_id)
        file_path = task_dir / "state.json"
        
        if not file_path.exists():
            return None
            
        with open(file_path, "r") as f:
            data = json.load(f)
            
        # Reconstruct objects
        subtasks_data = data.pop("subtasks", [])
        subtasks = [SubTask(**st) for st in subtasks_data]
        
        return FractalTask(subtasks=subtasks, **data)

    def append_history(self, task_id: str, entry: Dict[str, Any]):
        task = self.load_task(task_id)
        if task:
            task.history.append({
                "timestamp": datetime.utcnow().isoformat(),
                **entry
            })
            self.save_task(task)
            
            # Also append to a readable markdown log
            log_path = self._get_task_dir(task_id) / "history.md"
            with open(log_path, "a") as f:
                f.write(f"\n## {entry.get('action', 'Update')} - {datetime.utcnow().isoformat()}\n")
                f.write(f"{entry.get('details', '')}\n")
