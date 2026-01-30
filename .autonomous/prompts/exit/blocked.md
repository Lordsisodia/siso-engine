# Exit: Blocked

Use when you cannot proceed due to external dependency or critical error.

---

## Output Format

```
<promise>COMPLETE</promise>

**Status:** BLOCKED
**Task:** [Task name]
**Blocker:** [Specific issue]
**Context:** [Relevant background]
**Help Needed:** [What human needs to do]
```

---

## Example

```
<promise>COMPLETE</promise>

**Status:** BLOCKED
**Task:** TASK-2026-01-30-001: Set up user authentication
**Blocker:** Supabase project not accessible (connection timeout)
**Context:** Tried 3 times, verified credentials in CONFIG.yaml
**Help Needed:** Check Supabase project status and network access
```

---

## Common Blockers

- **Wrong branch** — on main/master, need to switch to dev
- **Missing credentials** — API keys not configured
- **External dependency down** — Supabase, GitHub, etc.
- **Unclear requirements** — spec is ambiguous
- **Technical impossibility** — requested approach won't work
