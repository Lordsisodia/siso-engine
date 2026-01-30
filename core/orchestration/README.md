# Orchestration System

> Task routing, pipeline execution, and workflow management for Blackbox5

## Overview

The orchestration directory contains systems for coordinating agent execution:
- **pipeline/** - Pipeline processing and task execution
- **routing/** - Intelligent task-to-agent routing
- **state/** - State management and event bus
- **resilience/** - Fault tolerance (circuit breakers, atomic commits)

## Directory Structure

```
orchestration/
├── pipeline/              # Pipeline processing
│   ├── unified_pipeline.py
│   ├── feature_pipeline.py
│   ├── testing_pipeline.py
│   ├── context_extractor.py
│   ├── token_compressor.py
│   ├── complexity.py
│   ├── anti_pattern_detector.py
│   └── test_*.py
├── routing/               # Task routing
│   ├── task_router.py
│   └── task_router_examples.py
├── state/                 # State management
│   ├── state_manager.py
│   ├── event_bus.py
│   └── demo_race_condition_fixes.py
├── resilience/            # Fault tolerance
│   ├── circuit_breaker.py
│   ├── circuit_breaker_types.py
│   ├── atomic_commit_manager.py
│   └── circuit_breaker_examples.py
├── tests/                 # Orchestration tests
├── Orchestrator.py        # Main orchestrator
├── orchestrator_deviation_integration.py
├── examples_anti_pattern.py
└── exceptions.py
```

## Key Components

| Component | File | Purpose |
|-----------|------|---------|
| Orchestrator | `Orchestrator.py` | Main orchestration engine |
| Task Router | `routing/task_router.py` | Routes tasks to agents |
| State Manager | `state/state_manager.py` | Distributed state |
| Event Bus | `state/event_bus.py` | Event-driven communication |
| Circuit Breaker | `resilience/circuit_breaker.py` | Failure isolation |

## For AI Agents

- Start with `Orchestrator.py` for understanding execution flow
- Task routing logic is in `routing/task_router.py`
- State management uses Redis via `state/event_bus.py`
- Circuit breakers prevent cascade failures
