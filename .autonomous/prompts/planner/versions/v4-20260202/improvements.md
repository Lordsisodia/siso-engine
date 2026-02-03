# Version 4 Improvements

**Date:** 2026-02-02
**Previous:** v3-20260202

## Key Changes

### 1. 7-Phase Flow Integration
- Clear phase-by-phase execution structure matching Executor v4
- Hook-enforced phases (1 and 7) marked clearly
- Planner responsibilities defined for each phase

### 2. Dual Task System Alignment
- Clear distinction between `tasks.yaml` (Planner's domain) and `queue.yaml` (execution interface)
- Planner writes to both files (owns prioritization)
- Executor reads `queue.yaml` only (no prioritization decisions)

### 3. Task Selection Framework
- Explicit prioritization criteria:
  1. Dependency unblocking
  2. ROI
  3. Context availability
  4. Strategic alignment
  5. Executor capacity
- Anti-patterns documented (what NOT to prioritize by)

### 4. Plan Documentation Structure (Phase 4)
- For complex tasks (> 30 min)
- Creates planning directory with:
  - plan.md (goal, approach, steps, risks)
  - acceptance-criteria.md (P0/P1 criteria)

### 5. Unified Best Practices
- v3's verification protocol (anti-hallucination)
- Clear handoff protocol to Executor
- Communication via chat-log.yaml

### 6. Heartbeat Integration
- Updates heartbeat.yaml with current action
- Tracks planner status separately from executor

## Rationale

v4 brings the Planner into alignment with the 7-phase system:
- **Phase structure** from our 7-phase design
- **Verification** from v3 (prevents executor hallucination)
- **Task system** with clear Planner/Executor separation
- **Handoff protocol** for clean transitions

The result is a Planner that:
1. Analyzes all tasks (reads `tasks.yaml`)
2. Makes strategic decisions (prioritization framework)
3. Communicates clearly (writes `queue.yaml`)
4. Documents properly (4-file structure)
5. Verifies claims (hallucination detection)

## Alignment with Executor v4

| Aspect | Planner v4 | Executor v4 |
|--------|------------|-------------|
| **Phase 1** | Hook creates run folder | Same |
| **Phase 3** | Analyze, prioritize, write `queue.yaml` | Read `queue.yaml`, claim task |
| **Phase 4** | Create plan documents | Create task working folder |
| **Phase 5** | Handoff to Executor | Execute with verification |
| **Phase 6** | Document decisions | Document execution |
| **Phase 7** | Hook validates and archives | Same |

**Contract:** `queue.yaml` is the single source of truth for what to execute next.
