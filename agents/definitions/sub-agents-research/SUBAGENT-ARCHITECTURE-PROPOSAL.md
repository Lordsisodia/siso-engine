# BlackBox5 Sub-Agent Architecture Proposal

**Date:** 2026-02-07
**Status:** Draft for Review
**Based on:** Comprehensive analysis of 60+ agents across internal and external sources

---

## Executive Summary

This proposal outlines a complete sub-agent ecosystem for BlackBox5 that addresses:
1. **Tunnel vision prevention** - Cross-file consistency agents
2. **Quality gates** - Multi-level verification system
3. **Long-term memory** - Persistent context and ADR maintenance
4. **Workflow orchestration** - Thin orchestrator pattern with 4 core flows

**Key Innovation:** The "Ghost of the Past" (ADR maintainer) ensures agents never undo critical decisions 6 months later.

---

## Proposed Sub-Agent Suite

### Tier 1: Core Workflow Agents (Must Have)

| Agent | Role | When to Call | Replaces/Extends |
|-------|------|--------------|------------------|
| **bb5-master-orchestrator** | Routes requests to appropriate flows | Every user request | Current manual orchestration |
| **bb5-research-synthesizer** | Merges 4 parallel researcher outputs | After research phase | Manual synthesis |
| **bb5-dependency-analyzer** | Detects conflicts between parallel tasks | Planning phase | Current manual dependency tracking |
| **bb5-debugger** | Root cause analysis on failures | Execution failures | Current retry loops |
| **bb5-integrator** | Merges parallel execution results | After wave execution | Manual conflict resolution |

### Tier 2: Memory & Context Agents (High Value)

| Agent | Role | When to Call | Pattern Source |
|-------|------|--------------|----------------|
| **bb5-scribe** | Maintains run documentation (THOUGHTS, DECISIONS, LEARNINGS) | Continuous during execution | Continuous-Claude-v3 chronicler |
| **bb5-ghost-of-past** (ADR maintainer) | Records why decisions were made | At every significant decision | ADR pattern + episodic memory |
| **bb5-context-persistence** | Manages 3-tier memory (short/medium/long) | Continuous | BB5 memory system |
| **bb5-bookkeeper** | Tracks organizational hygiene | Scheduled/continuous | Existing bookkeeper sub-agent |

### Tier 3: Quality & Safety Agents (Critical)

| Agent | Role | When to Call | Pattern Source |
|-------|------|--------------|----------------|
| **bb5-validator** | 3-level verification (existence/substantive/wired) | Post-execution | Existing bb5-verifier |
| **bb5-qa-specialist** | Regression testing, test generation | Post-validation | Continuous-Claude-v3 arbiter |
| **bb5-security-guard** | Vulnerability scanning, OWASP compliance | Pre-merge | Continuous-Claude-v3 aegis |
| **bb5-performance-profiler** | Efficiency gates, Big-O analysis | Post-implementation | Novel |

### Tier 4: Specialized Agents (Domain-Specific)

| Agent | Role | When to Call | Pattern Source |
|-------|------|--------------|----------------|
| **bb5-refactor-scout** | Technical debt detection | Scheduled/manual | Continuous-Claude-v3 phoenix |
| **bb5-triage-router** | Classifies and routes to specialists | Entry point | Novel |
| **bb5-test-writer** | Automated test generation | Post-implementation | Novel |
| **bb5-documentation-reviewer** | Doc-code consistency | Pre-merge | Novel |

### Tier 5: Meta Agents (Self-Improving)

| Agent | Role | When to Call | Pattern Source |
|-------|------|--------------|----------------|
| **bb5-self-evolver** | Modifies other agents based on success rates | Weekly/continuous | Novel - highest level |
| **bb5-meta-agent** | Creates new agent definitions from descriptions | On demand | claude-code-hooks-mastery |

---

## Workflow Architecture

### 5 Core Flows

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BLACKBOX5 MASTER ORCHESTRATOR                            │
│                         (15% context budget)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   RESEARCH   │  │   PLANNING   │  │   EXECUTION  │  │ VERIFICATION │    │
│  │    FLOW      │  │    FLOW      │  │    FLOW      │  │    FLOW      │    │
│  │              │  │              │  │              │  │              │    │
│  │ 4 parallel   │  │ Planner-     │  │ Wave-based   │  │ 3-level      │    │
│  │ researchers  │  │ Checker loop │  │ parallel     │  │ artifact     │    │
│  │ → Synthesizer│  │ → Dependency │  │ → Debugger   │  │ check        │    │
│  │              │  │   analyzer   │  │   on fail    │  │ → QA check   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │             │
│         └─────────────────┴─────────────────┴─────────────────┘             │
│                           │                                                 │
│                           ▼                                                 │
│              ┌─────────────────────────┐                                   │
│              │    MEMORY FLOW          │                                   │
│              │  (Scribe + ADR + Ghost) │                                   │
│              │    Continuous           │                                   │
│              └─────────────────────────┘                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Flow Details

#### 1. Research Flow
**Purpose:** Gather comprehensive context before any implementation

**Agents:**
- bb5-stack-researcher (tech stack, dependencies)
- bb5-architecture-researcher (patterns, components)
- bb5-convention-researcher (code style, standards)
- bb5-risk-researcher (security, pitfalls)
- bb5-research-synthesizer (merges outputs, extracts concepts)

**Output:** `research_package.yaml`

#### 2. Planning Flow
**Purpose:** Create actionable, validated implementation plans

**Agents:**
- bb5-architect (system design, component interfaces)
- bb5-planner (creates XML task plans)
- bb5-checker (validates against 7 dimensions)
- bb5-dependency-analyzer (builds DAG, calculates waves)

**Output:** `plan_package.yaml` with wave groups

#### 3. Execution Flow
**Purpose:** Implement tasks with maximum parallelism

**Agents:**
- Wave Orchestrator (manages parallel execution)
- bb5-executor (fresh context per task)
- bb5-debugger (root cause analysis on failure)
- bb5-integrator (merges parallel results)

**Output:** `execution_package.yaml`

#### 4. Verification Flow
**Purpose:** Ensure quality through multi-level checks

**Agents:**
- bb5-validator (3-level artifact check)
- bb5-qa-specialist (regression testing)
- bb5-security-guard (vulnerability scan)

**Output:** `verification_package.yaml`

#### 5. Memory Flow
**Purpose:** Persist context and decisions for future agents

**Agents:**
- bb5-scribe (maintains run documentation)
- bb5-ghost-of-past (maintains ADRs)
- bb5-context-persistence (3-tier memory management)

**Output:** Updated STATE.yaml, ADRs, archived runs

---

## Agent Specifications

### bb5-master-orchestrator

```yaml
name: bb5-master-orchestrator
description: |
  Central coordinator for all BlackBox5 sub-agents.
  Never does heavy lifting - only routes and coordinates.
  Maintains < 15% context usage by delegating everything.
model: sonnet
tools: [Task, Read]
color: purple

triggers:
  - All user requests
  - RALF task queue
  - Scheduled workflows

workflow_selection:
  exploration: [research]
  architecture: [research, planning]
  implementation: [research, planning, execution, verification]
  bugfix: [execution, verification]
  optimization: [research, execution]
  documentation: [memory]
```

### bb5-ghost-of-past (ADR Maintainer)

```yaml
name: bb5-ghost-of-past
description: |
  Maintains Architecture Decision Records (ADRs) that capture
  WHY decisions were made, not just WHAT was done.

  Prevents future agents from undoing critical optimizations
  by providing "episodic memory" of original struggles.
model: sonnet
tools: [Read, Write, Grep]
color: gray

triggers:
  - Significant architectural decisions
  - Performance optimizations
  - Trade-off discussions
  - Before any major refactor

adr_template:
  status: proposed | accepted | deprecated | superseded
  context: "What is the issue we're seeing?"
  decision: "What are we doing about it?"
  consequences: "What becomes easier/harder?"
  alternatives: "What else did we consider?"
  rationale: "Why this over alternatives?"
```

### bb5-scribe

```yaml
name: bb5-scribe
description: |
  Documentation and memory persistence agent.
  Transforms transient chat history into permanent,
  searchable codebase context.

  Maintains: THOUGHTS.md, DECISIONS.md, LEARNINGS.md, RESULTS.md
model: sonnet
tools: [Read, Write, Glob]
color: cyan

triggers:
  - Continuous during execution
  - On decision points
  - On failures/successes
  - Post-verification

outputs:
  - runs/run-*/THOUGHTS.md
  - runs/run-*/DECISIONS.md
  - runs/run-*/LEARNINGS.md
  - runs/run-*/RESULTS.md
  - decisions/ADR-XXX.md
```

### bb5-dependency-analyzer

```yaml
name: bb5-dependency-analyzer
description: |
  Ensures sub-agents working in parallel don't conflict.
  Identifies if a backend change requires frontend updates.

  Builds DAG of tasks, detects cycles, calculates waves.
model: sonnet
tools: [Read, Grep, Bash]
color: yellow

triggers:
  - Planning phase
  - Before major merge
  - When adding parallel tasks

algorithm:
  1. Parse all task dependencies
  2. Build directed acyclic graph
  3. Detect cycles (fail if found)
  4. Topological sort
  5. Group into waves by depth
  6. Calculate critical path

output: wave_groups.yaml
```

### bb5-debugger

```yaml
name: bb5-debugger
description: |
  Root cause analysis for failed verifications.
  Uses hypothesis-driven investigation with evidence trails.

  Part of thin orchestrator Stage 4 (when verification fails).
model: opus
tools: [Read, Bash, Grep, Glob]
color: red

triggers:
  - Verification failure
  - Test suite failure
  - Build failure
  - Runtime error

process:
  1. Gather error logs and stack traces
  2. Form hypotheses about root cause
  3. Test hypotheses systematically
  4. Document evidence trail
  5. Propose fix strategy
  6. Recommend retry or escalate

erotetic_check: |
  Before debugging, frame the question space E(X,Q):
  - X = [the failing component/behavior]
  - Q = [questions that must be answered]
  - Approach: [systematic hypothesis testing]
```

### bb5-self-evolver

```yaml
name: bb5-self-evolver
description: |
  The highest level of agentic intelligence.
  Monitors success rates and modifies other agents' prompts.

  Your CLI literally gets smarter the more you use it.
model: opus
tools: [Read, Write, Grep, Bash]
color: gold

triggers:
  - Weekly analysis
  - Repeated agent failures
  - User feedback on agent quality

process:
  1. Analyze agent success metrics
  2. Identify failure patterns
  3. Propose prompt improvements
  4. A/B test new prompts
  5. Deploy improvements
  6. Monitor results

constraints:
  - Never modifies core orchestrator
  - Requires human approval for changes
  - Maintains version history
```

---

## Handoff Data Formats

### Between Research and Planning

```yaml
research_package:
  version: "2.0"
  meta:
    research_id: "RES-XXX"
    timestamp: "2026-02-07T12:00:00Z"

  findings:
    stack:
      primary_language: "python"
      frameworks: ["fastapi", "sqlalchemy"]
      key_insights: [...]

    architecture:
      patterns: ["repository", "dependency-injection"]
      components: [...]

    convention:
      style_guide: "black + ruff"
      naming_conventions: {...}

    risk:
      security_risks: [...]
      mitigation_strategies: [...]

  synthesis:
    concepts:
      - name: "Repository Pattern"
        applicability_score: 90
        implementation_approaches: [...]

    conflicts: [...]
    gaps: [...]
```

### Between Planning and Execution

```yaml
plan_package:
  version: "2.0"
  meta:
    plan_id: "PLAN-XXX"
    checker_iterations: 2
    final_score: 87

  waves:
    total_waves: 4
    wave_groups:
      0: ["T-001", "T-002"]
      1: ["T-003", "T-004", "T-005"]
      2: ["T-006", "T-007"]
      3: ["T-008", "T-009", "T-010"]

  tasks:
    - id: "T-001"
      title: "Setup database models"
      type: "implement"
      estimated_effort: "PT2H"
      assignee: "bb5-executor"
      dependencies: []
      deliverable: "src/models.py"
      acceptance_criteria: [...]

  risk_register: [...]
```

### Between Execution and Verification

```yaml
execution_package:
  version: "2.0"
  meta:
    execution_id: "EXEC-XXX"
    plan_id: "PLAN-XXX"

  wave_results:
    - wave: 0
      status: "completed"
      tasks: ["T-001", "T-002"]
      all_succeeded: true

  task_results:
    - task_id: "T-001"
      status: "COMPLETE"
      commit: "abc123"
      summary: "Implemented User model"

  artifacts:
    code_changes:
      - file: "src/models.py"
        commit: "abc123"

    issues:
      - task_id: "T-005"
        issue: "Partial completion"
        reason: "Missing edge case handling"
```

---

## Integration with Existing BB5 Systems

### BMAD Skills Integration

| BMAD Skill | Uses Flows | Integration Point |
|------------|------------|-------------------|
| bmad-pm | Planning | PRD → Planner input |
| bmad-architect | Research + Planning | Architect agent |
| bmad-dev | Execution | Executor agent |
| bmad-qa | Verification | Verifier + QA agents |
| bmad-tea | All flows | Orchestrates for RALF |

### RALF Integration

```
RALF-Planner ──► Planning Flow ──► plans/
RALF-Executor ──► Execution Flow ──► commits
RALF-Scout ──► Research Flow ──► research/
```

### Memory System Integration

```
Ephemeral (runs/) ←── bb5-scribe ──→ Short-term (STATE.yaml)
                           ↓
                    Medium-term (Plans, Timeline)
                           ↓
                    Long-term (Brain, Embeddings, ADRs)
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Create agent template system
- [ ] Implement bb5-master-orchestrator
- [ ] Set up queue system (YAML-based)
- [ ] Create shared state management

### Phase 2: Research Flow (Week 2)
- [ ] Implement 4 parallel researchers
- [ ] Create bb5-research-synthesizer
- [ ] Build research package format

### Phase 3: Planning Flow (Week 3)
- [ ] Implement Planner+Checker loop
- [ ] Create bb5-dependency-analyzer
- [ ] Build plan package format

### Phase 4: Execution Flow (Week 4)
- [ ] Implement Wave Orchestrator
- [ ] Create bb5-debugger
- [ ] Build bb5-integrator

### Phase 5: Verification Flow (Week 5)
- [ ] Enhance bb5-validator
- [ ] Create bb5-qa-specialist
- [ ] Create bb5-security-guard

### Phase 6: Memory Flow (Week 6)
- [ ] Create bb5-scribe
- [ ] Create bb5-ghost-of-past (ADR)
- [ ] Implement 3-tier persistence

### Phase 7: Meta Agents (Week 7)
- [ ] Create bb5-self-evolver
- [ ] Create bb5-meta-agent (agent generator)
- [ ] Set up success metrics tracking

### Phase 8: Integration (Week 8)
- [ ] Integrate with BMAD skills
- [ ] Connect to RALF
- [ ] Performance optimization
- [ ] Documentation

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Research synthesis time | < 5 min | Time from request to synthesis |
| Planning iterations | < 3 | Average checker loops |
| Wave efficiency | > 80% | Parallel task completion rate |
| Verification pass rate | > 85% | First-time pass percentage |
| Memory persistence | 100% | All runs documented |
| Agent success rate | > 90% | Tasks completed without retry |

---

## File Locations

New agents should be created in:
```
2-engine/agents/definitions/claude-native/
├── orchestrator/
│   └── bb5-master-orchestrator.md
├── research/
│   ├── bb5-stack-researcher.md (exists)
│   ├── bb5-architecture-researcher.md (exists)
│   ├── bb5-convention-researcher.md (exists)
│   ├── bb5-risk-researcher.md (exists)
│   └── bb5-research-synthesizer.md (NEW)
├── planning/
│   ├── bb5-planner.md (exists)
│   ├── bb5-checker.md (exists)
│   ├── bb5-architect.md (exists)
│   └── bb5-dependency-analyzer.md (NEW)
├── execution/
│   ├── bb5-executor.md (exists)
│   ├── bb5-verifier.md (exists)
│   ├── bb5-debugger.md (NEW)
│   └── bb5-integrator.md (NEW)
├── verification/
│   ├── bb5-validator.md (exists)
│   ├── bb5-qa-specialist.md (NEW)
│   └── bb5-security-guard.md (NEW)
├── memory/
│   ├── bb5-scribe.md (NEW)
│   ├── bb5-ghost-of-past.md (NEW)
│   └── bb5-context-persistence.md (NEW)
└── meta/
    ├── bb5-self-evolver.md (NEW)
    └── bb5-meta-agent.md (NEW)
```

---

## Next Steps

1. **Review this proposal** with stakeholders
2. **Prioritize agents** based on current pain points
3. **Create agent templates** for consistent formatting
4. **Implement Phase 1** (Foundation)
5. **Test with pilot workflows**
6. **Iterate based on feedback**

---

## References

- Thin Orchestrator Pattern: `2-engine/agents/definitions/claude-native/workflows/thin-orchestrator.md`
- Planner-Checker Loop: `2-engine/agents/definitions/claude-native/workflows/planner-checker-loop.md`
- Wave Execution: `2-engine/agents/definitions/claude-native/workflows/wave-execution.md`
- External Research: `6-roadmap/_research/external/GitHub/Claude-Code/`
- Agent Registry: `5-project-memory/blackbox5/.autonomous/agents/agent-registry.yaml`
