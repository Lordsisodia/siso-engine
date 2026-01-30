"""
Episodic Memory Module for Enhanced Memory System

This module provides episode-based memory that:
- Links related tasks, decisions, and outcomes
- Enables "what happened when we did X?" queries
- Tracks relationships across conversations
- Supports temporal organization
"""

from .Episode import Episode
from .EpisodicMemory import EpisodicMemory, create_episodic_memory

__all__ = [
    'Episode',
    'EpisodicMemory',
    'create_episodic_memory',
]
