# Exit: Partial

Use when task is partially complete (blocker or scope reduction).

---

## Output Format

```
<promise>COMPLETE</promise>

**Status:** PARTIAL
**Task:** [Task name]
**Completed:** [What was done]
**Remaining:** [What's left]
**Blocker:** [Why you couldn't finish]
**Next Steps:** [What needs to happen]
```

---

## Example

```
<promise>COMPLETE</promise>

**Status:** PARTIAL
**Task:** TASK-2026-01-30-001: Set up user authentication
**Completed:** Clerk integration, login component
**Remaining:** Protected routes, logout flow
**Blocker:** Need UI design for protected route fallback
**Next Steps:** Get design approval, then complete remaining items
```
