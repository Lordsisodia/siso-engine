# Workflow: 05 - Sprint (Sprint Planning)

**Phase:** Implementation
**Purpose:** Plan sprint execution
**Trigger:** SP (Sprint Planning)
**Agent:** Bob (SM)
**Complexity:** Medium
**Time:** 1 hour

## Overview

The Sprint phase creates executable sprint plans:
- Sprint goal
- Story selection
- Task breakdown
- Capacity planning

## Input

- Epics and stories
- Team capacity
- Previous velocity

## Output

- `sprint-{number}-plan.md` - Sprint plan
- Task assignments

## Procedure

### Step 1: Review Backlog

**Objective:** Understand available work

**Actions:**
1. Review epic breakdown
2. Check story priorities
3. Note dependencies
4. Identify blockers

### Step 2: Assess Capacity

**Objective:** Know team availability

**Actions:**
1. Check team availability
2. Account for meetings/PTO
3. Calculate effective capacity
4. Apply velocity factor

### Step 3: Select Stories

**Objective:** Choose sprint work

**Actions:**
1. Pull highest priority stories
2. Check against capacity
3. Ensure dependencies met
4. Balance team load

### Step 4: Define Sprint Goal

**Objective:** Unifying objective

**Actions:**
1. Identify common theme
2. Write sprint goal
3. Ensure it's achievable
4. Get team agreement

### Step 5: Break into Tasks

**Objective:** Create executable units

**Actions:**
1. Split stories into tasks
2. Estimate task hours
3. Identify task owners
4. Note dependencies

### Step 6: Commit

**Objective:** Team agreement

**Actions:**
1. Review full plan
2. Check for concerns
3. Adjust if needed
4. Finalize commitment

## Sprint Plan Structure

```markdown
# Sprint {N} Plan: {Project Name}

**Dates:** {start} - {end}
**Sprint Goal:** {One sentence goal}
**Capacity:** {X} story points

---

## Stories

### Story 1: {Name}
**Points:** X
**Owner:** {name}
**Status:** Committed

**Tasks:**
- [ ] Task 1 (Xh) - {owner}
- [ ] Task 2 (Xh) - {owner}

### Story 2: ...

---

## Capacity

| Team Member | Capacity | Allocation |
|-------------|----------|------------|
| {Name} | Xh | Story A, B |

## Risks

| Risk | Mitigation |
|------|------------|
| Risk 1 | Strategy |

## Definition of Done

- [ ] Code complete
- [ ] Tests passing
- [ ] Reviewed
- [ ] Documented
```

## Verification

- [ ] Sprint goal is clear
- [ ] Stories fit capacity
- [ ] Tasks are defined
- [ ] Owners assigned
- [ ] Dependencies noted
- [ ] Team committed

## Transition

When sprint plan is ready, trigger **CS (Create Story)** or **DS (Dev Story)** for implementation.
