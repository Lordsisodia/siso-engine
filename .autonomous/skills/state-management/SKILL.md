---
id: state-management
name: State Management
version: 1.0.0
category: core
description: Update STATE.yaml to reflect current project state
trigger: After task completion, at end of run
inputs:
  - name: task_id
    type: string
    required: true
    description: Task that was completed
  - name: status
    type: string
    required: true
    description: "completed | in_progress | blocked"
  - name: commit_hash
    type: string
    required: false
    description: Git commit hash if available
  - name: result
    type: string
    required: false
    description: "success | partial | failed"
outputs:
  - name: update_status
    type: string
    description: success | failure
  - name: state_path
    type: string
    description: Path to updated STATE.yaml
commands:
  - update-task-status
  - mark-completed
  - set-next-action
  - update-metrics
---

# State Management

## Purpose

Keep STATE.yaml synchronized with actual work completed. Prevent stale roadmap state that causes duplicate work.

## When to Use

- **After task completion** — Mark task as completed
- **After git commit** — Record commit hash in state
- **At run end** — Update metrics, set next action
- **When discovering duplicate** — Mark already-completed work

---

## Problem This Solves

**Before:** Agents would pick up tasks from STATE.yaml that were already completed, wasting time on duplicate work.

**After:** STATE.yaml is always current. Agents see accurate task status.

---

## Command: update-task-status

### Input
- `task_id`: The task identifier (e.g., "TASK-1769862609")
- `status`: New status ("completed", "in_progress", "blocked")
- `commit_hash`: Optional git commit hash
- `result`: "success", "partial", or "failed"

### Process

1. **Read STATE.yaml**
   ```bash
   cat STATE.yaml
   ```

2. **Find task in appropriate section**
   - Check `tasks.active`
   - Check `tasks.backlog`
   - Check `tasks.completed` (if already there, log warning)

3. **Update task record**
   ```yaml
   tasks:
     completed:
       - id: "TASK-1769862609"
         title: "[Original title]"
         completed_at: "2026-02-01T00:50:00Z"
         completed_by: "Legacy"
         commit_hash: "abc123"  # if provided
         result: "success"
   ```

4. **Remove from active/backlog**
   - Remove from `tasks.active` if present
   - Remove from `tasks.backlog` if present

5. **Update timestamps**
   ```yaml
   project:
     last_updated: "2026-02-01T00:50:00Z"
     updated_by: "Legacy"
   ```

6. **Write updated STATE.yaml**

### Output

```yaml
update_result:
  status: "success"
  task_id: "TASK-1769862609"
  previous_status: "in_progress"
  new_status: "completed"
  state_path: "STATE.yaml"
  timestamp: "2026-02-01T00:50:00Z"
```

---

## Command: mark-completed

### Purpose
Mark a task as completed with all required fields.

### Input
- `task_id`: Task identifier
- `commit_hash`: Optional commit hash
- `result`: "success" | "partial" | "failed"

### Process

1. Extract task info from wherever it exists (active, backlog, or plans)
2. Move to `tasks.completed` with full metadata
3. Update project timestamps
4. Log the completion

### Example

```markdown
**Before:**
tasks:
  active:
    - id: "TASK-1769862609"
      title: "Implement BMAD Framework"

**After:**
tasks:
  active: []  # removed
tasks:
  completed:
    - id: "TASK-1769862609"
      title: "Implement BMAD Framework"
      completed_at: "2026-02-01T00:50:00Z"
      completed_by: "Legacy"
      commit_hash: "8536853"
      result: "success"
```

---

## Command: set-next-action

### Purpose
Update the `next_action` field to point to the next unblocked task.

### Process

1. Read `tasks.active` — is there an in-progress task?
2. If yes: Set `next_action` to that task
3. If no: Check `tasks.backlog` for highest priority
4. Update STATE.yaml:
   ```yaml
   tasks:
     next_action: "TASK-[next-id]"
   ```

---

## Command: update-metrics

### Purpose
Update improvement and activity metrics in STATE.yaml.

### Input
- `runs_completed`: Increment by 1
- `learnings_captured`: Increment if learning captured
- `improvements_applied`: Increment if improvement made

### Process

1. Read current metrics
2. Increment appropriate counters
3. Update timestamp
4. Write back

### Example

```yaml
improvement_metrics:
  runs_completed: 48  # was 47
  learnings_captured: 48  # was 47
  last_review: null
  next_review_due: "2026-02-05"
```

---

## Integration with Git Commit

### Recommended Workflow

```markdown
1. Complete task execution
2. Run skill:git-commit
   - Creates commit
   - Returns commit_hash
3. Run skill:state-management
   - Updates task status to "completed"
   - Records commit_hash
   - Sets next_action
   - Updates metrics
4. Both committed together
```

---

## Safety Rules

### Never
- Delete task history (always move to completed)
- Set next_action to a blocked task
- Overwrite without reading first

### Always
- Preserve all task metadata when moving
- Update timestamps
- Validate YAML before writing
- Create backup if STATE.yaml > 100KB

---

## Error Handling

### Task Not Found

```yaml
error: "TASK_NOT_FOUND"
task_id: "TASK-999999"
message: "Task not found in active, backlog, or completed"
action: "Check task ID or search all tasks"
```

### Already Completed

```yaml
warning: "ALREADY_COMPLETED"
task_id: "TASK-1769862609"
existing_completion: "2026-01-31T23:00:00Z"
message: "Task was already marked complete"
action: "Verify this is not duplicate work"
```

### YAML Parse Error

```yaml
error: "YAML_PARSE_ERROR"
message: "Could not parse STATE.yaml"
action: "Manual intervention required"
backup: "STATE.yaml.backup.20260201-005000"
```

---

## Examples

### Example 1: Normal Task Completion

```markdown
**Input:**
- task_id: "TASK-1769862609"
- commit_hash: "8536853"
- result: "success"

**Process:**
1. Found task in tasks.active
2. Moved to tasks.completed with metadata
3. Updated timestamps
4. Set next_action to next unblocked task

**Output:**
update_result:
  status: "success"
  task_id: "TASK-1769862609"
  new_status: "completed"
  next_action: "TASK-1769861933"
```

### Example 2: Discovering Duplicate Work

```markdown
**Scenario:**
Agent starts PLAN-005, discovers TASK-1769800918 already completed it.

**Process:**
1. Check STATE.yaml — PLAN-005 still marked "ready_to_start"
2. Update STATE.yaml:
   - Mark PLAN-005 as completed (by TASK-1769800918)
   - Set next_action to next real task
3. Abort current run with note

**Result:**
STATE.yaml now accurate, no future duplicate attempts
```

---

## Verification

- [ ] STATE.yaml updated with correct timestamp
- [ ] Task moved to completed with full metadata
- [ ] commit_hash recorded (if provided)
- [ ] next_action points to valid next task
- [ ] metrics incremented
- [ ] YAML is valid
- [ ] Changes committed with git-commit
