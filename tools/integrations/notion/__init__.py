"""
Notion Integration for BlackBox5
=================================

This module provides integration with Notion service.

Usage:
    >>> from integration.notion import NotionManager
    >>> manager = NotionManager()
    >>> await manager.create_page(parent_id, properties, children)
"""

from .manager import NotionManager

__all__ = ["NotionManager"]

__version__ = "1.0.0"
