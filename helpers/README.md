# Helpers

> Shared utilities and integrations for Blackbox5

## Overview

This directory contains helper modules that provide common functionality across the engine. These are organized by purpose and scope.

## Structure

```
helpers/
├── core/               # Core utilities (framework-agnostic)
│   ├── base.py         # Base helper classes
│   └── registry.py     # Helper registration system
│
├── git/                # Consolidated Git operations
│   └── git_ops.py      # All git functionality in one module
│
├── integrations/       # External service integrations
│   ├── cloudflare/     # Cloudflare API helpers
│   ├── github/         # GitHub API helpers
│   ├── github-actions/ # GitHub Actions helpers
│   ├── mcp/            # MCP server helpers
│   ├── notion/         # Notion API helpers
│   ├── obsidian/       # Obsidian helpers
│   ├── supabase/       # Supabase helpers
│   ├── vercel/         # Vercel helpers
│   └── vibe/           # Vibe coding helpers
│
└── legacy/             # Deprecated helpers (being migrated)
```

## Core Helpers

The core/ directory contains framework-agnostic utilities:

| File | Purpose |
|------|---------|
| base.py | Base classes for helpers |
| registry.py | Helper registration and discovery |

## Git Module

The git/ directory contains the consolidated git module:

**Before:** Git operations scattered across multiple files
**After:** All git functionality in git_ops.py

### Features
- Repository operations (clone, pull, push)
- Branch management
- Commit operations with safety checks
- PR creation and management
- Status and diff operations

### Usage

```python
from helpers.git.git_ops import GitOps

git = GitOps("/path/to/repo")
git.safe_commit("message", files=["file1.py", "file2.py"])
```

## Integrations

The integrations/ directory contains helpers for external services:

| Service | Purpose |
|---------|---------|
| cloudflare/ | Cloudflare API operations |
| github/ | GitHub API, PRs, issues |
| github-actions/ | Workflow management |
| mcp/ | MCP server interactions |
| notion/ | Notion page/database ops |
| obsidian/ | Obsidian vault operations |
| supabase/ | Database operations |
| vercel/ | Deployment management |
| vibe/ | Vibe coding utilities |

Each integration follows the same pattern:
- README.md - Integration-specific docs
- *.py - Helper modules
- examples/ - Usage examples

## Legacy

The legacy/ directory contains deprecated helpers being migrated to the new structure. Do not use for new code.
