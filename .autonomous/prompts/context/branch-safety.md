# Branch Safety Protocol

CRITICAL: All work MUST stay on `dev` branch.

---

## Allowed Branches

- `dev` (primary)
- `develop`
- `feature/*`
- `bugfix/*`
- `ralph/*`

## Forbidden Branches (NEVER)

- `main`
- `master`
- `production`
- `release/*`

---

## Pre-Flight Check

```bash
git branch --show-current
```

**If not on `dev`:**
```bash
git checkout dev
git pull origin dev
```

---

## Commit Rules

- Commit to current branch (must be allowed)
- Never force push
- Never push to main/master
- Use descriptive messages: `"feat: [feature] - [what changed]"`

---

## Emergency Stop

If you find yourself on `main` or `master`:
1. STOP immediately
2. Do not commit
3. Alert user
4. Exit with BLOCKED status
