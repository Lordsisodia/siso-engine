# RALF Skills

**Location:** `$RALF_ENGINE_DIR/skills/` (in the engine)
**Purpose:** Transferable capabilities for autonomous task execution

---

## Philosophy

Skills are modular capabilities that Legacy can invoke:

1. **Single Responsibility** — Each skill does one thing well
2. **Documented Interface** — Clear inputs and outputs
3. **Tested** — Skills have verification steps
4. **Composable** — Skills can combine for complex workflows

---

## Skill Categories

### BMAD Agent Skills

| Skill | Agent | Role | Commands |
|-------|-------|------|----------|
| `bmad-pm.md` | John | Product Manager | CP, VP, EP, CE, IR, CC |
| `bmad-architect.md` | Winston | Architect | CA, VA, EA, IR |
| `bmad-analyst.md` | Mary | Business Analyst | BP, RS, CB, DP |
| `bmad-sm.md` | Bob | Scrum Master | SP, CS, ER, CC |
| `bmad-ux.md` | Sally | UX Designer | CU, VU, EU |
| `bmad-dev.md` | Amelia | Developer | DS, CR, QD |
| `bmad-qa.md` | Quinn | QA Engineer | QA, VT, RT |
| `bmad-quick-flow.md` | Barry | Solo Dev | TS, QD, CR |

**Command Reference:** See `../routes.yaml` for full command routing

**Workflow Patterns:** See `../workflows/` for A/P/C menu and WIP tracking patterns

### Core Skills (from BB5)

| Skill | Source | Purpose |
|-------|--------|---------|
| `first-principles-analysis` | BB5 1-agents/.skills/ | Structured problem decomposition |
| `testing-frameworks` | BB5 1-agents/.skills/ | Test writing and execution |
| `documentation-standards` | BB5 1-agents/.skills/ | Consistent documentation |

### MCP Integration Skills

| Skill | MCP | Purpose |
|-------|-----|---------|
| `supabase-operations` | Supabase | DDL, RLS, migrations |
| `file-operations` | File System | Read/write files |
| `browser-testing` | Chrome DevTools | UI testing, debugging |
| `complex-reasoning` | Sequential Thinking | Multi-step problems |
| `code-search` | Serena | Find patterns, references |

### Legacy-Specific Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `task-selection` | Choose next task from STATE.yaml | Active |
| `run-initialization` | Set up new run folder | Active |
| `git-commit` | Safe commit to dev branch | Active |
| `context-management` | Preserve/restore context | Active |

### Web Search & Research Skills

| Skill | Purpose | Tool | Status |
|-------|---------|------|--------|
| `web-search` | Search the web via SearXNG | `bin/web-search` | Active |

**Deployment:** See `deploy/searxng/` for Render/Railway deployment configs

### Cloud & Infrastructure Skills

| Skill | Purpose | Tool | Status |
|-------|---------|------|--------|
| `ralf-cloud-control` | Manage RALF agents in Kubernetes | `bin/ralf-cloud` | Active |

**Infrastructure:** See `6-roadmap/01-research/infrastructure/ralf-k8s-simple/` for K8s deployment

---

## Skill Format

Each skill is a markdown file:

```markdown
# Skill Name

**Purpose:** One-line description
**Trigger:** When to use
**Input:** Required inputs
**Output:** Expected outputs

## Procedure

1. Step one
2. Step two

## Verification

How to verify skill executed correctly

## Example

Example usage
```

---

## Usage

RALF invokes skills by:

1. **Inline** — "Using [skill-name], do X"
2. **Sub-agent** — Spawn agent with skill context
3. **Reference** — Link to skill file for complex procedures

Skills are loaded from the engine (`$RALF_ENGINE_DIR/skills/`) and applied to the project.

---

## Adding Skills

To add a new skill:

1. Create `[skill-name].md` in `$RALF_ENGINE_DIR/skills/`
2. Follow skill format template
3. Add to index above
4. Test before relying on
5. All projects get the skill automatically (it's in the engine)

