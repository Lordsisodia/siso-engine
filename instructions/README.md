# Instructions

> Agent prompts and system instructions for Blackbox5

## Overview

This directory contains all prompts, instructions, and procedural documentation for agents in the RALF (Recursive Autonomous Learning Framework) system.

## Structure

```
instructions/
├── README.md                   # This file
│
├── agents/                     # Agent-specific prompts
│   ├── analyzer-validator.md   # Analysis validation
│   ├── deep-repo-scout.md      # Repository scouting
│   ├── implementation-planner.md # Planning
│   ├── integration-analyzer.md # Integration analysis
│   ├── intelligent-scout.md    # Intelligent scouting
│   ├── improvement-scout.md    # Improvement finding
│   ├── planner-validator.md    # Plan validation
│   ├── scout-validator.md      # Scout validation
│   ├── six-agent-pipeline.md   # Pipeline orchestration
│   └── deprecated/             # Legacy prompts
│
├── architect/                  # Architect agent versions
│   ├── README.md
│   └── versions/
│       ├── v1-20260201/
│       ├── v2-20260201/
│       └── v3-20260202/
│
├── executor/                   # Executor agent versions
│   ├── README.md
│   └── versions/
│       ├── v1-20260201/
│       ├── v2-20260201/
│       └── v3-20260202/
│
├── planner/                    # Planner agent versions
│   ├── README.md
│   └── versions/
│       ├── v1-20260201/
│       ├── v2-20260201/
│       └── v3-20260202/
│
├── verifier/                   # Verifier agent
│   └── verifier-v1.md
│
├── system/                     # System-level prompts
│   ├── ralf.md                 # Main RALF v2.0 prompt
│   ├── ralf-executor.md        # Executor prompt (7-phase flow)
│   ├── ralf-improvement-loop.md # Improvement loop
│   └── ralf-scout-improve.md   # Scout improvement
│
├── context/                    # Context management
├── exit/                       # Exit procedures
├── procedures/                 # Standard procedures
└── workflows/                  # Workflow definitions
```

## Agent Prompts

Located in agents/, these are the prompts used by specific agents.

### Consolidated Scout Prompts

Following consolidation (TASK-ARCH-062), most scout-related prompts are now symlinks to canonical versions in the research pipeline:

| Prompt | Type | Description |
|--------|------|-------------|
| deep-repo-scout.md | Symlink | Deep repository analysis |
| analyzer-validator.md | Symlink | Validates analysis quality |
| planner-validator.md | Symlink | Validates planning quality |
| scout-validator.md | Symlink | Validates scout extractions |
| integration-analyzer.md | Symlink | Integration value analysis |
| implementation-planner.md | Symlink | Creates implementation plans |

### Engine-Specific Prompts

These prompts remain unique to the engine:

| Prompt | Description |
|--------|-------------|
| improvement-scout.md | Finds improvement opportunities |
| intelligent-scout.md | Intelligent repository scouting |
| six-agent-pipeline.md | 6-agent pipeline orchestration |

## Versioned Agent Prompts

The architect/, executor/, and planner/ directories contain versioned prompts:

### Version Format

Each version folder: v{number}-{YYYYMMDD}/

Contains:
- {agent}.md - The prompt file
- improvements.md - What changed from previous version

### Current Versions

| Agent | Latest | Key Feature |
|-------|--------|-------------|
| Executor | v3-20260202 | Verification enforcement (anti-hallucination) |
| Planner | v3-20260202 | Verification-aware planning |
| Architect | v3-20260202 | RALF-integrated |

## System Prompts

Located at the root of instructions/, these define core RALF behavior:

| File | Purpose |
|------|---------|
| ralf.md | Main RALF v2.0 system prompt |
| ralf-executor.md | Current executor with 7-phase flow |
| ralf-improvement-loop.md | Self-improvement loop |
| ralf-scout-improve.md | Scout improvement process |

## Usage

### Using a Specific Version

```bash
# Executor v3
cat executor/versions/v3-20260202/executor.md | claude -p

# Planner v3
cat planner/versions/v3-20260202/planner.md | claude -p
```

### Using Agent Prompts

```bash
# Scout with intelligent prompt
cat agents/intelligent-scout.md | claude -p

# Six-agent pipeline
cat agents/six-agent-pipeline.md | claude -p
```

## Maintenance

**To update consolidated prompts:**
Edit the canonical source in 5-project-memory/blackbox5/.autonomous/research-pipeline/.templates/prompts/

**To add new engine-specific prompts:**
Create directly in agents/ (not as symlinks)

**To version a prompt:**
1. Create new folder: versions/v{N+1}-{YYYYMMDD}/
2. Copy and modify the prompt
3. Document changes in improvements.md
