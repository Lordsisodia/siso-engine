# Deprecated Engine Prompts

These are the original engine prompt versions preserved for reference after consolidation (TASK-ARCH-062).

## Files

| File | Original Purpose | Replaced By |
|------|-----------------|-------------|
| `analyzer-validator.md.engine-original` | Simple analyzer validation | `research-pipeline/analyst-validator.md` |
| `planner-validator.md.engine-original` | Simple planner validation | `research-pipeline/planner-validator.md` |
| `scout-validator.md.engine-original` | Simple scout validation | `research-pipeline/scout-validator.md` |
| `deep-repo-scout.md.engine-original` | 3-loop repo analysis | `research-pipeline/scout-worker.md` |
| `integration-analyzer.md.engine-original` | Integration assessment | `research-pipeline/analyst-worker.md` |

## Key Differences

### Original Engine Prompts
- Simpler structure
- Basic task descriptions
- Direct output formats
- No worker-validator coordination

### Research Pipeline Replacements
- Worker-validator coordination protocols
- Timeline memory integration
- Token budget management
- Communication patterns via shared state
- Self-improvement mechanisms
- More detailed phase breakdowns

## Migration Notes

The engine now uses symlinks to the research pipeline versions. These originals are kept for:
1. Historical reference
2. Rollback if needed
3. Understanding the evolution

If you need to revert to an original, copy it back to the parent directory and remove the symlink.
