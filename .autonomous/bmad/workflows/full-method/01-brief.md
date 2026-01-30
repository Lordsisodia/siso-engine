# Workflow: 01 - Brief (Product Brief)

**Phase:** Analysis
**Purpose:** Create executive product brief
**Trigger:** CB (Create Brief), BP (Brainstorm Project)
**Agent:** Mary (Analyst) or John (PM)
**Complexity:** Medium
**Time:** 30-60 minutes

## Overview

The Brief phase creates a concise executive document that captures:
- Problem statement
- Target users
- Solution hypothesis
- Success metrics
- Key constraints

## Input

- Product idea or problem statement
- Market context
- Stakeholder input

## Output

- `brief-{project-name}.md` - Product brief document

## Procedure

### Step 0: A/P/C Menu

Check for existing WIP in `../../wip/cb-*.md` or `../../wip/bp-*.md`

### Step 1: Problem Definition

**Objective:** Clearly articulate the problem

**Actions:**
1. Interview stakeholders about pain points
2. Quantify the problem (frequency, impact)
3. Identify who has this problem
4. Document current workarounds

**Output:** Problem statement section

### Step 2: Target Users

**Objective:** Define who we're solving for

**Actions:**
1. Identify primary user personas
2. Define secondary users
3. Map user needs to problem
4. Prioritize user segments

**Output:** User definition section

### Step 3: Solution Hypothesis

**Objective:** Propose solution approach

**Actions:**
1. Brainstorm solution options
2. Evaluate feasibility of each
3. Select preferred approach
4. Document rationale

**Output:** Solution hypothesis section

### Step 4: Success Metrics

**Objective:** Define what success looks like

**Actions:**
1. Define user success metrics
2. Define business success metrics
3. Set target values
4. Identify measurement methods

**Output:** Success metrics section

### Step 5: Constraints & Assumptions

**Objective:** Document limitations and assumptions

**Actions:**
1. List technical constraints
2. List business constraints
3. Document key assumptions
4. Identify risks

**Output:** Constraints section

### Step 6: Polish & Finalize

**Objective:** Create executive-ready document

**Actions:**
1. Review for clarity
2. Ensure executive summary is crisp
3. Add visuals if helpful
4. Get stakeholder alignment

**Output:** Final brief document

## Brief Template

```markdown
# Product Brief: {Project Name}

**Date:** {date}
**Author:** {agent name}
**Status:** Draft | Review | Approved

---

## Executive Summary

One-paragraph summary of the problem, solution, and expected outcome.

## Problem Statement

### What is the problem?
Clear, concise problem description.

### Who has this problem?
Target users and their context.

### Current impact
Quantified pain (time lost, money, frustration).

## Solution Hypothesis

### Proposed solution
High-level description of the approach.

### Why this solution?
Key rationale and differentiators.

### Key features
3-5 core capabilities.

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| User adoption | X% | Analytics |
| User satisfaction | X NPS | Surveys |
| Business outcome | $X | Revenue/savings |

## Constraints

### Technical
- Constraint 1
- Constraint 2

### Business
- Budget limit
- Timeline

### Assumptions
- Assumption 1
- Assumption 2

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Risk 1 | High/Med/Low | High/Med/Low | Strategy |

## Next Steps

1. {Next action}
2. {Next action}
```

## Verification

- [ ] Problem clearly articulated
- [ ] Users defined with personas
- [ ] Solution hypothesis testable
- [ ] Metrics are measurable
- [ ] Constraints documented
- [ ] Document is executive-ready

## Transition to Next Phase

When brief is approved, trigger **CP (Create PRD)** to begin Planning phase.
