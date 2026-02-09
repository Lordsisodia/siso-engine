# Agents

> Unified agent framework for Blackbox5

## Overview

This directory contains the unified agent framework that consolidates three previously separate systems into one cohesive architecture.

## Structure

```
agents/
├── framework/           # Core agent infrastructure
│   ├── base_agent.py    # BaseAgent class - all agents extend this
│   ├── agent_loader.py  # Dynamic agent loading and registration
│   ├── skill_manager.py # Skill registration and execution
│   └── task_schema.py   # Task validation schemas
│
└── definitions/         # Agent definitions organized by type
    ├── bmad/           # BMAD (Blackbox Multi-Agent Director) agents
    ├── core/           # Core system agents
    ├── improvement/    # Self-improvement agents
    ├── managerial/     # Management/coordination agents
    ├── specialists/    # Domain-specific agents
    └── sub-agents/     # Task-specific sub-agents
```

## Framework vs Definitions

### Framework (framework/)
The framework provides the infrastructure for all agents:
- **BaseAgent**: Abstract base class that all agents extend
- **AgentLoader**: Dynamically loads and registers agents
- **SkillManager**: Manages skill registration and execution
- **TaskSchema**: Validates task structures

### Definitions (definitions/)
Agent definitions are organized by their role in the system:

| Directory | Purpose | Examples |
|-----------|---------|----------|
| bmad/ | BMAD system agents | scout, planner, executor, verifier |
| core/ | Core infrastructure | registry, coordinator |
| improvement/ | Self-improvement | loop, analyzer |
| managerial/ | Management | orchestrator, router |
| specialists/ | Domain experts | git, testing, docs |
| sub-agents/ | Task workers | research, validation |

## Usage

### Creating a New Agent

```python
from agents.framework.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__("my_agent")
    
    async def execute(self, task):
        # Agent logic here
        pass
```

### Loading Agents

```python
from agents.framework.agent_loader import AgentLoader

loader = AgentLoader()
agent = loader.get_agent("scout")
```

## Migration Notes

This unified framework consolidates:
1. core/agents/definitions/ (old Framework)
2. core/autonomous/agents/ (old Redis Runtime)
3. .autonomous/bin/ (old Standalone Scripts)

All agents now use the same BaseAgent class and skill system.
