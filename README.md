# Blackbox5 Engine

> Core multi-agent orchestration engine with intelligent task routing, wave-based parallelization, and proactive guide suggestions.

## Overview

The 2-engine directory contains the **Blackbox5 core infrastructure** - a purpose-based, consolidated architecture for multi-agent orchestration, memory management, and tool integration.

- **Current file count:** ~530 files (down from 10,000+ after reorganization)
- **Status:** Reorganization completed 2026-02-07
- **Architecture:** Purpose-based naming with clear separation of concerns

## Directory Structure

```
2-engine/
├── agents/                    # Unified agent framework
│   ├── framework/             # BaseAgent, agent_loader, skill_manager
│   └── definitions/           # Agent definitions by type (core, managerial, specialists)
│
├── helpers/                   # Shared utilities and integrations
│   ├── core/                  # Core helper utilities
│   ├── git/                   # Git operation helpers
│   ├── integrations/          # External service integrations
│   └── legacy/                # Legacy helper code
│
├── instructions/              # Agent prompts and instructions
│   ├── agents/                # Agent-specific prompts
│   ├── system/                # System prompts and procedures
│   ├── workflows/             # Workflow definitions
│   └── archive/               # Legacy prompts
│
├── workflows/                 # Workflow definitions and orchestration engine
│   └── engine/                # Orchestrator, routing, state, resilience
│
├── configuration/             # System and agent configuration
│   ├── agents/                # Agent configurations
│   ├── mcp/                   # MCP server configurations
│   └── system/                # System-wide settings
│
├── connections/               # External service connections (MCP, hooks)
│   ├── communications/        # Communication protocols
│   ├── hooks/                 # Claude Code hooks
│   └── mcp/                   # MCP server connections
│
├── interface/                 # CLI and API interfaces
│   ├── cli/                   # Command-line interface (bb5 command)
│   ├── api/                   # REST API endpoints
│   ├── client/                # Client libraries
│   └── handlers/              # Request handlers
│
├── safety/                    # Guardrails and validation
│   ├── classifier/            # Content safety classification
│   ├── kill_switch/           # Emergency stop system
│   └── safe_mode/             # Safe execution mode
│
├── executables/               # CLI tools and scripts
│   ├── bb5                    # Main bb5 CLI wrapper
│   ├── scout-analyze.py       # Scout analysis script
│   ├── executor-implement.py  # Executor implementation script
│   ├── verifier-validate.py   # Verifier validation script
│   └── *.py                   # Additional agent scripts
│
├── documentation/             # Engine documentation
│   ├── engine/                # Core engine docs
│   ├── completions/           # Completed work documentation
│   └── archive/               # Legacy documentation
│
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── safety/                # Safety system tests
│
├── infrastructure/            # Docker, deployment infrastructure
├── modules/                   # Optional modules (fractal genesis)
└── examples/                  # Usage examples
```

## Key Components

### BaseAgent Framework
**Location:** `agents/framework/`

The unified agent framework providing:
- `base_agent.py` - BaseAgent class for all agents
- `agent_loader.py` - Multi-format agent loading
- `skill_manager.py` - Composable skill system
- `task_schema.py` - Task definition schemas

### Orchestrator
**Location:** `workflows/engine/Orchestrator.py`

Wave-based parallelization engine with:
- Intelligent task routing
- Pipeline management (`workflows/engine/pipeline/`)
- State management (`workflows/engine/state/`)
- Resilience patterns (`workflows/engine/resilience/`)

### CLI Entry Points
**Location:** `interface/cli/` and `executables/`

- `interface/cli/bb5.py` - Main CLI implementation
- `executables/bb5` - bb5 command wrapper
- `executables/*.py` - Agent-specific scripts

## Getting Started

### Running the CLI

```bash
# Ask a question
bb5 ask "What is 2+2?"

# Build something
bb5 ask "Create a REST API for user management"

# Use specific agent
bb5 ask --agent testing-agent "Write unit tests"

# Multi-agent strategy
bb5 ask --strategy multi_agent "Design and implement a payment system"

# JSON output
bb5 ask --json "Analyze this codebase"
```

### Importing Key Modules

```python
# BaseAgent framework
from agents.framework.base_agent import BaseAgent
from agents.framework.agent_loader import AgentLoader
from agents.framework.skill_manager import SkillManager

# Orchestrator
from workflows.engine.Orchestrator import Orchestrator

# Interface
from interface.cli.bb5 import main as cli_main
from interface.api.main import get_blackbox5
```

### REST API

```bash
# Start server
python -m interface.api.main

# Make request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 2+2?"}'
```

## Architecture Principles

### 1. Purpose-Based Naming
Every directory name reflects its purpose, not its implementation:
- `agents/` - Everything related to agents
- `helpers/` - Shared utilities (not `lib/` or `utils/`)
- `instructions/` - Prompts and instructions (not `prompts/`)
- `workflows/` - Orchestration and workflows
- `connections/` - External integrations
- `executables/` - Runnable scripts

### 2. Clear Separation of Concerns
- **Framework** (`agents/framework/`) - Shared infrastructure
- **Definitions** (`agents/definitions/`) - Agent implementations
- **Configuration** (`configuration/`) - Settings and schemas
- **Interface** (`interface/`) - User-facing entry points

### 3. Single Source of Truth
- One agent framework (`agents/framework/`)
- One configuration system (`configuration/`)
- One workflow engine (`workflows/engine/`)
- Project-specific data lives in `5-project-memory/`

## Quick Reference

### Find Agents
| Type | Location |
|------|----------|
| Framework | `agents/framework/` |
| Core agents | `agents/definitions/core/` |
| Managerial | `agents/definitions/managerial/` |
| Specialists | `agents/definitions/specialists/` |

### Find Helpers
| Category | Location |
|----------|----------|
| Core utilities | `helpers/core/` |
| Git operations | `helpers/git/` |
| Integrations | `helpers/integrations/` |

### Find Workflows
| Component | Location |
|-----------|----------|
| Orchestrator | `workflows/engine/Orchestrator.py` |
| Pipeline | `workflows/engine/pipeline/` |
| Routing | `workflows/engine/routing/` |
| State | `workflows/engine/state/` |
| Resilience | `workflows/engine/resilience/` |

### Find Configuration
| Type | Location |
|------|----------|
| Agent configs | `configuration/agents/` |
| MCP configs | `configuration/mcp/` |
| System settings | `configuration/system/` |

### Find Safety Controls
| Component | Location |
|-----------|----------|
| Kill switch | `safety/kill_switch/` |
| Classifier | `safety/classifier/` |
| Safe mode | `safety/safe_mode/` |

### Find Documentation
| Type | Location |
|------|----------|
| Engine docs | `documentation/engine/` |
| Completions | `documentation/completions/` |
| Guides | `instructions/system/` |

## Reorganization History

The engine was reorganized on 2026-02-07 from 10,000+ files to ~530 files:

| Old Structure | New Structure |
|---------------|---------------|
| `core/` + `.autonomous/` | `agents/` |
| `lib/` | `helpers/` |
| `config/` | `configuration/` |
| `prompts/` | `instructions/` |
| `bin/` | `executables/` |
| `core/orchestration/` | `workflows/` |
| `mcp/` | `connections/` |
| `runtime/memory/` | Moved to `5-project-memory/blackbox5/data/` |

See `REORGANIZATION_SUMMARY.md` for complete details.

## For AI Agents

**Navigation Tips:**
1. Always check this README first when exploring 2-engine/
2. For agent framework details, see `agents/framework/`
3. For workflow engine details, see `workflows/engine/`
4. For system overview, see `../SYSTEM-MAP.yaml`
5. For project state, see `../5-project-memory/blackbox5/STATE.yaml`

**Key Entry Points:**
- CLI: `interface/cli/bb5.py`
- Orchestrator: `workflows/engine/Orchestrator.py`
- BaseAgent: `agents/framework/base_agent.py`
- Safety: `safety/kill_switch/kill_switch.py`

**Important Notes:**
- `.autonomous/` is LEGACY - do not modify
- `helpers/legacy/` contains old code being phased out
- All documentation is consolidated in `documentation/`
- Cache files (`__pycache__`, `.pyc`) can be safely deleted

## Documentation

| Guide | Location |
|-------|----------|
| System Map | `../SYSTEM-MAP.yaml` |
| Agent Guide | `../AGENT-GUIDE.md` |
| Reorganization Summary | `REORGANIZATION_SUMMARY.md` |
| Consolidation Plan | `CONSOLIDATION_PLAN_DETAILED.md` |

## License

MIT License - see LICENSE file for details.

## Version

Current version: 5.1.0 (Reorganized)
