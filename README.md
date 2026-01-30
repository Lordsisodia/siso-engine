# Blackbox5 Engine

> Core multi-agent orchestration engine with intelligent task routing, wave-based parallelization, and proactive guide suggestions.

## Overview

The 2-engine directory contains the core systems for multi-agent orchestration, memory management, and tool integration. This is a **consolidated structure** (previously 8 separate directories).

## Directory Structure

```
2-engine/
├── core/                    # Core orchestration systems
│   ├── agents/definitions/  # Agent implementations (21 agents)
│   ├── autonomous/          # Redis-based autonomous agent system
│   ├── interface/           # CLI, API, client libraries
│   ├── orchestration/       # Pipeline, routing, state, resilience
│   ├── safety/              # Kill switch, classifier, safe mode
│   ├── docs/                # Implementation docs
│   └── CORE-STRUCTURE.md    # Detailed core navigation guide
│
├── runtime/                 # Runtime systems
│   ├── commands/            # CLI commands
│   ├── hooks/               # Claude Code hooks
│   ├── memory/              # Multi-tier memory system
│   │   ├── systems/         # Core memory implementations
│   │   ├── working/         # Short-term working memory
│   │   ├── episodic/        # Long-term episodic memory
│   │   ├── brain/           # Knowledge graph (Neo4j)
│   │   ├── docs/            # Memory documentation
│   │   └── MEMORY-STRUCTURE.md
│   └── monitoring/          # Health, logging, status, alerts
│
├── tools/                   # Tools and integrations
│   ├── core/                # Core tools (base.py, registry.py)
│   ├── git/                 # Git operations
│   ├── integrations/        # External integrations
│   └── docs/                # Tools documentation
│
├── examples/                # Example usage and demos
│   ├── agent-usage/         # Agent usage examples
│   ├── autonomous/          # Autonomous system examples
│   ├── orchestration/       # Orchestration examples
│   └── resilience/          # Resilience pattern examples
│
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── README.md            # Test documentation
│
├── .autonomous/             # LEGACY: Bash-based autonomous system
├── .config/                 # Configuration files
├── .docs/                   # Engine documentation archive
│   └── completions/         # Completed work documentation
├── modules/                 # Fractal genesis modules
└── README.md                # This file
```

## Quick Start

### CLI Usage

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

**CLI Entry:** `core/interface/cli/bb5.py`

### Python API

```python
from core.interface.api.main import get_blackbox5
import asyncio

async def main():
    bb5 = await get_blackbox5()
    result = await bb5.process_request("What is 2+2?")
    print(result['result'])

asyncio.run(main())
```

### REST API

```bash
# Start server
python -m core.interface.api.main

# Make request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 2+2?"}'
```

**API Server:** `core/interface/api/main.py`

## Quick Reference

### Find Agents
| Type | Location |
|------|----------|
| Core agents | `core/agents/definitions/core/` |
| Managerial | `core/agents/definitions/managerial/` |
| Specialists | `core/agents/definitions/specialists/` |
| Autonomous | `core/autonomous/agents/` |

### Find Memory Systems
| Tier | Location |
|------|----------|
| System code | `runtime/memory/systems/` |
| Working | `runtime/memory/working/` |
| Episodic | `runtime/memory/episodic/` |
| Brain | `runtime/memory/brain/` |

### Find Tools
| Category | Location |
|----------|----------|
| Core tools | `tools/core/` |
| Git | `tools/git/` |
| Integrations | `tools/integrations/` |

### Find Safety Controls
```
core/safety/
├── kill_switch/       # Emergency stop
├── classifier/        # Content safety
└── safe_mode/         # Safe execution
```

### Find Autonomous System
```
core/autonomous/
├── agents/            # Supervisor, autonomous, interface agents
├── redis/             # Redis coordination layer
├── schemas/           # Task definitions
├── stores/            # Storage backends (JSON, SQLite)
└── README.md          # Documentation
```

### Find Examples
| Category | Location |
|----------|----------|
| Agent usage | `examples/agent-usage/` |
| Autonomous | `examples/autonomous/` |
| Orchestration | `examples/orchestration/` |
| Resilience | `examples/resilience/` |

### Find Tests
| Type | Location |
|------|----------|
| Unit tests | `tests/unit/` |
| Integration tests | `tests/integration/` |
| Component tests | `core/<component>/tests/` |

### Find Documentation
| Type | Location |
|------|----------|
| Engine docs | `.docs/` |
| Completed work | `.docs/completions/` |
| Core docs | `core/docs/` |
| Memory docs | `runtime/memory/docs/` |
| Autonomous guides | `1-docs/guides/autonomous/` |
| Autonomous research | `1-docs/research/autonomous-system/` |

## Architecture

Blackbox5 consists of:

- **Orchestrator** (`core/orchestration/Orchestrator.py`) - Wave-based parallelization
- **TaskRouter** (`core/orchestration/routing/`) - Intelligent complexity-based routing
- **AgentLoader** (`core/agents/definitions/core/agent_loader.py`) - Multi-format agent loading
- **SkillManager** (`core/agents/definitions/core/skill_manager.py`) - Composable skill system
- **Memory System** (`runtime/memory/`) - Multi-tier persistent storage
- **EventBus** (`core/orchestration/state/event_bus.py`) - Redis-based event communication
- **Safety System** (`core/safety/`) - Kill switch, content classification, safe mode
- **Autonomous System** (`core/autonomous/`) - Redis-coordinated autonomous agents

### Request Pipeline

1. Parse request into Task
2. Route to single or multi-agent based on complexity
3. Execute with orchestration
4. Check for guide suggestions
5. Return result with metadata

## Consolidation History

This structure consolidates 8 previous directories:
- `01-core/` → `core/`
- `02-agents/` → `core/agents/`
- `03-knowledge/` → `runtime/memory/`
- `04-work/` → `core/orchestration/`
- `05-tools/` → `tools/core/`
- `06-integrations/` → `tools/integrations/`
- `07-operations/` → `runtime/`
- `08-development/` → `1-docs/development/`
- `08-autonomous-system/` → `core/autonomous/` + `1-docs/guides/autonomous/` + `1-docs/research/autonomous-system/` + `examples/autonomous/`

## For AI Agents

**Navigation Tips:**
1. Always check this README first when exploring 2-engine/
2. For core/ details, see `core/CORE-STRUCTURE.md`
3. For memory/ details, see `runtime/memory/MEMORY-STRUCTURE.md`
4. For autonomous system, see `core/autonomous/README.md`
5. For system overview, see `../SYSTEM-MAP.yaml`
6. For project state, see `../5-project-memory/siso-internal/STATE.yaml`

**Key Entry Points:**
- CLI: `core/interface/cli/bb5.py`
- Orchestrator: `core/orchestration/Orchestrator.py`
- Memory: `runtime/memory/systems/ProductionMemorySystem.py`
- Safety: `core/safety/kill_switch/kill_switch.py`
- Autonomous: `core/autonomous/agents/supervisor.py`

**Important Notes:**
- `.autonomous/` is LEGACY - do not modify
- `core/autonomous/` is the new Redis-based autonomous system
- All documentation is consolidated in `docs/` subdirectories
- Cache files (`__pycache__`, `.pyc`) can be safely deleted

## Documentation

| Guide | Location |
|-------|----------|
| System Map | `../SYSTEM-MAP.yaml` |
| Agent Guide | `../AGENT-GUIDE.md` |
| Core Structure | `core/CORE-STRUCTURE.md` |
| Memory Structure | `runtime/memory/MEMORY-STRUCTURE.md` |
| Autonomous System | `core/autonomous/README.md` |

## License

MIT License - see LICENSE file for details.

## Version

Current version: 5.0.0
