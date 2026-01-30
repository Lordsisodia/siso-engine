# Workflow: 03 - Arch (Architecture Design)

**Phase:** Planning
**Purpose:** Technical architecture and design
**Trigger:** CA (Create Architecture)
**Agent:** Winston (Architect)
**Complexity:** High
**Time:** 2-4 hours

## Overview

The Arch phase creates technical architecture covering:
- System components
- Interface contracts
- Technology choices
- Architecture Decision Records (ADRs)

## Input

- PRD document
- Existing system context
- Technical constraints

## Output

- `architecture-{project-name}.md` - Architecture document
- `adr-{number}-{decision}.md` - Architecture Decision Records

## Procedure

### Step 1: Understand Context

**Objective:** Read and understand requirements

**Actions:**
1. Read PRD thoroughly
2. Identify constraints
3. Review existing systems
4. Note integration points

### Step 2: Identify Constraints

**Objective:** Document all limitations

**Actions:**
1. List technical constraints
2. List business constraints
3. List organizational constraints
4. Document trade-offs

### Step 3: Define Components

**Objective:** System decomposition

**Actions:**
1. Identify major components
2. Define responsibilities
3. Map dependencies
4. Draw component diagram

### Step 4: Design Interfaces

**Objective:** API and data contracts

**Actions:**
1. Define API endpoints
2. Specify data models
3. Document error handling
4. Define authentication

### Step 5: Select Patterns

**Objective:** Architectural patterns

**Actions:**
1. Evaluate pattern options
2. Select appropriate patterns
3. Document rationale
4. Note implementation notes

### Step 6: Document Decisions (ADRs)

**Objective:** Record key decisions

**Actions:**
1. Identify decision points
2. Document options considered
3. Record chosen approach
4. Explain rationale

### Step 7: Define Standards

**Objective:** Coding and design standards

**Actions:**
1. Document naming conventions
2. Define code organization
3. Specify testing approach
4. Set documentation standards

## Architecture Document Structure

```markdown
# Architecture: {Project Name}

**Version:** 1.0
**Date:** {date}
**Author:** Winston (Architect)

---

## 1. Overview

### Context
### Goals
### Constraints

## 2. System Components

### Component Diagram
```
[Diagram description]
```

### Component Descriptions

#### Component A
**Responsibility:**
**Interfaces:**
**Dependencies:**

## 3. Interface Contracts

### API Endpoints

#### POST /api/resource
**Description:**
**Request:**
```json
{}
```
**Response:**
```json
{}
```

### Data Models

## 4. Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Frontend | X | Reason |
| Backend | Y | Reason |
| Database | Z | Reason |

## 5. Architecture Decisions

### ADR-001: {Decision Title}
**Status:** Proposed | Accepted | Deprecated
**Context:**
**Decision:**
**Consequences:**

## 6. Standards

### Code Organization
### Naming Conventions
### Testing Standards

## 7. Deployment

### Infrastructure
### CI/CD Pipeline
### Monitoring
```

## Verification

- [ ] All PRD requirements addressed
- [ ] Components clearly defined
- [ ] Interfaces specified
- [ ] ADRs written for major decisions
- [ ] Standards documented
- [ ] Diagrams created

## Transition

When architecture is complete, trigger **CE (Create Epics)** to begin Solutioning phase.
