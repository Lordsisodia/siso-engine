"""
Vercel Integration for BlackBox5
=================================

This module provides integration with Vercel deployment service.

Usage:
    >>> from integration.vercel import VercelManager
    >>> manager = VercelManager()
    >>> await manager.create_deployment(...)
"""

from .manager import VercelManager

__all__ = ["VercelManager"]

__version__ = "1.0.0"
