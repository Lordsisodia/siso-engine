# Quick Flow: Phase 2 - DEV

## Purpose

Implement the feature with atomic commits and immediate testing.

## When to Use

After completing SPEC phase

## Input

Quick Spec from Phase 1

## Output

Implemented feature with tests

## Steps

### 1. Pre-Implementation Checks

```bash
# Verify files exist
ls [file paths from spec]

# Check existing tests
find ~/.blackbox5 -name "*test*" | grep [component]

# Check recent commits
git log --oneline -5
```

### 2. Implement

For each file:

1. **Make atomic change**
   - One logical change per file
   - Minimal, focused modification

2. **Test immediately**
   ```bash
   # Shell script
   bash script.sh && echo "PASS" || echo "FAIL"

   # Python
   python -c "import module; module.function()" && echo "PASS"

   # Existing tests
   pytest [test file] -v
   ```

3. **Commit**
   ```bash
   git add [file]
   git commit -m "ralf: [component] specific change

   - What changed
   - Why this approach

   Part of [TASK-ID]"
   ```

### 3. Verify

- [ ] All files modified as per spec
- [ ] Tests pass
- [ ] No regressions

## Rules

1. **One change, one commit**
2. **Test immediately after each change**
3. **If tests fail, fix before continuing**
4. **Stay in scope** - resist scope creep

## Dev Log Template

```markdown
# Dev Log: [TASK-ID]

## Changes Made

### [File 1]
- Change: [what was changed]
- Test: [how it was tested]
- Result: [PASS/FAIL]

### [File 2]
- Change: [what was changed]
- Test: [how it was tested]
- Result: [PASS/FAIL]

## Commits
- [hash]: [message]
- [hash]: [message]

## Time Spent
[Actual time]
```

## Success Criteria

- [ ] All spec items implemented
- [ ] Tests pass
- [ ] Atomic commits made
- [ ] Within estimated time (+/- 20%)

## Next Phase

Proceed to `~/.blackbox5/2-engine/.autonomous/bmad/workflows/quick-flow/03-review.md`
