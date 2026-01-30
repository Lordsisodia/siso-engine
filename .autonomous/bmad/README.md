# BMAD for Blackbox5

**B**reakthrough **M**ethod for **A**gile **AI** **D**riven Development - Integrated into Blackbox5

## Overview

BMAD provides structured workflows for AI-driven development, adapted for Blackbox5's autonomous system. It offers two execution paths based on task complexity.

## Quick Start

### Path Selection

| Path | Use For | Time | Workflows |
|------|---------|------|-----------|
| **Quick Flow** | Bug fixes, small features | < 2 hrs | 3 workflows |
| **Full Method** | Products, platforms, complex features | > 2 hrs | 6 workflows |

### Usage

**Automatic:** RALF assesses task complexity and selects appropriate path

**Manual Override:** Add to task metadata:
```yaml
path: quick  # or "full"
```

## Directory Structure

```
bmad/
├── modules/
│   ├── core/           # Essential workflows
│   ├── builder/        # Custom workflow creation
│   └── testing/        # Test Architect (TEA)
├── workflows/
│   ├── quick-flow/     # Simple path (3 phases)
│   └── full-method/    # Complete method (6 phases)
├── agents/             # 21 specialized agents
└── party-mode/         # Multi-agent sessions
```

## Workflows

### Quick Flow
1. **Spec** (`01-spec.md`) - Quick technical specification
2. **Dev** (`02-dev.md`) - Implementation
3. **Review** (`03-review.md`) - Code review

### Full Method - Implemented
1. **Brief** (`01-brief.md`) - Product brief ✅
2. **PRD** (`02-prd.md`) - Requirements document ✅
3. **Arch** (`03-arch.md`) - Architecture design ✅
4. **Epics** (`04-epics.md`) - Story breakdown ✅
5. **Sprint** (`05-sprint.md`) - Sprint planning ✅
6. **Story** (`06-story.md`) - Story implementation ✅
7. **Retrospective** (`07-retrospective.md`) - Learn and improve ✅

## Agents

### Core (8) - Implemented
- Product Manager (John) ✅
- Architect (Winston) ✅
- Developer (Amelia) ✅
- UX Designer (Sally) ✅
- Scrum Master (Bob) ✅
- QA Engineer (Quinn) ✅
- Test Architect (TEA) ✅
- Quick Flow (Barry) ✅

### Specialized (14)
- Security Expert
- Performance Engineer
- DevOps Engineer
- Data Engineer
- ML Engineer
- Frontend Developer
- Backend Developer
- Database Admin
- Technical Writer
- Accessibility Expert
- Localization Expert
- API Designer
- Code Reviewer
- Refactoring Expert

## Party Mode

Multi-agent collaborative sessions:
- Planning sessions
- Troubleshooting sessions
- Design sessions
- Review sessions

## Integration with RALF

BMAD enhances RALF with:
- Structured workflows
- Specialized agents
- Complexity-based path selection
- Retrospectives

BMAD does not replace RALF - it provides the "how" while RALF provides the "what" and "when".

## Version

- BMAD Version: 6.0.0-alpha (adapted)
- Blackbox5 Integration: v1.0
- Last Updated: 2026-01-30
