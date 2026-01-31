---
name: continuous-improvement
description: Systematic self-improvement through reflection and learning
category: process
trigger: After runs, retrospectives, process improvement
inputs:
  - name: run_data
    type: document
    description: Run results and metrics
outputs:
  - name: improvements
    type: document
    description: Improvement recommendations
---

# Continuous Improvement

## Purpose

Systematically improve processes, skills, and outcomes through reflection and learning.

## When to Use

- After completing a run
- During retrospectives
- When patterns of friction emerge
- Every 5 runs (first principles review)

## Process

### After Every Run

Document in LEARNINGS.md:
- What worked well
- What was harder than expected
- What would you do differently
- Any patterns detected

### Every 5 Runs (First Principles Review)

1. Read last 5 LEARNINGS.md files
2. Synthesize patterns across runs
3. Propose concrete improvements to:
   - CLAUDE.md
   - LEGACY.md
   - Relevant skill files
4. Create summary for user approval
5. Apply approved changes

### Improvement Triggers

Activate continuous improvement when:
- User says "improve", "optimize", "refine", "iterate"
- Recurring friction in similar tasks
- First principles review (every 5 runs)
- Explicit skill invocation

## Documentation Template

```markdown
# LEARNINGS.md

## Run [ID] - [Date]

### What Worked Well
-

### What Was Harder Than Expected
-

### What Would I Do Differently
-

### Patterns Detected
-

### Proposed Improvements
-
```

## Integration

This skill integrates with:
- CLAUDE.md (user instructions)
- LEGACY.md (operational procedures)
- Individual skill files
- Run documentation
