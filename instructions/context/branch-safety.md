# Branch Safety Protocol

RALF can run on `main` branch or feature branches.

---

## Allowed Branches

- `main` (primary development branch)
- `feature/*`
- `ralf/*`
- `bugfix/*`
- `dev`
- `develop`

## Forbidden Branches (NEVER)

- `master` (legacy - use main instead)
- `production`
- `release/*` (use feature branches instead)

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
