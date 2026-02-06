# BB5 Stop Hook - Comprehensive Validation Checklist

**Status:** 📋 Research Complete - Ready for Implementation
**Version:** 1.0
**Date:** 2026-02-06

---

## Overview

The Stop hook is BB5's **quality gate and task completion validator**. It fires when Claude is about to stop responding and can **BLOCK completion** until work is properly validated.

**Critical Capability:** Unlike most hooks, Stop can **prevent Claude from stopping**, forcing it to continue working until validation passes.

---

## STOP Hook Input Format

Claude Code sends JSON via stdin:

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/dir",
  "hook_event_name": "Stop",
  "stop_hook_active": false
}
```

**Key field:** `stop_hook_active` - prevents infinite loops

---

## BLOCKING VALIDATIONS (Must Pass to Stop)

These validations **BLOCK** the agent from stopping if they fail:

### 1. Run Documentation Completeness

**Files to Check:**
| File | Min Chars | Min Sections | Required Headers | Optional |
|------|-----------|--------------|------------------|----------|
| `THOUGHTS.md` | 500 | 2 | ## Task, ## Approach | No |
| `RESULTS.md` | 400 | 1 | ## Summary | No |
| `DECISIONS.md` | 200 | 1 | - | No |
| `LEARNINGS.md` | 300 | 1 | - | No |
| `ASSUMPTIONS.md` | 100 | 1 | - | Yes |

**Template Placeholders to Block On:**
- `FILL_ME`
- `UNFILLED`
- `{AGENT_TYPE}`
- `{RUN_ID}`
- `{TASK_ID}`
- Any `{placeholder}` pattern

**Validation Logic:**
```python
# BLOCK if:
- Required file doesn't exist
- Content < min_chars
- Sections < min_sections
- Contains unfilled template placeholders
- Missing required headers
```

### 2. Task Completion Status

**Check if agent claimed a task:**

```python
# Look for task claim indicators:
- .task-claimed file exists in run folder
- RALF_RUN_DIR contains task reference
- THOUGHTS.md references TASK-XXX
- Agent type is "executor"
```

**If task claimed, BLOCK if:**
- No `PROMISE_COMPLETE` marker in RESULTS.md
- Task status not marked complete in queue.yaml
- Acceptance criteria not checked off
- No completion summary in RESULTS.md

**Required Markers in RESULTS.md:**
```markdown
**PROMISE_COMPLETE**
Status: COMPLETE | PARTIAL | BLOCKED
Completion: XX%
```

### 3. Git State Validation

**BLOCK if:**
- Uncommitted changes exist (staged or unstaged)
- Merge conflicts detected
- Working tree is dirty
- Changes not pushed to remote (if branch exists)

**Git Commands to Run:**
```bash
# Check for uncommitted changes
git status --porcelain

# Check for merge conflicts
git diff --name-only --diff-filter=U

# Check current branch
git branch --show-current

# Check if changes pushed
git log --oneline @{u}..HEAD 2>/dev/null
```

**Warning Only (Don't Block):**
- Unpushed commits (warn but allow)
- Branch is behind remote (warn but allow)

### 4. Skill Usage Documentation

**BLOCK if:**
- "Skill Usage for This Task" section missing from THOUGHTS.md
- No skill selection documentation
- Applicable skills identified but no decision recorded

**Required Documentation:**
```markdown
## Skill Usage for This Task (REQUIRED)

**Applicable skills:** [list skills checked or 'None']
**Skill invoked:** [skill name or 'None']
**Confidence:** [percentage if calculated, or N/A]
**Rationale:** [why skill was or wasn't used]
```

### 5. Validation Scripts Pass

**Run These Validators:**

| Script | Purpose | Block On Failure |
|--------|---------|------------------|
| `validate-run-documentation.py` | Check all required docs | Yes |
| `validate-skill-usage.py` | Verify skill checking was done | Yes |
| `validate-ssot.py` | Check STATE.yaml consistency | Yes |

**Execution:**
```python
# Run each validator
# If any return non-zero exit code → BLOCK
# Capture stderr for reason message
```

---

## WARNING VALIDATIONS (Warn but Allow)

These validations **WARN** but don't block:

### 6. Timeline Updates

**Warn if:**
- No timeline entry for this run
- timeline.yaml not updated

**Check:**
```yaml
# Look for recent entry in timeline.yaml
events:
  - timestamp: "2026-02-06T..."  # Should be recent
    type: "task_execution"
    run_id: "{current_run}"
```

### 7. Learning Extraction

**Warn if:**
- LEARNINGS.md has no structured YAML blocks
- No action items extracted
- Learning categories not specified

**Check for:**
```yaml
learning:
  id: "L-{timestamp}-001"
  category: "process|technical|documentation|skills|infrastructure"
  observation: "..."
  impact: "high|medium|low"
  action_item: "..."
```

### 8. Queue Synchronization

**Warn if:**
- queue.yaml not updated with run results
- Task status in queue doesn't match claimed status

**Check:**
```yaml
# Task should be updated in queue.yaml
tasks:
  - id: "TASK-XXX"
    status: "completed"  # Should match claimed status
    completed_at: "..."
    completed_by: "{run_id}"
```

---

## AUTO-ACTIONS (If Validation Passes)

After allowing stop, these actions run asynchronously:

### 9. Task Status Updates

**Move task from active to completed:**
```bash
# Move task folder
mv tasks/active/TASK-XXX tasks/completed/TASK-XXX

# Update task.md status
task_status: "completed"
completed_at: "2026-02-06T..."
completed_by: "{run_id}"
```

**Update queue.yaml:**
```yaml
# Update task entry
tasks:
  - id: "TASK-XXX"
    status: "completed"
    completed_at: "2026-02-06T..."
    completed_by: "{run_id}"
```

### 10. STATE.yaml Synchronization

**Update roadmap state:**
```yaml
# Update plan status
plans:
  - id: "PLAN-XXX"
    status: "completed"
    completed_at: "..."

# Update goal progress
goals:
  - id: "IG-XXX"
    progress_percentage: XX
```

### 11. Learning Extraction (RETAIN)

**Extract learnings to learning-index.yaml:**
```yaml
learnings:
  - id: "L-{timestamp}-001"
    source_run: "{run_id}"
    source_task: "TASK-XXX"
    category: "..."
    observation: "..."
    extracted_at: "..."
```

### 12. Skill Usage Logging

**Update operations/skill-usage.yaml:**
```yaml
usages:
  - timestamp: "..."
    task: "TASK-XXX"
    skill: "skill-name"
    outcome: "success|failure|partial"
    effectiveness: 4
```

### 13. Git Auto-Commit (Optional)

**If configured and clean:**
```bash
# Stage all changes
git add -A

# Create commit
git commit -m "claude: [component] [description]

- Detailed changes
- Task: [TASK-ID]
- Validation: [results]

Co-authored-by: Claude <claude@blackbox5.local>"

# Push if configured
git push origin {branch}
```

### 14. Events Log Update

**Append to events.yaml:**
```yaml
events:
  - timestamp: "2026-02-06T..."
    type: "task_completed"
    task_id: "TASK-XXX"
    run_id: "{run_id}"
    result: "success|partial|blocked"
```

---

## OUTPUT FORMAT

### Block Response (Prevent Stop)

```json
{
  "decision": "block",
  "reason": "THOUGHTS.md is incomplete (only 200 chars, minimum 500). Please document your reasoning before completing.",
  "failures": [
    {
      "category": "documentation",
      "file": "THOUGHTS.md",
      "issue": "insufficient_content",
      "details": "200 chars (min: 500)"
    },
    {
      "category": "git",
      "issue": "uncommitted_changes",
      "details": "3 files have uncommitted changes"
    }
  ],
  "suggested_actions": [
    "Complete THOUGHTS.md with at least 500 characters",
    "Run 'git status' to see uncommitted changes",
    "Commit changes with: git commit -m '...'"
  ]
}
```

### Allow Response (Permit Stop)

```json
{
  "decision": "allow",
  "validations_passed": 8,
  "warnings": 2,
  "auto_actions_triggered": [
    "task_status_updated",
    "queue_synced",
    "learnings_extracted"
  ]
}
```

Or simply exit 0 with no output.

---

## BYPASS MECHANISMS

**Emergency Bypass (Don't Block):**

```bash
# Environment variable
export RALF_SKIP_VALIDATION=1

# Or create skip file
touch .ralf-skip-validation

# Or in hook input JSON
{"stop_hook_active": true}  # Prevents infinite loops
```

---

## PERFORMANCE BUDGET

| Phase | Target Time |
|-------|-------------|
| Documentation validation | <100ms |
| Git state check | <50ms |
| Task status check | <50ms |
| Validation scripts | <200ms |
| **Total (blocking)** | **<400ms** |
| Auto-actions (async) | <500ms |

---

## EXIT CODES

| Code | Behavior |
|------|----------|
| **0** | Success - Claude stops (unless JSON contains `decision: "block"`) |
| **2** | Blocking error - prevents stop, stderr shown to Claude |
| **Other** | Non-blocking error - stderr shown in verbose mode only |

---

## CONFIGURATION

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/2-engine/.autonomous/hooks/active/stop.py",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

---

## IMPLEMENTATION ARCHITECTURE

```
stop/
├── README.md              # This file
├── STOP_HOOK_CHECKLIST.md # Comprehensive checklist
├── versions/
│   └── v1/
│       ├── hook.py        # Main implementation
│       ├── lib/
│       │   ├── __init__.py
│       │   ├── validator.py   # Validation logic
│       │   ├── actions.py     # Auto-actions
│       │   └── output.py      # JSON output formatting
│       ├── validators/        # Individual validators
│       │   ├── documentation.py
│       │   ├── git_state.py
│       │   ├── task_status.py
│       │   └── skill_usage.py
│       ├── requirements.txt
│       └── IMPROVEMENTS.md
```

---

## SUMMARY: WHAT THE STOP HOOK MUST DO

### Phase 1: Parse Input
1. Read JSON from stdin
2. Check `stop_hook_active` to prevent infinite loops
3. Check bypass flags (`RALF_SKIP_VALIDATION`, `.ralf-skip-validation`)

### Phase 2: Run Validations (Blocking)
4. **Documentation Check** - All 5 files present, filled, no placeholders
5. **Task Completion Check** - If claimed, must have PROMISE_COMPLETE
6. **Git State Check** - No uncommitted changes, no conflicts
7. **Skill Usage Check** - Documented in THOUGHTS.md
8. **Validation Scripts** - All pass (validate-run-docs, validate-ssot, etc.)

### Phase 3: Decide
9. If any blocking check fails → Output `{"decision": "block", ...}`
10. If all pass → Output `{"decision": "allow"}` or exit 0

### Phase 4: Auto-Actions (Async)
11. Update task status (active → completed)
12. Update queue.yaml
13. Sync STATE.yaml
14. Extract learnings to learning-index.yaml
15. Log skill usage
16. Auto-commit if configured
17. Update events.yaml

---

## RELATED DOCUMENTATION

- [BB5 Key Thesis](../../../../5-project-memory/blackbox5/.docs/BB5-KEY-THESIS.md)
- [SessionStart Hook](../session-start/README.md)
- [Task Completion Workflow](../../../../2-engine/.autonomous/workflows/task-completion.yaml)
- [Run Documentation Validation](../../../../5-project-memory/blackbox5/bin/validate-run-documentation.py)
- [SSOT Validation](../../../../5-project-memory/blackbox5/bin/validate-ssot.py)

---

*Generated from comprehensive research across BB5 architecture, templates, and validation scripts*
