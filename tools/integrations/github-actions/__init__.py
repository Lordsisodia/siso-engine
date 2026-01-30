"""
GitHub Actions Integration for BlackBox5
==========================================

This module provides integration with GitHub Actions service.

Usage:
    >>> from integration.github_actions import GitHubActionsManager
    >>> manager = GitHubActionsManager(owner="owner", repo="repo")
    >>> await manager.list_workflows()
"""

from .manager import GitHubActionsManager

__all__ = ["GitHubActionsManager"]

__version__ = "1.0.0"
