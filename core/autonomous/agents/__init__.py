"""
Autonomous system agents.

Core agent types:
- Supervisor: Creates and manages tasks
- Autonomous: Claims and executes tasks
- Interface: User liaison and reporting
"""

from .supervisor import SupervisorAgent, TaskBreakdown
from .autonomous import AutonomousAgent, AutonomousAgentPool
from .interface import InterfaceAgent

__all__ = [
    'SupervisorAgent',
    'TaskBreakdown',
    'AutonomousAgent',
    'AutonomousAgentPool',
    'InterfaceAgent',
]
