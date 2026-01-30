"""
Git Operations - Git utilities for atomic commits
"""

from .git_client import GitClient
from .commit_manager import CommitManager, CommitInfo

# Alias for compatibility with atomic_commit_manager
GitOps = CommitManager

__all__ = ['GitClient', 'CommitManager', 'GitOps', 'CommitInfo']
