# Architect Prompts

**Agent Type:** Architecture Agent
**Core Philosophy:** "Structure enables scale"

## Versions

### v4-20260202 (Current)
**File:** `versions/v4-20260202/architect.md`

**Key Features:**
- 7-phase flow integration (matches Planner v4 and Executor v4)
- Clear role definition vs Planner and Executor
- Architecture Decision Records (ADRs)
- State machine for complex architectural work
- Plan review integration

**Improvements:** See `versions/v4-20260202/improvements.md`

---

### v3-20260202
**File:** `versions/v3-20260202/architect.md`

**Key Features:**
- RALF system integration
- Works with planner and executor
- Architecture decisions feed into system
- Multi-agent coordination

**Improvements:** See `versions/v3-20260202/improvements.md`

---

### v2-20260201
**File:** `versions/v2-20260201/architect.md`

**Key Features:**
- Coordinator capabilities
- Multi-agent orchestration
- System-wide architecture planning

**Improvements:** See `versions/v2-20260201/improvements.md`

---

### v1-20260201
**File:** `versions/v1-20260201/architect.md`

**Key Features:**
- Architecture review capabilities
- System design analysis
- Pattern identification

**Improvements:** See `versions/v1-20260201/improvements.md`

## Evolution

```
v1 (Review) → v2 (Coordinate) → v3 (RALF-Integrated) → v4 (7-phase integrated)
```

## Usage

```bash
# Latest version
cat versions/v4-20260202/architect.md | claude -p

# With dynamic context
cat versions/v4-20260202/architect.md \
    ../../../../5-project-memory/blackbox5/project-structure.md \
    ../../../../5-project-memory/blackbox5/architecture/map.md | claude -p
```

## Usage

```bash
# Latest version
cat versions/v3-20260202/architect.md | claude -p

# With dynamic context
cat versions/v3-20260202/architect.md \
    ../../../../5-project-memory/blackbox5/project-structure.md \
    ../../../../5-project-memory/blackbox5/architecture/map.md | claude -p
```

## Key Principles (All Versions)

1. **Design for change** - Architecture must evolve
2. **Document decisions** - Why matters as much as what
3. **Consider integration** - New components must fit
4. **Think system-wide** - Local changes have global effects
5. **Enable others** - Architecture serves the agents
