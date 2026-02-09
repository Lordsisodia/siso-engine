# Version 4 Improvements

**Date:** 2026-02-02
**Previous:** v3-20260202

## Key Changes

### 1. 7-Phase Flow Integration
- Clear phase-by-phase execution structure
- Hook-enforced phases (1 and 7) marked clearly
- Executor responsibilities defined for each phase

### 2. Dual Task System Support
- Clear distinction between `tasks.yaml` (Planner's domain) and `queue.yaml` (execution interface)
- Executor reads from `queue.yaml` (simple)
- Gets full context from `tasks.yaml` (rich)
- No prioritization reasoning - just execution

### 3. Task Claiming Mechanism
- Explicit claim step via `events.yaml`
- Prevents duplicate execution
- Clear idle behavior when no task assigned

### 4. Task Folder Creation (Phase 4)
- For complex tasks (> 30 min)
- Creates working directory with:
  - README.md (goal, plan, progress)
  - TASK-CONTEXT.md (from Planner)
  - ACTIVE-CONTEXT.md (for Executor discoveries)

### 5. Unified Best Practices
- v3's verification (anti-hallucination)
- v2's skill checking (Step 2.5)
- Dynamic context loading (project-structure, architecture)
- Clear communication protocol

### 6. Improved Documentation
- THOUGHTS.md with Skill Usage section (mandatory)
- RESULTS.md with Verification Evidence (mandatory)
- DECISIONS.md for key choices
- metadata.yaml for machine-readable state

## Rationale

v4 brings together all the learnings:
- **Phase structure** from our 7-phase design
- **Verification** from v3 (prevents hallucination)
- **Skills** from v2 (leverages BMAD framework)
- **Context loading** from our dynamic prompt system
- **Task system** with clear Planner/Executor separation

The result is an executor that:
1. Knows exactly what to do (reads `queue.yaml`)
2. Knows how to do it (skills + verification)
3. Documents properly (4-file structure)
4. Communicates clearly (events, chat-log)
