# BMAD Commands for RALF

## Command Triggers (2-Letter Codes)

| Command | Agent | Description | When to Use |
|---------|-------|-------------|-------------|
| **CP** | PM (John) | Create PRD | New feature needs requirements |
| **VP** | PM (John) | Validate PRD | Check PRD completeness |
| **EP** | PM (John) | Edit PRD | Update existing PRD |
| **CE** | PM (John) | Create Epics | Break PRD into stories |
| **IR** | PM/Architect | Implementation Readiness | Verify alignment |
| **CC** | PM/SM | Course Correction | Major change mid-impl |
| **CA** | Architect (Winston) | Create Architecture | Technical decisions |
| **BP** | Analyst (Mary) | Brainstorm Project | Facilitated brainstorming |
| **RS** | Analyst (Mary) | Research | Market/domain/tech research |
| **CB** | Analyst (Mary) | Create Brief | Executive product brief |
| **DP** | Analyst (Mary) | Document Project | Document existing project |
| **SP** | SM (Bob) | Sprint Planning | Generate sprint sequence |
| **CS** | SM (Bob) | Create Story | Prepare story for dev |
| **ER** | SM (Bob) | Epic Retrospective | Review epic work |
| **CU** | UX (Sally) | Create UX | UX design work |
| **TS** | Barry | Tech Spec | Quick technical spec |
| **QD** | Barry | Quick Dev | Implement end-to-end |
| **DS** | Dev (Amelia) | Dev Story | Write tests and code |
| **CR** | Dev/Barry | Code Review | Comprehensive review |
| **QA** | Quinn | Automate | Generate tests |

## Usage in Tasks

Add to task metadata:

```yaml
---
Task ID: RALF-2026-01-30-001
triggers:
  - CP  # Will spawn PM for PRD creation
  - CE  # Then spawn PM for epic breakdown
path: full
---
```

## Command Routing

```
CP → pm-john.md → Create PRD workflow
VP → pm-john.md → Validate PRD workflow
EP → pm-john.md → Edit PRD workflow
CE → pm-john.md → Create Epics workflow
IR → pm-john.md OR architect-winston.md → Readiness check
CC → pm-john.md OR sm-bob.md → Course correction

CA → architect-winston.md → Architecture workflow

BP → analyst-mary.md → Brainstorm workflow
RS → analyst-mary.md → Research workflow
CB → analyst-mary.md → Product Brief workflow
DP → analyst-mary.md → Document Project workflow

SP → sm-bob.md → Sprint Planning workflow
CS → sm-bob.md → Create Story workflow
ER → sm-bob.md → Retrospective workflow

CU → ux-sally.md → UX Design workflow

TS → quick-flow-barry.md → Tech Spec workflow
QD → quick-flow-barry.md → Quick Dev workflow
CR → quick-flow-barry.md OR dev-amelia.md → Code Review

DS → dev-amelia.md → Dev Story workflow

QA → qa-quinn.md → Test Automation workflow
```

## Agent Selection Logic

```python
if command in ['CP', 'VP', 'EP', 'CE']:
    agent = 'pm-john'
elif command == 'CA':
    agent = 'architect-winston'
elif command in ['BP', 'RS', 'CB', 'DP']:
    agent = 'analyst-mary'
elif command in ['SP', 'CS', 'ER', 'CC']:
    agent = 'sm-bob'
elif command == 'CU':
    agent = 'ux-sally'
elif command in ['TS', 'QD']:
    agent = 'quick-flow-barry'
elif command in ['DS', 'CR']:
    agent = 'dev-amelia'
elif command == 'QA':
    agent = 'qa-quinn'
```
