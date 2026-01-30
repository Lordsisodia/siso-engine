# Version 2.1 Improvements

## Overview

Agent-2.1 merges BMAD (Breakthrough Method for Agile AI Driven Development) methodology from Agent-1.3 with Claude Code best practices from Agent-2.0. This version provides contextually-adaptive execution with rigorous precision.

## What Changed from 2.0 to 2.1

Agent-2.0 was Claude-only. Agent-2.1 brings back all BMAD features:

### BMAD Features Restored

1. **BMAD Method Integration** - Full explanation of BMAD philosophy
2. **BMAD Path Selection** - Quick Flow vs Full BMAD with decision criteria
3. **BMAD "Party Mode"** - Multi-agent collaboration patterns
4. **BMAD Contextual Help** - Self-assessment questions when stuck
5. **BMAD Retrospective** - Structured learning documentation
6. **BMAD Integration Summary** - Feature mapping table

### What Stayed from 2.0 (Claude Best Practices)

1. **Read Before Change** - NEVER propose changes to unread code
2. **Task State Discipline** - Mark complete IMMEDIATELY
3. **No Time Estimates** - Focus on action, not predictions
4. **Tool Usage Rules** - Task tool for exploration, parallel vs sequential
5. **Objective Communication** - No emojis unless requested, no colons before tools

## Key Improvements (Combined)

### 1. Read Before Change + BMAD Structure

**Before:** BMAD had structure but implicit safety
**After:** BMAD structure + explicit "read before change" rule

### 2. Immediate Task State + BMAD Tracking

**Before:** BMAD tracked time (estimates), Claude forbade estimates
**After:** BMAD tracking without time estimates, immediate state updates

### 3. Tool Usage + Party Mode

**Before:** BMAD had Party Mode (multi-agent), Claude had tool rules
**After:** Party Mode with proper Task tool usage

### 4. Objective Communication + BMAD Collaboration

**Before:** BMAD emphasized collaboration, Claude emphasized objectivity
**After:** Objective collaboration (best of both)

## Comparison Table

| Feature | Agent-1.3 (BMAD) | Agent-2.0 (Claude) | Agent-2.1 (Both) |
|---------|------------------|-------------------|------------------|
| **Core Focus** | BMAD methodology | Claude best practices | **Both combined** |
| **Read Before Change** | Implicit | **Explicit** | **Explicit + enforced** |
| **Task State** | Basic updates | **Immediate** | **Immediate + BMAD tracking** |
| **Time Estimates** | Tracked | **Forbidden** | **Forbidden** |
| **Tool Usage** | Mentioned | **Explicit rules** | **Explicit + BMAD patterns** |
| **Communication** | Standard | **Objective** | **Objective** |
| **Path Selection** | BMAD Quick/Full | SOP Quick/Full | **BMAD Quick/Full** |
| **Multi-Agent** | BMAD Party Mode | Basic | **BMAD Party Mode** |
| **Retrospective** | BMAD style | Minimal | **BMAD style** |

## Research Sources

- [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) - Complete Claude Code agent prompts
- [dontriskit/awesome-ai-system-prompts](https://github.com/dontriskit/awesome-ai-system-prompts) - Claude system prompts
- BMAD Methodology - From Agent-1.3

## Migration Notes

To upgrade from Agent-2.0 to Agent-2.1:

1. Update `ralf.md` to reference Agent-2.1
2. No breaking changes - all 2.0 rules still apply
3. Additional BMAD features are additive

## Version History

- **Agent-1.0** - Initial RALF agent
- **Agent-1.1** - Bug fixes
- **Agent-1.2** - Improvements
- **Agent-1.3** - BMAD-Enhanced
- **Agent-2.0** - Claude-Optimized (Claude only, no BMAD)
- **Agent-2.1** - BMAD + Claude Combined (this version)
