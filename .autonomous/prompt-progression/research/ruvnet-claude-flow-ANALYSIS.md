# GitHub Issues Analysis: Claude Flow

**Repository:** ruvnet/claude-flow
**Generated:** 2026-01-19 08:28:45
**Focus Area:** claude-flow

## Summary

- **Total issues fetched:** 20
- **New issues analyzed:** 10
- **Previously seen:** 10

## Issue #938: Too much "vibe coded" options, zero intuitive

**State:** OPEN
**Created:** 2026-01-12T13:41:49Z
**URL:** https://github.com/ruvnet/claude-flow/issues/938

### Description

It looks like a promising project until you play with it. Actually, I still haven't been able to do a thing with it: the list of commands, sub-commands and options is overwhelming. I start a swarm or an agent, ¿what's next? Documentation is poorly written, and the ultimate **red flag** is:

<img wid...

### Analysis

This issue relates to claude-flow. Related to **documentation**. Impact assessment needed based on labels and community engagement.

## Issue #936: Docs links broken

**State:** OPEN
**Created:** 2026-01-11T12:00:57Z
**URL:** https://github.com/ruvnet/claude-flow/issues/936

### Description

Quite nice project but several docs links I tried to follow were broken :(

### Analysis

This issue relates to claude-flow. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #933: Quite a few bad links in the docs

**State:** OPEN
**Created:** 2026-01-11T02:37:25Z
**URL:** https://github.com/ruvnet/claude-flow/issues/933

### Description

Noticed one bad link and decided to run lychee.

Command: `/tmp/lychee/lychee --root-dir . --exclude 'http://localhost*' --exclude 'https://localhost*' .`

Results:
- 1016 total
- 699 OK
- 242 errors
- 28 excluded
- 47 redirects

<details>
   <summary>Lychee report</summary>

---

Issues found in 77...

### Analysis

This issue relates to claude-flow. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #932: Bug: Memory protocol injection fails due to invalid fs/promises import in inject-memory-protocol.js

**State:** OPEN
**Created:** 2026-01-09T18:54:34Z
**URL:** https://github.com/ruvnet/claude-flow/issues/932

### Description

## Bug Description

When running swarm commands with the `--claude` flag, the memory protocol injection fails silently with the warning:

```
⚠️  Memory protocol injection not available, using standard prompt
```

This prevents the memory coordination protocol from being injected into CLAUDE.md, cau...

### Analysis

This issue relates to claude-flow. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #930: Feature Request: Toggle-able WH(Y) Architecture Decision Record (ADR) Mode

**State:** OPEN
**Created:** 2026-01-08T22:27:47Z
**URL:** https://github.com/ruvnet/claude-flow/issues/930

### Description

# ADR-CF3-001: Enhanced ADR Format for Claude-Flow v3
@ruvnet for consideration in claude-flow_v3 please.

## Feature Request: Toggle-able WH(Y) Architecture Decision Record (ADR) Mode

| Field | Value |
|-------|-------|
| **Decision ID** | ADR-CF3-001 |
| **Initiative** | Claude-Flow v3 ADR Enhanc...

### Analysis

This issue relates to claude-flow. Related to **installation** or **setup**. Impact assessment needed based on labels and community engagement.

## Issue #928: Feedback on your reasoningbank-intelligence skill

**State:** OPEN
**Created:** 2026-01-05T22:13:37Z
**URL:** https://github.com/ruvnet/claude-flow/issues/928

### Description

I took a look at your **reasoningbank-intelligence** skill and wanted to share some thoughts.

**Links:**
- [GitHub](https://github.com/ruvnet/claude-flow/blob/main/.claude/skills/reasoningbank-intelligence/SKILL.md)
- [Your agentic skill in the SkillzWave marketplace](https://skillzwave.ai/skill/ru...

### Analysis

This issue relates to claude-flow. Related to **installation** or **setup**. Impact assessment needed based on labels and community engagement.

## Issue #927: 🚀 Claude-Flow V3 Complete Implementation: 15-Agent Concurrent Swarm

**State:** OPEN
**Created:** 2026-01-04T17:12:21Z
**URL:** https://github.com/ruvnet/claude-flow/issues/927

### Description

# Claude-Flow V3: Complete Implementation Overview

## 🎯 Executive Summary

This issue tracks the complete implementation of **Claude-Flow v3** using a **15-agent concurrent swarm** architecture. The implementation follows 10 Architecture Decision Records (ADRs), TDD London School methodology, and t...

### Analysis

This issue relates to claude-flow. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #920: MCP server fails to start on Windows due to path comparison bug

**State:** OPEN
**Created:** 2025-12-21T20:21:05Z
**URL:** https://github.com/ruvnet/claude-flow/issues/920

### Description

## Bug Description

The MCP server silently fails to start on Windows when running `npx claude-flow mcp start`. The server process spawns but exits immediately without doing anything.

## Root Cause

In `src/mcp/mcp-server.js` at line 2637, the entry point check uses an incorrect file URL format:

`...

### Analysis

This issue relates to claude-flow. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #919: Hive-Mind Prompt References Non-Existent MCP Tools

**State:** OPEN
**Created:** 2025-12-21T11:44:17Z
**URL:** https://github.com/ruvnet/claude-flow/issues/919

### Description

## Hive-Mind Prompt References Non-Existent MCP Tools

**Related**: #236, #125

### Summary

The `hive-mind spawn` command generates a coordination prompt that references 20+ MCP tools which do not exist in the actual MCP server. This causes spawned Claude Code instances to halt and request alternat...

### Analysis

This issue relates to claude-flow. Related to **installation** or **setup**. Impact assessment needed based on labels and community engagement.

## Issue #918: Hive Mind prompt template references non-existent MCP tools

**State:** OPEN
**Created:** 2025-12-19T08:36:28Z
**URL:** https://github.com/ruvnet/claude-flow/issues/918

### Description

The Hive Mind wizard template (claude-flow hive-mind start) generates a prompt that references ~15 non-existent MCP tools.                                         
                                                                                                                                        ...

### Analysis

This issue relates to claude-flow. Related to **documentation**. Impact assessment needed based on labels and community engagement.

## Recommendations

- Review 10 new issues above
- Prioritize based on labels and community response
- Consider backlog items for high-priority patterns

