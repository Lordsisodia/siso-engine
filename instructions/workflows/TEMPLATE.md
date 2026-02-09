# Workflow Template for BMAD Skills

**Purpose:** Template showing how to implement A/P/C menu and WIP tracking in skills
**Usage:** Copy this template when creating new BMAD workflows

## Workflow Header

Every workflow skill should start with:

```markdown
# Skill: {Agent Name} - {Workflow Name}

**Purpose:** {One-line description}
**Trigger:** {Command} ({2-letter code})
**Input:** {What the skill needs}
**Output:** {What the skill produces}
**Complexity:** {simple|medium|complex}
```

## Standard Procedure with A/P/C + WIP

```markdown
## Procedure

### {Command}: {Workflow Name}

#### Step 0: A/P/C Menu & WIP Check

**Check for existing WIP:**
1. Search `./wip/{command}-*.md`
2. If found, read most recent WIP file
3. Present menu:

```
[Found existing work: {title}]
[A] Advanced  - Full workflow with all steps
[P] Party     - Multi-agent collaborative mode
[C] Continue  - Resume from {current_step} (Step X of Y)
```

**If Continue (C):**
- Load WIP file
- Skip steps in `stepsCompleted`
- Resume from `currentStep`

**If Party (P):**
- Spawn multiple agents simultaneously
- Coordinate via shared WIP file
- Each agent updates WIP as they complete

**If Advanced (A) or no WIP:**
- Create new WIP file
- Run full workflow sequentially

---

#### Step 1: {First Step Name}

**Actions:**
1. [Action 1]
2. [Action 2]
3. [Action 3]

**Save WIP:**
```yaml
stepsCompleted: [step-1-name]
currentStep: step-2-name
artifacts: [any files created]
```

---

#### Step 2: {Second Step Name}

**Actions:**
1. [Action 1]
2. [Action 2]

**Save WIP:**
```yaml
stepsCompleted: [step-1-name, step-2-name]
currentStep: step-3-name
artifacts: [updated list]
```

---

[Continue for all steps...]

#### Step N: Complete

**Actions:**
1. Final review
2. Update WIP status to `completed`
3. Archive WIP file
4. Output final artifact

**Final WIP:**
```yaml
status: completed
stepsCompleted: [all steps]
currentStep: null
completedAt: ISO8601 timestamp
```
```

## Example: CP (Create PRD) with WIP

```markdown
### CP: Create PRD

#### Step 0: A/P/C Menu

Check `./wip/cp-*.md` for existing work...

[Menu presented if WIP found]

#### Step 1: Discovery

**Objective:** Understand product idea, users, market

**Actions:**
1. Interview user about problem
2. Define target users
3. Identify constraints
4. Document assumptions

**Output:** Discovery notes

**Save WIP:**
```yaml
---
workflow: create-prd
command: CP
status: in_progress
stepsCompleted: [discovery]
currentStep: success-criteria
stepsRemaining:
  - success-criteria
  - user-journeys
  - domain-requirements
  - functional-requirements
  - non-functional-requirements
  - polish
  - complete
context:
  product_idea: "..."
  target_users: [...]
  constraints: [...]
artifacts:
  - ./wip/cp-{name}-discovery.md
---
```

#### Step 2: Success Criteria

**Objective:** Define user/business/technical success

**Actions:**
1. Define user success metrics
2. Define business success metrics
3. Define technical success metrics

**Save WIP:**
Update `stepsCompleted: [discovery, success-criteria]`

[Continue for all 8 steps...]

#### Step 8: Complete

**Actions:**
1. Compile final PRD
2. Move WIP to `status: completed`
3. Archive WIP file to `./wip/archive/`
4. Output: `prd-{name}.md`
```

## WIP File Helper

Include this in every skill for WIP management:

```markdown
## WIP Management

### Create WIP

```yaml
---
workflow: {workflow-name}
command: {COMMAND}
status: in_progress
started: {timestamp}
updated: {timestamp}
stepsCompleted: []
currentStep: step-1-name
stepsRemaining:
  - step-1-name
  - step-2-name
  - step-3-name
context:
  title: "{work title}"
  description: "{brief description}"
artifacts: []
---
```

### Update WIP After Each Step

Update these fields:
- `stepsCompleted` - Add finished step
- `currentStep` - Set to next step
- `stepsRemaining` - Remove finished step
- `updated` - Set to current timestamp
- `artifacts` - Add any new files

### Complete WIP

```yaml
status: completed
stepsCompleted: [all steps]
currentStep: null
completedAt: {timestamp}
```

Then move to `./wip/archive/`
```

## Verification Checklist

- [ ] A/P/C menu presented at start
- [ ] WIP file created on workflow start
- [ ] WIP updated after each step
- [ ] Continue option works correctly
- [ ] Party mode spawns multiple agents
- [ ] Advanced mode runs all steps
- [ ] WIP archived on completion
- [ ] Final artifact produced

## File Locations

| File | Purpose |
|------|---------|
| `./wip/{command}-*.md` | Active WIP files |
| `./wip/archive/` | Completed/abandoned WIP |
| `../../2-engine/.autonomous/workflows/apc-menu-pattern.md` | A/P/C pattern docs |
| `../../2-engine/.autonomous/workflows/wip-tracking-system.md` | WIP system docs |
| `../../2-engine/.autonomous/routes.yaml` | Command routing |
