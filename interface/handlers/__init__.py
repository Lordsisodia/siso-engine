"""
Agent Output Bus Handlers

This package contains handlers for the AgentOutputBus.
Each handler receives parsed agent outputs and routes them to appropriate systems.
"""

# Import handlers that are always available
from .database_handler import DatabaseHandler
from .notification_handler import NotificationHandler

# Import handlers that may have dependencies
try:
    from .vibe_handler import VibeKanbanHandler
    _vibe_available = True
except (ImportError, NameError):
    _vibe_available = False
    VibeKanbanHandler = None

try:
    from .scheduler_handler import SchedulerHandler
    _scheduler_available = True
except (ImportError, NameError):
    _scheduler_available = False
    SchedulerHandler = None

__all__ = [
    "DatabaseHandler",
    "NotificationHandler",
]

if _vibe_available:
    __all__.append("VibeKanbanHandler")

if _scheduler_available:
    __all__.append("SchedulerHandler")
