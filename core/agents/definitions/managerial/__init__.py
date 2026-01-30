"""
BlackBox5 Managerial Agent Package

A comprehensive system for managing teams of AI agents with Vibe Kanban integration.
"""

from .skills.vibe_kanban_manager import (
    VibeKanbanManager,
    TaskStatus,
    Priority,
    TaskInfo,
    AgentState,
    Repository,
    ManagementMetrics,
    create_manager,
    quick_status
)

from .memory.management_memory import (
    ManagementMemory,
    EventType,
    Event,
    TaskHistory,
    AgentPerformance,
    DependencyGraph,
    get_management_memory
)

from .task_lifecycle import (
    TaskLifecycleManager,
    TaskPlan,
    ExecutionResult,
    LifecycleStage,
    get_lifecycle_manager
)

from .skills.team_dashboard import (
    TeamDashboard,
    AlertLevel,
    Alert,
    AgentStatus,
    QueueStatus,
    ResourceMetrics,
    get_dashboard,
    show_dashboard,
    watch_dashboard
)

__all__ = [
    # Vibe Kanban Manager
    "VibeKanbanManager",
    "TaskStatus",
    "Priority",
    "TaskInfo",
    "AgentState",
    "Repository",
    "ManagementMetrics",
    "create_manager",
    "quick_status",

    # Management Memory
    "ManagementMemory",
    "EventType",
    "Event",
    "TaskHistory",
    "AgentPerformance",
    "DependencyGraph",
    "get_management_memory",

    # Task Lifecycle
    "TaskLifecycleManager",
    "TaskPlan",
    "ExecutionResult",
    "LifecycleStage",
    "get_lifecycle_manager",

    # Team Dashboard
    "TeamDashboard",
    "AlertLevel",
    "Alert",
    "AgentStatus",
    "QueueStatus",
    "ResourceMetrics",
    "get_dashboard",
    "show_dashboard",
    "watch_dashboard",
]

__version__ = "1.0.0"
