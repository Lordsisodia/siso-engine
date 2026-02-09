# Blackbox5 Engine Consolidation Analysis

**Date:** 2026-02-07
**Current State:** 522 files across 8 top-level directories

---

## Executive Summary

The 522-file engine has significant consolidation opportunities:
- **~90 duplicate/outdated prompt files** in instructions/
- **~38 legacy helper files** that are unused or duplicated
- **~20 empty directories** to remove
- **~7 deprecated config files** per migration guide
- **Multiple broken imports** and path references

**Estimated reduction:** 250-300 files (50%+ reduction)

---

## 1. INSTRUCTIONS/ Directory (90+ files → ~40 files)

### Critical Issues

#### Duplicate Prompts
| Files | Issue | Action |
|-------|-------|--------|
| `agents/improvement-scout.md` + `agents/intelligent-scout.md` + `ralf-scout-improve.md` | 3 scout prompts, 80% overlap | Consolidate to single `agents/scout.md` with output modes |
| `ralf-executor.md` (root) vs `executor/versions/v4/executor.md` | Root is v2, conflicts with v4 | Archive root version |
| `system/identity.md` + `system/planner-identity.md` + `system/executor-identity.md` | Duplicate identity definitions | Archive - use versioned prompts only |
| `ralf.md` vs `system/identity.md` | Root ralf.md duplicates identity | Archive root version |

#### Outdated Versions to Archive
- `executor/versions/v1-*/` and `v2-*/`
- `planner/versions/v1-*/` and `v2-*/`
- `architect/versions/v1-*/` and `v2-*/`

#### Misplaced Files
- `instructions/workflows/` (35 YAML files) → Should be in `workflows/definitions/`
- `procedures/` (2 files) → Merge into guides/
- `exit/` (3 files) → Merge into single template
- `context/` (3 files) → Merge into templates/

### Recommended Structure
```
instructions/
├── agents/
│   ├── scout.md              # Consolidated (was 3 files)
│   └── six-agent-pipeline.md
├── executor/
│   ├── current -> versions/v4/executor.md
│   └── versions/v4-*/
├── planner/
│   ├── current -> versions/v4/planner.md
│   └── versions/v4-*/
├── architect/
│   ├── current -> versions/v4/architect.md
│   └── versions/v4-*/
├── templates/                # NEW: Shared components
│   ├── base-identity.md
│   ├── 7-phase-flow.md
│   ├── communication-protocol.md
│   └── exit-conditions.md
├── guides/
│   ├── execution-protocol.md
│   ├── task-selection.md
│   └── exit-conditions.md    # Merged from exit/*.md
└── archive/
    ├── v1-versions/
    ├── v2-versions/
    └── root-ralf-*.md
```

---

## 2. HELPERS/ Directory (136 files → ~60 files)

### Critical Issues

#### Broken Imports
- `helpers/core/registry.py` imports non-existent files:
  - `file_tools`, `bash_tool`, `search_tool`

#### Duplicate Git Helpers
- `git/git_ops.py` (331 lines) - Most complete
- `git/git_client.py` (60 lines) - Subset
- `git/commit_manager.py` (72 lines) - Duplicates CommitInfo

**Action:** Merge into single `git/git_ops.py`

#### Legacy Directory (38 files)

**Exact Duplicates:**
- `legacy/paths.py` = `5-project-memory/blackbox5/.autonomous/lib/paths.py`

**Test Files (move to tests/):**
- `test_decision_registry.py`
- `test_memory.py`
- `test_session_tracker.py`
- `test_state_machine.py`
- `test_workspace.py`
- `test_paths.py`
- `test_workflow_loader.py`

**Likely Unused (verify then delete):**
- `api_server.py`, `api_auth.py`, `webhook_receiver.py`
- `memory.py`, `session_tracker.py`, `state_machine.py`, `workspace.py`
- `workflow_loader.py`, `generate_workflows.py`
- `connectors/` (Slack, Jira, Trello)

**Potentially Still Used (review):**
- `decision_registry.py`, `context_budget.py`, `phase_gates.py`
- `skill_router.py`, `event_logger.py`, `roadmap_sync.py`
- `unified_config.py`

#### Integration Issues
- `vibe/__init__.py` has broken import: `from .VibeKanbanManager` should be `from .manager import VibeKanbanManager`
- 9 integrations exist but only GitHub and MCP are actively used

### Recommended Structure
```
helpers/
├── core/
│   ├── base.py
│   ├── registry.py           # Fix imports
│   └── integration_base.py   # NEW: Base class for integrations
├── git/
│   └── git_ops.py            # MERGED: All git functionality
└── integrations/
    ├── _template/
    ├── github/               # Keep (used)
    ├── mcp/                  # Keep (used)
    └── [review others for deletion]
```

---

## 3. AGENTS/ Directory (53 files → ~45 files)

### Critical Issues

#### Empty/Placeholder Directories
- `runtime/` - Completely empty
- `definitions/improvement/` - Only placeholder README

**Action:** Delete both

#### Duplicate Coordinator
- `definitions/managerial/claude-coordinator.sh` (bash)
- `definitions/managerial/task_lifecycle.py` (Python)

**Action:** Delete shell script, keep Python

#### Documentation in Code Directory
- `definitions/managerial/QUICKSTART.md`
- `definitions/managerial/COORDINATOR-AGENT-DESIGN.md`

**Action:** Move to `1-docs/`

#### Poor Naming
- `bmad/` → Should be `analysis_framework/`
- `sub-agents/` → Should be `sub-agent-specs/` (they're specs, not agents)

#### Research Agent Overlap
- `definitions/core/AnalystAgent.py` - Has research capabilities
- `definitions/specialists/research-specialist.yaml` - Research specialist
- `definitions/sub-agents/research-agent/SUBAGENT.md` - BB5 research spec

**Action:** Consolidate specialist into AnalystAgent

### Recommended Structure
```
agents/
├── framework/                # Keep as-is (4 files)
│   ├── base_agent.py
│   ├── agent_loader.py
│   ├── skill_manager.py
│   └── task_schema.py
└── definitions/
    ├── executable/           # Was: core/
    │   ├── ArchitectAgent.py
    │   ├── AnalystAgent.py   # Absorbs research-specialist
    │   └── DeveloperAgent.py
    ├── yaml-agents/          # Was: specialists/
    │   └── [17 specialist YAMLs]
    ├── sub-agent-specs/      # Was: sub-agents/
    │   └── [9 sub-agent specs]
    ├── analysis-framework/   # Was: bmad/
    │   └── [6 BMAD files]
    └── orchestration/        # Was: managerial/
        ├── task_lifecycle.py
        ├── skills/
        └── memory/
```

---

## 4. WORKFLOWS/ & CONFIGURATION/ Directories

### Critical Issues

#### Empty Directories
- `config/` (empty) - Delete
- `mcp/` (empty) - Delete

#### Misplaced Workflow Definitions
- `instructions/workflows/` (35 YAML files) → Move to `workflows/definitions/`

#### Deprecated Config Files (per MIGRATION-GUIDE.md)
- `configuration/agents/default.yaml`
- `configuration/agents/api-config.yaml`
- `configuration/agents/cli-config.yaml`
- `configuration/agents/github-config.yaml`
- `configuration/agents/alert-config.yaml`
- `configuration/agents/code-review-config.yaml`
- `configuration/agents/skill-registry.yaml`

#### MCP Config Split
- `configuration/mcp/` - Moltbot/OpenClaw configs
- `configuration/system/mcp-servers.json` - Server definitions
- `connections/mcp/` - Implementation

**Action:** Consolidate to single location

---

## 5. CONNECTIONS/ Directory

### Critical Issues

#### Empty Directory
- `2-engine/mcp/` exists but is EMPTY

**Action:** Delete

#### Broken Hook Script
- `hooks/active/github-auto-push.sh` references `../../lib/paths.sh` (moved to helpers/)

**Action:** Fix path or delete

#### Empty Version Directories
- 14 empty directories under `hooks/pipeline/*/versions/v1/`

**Action:** Delete all

---

## 6. INTERFACE/ Directory

### Critical Issues

#### Broken Imports
- `interface/cli/bb5.py` imports `from infrastructure.main import get_blackbox5` (infrastructure/ is empty)

#### Orphaned Agent Files
- `interface/epic_agent.py`
- `interface/task_agent.py`
- `interface/prd_agent.py`

**Action:** Verify if used, consolidate or delete

#### Design Docs in Code Dir
- `interface/INTEGRATION-IDEAS.md`
- `interface/AGENT-OUTPUT-BUS-DESIGN.md`

**Action:** Move to documentation/

---

## 7. SAFETY/ Directory

### Issues

#### Misplaced Test State Files
- `safety/tests/blackbox5/2-engine/01-core/safety/.kill_switch_state.json`
- `safety/tests/blackbox5/2-engine/01-core/safety/.safe_mode_state.json`

**Action:** Move to proper tests/ location, add to .gitignore

#### Pytest Cache in Source
- `safety/tests/.pytest_cache/`

**Action:** Add to .gitignore, delete

---

## 8. INFRASTRUCTURE/ Directory

### Critical Issue

All three subdirectories are EMPTY:
- `memory-algorithms/`
- `memory-systems/`
- `memory-utils/`

**Action:** Delete entire infrastructure/ directory

---

## 9. EXECUTABLES/ Directory

### Issues

#### Broken Stubs
Three executables are bash stubs pointing to non-existent project memory locations:
- `scout-intelligent.py`
- `improvement-loop.py`
- `planner-prioritize.py`

**Action:** Delete or fix

#### Compiled Files
- `__pycache__/` directory committed

**Action:** Add to .gitignore, delete

---

## 10. DOCUMENTATION/ Directory

### Issues

#### Empty Directories
- `documentation/memory/`
- `documentation/autonomous/`

**Action:** Delete

#### Completion Reports Accumulation
- 14 completion reports in `completions/`

**Action:** Move to project memory or archive

---

## Priority Action List

### HIGH (Broken/Non-functional)
1. Fix `helpers/core/registry.py` broken imports
2. Fix `helpers/integrations/vibe/__init__.py` broken import
3. Delete broken executable stubs (3 files)
4. Fix `interface/cli/bb5.py` broken infrastructure import
5. Delete empty directories (20+)
6. Remove `__pycache__/` directories

### MEDIUM (Duplicates/Cleanup)
7. Merge git helpers into single file
8. Archive outdated prompt versions (v1, v2)
9. Consolidate 3 scout prompts into 1
10. Delete deprecated config files (7 files)
11. Move test files from safety/ to tests/
12. Delete legacy/ unused files (~20 files)

### LOW (Organization)
13. Move workflow YAMLs to workflows/definitions/
14. Rename directories for clarity
15. Consolidate MCP config locations
16. Move documentation out of code directories

---

## Expected Outcome

| Metric | Before | After |
|--------|--------|-------|
| Total files | 522 | ~250-300 |
| Empty directories | 20+ | 0 |
| Broken imports | 5+ | 0 |
| Duplicate prompts | 15+ files | Consolidated |
| Legacy files | 38 | ~10 (reviewed) |

**Result:** Cleaner, more maintainable engine with clear purpose for each directory.
