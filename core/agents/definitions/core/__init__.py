"""
Core Agent Infrastructure

This module provides the foundational classes for the Blackbox 5 agent system:
- BaseAgent: Abstract base class for all agents
- AgentLoader: Dynamic agent loading and registration
- SkillManager: Skill discovery and management
"""

from .base_agent import BaseAgent, AgentTask, AgentConfig, AgentResult
from .agent_loader import AgentLoader
from .skill_manager import SkillManager, Skill

__all__ = [
    'BaseAgent',
    'AgentTask',
    'AgentConfig',
    'AgentResult',
    'AgentLoader',
    'SkillManager',
    'Skill',
]
