# Workflow: 04 - Epics (Story Breakdown)

**Phase:** Solutioning
**Purpose:** Break PRD into implementable stories
**Trigger:** CE (Create Epics)
**Agent:** John (PM) or Bob (SM)
**Complexity:** Medium
**Time:** 1-2 hours

## Overview

The Epics phase breaks down requirements into:
- Epics (large bodies of work)
- Stories (implementable units)
- Dependencies and sequencing

## Input

- PRD document
- Architecture document
- Team capacity

## Output

- `epics-{project-name}.md` - Epic breakdown
- Stories ready for sprint planning

## Procedure

### Step 1: Read PRD

**Objective:** Understand all requirements

**Actions:**
1. Read PRD thoroughly
2. Note all functional requirements
3. Identify technical requirements
4. Map dependencies

### Step 2: Group into Epics

**Objective:** Organize by theme

**Actions:**
1. Group related capabilities
2. Name each epic
3. Define epic scope
4. Identify epic dependencies

### Step 3: Break into Stories

**Objective:** Create implementable units

**Actions:**
1. Split epics into stories
2. Ensure INVEST criteria
3. Write story descriptions
4. Define acceptance criteria

### Step 4: Prioritize

**Objective:** Order by value and dependency

**Actions:**
1. Assess business value
2. Map technical dependencies
3. Sequence stories
4. Identify MVP

### Step 5: Estimate

**Objective:** Size the work

**Actions:**
1. Estimate story points
2. Identify risks
3. Note uncertainties
4. Buffer for unknowns

## Epic Document Structure

```markdown
# Epics: {Project Name}

**Date:** {date}
**Author:** {agent name}

---

## Epic 1: {Epic Name}

**Description:**
**Priority:** High/Medium/Low
**Dependencies:** None | Epic X

### Stories

#### Story 1.1: {Story Name}
**As a** {user}
**I want** {capability}
**So that** {benefit}

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

**Points:** X
**Priority:** High/Medium/Low

#### Story 1.2: ...

## Epic 2: ...

---

## Priority Matrix

| Epic | Priority | Est. Points | Dependencies |
|------|----------|-------------|--------------|
| Epic 1 | High | X | None |
| Epic 2 | Medium | Y | Epic 1 |

## Sprint Recommendations

### Sprint 1
- Story 1.1
- Story 1.2

### Sprint 2
- Story 2.1
- Story 2.2
```

## Story Criteria (INVEST)

- **I**ndependent - Can be developed separately
- **N**egotiable - Details can be discussed
- **V**aluable - Delivers user value
- **E**stimable - Can be sized
- **S**mall - Fits in sprint
- **T**estable - Has acceptance criteria

## Verification

- [ ] All PRD requirements covered
- [ ] Stories follow INVEST
- [ ] Dependencies mapped
- [ ] Priorities assigned
- [ ] Estimates provided
- [ ] MVP identified

## Transition

When epics are ready, trigger **SP (Sprint Planning)** to begin Implementation phase.
