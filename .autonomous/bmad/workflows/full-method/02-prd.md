# Workflow: 02 - PRD (Product Requirements Document)

**Phase:** Planning
**Purpose:** Detailed requirements document
**Trigger:** CP (Create PRD)
**Agent:** John (PM)
**Complexity:** High
**Time:** 2-4 hours

## Overview

The PRD phase creates comprehensive requirements covering:
- User journeys
- Functional requirements
- Non-functional requirements
- Domain requirements
- Success criteria

## Input

- Product brief (from Brief phase)
- Stakeholder input
- Technical constraints

## Output

- `prd-{project-name}.md` - Product Requirements Document

## Procedure

### Step 1: Discovery

**Objective:** Deep understanding of needs

**Actions:**
1. Review brief document
2. Interview stakeholders
3. Research competitors
4. Document assumptions

### Step 2: Success Criteria

**Objective:** Define measurable outcomes

**Actions:**
1. Define user success metrics
2. Define business success metrics
3. Define technical success metrics
4. Set acceptance criteria

### Step 3: User Journeys

**Objective:** Map user flows

**Actions:**
1. Identify user personas
2. Map primary journeys
3. Map edge cases
4. Document touchpoints

### Step 4: Domain Requirements

**Objective:** Domain-specific needs

**Actions:**
1. Identify domain entities
2. Define business rules
3. Document compliance needs
4. Map integrations

### Step 5: Functional Requirements

**Objective:** THE CAPABILITY CONTRACT (20-50 FRs)

**Actions:**
1. List all capabilities
2. Prioritize by value
3. Write detailed FRs
4. Link to user journeys

### Step 6: Non-Functional Requirements

**Objective:** Performance, security, reliability

**Actions:**
1. Define performance requirements
2. Document security needs
3. Specify reliability targets
4. Add compliance requirements

### Step 7: Polish

**Objective:** Professional document

**Actions:**
1. Review for completeness
2. Check consistency
3. Add table of contents
4. Final formatting

## PRD Structure

```markdown
# PRD: {Project Name}

**Version:** 1.0
**Date:** {date}
**Author:** John (PM)

---

## 1. Overview

### Problem Statement
### Solution Overview
### Target Users

## 2. Success Criteria

### User Success
### Business Success
### Technical Success

## 3. User Journeys

### Journey 1: {Name}
**Actor:** {User type}
**Goal:** {What they want}
**Steps:**
1. Step one
2. Step two

### Journey 2: {Name}
...

## 4. Domain Requirements

### Entities
### Business Rules
### Compliance

## 5. Functional Requirements

### FR-001: {Requirement name}
**Priority:** Must/Should/Could
**Description:**
**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

### FR-002: ...

## 6. Non-Functional Requirements

### Performance
- Response time: < Xms
- Throughput: X req/s

### Security
- Authentication method
- Authorization model

### Reliability
- Uptime: 99.X%
- Recovery time: < X min

## 7. Out of Scope

What's explicitly not included.

## 8. Appendix

### Glossary
### References
```

## Verification

- [ ] 20-50 functional requirements defined
- [ ] All user journeys mapped
- [ ] NFRs cover performance, security, reliability
- [ ] Success criteria are measurable
- [ ] Document is polished and readable

## Transition

When PRD is complete, trigger **CA (Create Architecture)** to begin Architecture phase.
