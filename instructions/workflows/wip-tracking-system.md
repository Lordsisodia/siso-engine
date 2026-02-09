# WIP File Tracking System

**Purpose:** Track work-in-progress across workflows with resumable state
**Location:** `2-engine/.autonomous/wip/`
**Pattern:** YAML frontmatter + Markdown body

## WIP File Structure

### Filename Convention

```
{command}-{short-description}-{timestamp}.md

Examples:
- cp-authentication-20260130-100000.md
- ts-api-endpoint-20260130-143000.md
- qd-bug-fix-20260130-160000.md
```

### Frontmatter Schema

```yaml
---
# Required Fields
workflow: string           # Workflow name (e.g., "create-prd")
command: string            # 2-letter command (e.g., "CP")
status: string             # in_progress | paused | completed | abandoned
started: ISO8601           # Start timestamp
updated: ISO8601           # Last update timestamp

# Progress Tracking
stepsCompleted: []         # Array of completed step names
currentStep: string        # Current active step
stepsRemaining: []         # Array of pending step names

# Context
context:                   # Key-value context
  title: string
  description: string
  requirements: []
  constraints: []

# Artifacts
artifacts: []              # List of generated files

# Agent Info (for Party mode)
agents: []                 # Agents involved in this work
primaryAgent: string       # Lead agent

# Git Info
gitBranch: string          # Associated branch
gitCommits: []             # Commits made during workflow

# Telemetry
timeSpentMinutes: number   # Accumulated time
contextSwitches: number    # Number of interruptions
---
```

## WIP Status Values

| Status | Meaning | Action on Continue |
|--------|---------|-------------------|
| `in_progress` | Actively being worked | Resume from current step |
| `paused` | Intentionally stopped | Resume from current step |
| `completed` | All steps done | Archive, don't show in menu |
| `abandoned` | Discarded | Archive, don't show in menu |

## Example WIP Files

### Example 1: PRD Creation (CP)

```yaml
---
workflow: create-prd
command: CP
status: in_progress
started: 2026-01-30T10:00:00Z
updated: 2026-01-30T11:30:00Z
stepsCompleted:
  - discovery
  - success-criteria
  - user-journeys
currentStep: domain-requirements
stepsRemaining:
  - functional-requirements
  - non-functional-requirements
  - polish
  - complete
context:
  title: "User Authentication System"
  problem_statement: "Users need secure, easy login"
  target_users:
    - end_users
    - admins
  constraints:
    - must_support_sso
    - gdpr_compliant: true
artifacts:
  - ./wip/cp-auth-discovery.md
  - ./wip/cp-auth-journeys.md
agents:
  - bmad-pm
primaryAgent: bmad-pm
gitBranch: bmad/cp-authentication
timeSpentMinutes: 90
contextSwitches: 0
---

# WIP: Create PRD - User Authentication System

## Completed Steps

### 1. Discovery ✓
- Problem: Users struggle with password management
- Users: End users, Admins
- Market: B2B SaaS

### 2. Success Criteria ✓
- User: Login in < 5 seconds
- Business: Reduce support tickets by 50%
- Technical: 99.9% uptime

### 3. User Journeys ✓
- New user registration
- Existing user login
- Password reset
- SSO login

## Current Step: Domain Requirements

Working on:
- [ ] Authentication flows
- [ ] Security requirements
- [ ] Integration points

## Notes

- Need to clarify SSO providers
- Consider magic link option

## Next Steps

Complete domain requirements, then move to functional requirements.
```

### Example 2: Quick Dev (QD)

```yaml
---
workflow: quick-dev
command: QD
status: paused
started: 2026-01-30T14:00:00Z
updated: 2026-01-30T14:30:00Z
stepsCompleted:
  - read-context
  - implement
currentStep: test
stepsRemaining:
  - verify
  - ship
context:
  title: "Fix login button styling"
  issue: "Button misaligned on mobile"
  component: "LoginForm"
artifacts:
  - src/components/LoginForm.tsx
agents:
  - bmad-quick-flow
primaryAgent: bmad-quick-flow
gitBranch: bmad/qd-login-button
timeSpentMinutes: 30
contextSwitches: 1
---

# WIP: Quick Dev - Fix Login Button

## Progress

- [x] Read existing code
- [x] Implement fix (added responsive classes)
- [ ] Test manually
- [ ] Ship

## Implementation Notes

Added `w-full sm:w-auto` to button for mobile responsiveness.

## Blockers

None - just need to test and commit.
```

## WIP Management Commands

### List Active WIP Files

```bash
# List all in-progress WIP files
ls -la ./wip/*.md | grep -E "status: in_progress|status: paused"
```

### Archive Completed WIP

```bash
# Move completed/abandoned WIP to archive
mv ./wip/cp-*-completed.md ./wip/archive/
```

### Clean Old WIP

```bash
# Remove WIP files older than 30 days
find ./wip -name "*.md" -mtime +30 -exec rm {} \;
```

## Integration with Skills

### At Workflow Start

```markdown
1. Check for existing WIP:
   - Search `./wip/{command}-*.md`
   - Filter by status: in_progress, paused
   - Sort by updated (most recent first)

2. If WIP found:
   - Read most recent WIP file
   - Present A/P/C menu with Continue option
   - Show summary: "Continue {title}? (Step X of Y)"

3. If user selects Continue:
   - Load WIP context
   - Skip completed steps
   - Resume from currentStep
```

### At Step Completion

```markdown
1. Complete step work
2. Update WIP:
   - Add step to stepsCompleted
   - Update currentStep to next
   - Update updated timestamp
   - Add any artifacts created
3. Save WIP file
4. Continue to next step
```

### At Workflow Completion

```markdown
1. Mark WIP status: completed
2. Update final artifacts list
3. Add completion timestamp
4. Move to archive (optional)
```

## WIP Helper Functions

```python
# Pseudo-code for WIP operations

def create_wip(command, workflow, context):
    """Create new WIP file"""
    wip = {
        "workflow": workflow,
        "command": command,
        "status": "in_progress",
        "started": now(),
        "updated": now(),
        "stepsCompleted": [],
        "currentStep": None,
        "stepsRemaining": get_workflow_steps(workflow),
        "context": context,
        "artifacts": []
    }
    return save_wip(wip)

def load_wip(filename):
    """Load and parse WIP file"""
    content = read_file(filename)
    frontmatter, body = parse_frontmatter(content)
    return {**frontmatter, "body": body}

def update_wip(filename, updates):
    """Update WIP file with new values"""
    wip = load_wip(filename)
    wip.update(updates)
    wip["updated"] = now()
    return save_wip(wip, filename)

def complete_step(wip_file, step_name, artifacts=None):
    """Mark step as completed"""
    wip = load_wip(wip_file)
    wip["stepsCompleted"].append(step_name)
    wip["currentStep"] = get_next_step(wip)
    wip["stepsRemaining"] = [s for s in wip["stepsRemaining"] if s != step_name]
    if artifacts:
        wip["artifacts"].extend(artifacts)
    return update_wip(wip_file, wip)

def list_active_wip():
    """List all active WIP files"""
    files = glob("./wip/*.md")
    active = []
    for f in files:
        wip = load_wip(f)
        if wip["status"] in ["in_progress", "paused"]:
            active.append(wip)
    return sorted(active, key=lambda x: x["updated"], reverse=True)
```

## Best Practices

1. **Save after EVERY step** - Don't lose progress
2. **Include context** - WIP should be resumable by any agent
3. **Link artifacts** - Reference all files created
4. **Update timestamps** - Track actual time spent
5. **Archive completed** - Keep ./wip/ clean
6. **Git branch tracking** - Link WIP to git work

## Verification

- [ ] WIP files created automatically
- [ ] Frontmatter valid YAML
- [ ] Steps tracked accurately
- [ ] Continue resumes correctly
- [ ] Archive process works
- [ ] Old WIP cleaned up
