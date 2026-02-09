# Stop Hook

**Status:** 🚧 Under Redesign (Post-Review)
**Priority:** HIGH
**Location:** `pipeline/stop/`
**Language:** Python

---

## ⚠️ CRITICAL FINDING: Stop Hooks Cannot Block

**After comprehensive 5-agent review (all scored 42/100), we discovered a fundamental issue:**

> **Stop hooks fire AFTER the session has ended. They cannot prevent Claude from stopping.**

The original design assumed Stop hooks could "block" completion like PreToolUse hooks. This is **incorrect**.

### What Stop Hooks Actually Do
- Fire when session ends (user exits, context full, etc.)
- Can only perform cleanup, logging, notifications
- Cannot prevent session termination
- Run asynchronously from the ended session

### If You Need Blocking Validation
Use these alternatives:
- **PreCompact Hook** - Fires before context compaction, can block
- **UserPromptSubmit Hook** - Can detect "exit" intent and warn
- **Explicit `/complete` command** - Run validation before allowing exit

---

## Purpose (Corrected)

The Stop hook is BB5's **session-end cleanup and notification system**. It fires when a Claude session ends and performs:

1. **Async Cleanup** - Update state files, move completed tasks
2. **Notifications** - Send alerts (Telegram, desktop) about session completion
3. **Logging** - Record session metrics, token usage, outcomes
4. **Auto-Actions** - Commit changes, extract learnings (with safeguards)

**It CANNOT:**
- Block or prevent session end
- Force Claude to continue working
- Validate work before allowing stop

---

## When It Fires

- When user types `exit` or ends session
- When context window is exceeded
- When session times out
- **Does NOT fire** on Ctrl+C or forced termination

---

## Actual Input Format

```json
{
  "session_id": "uuid-string",
  "transcript_path": "/path/to/transcript.jsonl",
  "duration_seconds": 3600
}
```

**Note:** The original design included `hook_event_name`, `stop_hook_active`, and `cwd` fields. These **do not exist** in Claude Code's Stop hook input.

---

## Why BB5 Needs This

1. **RALF Monitor** - Send Telegram notifications about session completion
2. **State Cleanup** - Move tasks, update queue.yaml asynchronously
3. **Metrics Collection** - Log token usage, duration, outcomes
4. **Learning Extraction** - Run RETAIN on completed runs
5. **Git Auto-Commit** - Commit changes after session ends

---

## Functional Requirements (Redesigned)

### Phase 1: RALF Monitor (v1.0)

Send Telegram notification with:
- Agent type and project
- Session duration and token usage
- Task completed (if any)
- Quick links to run folder

See: [RALF Monitor Spec](../../.research/ralf-monitor/RALF_MONITOR_SPEC.md)

### Phase 2: Safe Auto-Actions (v1.1)

**⚠️ WARNING:** Auto-actions must have proper failure handling (see Lessons Learned).

**Actions:**
- Update task status in queue.yaml
- Move task folder (active → completed)
- Extract learnings via RETAIN
- Log skill usage
- Auto-commit changes

**Required Safeguards:**
- Pre-action validation
- Backup before mutate
- Transaction wrapper (all-or-nothing)
- Post-action verification
- Failure notification
- Dead letter queue for retries

### Phase 3: Advanced Cleanup (v1.2)

- Run folder archival
- Old events cleanup
- Metrics aggregation
- SSOT synchronization

---

## THOUGHTS.md Reasoning Documentation Requirement

**Critical BB5 Principle:** *"I always want the AI to document its reasoning because it makes the AI reason better."*

### Why Document Reasoning

1. **Improves AI Reasoning** - Forces structured, explicit thinking
2. **Debugging** - Other AIs can trace decision paths and understand why choices were made
3. **Knowledge Transfer** - Context preserved for future sessions
4. **Accountability** - Clear record of decision rationale

### Required THOUGHTS.md Section

```markdown
## Reasoning Log

### Decision 1: [Decision Topic]
**Context:** [What we knew at the time]
**Options Considered:**
- Option A: [Description]
  - Pros: [...]
  - Cons: [...]
- Option B: [Description]
  - Pros: [...]
  - Cons: [...]
**Decision:** [What we chose]
**Rationale:** [Why we chose it]
**Confidence:** [High/Medium/Low]
**Reversibility:** [High/Medium/Low]

### Decision 2: [Next Decision]
[Same format...]
```

### Validation

The Stop hook (or PreCompact hook for blocking) should verify:
- Reasoning Log section exists in THOUGHTS.md
- At least one decision documented
- Each decision has context, options, rationale
- Confidence level specified

---

## Technical Architecture

### File Structure
```
stop/
├── README.md              # This file
├── STOP_HOOK_CHECKLIST.md # Comprehensive validation checklist (legacy)
├── versions/
│   └── v1/
│       ├── hook.py        # Main implementation
│       ├── lib/
│       │   ├── __init__.py
│       │   ├── monitor.py     # RALF Monitor notifications
│       │   ├── actions.py     # Auto-actions with safeguards
│       │   └── cleanup.py     # Cleanup operations
│       ├── requirements.txt
│       └── IMPROVEMENTS.md
```

### Module Breakdown

#### `monitor.py` - RALF Monitor
- `send_telegram_notification(session_data)` → bool
- `format_notification_message(data)` → str
- `collect_session_metrics()` → dict

#### `actions.py` - Safe Auto-Actions
- `run_with_transaction(actions)` → bool
- `update_task_status(task_id)` → bool
- `extract_learnings(run_dir)` → bool
- `backup_before_mutate(file_path)` → backup_path

#### `cleanup.py` - Cleanup Operations
- `archive_run_folder(run_dir)` → bool
- `cleanup_old_events()` → bool

#### `hook.py` (main)
- Parse stdin JSON
- Collect session data
- Send RALF Monitor notification
- Run auto-actions in transaction
- Log results

---

## Dependencies

### Required
- Python 3.8+
- PyYAML
- requests (for Telegram API)
- git

### Optional
- pydantic (for data validation)

---

## Error Handling

### Graceful Degradation
- If notification fails → Log error, don't fail
- If auto-action fails → Retry with backoff, then dead letter queue
- If cleanup fails → Log for manual intervention

### No Blocking
- Stop hook **never** blocks session end
- All errors are logged, not shown to user
- Background processing for heavy operations

---

## Performance Budget

| Operation | Target Time |
|-----------|-------------|
| Parse input | <10ms |
| Collect metrics | <50ms |
| Send notification | <200ms (async) |
| Auto-actions | <500ms (async) |
| **Total** | **<100ms** (exit immediately) |

**Note:** Heavy work must be backgrounded. Stop hook exits immediately.

---

## Exit Codes

| Code | Behavior |
|------|----------|
| **0** | Success - Hook completed |
| **Non-zero** | Error logged, session already ended |

**Note:** Unlike PreToolUse, exit code 2 does NOT block for Stop hooks.

---

## Configuration

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/2-engine/.autonomous/hooks/active/ralf-monitor.py",
            "timeout": 30
          },
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/2-engine/.autonomous/hooks/active/stop-cleanup.py",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

---

## Lessons Learned

See comprehensive lessons from 5-agent harsh review:
- [STOP_HOOK_DESIGN_LESSONS.md](../../.research/lessons-learned/STOP_HOOK_DESIGN_LESSONS.md)

### Key Takeaways

1. **Stop hooks cannot block** - They fire after session ends
2. **BB5-specific validations needed** - Hindsight, RALF, agent types
3. **Auto-actions need safeguards** - Transactions, backups, failure handling
4. **Validation logic must be specific** - Avoid false positives/negatives
5. **UX should enable, not enforce** - Help users, don't punish them
6. **Document reasoning** - Required in THOUGHTS.md for better AI cognition

---

## Research Findings

### What Other Systems Use Stop Hooks For

| Tool | Stop Hook Use Case |
|------|-------------------|
| **Claude Code (disler)** | TTS announcements, logging, transcript export |
| **Claude Code (ChatPRD)** | Code quality validation (advisory only) |
| **BB5 (existing)** | Documentation validation, hierarchy updates |
| **Cursor** | Auto-commit, notifications |
| **Cline** | Task completion tracking |
| **Copilot** | Session logging, cleanup |

### Common Patterns

1. **Notifications** - Alert when work completes
2. **Auto-Commit** - Commit changes when session ends
3. **Logging** - Record session metrics
4. **Cleanup** - Archive, temp file removal
5. **Async Actions** - Background processing

**NOT Common:**
- Blocking session end (impossible)
- Validation gates (use PreCompact instead)

---

## Related

- [BB5 Key Thesis](../../../../5-project-memory/blackbox5/.docs/BB5-KEY-THESIS.md)
- [Hooks Main README](../../README.md)
- [SessionStart Hook](../session-start/) (initialization)
- [RALF Monitor Spec](../../.research/ralf-monitor/RALF_MONITOR_SPEC.md)
- [Design Lessons](../../.research/lessons-learned/STOP_HOOK_DESIGN_LESSONS.md)
- [Harsh Review Summary](../../../../5-project-memory/blackbox5/.autonomous/analysis/stop-hook-reviews/SUMMARY.md)

---

*Redesigned after comprehensive 5-agent review process*
