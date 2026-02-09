# Procedures

> Standard execution procedures for RALF agents

## Overview

This directory contains procedural documentation that guides RALF agents through common operations. These are step-by-step instructions for executing tasks, selecting work, and handling standard scenarios.

## Files

| File | Purpose | Used By |
|------|---------|---------|
| `execution-protocol.md` | 5-phase task execution flow (Align, Plan, Execute, Validate, Document) | Executor |
| `task-selection.md` | Algorithm for selecting the next task from queue | Planner, Executor |

## Execution Protocol (5 Phases)

The `execution-protocol.md` defines the standard flow:

1. **Align** - Restate task, goal, constraints, inputs, outputs
2. **Plan** - Create micro-plan with steps and success criteria
3. **Execute** - Write code, use sub-agents, document as you go
4. **Validate** - Run quality gates (tests, type checking, connections)
5. **Document** - Update tracking (task file, STATE.yaml, WORK-LOG.md, commit)

## Task Selection Algorithm

The `task-selection.md` defines how agents pick work:

1. Read STATE.yaml for active tasks
2. Filter by dependencies (all must be completed)
3. Prioritize by: priority level > creation date > project
4. Verify context exists
5. Mark in progress

## Key Principles

- **ONE task only** — Never batch multiple tasks
- **Read before change** — NEVER propose changes to unread code
- **Check for duplicates** — Search completed tasks before starting
- **Integration required** — Code must work with existing system
