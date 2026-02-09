# BMAD Workflows

**Location:** `2-engine/.autonomous/workflows/`
**Purpose:** Reusable workflow patterns for BMAD skills

## Files

| File | Purpose |
|------|---------|
| `TEMPLATE.md` | Template for creating new BMAD workflows |
| `apc-menu-pattern.md` | A/P/C (Advanced/Party/Continue) menu pattern |
| `wip-tracking-system.md` | Work-in-progress file tracking system |

## Quick Reference

### A/P/C Menu

Present at workflow start:
- **[A] Advanced** - Full workflow, all steps
- **[P] Party** - Multi-agent collaborative mode
- **[C] Continue** - Resume from WIP checkpoint

### WIP File Location

```
2-engine/.autonomous/wip/
├── {command}-{description}-{timestamp}.md  # Active WIP
└── archive/                                 # Completed WIP
```

### WIP Frontmatter

```yaml
---
workflow: create-prd
command: CP
status: in_progress  # in_progress | paused | completed | abandoned
started: 2026-01-30T10:00:00Z
updated: 2026-01-30T11:30:00Z
stepsCompleted: [discovery, success-criteria]
currentStep: user-journeys
context:
  title: "Work Title"
artifacts: []
---
```

## Usage in Skills

See `TEMPLATE.md` for complete example of integrating A/P/C and WIP into skills.

## Integration with routes.yaml

Commands are defined in `../routes.yaml` under `bmad.commands`:

```yaml
bmad:
  commands:
    CP: { skill: bmad-pm, workflow: create-prd }
    TS: { skill: bmad-quick-flow, workflow: tech-spec }
```
