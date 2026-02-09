import json
import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Import path resolution library
lib_dir = Path(__file__).parent.parent.parent.parent / ".autonomous" / "lib"
if str(lib_dir) not in sys.path:
    sys.path.insert(0, str(lib_dir))

try:
    from paths import get_path_resolver
    _resolver = get_path_resolver()
    MEMORY_ROOT = str(_resolver.get_tasks_path())
except ImportError:
    # Fallback to default
    MEMORY_ROOT = "~/.blackbox5/5-project-memory/blackbox5/tasks"

# Import caching layer
try:
    from storage.cache_manager import CacheManager, FileCache, MemoryCache
    _CACHE_AVAILABLE = True
except ImportError:
    _CACHE_AVAILABLE = False

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
    def __init__(self, root_path: str = MEMORY_ROOT, enable_caching: bool = True):
        self.root_path = Path(root_path).expanduser()
        self.root_path.mkdir(parents=True, exist_ok=True)

        # Initialize caching layer
        self._caching_enabled = enable_caching and _CACHE_AVAILABLE
        if self._caching_enabled:
            cache_root = str(Path(root_path).parent / ".cache")
            self._cache = CacheManager(cache_root)
        else:
            self._cache = None

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

        # Invalidate cache after save
        if self._caching_enabled and self._cache:
            self._cache.invalidate_file(str(file_path))

    def load_task(self, task_id: str) -> Optional[FractalTask]:
        task_dir = self._get_task_dir(task_id)
        file_path = task_dir / "state.json"

        def _load_raw():
            """Load raw JSON data from file."""
            if not file_path.exists():
                return None
            with open(file_path, "r") as f:
                return json.load(f)

        def _build_task(data):
            """Build FractalTask from raw data."""
            if data is None:
                return None
            subtasks_data = data.pop("subtasks", [])
            subtasks = [SubTask(**st) for st in subtasks_data]
            return FractalTask(subtasks=subtasks, **data)

        # Use file-based caching if enabled
        if self._caching_enabled and self._cache:
            raw_data = self._cache.get_file_cached(str(file_path), _load_raw)
            # Make a copy to avoid modifying cached data
            if raw_data is not None:
                import copy
                raw_data = copy.deepcopy(raw_data)
            return _build_task(raw_data)

        raw_data = _load_raw()
        return _build_task(raw_data)

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

    def list_tasks(self) -> List[str]:
        """List all task IDs with directory scan caching."""
        def _scan():
            return [d.name for d in self.root_path.iterdir() if d.is_dir()]

        if self._caching_enabled and self._cache:
            return self._cache.get_task_scan_cached(str(self.root_path), _scan)

        return _scan()

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics if caching is enabled."""
        if self._caching_enabled and self._cache:
            return self._cache.get_stats()
        return None

    def clear_cache(self) -> None:
        """Clear all caches."""
        if self._caching_enabled and self._cache:
            self._cache.clear_all()
