# Exit: Success

Use when task is fully complete.

---

## Output Format

```
<promise>COMPLETE</promise>

**Status:** SUCCESS
**Task:** [Task name from STATE.yaml]
**Summary:** [One line what was accomplished]
**Artifacts:** [Files created/modified]
**Next Task:** [What should be done next, if known]
```

---

## Example

```
<promise>COMPLETE</promise>

**Status:** SUCCESS
**Task:** TASK-2026-01-30-001: Set up user authentication
**Summary:** Implemented Clerk auth with login/logout flows
**Artifacts:**
- src/auth/clerk.ts
- src/components/LoginButton.tsx
- src/hooks/useAuth.ts
**Next Task:** TASK-2026-01-30-002: Create protected routes
```
