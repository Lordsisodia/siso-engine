# Workflows

> Workflow definitions and orchestration engine for Blackbox5

## Overview

This directory contains the workflow orchestration system that coordinates agent execution, manages pipelines, and handles task routing.

## Structure

```
workflows/
└── engine/                    # Orchestration engine
    ├── Orchestrator.py        # Main orchestrator
    ├── orchestrator_deviation_integration.py
    ├── exceptions.py          # Workflow exceptions
    ├── examples_anti_pattern.py
    │
    ├── pipeline/              # Pipeline processing
    │   ├── unified_pipeline.py
    │   ├── feature_pipeline.py
    │   ├── testing_pipeline.py
    │   ├── context_extractor.py
    │   ├── token_compressor.py
    │   ├── complexity.py
    │   └── anti_pattern_detector.py
    │
    ├── routing/               # Task routing
    │   └── task_router.py
    │
    ├── state/                 # State management
    │   ├── state_manager.py
    │   └── event_bus.py
    │
    ├── resilience/            # Fault tolerance
    │   ├── circuit_breaker.py
    │   ├── circuit_breaker_types.py
    │   └── atomic_commit_manager.py
    │
    └── tests/                 # Orchestration tests
```

## Orchestrator

The Orchestrator (engine/Orchestrator.py) is the central workflow engine:

### Responsibilities
- Task routing and distribution
- Pipeline execution management
- State coordination
- Error handling and recovery

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| Orchestrator | Orchestrator.py | Main orchestration engine |
| Task Router | routing/task_router.py | Routes tasks to appropriate agents |
| State Manager | state/state_manager.py | Distributed state management |
| Event Bus | state/event_bus.py | Event-driven communication |
| Circuit Breaker | resilience/circuit_breaker.py | Failure isolation and recovery |

## Pipeline System

Located in engine/pipeline/, handles different types of workflows:

| Pipeline | Purpose |
|----------|---------|
| unified_pipeline.py | General task processing |
| feature_pipeline.py | Feature development workflow |
| testing_pipeline.py | Testing and validation workflow |
| context_extractor.py | Context gathering for tasks |
| token_compressor.py | Token usage optimization |
| complexity.py | Task complexity analysis |
| anti_pattern_detector.py | Detects workflow anti-patterns |

## Routing

The engine/routing/ directory handles intelligent task-to-agent routing:

- Task Router (task_router.py): Analyzes tasks and routes to appropriate agents based on:
  - Task type
  - Required skills
  - Agent availability
  - Historical performance

## State Management

The engine/state/ directory provides distributed state:

- State Manager (state_manager.py): Manages workflow state
- Event Bus (event_bus.py): Enables event-driven communication between components

## Resilience

The engine/resilience/ directory provides fault tolerance:

| Component | Purpose |
|-----------|---------|
| circuit_breaker.py | Prevents cascade failures |
| circuit_breaker_types.py | Circuit breaker implementations |
| atomic_commit_manager.py | Ensures atomic operations |

## Usage

### Starting the Orchestrator

```python
from workflows.engine.Orchestrator import Orchestrator

orchestrator = Orchestrator()
orchestrator.start()
```

### Routing a Task

```python
from workflows.engine.routing.task_router import TaskRouter

router = TaskRouter()
agent = router.route_task(task_description, required_skills)
```

### Using Pipelines

```python
from workflows.engine.pipeline.unified_pipeline import UnifiedPipeline

pipeline = UnifiedPipeline()
result = pipeline.execute(task)
```

## For AI Agents

- Start with Orchestrator.py for understanding execution flow
- Task routing logic is in routing/task_router.py
- State management uses Redis via state/event_bus.py
- Circuit breakers prevent cascade failures
