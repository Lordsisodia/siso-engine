# Agent Definitions

Complete agent definitions for BB5 including core agents, specialists, BMAD roles, and sub-agents.

## Structure

```
agents/definitions/
├── bmad/                    # BMAD role definitions
│   ├── architecture.py
│   ├── business.py
│   ├── development.py
│   ├── framework.py
│   └── model.py
├── core/                    # Core agent implementations
│   ├── AnalystAgent.py
│   ├── ArchitectAgent.py
│   └── DeveloperAgent.py
├── improvement/             # Continuous improvement agents
├── managerial/              # Managerial agent components
│   ├── task_lifecycle.py
│   ├── memory/
│   └── skills/
├── specialists/             # Specialist YAML definitions
│   ├── accessibility-specialist.yaml
│   ├── api-specialist.yaml
│   ├── backend-specialist.yaml
│   └── ... (18 specialists)
└── sub-agents/              # Sub-agent definitions
    ├── architect/
    ├── bookkeeper/
    ├── concept-analyzer/
    ├── context-scout/
    ├── documentation-agent/
    ├── first-principles/
    ├── planner/
    ├── research-agent/
    └── validator/
```

## Core Agents

### AnalystAgent
Research and analysis specialist:
- Pattern detection
- Information gathering
- Best practices research

### ArchitectAgent
System design specialist:
- Architecture patterns
- Scalability planning
- Integration design

### DeveloperAgent
Implementation specialist:
- Code generation
- Testing strategies
- Documentation

## BMAD Roles

Business-Multi-Agent-Development (BMAD) role definitions:
- `architecture.py` - System architecture role
- `business.py` - Business analysis role
- `development.py` - Development role
- `framework.py` - Framework specialist role
- `model.py` - AI/ML specialist role

## Specialists

18 specialist definitions in YAML format:
- Accessibility, API, Backend, Compliance
- Data, Database, DevOps, Documentation
- Frontend, Integration, ML, Mobile
- Monitoring, Performance, Research
- Security, Testing, UI/UX

## Managerial Components

### Task Lifecycle
`task_lifecycle.py` - Complete task lifecycle management:
- Planning and creation
- Assignment and execution
- Monitoring and checkpointing
- Review and quality assurance
- Merge and integration
- Cleanup and archival

### Skills
- `team_dashboard.py` - Team management dashboard
- `vibe_kanban_manager.py` - Kanban-style task management

### Memory
- `management_memory.py` - Persistent management memory

## Sub-Agents

Specialized sub-agents for complex tasks:
- **architect** - Architecture analysis
- **bookkeeper** - Record keeping
- **concept-analyzer** - Concept analysis
- **context-scout** - Context gathering
- **documentation-agent** - Documentation generation
- **first-principles** - First principles thinking
- **planner** - Task planning
- **research-agent** - Research tasks
- **validator** - Validation and verification

Each sub-agent has a `SUBAGENT.md` defining its purpose and capabilities.
