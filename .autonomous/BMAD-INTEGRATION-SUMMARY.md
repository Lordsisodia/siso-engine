# BMAD Integration Summary

## What We Already Have (Don't Duplicate)

### Skills System
Location: `2-engine/.autonomous/skills/`
- Already has skill format
- Already has run-initialization skill
- Skills are the right place for BMAD capabilities

### Run Folder Structure
Location: `5-project-memory/ralf-core/.autonomous/runs/`
- Already creates run-NNNN folders
- Already has THOUGHTS.md, DECISIONS.md, etc.
- Don't create separate "outputs" folder

## What BMAD Has That We Should Integrate

### 1. Command System (2-Letter Triggers)
**Status:** Partially integrated in `bmad/COMMANDS.md`

**Integration:** Add to task metadata or routes.yaml
```yaml
# In routes.yaml
bmad_commands:
  CP: { agent: pm, action: create-prd }
  TS: { agent: quick-flow, action: tech-spec }
```

### 2. Agent Personas
**Status:** Created in `bmad/agents/` but should be skills

**Better Integration:** Convert to skills
```
skills/
├── bmad-pm.md          # Product Manager skill
├── bmad-architect.md   # Architect skill
├── bmad-analyst.md     # Analyst skill
└── bmad-qa.md          # QA skill
```

### 3. Workflow Step Patterns
**Status:** Not integrated

**Key Patterns to Extract:**
- **A/P/C Menu:** Advanced/Party/Continue options
- **WIP Files:** Work-in-progress with frontmatter
- **stepsCompleted Array:** Track progress
- **Step-by-step:** No skipping, sequential only

### 4. Module System
**Status:** Partial (we have module.yaml)

**Missing:**
- Install-time configuration
- User skill level selection
- Artifact path configuration

### 5. Party Mode (Multi-Agent)
**Status:** Not integrated

**What it is:** Multiple agents in one session
**RALF equivalent:** Sequential sub-agent spawning
**Gap:** True parallel multi-agent sessions

## Recommended Integration Plan

### Phase 1: Convert Agents to Skills (P0)

Move from `bmad/agents/` to `skills/`:

```bash
# Create BMAD skills
cp bmad/agents/pm-john.md skills/bmad-pm.md
cp bmad/agents/architect-winston.md skills/bmad-architect.md
cp bmad/agents/analyst-mary.md skills/bmad-analyst.md
cp bmad/agents/qa-quinn.md skills/bmad-qa.md
```

Update skill format to match existing skills.

### Phase 2: Command Integration (P0)

Add to `routes.yaml`:

```yaml
bmad:
  enabled: true
  commands:
    CP: { skill: bmad-pm, workflow: create-prd }
    TS: { skill: bmad-quick-flow, workflow: tech-spec }
    # ... etc
```

### Phase 3: Workflow Patterns (P1)

Add to workflows:
- A/P/C menu pattern
- WIP file pattern
- Step tracking

### Phase 4: Module Configuration (P1)

Add to `routes.yaml`:

```yaml
bmad:
  skill_level: intermediate  # beginner/intermediate/expert
  artifact_paths:
    planning: ./planning
    implementation: ./implementation
```

## What NOT to Integrate

| BMAD Feature | Why Not | Alternative |
|--------------|---------|-------------|
| Slash commands | Requires IDE integration | Task metadata triggers |
| Interactive prompts | Breaks autonomy | Pre-configuration in routes.yaml |
| File templating | Complex | Static files |
| Multi-turn conversations | Not autonomous | Single-shot with WIP files |
| Excalidraw integration | Visual/not autonomous | Skip |
| Worktree isolation | Sequential execution | Simple git workflow |

## Current Status

✅ Agent personas extracted from BMAD
✅ Command triggers documented
✅ Quick Flow workflows created
✅ **Agents converted to skills** (8 skills in `skills/`)
✅ **Command triggers added to routes.yaml**
✅ **A/P/C menu pattern implemented** (`workflows/apc-menu-pattern.md`)
✅ **WIP file tracking implemented** (`workflows/wip-tracking-system.md`)
✅ **Module configuration added** (routes.yaml `bmad.*`)
⚠️ Party Mode - requires multi-agent parallel execution (future)

## Completed Integration

### Phase 1: Skills ✅
All 8 BMAD agents converted to skills:
- `bmad-pm.md` - John (Product Manager)
- `bmad-architect.md` - Winston (Architect)
- `bmad-analyst.md` - Mary (Business Analyst)
- `bmad-sm.md` - Bob (Scrum Master)
- `bmad-ux.md` - Sally (UX Designer)
- `bmad-dev.md` - Amelia (Developer)
- `bmad-qa.md` - Quinn (QA Engineer)
- `bmad-quick-flow.md` - Barry (Solo Dev)

### Phase 2: Command Routing ✅
All 26 BMAD commands mapped in `routes.yaml`:
- PM commands: CP, VP, EP, CE
- Architect commands: CA, VA, EA
- Analyst commands: BP, RS, CB, DP
- SM commands: SP, CS, ER, CC
- UX commands: CU, VU, EU
- Dev commands: DS, CR
- QA commands: QA, VT, RT
- Quick Flow: TS, QD
- Shared: IR, CC

### Phase 3: Workflow Patterns ✅
- A/P/C menu pattern documented
- WIP file format specified
- Step tracking implemented
- Sequential execution enforced

### Phase 4: Module Configuration ✅
- Skill level setting (beginner/intermediate/expert)
- Artifact paths configured
- GitHub integration settings
- Telemetry tracking enabled
