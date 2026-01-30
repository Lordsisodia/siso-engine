# Task Selection Procedure

How Ralph picks what to work on.

---

## Selection Algorithm

**Step 1: Read STATE.yaml**
```yaml
Look for: active_tasks with status: "pending" or "ready_for_dev"
```

**Step 2: Filter by Dependencies**
- Check `requires` field
- All dependencies must be `completed`
- Skip tasks with unmet dependencies

**Step 3: Prioritize**
1. Priority: `high` > `medium` > `low`
2. Created: oldest first
3. Project: e-commerce > siso-internal

**Step 4: Verify Context**
- Task file exists
- PRD/epic available (if referenced)
- You have all needed context

---

## Selection Rules

- **ONE task only** — never pick multiple
- **Smallest scope wins** — if uncertain, pick the smaller task
- **Ready for dev** — task must be actionable, not just planned

---

## Sub-Agent for Complex Selection

If task selection is complex, spawn a selector:

```bash
# Task: "Analyze STATE.yaml and recommend next task based on dependencies and priority"
# Output: task-selection-result.json
```

---

## Marking In Progress

Once selected:
1. Update task file in `$RALF_PROJECT_DIR/tasks/active/`: status → `in_progress`
2. Update project STATE.yaml if it exists: started_at timestamp
3. Log learnings to `$RALF_PROJECT_DIR/memory/insights/`
