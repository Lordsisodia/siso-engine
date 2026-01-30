# Workflow: 06 - Story (Story Implementation)

**Phase:** Implementation
**Purpose:** Implement a single story
**Trigger:** CS (Create Story), DS (Dev Story)
**Agent:** Amelia (Developer)
**Complexity:** Medium
**Time:** 2-8 hours

## Overview

The Story phase implements a single user story:
- Understand requirements
- Write tests
- Implement code
- Review and verify

## Input

- Story description
- Acceptance criteria
- Architecture context

## Output

- Working code
- Tests
- Documentation updates

## Procedure

### Step 1: Understand Story

**Objective:** Clear understanding of requirements

**Actions:**
1. Read story description
2. Review acceptance criteria
3. Check architecture doc
4. Ask clarifying questions

### Step 2: Plan Implementation

**Objective:** Design approach

**Actions:**
1. Identify files to modify
2. Plan test approach
3. Note dependencies
4. Estimate effort

### Step 3: Write Tests

**Objective:** Test-first development

**Actions:**
1. Write failing tests
2. Cover happy path
3. Cover edge cases
4. Verify tests fail correctly

### Step 4: Implement

**Objective:** Make tests pass

**Actions:**
1. Write minimal code
2. Focus on functionality
3. Follow code standards
4. Keep tests passing

### Step 5: Refactor

**Objective:** Clean code

**Actions:**
1. Improve readability
2. Remove duplication
3. Optimize if needed
4. Keep tests green

### Step 6: Verify

**Objective:** Confirm completion

**Actions:**
1. Run all tests
2. Check acceptance criteria
3. Manual verification
4. Update documentation

### Step 7: Review

**Objective:** Quality check

**Actions:**
1. Self-review code
2. Run linters
3. Check for TODOs
4. Prepare for PR

## Story Implementation Checklist

```markdown
## Story: {Name}

**Status:** In Progress → Complete

### Implementation
- [ ] Tests written
- [ ] Code implemented
- [ ] Refactoring done
- [ ] Tests passing

### Quality
- [ ] Self-reviewed
- [ ] Standards followed
- [ ] No TODOs left
- [ ] Documentation updated

### Verification
- [ ] Acceptance criteria met
- [ ] Manual testing done
- [ ] Edge cases handled
- [ ] No regressions
```

## Definition of Done

- Code implemented
- Tests written and passing
- Code reviewed
- Documentation updated
- Acceptance criteria met
- No known bugs

## Verification

- [ ] All acceptance criteria pass
- [ ] Tests cover requirements
- [ ] Code follows standards
- [ ] Documentation updated
- [ ] Ready for integration

## Transition

When story is complete:
- If more stories in sprint → Next **CS/DS**
- If sprint complete → **ER (Epic Retrospective)**
- If issues found → **CC (Course Correction)**
