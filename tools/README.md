# Tools and Integrations

> Tool system and external integrations for Blackbox5

## Overview

The tools directory contains:
- **core/** - Base tool framework and registry
- **git/** - Git operations
- **integrations/** - External service integrations
- **docs/** - Documentation archive

## Directory Structure

```
tools/
├── core/              # Base tool framework
│   ├── base.py       # Base tool classes
│   └── registry.py   # Tool registry
├── git/               # Git operations
│   ├── git_ops.py
│   ├── git_client.py
│   └── commit_manager.py
├── integrations/      # External service integrations
│   ├── _template/    # Template for new integrations
│   ├── cloudflare/
│   ├── github/
│   ├── github-actions/
│   ├── mcp/
│   ├── notion/
│   ├── obsidian/
│   ├── supabase/
│   ├── vercel/
│   └── vibe/
└── docs/              # Documentation archive
```

## Available Integrations

| Integration | Purpose | Status |
|-------------|---------|--------|
| GitHub | Repository operations | Active |
| GitHub Actions | CI/CD integration | Active |
| Supabase | Database operations | Active |
| Notion | Documentation sync | Active |
| MCP | Model Context Protocol | Active |
| Cloudflare | Deployment | Active |
| Vercel | Deployment | Active |
| Obsidian | Knowledge base | Active |
| Vibe | Kanban integration | Active |

## For AI Agents

- New integrations should follow the `_template/` structure
- Each integration should have its own README
- Core tool framework is in `core/`
- Git operations are separated into `git/` for reuse
