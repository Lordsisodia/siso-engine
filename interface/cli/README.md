# CLI Interface

Command-line interface for BlackBox5.

## Overview

This directory contains the command-line interface implementation for BlackBox5, providing commands for task management, epic creation, PRD generation, and GitHub integration.

## Files

| File | Purpose |
|------|---------|
| `bb5.py` | Main CLI entry point with multi-agent orchestration |
| `router.py` | Command routing and registration system |
| `base.py` | Base CLI classes and utilities |
| `task_commands.py` | Task management commands (create, list, update, complete) |
| `epic_commands.py` | Epic management commands |
| `prd_commands.py` | PRD creation and management commands |
| `github_commands.py` | GitHub integration commands (PRs, issues, sync) |
| `bb5` | Shell wrapper script |
| `legacy/` | Legacy CLI commands |

## Commands

### Ask
```bash
bb5 ask "What is 2+2?"
bb5 ask --agent testing-agent "Write tests for this function"
```

### Inspect
```bash
bb5 inspect orchestrator    # Inspect orchestrator state
bb5 inspect agent <name>    # Inspect specific agent
```

### Agents
```bash
bb5 agents                  # List all available agents
bb5 agents --detail         # Show detailed agent info
```

### Skills
```bash
bb5 skills                  # List all available skills
bb5 skills --detail         # Show skill details
```

### Guide
```bash
bb5 guide "test this code"  # Get guidance on a task
```

### Tasks
```bash
bb5 task create "Fix bug"   # Create a new task
bb5 task list               # List active tasks
bb5 task complete <id>      # Mark task complete
```

### Epics
```bash
bb5 epic create "Feature X" # Create new epic
bb5 epic list               # List epics
bb5 epic show <id>          # Show epic details
```

### PRDs
```bash
bb5 prd create "Feature"    # Create PRD
bb5 prd list                # List PRDs
bb5 prd show <id>           # Show PRD
```

### GitHub
```bash
bb5 github pr create        # Create pull request
bb5 github issue list       # List issues
bb5 github sync             # Sync with GitHub
```

## Architecture

```
CLI Entry (bb5.py)
    ↓
Router (router.py)
    ↓
Command Handlers
    ├── task_commands.py
    ├── epic_commands.py
    ├── prd_commands.py
    └── github_commands.py
```

## Adding New Commands

1. Create command handler in appropriate file
2. Register in `router.py`:
```python
@router.register("my_command")
def handle_my_command(args):
    # Implementation
    pass
```
3. Add to `bb5.py` argument parser

## Related

- [Infrastructure](../../infrastructure/) - System initialization
- [Agents](../../agents/) - Agent definitions
- [Client](../client/) - Client libraries
