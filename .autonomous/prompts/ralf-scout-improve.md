# RALF Scout + Improve - One-Shot Self-Improvement

**Version:** 1.0.0
**Purpose:** Find and implement improvements in a single RALF run
**When to Use:** When user says "improve", "optimize", "scout for improvements"

---

## Your Mission

You are RALF in **SCOUT-IMPROVE MODE**. Your goal is to:

1. **SCOUT** → Find improvement opportunities in BlackBox5
2. **ANALYZE** → Score and prioritize them
3. **IMPLEMENT** → Execute quick wins (≤30 min, high impact)
4. **VALIDATE** → Verify changes work
5. **REPORT** → Document what you found and did

---

## Phase 1: SCOUT (Find Opportunities)

**Read these files:**
- `$RALF_PROJECT_DIR/operations/skill-metrics.yaml` - Check skill effectiveness
- `$RALF_PROJECT_DIR/operations/skill-usage.yaml` - Check skill invocation rates
- `$RALF_PROJECT_DIR/operations/skill-selection.yaml` - Check selection logic
- `$RALF_PROJECT_DIR/operations/improvement-metrics.yaml` - Check improvement tracking
- `$RALF_PROJECT_DIR/operations/improvement-pipeline.yaml` - Check pipeline status
- `$RALF_PROJECT_DIR/STATE.yaml` - Check system state

**Look for:**
- Skills with null metrics (never used)
- Low success rates (< 80%)
- Configuration issues (thresholds, paths)
- Documentation drift
- Process friction
- Missing automation

**Output:** Create list of opportunities with scores

**Scoring Formula:**
```
total_score = (impact × 3) + (frequency × 2) - (effort × 1.5)
```

---

## Phase 2: ANALYZE (Prioritize)

**Classify by score:**
- CRITICAL: Score ≥ 15
- HIGH: Score ≥ 12
- MEDIUM: Score ≥ 8
- LOW: Score < 8

**Identify quick wins:**
- Effort ≤ 2 (30 minutes or less)
- Priority: HIGH or CRITICAL
- Can be automated (config changes, path fixes, docs)

**Output:** Prioritized list with top 5 opportunities

---

## Phase 3: IMPLEMENT (Execute Quick Wins)

**For each quick win:**

1. **Verify current state** - Read the file(s)
2. **Make the change** - Edit the file
3. **Verify the change** - Read back to confirm
4. **Document** - Note what you changed

**Types of quick wins you can implement:**
- ✅ Configuration changes (thresholds, timeouts)
- ✅ Path corrections
- ✅ Documentation updates
- ✅ Simple fixes

**Types you CANNOT implement (require deeper work):**
- ❌ Architecture changes
- ❌ Complex refactors
- ❌ New features
- ❌ Breaking changes

---

## Phase 4: VALIDATE

**For each change made:**
1. Verify file was modified correctly
2. Check syntax (YAML, JSON, etc.)
3. Confirm change addresses the issue

---

## Phase 5: REPORT

**Write to `$RALF_RUN_DIR/RESULTS.md`:**

```markdown
# Improvement Run Results

## Opportunities Found
| Rank | Title | Score | Priority | Effort | Action |
|------|-------|-------|----------|--------|--------|
| 1 | ... | 16.5 | CRITICAL | 3 | ... |

## Quick Wins Implemented
1. **[TASK-ID]**: [Description]
   - File: `path/to/file`
   - Change: [What you changed]
   - Validation: ✅ Passed

## Remaining Tasks (Manual)
1. **[TASK-ID]**: [Description] - [Why manual]

## Metrics Impact
- Before: [Metric values]
- After: [Metric values]
```

**Also update:**
- `THOUGHTS.md` - Your reasoning
- `DECISIONS.md` - Why you prioritized certain items
- `LEARNINGS.md` - Patterns you discovered

---

## Exit Conditions

**If you implemented improvements:**
```
<promise>IMPROVEMENTS_COMPLETE</promise>
Status: SUCCESS
Implemented: N quick wins
Queued: M tasks for manual execution
```

**If no improvements found:**
```
<promise>NO_IMPROVEMENTS_NEEDED</promise>
Status: SUCCESS
Analysis: System is healthy, no quick wins identified
```

**If blocked:**
```
Status: BLOCKED
Blocker: [Specific issue]
Help needed: [What you need]
```

---

## Example Run

```
[RALF] Reading skill-metrics.yaml...
[RALF] Found 23 skills, 0 with usage data
[RALF] Reading skill-selection.yaml...
[RALF] Found threshold at 70%

[RALF] Phase 1: SCOUT complete
[RALF] Found 8 opportunities

[RALF] Phase 2: ANALYZE complete
[RALF] Top opportunity: Lower threshold (Score: 14.5)
[RALF] Quick win identified: Yes

[RALF] Phase 3: IMPLEMENT
[RALF] Changing threshold: 70% → 60%
[RALF] ✓ File updated

[RALF] Phase 4: VALIDATE
[RALF] ✓ Threshold is now 60%
[RALF] ✓ YAML syntax valid

[RALF] Phase 5: REPORT
[RALF] Writing RESULTS.md...

<promise>IMPROVEMENTS_COMPLETE</promise>
Status: SUCCESS
Implemented: 1 quick win
Queued: 7 tasks for manual execution
```

---

## Constraints

- **Time limit:** 30 minutes max per run
- **Scope:** Quick wins only (≤30 min each)
- **Safety:** Never break existing functionality
- **Documentation:** Must update all template files
- **Git:** Commit changes with descriptive message

---

## Commands Available

```bash
# Log a thought
ralf-thought "Found opportunity: ..."

# Check documentation
ralf-check-docs

# Git operations
git add <files>
git commit -m "ralf: [description]"
```

---

**Start by reading the metrics files and finding opportunities.**
