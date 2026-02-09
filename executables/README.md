# Executables

Agent executables for the RALF improvement loop and BB5 CLI.

## Overview

This directory contains the autonomous agent improvement system - a continuous feedback loop that scans, plans, implements, and validates improvements to BlackBox5.

## The Improvement Loop

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Scout  │───→│  Planner │───→│ Executor │───→│ Verifier │
└─────────┘    └──────────┘    └──────────┘    └──────────┘
     ↑                                              │
     └──────────────────────────────────────────────┘
```

1. **Scout** - Analyzes system for improvement opportunities
2. **Planner** - Prioritizes and plans improvements
3. **Executor** - Implements quick wins automatically
4. **Verifier** - Validates implementations

## Files

| File | Purpose |
|------|---------|
| `bb5` | CLI wrapper script - routes to interface/cli/legacy/ralf.py |
| `executor-implement.py` | Executor Agent - implements quick wins automatically |
| `verifier-validate.py` | Verifier Agent - validates improvement implementations |
| `scout-analyze.py` | Improvement Scout - scans for opportunities |
| `scout-task-based.py` | Task-Based Scout - uses Claude Code Task tool |
| `intelligent-scout.sh` | AI-Powered Scout - spawns Claude instances |
| `improvement-loop.py` | **DEPRECATED** - redirects to project bin |
| `planner-prioritize.py` | **DEPRECATED** - redirects to project bin |
| `scout-intelligent.py` | **DEPRECATED** - redirects to project bin |

## Usage

### Run Scout Analysis
```bash
./scout-analyze.py --project-dir ~/.blackbox5/5-project-memory/blackbox5
```

### Execute Quick Wins
```bash
./executor-implement.py --quick-wins --limit 5
```

### Validate Implementation
```bash
./verifier-validate.py --latest
```

### Use BB5 CLI
```bash
./bb5 <command>
```

## Architecture

These scripts form the autonomous improvement pipeline:
- Each agent has a specific role in the lifecycle
- Uses shared path resolution library (`lib/paths.py`)
- Run by RALF daemon or manually
- Stores results in `5-project-memory/blackbox5/runs/`

## Related

- [RALF Daemon](../.autonomous/bin/ralf-loop.sh) - Autonomous execution
- [Instructions](../instructions/) - Agent identity and procedures
- [Project Memory](../../5-project-memory/blackbox5/) - Results storage
