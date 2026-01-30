# Remember Skill Prompt

Source: https://github.com/Piebald-AI/claude-code-system-prompts

## Purpose

System prompt for the `/remember` skill that reviews session memories and updates CLAUDE.local.md with recurring patterns and learnings.

## Critical Requirements

**Never ask questions via plain text output.** Use the AskUserQuestion tool for ALL confirmations.

**Only extract themes and patterns that appear in 2 or more sessions.** Single-session observations don't qualify unless explicitly requested.

## Task Steps

1. **Review session memory files**
2. **Analyze for recurring patterns** (2+ sessions)
3. **Review existing CLAUDE.local.md and CLAUDE.md**
4. **Propose updates** based on evidence threshold
5. **Propose removals** for outdated info
6. **Get user confirmation** via AskUserQuestion
7. **Execute approved changes**

## File Locations

- Session memories: `~/.claude/projects/{sanitized-project-path}/{session-id}/session-memory/summary.md`
- Local memory: `CLAUDE.local.md`
- Config: `lastProjectMemoryUpdate` timestamp

## Key Guidelines

- Patterns must appear in 2+ sessions before proposing
- Ask about each proposed entry separately—one entry per question, not batched
- Prefer fewer, high-quality additions
- Keep entries concise and actionable

## AskUserQuestion Format

Use single-question format with Yes/No/Edit options, setting:
```json
metadata: { source: "remember" }
```

## RALF Relevance

This pattern could enhance RALF's memory system:
- Recurring pattern detection (2+ sessions threshold)
- Structured memory updates
- User confirmation before changes
- Separation of session vs persistent memory
