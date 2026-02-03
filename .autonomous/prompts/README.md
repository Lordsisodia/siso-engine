# RALF Prompts

**Location:** `2-engine/.autonomous/prompts/`

This directory contains all prompts for the RALF (Recursive Autonomous Learning Framework) system.

## Structure

```
prompts/
├── README.md              # This file
├── ralf.md               # Main RALF v2.0 prompt (PRESERVED)
├── ralf-executor.md      # Current executor prompt (PRESERVED)
│
├── executor/             # Executor agent prompts
│   ├── README.md
│   └── versions/
│       ├── v1-20260201/
│       ├── v2-20260201/
│       └── v3-20260202/
│
├── planner/              # Planner agent prompts
│   ├── README.md
│   └── versions/
│       ├── v1-20260201/
│       ├── v2-20260201/
│       └── v3-20260202/
│
└── architect/            # Architect agent prompts
    ├── README.md
    └── versions/
        ├── v1-20260201/
        ├── v2-20260201/
        └── v3-20260202/
```

## Version Format

Each version folder: `v{number}-{YYYYMMDD}/`

Contains:
- `{agent}.md` - The prompt file
- `improvements.md` - What changed from previous version

## Current Versions

| Agent | Latest | Key Feature |
|-------|--------|-------------|
| Executor | v3-20260202 | Verification enforcement (anti-hallucination) |
| Planner | v3-20260202 | Verification-aware planning |
| Architect | v3-20260202 | RALF-integrated |

## Preserved Files

These files are maintained at the root level for backward compatibility:

- `ralf.md` - Main RALF v2.0 prompt
- `ralf-executor.md` - Current executor prompt with 7-phase flow

## Usage

To use a specific version:

```bash
# Executor v3
cat executor/versions/v3-20260202/executor.md | claude -p

# Planner v3
cat planner/versions/v3-20260202/planner.md | claude -p

# With dynamic context
cat executor/versions/v3-20260202/executor.md \
    ../../../5-project-memory/blackbox5/project-structure.md | claude -p
```

## Version History

See individual `improvements.md` files in each version folder for detailed changelogs.
