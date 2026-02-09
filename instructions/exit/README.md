# Exit

> Exit procedures and status formats for RALF

## Overview

This directory contains standardized exit formats for different completion scenarios. RALF agents use these templates to report task completion status.

## Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `success.md` | Full completion format | Task is fully complete |
| `partial.md` | Partial completion format | Task partially complete (blocker or scope reduction) |
| `blocked.md` | Blocked status format | Cannot proceed due to external dependency or critical error |

## Exit: Success

Use when task is fully complete.

**Output Format:**
```
<promise>COMPLETE</promise>

**Status:** SUCCESS
**Task:** [Task name from STATE.yaml]
**Summary:** [One line what was accomplished]
**Artifacts:** [Files created/modified]
**Next Task:** [What should be done next, if known]
```

## Exit: Partial

Use when task is partially complete (blocker or scope reduction).

**Output Format:**
```
<promise>COMPLETE</promise>

**Status:** PARTIAL
**Task:** [Task name]
**Completed:** [What was done]
**Remaining:** [What's left]
**Blocker:** [Why you couldn't finish]
**Next Steps:** [What needs to happen]
```

## Exit: Blocked

Use when you cannot proceed due to external dependency or critical error.

**Output Format:**
```
<promise>COMPLETE</promise>

**Status:** BLOCKED
**Task:** [Task name]
**Blocker:** [Specific issue]
**Context:** [Relevant background]
**Help Needed:** [What human needs to do]
```

## Common Blockers

- **Wrong branch** — on main/master, need to switch to dev
- **Missing credentials** — API keys not configured
- **External dependency down** — Supabase, GitHub, etc.
- **Unclear requirements** — spec is ambiguous
- **Technical impossibility** — requested approach won't work

## Usage

RALF agents must use these formats when exiting:

1. Determine status: SUCCESS, PARTIAL, or BLOCKED
2. Fill in the appropriate template
3. Include `<promise>COMPLETE</promise>` marker
4. Provide clear, actionable information
