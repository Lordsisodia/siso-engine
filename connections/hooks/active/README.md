# BB5 Active Hooks

**Location:** `2-engine/.autonomous/hooks/active/`

This directory contains symlinks to currently enabled hooks.

---

## Currently Active

| Hook | Version | Target | Status |
|------|---------|--------|--------|
| *(none yet)* | - | - | - |

---

## How to Activate a Hook

```bash
# From the hooks directory
cd 2-engine/.autonomous/hooks/

# Create symlink from active to pipeline version
ln -sf ../pipeline/session-start/versions/v1/hook.py active/session-start.py

# Configure in ~/.claude/settings.json
```

---

## Activation Checklist

- [ ] Hook implemented in `pipeline/{hook}/versions/v{version}/`
- [ ] IMPROVEMENTS.md documents iterations
- [ ] Hook tested in isolation
- [ ] Symlink created in `active/`
- [ ] ~/.claude/settings.json updated
- [ ] Tested in live session

---

*Part of BB5 Autonomous Execution Operating System*
