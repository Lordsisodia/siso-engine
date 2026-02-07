# BlackBox5 Sub-Agent Workflow Reference

**Purpose:** Quick reference for which agent to use, when, and in which workflow.

---

## Agent Quick Reference Table

| Agent | Tier | Primary Workflow | When to Call | Key Output |
|-------|------|------------------|--------------|------------|
| bb5-master-orchestrator | 1 | All | Every user request | Flow selection |
| bb5-architect | 1 | Planning | Architecture questions | Component design |
| bb5-dependency-analyzer | 1 | Planning | Before parallel execution | Wave groups |
| bb5-debugger | 1 | Execution | On failure | Root cause + fix |
| bb5-scribe | 2 | Memory | Continuous | Run documentation |
| bb5-ghost-of-past | 2 | Memory | At decisions | ADR records |
| bb5-performance-profiler | 2 | Verification | Post-implementation | Efficiency report |
| bb5-refactor-scout | 3 | Background | Scheduled/manual | Debt detection |
| bb5-self-evolver | 4 | Meta | Weekly | Improved prompts |

---

## Tier 1: Core Workflow Agents

### bb5-master-orchestrator
```yaml
role: Central coordinator - routes requests to appropriate flows
context_budget: 15% (never does heavy lifting)
triggers:
  - Every user request
  - RALF task queue items
  - Scheduled workflow activation

decision_matrix:
  "research|analyze|understand":
    flows: [research]
    agents: [4-researchers, synthesizer]

  "design|architect|structure|refactor":
    flows: [research, planning]
    agents: [architect, planner, checker, dependency-analyzer]

  "implement|build|create|add":
    flows: [research, planning, execution, verification]
    agents: [all-tier-1]

  "fix|debug|error|broken":
    flows: [execution, verification]
    agents: [executor, debugger, validator]

  "improve|optimize":
    flows: [research, execution, verification]
    agents: [researchers, executor, performance-profiler]

escalation_conditions:
  - Unclear requirements
  - Scope creep detected
  - Context overflow (>85%)
  - Max retries exceeded
  - Safety concerns

output: orchestrator_plan.yaml
```

### bb5-architect (The "Where & Why" Agent)
```yaml
role: Maintains high-level Repo Map and PROJECT_STATE.md
primary_concern: Where files go and why they belong there

triggers:
  - Start of any new feature request
  - "Should we..." questions
  - Multi-file implementation needed
  - Refactoring across modules

workflow: Planning Flow
  position: Before Planner, after Research
  input: research_package.yaml
  output: architecture_design.yaml

responsibilities:
  - Identify which files need modification across modules
  - Prevent breaking changes through structural awareness
  - Create multi-file implementation plan
  - Maintain PROJECT_STATE.md (repo map)
  - Define component boundaries
  - Design interfaces between components

deliverables:
  - component_diagram: "Mermaid or text"
  - file_modifications:
      - path: "src/auth/service.py"
        change_type: "modify"
        reason: "Add JWT validation"
      - path: "src/auth/models.py"
        change_type: "create"
        reason: "New UserSession model"
  - integration_points:
      - from: "auth-service"
        to: "user-service"
        via: "API call"
  - migration_path: "If structural changes needed"

prevents: "Tunnel vision - ensures cross-file consistency"
```

### bb5-dependency-analyzer
```yaml
role: Ensures parallel sub-agents don't conflict
primary_concern: Task ordering and conflict detection

triggers:
  - Planning phase completion
  - Before wave execution
  - When adding parallel tasks
  - Before major merge

workflow: Planning Flow
  position: After Planner-Checker loop
  input: validated_plan.yaml
  output: wave_groups.yaml

algorithm:
  1. Parse all task dependencies
  2. Build directed acyclic graph (DAG)
  3. Detect cycles (fail if found)
  4. Topological sort
  5. Group into waves by depth
  6. Calculate critical path
  7. Identify cross-dependencies

detects:
  - backend_change_requires_frontend_update
  - database_schema_requires_migration
  - api_change_breaks_clients
  - shared_resource_conflicts

output_format:
  wave_groups:
    wave_0: ["T-001", "T-002"]  # No dependencies
    wave_1: ["T-003", "T-004"]  # Depends on wave_0
    wave_2: ["T-005"]           # Depends on wave_1

  critical_path: ["T-001", "T-003", "T-005"]
  estimated_duration: "45 minutes"

  warnings:
    - task: "T-004"
      warning: "Modifies shared resource with T-003"
      recommendation: "Add coordination lock"

prevents: "Parallel execution conflicts"
```

### bb5-debugger
```yaml
role: Root cause analysis when things fail
primary_concern: Why did it break and how to fix it

triggers:
  - Verification failure
  - Test suite failure
  - Build failure
  - Runtime error
  - Wave execution failure

workflow: Execution Flow
  position: On failure, before retry
  input: failure_context.yaml
  output: debug_report.yaml

process:
  1. Gather error logs and stack traces
  2. Form hypotheses about root cause
  3. Test hypotheses systematically
  4. Document evidence trail
  5. Propose fix strategy
  6. Recommend retry or escalate

erotetic_check: |
  Before debugging, frame E(X,Q):
  - X = [the failing component/behavior]
  - Q = [questions that must be answered]
    - What changed?
    - What was expected?
    - What actually happened?
    - What's different from working cases?

output_format:
  root_cause: "Specific technical reason"
  evidence:
    - type: "log"
      source: "test_output.log:45"
      content: "..."
  fix_strategy:
    approach: "Specific fix"
    confidence: 85
    estimated_effort: "PT30M"
  recommendation: "retry" | "escalate" | "abort"

prevents: "Endless retry loops without understanding"
```

---

## Tier 2: Memory & Context Agents

### bb5-scribe (The "Memory" Agent)
```yaml
role: Transforms transient chat into permanent codebase context
primary_concern: Documenting what we did, why, and what's next

triggers:
  - Continuous during execution
  - On decision points
  - On failures/successes
  - Post-verification
  - Session end

workflow: Memory Flow
  position: Continuous (runs alongside other flows)
  output: Run documentation + STATE updates

responsibilities:
  - Update THOUGHTS.md in run folders
  - Capture DECISIONS.md at decision points
  - Record LEARNINGS.md from outcomes
  - Update TIMELINE with events
  - Maintain ASSUMPTIONS.md
  - Archive completed runs

files_maintained:
  - runs/run-*/THOUGHTS.md      # Thinking process
  - runs/run-*/DECISIONS.md    # Decisions made
  - runs/run-*/LEARNINGS.md    # What worked/didn't
  - runs/run-*/RESULTS.md      # Outcomes
  - runs/run-*/ASSUMPTIONS.md  # Working assumptions

benefit: "Any future agent can read these and understand context"
```

### bb5-ghost-of-past (ADR Maintainer)
```yaml
role: Records WHY decisions were made, not just WHAT
primary_concern: Episodic memory - preventing undoing critical work

triggers:
  - Significant architectural decisions
  - Performance optimizations
  - Trade-off discussions
  - Before any major refactor
  - "Why is it like this?" questions

workflow: Memory Flow
  position: At decision points
  output: decisions/ADR-XXX.md

adr_template:
  status: proposed | accepted | deprecated | superseded
  context: "What is the issue we're seeing?"
  decision: "What are we doing about it?"
  consequences:
    positive: ["..."]
    negative: ["..."]
  alternatives_considered:
    - option: "What we didn't choose"
      reason: "Why we rejected it"
  rationale: "Why this over alternatives"
  trade_offs:
    - dimension: "complexity vs performance"
      chosen: "performance"
      rejected: "simplicity"

intelligence_gain: |
  When you revisit code 6 months later,
  the subagent won't undo a critical performance
  optimization because it has "episodic memory"
  of the original struggle.

example_scenario: |
  Agent wants to simplify complex caching logic.
  Ghost-of-Past shows ADR-042:
    "We accepted complexity for 10x performance gain
     after load testing showed O(n²) was killing us
     at 10k users."
  Result: Agent keeps the complexity, adds better comments.
```

### bb5-performance-profiler
```yaml
role: Efficiency gate - ensures correctness doesn't sacrifice performance
primary_concern: Catching O(n) → O(n²) regressions

triggers:
  - Post-implementation verification
  - Before merge to main
  - Optimization requests
  - Suspicion of performance regression

workflow: Verification Flow
  position: After validator, before QA
  input: code_changes.yaml
  output: performance_report.yaml

analysis:
  - Static analysis (Big-O estimation)
  - Benchmark comparison (if tests exist)
  - Database query analysis
  - Memory usage patterns
  - API response time impact

flags:
  - nested_loop_in_hot_path
  - n_plus_1_queries
  - memory_leak_pattern
  - blocking_io_in_async
  - unnecessary_allocation

output_format:
  overall_grade: "A" | "B" | "C" | "D" | "F"
  issues:
    - severity: "high"
      location: "src/service.py:45"
      issue: "Nested loop turns O(n) into O(n²)"
      suggestion: "Use hash map for lookup"
  benchmarks:
    before: "120ms"
    after: "145ms"
    delta: "+21%"
    acceptable: false

prevents: "Death by a thousand cuts performance degradation"
```

---

## Tier 3: Background & Specialized Agents

### bb5-refactor-scout
```yaml
role: Technical debt detection across codebase
primary_concern: Finding duplicated logic and "smelly" code

triggers:
  - Scheduled (weekly)
  - Manual: ai scout --refactor
  - Pre-major-release
  - Codebase health check

workflow: Background (independent)
  schedule: "0 0 * * 0"  # Weekly on Sunday
  duration: "Background, low priority"

searches_for:
  - duplicated_logic_across_files
  - long_functions (>50 lines)
  - high_cyclomatic_complexity
  - missing_error_handling
  - hardcoded_values
  - TODO_comments_older_than_30_days
  - deprecated_api_usage

output_format:
  debt_items:
    - id: "DEBT-001"
      type: "duplication"
      severity: "medium"
      files: ["src/auth.py:45", "src/utils.py:120"]
      description: "Same validation logic in two places"
      estimated_effort: "PT2H"
      recommendation: "Extract to shared validator"

  summary:
    total_items: 12
    high_severity: 2
    estimated_total_effort: "PT16H"

action: "Creates refactoring tasks in backlog"
```

---

## Tier 4: Meta Agents

### bb5-self-evolver
```yaml
role: Monitors and improves other agents
primary_concern: Your CLI gets smarter the more you use it

triggers:
  - Weekly analysis
  - Repeated agent failures detected
  - User feedback on agent quality
  - Success rate drops below threshold

workflow: Meta (runs independently)
  schedule: "Weekly"
  permissions: "Read-only on agents, Write to proposals/"

process:
  1. Analyze agent success metrics from runs/
  2. Identify failure patterns
  3. Propose prompt improvements
  4. Create A/B test plan
  5. Submit proposal for human approval
  6. If approved: Deploy and monitor

metrics_tracked:
  - task_success_rate per agent
  - retry_count per agent
  - user_escalation_rate
  - completion_time trends
  - error_patterns

improvement_types:
  - add_example_to_prompt
  - clarify_instructions
  - add_tool_to_agent
  - adjust_output_format
  - add_erotetic_check

constraints:
  - Never modifies core orchestrator
  - Requires human approval for all changes
  - Maintains version history
  - Can only propose, not deploy automatically

output: proposals/agent-improvement-XXX.md
```

---

## Workflow Integration Diagrams

### Full Implementation Workflow

```
User Request
    │
    ▼
┌─────────────────┐
│  Orchestrator   │──► Classifies request
│   (15% budget)  │
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    ▼         ▼        ▼        ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Research│ │Planning│ │Execution│ │Verify  │
│  Flow  │ │  Flow  │ │  Flow   │ │  Flow  │
└───┬────┘ └───┬────┘ └────┬───┘ └────┬───┘
    │          │           │          │
    ▼          ▼           ▼          ▼
Synthesis  Architecture  Wave      3-Level
Package    Design       Execution Check
           + Waves
    │          │           │          │
    └──────────┴───────────┴──────────┘
                    │
                    ▼
            ┌──────────────┐
            │ Memory Flow  │──► Continuous
            │  (Scribe)    │    ADR updates
            └──────────────┘
                    │
                    ▼
            ┌──────────────┐
            │   COMPLETE   │
            │   or RETRY   │
            └──────────────┘
```

### When to Call Each Agent (Decision Tree)

```
START: New Request
    │
    ▼
Is it a question about
existing code?
    │
    ├── YES ──► bb5-explorer (deep dive)
    │
    └── NO ──► Is it about architecture/design?
                  │
                  ├── YES ──► bb5-architect
                  │              └── Creates component design
                  │
                  └── NO ──► Is it implementation?
                                │
                                ├── YES ──► Planning Flow
                                │              ├── bb5-planner (creates tasks)
                                │              ├── bb5-checker (validates)
                                │              └── bb5-dependency-analyzer
                                │                     (orders tasks)
                                │
                                └── NO ──► Is something broken?
                                              │
                                              ├── YES ──► bb5-debugger
                                              │              (root cause)
                                              │
                                              └── NO ──► Routine task?
                                                            │
                                                            ├── YES ──► bb5-executor
                                                            │
                                                            └── NO ──► Orchestrator
                                                                           (classify)

DURING any flow:
  - bb5-scribe (continuous documentation)
  - bb5-ghost-of-past (at decisions)

AFTER implementation:
  - bb5-validator (3-level check)
  - bb5-performance-profiler (efficiency)
  - bb5-qa-specialist (regression)

BACKGROUND:
  - bb5-refactor-scout (weekly debt scan)
  - bb5-self-evolver (weekly improvement)
```

---

## Quick Decision Guide

| Situation | Call This Agent | In This Flow |
|-----------|-----------------|--------------|
| "Where should this code go?" | bb5-architect | Planning |
| "Will these parallel tasks conflict?" | bb5-dependency-analyzer | Planning |
| "Why did this fail?" | bb5-debugger | Execution |
| "Document what we did" | bb5-scribe | Memory |
| "Why did we choose this approach?" | bb5-ghost-of-past | Memory |
| "Is this performant?" | bb5-performance-profiler | Verification |
| "Find technical debt" | bb5-refactor-scout | Background |
| "Improve our agents" | bb5-self-evolver | Meta |
| "New feature request" | bb5-master-orchestrator | All flows |
| "Research this topic" | 4-researchers + synthesizer | Research |

---

## Success Metrics per Agent

| Agent | Success Metric | Target |
|-------|---------------|--------|
| architect | Plans without breaking changes | >95% |
| dependency-analyzer | Cycle detection accuracy | 100% |
| debugger | Fix success rate | >80% |
| scribe | Documentation completeness | 100% |
| ghost-of-past | ADR retrieval usefulness | >90% |
| performance-profiler | Regression detection | >85% |
| refactor-scout | True positive rate | >70% |
| self-evolver | Improvement acceptance rate | >60% |

---

## File Locations

```
2-engine/agents/definitions/claude-native/
├── orchestrator/
│   └── bb5-master-orchestrator.md
├── planning/
│   ├── bb5-architect.md
│   └── bb5-dependency-analyzer.md
├── execution/
│   └── bb5-debugger.md
├── memory/
│   ├── bb5-scribe.md
│   └── bb5-ghost-of-past.md
├── verification/
│   └── bb5-performance-profiler.md
├── background/
│   └── bb5-refactor-scout.md
└── meta/
    └── bb5-self-evolver.md
```

---

## Implementation Priority

### Phase 1 (This Week)
1. bb5-architect - Critical for file placement
2. bb5-dependency-analyzer - Prevents conflicts
3. bb5-debugger - Completes thin orchestrator

### Phase 2 (Next Week)
4. bb5-scribe - Memory foundation
5. bb5-ghost-of-past - Prevents regression

### Phase 3 (Following Week)
6. bb5-performance-profiler - Quality gate
7. bb5-refactor-scout - Debt management

### Phase 4 (Later)
8. bb5-self-evolver - Meta improvement

---

## Usage Examples

### Example 1: New Feature Implementation
```
User: "Add user authentication"

Orchestrator: "Implementation request detected"
  → Activates: Research + Planning + Execution + Verification

Research Flow:
  → 4 researchers analyze auth patterns
  → Synthesizer extracts concepts

Planning Flow:
  → Architect: "Auth service goes in src/auth/,
                needs User model, session management"
  → Planner: Creates 8 tasks
  → Checker: Validates plan (score: 92)
  → Dependency-Analyzer: "3 waves needed"

Execution Flow:
  → Wave 0: Setup (sequential)
  → Wave 1: Core implementation (parallel)
  → Wave 2: Integration (sequential)
  → Wave 3: Tests + docs (parallel)

Verification Flow:
  → Validator: 3-level check (score: 88)
  → Performance-Profiler: "No regressions"

Memory Flow:
  → Scribe: Documents entire run
  → Ghost-of-Past: Records why JWT vs sessions
```

### Example 2: Debugging Production Issue
```
User: "Users can't login, getting 500 errors"

Orchestrator: "Bug fix request detected"
  → Activates: Execution + Verification

Execution Flow:
  → Executor: Attempts fix
  → Fails: Tests don't pass
  → Debugger activated

Debugger:
  → Analyzes logs
  → Finds: "NullPointer in auth service"
  → Root cause: "Missing null check after DB update"
  → Fix: "Add validation at line 45"
  → Recommends: retry

Execution Flow (retry):
  → Executor applies fix
  → Success

Verification Flow:
  → Validator: All checks pass
  → QA: Regression tests pass

Memory Flow:
  → Scribe: Documents bug + fix
  → Ghost-of-Past: Records why null check matters
```

---

## Summary

This reference provides:
- **9 core agents** across 4 tiers
- **5 workflows** with clear handoffs
- **Decision trees** for when to use each agent
- **File locations** for implementation
- **Success metrics** for validation

All agents serve specific purposes in specific workflows, preventing the "tunnel vision" problem while maintaining system coherence.
