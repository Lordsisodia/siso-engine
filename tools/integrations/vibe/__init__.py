"""
Vibe Kanban Integration for BlackBox5
======================================

Provides Vibe Kanban card management following CCPM's GitHub patterns.
"""

from .VibeKanbanManager import (
    CardData,
    CardSpec,
    CardStatus,
    Column,
    CommentData,
    STATUS_TO_COLUMN,
    VibeKanbanManager,
)

__all__ = [
    "VibeKanbanManager",
    "CardData",
    "CardSpec",
    "CardStatus",
    "Column",
    "CommentData",
    "STATUS_TO_COLUMN",
]
