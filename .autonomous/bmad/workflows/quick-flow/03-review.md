# Quick Flow: Phase 3 - REVIEW

## Purpose

Self-review code quality before completion.

## When to Use

After DEV phase, before marking task complete

## Input

Implemented feature from Phase 2

## Output

Review checklist completed, approval to complete

## Review Checklist

### Code Quality

- [ ] **Follows conventions** - Matches project style
- [ ] **No duplication** - DRY principle applied
- [ ] **Clear naming** - Variables, functions, files well-named
- [ ] **Appropriate comments** - Where logic is complex
- [ ] **Error handling** - Edge cases considered

### Testing

- [ ] **Unit tests pass** - `pytest` or equivalent
- [ ] **Integration tests pass** - If applicable
- [ ] **Manual verification** - Tested the actual behavior
- [ ] **Edge cases covered** - Boundary conditions tested

### Functionality

- [ ] **Meets spec** - Implements what was specified
- [ ] **No regressions** - Existing features still work
- [ ] **Performance acceptable** - No obvious slowdowns
- [ ] **Security considered** - No obvious vulnerabilities

### Documentation

- [ ] **Code comments** - Where needed
- [ ] **README updated** - If applicable
- [ ] **CHANGELOG updated** - If project uses one

## Review Process

### 1. Static Review

Read through each changed file:

```bash
git diff HEAD~[N]  # N = number of commits
```

Ask:
- Would I understand this if I didn't write it?
- Is there a simpler way?
- Are there edge cases not handled?

### 2. Test Review

Run all tests:

```bash
# Project tests
pytest

# Or
npm test

# Or manual verification
[test commands]
```

### 3. Regression Check

Verify existing functionality:

```bash
# Run existing tests
pytest [existing test files]

# Check no files unintentionally modified
git status
```

## Review Outcomes

### PASS
All checklist items pass → Proceed to completion

### NEEDS_FIX
Some items fail → Fix and re-review

```markdown
## Fixes Needed
- [ ] [Issue 1] - [Fix approach]
- [ ] [Issue 2] - [Fix approach]
```

### NEEDS_REWORK
Significant issues → Consider rolling back

```bash
# Rollback procedure
git reset --soft HEAD~[N]
git stash
# Return to DEV phase
```

## Review Document Template

```markdown
# Code Review: [TASK-ID]

**Reviewer:** Agent-1.3 (self-review)
**Date:** [timestamp]

## Checklist Results

### Code Quality
- [x] Follows conventions
- [x] No duplication
- [x] Clear naming
- [ ] Comments (N/A - code is clear)
- [x] Error handling

### Testing
- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manual verification
- [x] Edge cases covered

### Functionality
- [x] Meets spec
- [x] No regressions
- [x] Performance acceptable
- [x] Security considered

### Documentation
- [x] Code comments
- [ ] README (N/A - no user-facing changes)
- [ ] CHANGELOG (N/A - internal change)

## Result

**[PASS / NEEDS_FIX / NEEDS_REWORK]**

## Notes
[Any observations, learnings, or concerns]
```

## Success Criteria

- [ ] All checklist items pass
- [ ] Review document created
- [ ] Outcome recorded

## Next Step

Mark task complete:
1. Update task status to "completed"
2. Move to completed folder
3. Create run documentation
4. Commit and push
5. Output `<promise>COMPLETE</promise>`
