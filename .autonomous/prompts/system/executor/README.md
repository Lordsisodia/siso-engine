# RALF-Executor Prompts

**Role:** Execution Agent
**Purpose:** Execute tasks from queue, commit code, report status

---

## Variations

| Version | File | Status | Description |
|---------|------|--------|-------------|
| v1 | [v1.md](variations/v1.md) | Ready | Initial version with file-based communication |

## Improvement Notes

- [v1-IMPROVEMENTS.md](variations/v1-IMPROVEMENTS.md) — Known limitations, testing checklist, future versions

---

## Quick Start

```bash
# Use v1 prompt
cat variations/v1.md

# Check improvement notes
cat variations/v1-IMPROVEMENTS.md
```

---

## Version History

### v1.0.0 (2026-02-01)
- Initial version
- File-based communication with Planner
- 30-second loop
- Skill-based execution
- Quality gates before commit
