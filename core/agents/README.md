# Agent System

> Agent definitions and implementations for Blackbox5

## Overview

This directory contains all agent definitions organized by category:
- **definitions/core/** - Core agent framework and 3 main agents
- **definitions/managerial/** - Coordination and management agents
- **definitions/specialists/** - 18 specialist agents (YAML definitions)

## Directory Structure

```
agents/
└── definitions/
    ├── core/              # Core agents and framework
    │   ├── base_agent.py           # Base agent class
    │   ├── agent_loader.py         # Dynamic agent loading
    │   ├── skill_manager.py        # Skill management
    │   ├── AnalystAgent.py         # Mary - Research & analysis
    │   ├── ArchitectAgent.py       # Alex - System design
    │   ├── DeveloperAgent.py       # Amelia - Implementation
    │   └── test_*.py               # Test files
    ├── managerial/        # Managerial agents
    │   ├── task_lifecycle.py       # Task lifecycle management
    │   ├── memory/                 # Management memory
    │   ├── skills/                 # Managerial skills
    │   └── *.md                    # Documentation
    └── specialists/       # 18 specialist agents (YAML)
        ├── accessibility-specialist.yaml
        ├── api-specialist.yaml
        ├── backend-specialist.yaml
        ├── compliance-specialist.yaml
        ├── data-specialist.yaml
        ├── database-specialist.yaml
        ├── devops-specialist.yaml
        ├── documentation-specialist.yaml
        ├── frontend-specialist.yaml
        ├── integration-specialist.yaml
        ├── ml-specialist.yaml
        ├── mobile-specialist.yaml
        ├── monitoring-specialist.yaml
        ├── performance-specialist.yaml
        ├── research-specialist.yaml
        ├── security-specialist.yaml
        ├── testing-specialist.yaml
        └── ui-ux-specialist.yaml
```

## Core Agents

| Agent | File | Role |
|-------|------|------|
| **Analyst** (Mary) | `definitions/core/AnalystAgent.py` | Research & analysis |
| **Architect** (Alex) | `definitions/core/ArchitectAgent.py` | System design |
| **Developer** (Amelia) | `definitions/core/DeveloperAgent.py` | Implementation |

## Specialist Agents

Specialist agents are defined in YAML files with:
- `role`: Agent's primary function
- `capabilities`: List of skills
- `prompt`: System prompt template
- `tools`: Available tool integrations

## For AI Agents

- Core agent framework is in `definitions/core/`
- Add new specialists as YAML files in `definitions/specialists/`
- Managerial agents handle coordination in `definitions/managerial/`
- All agents use the skill system from `skill_manager.py`
