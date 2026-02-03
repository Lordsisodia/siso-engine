# Planner v1 Improvement Notes

**Version:** 1.0.0
**Created:** 2026-02-01
**Status:** Initial version, ready for testing

---

## What's Working (Hypothesized)

### Strengths
1. **Clear separation of concerns** — Planner doesn't execute, only plans
2. **Comprehensive communication spec** — All files documented
3. **Loop behavior well-defined** — 30-second cycle with clear steps
4. **First principles integration** — Built-in deconstruction guidance
5. **Context levels** — Flexible task specification (1/2/3)

### Design Decisions
- File-based communication (simple, debuggable)
- Queue depth target of 5 (balance between ahead and over-planning)
- Analysis during idle time (uses CPU efficiently)
- Heartbeat mechanism (health monitoring)

---

## Known Limitations

### 1. Planning Logic Not Fully Specified
**Issue:** "Plan more tasks" is vague.
**Current:** "Read STATE.yaml, find next_action"
**Need:** Actual planning algorithm

**Potential improvements:**
- Dependency graph analysis
- Effort estimation based on historical data
- Priority scoring algorithm
- Parallel vs sequential task ordering

### 2. Question Answering Not Detailed
**Issue:** "Formulate answer" lacks structure
**Current:** Generic guidance
**Need:** Structured response format

**Potential improvements:**
- Answer templates by question type
- Context gathering before answering
- Confidence levels in answers
- Fallback when uncertain

### 3. Failure Recovery Basic
**Issue:** "IF systemic: Clear queue, re-plan" is vague
**Current:** High-level decision tree
**Need:** Specific recovery procedures

**Potential improvements:**
- Failure classification (recoverable vs fatal)
- Automatic retry with backoff
- Escalation thresholds
- Rollback procedures

### 4. No Learning Integration
**Issue:** Doesn't explicitly use past learnings
**Current:** Generic "analyze patterns"
**Need:** Specific learning integration

**Potential improvements:**
- Read LEARNINGS.md from recent runs
- Pattern matching against known issues
- Adaptive planning based on Executor's style
- Historical success rate per task type

---

## Testing Checklist

### Phase 1: Basic Functionality
- [ ] Planner starts and writes heartbeat
- [ ] Planner reads STATE.yaml correctly
- [ ] Planner fills queue when empty
- [ ] Planner responds to questions within 2 minutes
- [ ] Planner writes analysis during idle time

### Phase 2: Communication
- [ ] Queue.yaml format correct
- [ ] Chat responses formatted correctly
- [ ] Events.yaml read correctly
- [ ] Heartbeat updated every 30s

### Phase 3: Adaptation
- [ ] Adjusts queue based on Executor events
- [ ] Handles Executor failure gracefully
- [ ] Updates plans based on discoveries
- [ ] Maintains 3-5 task queue depth

### Phase 4: Edge Cases
- [ ] Handles empty STATE.yaml
- [ ] Handles corrupted queue.yaml
- [ ] Recovers from crash
- [ ] Handles Executor timeout

---

## Metrics to Track

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Queue depth stability | 3-5 tasks | Check queue.yaml every minute |
| Question response time | < 2 min | Timestamp analysis |
| Planning quality | Executor success rate | Track completed vs failed |
| Analysis output | 1 doc per hour idle | Count knowledge/analysis files |
| State consistency | No conflicts | Verify STATE.yaml updates |

---

## Future Versions

### v1.1 Ideas
- Add learning integration (read past LEARNINGS.md)
- Add effort estimation based on history
- Add dependency visualization
- Add automatic pattern recognition

### v2.0 Ideas
- Multiple queue strategies (FIFO, priority, dependency-based)
- Predictive planning (anticipate Executor needs)
- Self-improvement loop (analyze own planning effectiveness)
- Integration with external knowledge bases

### v3.0 Ideas
- Multi-Planner coordination (for large projects)
- Machine learning for effort estimation
- Automatic skill recommendation
- Dynamic context level selection

---

## Feedback from Runs

### Run 1: [Date]
- What worked:
- What didn't:
- Changes needed:

### Run 2: [Date]
- What worked:
- What didn't:
- Changes needed:

[Add more as we test]

---

## Comparison to Single-Agent

| Aspect | Single RALF | Dual Planner | Notes |
|--------|-------------|--------------|-------|
| Planning depth | Shallow | Deep | Planner has time to analyze |
| Context switching | High | None | Each agent focused |
| Communication overhead | None | File I/O | Measure if bottleneck |
| Adaptability | Reactive | Proactive | Planner sees patterns |
| Complexity | Low | Medium | Worth it for throughput? |

---

## Open Questions

1. Is 30-second loop optimal? Too fast? Too slow?
2. Is 5-task queue depth right? Should it be dynamic?
3. Should Planner ever execute simple tasks?
4. How to handle Planner-Executor disagreement?
5. Should Planner have sub-agents for different analysis types?

---

## Related Files

- `DUAL-RALF-ARCHITECTURE.md` — System architecture
- `communications/protocol.yaml` — Communication rules
- `executor/variations/v1.md` — Companion agent prompt
- `CLAUDE.md` — High-level guidance (shared)
- `LEGACY.md` — Execution procedures (Executor uses this)

---

**Next Review:** After 10 runs or 1 week, whichever comes first
