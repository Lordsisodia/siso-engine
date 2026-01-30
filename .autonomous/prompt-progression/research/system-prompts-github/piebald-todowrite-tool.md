# TodoWrite Tool Description

Source: https://github.com/Piebald-AI/claude-code-system-prompts

## Purpose

Creates and manages structured task lists for coding sessions to track progress, organize complex tasks, and demonstrate thoroughness.

## When to Use

- Complex multi-step tasks (3+ distinct steps)
- Non-trivial tasks requiring careful planning
- User explicitly requests todo list
- User provides multiple tasks
- After receiving new instructions
- When starting a task (mark in_progress BEFORE beginning)
- After completing a task (mark completed, add follow-ups)

## When NOT to Use

- Single, straightforward task
- Trivial task with no organizational benefit
- Task completable in <3 trivial steps
- Purely conversational/informational tasks

## Task States

| State | Description |
|-------|-------------|
| `pending` | Not yet started |
| `in_progress` | Currently working on (limit: ONE at a time) |
| `completed` | Finished successfully |

## Task Description Requirements

- `content`: Imperative form ("Run tests")
- `activeForm`: Present continuous ("Running tests")

## Management Rules

- Update status in real-time
- **Mark complete IMMEDIATELY after finishing**
- **Exactly ONE `in_progress` task at any time**
- Complete current tasks before starting new ones
- Remove irrelevant tasks entirely
- **ONLY mark completed when FULLY accomplished**
- If blocked, create new task describing resolution needed
- **Never mark completed if:**
  - Tests are failing
  - Implementation partial
  - Unresolved errors
  - Missing files/dependencies

## RALF Relevance

This is the exact pattern RALF should follow:
- One in_progress task at a time
- Mark complete immediately
- Never mark complete if tests failing or errors unresolved
- Imperative content, present continuous activeForm
