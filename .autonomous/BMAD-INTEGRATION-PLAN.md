# BMAD Integration Plan for Blackbox5

## Overview

This document outlines how to reverse-engineer and integrate BMAD (Breakthrough Method for Agile AI Driven Development) into Blackbox5's .autonomous system.

## BMAD Architecture Analysis

### Core Components

| BMAD Component | Purpose | Blackbox5 Equivalent |
|----------------|---------|---------------------|
| BMM (Core) | 34+ workflows across 4 phases | `prompts/workflows/` |
| BMB (Builder) | Create custom agents/workflows | `prompt-progression/versions/` |
| TEA (Testing) | Risk-based test strategy | `skills/testing/` |
| Agents (21) | Specialized personas | `agents/` |
| Workflows | Guided execution paths | `workflows/` |
| Party Mode | Multi-agent sessions | Sub-agent spawning |

### BMAD Directory Structure

```
BMAD-METHOD/
├── src/
│   └── modules/
│       ├── bmm/          # Core framework
│       ├── bmb/          # Builder module
│       ├── tea/          # Test architect
│       └── ...           # Other modules
├── docs/                 # Documentation
├── test/                 # Tests
└── tools/                # Dev tools
```

## Integration Strategy

### Phase 1: Core BMAD Structure (Immediate)

Create parallel structure in `.autonomous/`:

```
2-engine/.autonomous/
├── bmad/                      # NEW: BMAD integration
│   ├── modules/               # BMAD modules
│   │   ├── core/              # BMM equivalent
│   │   ├── builder/           # BMB equivalent
│   │   └── testing/           # TEA equivalent
│   ├── workflows/             # All workflows
│   │   ├── quick-flow/        # Simple path
│   │   └── full-method/       # Complete method
│   ├── agents/                # 21 specialized agents
│   └── party-mode/            # Multi-agent sessions
├── prompts/                   # EXISTING
├── skills/                    # EXISTING
└── shell/                     # EXISTING
```

### Phase 2: Workflow Migration (Week 1)

Map BMAD workflows to Blackbox5:

| BMAD Workflow | Blackbox5 Implementation | Status |
|--------------|-------------------------|--------|
| `/quick-spec` | `bmad/workflows/quick-flow/01-spec.md` | TODO |
| `/dev-story` | `bmad/workflows/quick-flow/02-dev.md` | TODO |
| `/code-review` | `bmad/workflows/quick-flow/03-review.md` | TODO |
| `/product-brief` | `bmad/workflows/full-method/01-brief.md` | TODO |
| `/create-prd` | `bmad/workflows/full-method/02-prd.md` | TODO |
| `/create-architecture` | `bmad/workflows/full-method/03-arch.md` | TODO |
| `/create-epics-and-stories` | `bmad/workflows/full-method/04-epics.md` | TODO |
| `/sprint-planning` | `bmad/workflows/full-method/05-sprint.md` | TODO |
| `/create-story` | `bmad/workflows/full-method/06-story.md` | TODO |

### Phase 3: Agent Migration (Week 2)

Create 21 BMAD agents in `bmad/agents/`:

**Core Agents:**
1. `product-manager.md` - PM persona
2. `architect.md` - Technical architect
3. `developer.md` - Implementation
4. `ux-designer.md` - UX/UI
5. `scrum-master.md` - Process facilitator
6. `qa-engineer.md` - Quality (Quinn)
7. `test-architect.md` - Test strategy (TEA)

**Specialized Agents:**
8. `security-expert.md` - Security reviews
9. `performance-engineer.md` - Optimization
10. `devops-engineer.md` - CI/CD, infrastructure
11. `data-engineer.md` - Data pipelines
12. `ml-engineer.md` - Machine learning
13. `frontend-developer.md` - UI implementation
14. `backend-developer.md` - API implementation
15. `database-admin.md` - Database design
16. `technical-writer.md` - Documentation
17. `accessibility-expert.md` - a11y
18. `localization-expert.md` - i18n
19. `api-designer.md` - API specifications
20. `code-reviewer.md` - Review specialist
21. `refactoring-expert.md` - Code improvement

### Phase 4: Party Mode (Week 3)

Implement BMAD's "Party Mode" in `bmad/party-mode/`:

```
bmad/party-mode/
├── orchestrator.md        # Multi-agent session manager
├── templates/
│   ├── planning-session.md
│   ├── troubleshooting-session.md
│   ├── design-session.md
│   └── review-session.md
└── agents/
    └── party-host.md      # Facilitates multi-agent sessions
```

### Phase 5: Module System (Week 4)

Create extensible module system:

```
bmad/modules/
├── core/                  # Always loaded
│   ├── module.yaml
│   └── workflows/
├── builder/               # BMB equivalent
│   ├── module.yaml
│   └── workflows/
├── testing/               # TEA equivalent
│   ├── module.yaml
│   └── workflows/
└── custom/                # User-created modules
    └── README.md
```

## Reverse Engineering Tasks

### Task 1: Extract BMAD Workflow Patterns

**What to capture:**
- Workflow step structure
- Input/output formats
- Decision points
- Success criteria
- Error handling

**How:**
1. Clone BMAD repo locally
2. Analyze `src/modules/bmm/workflows/`
3. Document patterns in `bmad/docs/workflow-patterns.md`

### Task 2: Extract Agent Definitions

**What to capture:**
- Agent personas
- System prompts
- Tool configurations
- Role definitions

**How:**
1. Find `.agent.yaml` files in BMAD
2. Analyze agent structure
3. Create equivalent in `bmad/agents/`

### Task 3: Extract Command Patterns

**What to capture:**
- `/command` structure
- Parameter handling
- Context passing
- Response formats

**How:**
1. Analyze how BMAD commands work
2. Map to Blackbox5 Task tool
3. Create command handlers

## Implementation Priority

### P0 (Critical Path)
- [ ] Create `bmad/` directory structure
- [ ] Implement Quick Flow (3 workflows)
- [ ] Create 7 core agents
- [ ] Integrate with existing `ralf.md`

### P1 (High Value)
- [ ] Implement Full Method (6 workflows)
- [ ] Create remaining 14 agents
- [ ] Add Party Mode
- [ ] Create module system

### P2 (Nice to Have)
- [ ] Custom module builder (BMB)
- [ ] Testing module (TEA)
- [ ] Advanced telemetry
- [ ] Workflow visualization

## Files to Create

### Immediate (This Session)

1. **Directory Structure:**
   ```
   2-engine/.autonomous/bmad/
   ├── README.md
   ├── modules/
   │   └── core/
   │       └── module.yaml
   ├── workflows/
   │   ├── quick-flow/
   │   │   ├── 01-spec.md
   │   │   ├── 02-dev.md
   │   │   └── 03-review.md
   │   └── full-method/
   │       ├── 01-brief.md
   │       ├── 02-prd.md
   │       ├── 03-arch.md
   │       ├── 04-epics.md
   │       ├── 05-sprint.md
   │       └── 06-story.md
   └── agents/
       ├── product-manager.md
       ├── architect.md
       ├── developer.md
       ├── ux-designer.md
       ├── scrum-master.md
       ├── qa-engineer.md
       └── test-architect.md
   ```

2. **Integration Files:**
   - `bmad/README.md` - Overview
   - `bmad/QUICKSTART.md` - Getting started
   - `bmad/INTEGRATION.md` - How it fits with existing RALF

## Migration Path

### For Existing RALF Users

1. **No Breaking Changes:** Existing `ralf.md` continues to work
2. **Opt-in BMAD:** Use BMAD workflows when beneficial
3. **Gradual Adoption:** Start with Quick Flow, expand to Full Method

### Usage Examples

**Quick Flow (existing task):**
```bash
# Task exists in tasks/active/
# RALF uses Quick Flow automatically for simple tasks
```

**Full Method (new complex task):**
```bash
# Task marked as "complex" in metadata
# RALF uses Full BMAD method
```

**Party Mode (multi-agent):**
```bash
# Spawn multiple agents for session
# Product Manager + Architect + Developer
```

## Success Metrics

- [ ] All 9 BMAD workflows implemented
- [ ] All 21 agents created
- [ ] Party Mode functional
- [ ] Module system extensible
- [ ] Documentation complete
- [ ] Tests passing
- [ ] No regression in existing RALF

## Next Steps

1. **Approve this plan**
2. **Create directory structure**
3. **Implement P0 items**
4. **Test integration**
5. **Iterate based on feedback**
