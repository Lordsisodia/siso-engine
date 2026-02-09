# Template System Guide

**Version:** 1.0.0
**Last Updated:** 2026-02-01
**Purpose:** Define and enforce template file naming conventions for BlackBox5

---

## Overview

BlackBox5 uses a template system to maintain consistency across project documentation. Templates are starting points for creating real documentation files and should never be edited directly.

**Key Principle:** Template files are patterns, not production files.

---

## Template File Naming Convention

### Standard Format

All template files MUST follow this naming pattern:

```
[descriptive-name].md.template
```

**Examples:**
- `THOUGHTS.md.template` ✅
- `epic.md.template` ✅
- `technical.md.template` ✅
- `STATE.yaml.template` ✅

**Never use:**
- `THOUGHTS.template` ❌ (missing .md extension)
- `epic.template.md` ❌ (wrong order)
- `template-epic.md` ❌ (prefix instead of suffix)

### Location Convention

Templates are organized by type in `.templates/`:

```
.templates/
├── root/           # Project root file templates
├── epic/           # Epic documentation templates
├── tasks/          # Task execution templates
├── research/       # Research analysis templates
├── decisions/      # Decision record templates
├── reviews/        # Review templates
└── agents/         # Agent-specific templates
```

---

## Template vs Real Files

### Template Files (.template suffix)

- **Location:** `.templates/` directory
- **Purpose:** Provide starting structure for documentation
- **Usage:** Copy and fill in, never edit directly
- **Identification:** Ends in `.template` extension
- **Content:** Contains `FILL_ME` placeholders and structure

### Real Files (no .template suffix)

- **Location:** Actual project directories (`plans/`, `runs/`, etc.)
- **Purpose:** Production documentation for the project
- **Usage:** Read and update as project progresses
- **Identification:** No `.template` extension
- **Content:** Filled-in, actual project data

---

## Template Categories

### 1. Root File Templates (`.templates/root/`)

Templates for project-level files:

| Template | Output File | Purpose |
|----------|-------------|---------|
| `STATE.yaml.template` | `STATE.yaml` | Project state tracking |
| `ACTIVE.md.template` | `ACTIVE.md` | Current work dashboard |
| `WORK-LOG.md.template` | `WORK-LOG.md` | Activity log |
| `timeline.yaml.template` | `timeline.yaml` | Project milestones |
| `feature_backlog.yaml.template` | `feature_backlog.yaml` | Feature queue |

### 2. Epic Templates (`.templates/epic/`)

Templates for epic documentation:

| Template | Output File | Purpose |
|----------|-------------|---------|
| `epic.md.template` | `epic.md` | Main epic specification |
| `README.md.template` | `README.md` | Epic overview |
| `INDEX.md.template` | `INDEX.md` | Navigation |
| `XREF.md.template` | `XREF.md` | Cross-references |
| `ARCHITECTURE.md.template` | `ARCHITECTURE.md` | Technical design |
| `TASK-SUMMARY.md.template` | `TASK-SUMMARY.md` | Task tracking |
| `metadata.yaml.template` | `metadata.yaml` | Epic metadata |

### 3. Task Templates (`.templates/tasks/`)

Templates for task execution:

| Template | Output File | Purpose |
|----------|-------------|---------|
| `task-specification.md.template` | `TASK-XXX.md` | Task definition |
| `task-context-bundle.md.template` | `TASK-XXX-CONTEXT.md` | Task context |
| `task-completion.md.template` | `TASK-XXX-COMPLETION.md` | Task completion record |
| `task-acceptance-criteria.md.template` | `TASK-XXX-ACCEPTANCE.md` | Acceptance criteria |
| `THOUGHTS.md.template` | `THOUGHTS.md` | Executor thoughts |
| `LEARNINGS.md.template` | `LEARNINGS.md` | Task learnings |

### 4. Research Templates (`.templates/research/`)

Templates for 4D research framework:

| Template | Output File | Purpose |
|----------|-------------|---------|
| `STACK.md.template` | `STACK.md` | Technology analysis |
| `FEATURES.md.template` | `FEATURES.md` | Feature breakdown |
| `ARCHITECTURE.md.template` | `ARCHITECTURE.md` | System design |
| `PITFALLS.md.template` | `PITFALLS.md` | Risk analysis |
| `SUMMARY.md.template` | `SUMMARY.md` | 4D synthesis |

### 5. Decision Templates (`.templates/decisions/`)

Templates for decision records:

| Template | Output File | Purpose |
|----------|-------------|---------|
| `architectural.md.template` | `DEC-XXX-ARCH.md` | Architectural decisions |
| `scope.md.template` | `DEC-XXX-SCOPE.md` | Scope decisions |
| `technical.md.template` | `DEC-XXX-TECH.md` | Technical decisions |

### 6. Review Templates (`.templates/reviews/`)

Templates for project reviews:

| Template | Output File | Purpose |
|----------|-------------|---------|
| `first-principles-review.md.template` | `REVIEW-XXX.md` | First principles review |

### 7. Agent Templates (`.templates/agents/`)

Templates for agent-specific documentation:

| Template | Output File | Purpose |
|----------|-------------|---------|
| `agent-version.md.template` | `VERSION.md` | Agent version tracking |

---

## How to Use Templates

### Step 1: Copy Template to Real Location

```bash
# Example: Create new task specification
cp .templates/tasks/task-specification.md.template \
   .autonomous/tasks/active/TASK-1769915001.md

# Example: Create new epic
cp .templates/epic/* plans/active/epic-name/

# Example: Create decision record
cp .templates/decisions/technical.md.template \
   decisions/technical/DEC-2026-02-01-TECH-api-design.md
```

### Step 2: Fill in Placeholders

Replace all `FILL_ME` markers with actual content:

```markdown
# Before (template)
**Status:** FILL_ME
**Date:** FILL_ME

# After (real file)
**Status:** In Progress
**Date:** 2026-02-01
```

### Step 3: Remove Template Markers

Ensure no `FILL_ME` or template-specific markers remain.

### Step 4: Update Indexes

Add the new file to relevant indexes and STATE.yaml.

---

## Template File Header Convention

### Required Warning Header

All template files SHOULD include a warning header at the top:

```
# =============================================================================
# THIS IS A TEMPLATE FILE - DO NOT EDIT DIRECTLY
# =============================================================================
# Purpose: [What this template creates]
# Usage: Copy to target location and fill in FILL_ME placeholders
# Location: [Where this template should be copied to]
# =============================================================================
```

### Example

```markdown
# =============================================================================
# THIS IS A TEMPLATE FILE - DO NOT EDIT DIRECTLY
# =============================================================================
# Purpose: Task execution thoughts documentation
# Usage: Copy to runs/executor/run-XXX/THOUGHTS.md
# Location: .templates/tasks/THOUGHTS.md.template
# =============================================================================

# Thoughts - [TASK-ID]
...
```

---

## Common Mistakes to Avoid

### ❌ Don't

- Edit `.template` files directly (they're patterns)
- Create real files in `.templates/` directory
- Skip the `.template` suffix on template files
- Leave `FILL_ME` placeholders in real files
- Report "bugs" about template file discrepancies
- Use templates without understanding their purpose

### ✅ Do

- Copy templates to target locations before editing
- Fill in all `FILL_ME` placeholders
- Check for `.template` suffix before reporting issues
- Update templates when patterns change
- Document template usage in this guide
- Keep templates and real files separate

---

## Template Maintenance

### When to Update Templates

Update templates when:

1. **New fields needed** - Add `FILL_ME` placeholders for new required fields
2. **Pattern changes** - Update structure to reflect new documentation patterns
3. **Bug fixes** - Fix errors in template structure or placeholders
4. **Process improvement** - Add new sections or remove obsolete ones

### Template Update Process

1. Update template file in `.templates/`
2. Document change in this guide
3. Update `.docs/ai-template-usage-guide.md` if needed
4. Add entry to WORK-LOG.md
5. Communicate change to team (if applicable)

---

## Validation Checklist

Before creating documentation from templates:

- [ ] Identified correct template for the task
- [ ] Verified template follows `.md.template` or `.yaml.template` naming
- [ ] Copied template to correct target location
- [ ] Removed `.template` suffix from copy
- [ ] Filled in all `FILL_ME` placeholders
- [ ] Added warning header (if template includes it)
- [ ] Updated relevant indexes and STATE.yaml
- [ ] Updated WORK-LOG.md

---

## For AI Agents

### Template Discovery Rule

**ALWAYS check for `.template` suffix before reporting issues:**

```bash
# Check if file is a template
if [[ "$FILE" == *.template ]]; then
    echo "This is a template file - not a bug"
    exit 0
fi
```

### File Search Behavior

When searching for files:

1. **Exclude `.template` files** from grep searches unless specifically looking for templates
2. **Use `--exclude='*.template'` flag** to filter out templates
3. **Check file extension** - if ends in `.template`, it's a pattern not production data

### Example: Excluding Templates from Grep

```bash
# Find all markdown files EXCEPT templates
find . -name "*.md" ! -name "*.template"

# Grep real files only (exclude templates)
grep -r "TODO" --include="*.md" --exclude="*.template"
```

---

## Related Documentation

- **[AI Template Usage Guide](.docs/ai-template-usage-guide.md)** - How AI agents use templates
- **[.docs System Guide](.docs/dot-docs-system.md)** - Overall .docs directory structure
- **[Naming Conventions](_NAMING.md)** - General project naming rules
- **STATE.yaml** - Current project state and structure

---

## Template Inventory

As of 2026-02-01, the following templates exist:

| Category | Template Count | Location |
|----------|---------------|----------|
| Root | 8 | `.templates/root/` |
| Epic | 7 | `.templates/epic/` |
| Tasks | 7 | `.templates/tasks/` |
| Research | 5 | `.templates/research/` |
| Decisions | 3 | `.templates/decisions/` |
| Reviews | 1 | `.templates/reviews/` |
| Agents | 1 | `.templates/agents/` |
| **Total** | **32** | `.templates/` |

---

**Last Reviewed:** 2026-02-01
**Next Review:** When template patterns change or new templates added
