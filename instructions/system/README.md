# System

> System identity prompts for RALF agents

## Overview

This directory contains identity and role-definition prompts for the RALF system and its specialized agents. These prompts define who the agents are, what they do, and how they behave.

## Files

| File | Purpose |
|------|---------|
| `identity.md` | Main RALF identity (v2.0) - Recursive Autonomous Learning Framework |
| `planner-identity.md` | RALF-Planner agent identity (strategist) |
| `executor-identity.md` | RALF-Executor agent identity (tactician) |
| `handover/DUAL-RALF-HANDOVER.md` | Complete handover for Dual-RALF system |

## RALF Identity (identity.md)

Core identity for the main RALF system:

- **Role:** Autonomous Software Architect & Builder
- **Purpose:** Ship features, documentation, and infrastructure
- **Core Philosophy:** "Deterministically excellent through first principles thinking"

**Non-Negotiables:**
- ONE Task Per Loop
- First Principles Thinking (Always)
- Context & Transparency
- GitHub Integration
- Testing Rigor
- MCP Mastery

## RALF-Planner Identity (planner-identity.md)

The thinker, not the doer:

- **Job:** Analyze, Plan, Organize, Answer, Adapt
- **Writes to:** queue.yaml, chat-log.yaml (answers), heartbeat.yaml
- **Reads from:** events.yaml, chat-log.yaml (questions), heartbeat.yaml
- **Does NOT:** Execute code, make commits, modify code files

**Loop Behavior (every 30 seconds):**
1. Read events.yaml (check Executor progress)
2. Read chat-log.yaml (check for questions)
3. Check queue.yaml depth
4. Plan more tasks if queue < 2
5. Write heartbeat

## RALF-Executor Identity (executor-identity.md)

The doer, not the thinker:

- **Job:** Read queue, Execute, Commit, Report, Ask
- **Writes to:** events.yaml, chat-log.yaml (questions), heartbeat.yaml, STATE.yaml
- **Reads from:** queue.yaml, chat-log.yaml (answers), heartbeat.yaml
- **Does NOT:** Plan new tasks, analyze codebase structure, select tasks from STATE.yaml

**Loop Behavior (every 30 seconds):**
1. Read queue.yaml (check for tasks)
2. Read heartbeat.yaml (check Planner health)
3. Claim and execute available tasks
4. Commit changes
5. Write heartbeat

## Dual-RALF Handover

The `handover/DUAL-RALF-HANDOVER.md` contains complete documentation for the dual-agent system:

- Architecture overview
- Communication protocol via YAML files
- 30-second loop behavior
- Task lifecycle
- Quality gates
- Error handling
- Testing checklist
- Metrics to track

## Communication Flow

```
Planner (Strategist)          Executor (Tactician)
      │                              │
      ├──► queue.yaml (tasks) ──────►│
      │◄── events.yaml (status) ◄────┤
      │◄──► chat-log.yaml (Q&A) ◄──►│
      └──► heartbeat.yaml ◄──────────┘
```

## Usage

These identity prompts are used when spawning RALF agents:

```bash
# Main RALF
cat system/identity.md | claude -p

# Planner agent
cat system/planner-identity.md | claude -p

# Executor agent
cat system/executor-identity.md | claude -p
```
