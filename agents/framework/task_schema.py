"""
Task data structures for autonomous agent system.

Based on research from LangGraph, CrewAI, Temporal, and Plandex.
Production-ready task tracking with state management, dependencies, and metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4


class TaskState(Enum):
    """Task lifecycle states

    Based on production state machines from Temporal and LangGraph.
    """
    BACKLOG = "backlog"         # Not yet scheduled
    PENDING = "pending"         # Ready to be claimed
    ASSIGNED = "assigned"       # Claimed by agent
    ACTIVE = "active"          # Agent is working
    PAUSED = "paused"          # Waiting for input
    REVIEW = "review"          # Under review
    APPROVED = "approved"       # Ready to merge
    DONE = "done"              # Complete
    FAILED = "failed"          # Execution failed
    CANCELLED = "cancelled"    # Cancelled


@dataclass
class TaskMetrics:
    """Metrics for task analysis

    Tracks execution time, resource usage, and quality metrics.
    """
    # Execution time
    cycle_time: Optional[float] = None      # Total time (created → done)
    wait_time: Optional[float] = None        # Time until started
    work_time: Optional[float] = None        # Actual work time

    # Resource usage
    token_usage: int = 0
    api_calls: int = 0
    cpu_time: float = 0.0

    # Quality metrics
    success_rate: float = 1.0
    error_count: int = 0
    retry_count: int = 0

    # Agent performance
    agent_id: Optional[str] = None
    agent_performance: Dict[str, float] = field(default_factory=dict)

    def calculate(self, task: 'Task'):
        """Calculate metrics from task"""
        if task.completed_at and task.created_at:
            self.cycle_time = (task.completed_at - task.created_at).total_seconds()

        if task.started_at and task.created_at:
            self.wait_time = (task.started_at - task.created_at).total_seconds()

        if task.completed_at and task.started_at:
            self.work_time = (task.completed_at - task.started_at).total_seconds()

        if task.state == TaskState.DONE:
            self.success_rate = 1.0
        elif task.state == TaskState.FAILED:
            self.success_rate = 0.0

        self.agent_id = task.assignee


@dataclass
class Task:
    """Production-ready task tracking

    Combines best practices from:
    - LangGraph: State management
    - CrewAI: Task delegation
    - Temporal: Event sourcing
    - Plandex: Version control integration
    """

    # Identity
    id: str = field(default_factory=lambda: f"task-{uuid4()}")
    title: str = ""
    description: str = ""

    # Classification
    type: str = "general"              # Task type (development, testing, etc.)
    priority: int = 5                  # 1-10, higher is more important
    tags: List[str] = field(default_factory=list)

    # State
    state: TaskState = TaskState.BACKLOG
    assignee: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Monitoring
    monitored_at: Optional[datetime] = None  # Last time task was reviewed/checked
    monitored_by: Optional[str] = None       # Who last monitored it
    monitor_notes: Optional[str] = None      # Notes from monitoring

    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)

    # Execution
    retry_count: int = 0
    max_retries: int = 3
    error_log: List[str] = field(default_factory=list)

    # Checkpointing (for resumable workflows)
    checkpoint_data: Dict[str, Any] = field(default_factory=dict)
    checkpoint_timestamp: Optional[datetime] = None

    # Result
    result: Optional[Dict[str, Any]] = None
    artifacts: List[str] = field(default_factory=list)  # Files/commits created

    # Metrics
    metrics: TaskMetrics = field(default_factory=TaskMetrics)

    # Schema version (for evolution)
    schema_version: str = "2.0"

    def can_transition_to(self, new_state: TaskState) -> bool:
        """Check if state transition is valid"""
        valid_transitions = {
            TaskState.BACKLOG: [TaskState.PENDING],
            TaskState.PENDING: [TaskState.ASSIGNED, TaskState.CANCELLED],
            TaskState.ASSIGNED: [TaskState.ACTIVE, TaskState.CANCELLED],
            TaskState.ACTIVE: [TaskState.DONE, TaskState.FAILED, TaskState.PAUSED],
            TaskState.PAUSED: [TaskState.ACTIVE, TaskState.CANCELLED],
            TaskState.FAILED: [TaskState.PENDING],  # Can retry
            TaskState.DONE: [],  # Terminal
            TaskState.CANCELLED: [],  # Terminal
            TaskState.REVIEW: [TaskState.APPROVED, TaskState.CANCELLED],
            TaskState.APPROVED: [TaskState.DONE],
        }

        return new_state in valid_transitions.get(self.state, [])

    def transition_to(self, new_state: TaskState):
        """Transition to new state"""
        if not self.can_transition_to(new_state):
            raise ValueError(f"Invalid transition: {self.state} → {new_state}")

        old_state = self.state
        self.state = new_state

        # Update timestamps
        if new_state == TaskState.ASSIGNED and not self.assigned_at:
            self.assigned_at = datetime.now()
        elif new_state == TaskState.ACTIVE and not self.started_at:
            self.started_at = datetime.now()
        elif new_state == TaskState.DONE and not self.completed_at:
            self.completed_at = datetime.now()

        return old_state

    def add_error(self, error: str):
        """Add error to log"""
        self.error_log.append(f"[{datetime.now().isoformat()}] {error}")
        self.retry_count += 1

    def save_checkpoint(self, data: Dict[str, Any]):
        """Save checkpoint data for resumable workflows"""
        self.checkpoint_data = data
        self.checkpoint_timestamp = datetime.now()

    def is_available_for(self, agent_id: str, capabilities: List[str]) -> bool:
        """Check if task is available for this agent"""
        if self.state != TaskState.PENDING:
            return False

        if self.type not in capabilities:
            return False

        # Check if dependencies are satisfied
        deps_satisfied = True
        # Note: In production, this would check against task registry

        return deps_satisfied

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.type,
            "priority": self.priority,
            "tags": self.tags,
            "state": self.state.value,
            "assignee": self.assignee,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "monitored_at": self.monitored_at.isoformat() if self.monitored_at else None,
            "monitored_by": self.monitored_by,
            "monitor_notes": self.monitor_notes,
            "depends_on": self.depends_on,
            "blocks": self.blocks,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_log": self.error_log,
            "checkpoint_data": self.checkpoint_data,
            "checkpoint_timestamp": self.checkpoint_timestamp.isoformat() if self.checkpoint_timestamp else None,
            "result": self.result,
            "artifacts": self.artifacts,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create Task from dictionary"""
        task = cls(
            id=data.get("id", f"task-{uuid4()}"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            type=data.get("type", "general"),
            priority=data.get("priority", 5),
            tags=data.get("tags", []),
            state=TaskState(data.get("state", TaskState.BACKLOG.value)),
            assignee=data.get("assignee"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            assigned_at=datetime.fromisoformat(data["assigned_at"]) if data.get("assigned_at") else None,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            monitored_at=datetime.fromisoformat(data["monitored_at"]) if data.get("monitored_at") else None,
            monitored_by=data.get("monitored_by"),
            monitor_notes=data.get("monitor_notes"),
            depends_on=data.get("depends_on", []),
            blocks=data.get("blocks", []),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            error_log=data.get("error_log", []),
            checkpoint_data=data.get("checkpoint_data", {}),
            checkpoint_timestamp=datetime.fromisoformat(data["checkpoint_timestamp"]) if data.get("checkpoint_timestamp") else None,
            result=data.get("result"),
            artifacts=data.get("artifacts", []),
        )
        return task


# ============ TASK REGISTRY ============

class TaskRegistry:
    """Central task registry with multiple backend support"""

    def __init__(self, backend: str = "json"):
        """
        Initialize task registry.

        Args:
            backend: Storage backend ("json", "sqlite", "postgres")
        """
        self.backend = backend
        self._tasks: Dict[str, Task] = {}

        if backend == "json":
            from .stores.json_store import JSONTaskStore
            self.store = JSONTaskStore()
        elif backend == "sqlite":
            from .stores.sqlite_store import SQLiteTaskStore
            self.store = SQLiteTaskStore()
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def create(self, **kwargs) -> Task:
        """Create new task"""
        task = Task(**kwargs)
        self._tasks[task.id] = task
        self.store.save(task)
        return task

    def get(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        if task_id not in self._tasks:
            # Try loading from store
            task = self.store.load(task_id)
            if task:
                self._tasks[task_id] = task
                return task
        return self._tasks.get(task_id)

    def update(self, task: Task):
        """Update task"""
        self._tasks[task.id] = task
        self.store.save(task)

    def get_all(self) -> List[Task]:
        """Get all tasks"""
        # Load from store if cache is empty
        if not self._tasks:
            self._tasks = {t.id: t for t in self.store.load_all()}
        return list(self._tasks.values())

    def get_available(self, agent_id: str, capabilities: List[str]) -> List[Task]:
        """Get tasks available for this agent"""
        available = []

        for task in self.get_all():
            if task.is_available_for(agent_id, capabilities):
                available.append(task)

        # Sort by priority
        available.sort(key=lambda t: t.priority, reverse=True)
        return available

    def delete(self, task_id: str):
        """Delete task"""
        if task_id in self._tasks:
            del self._tasks[task_id]
        self.store.delete(task_id)
