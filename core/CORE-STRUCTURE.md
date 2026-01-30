# Core Directory Structure

> Complete map of the 2-engine/core/ directory for agent navigation

## Overview

The `core/` directory contains the fundamental orchestration systems of Blackbox5:
- **agents/** - Agent definitions and implementations
- **orchestration/** - Pipeline, routing, state management, resilience
- **interface/** - CLI, API, client libraries, handlers
- **safety/** - Kill switch, constitutional AI, safe mode
- **docs/** - Implementation documentation and reports

---

## agents/

Agent definitions organized by category.

### Structure
```
agents/
├── definitions/           # Agent implementations
│   ├── core/             # Core 4 agents (base classes + implementations)
│   │   ├── base_agent.py
│   │   ├── agent_loader.py
│   │   ├── skill_manager.py
│   │   ├── AnalystAgent.py
│   │   ├── ArchitectAgent.py
│   │   ├── DeveloperAgent.py
│   │   └── test_*.py     # Various test files
│   ├── managerial/       # Managerial/coordination agents
│   │   ├── task_lifecycle.py
│   │   ├── memory/
│   │   ├── skills/
│   │   ├── claude-coordinator.sh
│   │   └── *.md          # Documentation
│   └── specialists/      # 18 specialist agents (YAML definitions)
│       ├── accessibility-specialist.yaml
│       ├── api-specialist.yaml
│       ├── backend-specialist.yaml
│       ├── compliance-specialist.yaml
│       ├── data-specialist.yaml
│       ├── database-specialist.yaml
│       ├── devops-specialist.yaml
│       ├── documentation-specialist.yaml
│       ├── frontend-specialist.yaml
│       ├── integration-specialist.yaml
│       ├── ml-specialist.yaml
│       ├── mobile-specialist.yaml
│       ├── monitoring-specialist.yaml
│       ├── performance-specialist.yaml
│       ├── research-specialist.yaml
│       ├── security-specialist.yaml
│       ├── testing-specialist.yaml
│       └── ui-ux-specialist.yaml
└── __init__.py
```

### Key Files

| File | Purpose |
|------|---------|
| `definitions/core/base_agent.py` | Base agent class with skill management |
| `definitions/core/skill_manager.py` | Skill registration and execution |
| `definitions/core/agent_loader.py` | Dynamic agent loading |
| `definitions/core/AnalystAgent.py` | Mary - Research & analysis |
| `definitions/core/ArchitectAgent.py` | Alex - System design |
| `definitions/core/DeveloperAgent.py` | Amelia - Implementation |

---

## orchestration/

Core orchestration systems for task routing, pipeline execution, and state management.

### Structure
```
orchestration/
├── pipeline/              # Pipeline processing systems
│   ├── unified_pipeline.py
│   ├── feature_pipeline.py
│   ├── testing_pipeline.py
│   ├── bb5-pipeline.py
│   ├── context_extractor.py
│   ├── token_compressor.py
│   ├── complexity.py
│   ├── anti_pattern_detector.py
│   ├── guide_middleware.py
│   ├── pipeline_integration.py
│   └── test_*.py
├── routing/               # Task routing and assignment
│   ├── task_router.py
│   └── task_router_examples.py
├── state/                 # State management and event bus
│   ├── state_manager.py
│   ├── event_bus.py
│   ├── state_manager_demo.py
│   ├── demo_race_condition_fixes.py
│   └── STATE_MANAGER_RACE_CONDITION_FIXES.md
├── resilience/            # Circuit breakers and atomic commits
│   ├── circuit_breaker.py
│   ├── circuit_breaker_types.py
│   ├── circuit_breaker_examples.py
│   ├── circuit_breaker_standalone.py
│   ├── atomic_commit_manager.py
│   └── atomic_commit_standalone.py
├── tests/                 # Orchestration tests
├── Orchestrator.py        # Main orchestrator
├── orchestrator_deviation_integration.py
├── examples_anti_pattern.py
├── exceptions.py
└── __init__.py
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `Orchestrator.py` | Main orchestration engine |
| `pipeline/unified_pipeline.py` | Unified task processing pipeline |
| `routing/task_router.py` | Intelligent task-to-agent routing |
| `state/state_manager.py` | Distributed state management |
| `state/event_bus.py` | Event-driven communication |
| `resilience/circuit_breaker.py` | Failure isolation |
| `resilience/atomic_commit_manager.py` | Transaction safety |

---

## interface/

All interfaces for interacting with the system.

### Structure
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
│   ├── main.py
│   ├── server.py
│   └── README.md
├── client/                # Client libraries
│   ├── AgentClient.py
│   ├── ClaudeCodeClient.py
│   ├── ClaudeCodeAgentMixin.py
│   ├── GLMClient.py
│   ├── TokenOptimizer.py
│   ├── output_format.py
│   ├── add_output_format_to_agents.py
│   └── test_*.py
├── handlers/              # Event handlers
│   ├── vibe_handler.py
│   ├── notification_handler.py
│   ├── database_handler.py
│   └── scheduler_handler.py
├── AgentOutputBus.py      # Agent output coordination
├── AgentOutputParser.py   # Output parsing
├── epic_agent.py          # Epic management agent
├── prd_agent.py           # PRD creation agent
├── task_agent.py          # Task management agent
├── demo_agent_coordination.py
├── config.py
├── exceptions.py
├── __init__.py
└── *.md                   # Design documentation
```

### Key Files

| File | Purpose |
|------|---------|
| `cli/bb5.py` | Main CLI entry point |
| `api/server.py` | REST API server |
| `client/ClaudeCodeClient.py` | Claude Code integration |
| `client/AgentClient.py` | Generic agent client |
| `AgentOutputBus.py` | Output coordination bus |
| `epic_agent.py` | Epic management |
| `prd_agent.py` | PRD creation |
| `task_agent.py` | Task management |

---

## safety/

Safety systems for controlling and monitoring AI behavior.

### Structure
```
safety/
├── kill_switch/           # Emergency stop system
│   ├── __init__.py
│   ├── kill_switch.py
│   ├── kill_switch_monitor.py
│   ├── keyboard_trigger.py
│   ├── cli_commands.py
│   └── tests/
├── classifier/            # Content classification
│   ├── __init__.py
│   ├── classifier.py
│   ├── training_data.py
│   └── tests/
├── safe_mode/             # Safe execution mode
│   ├── __init__.py
│   ├── safe_mode.py
│   ├── dry_run.py
│   └── tests/
├── tests/                 # Safety system tests
├── QUICK_REFERENCE.md     # Quick reference guide
├── SAFETY-INTEGRATION-GUIDE.md
├── SAFETY-IMPLEMENTATION-COMPLETE.md
├── PHASE1-COMPLETE.md
├── FINAL_REPORT.md
└── __init__.py
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `kill_switch/` | Emergency stop mechanism |
| `classifier/` | Content safety classification |
| `safe_mode/` | Dry-run and safe execution |

---

## docs/

Implementation documentation, test results, and reports.

### Contents
```
docs/
├── orchestration-implementation.md
├── PHASE1-COMPLETE.md
├── PHASE1-TEST-RESULTS.md
├── PULL-REQUEST-CREATED.md
├── TESTING-CHECKLIST.md
└── TIER2-INTEGRATION-TEST-RESULTS.md
```

---

## Quick Reference

### Find Agent Definitions
```
agents/definitions/
├── core/         # Base classes + 3 core agents
├── managerial/   # Coordination agents
└── specialists/  # 18 specialist YAMLs
```

### Find Orchestration Logic
```
orchestration/
├── Orchestrator.py    # Main orchestrator
├── pipeline/          # Task processing
├── routing/           # Task routing
├── state/             # State management
└── resilience/        # Fault tolerance
```

### Find CLI/API
```
interface/
├── cli/bb5.py         # CLI entry
├── api/server.py      # REST API
└── client/            # Client libraries
```

### Find Safety Controls
```
safety/
├── kill_switch/       # Emergency stop
├── classifier/        # Content safety
└── safe_mode/         # Safe execution
```

---

## For AI Agents

**Navigation Tips:**
1. Always check `CORE-STRUCTURE.md` first when exploring core/
2. Agent implementations are in `agents/definitions/`, not root
3. Orchestrator is the main entry point for task execution
4. CLI entry is `interface/cli/bb5.py`
5. Safety systems are in `safety/` - understand before modifying

**State of Consolidation:**
- This structure is post-consolidation (was 01-core/)
- All agent definitions merged from 02-agents/
- All orchestration merged from 04-work/
- If you find references to old paths, update them
