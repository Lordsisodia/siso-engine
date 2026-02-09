# RALF Infrastructure Guide

How the RALF autonomous system is organized.

---

## Architecture: Engine + Project Memory

RALF is split into two parts:

### 1. Engine (`2-engine/.autonomous/`)
**What:** How to run - the code that executes
**Contains:**
- `shell/ralf-loop.sh` - Main entry point
- `lib/` - Python libraries (session_tracker, state_machine, workspace)
- `prompts/` - Prompt templates
- `skills/` - Skill definitions

### 2. Project Memory (`5-project-memory/{project}/.autonomous/`)
**What:** What to do - tasks, runs, learnings
**Contains:**
- `tasks/active/` - Pending tasks
- `runs/` - Run history
- `workspaces/` - Per-task workspaces
- `memory/` - Decisions and insights
- `routes.yaml` - Project configuration

---

## Current Projects

| Project | Path | Purpose |
|---------|------|---------|
| **siso-internal** | `5-project-memory/siso-internal/` | The SISO web app |
| **ralf-core** | `5-project-memory/ralf-core/` | Improving RALF itself |

---

## How RALF Knows Where Things Are

When RALF starts, it reads:
1. **Environment variables** set by the loop script:
   - `RALF_PROJECT_DIR` - Where the project memory is
   - `RALF_ENGINE_DIR` - Where the engine is

2. **Project's `routes.yaml`** - Project-specific paths

---

## Task Files

**Location:** `{project}/.autonomous/tasks/active/`

**Format:** Markdown with YAML frontmatter

**Naming:**
- Regular tasks: `TASK-YYYY-MM-DD-NNN.md`
- RALF improvements: `RALF-YYYY-MM-DD-NNN.md`

---

## Running RALF

```bash
# From a project with .autonomous/
./.autonomous/ralf

# Or directly with engine
../../blackbox5/2-engine/.autonomous/shell/ralf-loop.sh /path/to/project
```

---

## Feedback System

Projects can send feedback to RALF-CORE:

```
Project feedback/ → RALF-CORE feedback/incoming/
```

This helps RALF improve itself based on real usage.

---

## What to Ignore (Legacy BB5)

**Old systems not used by RALF:**
- `2-engine/07-operations/runtime/task_registry/` - Old Python system
- `2-engine/07-operations/runtime/ralphy/` - Old shell scripts
- `2-engine/01-core/` - Documentation only
- `2-engine/02-agents/` - Empty

RALF uses its own simpler file-based system.

---

## After Completing Work

1. Update task file in `{project}/.autonomous/tasks/active/`
2. Update project `STATE.yaml` if it exists
3. Document learnings in `{project}/.autonomous/memory/insights/`
4. Submit feedback if you encountered issues
