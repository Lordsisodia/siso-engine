# AI Template Usage Guide

**For**: Autonomous agents (RALF, Claude, etc.)
**Purpose**: How to use project memory templates effectively
**Version**: 1.0

---

## Quick Start

When starting work on any project:

1. **Read STATE.yaml** - Understand current project state
2. **Read ACTIVE.md** - See what's being worked on
3. **Check for Context Bundle** - Look for TASK-XXX-CONTEXT.md
4. **Use Templates** - Follow patterns documented here

---

## Template Categories

### 1. Task Templates

#### When to Use
- Creating a new task
- Starting work on an existing task
- Handing off work to another agent

#### Template Location
```
templates/
├── task-specification.md      # For new tasks
├── task-context-bundle.md     # For context gathering
└── task-completion.md         # For completing tasks
```

#### How to Use

**Step 1: Create Task Specification**
```bash
# Copy template
cp templates/task-specification.md tasks/active/TASK-$(date +%s).md

# Fill in:
# - Task ID
# - Title
# - Description
# - Acceptance criteria
# - Dependencies
```

**Step 2: Create Context Bundle (CRITICAL)**
```bash
# Copy template
cp templates/task-context-bundle.md tasks/active/TASK-XXX-CONTEXT.md

# Fill in by gathering:
# - Related epic location
# - Related PRD sections
# - Research findings
# - Dependencies
# - Related decisions
```

**Step 3: Work on Task**
```bash
# Read context bundle first
cat tasks/active/TASK-XXX-CONTEXT.md

# Do the work
# ...

# Update WORK-LOG.md
```

**Step 4: Complete Task**
```bash
# Copy completion template
cp templates/task-completion.md tasks/completed/TASK-XXX-COMPLETION.md

# Fill in:
# - What was done
# - Files changed
# - Decisions made
# - Time taken
```

---

### 2. Research Templates (4D Framework)

#### When to Use
- Starting a new feature/epic
- Evaluating technology choices
- Analyzing requirements

#### Template Location
```
templates/research/
├── STACK.md.template      # Technology analysis
├── FEATURES.md.template   # Feature breakdown
├── ARCHITECTURE.md.template # System design
├── PITFALLS.md.template   # Risk analysis
└── SUMMARY.md.template    # 4D synthesis
```

#### How to Use

**Step 1: Create Research Folder**
```bash
mkdir -p plans/active/feature-name/research
```

**Step 2: Fill Out 4D Templates**
```bash
# Technology Dimension
cp templates/research/STACK.md.template \
   plans/active/feature-name/research/STACK.md
# Fill in: Options, comparison, recommendation

# Feature Dimension
cp templates/research/FEATURES.md.template \
   plans/active/feature-name/research/FEATURES.md
# Fill in: Feature list, user stories, acceptance criteria

# Architecture Dimension
cp templates/research/ARCHITECTURE.md.template \
   plans/active/feature-name/research/ARCHITECTURE.md
# Fill in: Components, data flow, integrations

# Pitfalls Dimension
cp templates/research/PITFALLS.md.template \
   plans/active/feature-name/research/PITFALLS.md
# Fill in: Known issues, risks, mitigation strategies
```

**Step 3: Create Summary**
```bash
cp templates/research/SUMMARY.md.template \
   plans/active/feature-name/research/SUMMARY.md
# Synthesize all 4 dimensions into recommendations
```

---

### 3. Epic Templates

#### When to Use
- Creating a new epic
- Planning a major feature
- Breaking down large work

#### Template Location
```
templates/epic/
├── epic.md.template           # Main epic specification
├── README.md.template         # Quick overview
├── INDEX.md.template          # Navigation
├── XREF.md.template           # Cross-references
├── ARCHITECTURE.md.template   # Technical details
├── TASK-SUMMARY.md.template   # Task table
└── metadata.yaml.template     # Machine-readable
```

#### How to Use

**Step 1: Create Epic Folder**
```bash
mkdir -p plans/active/epic-name
```

**Step 2: Copy All Templates**
```bash
cp templates/epic/* plans/active/epic-name/
# Remove .template extension
rename 's/\.template$//' plans/active/epic-name/*.template
```

**Step 3: Fill Out in Order**
```bash
# 1. metadata.yaml - Define basic info
# 2. epic.md - Write full specification
# 3. README.md - Create summary
# 4. ARCHITECTURE.md - Design system
# 5. XREF.md - Link to PRD, research
# 6. INDEX.md - Create navigation
# 7. TASK-SUMMARY.md - List all tasks
```

**Step 4: Create Tasks**
```bash
# From task breakdown, create individual task files
for i in $(seq -w 1 18); do
    cp templates/task-specification.md \
       plans/active/epic-name/${i}.md
done
```

---

### 4. Decision Templates

#### When to Use
- Making architectural choices
- Documenting scope changes
- Recording technical decisions

#### Template Location
```
templates/decisions/
├── architectural.md.template
├── scope.md.template
└── technical.md.template
```

#### How to Use

**Step 1: Choose Template Type**
```bash
# For system structure changes
cp templates/decisions/architectural.md.template \
   decisions/architectural/DEC-$(date +%Y-%m-%d)-title.md

# For scope changes
cp templates/decisions/scope.md.template \
   decisions/scope/DEC-$(date +%Y-%m-%d)-title.md

# For technology choices
cp templates/decisions/technical.md.template \
   decisions/technical/DEC-$(date +%Y-%m-%d)-title.md
```

**Step 2: Fill Out Sections**
```markdown
# Required fields:
- Status: Proposed | Accepted | Deprecated
- Date: YYYY-MM-DD
- Author: Agent/Human name
- Context: What led to this
- Decision: What was decided
- Rationale: Why
- Alternatives: What else was considered
- Impact: What changes
```

**Step 3: Update Indexes**
```bash
# Add to decisions/INDEX.md
# Add to STATE.yaml decisions section
```

---

### 5. Root File Templates

#### When to Use
- Setting up new project
- Updating project state
- Creating dashboards

#### Template Location
```
templates/root/
├── STATE.yaml.template
├── WORK-LOG.md.template
├── ACTIVE.md.template
├── feature_backlog.yaml.template
├── test_results.yaml.template
├── CODE-INDEX.yaml.template
├── _NAMING.md.template
└── QUERIES.md.template
```

#### How to Use

**STATE.yaml Updates**
```bash
# Read current STATE.yaml
# Update relevant sections:
# - active_tasks
# - completed_tasks
# - active_features
# - decisions
# - recent_work
# DO NOT delete, only append/update
```

**WORK-LOG.md Updates**
```bash
# Add new entry at TOP (reverse chronological)
# Use template section from WORK-LOG.md.template
# Include:
# - Date
# - Work title
# - Time invested
# - Changes made
# - Files created/modified
# - Results
```

**ACTIVE.md Updates**
```bash
# Regenerate from STATE.yaml
# Or update manually:
# - Quick stats
# - Active features
# - Active tasks
# - Recent decisions
# - Next actions
```

---

## AI Workflow Patterns

### Pattern 1: Starting Work on Existing Task

```bash
# 1. Load context
cat STATE.yaml
cat ACTIVE.md

# 2. Find task
cat tasks/active/TASK-XXX-CONTEXT.md

# 3. If no context bundle, create one
cp templates/task-context-bundle.md \
   tasks/active/TASK-XXX-CONTEXT.md
# Fill from epic, research, decisions

# 4. Do work

# 5. Update WORK-LOG.md
# 6. Update STATE.yaml
# 7. Update task status
```

### Pattern 2: Creating New Epic

```bash
# 1. Research phase
mkdir -p plans/active/epic-name/research
cp templates/research/*.md.template \
   plans/active/epic-name/research/
# Fill out 4D research

# 2. Epic creation
cp templates/epic/* plans/active/epic-name/
# Fill out epic.md, metadata.yaml

# 3. Task breakdown
# Create task files 001.md, 002.md, etc.
# Create TASK-SUMMARY.md

# 4. Cross-references
# Create XREF.md linking PRD, research, tasks

# 5. Update STATE.yaml
# Add epic to active_features
```

### Pattern 3: Making a Decision

```bash
# 1. Create decision record
cp templates/decisions/architectural.md.template \
   decisions/architectural/DEC-$(date +%Y-%m-%d)-title.md

# 2. Fill out all sections
# Context, Decision, Rationale, Alternatives, Impact

# 3. Update related files
# Add to decisions/INDEX.md
# Update STATE.yaml decisions section
# Link from affected tasks/epics

# 4. Update WORK-LOG.md
# Document the decision
```

---

## Common Mistakes to Avoid

### ❌ Don't
- Delete existing content in STATE.yaml
- Create tasks without context bundles
- Make decisions without documenting alternatives
- Skip the research phase for large features
- Forget to update WORK-LOG.md
- Leave templates unfilled (remove template markers)

### ✅ Do
- Append to STATE.yaml, never replace
- Always create context bundles for tasks
- Document why alternatives were rejected
- Do 4D research before epic creation
- Update WORK-LOG.md after every work session
- Remove all template markers when done

---

## Template Checklist

Before marking work complete:

- [ ] All template markers removed
- [ ] All `FILL_ME` placeholders replaced
- [ ] Links verified (not broken)
- [ ] STATE.yaml updated
- [ ] WORK-LOG.md updated
- [ ] Cross-references created
- [ ] Context bundle complete

---

## Quick Reference

| Task | Template | Output Location |
|------|----------|-----------------|
| New task | task-specification.md | tasks/active/TASK-XXX.md |
| Task context | task-context-bundle.md | tasks/active/TASK-XXX-CONTEXT.md |
| Research | research/*.md | plans/active/X/research/ |
| Epic | epic/*.md | plans/active/epic-name/ |
| Decision | decisions/*.md | decisions/{type}/DEC-XXX.md |
| Work log | N/A (append) | WORK-LOG.md |
| State update | N/A (update) | STATE.yaml |

---

**Remember**: Templates are starting points. The goal is complete, accurate documentation that helps future agents (and humans) understand the project.
