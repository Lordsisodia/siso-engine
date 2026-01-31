---
id: task-selection
name: Task Selection
version: 1.0.0
category: core
description: Select the next task to work on from STATE.yaml
trigger: At start of every run, when current task completes
inputs:
  - name: state_path
    type: string
    required: false
    default: STATE.yaml
    description: Path to STATE.yaml file
  - name: current_run
    type: string
    required: true
    description: Current run ID
outputs:
  - name: selected_task
    type: object
    description: Task to work on
  - name: selection_reasoning
    type: string
    description: Why this task was selected
commands:
  - select-next-task
  - check-dependencies
  - prioritize
---

# Task Selection

## Purpose

Choose the highest-value task that can be worked on right now, considering dependencies, priority, and context.

## When to Use

- At the start of every run
- When current task completes
- When task becomes blocked

---

## Command: select-next-task

### Input
- `state_path`: Path to STATE.yaml
- `current_run`: Current run ID

### Process

1. **Load STATE.yaml**
   - Read all tasks
   - Extract active_tasks and in_progress tasks

2. **Filter eligible tasks**
   - Status must be: `pending` or `in_progress`
   - Current run must not be at capacity

3. **Check dependencies**
   - For each candidate, check `dependencies.requires`
   - All required tasks must be `completed`
   - If dependencies not met, skip

4. **Sort by priority**
   - Order: `critical` > `high` > `medium` > `low`
   - Within same priority: earliest created first

5. **Apply context filters**
   - Check MCP availability matches `mcp_requirements`
   - Verify context window can handle `context_window_estimate`

6. **Select top task**
   - First task in sorted list
   - Record selection reasoning

7. **Update STATE.yaml**
   - Set `current_run` on selected task
   - Add run to `runs` array
   - Update `status` to `in_progress` if pending

8. **Return selection**
   - Task ID and file path
   - Selection reasoning
   - Dependencies status

### Output

```yaml
selected_task:
  id: "LEGACY-2026-01-30-001"
  file: "tasks/TASK-2026-01-30-001.md"
  name: "Task Name"
  priority: "high"
  status: "in_progress"

selection_reasoning: |
  Selected LEGACY-2026-01-30-001 because:
  1. Highest priority (high) among eligible tasks
  2. All dependencies met (0 required)
  3. MCP requirements available (filesystem)
  4. Context window adequate (small)

dependencies_status:
  all_met: true
  required: []
  blocking: []
```

---

## Command: check-dependencies

### Input
- `task_id`: Task to check
- `state_path`: Path to STATE.yaml

### Process

1. Find task in STATE.yaml
2. Extract `dependencies.requires` list
3. For each required task ID:
   - Find task in STATE.yaml
   - Check status is `completed`
   - If not completed, mark as blocking
4. Return dependency status

### Output

```yaml
dependencies_status:
  task_id: "LEGACY-2026-01-30-005"
  all_met: false
  required:
    - "LEGACY-2026-01-30-001"
    - "LEGACY-2026-01-30-002"
  completed:
    - "LEGACY-2026-01-30-001"
  pending:
    - "LEGACY-2026-01-30-002"
  blocking:
    - task: "LEGACY-2026-01-30-002"
      reason: "status is pending, not completed"
```

---

## Command: prioritize

### Input
- `tasks`: Array of eligible tasks

### Process

1. **Sort by priority**
   ```
   critical (1) > high (2) > medium (3) > low (4)
   ```

2. **Within same priority, sort by:**
   - Created date (earlier first)
   - Effort estimate (smaller first)
   - Number of tasks blocked (more blocked = higher)

3. **Return sorted list**

### Priority Rules

| Priority | When to Use | Response Time |
|----------|-------------|---------------|
| Critical | Blocking release, security issue, data loss | Immediate |
| High | Core feature, significant value | Same day |
| Medium | Enhancement, nice-to-have | This week |
| Low | Cleanup, refactoring, docs | When possible |

---

## Examples

### Example 1: Simple Selection

```markdown
**STATE.yaml:**
- Task A: pending, high
- Task B: pending, medium
- Task C: in_progress, high (assigned to other run)

**Process:**
1. Load: 3 tasks found
2. Filter: Task A (pending), Task B (pending), Task C (in_progress - skip)
3. Dependencies: Both have no requirements
4. Sort: Task A (high) > Task B (medium)
5. Select: Task A

**Output:**
selected_task:
  id: "LEGACY-2026-01-30-001"  # Task A
  priority: "high"
```

### Example 2: Dependency Blocking

```markdown
**STATE.yaml:**
- Task A: pending, high, requires: [Task B]
- Task B: pending, high
- Task C: pending, medium

**Process:**
1. Load: 3 tasks
2. Filter: All pending
3. Dependencies:
   - Task A: requires Task B (pending) → BLOCKED
   - Task B: no requirements → OK
   - Task C: no requirements → OK
4. Eligible: Task B, Task C
5. Sort: Task B (high) > Task C (medium)
6. Select: Task B

**Output:**
selected_task:
  id: "LEGACY-2026-01-30-002"  # Task B

dependencies_status:
  note: "Task A was higher priority but blocked by this task"
```

---

## Error Handling

### No Tasks Available

```yaml
error: "NO_TASKS_AVAILABLE"
message: "No pending or in_progress tasks found"
action: "Check STATE.yaml or create new tasks"
```

### All Tasks Blocked

```yaml
error: "ALL_TASKS_BLOCKED"
message: "Tasks exist but all have unmet dependencies"
blocked_tasks:
  - task: "LEGACY-001"
    blocked_by: ["LEGACY-002"]
  - task: "LEGACY-003"
    blocked_by: ["LEGACY-004"]
action: "Complete blocking tasks first"
```

### Circular Dependencies

```yaml
error: "CIRCULAR_DEPENDENCY"
message: "Tasks have circular dependency"
cycle: ["LEGACY-001", "LEGACY-002", "LEGACY-001"]
action: "Human intervention required to resolve"
```
