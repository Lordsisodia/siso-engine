# Dual-RALF Handover Document

**Version:** 1.0.0
**Created:** 2026-02-01
**Status:** Ready for deployment

---

## What Was Built

### Architecture Overview

Dual-RALF is a dual-agent autonomous system where two specialized Claude instances work in parallel on the same codebase:

```
┌─────────────────┐         ┌─────────────────┐
│  RALF-Planner   │◄───────►│  RALF-Executor  │
│  (Strategist)   │  Files  │  (Tactician)    │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │    ┌───────────────┐      │
         └───►│  BlackBox5    │◄─────┘
              │  Codebase     │
              └───────────────┘
```

### Agent Responsibilities

| Aspect | RALF-Planner | RALF-Executor |
|--------|--------------|---------------|
| **Role** | Thinker, analyst, organizer | Doer, implementer, committer |
| **Primary work** | Analyze codebase, plan tasks, answer questions | Execute tasks, write code, run tests |
| **Writes to** | queue.yaml, chat-log.yaml (answers) | events.yaml, chat-log.yaml (questions) |
| **Reads from** | events.yaml, chat-log.yaml (questions) | queue.yaml, chat-log.yaml (answers) |
| **Makes commits** | No | Yes |
| **Modifies code** | No (plans reorganization) | Yes |
| **Loop timing** | Every 30 seconds | Every 30 seconds |

---

## Why It Was Built

### Problems with Single-Agent System

1. **Context switching overhead** — Planning and execution compete for the same context window
2. **Stale STATE.yaml** — No automatic updates led to duplicate work (17% of runs)
3. **No parallel processing** — Analysis and execution happened sequentially
4. **Limited specialization** — One agent tried to do everything

### Efficiency Gains

| Metric | Single Agent | Dual Agent | Improvement |
|--------|--------------|------------|-------------|
| Context switches | High | None | 100% reduction |
| Analysis during execution | No | Yes | Parallel processing |
| Duplicate work | 17% | Target <5% | 70% reduction |
| Queue depth | 1-2 tasks | 3-5 tasks | Better planning |

### Why 2 Agents (Not 1, Not 10)

- **1 agent**: Context switching overhead, no parallel work
- **2 agents**: Optimal coordination (1 communication link), clear responsibilities
- **10 agents**: Coordination overhead grows quadratically (45 links), diminishing returns

---

## How It Works

### Communication Protocol

Agents communicate via YAML files in `5-project-memory/blackbox5/.autonomous/communications/`:

```
communications/
├── queue.yaml      # Planner writes tasks, Executor reads
├── events.yaml     # Executor writes status, Planner reads
├── chat-log.yaml   # Bidirectional messages (questions/answers)
├── heartbeat.yaml  # Both write health status
└── protocol.yaml   # Communication rules
```

### File-Based Communication

**Why files?**
- Works in GitHub Codespaces without additional infrastructure
- Atomic writes prevent conflicts
- Git history provides audit trail
- No network dependencies

**Conflict prevention:**
```bash
# Atomic write pattern
1. Write to temp file: queue.yaml.tmp
2. Rename: mv queue.yaml.tmp queue.yaml
3. Git operations use locks
```

### 30-Second Loop

**Planner loop:**
1. Read events.yaml (check Executor progress)
2. Read chat-log.yaml (answer questions)
3. Read heartbeat.yaml (check Executor health)
4. Check queue depth (plan more if <2 tasks)
5. Write heartbeat.yaml
6. Sleep 30 seconds

**Executor loop:**
1. Read queue.yaml (check for tasks)
2. Read heartbeat.yaml (check Planner health)
3. IF task available: claim and execute
4. IF no task: report idle
5. Write heartbeat.yaml
6. Sleep 30 seconds

### Task Lifecycle

```
Planner                          Executor
   │                                │
   ├─► Analyze codebase ───────────►│ (idle)
   │                                │
   ├─► Write task to queue.yaml ───►│
   │                                ├─► Read queue.yaml
   │                                ├─► Claim task
   │◄─ Write events.yaml (started) ─┤
   │                                ├─► Execute task
   │                                ├─► Run quality gates
   │                                ├─► Commit changes
   │◄─ Write events.yaml (done) ────┤
   ├─► Read events.yaml ───────────►│ (idle)
   │                                │
   ├─► Mark complete in STATE.yaml  │
   │                                │
```

---

## File Locations and Structure

### Core Prompts

```
2-engine/.autonomous/prompts/system/
├── planner/
│   ├── README.md
│   └── variations/
│       ├── v1.md                    # Complete operational prompt
│       └── v1-IMPROVEMENTS.md       # Known limitations, testing checklist
├── executor/
│   ├── README.md
│   └── variations/
│       ├── v1.md                    # Complete operational prompt
│       └── v1-IMPROVEMENTS.md       # Known limitations, testing checklist
└── handover/
    └── DUAL-RALF-HANDOVER.md        # This document
```

### Communication Files

```
5-project-memory/blackbox5/.autonomous/
├── communications/
│   ├── queue.yaml                   # Task assignments
│   ├── events.yaml                  # Execution status
│   ├── chat-log.yaml               # Bidirectional messages
│   ├── heartbeat.yaml              # Health checks
│   └── protocol.yaml               # Communication rules
├── runs/
│   ├── active/                     # Currently executing runs
│   ├── completed/                  # Finished runs (47 historical)
│   └── archived/                   # Old runs (moved after 90 days)
├── tasks/
│   ├── active/                     # Pending tasks
│   └── completed/                  # Finished tasks
└── memory/
    ├── learnings/                  # Captured learnings
    ├── decisions/                  # Decision registry
    └── assumptions/                # Validated assumptions
```

### Shell Scripts

```
bin/
├── ralf-planner                    # Start Planner agent
├── ralf-executor                   # Start Executor agent
└── ralf-dual                       # Start both with tmux
```

### State Files

```
5-project-memory/blackbox5/
├── STATE.yaml                      # Ground truth state
├── goals.yaml                      # Project goals
└── MAP.yaml                        # Codebase map (Planner maintains)
```

---

## How to Start/Stop/Monitor

### Starting the System

```bash
# Option 1: Start both agents with tmux
~/.blackbox5/bin/ralf-dual

# Option 2: Start individually (in separate terminals)
~/.blackbox5/bin/ralf-planner
~/.blackbox5/bin/ralf-executor

# Option 3: Start with specific model
MODEL=claude-opus-4 ~/.blackbox5/bin/ralf-dual
```

### Stopping the System

```bash
# Stop both agents
~/.blackbox5/bin/ralf-dual --stop

# Or manually
pkill -f "ralf-planner"
pkill -f "ralf-executor"
```

### Monitoring

```bash
# Watch queue depth
watch -n 5 'cat ~/.blackbox5/5-project-memory/blackbox5/.autonomous/communications/queue.yaml | grep -c "status: pending"'

# Watch events
watch -n 5 'cat ~/.blackbox5/5-project-memory/blackbox5/.autonomous/communications/events.yaml'

# Check heartbeats
cat ~/.blackbox5/5-project-memory/blackbox5/.autonomous/communications/heartbeat.yaml

# View tmux sessions
tmux ls
tmux attach -t ralf-planner
tmux attach -t ralf-executor
```

---

## Key Design Decisions

### 1. File-Based vs. Network Communication

**Decision:** Use YAML files instead of Redis/message queue

**Rationale:**
- Works in GitHub Codespaces without additional services
- Simpler deployment (no infrastructure)
- Git provides audit trail
- Atomic file operations prevent conflicts

**Trade-off:** Slightly higher latency (30s loop) vs. real-time

### 2. Planner Doesn't Commit

**Decision:** Only Executor makes git commits

**Rationale:**
- Prevents conflicts between agents
- Clear ownership of changes
- Executor has context of what changed

**Trade-off:** Planner can't directly fix organizational issues

### 3. 30-Second Loop

**Decision:** Fixed 30-second polling interval

**Rationale:**
- Balance between responsiveness and resource usage
- Prevents tight-loop CPU spinning
- Allows for human intervention between cycles

**Trade-off:** Up to 30-second delay in task handoff

### 4. Same Codespace, Shared Filesystem

**Decision:** Both agents run in same GitHub Codespace

**Rationale:**
- Shared filesystem for communication
- No network complexity
- Single git repository
- Cost efficient

**Trade-off:** Can't scale beyond one Codespace

### 5. Queue Depth Target: 3-5 Tasks

**Decision:** Planner maintains 3-5 tasks in queue

**Rationale:**
- Prevents Executor idle time
- Not so many that plans become stale
- Allows Planner to adapt based on Executor discoveries

**Trade-off:** Planner must plan frequently

---

## Operational Details

### Pre-Planning/Pre-Execution Research

Both agents run research before acting:

```bash
# Check for duplicate tasks
grep -r "[task keyword]" ~/.blackbox5/5-project-memory/blackbox5/.autonomous/tasks/completed/ 2>/dev/null | head -5

# Check recent commits
cd ~/.blackbox5 && git log --oneline --since="1 week ago" | grep -i "[keyword]" | head -5

# Verify target paths exist
ls -la [target paths] 2>/dev/null

# Check file history
git log --oneline --since="1 week ago" -- [target paths] | head -3
```

### Context Budget Management

Track token usage to prevent context overflow:

```yaml
context_budget:
  config:
    max_tokens: 200000
    thresholds:
      subagent: 40      # Spawn sub-agent
      warning: 70       # Compress THOUGHTS.md
      critical: 85      # Emergency summary
      hard_limit: 95    # Force checkpoint exit
```

### Phase Gates

Track progress through development phases:

```yaml
gates:
  init: { status: passed, timestamp: "2026-02-01T00:00:00Z" }
  quick_spec: { status: pending }
  dev_story: { status: pending }
  code_review: { status: pending }
  validate: { status: pending }
  wrap: { status: pending }
```

### Integration Check (Executor)

Before committing, Executor verifies:

```bash
# 1. Does it import?
python3 -c "import [module]" && echo "✓ Imports successfully"

# 2. Does it work with existing code?
python3 -c "
from [new_module] import [class]
from [existing_module] import [existing_class]
# Try to use them together
" && echo "✓ Integrates with existing code"

# 3. Can it be called?
python3 -c "
from [module] import [main_function]
result = [main_function]()
print(f'✓ Returns: {type(result)}')
"
```

### Quality Gates

**Planner (before adding to queue):**
- [ ] Task is clear and actionable
- [ ] Approach is specified
- [ ] Files to modify identified
- [ ] Acceptance criteria defined
- [ ] Not a duplicate
- [ ] Target paths exist

**Executor (before commit):**
- [ ] Assumptions validated
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Committed to dev branch
- [ ] THOUGHTS.md shows clear reasoning
- [ ] No obvious errors
- [ ] Integration verified

---

## Skills Integration

### Available Skills

| Skill | Planner | Executor | Purpose |
|-------|---------|----------|---------|
| truth-seeking | ✓ | ✓ | Validate assumptions |
| deep-research | ✓ | | Research and analysis |
| architecture-design | ✓ | | System design |
| codebase-navigation | ✓ | | Find files, patterns |
| run-initialization | | ✓ | Create run folder |
| code-implementation | | ✓ | TDD development |
| testing-validation | | ✓ | Quality assurance |
| git-commit | | ✓ | Safe commits |
| state-management | | ✓ | Update STATE.yaml |
| documentation | ✓ | ✓ | Create docs |
| continuous-improvement | ✓ | | Capture learnings |

### Skill Discovery Process

1. Read `.skills/skills-index.yaml`
2. Match task keywords to skill triggers
3. Load skill file
4. Execute appropriate command
5. Document in THOUGHTS.md

---

## Communication Examples

### Task Assignment (queue.yaml)

```yaml
queue:
  - id: "TASK-001"
    type: implement
    title: "Add user authentication"
    priority: high
    estimated_minutes: 60
    context_level: 2
    approach: "Use JWT tokens, add middleware, create login endpoint"
    files_to_modify: ["src/auth.py", "src/middleware.py"]
    acceptance_criteria: ["Users can login", "Tokens expire after 24h"]
    dependencies: []
    added_at: "2026-02-01T12:00:00Z"
    status: pending
```

### Event Reporting (events.yaml)

```yaml
events:
  - timestamp: "2026-02-01T12:00:00Z"
    task_id: "TASK-001"
    type: started

  - timestamp: "2026-02-01T12:45:00Z"
    task_id: "TASK-001"
    type: completed
    result: success
    commit_hash: "abc123"
```

### Chat Message (chat-log.yaml)

```yaml
messages:
  - id: 1
    from: executor
    to: planner
    timestamp: "2026-02-01T12:10:00Z"
    type: question
    task_id: "TASK-001"
    content: "Should I use bcrypt or argon2 for password hashing?"

  - id: 2
    from: planner
    to: executor
    timestamp: "2026-02-01T12:11:00Z"
    type: answer
    in_reply_to: 1
    content: "Use argon2. It's the modern standard. Add TODO to migrate legacy bcrypt hashes."
```

---

## Error Handling

### Executor Failure

1. Stop execution
2. Document in THOUGHTS.md
3. Write to events.yaml (type: failed)
4. Ask in chat-log.yaml (if recoverable)
5. Wait for Planner response

### Planner Timeout

If Planner heartbeat > 2 minutes old:
1. Executor alerts and continues cautiously
2. Executor can proceed with defined fallbacks
3. Document assumption in THOUGHTS.md

### Communication Conflict

If both agents try to write same file:
1. Atomic writes prevent corruption
2. Last write wins (acceptable for heartbeat)
3. Queue uses append-only pattern
4. Events use append-only pattern

---

## Testing Checklist

### Phase 1: Basic Functionality
- [ ] Planner starts and writes heartbeat
- [ ] Executor starts and writes heartbeat
- [ ] Planner writes to queue.yaml
- [ ] Executor reads queue.yaml
- [ ] Executor claims tasks
- [ ] Executor executes tasks
- [ ] Executor writes events

### Phase 2: Communication
- [ ] Executor asks questions via chat-log.yaml
- [ ] Planner answers via chat-log.yaml
- [ ] Executor reports discoveries
- [ ] Heartbeats update every 30s
- [ ] Handles Planner timeout gracefully

### Phase 3: Quality
- [ ] Runs quality gates before commit
- [ ] Creates proper run documentation
- [ ] Commits safely (not to main/master)
- [ ] Updates STATE.yaml correctly

### Phase 4: Edge Cases
- [ ] Handles empty queue (idle timeout)
- [ ] Handles corrupted task in queue
- [ ] Recovers from crash mid-task
- [ ] Handles agent death/restart

---

## Metrics to Track

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Task completion rate | > 90% | completed / (completed + failed) |
| Average execution time | Match estimate | Compare actual vs estimated |
| Question frequency | < 1 per 3 tasks | Count chat questions |
| Idle time | < 10% | Time waiting for tasks |
| Commit success rate | 100% | Failed commits should be 0 |
| Duplicate work | < 5% | Tasks that repeat previous work |
| Queue depth | 3-5 tasks | Average pending tasks |

---

## Future Improvements

### v1.1 Ideas
- Add self-correction (read own past learnings)
- Add skill effectiveness tracking
- Add automatic context level selection
- Add parallel task execution (if independent)

### v2.0 Ideas
- Predictive execution (anticipate next task)
- Automatic error recovery (common fixes)
- Dynamic skill learning (new skills from patterns)
- Integration with external tools (CI/CD)

### v3.0 Ideas
- Multi-Executor coordination (load balancing)
- Specialization (Frontend Executor, Backend Executor)
- Self-optimization (tune own parameters)
- Autonomous skill creation

---

## Quick Reference

### Start the system
```bash
~/.blackbox5/bin/ralf-dual
```

### Check status
```bash
cat ~/.blackbox5/5-project-memory/blackbox5/.autonomous/communications/heartbeat.yaml
```

### View queue
```bash
cat ~/.blackbox5/5-project-memory/blackbox5/.autonomous/communications/queue.yaml
```

### View recent events
```bash
cat ~/.blackbox5/5-project-memory/blackbox5/.autonomous/communications/events.yaml
```

### Attach to tmux session
```bash
tmux attach -t ralf-planner   # or ralf-executor
```

### Read current STATE
```bash
cat ~/.blackbox5/5-project-memory/blackbox5/STATE.yaml
```

---

## Summary

Dual-RALF replaces the single-agent RALF with two specialized agents that work in parallel:

- **RALF-Planner**: Analyzes, plans, organizes, answers questions
- **RALF-Executor**: Executes tasks, writes code, makes commits

They communicate via YAML files in a shared GitHub Codespace, following a 30-second loop pattern. The system is designed for efficiency through specialization, with clear separation of concerns and robust error handling.

**Key principle:** Planner thinks so Executor can focus on doing.

---

**Next Steps:**
1. Review this handover document
2. Check v1 prompts in `planner/variations/v1.md` and `executor/variations/v1.md`
3. Run testing checklist
4. Deploy to production Codespace
5. Monitor metrics and iterate

**Questions?** Check the improvement notes in `v1-IMPROVEMENTS.md` for known limitations and future directions.
