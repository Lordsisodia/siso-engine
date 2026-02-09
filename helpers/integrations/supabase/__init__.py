"""
Supabase Integration for BlackBox5
===================================

This module provides integration with Supabase service.

Usage:
    >>> from integration.supabase import SupabaseManager
    >>> manager = SupabaseManager()
    >>> await manager.query("users", filters={"status": "active"})
"""

from .manager import SupabaseManager

__all__ = ["SupabaseManager"]

__version__ = "1.0.0"
