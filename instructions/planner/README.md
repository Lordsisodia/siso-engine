# Planner Prompts

**Agent Type:** Planning Agent
**Core Philosophy:** "Strategy before tactics"

## Versions

### v4-20260202 (Current)
**File:** `versions/v4-20260202/planner.md`

**Key Features:**
- 7-phase flow integration (matches Executor v4)
- Dual task system (tasks.yaml + queue.yaml)
- Task selection framework with prioritization criteria
- Clear handoff protocol to Executor
- Verification protocol (anti-hallucination)

**Improvements:** See `versions/v4-20260202/improvements.md`

---

### v3-20260202
**File:** `versions/v3-20260202/planner.md`

**Key Features:**
- Verification-aware planning
- Testable acceptance criteria
- Clear definition of "done"
- Integration test requirements

**Improvements:** See `versions/v3-20260202/improvements.md`

---

### v2-20260201
**File:** `versions/v2-20260201/planner.md`

**Key Features:**
- Legacy-based improvements
- Enhanced analysis capabilities
- Better task breakdown

**Improvements:** See `versions/v2-20260201/improvements.md`

---

### v1-20260201
**File:** `versions/v1-20260201/planner.md`

**Key Features:**
- Basic planning loop
- Task creation and prioritization
- Queue management
- Communication with executor

**Improvements:** See `versions/v1-20260201/improvements.md`

## Evolution

```
v1 (Basic) → v2 (Analysis) → v3 (Verification-aware) → v4 (7-phase integrated)
```

## Usage

```bash
# Latest version
cat versions/v4-20260202/planner.md | claude -p

# With dynamic context
cat versions/v4-20260202/planner.md \
    ../../../../5-project-memory/blackbox5/project-structure.md \
    ../../../../5-project-memory/blackbox5/architecture/map.md | claude -p
```

## Key Principles (All Versions)

1. **Analyze before planning** - Understand before deciding
2. **Prioritize ruthlessly** - Not all tasks are equal
3. **Clear specifications** - Executor should know what "done" means
4. **Testable criteria** - Every task must be verifiable
5. **Communicate** - Keep executor informed
