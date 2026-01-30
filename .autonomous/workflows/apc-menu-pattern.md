# Workflow Pattern: A/P/C Menu

**Purpose:** Standard menu pattern for workflow progression (Advanced/Party/Continue)
**Usage:** Include at the start of multi-step workflows
**Location:** `2-engine/.autonomous/workflows/apc-menu-pattern.md`

## Pattern Overview

The A/P/C menu is a decision point at the start of workflows that lets users choose their path:

- **A (Advanced):** Full workflow with all steps, detailed outputs
- **P (Party):** Multi-agent collaborative mode (multiple agents work together)
- **C (Continue):** Resume from last checkpoint/WIP file

## Implementation

### Step 1: Check for WIP Files

```markdown
## Workflow Start

First, check for existing WIP files:

1. Look in `./wip/` for files matching `{workflow-name}-*.md`
2. If found, read the most recent WIP file
3. Present A/P/C menu with context
```

### Step 2: Present A/P/C Menu

```markdown
### Choose Your Path

**[A] Advanced Mode**
- Full workflow with all steps
- Detailed documentation
- Complete verification gates
- Best for: Complex tasks, learning, high-stakes work

**[P] Party Mode (Multi-Agent)**
- Multiple agents collaborate simultaneously
- Parallel work streams
- Faster completion
- Best for: Large tasks, diverse expertise needed

**[C] Continue from Checkpoint**
- Resume from last saved state
- Skip completed steps
- Maintain context
- Best for: Interrupted work, iterative refinement
```

### Step 3: Route Based on Selection

| Selection | Action |
|-----------|--------|
| **A** | Run full workflow sequentially |
| **P** | Spawn multiple agents in parallel |
| **C** | Load WIP file, resume from `stepsCompleted` |

## WIP File Format

WIP files track progress and enable continuation:

```yaml
---
workflow: create-prd
command: CP
started: 2026-01-30T10:00:00Z
updated: 2026-01-30T11:30:00Z
status: in_progress  # in_progress | paused | completed
stepsCompleted:
  - discovery
  - success-criteria
  - user-journeys
stepsRemaining:
  - domain-requirements
  - functional-requirements
  - non-functional-requirements
  - polish
  - complete
current_step: domain-requirements
context:
  prd_title: "User Authentication System"
  problem_statement: "Users need secure login"
artifacts:
  - ./wip/cp-auth-discovery.md
  - ./wip/cp-auth-journeys.md
---

# WIP: Create PRD for User Authentication

## Completed Work

### Discovery (✓)
- [x] Problem identified
- [x] Users defined
- [x] Constraints documented

### Success Criteria (✓)
- [x] User success defined
- [x] Business success defined
- [x] Technical success defined

## Current Step: Domain Requirements

Working on...

## Next Steps

1. Complete domain requirements
2. Move to functional requirements
3. Continue sequential workflow
```

## Integration with Skills

Skills should:

1. **Check for WIP** at workflow start
2. **Present A/P/C** if no WIP exists or user wants fresh start
3. **Load WIP** if continuing, skip completed steps
4. **Save WIP** after each step completion
5. **Update WIP** frontmatter with progress

## Example Usage in Skill

```markdown
## Procedure

### CP: Create PRD

**Step 0: A/P/C Menu**

Check for existing WIP:
- If `./wip/cp-*.md` exists → Offer Continue option
- If user selects Continue → Load WIP, resume from `current_step`
- If user selects Advanced → Run full workflow
- If user selects Party → Spawn PM + Architect + Analyst together

**Step 1: Discovery**
[... work happens ...]

**Save WIP**
After completing step 1, save WIP file with `stepsCompleted: [discovery]`

**Step 2: Success Criteria**
[... work happens ...]

**Save WIP**
Update WIP file with `stepsCompleted: [discovery, success-criteria]`

[Continue for all steps...]
```

## Code Pattern

```python
# Pseudo-code for A/P/C handling

def start_workflow(command, workflow_name):
    # 1. Check for WIP
    wip_files = glob(f"./wip/{command.lower()}-*.md")
    has_wip = len(wip_files) > 0

    # 2. Present menu
    if has_wip:
        choice = present_menu("[A] Advanced  [P] Party  [C] Continue")
    else:
        choice = present_menu("[A] Advanced  [P] Party")

    # 3. Route
    if choice == "C":
        wip = load_wip(wip_files[-1])
        resume_from_step(wip.current_step)
    elif choice == "P":
        spawn_party_mode(workflow_name)
    else:
        run_full_workflow(workflow_name)

def complete_step(step_name, workflow_name):
    # Do the work...

    # Save WIP
    wip = {
        "workflow": workflow_name,
        "stepsCompleted": get_completed_steps() + [step_name],
        "current_step": get_next_step(),
        "status": "in_progress"
    }
    save_wip(wip)
```

## Verification

- [ ] WIP files created after each step
- [ ] Frontmatter properly formatted
- [ ] Menu presented at workflow start
- [ ] Continue option skips completed steps
- [ ] Party mode spawns multiple agents
- [ ] Advanced mode runs full workflow
