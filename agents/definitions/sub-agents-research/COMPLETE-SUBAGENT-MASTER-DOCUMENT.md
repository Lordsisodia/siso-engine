# BlackBox5 Complete Sub-Agent & Workflow Master Document

**Version:** 1.0
**Date:** 2026-02-07
**Purpose:** Single source of truth for ALL sub-agents and workflows in BlackBox5

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [All Sub-Agents Inventory](#all-sub-agents-inventory)
3. [All Workflows Inventory](#all-workflows-inventory)
4. [Agent-to-Workflow Mapping](#agent-to-workflow-mapping)
5. [Implementation Priority](#implementation-priority)

---

## Executive Summary

**Total Agents Identified:** 60+
**Total Workflows Identified:** 15+
**Categories:** Core, Memory, Quality, Specialized, Meta

This document consolidates:
- 9 Superintelligence Protocol sub-agents
- 8 Claude-native agents (GSD pattern)
- 17 Domain specialists
- 3 Core Python agents (Mary, Alex, Amelia)
- 6 Six-Agent RALF pipeline agents
- 60+ External GitHub agents (patterns adapted)
- 15+ Workflows (core + specialized)

---

## All Sub-Agents Inventory

### Category 1: Superintelligence Protocol (9 agents)

| # | Agent | Purpose | When to Call | Workflow |
|---|-------|---------|--------------|----------|
| 1 | **context-scout** | Deep reconnaissance of BB5 state | Task start, architecture, debugging | Superintelligence Protocol Step 1 |
| 2 | **first-principles** | Break problems to fundamentals | Complex tasks, novel problems, low confidence | Superintelligence Protocol Step 2 |
| 3 | **research-agent** | External research | Best practices, technology evaluation | Superintelligence Protocol Step 3 |
| 4 | **architect** | Design structural improvements | After context + first principles | Superintelligence Protocol Step 4 |
| 5 | **planner** | Create actionable plans | After architecture design | Superintelligence Protocol Step 5 |
| 6 | **validator** | Verify work meets requirements | Task completion, pre-commit | Superintelligence Protocol Step 6 |
| 7 | **bookkeeper** | Maintain organizational hygiene | Task milestones, completion | Superintelligence Protocol Step 7 |
| 8 | **concept-analyzer** | Map and track concepts | New concepts, refactoring | Conceptual architecture |
| 9 | **documentation-agent** | Maintain documentation | Documentation tasks | Documentation maintenance |

### Category 2: Claude-Native GSD Agents (8 agents)

| # | Agent | Purpose | When to Call | Workflow |
|---|-------|---------|--------------|----------|
| 10 | **bb5-stack-researcher** | Tech stack research | Start of implementation | Thin Orchestrator Stage 1 |
| 11 | **bb5-architecture-researcher** | System design patterns | Start of implementation | Thin Orchestrator Stage 1 |
| 12 | **bb5-convention-researcher** | Coding standards | Start of implementation | Thin Orchestrator Stage 1 |
| 13 | **bb5-risk-researcher** | Pitfalls and risks | Start of implementation | Thin Orchestrator Stage 1 |
| 14 | **bb5-planner** | Create implementation plans | After research | Thin Orchestrator Stage 2 |
| 15 | **bb5-checker** | Validate plans (7 dimensions) | After planning | Thin Orchestrator Stage 2 |
| 16 | **bb5-executor** | Fresh context execution | After planning approval | Thin Orchestrator Stage 3 |
| 17 | **bb5-verifier** | 10-step verification | After execution | Thin Orchestrator Stage 4 |

### Category 3: Core Python Agents (3 agents)

| # | Agent | Name | Purpose | When to Call |
|---|-------|------|---------|--------------|
| 18 | **AnalystAgent** | Mary | Research, data analysis | Analysis tasks |
| 19 | **ArchitectAgent** | Alex | System architecture | Design decisions |
| 20 | **DeveloperAgent** | Amelia | Code implementation | Development tasks |

### Category 4: Domain Specialists (18 agents)

| # | Agent | Purpose | When to Call |
|---|-------|---------|--------------|
| 21 | **accessibility-specialist** | WCAG compliance | Accessibility reviews |
| 22 | **api-specialist** | API design | API development |
| 23 | **backend-specialist** | Server-side dev | Backend work |
| 24 | **compliance-specialist** | Regulatory compliance | Compliance audits |
| 25 | **data-specialist** | ETL, data pipelines | Data engineering |
| 26 | **database-specialist** | Schema design | Database work |
| 27 | **devops-specialist** | CI/CD, infrastructure | DevOps tasks |
| 28 | **documentation-specialist** | Technical writing | Documentation |
| 29 | **frontend-specialist** | React/Vue/Angular | Frontend work |
| 30 | **integration-specialist** | Third-party APIs | Integration work |
| 31 | **ml-specialist** | Machine learning | ML tasks |
| 32 | **mobile-specialist** | iOS/Android | Mobile development |
| 33 | **monitoring-specialist** | Observability | Monitoring setup |
| 34 | **performance-specialist** | Optimization | Performance work |
| 35 | **research-specialist** | Investigation | Research tasks |
| 36 | **security-specialist** | Security architecture | Security reviews |
| 37 | **testing-specialist** | QA strategy | Testing work |
| 38 | **ui-ux-specialist** | Design systems | UI/UX work |

### Category 5: Six-Agent RALF Pipeline (6 agents)

| # | Agent | Purpose | When to Call |
|---|-------|---------|--------------|
| 39 | **Deep Repo Scout** | 3-loop repo analysis | GitHub repo discovery |
| 40 | **Scout Validator** | Approve/reject scout output | Scout completion |
| 41 | **Integration Analyzer** | Assess integration value | Scout validation |
| 42 | **Analyzer Validator** | Verify scoring | Analysis completion |
| 43 | **Implementation Planner** | Create executable tasks | Analysis validation |
| 44 | **Planner Validator** | Verify plans | Planning completion |

### Category 6: BMAD Framework (4 modules)

| # | Module | Purpose | When to Call |
|---|--------|---------|--------------|
| 45 | **BusinessAnalysis** | Goals, users, value | BMAD workflow start |
| 46 | **ModelDesign** | Entities, relationships | After business analysis |
| 47 | **ArchitectureDesign** | Components, interfaces | After model design |
| 48 | **DevelopmentPlan** | Phases, tasks, estimates | Final BMAD phase |

### Category 7: New Proposed Agents (12 agents)

| # | Agent | Purpose | When to Call | Workflow |
|---|-------|---------|--------------|----------|
| 49 | **bb5-master-orchestrator** | Route to appropriate flows | Every request | All flows |
| 50 | **bb5-research-synthesizer** | Merge 4 researcher outputs | After research | Research Flow |
| 51 | **bb5-dependency-analyzer** | Detect parallel conflicts | Planning phase | Planning Flow |
| 52 | **bb5-debugger** | Root cause analysis | On failure | Execution Flow |
| 53 | **bb5-integrator** | Merge parallel results | After waves | Execution Flow |
| 54 | **bb5-scribe** | Run documentation | Continuous | Memory Flow |
| 55 | **bb5-ghost-of-past** | ADR maintenance | At decisions | Memory Flow |
| 56 | **bb5-performance-profiler** | Efficiency gates | Post-implementation | Verification Flow |
| 57 | **bb5-refactor-scout** | Technical debt detection | Weekly/scheduled | Background |
| 58 | **bb5-self-evolver** | Improve other agents | Weekly | Meta |
| 59 | **bb5-triage-router** | Classify and route | Entry point | All flows |
| 60 | **bb5-test-writer** | Automated test generation | Post-implementation | Verification Flow |

### Category 8: External GitHub Agents (Patterns to Adapt)

| # | Agent | Source | Purpose | BlackBox5 Fit |
|---|-------|--------|---------|---------------|
| 61 | **kraken** | CCv3 | TDD implementation | bmad-dev |
| 62 | **phoenix** | CCv3 | Refactoring & migration | bmad-architect |
| 63 | **oracle** | CCv3 | External research | web-search |
| 64 | **aegis** | CCv3 | Security analysis | security-reviewer |
| 65 | **sleuth** | CCv3 | Debugging | debug workflow |
| 66 | **arbiter** | CCv3 | Test validation | bmad-qa |
| 67 | **maestro** | CCv3 | Multi-agent coordination | RALF orchestration |
| 68 | **critic** | CCv3 | Code review | code-review |
| 69 | **herald** | CCv3 | Release management | release workflow |
| 70 | **atlas** | CCv3 | E2E testing | E2E workflow |
| 71 | **profiler** | CCv3 | Performance analysis | performance workflow |
| 72 | **chronicler** | CCv3 | Session analysis | memory system |
| 73 | **meta-agent** | Hooks-Mastery | Agent generator | agent creation |

---

## All Workflows Inventory

### Core Workflows (5)

| # | Workflow | Purpose | Key Agents |
|---|----------|---------|------------|
| 1 | **Research Flow** | Gather comprehensive context | 4 researchers → synthesizer |
| 2 | **Planning Flow** | Create validated plans | Architect → Planner → Checker → Dependency Analyzer |
| 3 | **Execution Flow** | Implement with parallelism | Wave orchestrator → Executors → Debugger |
| 4 | **Verification Flow** | Quality gates | Validator → QA → Security |
| 5 | **Memory Flow** | Persist context | Scribe → Ghost-of-Past |

### Advanced Workflows (10+)

| # | Workflow | Purpose | Key Components |
|---|----------|---------|----------------|
| 6 | **Superintelligence Protocol** | 7-step deep analysis | Context Scout → First Principles → Research → Architect → Planner → Validator → Bookkeeper |
| 7 | **PRD-to-Epic-to-Tasks** | Feature breakdown | create-prd → create-epics → create-story → dev-story |
| 8 | **GitHub Analysis Pipeline** | External repo analysis | Scout → Validator → Analyzer → Validator → Planner → Validator |
| 9 | **Managerial Agent Workflow** | Task lifecycle | VibeKanban → TaskLifecycle → TeamDashboard |
| 10 | **BMAD Production Workflow** | 4-phase complete | Business → Model → Architecture → Development |
| 11 | **Adaptive Workflow (4-Tier)** | Complexity-based routing | Tier 1-4 selection |
| 12 | **GSD Framework** | Get-Shit-Done execution | Wave execution + Checkpoints + Atomic commits |
| 13 | **Six-Agent Pipeline** | Worker-Validator pairs | 3 workers + 3 validators |
| 14 | **RALF Loop** | Autonomous improvement | Scout → Analyzer → Planner → Executor |
| 15 | **A/P/C Menu Pattern** | Mode selection | Advanced / Party / Continue |

### Specialized Workflows (10+)

| # | Workflow | Purpose |
|---|----------|---------|
| 16 | **Validation Workflows** | PRD, Architecture, Tests, UX validation |
| 17 | **Edit Workflows** | PRD, Architecture, UX editing |
| 18 | **Planning Workflows** | Sprint planning, Tech spec, Implementation readiness |
| 19 | **Testing Workflows** | Test plan, Test architecture, Run tests, Test review |
| 20 | **Retrospective Workflows** | Epic retrospective, Course correction |
| 21 | **Research Workflows** | Research, Brainstorm, Document project |
| 22 | **WIP Tracking** | Work-in-progress management |
| 23 | **Code Review Workflow** | Systematic code reviews |
| 24 | **Incident Response** | Production issues (proposed) |
| 25 | **Release Management** | Deployment workflow (proposed) |

---

## Agent-to-Workflow Mapping

### Research Flow
```
Entry: User asks "research", "analyze", "understand"

Agents:
  - bb5-stack-researcher (parallel)
  - bb5-architecture-researcher (parallel)
  - bb5-convention-researcher (parallel)
  - bb5-risk-researcher (parallel)
  - bb5-research-synthesizer (after parallel)

Output: research_package.yaml
```

### Planning Flow
```
Entry: User asks "design", "architect", "plan"

Agents:
  - bb5-architect (component design)
  - bb5-planner (task creation)
  - bb5-checker (validation)
  - bb5-dependency-analyzer (wave calculation)

Output: plan_package.yaml with wave_groups
```

### Execution Flow
```
Entry: Plan approved, ready to implement

Agents:
  - Wave Orchestrator (manages waves)
  - bb5-executor (per task)
  - bb5-debugger (on failure)
  - bb5-integrator (merge results)

Output: execution_package.yaml
```

### Verification Flow
```
Entry: Execution complete

Agents:
  - bb5-validator (3-level check)
  - bb5-performance-profiler (efficiency)
  - bb5-qa-specialist (regression)
  - bb5-security-guard (vulnerabilities)

Output: verification_package.yaml
```

### Memory Flow
```
Entry: Continuous (runs alongside all flows)

Agents:
  - bb5-scribe (run documentation)
  - bb5-ghost-of-past (ADR maintenance)
  - bb5-context-persistence (3-tier memory)

Output: Updated STATE.yaml, ADRs, run archives
```

### Superintelligence Protocol
```
Entry: "Activate superintelligence protocol for this"

Agents (sequential):
  1. context-scout (gather data)
  2. first-principles (decompose)
  3. research-agent (external knowledge)
  4. architect (design)
  5. planner (create tasks)
  6. validator (verify)
  7. bookkeeper (maintain state)

Output: Comprehensive analysis + plan
```

---

## Implementation Priority

### Phase 1: Foundation (Critical)
1. **bb5-master-orchestrator** - Entry point for all requests
2. **bb5-debugger** - Completes thin orchestrator
3. **bb5-dependency-analyzer** - Prevents parallel conflicts
4. **bb5-research-synthesizer** - Merges parallel research

### Phase 2: Memory (High Value)
5. **bb5-scribe** - Documentation foundation
6. **bb5-ghost-of-past** - ADR maintenance

### Phase 3: Quality (Important)
7. **bb5-performance-profiler** - Efficiency gates
8. **bb5-test-writer** - Automated tests
9. **bb5-refactor-scout** - Debt detection

### Phase 4: Meta (Advanced)
10. **bb5-self-evolver** - Agent improvement
11. **bb5-triage-router** - Smart routing
12. **bb5-integrator** - Result merging

---

## Quick Reference: When to Call Which Agent

| Situation | Agent | Workflow |
|-----------|-------|----------|
| "Research this topic" | 4 researchers + synthesizer | Research |
| "Where should code go?" | bb5-architect | Planning |
| "Will parallel tasks conflict?" | bb5-dependency-analyzer | Planning |
| "Why did this fail?" | bb5-debugger | Execution |
| "Document what we did" | bb5-scribe | Memory |
| "Why did we choose this?" | bb5-ghost-of-past | Memory |
| "Is this performant?" | bb5-performance-profiler | Verification |
| "Find technical debt" | bb5-refactor-scout | Background |
| "New feature request" | bb5-master-orchestrator | All flows |
| "Complex architecture question" | Superintelligence Protocol | 7-step |
| "Fix this bug" | bb5-debugger + executor | Execution |
| "Review this code" | critic / code-reviewer | Validation |
| "Security audit" | aegis / security-guard | Verification |
| "Release this" | herald | Release |

---

## File Locations

### Existing Agents
```
2-engine/agents/definitions/
├── sub-agents/           # 9 Superintelligence agents
├── claude-native/        # 8 GSD agents
├── core/                 # 3 Python agents
├── specialists/          # 18 YAML specialists
├── bmad/                 # 4 BMAD modules
└── managerial/           # Task lifecycle
```

### New Agents (Proposed)
```
2-engine/agents/definitions/claude-native/
├── orchestrator/
│   └── bb5-master-orchestrator.md
├── research/
│   └── bb5-research-synthesizer.md
├── planning/
│   └── bb5-dependency-analyzer.md
├── execution/
│   ├── bb5-debugger.md
│   └── bb5-integrator.md
├── memory/
│   ├── bb5-scribe.md
│   └── bb5-ghost-of-past.md
├── verification/
│   ├── bb5-performance-profiler.md
│   └── bb5-test-writer.md
├── background/
│   └── bb5-refactor-scout.md
├── meta/
│   ├── bb5-self-evolver.md
│   └── bb5-triage-router.md
```

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Superintelligence Protocol | 9 |
| Claude-Native GSD | 8 |
| Core Python | 3 |
| Domain Specialists | 18 |
| Six-Agent RALF | 6 |
| BMAD Modules | 4 |
| New Proposed | 12 |
| External Patterns | 13+ |
| **Total Agents** | **73+** |
| **Total Workflows** | **25+** |

---

## Next Steps

1. Review this master document
2. Prioritize Phase 1 agents for implementation
3. Create agent templates for consistency
4. Implement orchestrator first (entry point)
5. Test with pilot workflows
6. Iterate based on usage

---

*This document is the single source of truth for BlackBox5 sub-agents and workflows.*
