# Task System Design

**Date:** 2026-02-02
**Status:** Design Proposal

## Overview

Dual task tracking system separating **planned work** from **ready-to-execute work**.

## Two Files, Different Purposes

### 1. tasks.yaml (Planner's Domain)

**Purpose:** Master list of all planned work

**Managed by:** Planner Agent

**Contains:**
```yaml
tasks:
  - id: "TASK-1769978192"
    title: "Implement verification hook"
    status: planned | ready | blocked
    priority: high
    reasoning: "Prevents hallucination by enforcing file checks"
    plan_doc: "plans/active/verification-system.md"
    context_links:
      - "architecture/hooks.md"
      - "decisions/d-002-hook-enforcement.md"
    dependencies:
      - "TASK-1769978190"
    estimated_effort: "2 hours"
    created_by: "planner"
    created_at: "2026-02-02T10:00:00Z"
    ready_at: null  # Set when fully planned
```

**Updated when:**
- New work identified
- Priorities change
- Plans are completed
- Dependencies resolved

### 2. queue.yaml (Execution Interface)

**Purpose:** What's ready to execute RIGHT NOW

**Managed by:** Planner writes, Executor reads

**Contains:**
```yaml
next_task: "TASK-1769978192"
status: ready
reasoning: "All dependencies complete, plan documented"
context_summary: "Implement file verification in stop hook"
plan_doc: "plans/active/verification-system.md"
updated_at: "2026-02-02T14:00:00Z"
updated_by: "planner"
```

**Updated when:**
- Task becomes ready to execute
- Executor claims a task
- Execution completes
- Blocker encountered

## Flow

```
┌─────────────────────────────────────────────────────────────┐
│  PLANNER                                                    │
│  ├── Analyzes tasks.yaml                                    │
│  ├── Prioritizes based on:                                  │
│  │   - Dependencies (what unblocks other work)              │
│  │   - ROI (highest impact)                                  │
│  │   - Context availability (is plan complete?)              │
│  │   - Strategic goals                                       │
│  ├── Selects next task                                      │
│  └── Updates queue.yaml                                     │
│      next_task: TASK-X                                      │
│      reasoning: "Unblocks 3 other tasks"                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  queue.yaml (single source of truth for executor)           │
│  next_task: TASK-X                                          │
│  reasoning: "Unblocks 3 other tasks"                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  EXECUTOR                                                   │
│  ├── Reads queue.yaml (simple, no reasoning needed)         │
│  ├── Claims task (events.yaml)                              │
│  ├── Reads full task from tasks.yaml                        │
│  └── Executes                                               │
└─────────────────────────────────────────────────────────────┘
```

## Key Principles

1. **Planner owns prioritization** - Complex reasoning about what to do next
2. **queue.yaml is the contract** - Clear handoff point between agents
3. **Executor owns execution** - No prioritization decisions, just execution
4. **tasks.yaml has full context** - Links to plans, reasoning, dependencies
5. **queue.yaml is minimal** - Just what's needed to start work

## Benefits

| Aspect | Benefit |
|--------|---------|
| **Separation** | Planner strategizes, executor tactics |
| **Clarity** | Executor knows exactly what to do |
| **Flexibility** | Planner can reorder without executor knowing |
| **Audit trail** | Full history in tasks.yaml |
| **Performance** | Executor doesn't scan all tasks |

## Files Location

- `tasks.yaml` → `.autonomous/communications/tasks.yaml`
- `queue.yaml` → `.autonomous/communications/queue.yaml`

## Update Frequency

| File | Updated By | Frequency |
|------|------------|-----------|
| tasks.yaml | Planner | As needed (new tasks, status changes) |
| queue.yaml | Planner | When next task changes |
| queue.yaml | Executor | When claiming/completing |
