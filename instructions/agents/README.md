# Agent Prompts - Consolidated

**Status:** Consolidated on 2026-02-06 (TASK-ARCH-062)

## Overview

This directory contains agent prompts for the RALF engine. Following consolidation (TASK-ARCH-062), most prompts are now symlinks to the canonical versions in the research pipeline.

## Prompt Hierarchy

```
Canonical Source (Research Pipeline)
    ↓
Symlinks (Engine)
    ↓
Backward Compatibility Maintained
```

## Consolidated Prompts (Symlinks)

| Engine File | Links To | Description |
|-------------|----------|-------------|
| `analyzer-validator.md` | `research-pipeline/.templates/prompts/analyst-validator.md` | Validates analysis quality |
| `planner-validator.md` | `research-pipeline/.templates/prompts/planner-validator.md` | Validates planning quality |
| `scout-validator.md` | `research-pipeline/.templates/prompts/scout-validator.md` | Validates scout extractions |
| `deep-repo-scout.md` | `research-pipeline/.templates/prompts/scout-worker.md` | Deep repository analysis |
| `integration-analyzer.md` | `research-pipeline/.templates/prompts/analyst-worker.md` | Integration value analysis |
| `implementation-planner.md` | `research-pipeline/.templates/prompts/planner-worker.md` | Creates implementation plans |

## Unique Engine Prompts (Not Consolidated)

These prompts remain unique to the engine:

| File | Purpose |
|------|---------|
| `improvement-scout.md` | Finds improvement opportunities |
| `intelligent-scout.md` | Intelligent repository scouting |
| `six-agent-pipeline.md` | 6-agent pipeline orchestration |

## Deprecated Originals

Original engine versions (pre-consolidation) are preserved in `deprecated/`:

- `analyzer-validator.md.engine-original`
- `planner-validator.md.engine-original`
- `scout-validator.md.engine-original`
- `deep-repo-scout.md.engine-original`
- `integration-analyzer.md.engine-original`
- `implementation-planner.md.engine-original`

## Why Consolidate?

The research pipeline prompts are more sophisticated:
- Worker-validator coordination protocols
- Timeline memory integration
- Token budget management
- Detailed communication patterns
- Self-improvement mechanisms

By consolidating, both pipelines benefit from the same high-quality prompts.

## Maintenance

**To update consolidated prompts:**
Edit the canonical source in `research-pipeline/.templates/prompts/`

**To add new engine-specific prompts:**
Create directly in this directory (not as symlinks)

## References

- Canonical prompts: `/Users/shaansisodia/.blackbox5/5-project-memory/blackbox5/.autonomous/research-pipeline/.templates/prompts/`
- Task: TASK-ARCH-062
