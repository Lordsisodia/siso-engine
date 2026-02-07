# BlackBox5 Final Lean Agent Catalog

**Version:** 2.0
**Date:** 2026-02-07
**Status:** Cleaned & Prioritized
**Agents:** 28 (down from 73+)
**Philosophy:** Maximum value, minimum redundancy

---

## Executive Summary

After comprehensive analysis of 73+ agents:
- **45+ agents eliminated** (redundant, deprecated, or unused)
- **28 agents kept** (lean, focused, valuable)
- **3 Tiers:** Core (10), Important (10), Specialized (8)

**Key Consolidations:**
- 6 validators → 1 comprehensive validator
- 11 scouts/researchers → 2 unified agents
- 5 planners → 2 focused agents
- 18 specialists → 8 essential specialists

---

## TIER 1: Core Agents (10) - Must Have

These form the backbone. Without these, the system doesn't work.

| # | Agent | Purpose | When to Call | Why Essential |
|---|-------|---------|--------------|---------------|
| 1 | **bb5-master-orchestrator** | Routes requests to workflows | Every request | Single entry point; maintains <15% context |
| 2 | **bb5-triage-router** | Classifies intent, assigns specialists | Complex requests | Prevents orchestrator overload |
| 3 | **bb5-stack-researcher** | Tech stack, dependencies analysis | Planning phase | Foundation for all decisions |
| 4 | **bb5-architecture-researcher** | Patterns, components, conventions | After stack research | Ensures codebase consistency |
| 5 | **bb5-planner** | Creates executable XML task plans | Research complete | Translates research to action |
| 6 | **bb5-dependency-analyzer** | Detects parallel task conflicts | Planning phase | Prevents "merge hell" |
| 7 | **bb5-executor** | Implements tasks with fresh context | Plan approved | The "doer" - writes code |
| 8 | **bb5-validator** | 3-level verification (exist/substantive/wired) | After execution | Quality gate before merge |
| 9 | **bb5-debugger** | Root cause analysis on failures | Execution/verification failure | Prevents retry loops |
| 10 | **bb5-scribe** | Maintains THOUGHTS, DECISIONS, LEARNINGS | Continuous | Transforms chat to context |

### Core Agent Details

#### 1. bb5-master-orchestrator
```yaml
name: bb5-master-orchestrator
role: Central coordinator - routes to appropriate workflows
context_budget: 15%
triggers:
  - Every user request
  - RALF task queue
  - Scheduled workflows

decision_matrix:
  "research|analyze": [research-flow]
  "design|architect": [research-flow, planning-flow]
  "implement|build": [research-flow, planning-flow, execution-flow, verification-flow]
  "fix|debug": [execution-flow, verification-flow]
  "optimize": [research-flow, execution-flow]

escalation:
  - Unclear requirements
  - Context overflow (>85%)
  - Safety concerns
```

#### 2. bb5-triage-router
```yaml
name: bb5-triage-router
role: Classifies intent, routes to best specialist
triggers:
  - Complex requests
  - Unclear which specialist to use
  - Multi-domain requests

classification:
  - frontend-heavy → frontend-specialist
  - backend-heavy → backend-specialist
  - security-critical → security-specialist
  - architecture-question → bb5-architecture-researcher
  - research-needed → bb5-stack-researcher
```

#### 3. bb5-stack-researcher
```yaml
name: bb5-stack-researcher
role: Analyze tech stack, dependencies, key libraries
triggers:
  - New project onboarding
  - Planning phase start
  - Technology evaluation

output:
  primary_language: "python"
  frameworks: ["fastapi", "sqlalchemy"]
  dependencies: [...]
  key_insights: [...]
  risks: [...]
```

#### 4. bb5-architecture-researcher
```yaml
name: bb5-architecture-researcher
role: Discover patterns, components, conventions
triggers:
  - After stack research
  - Architecture questions
  - Refactoring planning

output:
  architectural_pattern: "layered"
  components: [...]
  data_flows: [...]
  conventions:
    naming: "snake_case"
    style: "black + ruff"
```

#### 5. bb5-planner
```yaml
name: bb5-planner
role: Create executable task plans with XML format
triggers:
  - Research complete
  - Architecture defined
  - Ready to implement

input: research_package.yaml
output: plan.xml with:
  - phases
  - tasks with dependencies
  - acceptance_criteria
  - estimated_effort
```

#### 6. bb5-dependency-analyzer
```yaml
name: bb5-dependency-analyzer
role: Build DAG, detect cycles, calculate waves
triggers:
  - After planning
  - Before parallel execution
  - Adding parallel tasks

algorithm:
  1. Parse task dependencies
  2. Build directed acyclic graph
  3. Detect cycles (fail if found)
  4. Topological sort
  5. Group into waves

output: wave_groups.yaml
  wave_0: ["T-001", "T-002"]
  wave_1: ["T-003", "T-004"]
  critical_path: ["T-001", "T-003", "T-005"]
```

#### 7. bb5-executor
```yaml
name: bb5-executor
role: Fresh context task execution
context: 200k tokens, pristine
triggers:
  - Plan approved
  - Task ready

process:
  1. Parse XML task
  2. Read existing files
  3. Implement changes
  4. Verify locally
  5. Atomic commit
  6. Brief status report

output: xml status block
  result: COMPLETE|PARTIAL|BLOCKED
  summary: "One-line summary"
  commit: "abc123"
```

#### 8. bb5-validator
```yaml
name: bb5-validator
role: 3-level artifact verification
merged_from: [validator, bb5-checker, bb5-verifier]
triggers:
  - After execution
  - Pre-commit
  - Quality gate

levels:
  1. existence: "Files exist?"
  2. substantive: "Content is meaningful?"
  3. wired: "Everything connects?"

dimensions:
  - completeness
  - sequencing
  - estimation
  - verifiability
  - dependencies
  - risk_coverage
  - resource_fit

output: validator_report.yaml
  status: PASS|PARTIAL|FAIL
  score: 0-100
  issues: [...]
```

#### 9. bb5-debugger
```yaml
name: bb5-debugger
role: Root cause analysis for failures
triggers:
  - Verification failure
  - Test failure
  - Build failure
  - Runtime error

process:
  1. Gather error logs
  2. Form hypotheses
  3. Test systematically
  4. Document evidence
  5. Propose fix
  6. Recommend retry/escalate

erotetic_check: |
  Frame E(X,Q):
  - X = [failing component]
  - Q = [questions to answer]
```

#### 10. bb5-scribe
```yaml
name: bb5-scribe
role: Documentation and memory persistence
triggers:
  - Continuous during execution
  - Decision points
  - Failures/successes
  - Session end

files_maintained:
  - THOUGHTS.md      # Thinking process
  - DECISIONS.md     # Decisions made
  - LEARNINGS.md     # Outcomes
  - RESULTS.md       # Final results
  - ASSUMPTIONS.md   # Working assumptions

benefit: "Future agents can read and understand context"
```

---

## TIER 2: Important Agents (10) - High Value

Add significant value for specific scenarios.

| # | Agent | Purpose | When to Call |
|---|-------|---------|--------------|
| 11 | **bb5-research-synthesizer** | Merge parallel researcher outputs | After research phase |
| 12 | **bb5-integrator** | Merge parallel execution results | After wave execution |
| 13 | **bb5-ghost-of-past** | ADR maintenance (why decisions made) | At significant decisions |
| 14 | **bb5-context-persistence** | 3-tier memory management | Continuous |
| 15 | **bb5-bookkeeper** | Organizational hygiene | Scheduled |
| 16 | **bb5-risk-researcher** | Security risks, pitfalls | Research phase |
| 17 | **bb5-convention-researcher** | Code style, standards | Research phase |
| 18 | **bb5-qa-specialist** | Regression testing | Post-validation |
| 19 | **bb5-security-guard** | Vulnerability scanning | Pre-merge |
| 20 | **bb5-performance-profiler** | Efficiency analysis | Post-implementation |

### Important Agent Details

#### 11. bb5-research-synthesizer
```yaml
name: bb5-research-synthesizer
role: Merge outputs from 4 parallel researchers
triggers:
  - After parallel research
  - Conflicting findings
  - Gap identification

input: [stack_research, arch_research, convention_research, risk_research]
output: research_package.yaml
  - merged_findings
  - extracted_concepts
  - conflicts_resolved
  - gaps_identified
```

#### 12. bb5-integrator
```yaml
name: bb5-integrator
role: Merge results from parallel task execution
triggers:
  - After wave execution
  - Parallel task conflicts
  - Cross-task dependencies

process:
  1. Collect task outputs
  2. Detect conflicts
  3. Resolve merges
  4. Verify integration
```

#### 13. bb5-ghost-of-past
```yaml
name: bb5-ghost-of-past
role: Maintain ADRs (Architecture Decision Records)
triggers:
  - Significant architectural decisions
  - Performance optimizations
  - Trade-off discussions

adr_template:
  context: "What is the issue?"
  decision: "What are we doing?"
  consequences: {positive: [...], negative: [...]}
  alternatives: [...]
  rationale: "Why this choice?"

intelligence_gain: |
  Prevents future agents from undoing
  critical optimizations because they
  have "episodic memory" of why
```

#### 14. bb5-context-persistence
```yaml
name: bb5-context-persistence
role: 3-tier memory management
triggers:
  - Continuous
  - Session transitions

layers:
  short_term:   # Run folders, WIP files
  medium_term:  # STATE.yaml, plans, timeline
  long_term:    # Brain, embeddings, ADRs
```

#### 15. bb5-bookkeeper
```yaml
name: bb5-bookkeeper
role: Track organizational hygiene
triggers:
  - Scheduled (weekly)
  - Task milestones
  - Project events

tasks:
  - Update STATE.yaml
  - Archive completed runs
  - Clean up temp files
  - Update metrics
```

#### 16. bb5-risk-researcher
```yaml
name: bb5-risk-researcher
role: Identify security risks, pitfalls, anti-patterns
triggers:
  - Research phase
  - Security-critical features
  - Pre-merge review

output:
  risks: [...]
  anti_patterns: [...]
  edge_cases: [...]
  mitigation_strategies: [...]
```

#### 17. bb5-convention-researcher
```yaml
name: bb5-convention-researcher
role: Discover code style, standards, practices
triggers:
  - Research phase
  - New codebase onboarding
  - Convention questions

output:
  naming_conventions: {...}
  code_style: "black + ruff"
  organization: "src/..."
  documentation_standards: [...]
```

#### 18. bb5-qa-specialist
```yaml
name: bb5-qa-specialist
role: Regression testing, test generation
triggers:
  - Post-validation
  - Pre-merge
  - Release preparation

tasks:
  - Run test suite
  - Check coverage
  - Generate missing tests
  - Verify no regressions
```

#### 19. bb5-security-guard
```yaml
name: bb5-security-guard
role: Vulnerability scanning, OWASP compliance
triggers:
  - Pre-merge
  - Security audits
  - Auth/payment code changes

checks:
  - OWASP Top 10
  - Secrets exposure
  - Injection vulnerabilities
  - Insecure dependencies
```

#### 20. bb5-performance-profiler
```yaml
name: bb5-performance-profiler
role: Efficiency analysis, Big-O detection
triggers:
  - Post-implementation
  - Optimization requests
  - Suspicion of regression

analysis:
  - Static analysis (Big-O)
  - Benchmark comparison
  - Database query analysis
  - Memory usage patterns
```

---

## TIER 3: Specialized Agents (8) - Domain Experts

Deep expertise for specific domains. Called on-demand.

| # | Agent | Purpose | When to Call |
|---|-------|---------|--------------|
| 21 | **ArchitectAgent** | System design, scalability | Architecture questions |
| 22 | **AnalystAgent** | Research, data analysis | Complex research |
| 23 | **DeveloperAgent** | Implementation, debugging | Development tasks |
| 24 | **frontend-specialist** | React/Vue/Angular | Frontend-heavy work |
| 25 | **backend-specialist** | APIs, microservices | Backend-heavy work |
| 26 | **api-specialist** | API design, integration | API development |
| 27 | **database-specialist** | Schema, queries, migrations | Database work |
| 28 | **testing-specialist** | Test strategy, coverage | Complex testing |

### Specialist Details

#### 21. ArchitectAgent (Alex)
```yaml
name: ArchitectAgent
class: Python agent with ClaudeCodeAgentMixin
capabilities:
  - architecture
  - design_patterns
  - system_design
  - scalability
  - security_design
when_to_call: Architecture decisions, system design
```

#### 22. AnalystAgent (Mary)
```yaml
name: AnalystAgent
class: Python agent with ClaudeCodeAgentMixin
capabilities:
  - research
  - data_analysis
  - competitive_analysis
  - market_research
when_to_call: Research tasks, analysis
```

#### 23. DeveloperAgent (Amelia)
```yaml
name: DeveloperAgent
class: Python agent with ClaudeCodeAgentMixin
capabilities:
  - coding
  - implementation
  - debugging
  - code_review
  - testing
when_to_call: Development tasks
```

#### 24-28. Domain Specialists
```yaml
frontend-specialist:
  focus: React, Vue, Angular, UI components
  when: Frontend-heavy tasks

backend-specialist:
  focus: APIs, microservices, server logic
  when: Backend-heavy tasks

api-specialist:
  focus: REST, GraphQL, API design
  when: API development

database-specialist:
  focus: Schema design, optimization, migrations
  when: Database work

testing-specialist:
  focus: Test strategy, TDD, coverage
  when: Complex testing needs
```

---

## Agents Eliminated (45+)

### Merged into bb5-validator
- validator (Superintelligence)
- bb5-checker
- bb5-verifier
- Scout Validator (Six-Agent Pipeline)
- Analyzer Validator (Six-Agent Pipeline)
- Planner Validator (Six-Agent Pipeline)

### Merged into context-scout
- bb5-stack-researcher (as mode)
- bb5-architecture-researcher (as mode)
- bb5-convention-researcher (as mode)
- bb5-risk-researcher (as mode)
- Intelligent Scout
- Improvement Scout

### Deprecated (Unused/Overlapping)
- Deep Repo Scout (Six-Agent Pipeline)
- Integration Analyzer (Six-Agent Pipeline)
- Implementation Planner (Six-Agent Pipeline)
- AnalystAgent class (use AnalystAgent)
- ArchitectAgent class (use ArchitectAgent)
- DeveloperAgent class (use DeveloperAgent)
- research-specialist YAML
- documentation-specialist (use bb5-scribe)
- compliance-specialist (use security-specialist)
- accessibility-specialist (use frontend-specialist)
- ui-ux-specialist (use frontend-specialist)
- performance-specialist (use ArchitectAgent)
- monitoring-specialist (use bb5-bookkeeper)
- devops-specialist (use backend-specialist)
- integration-specialist (use backend-specialist)
- data-specialist (use AnalystAgent)
- ml-specialist (use DeveloperAgent)
- mobile-specialist (use frontend-specialist)

### External Patterns (Not Implemented)
- kraken, phoenix, oracle, aegis, sleuth, arbiter
- maestro, critic, herald, atlas, profiler, chronicler
- meta-agent (from Hooks-Mastery)

---

## Workflow Coverage

| Workflow | Primary Agents | Supporting Agents |
|----------|----------------|-------------------|
| **Research** | bb5-stack-researcher, bb5-architecture-researcher | bb5-research-synthesizer, bb5-risk-researcher, bb5-convention-researcher |
| **Planning** | bb5-planner, bb5-dependency-analyzer | ArchitectAgent |
| **Execution** | bb5-executor | bb5-debugger, bb5-integrator |
| **Verification** | bb5-validator | bb5-qa-specialist, bb5-security-guard, bb5-performance-profiler |
| **Memory** | bb5-scribe, bb5-ghost-of-past | bb5-context-persistence, bb5-bookkeeper |
| **Routing** | bb5-master-orchestrator, bb5-triage-router | - |
| **Specialized** | Domain specialists (8) | AnalystAgent, ArchitectAgent, DeveloperAgent |

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2) - CRITICAL
1. bb5-master-orchestrator
2. bb5-triage-router
3. bb5-stack-researcher
4. bb5-planner
5. bb5-executor

### Phase 2: Quality (Week 3-4) - HIGH PRIORITY
6. bb5-validator (merge existing validators)
7. bb5-debugger
8. bb5-scribe
9. bb5-dependency-analyzer

### Phase 3: Intelligence (Week 5-6) - IMPORTANT
10. bb5-research-synthesizer
11. bb5-architecture-researcher
12. bb5-ghost-of-past
13. bb5-integrator

### Phase 4: Polish (Week 7-8) - NICE TO HAVE
14. bb5-qa-specialist
15. bb5-security-guard
16. bb5-performance-profiler
17. Remaining specialists

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Total agents | 28 (from 73+) |
| Agent overlap | <5% |
| Time to route | <1s |
| Plan quality | >85% |
| First-pass verification | >80% |
| Memory persistence | 100% |

---

## Quick Reference: When to Call

| Situation | Agent |
|-----------|-------|
| New request | bb5-master-orchestrator |
| Unclear routing | bb5-triage-router |
| Research needed | bb5-stack-researcher + bb5-architecture-researcher |
| Create plan | bb5-planner |
| Check conflicts | bb5-dependency-analyzer |
| Implement | bb5-executor |
| Verify | bb5-validator |
| Debug | bb5-debugger |
| Document | bb5-scribe |
| Why this decision? | bb5-ghost-of-past |
| Architecture question | ArchitectAgent |
| Frontend work | frontend-specialist |
| Backend work | backend-specialist |
| Security audit | bb5-security-guard |

---

## File Locations

### Existing (Keep)
```
2-engine/agents/definitions/
├── core/
│   ├── ArchitectAgent.py
│   ├── AnalystAgent.py
│   └── DeveloperAgent.py
├── specialists/
│   ├── frontend-specialist.yaml
│   ├── backend-specialist.yaml
│   ├── api-specialist.yaml
│   ├── database-specialist.yaml
│   └── testing-specialist.yaml
└── claude-native/
    ├── researchers/
    │   ├── bb5-stack-researcher.md
    │   └── bb5-architecture-researcher.md
    ├── planner/
    │   └── bb5-planner.md
    └── execution/
        └── bb5-executor.md
```

### New (Create)
```
2-engine/agents/definitions/claude-native/
├── orchestrator/
│   ├── bb5-master-orchestrator.md
│   └── bb5-triage-router.md
├── research/
│   ├── bb5-research-synthesizer.md
│   ├── bb5-risk-researcher.md
│   └── bb5-convention-researcher.md
├── planning/
│   └── bb5-dependency-analyzer.md
├── execution/
│   ├── bb5-debugger.md
│   └── bb5-integrator.md
├── verification/
│   ├── bb5-validator.md (merged)
│   ├── bb5-qa-specialist.md
│   ├── bb5-security-guard.md
│   └── bb5-performance-profiler.md
├── memory/
│   ├── bb5-scribe.md
│   ├── bb5-ghost-of-past.md
│   ├── bb5-context-persistence.md
│   └── bb5-bookkeeper.md
```

---

## Summary

**28 agents. Clear responsibilities. No redundancy. Maximum value.**

This lean catalog provides:
- Complete workflow coverage
- Clear agent boundaries
- No overlapping responsibilities
- Maintainable architecture
- Scalable design

Ready for implementation.
