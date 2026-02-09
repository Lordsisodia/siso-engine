"""
Git Operations - Git utilities for atomic commits

This module provides comprehensive git operations including:
- Basic git commands (status, add, commit)
- Atomic commit protocol with conventional commit format
- Commit history and information retrieval
- Branch operations
- Rollback functionality

Main class: GitOps
"""

from .git_ops import GitOps, CommitInfo

# Backwards compatibility aliases
GitClient = GitOps
CommitManager = GitOps

__all__ = ['GitOps', 'CommitInfo', 'GitClient', 'CommitManager']
