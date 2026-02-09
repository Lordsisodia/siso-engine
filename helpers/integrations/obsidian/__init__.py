"""
Obsidian Integration for BlackBox5
===================================

This module provides integration with Obsidian note-taking application
through direct file system writes.

Usage:
    >>> from integration.obsidian import ObsidianExporter
    >>> exporter = ObsidianExporter(vault_path="/path/to/vault")
    >>> exporter.export_session(session_data)
"""

from .manager import ObsidianExporter

__all__ = ["ObsidianExporter"]

__version__ = "1.0.0"
