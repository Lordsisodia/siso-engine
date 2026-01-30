# Task Management with TodoWrite

Source: https://github.com/Piebald-AI/claude-code-system-prompts

## Core Principle

"Use these tools VERY frequently to ensure that you are tracking your tasks and giving the user visibility into your progress."

"These tools are also EXTREMELY helpful for planning tasks, and for breaking down larger complex tasks into smaller steps. If you do not use this tool when planning, you may forget to do important tasks - and that is unacceptable."

## Critical Rule

**"It is critical that you mark todos as completed as soon as you are done with a task. Do not batch up multiple tasks before marking them as completed."**

## Usage Patterns

Two examples demonstrate usage:
1. Running builds with type error fixes
2. Implementing a usage metrics feature with export functionality

The pattern involves:
- Creating todos
- Marking them "in_progress" while working
- Marking "completed" when finished

## RALF Relevance

RALF uses a similar task tracking system. Key insights:
- Mark complete IMMEDIATELY (don't batch)
- Use for planning and breaking down complex tasks
- Gives user visibility into progress
