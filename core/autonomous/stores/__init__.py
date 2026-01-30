"""
Task storage backends for autonomous agent system.

Supports multiple storage strategies:
- JSON files: Development, git-tracked
- SQLite: Production, ACID-compliant
"""

from .json_store import JSONTaskStore
from .sqlite_store import SQLiteTaskStore

__all__ = ['JSONTaskStore', 'SQLiteTaskStore']
