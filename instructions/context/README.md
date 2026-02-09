# Context

> Context management and project-specific guidance for RALF

## Overview

This directory contains context files that help RALF agents understand the infrastructure, project specifics, and safety protocols. These files provide essential background knowledge for effective operation.

## Files

| File | Purpose |
|------|---------|
| `bb5-infrastructure.md` | How RALF infrastructure is organized (Engine + Project Memory) |
| `project-specific.md` | Details about managed projects (e-commerce, SISO internal) |
| `branch-safety.md` | Git branch safety protocols and allowed branches |

## BB5 Infrastructure

The `bb5-infrastructure.md` explains:

- **Engine** (`2-engine/.autonomous/`) - How to run (code that executes)
- **Project Memory** (`5-project-memory/{project}/.autonomous/`) - What to do (tasks, runs, learnings)
- Environment variables: `RALF_PROJECT_DIR`, `RALF_ENGINE_DIR`
- Task file format and naming conventions
- Feedback system between projects and RALF-CORE

## Project-Specific Context

The `project-specific.md` documents:

- **E-Commerce Client Project** (HIGH priority) - React/Next.js + Supabase
- **SISO Internal App** (MEDIUM priority) - BlackBox5 project memory system
- API configuration (GLM 4.7, Kimi 2.5)
- Quality gates before marking complete

## Branch Safety

The `branch-safety.md` defines:

**Allowed Branches:**
- `main` (primary development)
- `feature/*`, `ralf/*`, `bugfix/*`
- `dev`, `develop`

**Forbidden Branches (NEVER):**
- `master`, `production`, `release/*`

**Emergency Stop:** If on main/master, STOP immediately and alert user.

## Usage

RALF agents should read these files:
- At session start to understand infrastructure
- When switching projects for project-specific details
- Before git operations for branch safety
