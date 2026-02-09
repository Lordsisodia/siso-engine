# BlackBox5 Agent Framework
"""
Framework infrastructure for BlackBox5 agents.

This package provides:
- BaseAgent: Abstract base class for all agents
- AgentLoader: Dynamic agent loading from Python and YAML
- SkillManager: Skill registration and execution
- TaskSchema: Task validation schemas
"""

from .base_agent import BaseAgent, AgentConfig, AgentState
from .agent_loader import AgentLoader
from .skill_manager import SkillManager
from .task_schema import TaskSchema, TaskValidationError

__all__ = [
    "BaseAgent",
    "AgentConfig",
    "AgentState",
    "AgentLoader",
    "SkillManager",
    "TaskSchema",
    "TaskValidationError",
]
