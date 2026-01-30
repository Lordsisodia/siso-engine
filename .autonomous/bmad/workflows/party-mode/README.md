# Party Mode (Multi-Agent Sessions)

**Purpose:** True parallel multi-agent execution
**Status:** Design document - implementation pending
**Location:** `2-engine/.autonomous/bmad/workflows/party-mode/`

## Overview

Party Mode enables multiple BMAD agents to work simultaneously on complex tasks, coordinating through a shared workspace.

## Session Types

### Planning Session
**Agents:** PM, Architect, Analyst
**Use Case:** Complex product planning
**Duration:** 1-2 hours

### Troubleshooting Session
**Agents:** Developer, Architect, QA
**Use Case:** Critical bug resolution
**Duration:** 30-60 minutes

### Design Session
**Agents:** UX, Architect, Frontend Dev
**Use Case:** Complex UI/UX design
**Duration:** 1-2 hours

### Review Session
**Agents:** QA, Developer, PM
**Use Case:** Comprehensive review
**Duration:** 30-60 minutes

## Architecture

```
Party Session
├── Coordinator (orchestrates)
├── Shared WIP File (state)
├── Agent A (working)
├── Agent B (working)
└── Agent C (working)
```

## Workflow

1. **Initiation**
   - User selects Party Mode
   - Choose session type
   - Spawn coordinator

2. **Setup**
   - Coordinator creates shared WIP
   - Spawns specialized agents
   - Distributes context

3. **Execution**
   - Agents work in parallel
   - Update shared WIP
   - Coordinator monitors

4. **Integration**
   - Agents complete work
   - Coordinator synthesizes
   - Produce final output

## Shared WIP Format

```yaml
---
session_type: planning
agents:
  - bmad-pm
  - bmad-architect
  - bmad-analyst
coordinator: bmad-pm
status: active
started: 2026-01-30T10:00:00Z
workstreams:
  pm:
    status: in_progress
    task: requirements gathering
    output: ./party/pm-output.md
  architect:
    status: in_progress
    task: technical constraints
    output: ./party/arch-output.md
  analyst:
    status: waiting
    task: market research
    output: ./party/analyst-output.md
---
```

## Implementation Status

- [ ] Coordinator agent logic
- [ ] Shared WIP synchronization
- [ ] Agent spawning protocol
- [ ] Conflict resolution
- [ ] Output synthesis

## Future Work

Party Mode requires significant infrastructure:
- Parallel agent execution
- State synchronization
- Conflict resolution
- Result synthesis

This is a Phase 2 enhancement after core BMAD workflows are stable.
