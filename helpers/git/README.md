# Git Operations Module

> Consolidated Git utilities for atomic commits and repository management

## Overview

This module provides comprehensive Git operations for BlackBox5, implementing the GSD "Atomic Commits" protocol. All git functionality is consolidated in a single module for easier maintenance and usage.

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Module initialization with exports and backwards compatibility aliases |
| `git_ops.py` | All git operations in one consolidated module |

## Features

- **Repository Operations**: Clone, pull, push, status
- **Atomic Commits**: Conventional commit format enforcement
- **Commit Management**: History, info retrieval, rollback
- **Branch Operations**: Current branch detection
- **Safety Checks**: Clean state validation, modified file detection

## Main Classes

### GitOps

Primary class for all git operations.

```python
from helpers.git.git_ops import GitOps

# Initialize with repo path
git = GitOps("/path/to/repo")

# Check repository state
if git.is_clean():
    print("Working directory is clean")
else:
    print(f"Modified files: {git.get_modified_files()}")

# Create conventional commit
git.create_commit(
    message="Add user authentication",
    type_="feat",
    scope="auth"
)
```

### CommitInfo

Data class containing commit information.

```python
from helpers.git.git_ops import CommitInfo

# CommitInfo fields:
# - hash: Short commit hash
# - short_hash: Short commit hash
# - full_hash: Full commit hash
# - author: Commit author name
# - date: Commit datetime
# - message: Full commit message
# - files_changed: List of changed files
# - commit_type: Parsed type (feat, fix, etc.)
# - scope: Parsed scope
# - description: Parsed description
```

## Usage Examples

### Basic Operations

```python
from helpers.git.git_ops import GitOps

git = GitOps()

# Get status
status = git.get_status()
print(status)

# Check if clean
is_clean = git.is_clean()

# Get modified files
files = GitOps.get_modified_files()
```

### Atomic Commits (GSD Protocol)

```python
from helpers.git.git_ops import GitOps

# Static method for atomic commits
commit_hash = GitOps.commit_task(
    task_type="feat",
    scope="auth",
    description="Add login functionality",
    files=["auth.py", "login.html"],
    body="Implements OAuth2 login flow"
)
# Creates: feat(auth): Add login functionality
```

### Commit Information

```python
from helpers.git.git_ops import GitOps

# Get current HEAD
head = GitOps.get_current_head()

# Get commit info
info = GitOps.get_commit_info("abc123")
print(f"Author: {info.author}")
print(f"Date: {info.date}")
print(f"Files: {info.files_changed}")

# Get commit history
history = GitOps.get_commit_history(count=5)
for commit in history:
    print(f"{commit.short_hash} - {commit.message}")
```

### Rollback Operations

```python
from helpers.git.git_ops import GitOps

# Create rollback commit (reverts specific commit)
new_hash = GitOps.create_rollback_commit("abc123")

# Soft reset last N commits
git = GitOps()
git.rollback(commits=1)  # Undo last commit, keep changes
```

## Conventional Commit Types

Valid commit types for atomic commits:

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `test` | Adding or updating tests |
| `refactor` | Code refactoring |
| `perf` | Performance improvements |
| `docs` | Documentation changes |
| `style` | Code style changes (formatting) |
| `chore` | Maintenance tasks |

## Backwards Compatibility

The module provides aliases for legacy code:

```python
from helpers.git import GitClient      # Same as GitOps
from helpers.git import CommitManager  # Same as GitOps
```

## CLI Usage

```bash
# Check repository state
python -m helpers.git check

# View commit history
python -m helpers.git history
```

## Related

- [Core Helpers](../core/) - Base tool classes
- [Legacy Helpers](../legacy/) - Deprecated git utilities (do not use)
