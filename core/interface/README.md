# Interface Layer

> CLI, API, and client libraries for Blackbox5

## Overview

The interface directory contains all user-facing interfaces:
- **cli/** - Command-line interface
- **api/** - REST API server
- **client/** - Client libraries for external use
- **handlers/** - Event handlers

## Directory Structure

```
interface/
├── cli/                   # Command-line interface
│   ├── bb5.py            # Main CLI entry point
│   ├── router.py         # Command routing
│   ├── base.py           # Base CLI classes
│   ├── task_commands.py
│   ├── epic_commands.py
│   ├── prd_commands.py
│   └── github_commands.py
├── api/                   # REST API
│   ├── main.py           # API entry point
│   ├── server.py         # Server implementation
│   └── README.md
├── client/                # Client libraries
│   ├── AgentClient.py
│   ├── ClaudeCodeClient.py
│   ├── GLMClient.py
│   ├── TokenOptimizer.py
│   └── output_format.py
├── handlers/              # Event handlers
│   ├── vibe_handler.py
│   ├── notification_handler.py
│   ├── database_handler.py
│   └── scheduler_handler.py
├── AgentOutputBus.py      # Agent output coordination
├── AgentOutputParser.py   # Output parsing
├── epic_agent.py          # Epic management
├── prd_agent.py           # PRD creation
├── task_agent.py          # Task management
├── config.py
└── exceptions.py
```

## Entry Points

| Interface | Entry Point | Usage |
|-----------|-------------|-------|
| CLI | `cli/bb5.py` | `python -m core.interface.cli.bb5` |
| API | `api/main.py` | `python -m core.interface.api.main` |
| Client | `client/AgentClient.py` | Import for programmatic use |

## For AI Agents

- CLI commands are organized by domain (task, epic, prd, github)
- API follows REST conventions
- Client libraries abstract the API for different use cases
- Handlers process events from the orchestration layer
