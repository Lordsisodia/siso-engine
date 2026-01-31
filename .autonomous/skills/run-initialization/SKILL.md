---
name: run-initialization
description: Initialize runs with proper documentation and structure
category: core
trigger: Starting a new run or task
inputs:
  - name: task_description
    type: string
    description: Description of the task to perform
outputs:
  - name: run_folder
    type: directory
    description: Initialized run folder with documentation
---

# Run Initialization

## Purpose

Initialize a new run with proper folder structure, documentation templates, and tracking.

## When to Use

At the start of every new task or run session.

## Procedure

### 1. Determine Run Number

Check existing runs and increment:
```
runs/run-YYYYMMDD_HHMMSS/
```

### 2. Create Run Folder

Create folder structure:
```
runs/run-YYYYMMDD_HHMMSS/
├── THOUGHTS.md
├── DECISIONS.md
├── ASSUMPTIONS.md
├── LEARNINGS.md
└── RESULTS.md
```

### 3. Copy Templates

Populate with template content:
- THOUGHTS.md - Working thoughts and analysis
- DECISIONS.md - Key decisions made
- ASSUMPTIONS.md - Assumptions and their validation
- LEARNINGS.md - What we learned
- RESULTS.md - Final results and outcomes

### 4. Update State

Update STATE.yaml or ACTIVE.md to reflect current run.

## Template Files

### THOUGHTS.md

```markdown
# THOUGHTS - Run [ID]

## Initial Assessment

## Analysis

## Considerations

## Conclusions
```

### DECISIONS.md

```markdown
# DECISIONS - Run [ID]

| Decision | Rationale | Alternatives |
|----------|-----------|--------------|
```

### ASSUMPTIONS.md

```markdown
# ASSUMPTIONS - Run [ID]

| Assumption | Validation | Risk |
|------------|------------|------|
```

### LEARNINGS.md

```markdown
# LEARNINGS - Run [ID]

## What Worked

## What Didn't

## Insights
```

### RESULTS.md

```markdown
# RESULTS - Run [ID]

## Summary

## Deliverables

## Next Steps
```

## Integration

This skill is automatically invoked at the start of RALF runs.
