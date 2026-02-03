# Executor Prompts

**Agent Type:** Task Execution Agent
**Core Philosophy:** "Code that doesn't integrate is code that doesn't work"

## Versions

### v3-20260202 (Current)
**File:** `versions/v3-20260202/executor.md`

**Key Features:**
- Verification enforcement (anti-hallucination)
- Mandatory file existence checks
- Import verification for Python modules
- "Verify or Die" philosophy

**Improvements:** See `versions/v3-20260202/improvements.md`

---

### v2-20260201
**File:** `versions/v2-20260201/executor.md`

**Key Features:**
- Skill checking (Step 2.5)
- Duplicate detection
- RALF-CONTEXT.md persistence
- BMAD skill integration

**Improvements:** See `versions/v2-20260201/improvements.md`

---

### v1-20260201
**File:** `versions/v1-20260201/executor.md`

**Key Features:**
- Basic executor loop
- Communication system (events.yaml, chat-log.yaml)
- Task claiming and execution
- Run documentation

**Improvements:** See `versions/v1-20260201/improvements.md`

## Evolution

```
v1 (Basic) → v2 (Skills) → v3 (Verification)
```

## Usage

```bash
# Latest version
cat versions/v3-20260202/executor.md | claude -p

# With dynamic context
cat versions/v3-20260202/executor.md \
    ../../../../5-project-memory/blackbox5/project-structure.md \
    ../../../../5-project-memory/blackbox5/architecture/map.md | claude -p
```

## Key Principles (All Versions)

1. **ONE task only** - Never batch multiple tasks
2. **Read before change** - NEVER propose changes to unread code
3. **Check for duplicates** - Search completed tasks before starting
4. **Integration required** - Code must work with existing system
5. **Atomic commits** - One logical change per commit
6. **Test everything** - Every change verified before marking complete
