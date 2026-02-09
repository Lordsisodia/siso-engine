# BB5 Hooks System

**Location:** `2-engine/.autonomous/hooks/`

This directory contains the Claude Code hooks system for BB5, organized by lifecycle stage and activation status.

---

## Quick Links

- [BB5 Key Thesis](../../5-project-memory/blackbox5/.docs/BB5-KEY-THESIS.md) - Guiding principles for all hook development
- [Active Hooks](./active/) - Currently enabled hooks
- [Pipeline Hooks](./pipeline/) - In-development hooks
- [Archive](./archive/) - Deprecated or superseded hooks
- [Research](./.research/) - Research and analysis documents

---

## Hook Types (12 Total)

| Hook | Status | Priority | Description |
|------|--------|----------|-------------|
| [SessionStart](./pipeline/session-start/) | 🚧 In Development | CRITICAL | Initialize session, load context, set env vars |
| [UserPromptSubmit](./pipeline/user-prompt-submit/) | 📋 Planned | HIGH | Validate/filter user prompts |
| [PreToolUse](./pipeline/pre-tool-use/) | 📋 Planned | HIGH | Block dangerous commands, security gates |
| [PostToolUse](./pipeline/post-tool-use/) | 📋 Planned | MEDIUM | Auto-formatting, logging, linting |
| [PostToolUseFailure](./pipeline/post-tool-use-failure/) | 📋 Planned | LOW | Error handling, recovery |
| [Notification](./pipeline/notification/) | 📋 Planned | MEDIUM | Desktop alerts, TTS, Slack |
| [SubagentStart](./pipeline/subagent-start/) | 📋 Planned | LOW | Subagent context setup |
| [SubagentStop](./pipeline/subagent-stop/) | 📋 Planned | MEDIUM | Subagent validation, notifications |
| [Stop](./pipeline/stop/) | 📋 Planned | HIGH | Task completion validation, quality gates |
| [PreCompact](./pipeline/pre-compact/) | 📋 Planned | LOW | Context preservation before compaction |
| [SessionEnd](./pipeline/session-end/) | 📋 Planned | LOW | Cleanup, archiving, metrics |
| [PermissionRequest](./pipeline/permission-request/) | 📋 Planned | LOW | Auto-allow rules, auditing |

**Legend:**
- ✅ Active - Hook is enabled and running
- 🚧 In Development - Being built/tested
- 📋 Planned - Designed but not implemented
- 📦 Archived - Deprecated or superseded

---

## Directory Structure

```
hooks/
├── README.md                 # This file
├── active/                   # Currently enabled hooks
│   └── (symlinks to pipeline versions)
├── pipeline/                 # All 12 hook types
│   ├── session-start/
│   │   ├── README.md
│   │   └── versions/
│   │       └── v1/
│   │           ├── hook.py (or .sh)
│   │           └── IMPROVEMENTS.md
│   ├── user-prompt-submit/
│   ├── pre-tool-use/
│   ├── post-tool-use/
│   ├── post-tool-use-failure/
│   ├── notification/
│   ├── subagent-start/
│   ├── subagent-stop/
│   ├── stop/
│   ├── pre-compact/
│   ├── session-end/
│   └── permission-request/
├── archive/                  # Deprecated hooks
│   └── README.md
└── .research/                # Research and analysis
    ├── BB5-KEY-THESIS.md     # Link to thesis
    ├── hook-languages-analysis.md
    └── (other research docs)
```

---

## Hook Development Workflow

1. **Research** - Document in `.research/`
2. **Design** - Create hook folder in `pipeline/`
3. **Implement** - Build v1 in `pipeline/{hook}/versions/v1/`
4. **Iterate** - Update version folders (v1, v2, etc.)
5. **Activate** - Symlink from `active/` to pipeline version
6. **Archive** - Move to `archive/` when superseded

---

## Hook Architecture Principles

Based on [BB5 Key Thesis](../../5-project-memory/blackbox5/.docs/BB5-KEY-THESIS.md):

1. **Enable Agents** - Hooks should help agents run effectively
2. **Remember** - Load context from previous sessions
3. **Learn** - Capture data for memory system
4. **Reliable** - Must not break agent workflows
5. **Fast** - SessionStart especially must be quick

---

## Configuration

Hooks are configured in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/2-engine/.autonomous/hooks/active/session-start.sh"
          }
        ]
      }
    ]
  }
}
```

---

## Current Status

**Last Updated:** 2026-02-06

**Active Hooks:** 0 (in development)
**Pipeline Hooks:** 12 folders created
**Next Milestone:** Complete SessionStart v1

---

*Part of the BB5 Autonomous Execution Operating System*
