# Blackbox5 Engine Reorganization Summary

**Date:** 2026-02-07
**Status:** Complete

## Overview

The 2-engine directory has been reorganized from 10,234+ files of mixed legacy/active code to a clean, purpose-based structure with ~522 files.

## Key Changes

### 1. Directory Structure (Purpose-Based Naming)

| Old | New | Purpose |
|-----|-----|---------|
| `core/` + `.autonomous/` | `agents/` | Unified agent framework |
| `lib/` | `helpers/` | Shared utilities and integrations |
| `config/` | `configuration/` | System and agent configuration |
| `prompts/` | `instructions/` | Agent instructions and prompts |
| `bin/` | `executables/` | CLI tools and scripts |
| `core/orchestration/` | `workflows/` | Workflow definitions and engine |
| `mcp/` | `connections/` | External service connections |
| `runtime/memory/` | `data/` | Runtime data storage |

### 2. Agent System Consolidation

**Before:** 3 parallel systems
- `core/agents/definitions/` (Framework - BaseAgent)
- `core/autonomous/agents/` (Redis Runtime)
- `.autonomous/bin/` (Standalone Scripts)

**After:** 1 unified system
- `agents/framework/` - BaseAgent, agent_loader, skill_manager
- `agents/definitions/` - All agent definitions organized by type
- `executables/` - Refactored scripts using BaseAgent

### 3. Data Separation

**Engine** (shared infrastructure): ~522 files
- Framework code
- Helper libraries
- Configuration schemas
- Workflow definitions

**Project Memory** (project-specific): 5.2MB, 69 files
- Brain/memory state
- Episode storage
- Vector embeddings
- Working memory

Moved from `runtime/memory/` to `5-project-memory/blackbox5/data/`

### 4. Deprecated Directories Removed

- `.autonomous/` (9,500+ legacy files)
- `core/` (consolidated into agents/)
- `runtime/` (data moved to project memory)
- `tools/` (consolidated into helpers/)
- `02-agents/` (duplicate)
- `.config/`, `.docs/` (temp directories)

## New Structure

```
2-engine/
├── agents/              # Unified agent framework
│   ├── framework/       # BaseAgent, loader, skills
│   ├── definitions/     # Agent definitions by type
│   └── runtime/         # Runtime agent instances
├── helpers/             # Shared utilities
│   ├── core/            # Core helpers
│   ├── git/             # Git operations
│   └── integrations/    # External service helpers
├── configuration/       # System configuration
│   ├── agents/          # Agent configs
│   ├── mcp/             # MCP server configs
│   └── system/          # System-wide settings
├── instructions/        # Agent instructions
│   ├── agents/          # Agent-specific prompts
│   ├── system/          # System prompts
│   └── archive/         # Legacy prompts
├── workflows/           # Workflow definitions
│   └── engine/          # Orchestrator, engines
├── connections/         # External integrations
│   ├── mcp/             # MCP servers
│   └── bridges/         # Legacy bridges
├── interface/           # User interfaces
│   ├── cli/             # Command-line tools
│   └── api/             # API endpoints
├── safety/              # Guardrails, validation
│   ├── guardrails/      # Safety checks
│   └── validation/      # Input/output validation
├── executables/         # CLI executables
│   ├── bb5              # bb5 wrapper
│   ├── ralf             # ralf wrapper
│   └── *.py             # Agent scripts
├── documentation/       # Engine docs
├── tests/               # Test suite
├── infrastructure/      # Docker, deployment
├── modules/             # Optional modules
└── examples/            # Usage examples
```

## File Counts

| Directory | Files |
|-----------|-------|
| agents | 53 |
| helpers | 136 |
| instructions | 93 |
| workflows | 32 |
| configuration | 26 |
| executables | 10 |
| **Total Engine** | **~522** |
| **Project Data** | **69 (5.2MB)** |

## Next Steps

1. **Update import paths** in moved Python files
2. **Test executables** to ensure scripts work in new locations
3. **Update documentation** references to old paths
4. **Verify MCP configurations** point to correct locations
