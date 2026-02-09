# Goals System Guide

**Location:** `goals/`
**Purpose:** Drive work, track progress, connect everything

---

## Quick Start

### For Humans

**Check current goals:**
```bash
cat goals/INDEX.yaml
```

**Add a new goal:**
```bash
cd goals/active
cp ../templates/goal-template.yaml IG-007/goal.yaml
# Edit goal.yaml
mkdir -p IG-007/journal
touch IG-007/timeline.yaml
```

**Update a goal:**
```bash
# Edit the goal file
code goals/active/IG-006/goal.yaml

# Add journal entry
code goals/active/IG-006/journal/2026-02-03.md
```

### For Agents

**Read all goals:**
1. Read `goals/INDEX.yaml` for quick overview
2. Read `goals/core/core-goals.yaml` for perpetual goals
3. Scan `goals/active/` for improvement goals

**Create a task from a goal:**
1. Read goal: `goals/active/IG-XXX/goal.yaml`
2. Find incomplete sub-goal
3. Create task in `tasks/active/TASK-XXX/`
4. Link back: `linked_goal: IG-XXX`
5. Update goal.yaml with new task ID

**Update progress:**
1. Complete task in `tasks/`
2. System auto-updates goal progress
3. Add event to `timeline.yaml`
4. If sub-goal completes, move to next one

---

## Architecture

### Goal Types

**Core Goals (goals/core/)**
- Perpetual - never complete
- Drive the system's purpose
- Have rolling metrics, not completion percentages
- Example: "Continuous Self-Improvement"

**Improvement Goals (goals/active/ and goals/completed/)**
- Specific initiatives with completion criteria
- Broken into sub-goals
- Track progress via linked tasks
- Example: "Restructure BlackBox5 Architecture"

### Folder Structure

```
goals/
├── README.md              # This guide
├── INDEX.yaml             # Auto-generated lookup
├── core/
│   └── core-goals.yaml    # Perpetual goals
├── active/
│   └── IG-XXX/            # Each goal gets folder
│       ├── goal.yaml      # Definition + sub-goals
│       ├── timeline.yaml  # Structured events
│       └── journal/       # Narrative updates
├── completed/
│   └── IG-XXX/            # Archived goals
└── templates/
    └── goal-template.yaml
```

### Key Files

**goal.yaml**
- Goal definition
- Sub-goals (inline, 2-5 items)
- Progress (auto-calculated)
- Links to tasks, decisions, learnings

**timeline.yaml**
- Structured events for agents
- Auto-updated when tasks complete
- Tracks progress over time

**journal/*.md**
- Narrative updates for humans
- Context, decisions, challenges
- Free-form, dated entries

**INDEX.yaml**
- Auto-generated summary
- Quick lookup for agents
- Shows what needs attention

---

## Design Decisions

### Why Sub-Goals Are Inline

Sub-goals are in `goal.yaml`, not separate files, because:
- Typically 2-5 items per goal
- One file read is faster
- If complex enough for separate file, should be separate goal

### Why Both Timeline and Journal

**timeline.yaml**: Structured, machine-readable
- Event types, timestamps, linked IDs
- Agents use for quick status

**journal/*.md**: Narrative, human-readable
- Context, reasoning, lessons
- Humans use for understanding

### Why ID Lists Not Symlinks

Goals link to tasks via IDs, not symlinks:
- Portability across systems
- Version control friendly
- No broken links if files move

### Why Auto-Calculated Progress

Progress updates automatically:
- System of record is task status
- Prevents drift between actual and reported
- Manual override available for edge cases

---

## Integration

### With Tasks

Tasks link back to goals:
```yaml
# In tasks/active/TASK-XXX/task.md
---
task_id: TASK-XXX
linked_goal: IG-006
linked_sub_goal: SG-006-1
---
```

Goal tracks linked tasks:
```yaml
# In goals/active/IG-006/goal.yaml
sub_goals:
  - id: SG-006-1
    linked_tasks:
      - TASK-XXX
```

### With Decisions

Decisions can reference goals:
```yaml
# In decisions/technical/DEC-XXX.md
---
decision_id: DEC-XXX
related_goals:
  - IG-006
---
```

Goal timeline links to decisions:
```yaml
# In goals/active/IG-006/timeline.yaml
events:
  - type: decision_made
    linked_decision: DEC-XXX
```

### With Knowledge

Completed goals extract learnings:
```yaml
# In goals/completed/IG-XXX/goal.yaml
key_learnings: "What we learned"
links:
  learnings:
    - knowledge/learnings/learning-001.md
```

---

## Best Practices

### Writing Good Goals

**Clear name:** "Restructure BlackBox5 Architecture"
**Not:** "Fix stuff"

**Measurable sub-goals:**
- "Migrate 120 tasks" (measurable)
- Not: "Work on tasks" (vague)

**Realistic weights:**
- Sub-goal weights must sum to 100
- Reflect actual effort, not arbitrary

**Specific acceptance criteria:**
- "All runs in agents/{planner,executor}/runs/"
- Not: "Organize runs"

### Maintaining Goals

**Weekly review:**
1. Check INDEX.yaml for blocked goals
2. Update progress percentages
3. Add journal entries for significant events
4. Move completed goals to completed/

**When goals change:**
- Update goal.yaml
- Add to timeline.yaml
- Explain in journal/

**When goals complete:**
1. Move folder to goals/completed/
2. Write outcome.yaml (what happened vs planned)
3. Extract key_learnings
4. Link to knowledge/

---

## Examples

### Creating a Goal

```bash
# 1. Create folder
mkdir -p goals/active/IG-007/journal

# 2. Copy template
cp goals/templates/goal-template.yaml goals/active/IG-007/goal.yaml

# 3. Edit goal.yaml
# - Fill in name, description
# - Define 2-5 sub-goals with weights
# - Set target completion

# 4. Create empty timeline
touch goals/active/IG-007/timeline.yaml

# 5. Update INDEX.yaml (or let system auto-update)
```

### Linking a Task

```yaml
# In goals/active/IG-007/goal.yaml
sub_goals:
  - id: SG-007-1
    linked_tasks:
      - TASK-100  # Add new task ID here

# In tasks/active/TASK-100/task.md
---
task_id: TASK-100
linked_goal: IG-007
linked_sub_goal: SG-007-1
---
```

### Tracking Progress

When TASK-100 completes:
1. Task status changes to "completed"
2. System reads goal.yaml, finds linked sub-goal
3. Calculates new progress percentage
4. Updates goal.yaml progress section
5. Adds event to timeline.yaml

---

## Troubleshooting

**Goal progress not updating:**
- Check that task has correct `linked_goal` ID
- Verify task status is "completed"
- Check that sub-goal weights sum to 100

**Can't find a goal:**
- Check INDEX.yaml for quick lookup
- Look in core/ (perpetual) vs active/ (improvement)
- Check completed/ if recently finished

**Sub-goal too complex:**
- If sub-goal needs its own sub-goals, make it a separate goal
- Link via `parent_goal` in new goal
- Update original goal to reference new goal

---

## Questions?

See `goals/README.md` for philosophy and `goals/templates/goal-template.yaml` for examples.
