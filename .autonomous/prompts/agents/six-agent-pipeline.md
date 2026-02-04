# 6-Agent RALF Pipeline - Orchestrator

**Version:** 1.0.0
**Purpose:** Coordinate 6-agent system for intelligent GitHub repo analysis
**Architecture:** 3 Workers + 3 Validators

---

## Agent Pipeline Flow

```
REPO_LIST (18 repos)
    ↓
[Deep Repo Scout] → 3-loop analysis → knowledge doc
    ↓
[Scout Validator] → Approve/Reject
    ↓ (if approved)
[Integration Analyzer] → Assess integration value
    ↓
[Analyzer Validator] → Verify scoring
    ↓ (if approved)
[Implementation Planner] → Create executable tasks
    ↓
[Planner Validator] → Verify plans
    ↓ (if approved)
EXECUTOR QUEUE (ready-to-run tasks)
```

---

## Queue System

### Stage 1: Scout Queue
- **Input:** `repo-list.yaml` (18 repos)
- **Worker:** Deep Repo Scout
- **Output:** `knowledge/REPO-NAME-knowledge.md`
- **Validator:** Scout Validator
- **Reject Path:** Back to Scout for rework

### Stage 2: Analyzer Queue
- **Input:** Approved knowledge docs
- **Worker:** Integration Analyzer
- **Output:** `assessments/integration-assessments.md`
- **Validator:** Analyzer Validator
- **Reject Path:** Back to Analyzer for rescoring

### Stage 3: Planner Queue
- **Input:** Validated assessments (high-ROI only)
- **Worker:** Implementation Planner
- **Output:** `plans/implementation-plans.md` + `tasks/TASK-*.md`
- **Validator:** Planner Validator
- **Reject Path:** Back to Planner for revision

### Stage 4: Executor Queue
- **Input:** Approved tasks
- **Worker:** RALF Executor (existing)
- **Output:** Implemented integrations

---

## File Structure

```
5-project-memory/blackbox5/.autonomous/
├── research-pipeline/
│   ├── repos/                    # Cloned repos (temp)
│   ├── knowledge/                # Scout output
│   │   ├── REPO-NAME-knowledge.md
│   │   └── rejected/             # Failed validation
│   ├── assessments/              # Analyzer output
│   │   ├── integration-assessments.md
│   │   └── adjusted/             # Post-validation
│   ├── plans/                    # Planner output
│   │   ├── implementation-plans.md
│   │   └── revision-needed/      # Failed validation
│   └── tasks/ready/              # Approved tasks
│       └── TASK-*.md
├── agents/
│   ├── scout-worker/
│   ├── scout-validator/
│   ├── analyzer-worker/
│   ├── analyzer-validator/
│   ├── planner-worker/
│   └── planner-validator/
└── communications/
    ├── scout-queue.yaml
    ├── analyzer-queue.yaml
    ├── planner-queue.yaml
    └── executor-queue.yaml
```

---

## Communication Protocol

Workers and validators communicate via YAML files:

### scout-queue.yaml
```yaml
queue:
  - repo_url: https://github.com/...
    status: pending|in_progress|completed|failed
    assigned_worker: scout-1
    knowledge_doc: knowledge/REPO-NAME-knowledge.md
    validation_status: pending|approved|rejected
    validator_feedback: ""
```

### analyzer-queue.yaml
```yaml
queue:
  - knowledge_doc: knowledge/REPO-NAME-knowledge.md
    status: pending|in_progress|completed
    assessment_doc: assessments/integration-assessments.md
    validation_status: pending|approved|adjusted
```

### planner-queue.yaml
```yaml
queue:
  - assessment_ref: assessments/integration-assessments.md#concept-name
    status: pending|in_progress|completed
    plan_doc: plans/implementation-plans.md
    tasks_created: [TASK-001, TASK-002]
    validation_status: pending|approved|needs_revision
```

### executor-queue.yaml
```yaml
queue:
  - task_file: tasks/ready/TASK-*.md
    status: pending|claimed|completed
    claimed_by: executor-1
    results: runs/run-*/RESULTS.md
```

---

## Run Cycle

Each agent runs in a loop:

1. **Check queue** for pending work
2. **Claim item** (update status to in_progress)
3. **Execute** (run the prompt)
4. **Submit** (create output, update status to completed)
5. **Wait for validator** (validator reviews and approves/rejects)
6. **If rejected:** Rework and resubmit
7. **If approved:** Move to next stage

---

## Exit Conditions

Pipeline completes when:
- All repos processed through Scout
- All approved knowledge docs analyzed
- All high-ROI concepts planned
- All plans validated and queued for execution

---

## Success Metrics

- **Quality over quantity** — Fewer, high-quality integrations > many shallow ones
- **Validator pass rate** — Target 60% (if 100% pass, validators are too lenient)
- **Executor success rate** — Target 90% (plans should be executable)
- **Time per repo** — Scout: 30min, Analyzer: 15min, Planner: 20min

---

## Start Command

```bash
cd ~/.blackbox5
./bin/ralf-six-agent-pipeline.sh
```

This starts all 6 agents in tmux sessions with proper environment.
