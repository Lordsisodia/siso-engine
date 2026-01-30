# Runtime Systems

> Runtime execution environment for Blackbox5

## Overview

The runtime directory contains systems that support the execution of agents and tasks:
- **commands/** - CLI command implementations
- **hooks/** - Claude Code integration hooks
- **memory/** - Multi-tier memory system
- **monitoring/** - Health checks, logging, and status tracking

## Directory Structure

```
runtime/
├── commands/           # CLI command implementations
│   ├── agents/        # Agent-related commands
│   ├── run/           # Task execution commands
│   ├── services/      # Service management commands
│   ├── specs/         # Specification commands
│   └── system/        # System-level commands
├── hooks/             # Claude Code hooks (future)
├── memory/            # Multi-tier memory system
│   ├── systems/       # Core memory implementations
│   ├── working/       # Short-term working memory
│   ├── episodic/      # Long-term episodic memory
│   ├── brain/         # Knowledge graph (Neo4j)
│   ├── docs/          # Memory documentation
│   └── MEMORY-STRUCTURE.md
└── monitoring/        # System monitoring
    ├── alerts/        # Alert management
    ├── health/        # Health checks
    ├── logging/       # Logging infrastructure
    └── status/        # Status tracking
```

## Quick Reference

| Component | Purpose | Entry Point |
|-----------|---------|-------------|
| Commands | CLI implementation | `commands/` subdirectories |
| Memory | Data persistence | `memory/systems/ProductionMemorySystem.py` |
| Monitoring | System health | `monitoring/status/` |

## For AI Agents

- Memory system details: See `memory/MEMORY-STRUCTURE.md`
- Commands are organized by domain (agents, run, services, specs, system)
- Monitoring provides health checks and logging infrastructure
