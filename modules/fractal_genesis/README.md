# Fractal Genesis Module

Recursive task decomposition system for BB5. Breaks complex objectives into manageable subtasks using first principles thinking.

## Overview

Fractal Genesis implements a recursive task decomposition algorithm:
1. Takes a high-level objective
2. Decomposes into 10 first principles
3. Recursively breaks down each principle
4. Tracks progress atomically

## Architecture

```
fractal_genesis/
├── core/
│   └── manager.py          # FractalGenesisManager - main entry point
├── data/
│   └── storage.py          # TaskStorage, FractalTask, SubTask dataclasses
├── integration/
│   └── atomic_timeline.py  # AtomicTimeline for commit tracking
└── logic/
    └── decomposition.py    # Decomposition algorithms
```

## Core Components

### FractalGenesisManager
Main orchestrator for fractal task processing:
- `start_new_task(objective)` - Initialize and decompose a task
- `process_task(task_id)` - Process and display task status

### TaskStorage
Persistent storage for fractal tasks:
- JSON-based state management
- History tracking with markdown logs
- Automatic path resolution

### FractalTask
Dataclass representing a fractal task:
- `id` - Unique identifier
- `objective` - High-level goal
- `subtasks` - List of SubTask objects
- `current_depth` / `max_depth` - Recursion tracking
- `history` - Execution history

## Usage

### CLI Usage
```bash
# Create a new fractal task
python -m modules.fractal_genesis.core.manager new --objective "Build a web app"

# Check task status
python -m modules.fractal_genesis.core.manager status --id FG-123456
```

### Programmatic Usage
```python
from modules.fractal_genesis.core.manager import FractalGenesisManager

manager = FractalGenesisManager()
task = manager.start_new_task("Build a web app")

# Task is automatically decomposed into subtasks
for subtask in task.subtasks:
    print(f"- [{subtask.status}] {subtask.title}")
```

## Integration

Fractal Genesis integrates with:
- **Atomic Timeline** - For atomic commit tracking
- **Task Storage** - For persistence in `~/.blackbox5/5-project-memory/`
