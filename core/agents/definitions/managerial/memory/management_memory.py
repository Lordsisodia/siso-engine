#!/usr/bin/env python3
"""
Management Memory System for BlackBox5

This system provides persistent memory for the managerial agent to track:
- Task states and history
- Agent activities and performance
- Merge decisions and outcomes
- Dependencies and blockers
- Team coordination events
- Metrics and trends over time
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import pickle


class EventType(Enum):
    """Types of events to track"""
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_BLOCKED = "task_blocked"
    AGENT_SPAWNED = "agent_spawned"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    MERGE_ATTEMPTED = "merge_attempted"
    MERGE_SUCCEEDED = "merge_succeeded"
    MERGE_FAILED = "merge_failed"
    REVIEW_REQUESTED = "review_requested"
    REVIEW_COMPLETED = "review_completed"
    BLOCKER_RESOLVED = "blocker_resolved"
    DEPENDENCY_ADDED = "dependency_added"
    DEPENDENCY_REMOVED = "dependency_removed"


@dataclass
class Event:
    """A management event"""
    event_type: EventType
    timestamp: str
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary, handling Enums"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        return data


@dataclass
class TaskHistory:
    """Complete history of a task"""
    task_id: str
    title: str
    created_at: str
    events: List[Event] = field(default_factory=list)
    final_status: Optional[str] = None
    completion_time: Optional[str] = None
    total_duration: Optional[float] = None  # seconds
    agent_performance: Dict[str, Any] = field(default_factory=dict)
    merge_info: Dict[str, Any] = field(default_factory=dict)

    def add_event(self, event: Event):
        """Add an event to history"""
        self.events.append(event)

    def to_dict(self) -> Dict:
        """Convert to dictionary, handling Event objects"""
        data = asdict(self)
        # Convert Event objects to dicts
        data['events'] = [e.to_dict() for e in self.events]
        return data


@dataclass
class AgentPerformance:
    """Performance tracking for agents"""
    task_id: str
    executor: str
    started_at: str
    completed_at: Optional[str] = None
    duration: Optional[float] = None
    success: bool = False
    files_modified: int = 0
    files_created: int = 0
    lines_changed: int = 0
    errors: List[str] = field(default_factory=list)
    quality_score: Optional[float] = None  # 0-1


@dataclass
class DependencyGraph:
    """Track task dependencies"""
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # task_id -> [depends_on]
    dependents: Dict[str, List[str]] = field(default_factory=dict)  # task_id -> [blocks]

    def add_dependency(self, task_id: str, depends_on: str):
        """Add a dependency relationship"""
        if task_id not in self.dependencies:
            self.dependencies[task_id] = []
        if depends_on not in self.dependencies[task_id]:
            self.dependencies[task_id].append(depends_on)

        if depends_on not in self.dependents:
            self.dependents[depends_on] = []
        if task_id not in self.dependents[depends_on]:
            self.dependents[depends_on].append(task_id)

    def remove_dependency(self, task_id: str, depends_on: str):
        """Remove a dependency relationship"""
        if task_id in self.dependencies and depends_on in self.dependencies[task_id]:
            self.dependencies[task_id].remove(depends_on)

        if depends_on in self.dependents and task_id in self.dependents[depends_on]:
            self.dependents[depends_on].remove(task_id)

    def get_blockers(self, task_id: str) -> List[str]:
        """Get tasks blocking this task"""
        blockers = []
        for dep in self.dependencies.get(task_id, []):
            blockers.append(dep)
        return blockers

    def get_blocked_by(self, task_id: str) -> List[str]:
        """Get tasks blocked by this task"""
        return self.dependents.get(task_id, [])


class ManagementMemory:
    """
    Persistent memory system for managerial agent.

    Stores all events, histories, and state for comprehensive
    task and agent tracking.
    """

    def __init__(
        self,
        memory_path: str = "~/.blackbox5/5-project-memory/management"
    ):
        """
        Initialize management memory

        Args:
            memory_path: Path to store memory data
        """
        self.memory_path = Path(memory_path)
        self.memory_path.mkdir(parents=True, exist_ok=True)

        # Data structures
        self._events: List[Event] = []
        self._task_histories: Dict[str, TaskHistory] = {}
        self._agent_performance: Dict[str, AgentPerformance] = {}
        self._dependency_graph = DependencyGraph()
        self._merge_decisions: Dict[str, Any] = {}
        self._metrics_history: List[Dict[str, Any]] = []

        # Load existing memory
        self._load()

    # =========================================================================
    # EVENT TRACKING
    # =========================================================================

    def record_event(
        self,
        event_type: EventType,
        task_id: Optional[str] = None,
        task_title: Optional[str] = None,
        **details
    ) -> Event:
        """
        Record a management event

        Args:
            event_type: Type of event
            task_id: Related task ID
            task_title: Related task title
            **details: Additional event details

        Returns:
            Event object
        """
        event = Event(
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id=task_id,
            task_title=task_title,
            details=details
        )

        self._events.append(event)

        # Add to task history if applicable
        if task_id and task_id in self._task_histories:
            self._task_histories[task_id].add_event(event)

        self._save()
        return event

    def get_events(
        self,
        event_type: Optional[EventType] = None,
        task_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get events with optional filtering

        Args:
            event_type: Filter by event type
            task_id: Filter by task ID
            limit: Maximum number of events

        Returns:
            List of events
        """
        events = self._events

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if task_id:
            events = [e for e in events if e.task_id == task_id]

        # Return most recent first
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    # =========================================================================
    # TASK HISTORY
    # =========================================================================

    def create_task_history(
        self,
        task_id: str,
        title: str,
        created_at: Optional[str] = None
    ) -> TaskHistory:
        """Create a new task history"""
        history = TaskHistory(
            task_id=task_id,
            title=title,
            created_at=created_at or datetime.now(timezone.utc).isoformat()
        )

        self._task_histories[task_id] = history
        self._save()
        return history

    def get_task_history(self, task_id: str) -> Optional[TaskHistory]:
        """Get task history"""
        return self._task_histories.get(task_id)

    def complete_task(
        self,
        task_id: str,
        final_status: str,
        completion_time: Optional[str] = None
    ):
        """Mark task as completed"""
        if task_id in self._task_histories:
            history = self._task_histories[task_id]
            history.final_status = final_status
            history.completion_time = completion_time or datetime.now(timezone.utc).isoformat()

            # Calculate duration
            created = datetime.fromisoformat(history.created_at.replace('Z', '+00:00'))
            completed = datetime.fromisoformat(history.completion_time.replace('Z', '+00:00'))
            history.total_duration = (completed - created).total_seconds()

            self._save()

    # =========================================================================
    # AGENT PERFORMANCE
    # =========================================================================

    def track_agent_start(
        self,
        task_id: str,
        executor: str
    ) -> AgentPerformance:
        """Start tracking agent performance"""
        perf = AgentPerformance(
            task_id=task_id,
            executor=executor,
            started_at=datetime.now(timezone.utc).isoformat()
        )

        self._agent_performance[task_id] = perf
        self._save()
        return perf

    def track_agent_completion(
        self,
        task_id: str,
        success: bool,
        files_modified: int = 0,
        files_created: int = 0,
        lines_changed: int = 0,
        errors: Optional[List[str]] = None
    ):
        """Record agent completion"""
        if task_id not in self._agent_performance:
            return

        perf = self._agent_performance[task_id]
        perf.completed_at = datetime.now(timezone.utc).isoformat()
        perf.success = success
        perf.files_modified = files_modified
        perf.files_created = files_created
        perf.lines_changed = lines_changed

        if errors:
            perf.errors = errors

        # Calculate duration
        started = datetime.fromisoformat(perf.started_at.replace('Z', '+00:00'))
        completed = datetime.fromisoformat(perf.completed_at.replace('Z', '+00:00'))
        perf.duration = (completed - started).total_seconds()

        # Calculate quality score (simple heuristic)
        if success:
            base_score = 1.0
            # Reduce for errors
            error_penalty = len(perf.errors) * 0.1
            perf.quality_score = max(0.0, base_score - error_penalty)
        else:
            perf.quality_score = 0.0

        self._save()

    def get_agent_performance(self, task_id: str) -> Optional[AgentPerformance]:
        """Get agent performance data"""
        return self._agent_performance.get(task_id)

    def get_agent_stats(self, executor: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregate agent statistics"""
        perfs = list(self._agent_performance.values())

        if executor:
            perfs = [p for p in perfs if p.executor == executor]

        if not perfs:
            return {}

        return {
            "total": len(perfs),
            "successful": sum(1 for p in perfs if p.success),
            "failed": sum(1 for p in perfs if not p.success),
            "avg_duration": sum(p.duration or 0 for p in perfs) / len(perfs),
            "avg_quality": sum(p.quality_score or 0 for p in perfs) / len(perfs),
            "total_files_modified": sum(p.files_modified for p in perfs),
            "total_files_created": sum(p.files_created for p in perfs)
        }

    # =========================================================================
    # DEPENDENCY TRACKING
    # =========================================================================

    def add_dependency(self, task_id: str, depends_on: str):
        """Add a dependency"""
        self._dependency_graph.add_dependency(task_id, depends_on)
        self.record_event(
            EventType.DEPENDENCY_ADDED,
            task_id=task_id,
            depends_on=depends_on
        )
        self._save()

    def remove_dependency(self, task_id: str, depends_on: str):
        """Remove a dependency"""
        self._dependency_graph.remove_dependency(task_id, depends_on)
        self.record_event(
            EventType.DEPENDENCY_REMOVED,
            task_id=task_id,
            depends_on=depends_on
        )
        self._save()

    def get_blockers(self, task_id: str) -> List[str]:
        """Get tasks blocking this task"""
        return self._dependency_graph.get_blockers(task_id)

    def get_blocked_by(self, task_id: str) -> List[str]:
        """Get tasks blocked by this task"""
        return self._dependency_graph.get_blocked_by(task_id)

    # =========================================================================
    # MERGE TRACKING
    # =========================================================================

    def record_merge_attempt(
        self,
        task_id: str,
        branch: str,
        merge_method: str = "merge"
    ):
        """Record a merge attempt"""
        self._merge_decisions[task_id] = {
            "attempted_at": datetime.now(timezone.utc).isoformat(),
            "branch": branch,
            "method": merge_method,
            "status": "attempted"
        }
        self.record_event(
            EventType.MERGE_ATTEMPTED,
            task_id=task_id,
            branch=branch,
            method=merge_method
        )
        self._save()

    def record_merge_success(
        self,
        task_id: str,
        commit_hash: Optional[str] = None
    ):
        """Record successful merge"""
        if task_id in self._merge_decisions:
            self._merge_decisions[task_id].update({
                "status": "succeeded",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "commit_hash": commit_hash
            })
        self.record_event(
            EventType.MERGE_SUCCEEDED,
            task_id=task_id,
            commit_hash=commit_hash
        )
        self._save()

    def record_merge_failure(
        self,
        task_id: str,
        error: str
    ):
        """Record failed merge"""
        if task_id in self._merge_decisions:
            self._merge_decisions[task_id].update({
                "status": "failed",
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "error": error
            })
        self.record_event(
            EventType.MERGE_FAILED,
            task_id=task_id,
            error=error
        )
        self._save()

    # =========================================================================
    # METRICS HISTORY
    # =========================================================================

    def record_metrics(self, metrics: Dict[str, Any]):
        """Record metrics snapshot"""
        metrics["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._metrics_history.append(metrics)
        self._save()

    def get_metrics_history(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get metrics history"""
        return self._metrics_history[-limit:]

    # =========================================================================
    # REPORTING
    # =========================================================================

    def generate_management_report(self) -> str:
        """Generate comprehensive management report"""
        report = ["# Management Memory Report"]
        report.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        report.append("")

        # Recent events
        report.append("## Recent Events")
        for event in self.get_events(limit=20):
            report.append(f"- {event.timestamp}: {event.event_type.value}")
            if event.task_title:
                report.append(f"  Task: {event.task_title}")
        report.append("")

        # Agent performance
        report.append("## Agent Performance")
        stats = self.get_agent_stats()
        if stats:
            report.append(f"- Total executions: {stats['total']}")
            report.append(f"- Success rate: {stats['successful']}/{stats['total']}")
            report.append(f"- Average duration: {stats['avg_duration']:.1f}s")
            report.append(f"- Average quality: {stats['avg_quality']:.2f}")
        report.append("")

        # Pending merges
        report.append("## Pending Merges")
        for task_id, merge_info in self._merge_decisions.items():
            if merge_info["status"] in ["attempted", "failed"]:
                report.append(f"- Task {task_id}: {merge_info['status']}")
        report.append("")

        return "\n".join(report)

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def _save(self):
        """Save memory to disk"""
        # Save events
        with open(self.memory_path / "events.json", 'w') as f:
            json.dump([e.to_dict() for e in self._events], f, indent=2)

        # Save task histories
        with open(self.memory_path / "task_histories.json", 'w') as f:
            json.dump(
                {k: v.to_dict() for k, v in self._task_histories.items()},
                f,
                indent=2,
                default=str  # Handle datetime and other non-serializable types
            )

        # Save agent performance
        with open(self.memory_path / "agent_performance.json", 'w') as f:
            json.dump(
                {k: asdict(v) for k, v in self._agent_performance.items()},
                f,
                indent=2
            )

        # Save dependency graph
        with open(self.memory_path / "dependency_graph.json", 'w') as f:
            json.dump({
                "dependencies": self._dependency_graph.dependencies,
                "dependents": self._dependency_graph.dependents
            }, f, indent=2)

        # Save merge decisions
        with open(self.memory_path / "merge_decisions.json", 'w') as f:
            json.dump(self._merge_decisions, f, indent=2)

        # Save metrics history
        with open(self.memory_path / "metrics_history.json", 'w') as f:
            json.dump(self._metrics_history, f, indent=2)

    def _load(self):
        """Load memory from disk"""
        # Load events
        events_file = self.memory_path / "events.json"
        if events_file.exists():
            with open(events_file) as f:
                events_data = json.load(f)
                self._events = [
                    Event(
                        event_type=EventType(e["event_type"]),
                        timestamp=e["timestamp"],
                        task_id=e.get("task_id"),
                        task_title=e.get("task_title"),
                        details=e.get("details", {})
                    )
                    for e in events_data
                ]

        # Load task histories
        histories_file = self.memory_path / "task_histories.json"
        if histories_file.exists():
            with open(histories_file) as f:
                histories_data = json.load(f)
                for task_id, history_data in histories_data.items():
                    history = TaskHistory(
                        task_id=history_data["task_id"],
                        title=history_data["title"],
                        created_at=history_data["created_at"],
                        final_status=history_data.get("final_status"),
                        completion_time=history_data.get("completion_time"),
                        total_duration=history_data.get("total_duration")
                    )
                    # Restore events
                    for event_data in history_data.get("events", []):
                        event = Event(
                            event_type=EventType(event_data["event_type"]),
                            timestamp=event_data["timestamp"],
                            task_id=event_data.get("task_id"),
                            task_title=event_data.get("task_title"),
                            details=event_data.get("details", {})
                        )
                        history.events.append(event)
                    self._task_histories[task_id] = history

        # Load agent performance
        perf_file = self.memory_path / "agent_performance.json"
        if perf_file.exists():
            with open(perf_file) as f:
                perf_data = json.load(f)
                for task_id, agent_perf in perf_data.items():
                    self._agent_performance[task_id] = AgentPerformance(**agent_perf)

        # Load dependency graph
        dep_file = self.memory_path / "dependency_graph.json"
        if dep_file.exists():
            with open(dep_file) as f:
                dep_data = json.load(f)
                self._dependency_graph.dependencies = dep_data.get("dependencies", {})
                self._dependency_graph.dependents = dep_data.get("dependents", {})

        # Load merge decisions
        merge_file = self.memory_path / "merge_decisions.json"
        if merge_file.exists():
            with open(merge_file) as f:
                self._merge_decisions = json.load(f)

        # Load metrics history
        metrics_file = self.memory_path / "metrics_history.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                self._metrics_history = json.load(f)

    def clear(self):
        """Clear all memory"""
        self._events = []
        self._task_histories = {}
        self._agent_performance = {}
        self._dependency_graph = DependencyGraph()
        self._merge_decisions = {}
        self._metrics_history = []
        self._save()


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_memory_instance: Optional[ManagementMemory] = None


def get_management_memory() -> ManagementMemory:
    """Get the singleton management memory instance"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = ManagementMemory()
    return _memory_instance


if __name__ == "__main__":
    # Test
    memory = get_management_memory()
    print(memory.generate_management_report())
