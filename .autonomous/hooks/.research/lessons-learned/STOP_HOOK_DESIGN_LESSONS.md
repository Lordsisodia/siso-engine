# Stop Hook Design Lessons Learned

**Date:** 2026-02-06
**Source:** 5-Sub-Agent Harsh Review Process
**Status:** Critical Findings

---

## Core Lesson: Claude Code Hook Types Have Different Capabilities

### The Fundamental Mistake
We designed a Stop hook that could "block" completion, but **Stop hooks cannot block**. They fire AFTER the session ends.

### Hook Type Capabilities Matrix

| Hook Type | Can Block | Input Fields | Use Case |
|-----------|-----------|--------------|----------|
| **SessionStart** | ❌ No | session_id, transcript_path | Initialization, context loading |
| **UserPromptSubmit** | ✅ Yes (exit 2) | prompt, context | Validation, safety checks |
| **PreToolUse** | ✅ Yes (exit 2) | tool_name, tool_input | Tool validation, blocking |
| **PostToolUse** | ❌ No | tool_name, tool_output, tool_error | Logging, side effects |
| **SubagentStart** | ❌ No | agent_type, task | Context injection |
| **SubagentStop** | ✅ Yes (exit 2) | agent_type, result | Subagent validation |
| **Stop** | ❌ No (post-session) | session_id, transcript_path, duration_seconds | Cleanup, notifications |
| **SessionEnd** | ❌ No | session_id | Final cleanup |

### What This Means for BB5

**If you need blocking validation:**
- Use **PreCompact** hook (fires before context compaction)
- Use **UserPromptSubmit** with intent detection
- Use explicit `/complete` command workflow

**If you need session-end cleanup:**
- Use **Stop** hook for notifications, logging, async cleanup
- Use **SessionEnd** for final state persistence

---

## Lesson 2: BB5-Specific Validations Required

Generic validation is insufficient. BB5 needs:

### Hindsight Memory Architecture
- Validate RETAIN extracted memories to 4-network system
- Check World/Experience/Opinion/Observation files updated
- Verify memories queryable via RECALL

### Agent Type-Specific Validations
| Agent Type | Required Validation |
|------------|---------------------|
| Planner | loop-metadata.yaml created, queue.yaml updated |
| Executor | task.md status updated, acceptance criteria checked |
| Scout | scout-report.md generated, findings logged |
| Verifier | verification-report.md created, sign-off recorded |
| Architect | decision_registry.yaml updated |
| Developer | Standard run documentation |

### RALF Loop Integration
- Validate loop metadata completeness
- Check improvement metrics updated
- Ensure Ralf-context.md propagated

### Multi-Layer Memory System
- Layer 1 (Swarm): events.yaml, queue.yaml, heartbeat.yaml
- Layer 2 (Hindsight): 4-network memory files
- Layer 3 (Run): THOUGHTS.md, DECISIONS.md, RESULTS.md

---

## Lesson 3: Auto-Actions Must Have Failure Handling

### The Dangerous Pattern
```python
# DON'T DO THIS - Fire and forget
async_run_auto_actions()  # No failure handling!
```

### Required Safety Mechanisms
1. **Pre-action validation** - Check preconditions
2. **Backup before mutate** - Enable rollback
3. **Transaction wrapper** - All-or-nothing semantics
4. **Post-action verification** - Confirm changes applied
5. **Failure notification** - Alert operator
6. **Dead letter queue** - Enable retry
7. **Circuit breaker** - Prevent cascade failures
8. **Idempotency checks** - Handle duplicate runs

### Race Conditions to Handle
- Concurrent task completion (file locking required)
- Task move + manual git ops
- State sync + manual edit (lost updates)

---

## Lesson 4: Validation Logic Must Be Specific

### False Positive Risks
| Scenario | Current | Should Be |
|----------|---------|-----------|
| Quick fix (< 5 min) | Blocks for short docs | Allow short docs |
| Exploration run | Blocks for missing RESULTS.md | Allow exploration |
| Placeholder in code | Blocks on `{placeholder}` | Ignore code fences |
| Task mentioned | Triggers completion validation | Require explicit claim |

### False Negative Risks
- No semantic validation (gibberish passes)
- Missing LEARNINGS.md only warns (should block for executor)
- No copy-paste detection from previous runs
- No empty section detection

### Severity Levels Needed
- **CRITICAL** - Block and require immediate fix
- **ERROR** - Block but can bypass with explicit override
- **WARNING** - Allow but require acknowledgment
- **INFO** - Log only

---

## Lesson 5: UX Must Enable, Not Enforce

### Current Design Problems
1. **Death by 1000 cuts** - One issue at a time blocking
2. **Vague errors** - "document your reasoning" without examples
3. **Aggressive git blocking** - ANY uncommitted change blocks
4. **Hidden bypass** - Buried in docs, stigmatized
5. **No context** - Missing task info, time spent, examples

### Better UX Principles
1. **Show all failures at once** - Never one-at-a-time
2. **Specific examples** - Show what good looks like
3. **Progress indicators** - "3/5 files complete"
4. **Tiered validation** - Different requirements by task size
5. **Surface bypass** - Make it visible, not stigmatized
6. **Celebrate success** - Positive reinforcement

---

## Lesson 6: Document AI Reasoning

**User Requirement:** "I always want the AI to document its reasoning because it makes the AI reason better."

### Why This Matters
1. **Improves AI reasoning** - Forces structured thinking
2. **Debugging** - Other AIs can trace decision paths
3. **Knowledge transfer** - Context for future sessions
4. **Accountability** - Clear record of why decisions made

### Implementation in THOUGHTS.md
```markdown
## Reasoning Log

### Decision 1: [Topic]
**Context:** [What we knew]
**Options Considered:**
- Option A: [Description] → Pros: ... Cons: ...
- Option B: [Description] → Pros: ... Cons: ...
**Decision:** [What we chose]
**Rationale:** [Why]
**Confidence:** [High/Medium/Low]

### Decision 2: [Topic]
[Same format...]
```

---

## Files Generated from This Research

| File | Purpose |
|------|---------|
| `STOP_HOOK_DESIGN_LESSONS.md` | This file - comprehensive lessons |
| `stop-hook-review-HOOKS.md` | Hook mechanics analysis |
| `stop-hook-review-INTEGRATION.md` | BB5 integration analysis |
| `stop-hook-review-VALIDATION.md` | Validation logic analysis |
| `stop-hook-review-AUTOACTIONS.md` | Auto-actions analysis |
| `stop-hook-review-UX.md` | UX/error messaging analysis |
| `SUMMARY.md` | Executive summary of all reviews |

---

## Next Steps

1. **Decide on hook type** - Stop for cleanup, PreCompact for blocking
2. **Rewrite checklist** - Remove blocking language, add BB5 specifics
3. **Design auto-actions** - With proper failure handling
4. **Redesign UX** - Enable good docs, not enforce them
5. **Implement RALF Monitor** - Telegram notifications for session tracking

---

*Documented for future hook development*
