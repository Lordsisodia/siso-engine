# SessionStart Hook

**Status:** 🚧 In Development
**Priority:** CRITICAL
**Location:** `pipeline/session-start/`
**Language:** Python (decided)

---

## Purpose

Initialize BB5 sessions by:
1. Detecting project and agent type
2. Loading relevant context from memory systems
3. Setting environment variables for the session
4. Injecting context into Claude's memory via JSON output

**Why Python:** Needs robust YAML parsing, complex context assembly, and future API call capability. 40ms startup acceptable for 5-10 min tasks.

---

## Functional Requirements

### Phase 1: Detection (v1.0)

#### 1.1 Project Detection
**Inputs:**
- `BB5_PROJECT` env var (if set)
- `.bb5-project` file in cwd or parent directories
- Current working directory path

**Outputs:**
- `project_name` (e.g., "blackbox5", "siso-internal")
- `project_root` (absolute path)

**Logic:**
1. Check `BB5_PROJECT` env var first
2. Look for `.bb5-project` file in cwd, then walk up tree
3. Parse path for known project patterns (`5-project-memory/{project}`)
4. Default to "blackbox5"

#### 1.2 Agent Type Detection
**Inputs:**
- `BB5_AGENT_TYPE` env var (if set)
- `RALF_RUN_DIR` path patterns
- Current working directory path
- File existence checks
- Git branch name

**Outputs:**
- `agent_type` (planner, executor, architect, scout, verifier, developer)

**Detection Order:**
1. Check `BB5_AGENT_TYPE` env var
2. Check `RALF_RUN_DIR` for agent patterns (`/planner/`, `/executor/`, etc.)
3. Check cwd path for agent patterns
4. Check for agent-specific files:
   - `queue.yaml` or `loop-metadata-template.yaml` → planner
   - `.task-claimed` or `task-*-spec.md` → executor
   - `architecture-review.md` or `system-designs/` → architect
   - `scout-report.md` → scout
   - `verification-report.md` → verifier
5. Check git branch name for agent hints
6. Default to "developer"

#### 1.3 Mode Detection
**Inputs:**
- `RALF_RUN_DIR` env var
- `BB5_AUTONOMOUS` env var
- Context file existence

**Outputs:**
- `mode` ("autonomous" or "manual")

**Logic:**
- If `RALF_RUN_DIR` is set → "autonomous"
- If `BB5_AUTONOMOUS=true` → "autonomous"
- Else → "manual"

---

### Phase 2: Context Loading (v1.1)

#### 2.1 Planner Context
**Files to Read:**
- `5-project-memory/{project}/.autonomous/agents/communications/queue.yaml`
- `5-project-memory/{project}/.autonomous/agents/communications/events.yaml`
- `5-project-memory/{project}/.autonomous/agents/planner/runs/`

**Data to Extract:**
- Queue stats: pending tasks count, completed count
- Recent events (last 5)
- Latest planner run ID
- Executor heartbeat status

**Output Structure:**
```json
{
  "queue": {
    "pending": 12,
    "completed": 45,
    "total": 57
  },
  "recent_events": [...],
  "latest_run": "run-20260206-001",
  "executor_status": "healthy"
}
```

#### 2.2 Executor Context
**Files to Read:**
- `queue.yaml` (find claimed task)
- `5-project-memory/{project}/tasks/active/{task_id}/task.md`

**Data to Extract:**
- Claimed task ID (from queue.yaml where claimed_by matches run_id)
- Task title, objective, acceptance criteria
- Task status

**Output Structure:**
```json
{
  "claimed_task": {
    "id": "TASK-001",
    "title": "Implement feature X",
    "status": "in_progress",
    "acceptance_criteria": [...]
  }
}
```

#### 2.3 Architect Context
**Files to Read:**
- `5-project-memory/{project}/goals/INDEX.yaml`
- `5-project-memory/{project}/decisions/`

**Data to Extract:**
- Active goals count
- Recent decisions (last 3)

#### 2.4 Scout/Verifier/Developer Context
**Files to Read:**
- Basic project info
- Recent activity from timeline

---

### Phase 3: Environment Setup (v1.0)

**Environment Variables to Set:**
```bash
export BB5_PROJECT="{project_name}"
export BB5_AGENT_TYPE="{agent_type}"
export BB5_MODE="{mode}"
export BB5_CONTEXT_LOADED="true"
export BB5_HOOK_VERSION="1.0.0"
```

**Method:** Append to `CLAUDE_ENV_FILE` (only SessionStart can do this)

---

### Phase 4: JSON Output (v1.0)

**Output Format:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "BB5 Session Initialized | Project: {project} | Agent: {agent} | Mode: {mode}",
    "project": "{project_name}",
    "agentType": "{agent_type}",
    "mode": "{mode}",
    "context": {
      // Agent-specific context from Phase 2
    }
  }
}
```

---

## Technical Architecture

### File Structure
```
session-start/
├── README.md              # This file
├── versions/
│   └── v1/
│       ├── hook.py        # Main implementation
│       ├── lib/
│       │   ├── __init__.py
│       │   ├── detector.py    # Detection logic
│       │   ├── context.py     # Context loading
│       │   └── output.py      # JSON output formatting
│       ├── requirements.txt
│       └── IMPROVEMENTS.md
```

### Module Breakdown

#### `detector.py`
Functions:
- `detect_project()` → str
- `detect_agent_type()` → str
- `detect_mode()` → str
- `get_run_id()` → str (from RALF_RUN_DIR or cwd)

#### `context.py`
Functions:
- `load_planner_context(project_root, run_id)` → dict
- `load_executor_context(project_root, run_id)` → dict
- `load_architect_context(project_root)` → dict
- `load_default_context(project_root)` → dict

#### `output.py`
Functions:
- `format_json_output(project, agent_type, mode, context)` → str
- `set_environment_vars(project, agent_type, mode)` → bool

#### `hook.py` (main)
- Parse stdin (Claude Code JSON input)
- Call detection functions
- Call context loading (based on agent type)
- Set environment variables
- Output JSON

---

## Dependencies

### Required
- Python 3.8+
- PyYAML (for robust YAML parsing)
- jq (system dependency for JSON validation)

### Optional (Future)
- requests (for API calls)
- pydantic (for data validation)

---

## Error Handling

### Graceful Degradation
- If project detection fails → default to "blackbox5"
- If agent detection fails → default to "developer"
- If context loading fails → continue with basic info
- If env var setting fails → log error but don't crash
- Always output valid JSON (even on error)

### Error Output
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "BB5 Session Initialized (with errors) | Check logs",
    "project": "unknown",
    "agentType": "unknown",
    "mode": "manual",
    "errors": ["error message 1", "error message 2"]
  }
}
```

---

## Performance Budget

| Phase | Target Time |
|-------|-------------|
| Detection | <20ms |
| Context Loading | <50ms |
| Env Setup | <10ms |
| JSON Output | <10ms |
| **Total** | **<100ms** |

---

## Testing Strategy

### Unit Tests
- Test each detector function in isolation
- Mock filesystem for file-based detection
- Test context loading with sample YAML files

### Integration Tests
- Run hook in actual BB5 directory
- Verify env vars are set correctly
- Verify JSON output is valid

### Performance Tests
- Measure execution time
- Profile slow operations
- Ensure <100ms total

---

## Future Enhancements (v2.0+)

- [ ] Caching for repeated calls
- [ ] API calls for external context (GitHub, Notion, etc.)
- [ ] Dynamic context based on time of day
- [ ] User preference loading
- [ ] Multi-project workspace support

---

## Configuration

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/2-engine/.autonomous/hooks/active/session-start.py"
          }
        ]
      }
    ]
  }
}
```

---

## Related

- [BB5 Key Thesis](../../../../5-project-memory/blackbox5/.docs/BB5-KEY-THESIS.md)
- [Hooks Main README](../../README.md)
- [Stop Hook](../stop/) (quality gates at session end)
- [SubagentStart Hook](../subagent-start/) (context for subagents)
