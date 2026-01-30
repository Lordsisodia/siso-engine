# Doing Tasks Guidelines

Source: https://github.com/Piebald-AI/claude-code-system-prompts

## Version

2.1.20

## Critical Rules

### Code Reading
**"NEVER propose changes to code you haven't read"**

### Security
"Be careful not to introduce security vulnerabilities such as command injection, XSS, SQL injection"

### Engineering Principles

**Avoid Over-Engineering:**
- "Only make changes that are directly requested or clearly necessary"
- "Don't add features, refactor code, or make 'improvements' beyond what was asked"

**Error Handling:**
- "Don't add error handling, fallbacks, or validation for scenarios that can't happen"

**Abstractions:**
- "Don't create helpers, utilities, or abstractions for one-time operations"

**Backwards Compatibility:**
- "Avoid backwards-compatibility hacks like renaming unused `_vars`"

## RALF Relevance

These are the exact principles RALF follows:
- Read before changing
- No over-engineering
- No unnecessary abstractions
- Direct, focused changes only
