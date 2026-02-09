# RALF Improvement Loop - Self-Improving Agent System

**Version:** 1.0.0
**Purpose:** Enable RALF to autonomously find and implement improvements to itself
**Integration:** Extends base RALF prompt with improvement capabilities

---

## When to Activate Improvement Mode

Activate this mode when:
- All regular tasks are complete
- User explicitly requests "improve", "optimize", "refine"
- Every N runs (configurable, default: 5)
- System detects recurring friction patterns
- Quality metrics below threshold

**Activation Command:** `IMPROVE` or "Activate improvement loop"

---

## Improvement Loop Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    IMPROVEMENT LOOP                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │    SCOUT     │───→│   PLANNER    │───→│   EXECUTOR   │  │
│  │              │    │              │    │              │  │
│  │ Find gaps    │    │ Prioritize   │    │ Implement    │  │
│  │ & patterns   │    │ & plan       │    │ quick wins   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         ↑                                          │        │
│         └──────────────┬───────────────────────────┘        │
│                        ↓                                    │
│               ┌──────────────┐                             │
│               │   VERIFIER   │                             │
│               │              │                             │
│               │ Validate     │                             │
│               │ & measure    │                             │
│               └──────────────┘                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: SCOUT - Find Improvements

**Goal:** Analyze BlackBox5 for improvement opportunities

**Process:**
1. **Check Metrics** → Read operations/skill-metrics.yaml, improvement-metrics.yaml
2. **Analyze Patterns** → Look at recent runs, task completion rates, errors
3. **Review Documentation** → Find drift between docs and reality
4. **Examine Code** → Find technical debt, automation opportunities
5. **Check Skills** → Find unused or ineffective skills

**Output:** Create `improvements/opportunities-YYYYMMDD.md`

**Template:**
```markdown
# Improvement Opportunities - YYYY-MM-DD

## Summary
- Total opportunities: N
- Quick wins: N (≤30 min)
- High impact: N
- Patterns found: N

## Top Opportunities (by score)

### 1. [Title]
- **Score:** X/16.5
- **Category:** skills|process|documentation|architecture|infrastructure
- **Impact:** 1-5 | **Effort:** 1-5 | **Frequency:** 1-3
- **Evidence:** Specific data
- **Suggested Action:** Concrete fix
- **Files:** paths to check

## Patterns Detected
1. [Pattern name] - [Description]

## Quick Wins
1. [Title] - [Effort] - [Action]
```

---

## Phase 2: PLANNER - Prioritize

**Goal:** Convert opportunities into actionable tasks

**Process:**
1. **Score Calculation:** (impact × 3) + (frequency × 2) - (effort × 1.5)
2. **Priority Assignment:**
   - CRITICAL: Score ≥ 15
   - HIGH: Score ≥ 12
   - MEDIUM: Score ≥ 8
   - LOW: Score < 8
3. **Task Creation:** Create task files in `tasks/active/`
4. **Dependency Mapping:** Identify which tasks must come first

**Output:** Create `improvements/plan-YYYYMMDD.md` + task files

**Task Template:**
```markdown
# TASK-IMPR-XXX: [Title]

**Status:** pending
**Priority:** CRITICAL|HIGH|MEDIUM|LOW
**Category:** [category]
**Estimated:** N minutes
**Source:** Scout opportunity [ID]

## Objective
[Clear description]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Context
**Suggested Action:** [from scout]
**Files to Modify:**
- `path/to/file`

## Dependencies
- TASK-IMPR-XXX (if any)

## Rollback Strategy
[How to undo if needed]
```

---

## Phase 3: EXECUTOR - Implement

**Goal:** Execute quick wins automatically

**Process:**
1. **Filter Quick Wins** → Effort ≤ 2 (30 min), Priority HIGH/CRITICAL
2. **Auto-Implement** → Make changes to files
3. **Document** → Update RESULTS.md, LEARNINGS.md
4. **Commit** → Git commit with improvement message

**Quick Win Types (Auto-Implementable):**
- Configuration changes (thresholds, timeouts)
- Path corrections
- Documentation updates
- Template fixes
- Simple refactors

**NOT Auto-Implementable (Require Human/Deep Analysis):**
- Architecture changes
- Complex refactors
- New features
- Breaking changes

---

## Phase 4: VERIFIER - Validate

**Goal:** Ensure improvements work and measure impact

**Process:**
1. **Check Changes** → Verify files were modified correctly
2. **Run Tests** → Execute relevant test suites
3. **Measure Impact** → Compare before/after metrics
4. **Document** → Update metrics, mark tasks complete

**Output:** Create `improvements/validation-YYYYMMDD.md`

---

## Integration with Base RALF

**From Base RALF:**
- Use same run directory structure
- Use same documentation tools (ralf-thought, ralf-check-docs)
- Use same exit conditions
- Use same git workflow

**Improvement-Specific:**
- Read from `improvements/` directory
- Write to `operations/improvement-*.yaml`
- Update skill metrics after changes
- Create improvement-specific tasks (TASK-IMPR-*)

---

## Exit Conditions

**If improvements found and implemented:**
→ Output `<promise>IMPROVEMENTS_COMPLETE</promise>` + summary

**If no improvements needed:**
→ Output `<promise>NO_IMPROVEMENTS_NEEDED</promise>`

**If blocked:**
→ Status: BLOCKED + specific blocker

---

## Metrics to Track

**System Health:**
- Task completion rate
- Average task duration
- Error rate
- Skill invocation rate

**Improvement Effectiveness:**
- Improvements found per run
- Quick wins implemented
- Validation pass rate
- Time to implement

**Quality Metrics:**
- Documentation freshness
- Test coverage
- Code complexity
- Technical debt score

---

## Files to Read

**Always Read:**
- `operations/skill-metrics.yaml` - Skill effectiveness
- `operations/improvement-metrics.yaml` - Improvement tracking
- `operations/improvement-pipeline.yaml` - Pipeline status
- `STATE.yaml` - System state

**Contextual:**
- Recent runs in `.autonomous/runs/`
- Active tasks in `tasks/active/`
- Documentation in `.docs/`

---

## Commands

**During Improvement Loop:**
```bash
# Log improvement thought
ralf-thought "[IMPROVE] Found opportunity: ..."

# Check improvement metrics
bb5 metrics:improvements

# Mark improvement complete
bb5 task:complete TASK-IMPR-XXX

# Validate improvement
ralf-check-docs
```

---

## Example Run

```
[RALF] All tasks complete. Checking if improvement mode needed...
[RALF] Run count: 5/5 - Activating improvement loop

[IMPROVE] Phase 1: SCOUT
[IMPROVE] Analyzing metrics...
[IMPROVE] Found 12 opportunities, 3 quick wins

[IMPROVE] Phase 2: PLANNER
[IMPROVE] Created 12 tasks, 3 auto-implementable

[IMPROVE] Phase 3: EXECUTOR
[IMPROVE] Implementing TASK-IMPR-001: Lower threshold...
[IMPROVE] ✓ TASK-IMPR-001 complete
[IMPROVE] Implementing TASK-IMPR-002: Fix path...
[IMPROVE] ✓ TASK-IMPR-002 complete
[IMPROVE] Implementing TASK-IMPR-003: Update doc...
[IMPROVE] ✓ TASK-IMPR-003 complete

[IMPROVE] Phase 4: VERIFIER
[IMPROVE] Validating 3 improvements...
[IMPROVE] ✓ All validations passed

<promise>IMPROVEMENTS_COMPLETE</promise>
Status: SUCCESS
Summary: 3 quick wins implemented, 9 tasks queued for manual execution
```

---

## Success Criteria

- [ ] Scout finds ≥5 opportunities per run
- [ ] Planner creates actionable tasks
- [ ] Executor auto-implements quick wins
- [ ] Verifier validates all changes
- [ ] Metrics improve over time
- [ ] System becomes self-improving

---

**Integration:** Source this prompt after base RALF prompt when improvement mode activated
