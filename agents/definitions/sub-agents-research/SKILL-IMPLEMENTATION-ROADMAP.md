# BlackBox5 Skill Implementation Roadmap

**Date:** 2026-02-08
**Purpose:** Curated list of skills to implement for Claude upload
**Based on:** 28-agent catalog analysis + existing skills audit

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Existing Skills | 27 SKILL.md files |
| Existing Registry | 23 skills |
| Skill Invocation Rate | 0% (critical gap) |
| Missing Skills Identified | 20 |
| **Skills to Implement (Priority)** | **12** |

**Key Insight:** Skills provide in-context guidance (no token cost), Agents provide isolated execution (token cost). The 28-agent system needs 12 new skills for optimal workflow coverage.

---

## Skills vs Agents: The Critical Distinction

| Aspect | **Skills** | **Agents** |
|--------|------------|------------|
| **Context** | In-context guidance (loaded into main context) | Isolated execution (separate context window) |
| **Token Cost** | No extra cost (part of main context) | Costs tokens (separate context) |
| **Purpose** | Provide expertise/frameworks/patterns | Execute tasks independently |
| **Invocation** | Keyword/pattern triggered via rules | Explicitly spawned via Task tool |
| **Best For** | Guidance, decision-making, lightweight analysis | Heavy lifting, implementation, verification |

---

## The 28 Agents → Skills Mapping

### Agents That Should Be SKILLS (6)
These are lightweight enough to run in-context:

| Agent | Skill Name | Why In-Context |
|-------|------------|----------------|
| bb5-stack-researcher | `stack-research` | Short research, guidance-based |
| bb5-architecture-researcher | `architecture-research` | Pattern discovery, conventions lookup |
| bb5-debugger | `debug-workflow` | Problem-solving guidance |
| bb5-scribe | `scribe` | Continuous documentation |
| bb5-dependency-analyzer | `dependency-analysis` | Utility function, quick analysis |
| bb5-convention-researcher | `convention-research` | Code style lookup |

### Agents That Must Remain AGENTS (22)
These need isolated execution for context management:

| Agent | Why Isolated |
|-------|--------------|
| bb5-master-orchestrator | Always running, maintains <15% context |
| bb5-triage-router | Fresh context for classification |
| bb5-planner | Creates complex XML plans |
| bb5-executor | Fresh 200k token context |
| bb5-validator | 3-level verification needs focus |
| bb5-integrator | Merges parallel results |
| bb5-context-persistence | Background memory service |
| bb5-bookkeeper | Scheduled hygiene tasks |
| bb5-security-guard | Security scanning isolation |
| bb5-performance-profiler | Analysis needs dedicated resources |
| bb5-research-synthesizer | Merges 4+ research outputs |
| bb5-ghost-of-past | ADR maintenance with persistence |
| bb5-qa-specialist | Regression testing |
| bb5-risk-researcher | Security analysis |
| ArchitectAgent | Complex architecture decisions |
| AnalystAgent | Deep research |
| DeveloperAgent | Implementation tasks |
| 5 Domain Specialists | Already skill patterns |

---

## Priority 1: CRITICAL (Implement First)

### 1. orchestrator
**Maps to:** bb5-master-orchestrator agent
**Purpose:** Route requests to appropriate workflows
**Triggers:** Every user request, "route", "workflow", "orchestrate"
**Auto-Activation:** ALWAYS (highest priority rule)
**Why Critical:** Single entry point for entire system
**Complexity:** HIGH
**File:** `~/.claude/skills/orchestrator/SKILL.md`

### 2. triage
**Maps to:** bb5-triage-router agent
**Purpose:** Classify intent and assign specialists
**Triggers:** "classify", "route", "assign", "specialist", "complex"
**Auto-Activation:** When complexity > threshold
**Why Critical:** Prevents orchestrator overload
**Complexity:** MEDIUM
**File:** `~/.claude/skills/triage/SKILL.md`

### 3. research-suite
**Maps to:** 4 research agents (stack, architecture, convention, risk)
**Purpose:** Unified research capability with modes
**Triggers:** "research", "analyze stack", "understand codebase", "tech analysis"
**Auto-Activation:** New project, planning phase, "research" keyword
**Why Critical:** Foundation for all decisions
**Complexity:** HIGH
**File:** `~/.claude/skills/research-suite/SKILL.md`

### 4. planner
**Maps to:** bb5-planner agent
**Purpose:** Create executable XML task plans
**Triggers:** "create plan", "plan implementation", "break down", "task plan"
**Auto-Activation:** Research complete, architecture defined
**Why Critical:** Translates research to action
**Complexity:** HIGH
**File:** `~/.claude/skills/planner/SKILL.md`

### 5. dependency-analysis
**Maps to:** bb5-dependency-analyzer agent
**Purpose:** Build DAG, detect cycles, calculate waves
**Triggers:** "parallel execution", "task order", "dependencies", "conflict detection"
**Auto-Activation:** After planning, before parallel execution
**Why Critical:** Prevents "merge hell"
**Complexity:** MEDIUM
**File:** `~/.claude/skills/dependency-analysis/SKILL.md`

### 6. validator
**Maps to:** bb5-validator agent
**Purpose:** 3-level verification (existence/substantive/wired)
**Triggers:** "validate", "verify", "check", "quality gate", "pre-merge"
**Auto-Activation:** After execution, pre-commit
**Why Critical:** Quality gate before merge
**Complexity:** HIGH
**File:** `~/.claude/skills/validator/SKILL.md`

### 7. debug-workflow
**Maps to:** bb5-debugger agent
**Purpose:** Root cause analysis for failures
**Triggers:** "debug", "fix failure", "error analysis", "why failed"
**Auto-Activation:** Verification failure, test failure, build failure
**Why Critical:** Prevents endless retry loops
**Complexity:** MEDIUM
**File:** `~/.claude/skills/debug-workflow/SKILL.md`

---

## Priority 2: HIGH VALUE (Implement Next)

### 8. scribe
**Maps to:** bb5-scribe agent
**Purpose:** Transform chat into permanent context (THOUGHTS, DECISIONS, LEARNINGS)
**Triggers:** "document", "record", "capture", "scribe"
**Auto-Activation:** Continuous during execution, decision points, session end
**Why High Value:** Memory persistence across sessions
**Complexity:** MEDIUM
**File:** `~/.claude/skills/scribe/SKILL.md`

### 9. adr-management
**Maps to:** bb5-ghost-of-past agent
**Purpose:** Maintain Architecture Decision Records
**Triggers:** "why this decision", "ADR", "decision record", "rationale"
**Auto-Activation:** Significant decisions, before major refactor
**Why High Value:** Prevents undoing critical optimizations
**Complexity:** LOW
**File:** `~/.claude/skills/adr-management/SKILL.md`

### 10. security-audit
**Maps to:** bb5-security-guard agent
**Purpose:** Vulnerability scanning and OWASP compliance
**Triggers:** "security check", "vulnerability scan", "OWASP", "security audit"
**Auto-Activation:** Pre-merge, auth/payment code changes
**Why High Value:** Security gate
**Complexity:** MEDIUM
**File:** `~/.claude/skills/security-audit/SKILL.md`

### 11. performance-analysis
**Maps to:** bb5-performance-profiler agent
**Purpose:** Efficiency analysis and Big-O detection
**Triggers:** "performance check", "optimize", "efficiency analysis", "Big-O"
**Auto-Activation:** Post-implementation, before merge
**Why High Value:** Catches regressions
**Complexity:** MEDIUM
**File:** `~/.claude/skills/performance-analysis/SKILL.md`

---

## Priority 3: IMPORTANT (Implement Later)

### 12. workflow-engine
**Maps to:** Workflow execution layer
**Purpose:** Manage workflow execution across 5 flows
**Triggers:** "run workflow", "execute flow", "workflow step"
**Auto-Activation:** Orchestrator flow selection
**Why Important:** Coordinates multi-step workflows
**Complexity:** HIGH
**File:** `~/.claude/skills/workflow-engine/SKILL.md`

---

## Skills NOT to Create (Already Exist)

| Skill Needed | Existing Skill | Location |
|--------------|----------------|----------|
| bmad-pm | `bmad-pm` | ~/.claude/skills/bmad-pm/ |
| bmad-architect | `bmad-architect` | ~/.claude/skills/bmad-architect/ |
| bmad-dev | `bmad-dev` | ~/.claude/skills/bmad-dev/ |
| bmad-analyst | `bmad-analyst` | ~/.claude/skills/bmad-analyst/ |
| bmad-qa | `bmad-qa` | ~/.claude/skills/bmad-qa/ |
| superintelligence | `superintelligence-protocol` | ~/.claude/skills/superintelligence-protocol/ |
| web-search | `web-search` | ~/.claude/skills/web-search/ |
| codebase-navigation | `codebase-navigation` | ~/.claude/skills/codebase-navigation/ |

---

## Implementation Order

### Phase 1: Foundation (Week 1)
1. `orchestrator` - Entry point
2. `triage` - Classification
3. `research-suite` - Research foundation

### Phase 2: Planning (Week 2)
4. `planner` - Task creation
5. `dependency-analysis` - Conflict prevention

### Phase 3: Quality (Week 3)
6. `validator` - Verification
7. `debug-workflow` - Failure analysis

### Phase 4: Memory (Week 4)
8. `scribe` - Documentation
9. `adr-management` - Decision records

### Phase 5: Gates (Week 5)
10. `security-audit` - Security
11. `performance-analysis` - Performance

### Phase 6: Coordination (Week 6)
12. `workflow-engine` - Flow management

---

## File Structure

```
~/.claude/skills/
├── orchestrator/
│   └── SKILL.md          # NEW - Priority 1
├── triage/
│   └── SKILL.md          # NEW - Priority 1
├── research-suite/
│   └── SKILL.md          # NEW - Priority 1
├── planner/
│   └── SKILL.md          # NEW - Priority 1
├── dependency-analysis/
│   └── SKILL.md          # NEW - Priority 1
├── validator/
│   └── SKILL.md          # NEW - Priority 1
├── debug-workflow/
│   └── SKILL.md          # NEW - Priority 1
├── scribe/
│   └── SKILL.md          # NEW - Priority 2
├── adr-management/
│   └── SKILL.md          # NEW - Priority 2
├── security-audit/
│   └── SKILL.md          # NEW - Priority 2
├── performance-analysis/
│   └── SKILL.md          # NEW - Priority 2
├── workflow-engine/
│   └── SKILL.md          # NEW - Priority 3
│
├── bmad-pm/              # EXISTING
├── bmad-architect/       # EXISTING
├── bmad-dev/             # EXISTING
├── bmad-analyst/         # EXISTING
├── bmad-qa/              # EXISTING
├── bmad-tea/             # EXISTING
├── bmad-sm/              # EXISTING
├── bmad-ux/              # EXISTING
├── bmad-quick-flow/      # EXISTING
├── superintelligence-protocol/  # EXISTING
├── web-search/           # EXISTING
├── codebase-navigation/  # EXISTING
└── [15 more existing skills...]
```

---

## Auto-Activation Rules to Create

Create these rule files in `~/.blackbox5/5-project-memory/blackbox5/.claude/rules/`:

### 009-orchestrator-auto-activation.md
```yaml
---
name: Orchestrator Auto-Activation
trigger:
  - all_requests
alwaysApply: true
priority: 100
---
Always active - routes all requests to appropriate workflows.
```

### 010-triage-auto-activation.md
```yaml
---
name: Triage Auto-Activation
trigger:
  - "complex"
  - "multi-domain"
  - "unclear"
  - "which specialist"
alwaysApply: false
priority: 95
---
Activate when request complexity exceeds threshold.
```

### 011-research-auto-activation.md
```yaml
---
name: Research Auto-Activation
trigger:
  - "research"
  - "analyze stack"
  - "understand codebase"
  - "tech analysis"
alwaysApply: false
priority: 90
---
Activate for research and analysis tasks.
```

[Additional rules for planner, validator, debug, etc.]

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Skills implemented | 12 |
| Auto-activation rules | 12 |
| Skill invocation rate | >50% |
| Agent escalation rate | <20% |
| Workflow coverage | 100% |

---

## Next Steps

1. **Create skill directories** for all 12 new skills
2. **Write SKILL.md files** following the template
3. **Create auto-activation rules** for each skill
4. **Update skill registry** with new entries
5. **Test activation** with sample prompts
6. **Upload to Claude** via skills interface

---

**Ready for implementation.**
