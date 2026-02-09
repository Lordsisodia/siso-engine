# Archive

> Archived and legacy RALF instructions

## Overview

This directory contains archived versions of RALF instructions that are no longer in active use but are preserved for historical reference.

## Files

| File | Description |
|------|-------------|
| `ralf-agent-2.3.md` | Legacy RALF agent v2.3 prompt (pre-Dual-RALF) |

## RALF-Agent 2.3

This is the original single-agent RALF prompt before the Dual-RALF architecture (Planner + Executor) was introduced.

**Key differences from Dual-RALF:**
- Single agent handled both planning and execution
- Context switching overhead between planning and execution
- No parallel processing capability
- Simpler communication (no inter-agent YAML files)

**Why it was replaced:**
- Planning and execution competed for the same context window
- No automatic STATE.yaml updates led to duplicate work
- Analysis and execution happened sequentially
- Limited specialization

## When to Reference

These archived files may be useful for:
1. Understanding RALF evolution
2. Comparing approaches
3. Extracting concepts for new implementations
4. Historical research

## Current System

For the current RALF system, see:
- `../system/` - Identity prompts
- `../planner/` - Planner agent versions
- `../executor/` - Executor agent versions
- `../system/handover/DUAL-RALF-HANDOVER.md` - Complete documentation
