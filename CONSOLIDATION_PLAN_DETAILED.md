# Detailed Consolidation Plan with Reasoning

## Philosophy

Each consolidation follows these principles:
1. **Single Source of Truth** - One canonical version, not duplicates
2. **Purpose-Based Organization** - Files live where their function suggests
3. **Active vs Archive** - Separate working code from historical reference
4. **Fix or Delete** - Broken/unused code is technical debt

---

## CATEGORY 1: Duplicate Prompt Consolidation (instructions/)

### 1.1 Three Scout Prompts → One

**Current State:**
- `agents/improvement-scout.md` (251 lines) - YAML-focused scout
- `agents/intelligent-scout.md` (335 lines) - JSON-focused scout
- `ralf-scout-improve.md` (217 lines) - One-shot condensed version

**Why They Exist:**
These were created at different times for slightly different use cases. The "intelligent" version added JSON output. The "improvement" version was for continuous loops. The "scout-improve" was a one-shot version.

**Why This Is Wrong:**
- 80% content overlap (same scoring formula: `(impact × 3) + (frequency × 2) - (effort × 1.5)`)
- Maintenance burden: Change scoring logic in 3 places
- Confusion: Which scout should I use?

**Consolidation Strategy:**
Create single `agents/scout.md` with output format parameter:
```yaml
scout:
  mode: detailed|quick|oneshot
  output_format: yaml|json
```

**Reduction:** 3 files → 1 file (save 2 files, ~600 lines → ~250 lines)

---

### 1.2 Root RALF Files vs Versioned Prompts

**Current State:**
- `ralf.md` (root) - Base RALF v2.0 identity
- `ralf-executor.md` (root) - v2 executor with skills, duplicate detection
- `executor/versions/v4-20260202/executor.md` - Current v4 with 7-phase flow

**Why They Exist:**
The root files were the original prompts. As RALF evolved, versioned prompts were created (v1, v2, v3, v4). The root files were kept for "backward compatibility."

**Why This Is Wrong:**
- Root `ralf-executor.md` documents v2 features that don't exist in v4
- Creates confusion: which is the "real" executor prompt?
- Changes made to versioned prompts don't propagate to root files
- README admits root files are "preserved for backward compatibility" = unused

**Consolidation Strategy:**
- Archive root `ralf.md` and `ralf-executor.md`
- Keep only versioned prompts in `executor/versions/`
- Create symlink: `executor/current.md` → `versions/v4/executor.md`

**Reduction:** 2 root files → 0 (archive), 1 symlink added

---

### 1.3 System Identity Files vs Agent Prompts

**Current State:**
- `system/identity.md` - Generic RALF identity
- `system/planner-identity.md` - Planner role definition
- `system/executor-identity.md` - Executor role definition
- `planner/versions/v4/planner.md` - Full planner prompt with identity built-in
- `executor/versions/v4/executor.md` - Full executor prompt with identity built-in

**Why They Exist:**
The system/identity files were created for a "Dual-RALF" system (separate planner and executor agents). The versioned prompts in planner/ and executor/ were created later with integrated identities.

**Why This Is Wrong:**
- Dual-RALF system was never fully deployed
- Identity in `system/planner-identity.md` duplicates first 100 lines of `planner/versions/v4/planner.md`
- Same for executor
- Having identity separate from the full prompt means they drift out of sync

**Consolidation Strategy:**
- Archive all `system/*-identity.md` files
- Identity is now embedded in versioned agent prompts (v4)
- If Dual-RALF is ever deployed, extract identity from versioned prompts

**Reduction:** 3 files → 0 (archive)

---

### 1.4 Version Sprawl (v1, v2, v3, v4)

**Current State:**
Each agent (executor, planner, architect) has:
- `versions/v1-20260201/` - Original version
- `versions/v2-20260201/` - Second iteration
- `versions/v3-20260202/` - Third iteration
- `versions/v4-20260202/` - Current version

**Why They Exist:**
Legitimate version history. Each iteration improved the prompts.

**Why This Is Wrong:**
- Keeping 3 outdated versions per agent = 9 outdated directories
- v1 and v2 are significantly different from v4 (not useful for reference)
- Git history already preserves old versions if needed
- Clutters the directory, makes finding current version harder

**Consolidation Strategy:**
- Keep only v3 (previous major) and v4 (current)
- Archive v1 and v2 to `archive/v1-versions/`, `archive/v2-versions/`
- If needed, old versions are in git history

**Reduction:** 12 version directories → 6 directories (save 6)

---

### 1.5 Small Directory Consolidation

**Current State:**
- `procedures/` - 2 files (execution-protocol.md, task-selection.md)
- `context/` - 3 files (bb5-infrastructure.md, branch-safety.md, project-specific.md)
- `exit/` - 3 files (success.md, partial.md, blocked.md)

**Why They Exist:**
Logical separation of concerns. Each directory has a specific purpose.

**Why This Is Wrong:**
- Directories with 2-3 files are overkill
- Creates deep nesting for little content
- Harder to navigate than a single directory

**Consolidation Strategy:**
- Merge `procedures/` into `guides/procedures.md` (single file)
- Merge `context/` into `guides/context.md` (single file with sections)
- Merge `exit/` into `templates/exit-conditions.md` (single file)

**Reduction:** 3 directories (8 files) → 1 directory (3 files)

---

### 1.6 Workflow Definitions in Wrong Place

**Current State:**
- `instructions/workflows/` - 35 YAML workflow files
- `workflows/engine/` - Python orchestration code

**Why They Exist:**
Workflows were originally instructions for agents. But they're actually workflow definitions that the orchestrator executes.

**Why This Is Wrong:**
- `instructions/` should be for agent prompts/instructions
- Workflow definitions are data files executed by code
- Separation of concerns: instructions (text) vs workflows (executable definitions)

**Consolidation Strategy:**
- Move `instructions/workflows/*.yaml` to `workflows/definitions/`
- Keep `instructions/` for agent prompts only
- `workflows/` becomes: `engine/` (code) + `definitions/` (YAML)

**Reduction:** No file reduction, but proper organization

---

## CATEGORY 2: Helper Consolidation (helpers/)

### 2.1 Three Git Helpers → One

**Current State:**
- `git/git_ops.py` (331 lines) - Full GitOps class with atomic commits, rollback, history
- `git/git_client.py` (60 lines) - Simple wrapper around git commands
- `git/commit_manager.py` (72 lines) - Commit management with conventional commits

**Why They Exist:**
`git_client.py` was the first simple wrapper. `git_ops.py` added more sophisticated operations. `commit_manager.py` was added for conventional commit formatting.

**Why This Is Wrong:**
- `GitClient` and `GitOps` both wrap git commands (duplicate abstraction)
- `CommitManager` duplicates commit logic from `GitOps`
- `CommitInfo` dataclass defined in BOTH `git_ops.py` and `commit_manager.py`
- Import confusion: which one should I use?

**Consolidation Strategy:**
- Keep `git_ops.py` (most complete)
- Merge `CommitManager` functionality into `GitOps` class
- Delete `git_client.py` and `commit_manager.py`
- Single import: `from helpers.git import GitOps`

**Reduction:** 3 files → 1 file (save 2 files, ~400 lines)

---

### 2.2 Legacy Directory Cleanup

**Current State:**
38 files in `helpers/legacy/` including:
- `paths.py` - EXACT DUPLICATE of project memory version
- 7 test files that should be in `tests/`
- `api_server.py`, `api_auth.py`, `webhook_receiver.py` - Unused Flask code
- `memory.py`, `session_tracker.py`, `state_machine.py`, `workspace.py` - Old implementations
- `connectors/` - Slack, Jira, Trello connectors (likely unused)

**Why They Exist:**
These were active components of earlier RALF versions. When the architecture changed, they were moved to "legacy" rather than deleted "just in case."

**Why This Is Wrong:**
- `paths.py` is byte-for-byte identical to project memory version (maintenance nightmare)
- Old memory/session/state systems were replaced by new implementations
- Flask API server was never deployed
- Connectors were created but not integrated
- 14,700 lines of code = mental overhead when exploring codebase

**Consolidation Strategy:**

**Exact Duplicates (Delete):**
- `paths.py` - Use project memory version

**Test Files (Move):**
- All `test_*.py` → `tests/unit/legacy/` (if still relevant) or delete

**Definitely Delete:**
- `api_server.py`, `api_auth.py`, `webhook_receiver.py` - No imports found
- `memory.py`, `session_tracker.py`, `state_machine.py`, `workspace.py` - Replaced by new systems
- `workflow_loader.py`, `generate_workflows.py` - Replaced by new workflow system
- `connectors/` - No imports found

**Review Then Decide:**
- `decision_registry.py`, `context_budget.py`, `phase_gates.py`
- `skill_router.py`, `event_logger.py`, `roadmap_sync.py`
- `unified_config.py`

**Reduction:** 38 files → ~10 files (save 28 files, ~10,000 lines)

---

### 2.3 Broken Core Registry Imports

**Current State:**
`helpers/core/registry.py` imports:
```python
from .file_tools import FileReadTool, FileWriteTool
from .bash_tool import BashExecuteTool
from .search_tool import SearchTool
```

**Why They Exist:**
These tools were planned but never implemented. The imports were added as placeholders.

**Why This Is Wrong:**
- Importing non-existent modules = broken code
- Anyone importing `registry.py` gets ImportError
- Registry should only register tools that exist

**Consolidation Strategy:**
- Remove broken imports
- Add registration for tools that DO exist
- Or make registration dynamic (only register if file exists)

**Reduction:** Fix 1 file (no reduction, but fixes broken code)

---

## CATEGORY 3: Agent Definition Consolidation (agents/)

### 3.1 Empty/Placeholder Directories

**Current State:**
- `agents/runtime/` - Completely empty (0 files)
- `agents/definitions/improvement/` - Only contains placeholder README: "Placeholder for Scout/Executor/Verifier agents (Phase 2)"

**Why They Exist:**
`runtime/` was planned for runtime agent instances. `improvement/` was planned for Phase 2 implementation.

**Why This Is Wrong:**
- Empty directories clutter the structure
- Placeholder README from months ago with no progress
- If needed, directories can be recreated

**Consolidation Strategy:**
- Delete both directories
- Create them when actually implementing those features

**Reduction:** 2 directories → 0

---

### 3.2 Duplicate Coordinator Implementation

**Current State:**
- `definitions/managerial/claude-coordinator.sh` (bash script, ~350 lines)
- `definitions/managerial/task_lifecycle.py` (Python class, ~600 lines)

**Why They Exist:**
The bash script was the original coordinator. The Python version was created later as a more robust implementation.

**Why This Is Wrong:**
- Two implementations of same functionality = maintenance burden
- Bash version is less capable (no error handling, harder to test)
- Shell script in Python definitions directory is wrong place anyway

**Consolidation Strategy:**
- Delete `claude-coordinator.sh`
- Keep `task_lifecycle.py` as canonical implementation
- If shell wrapper needed, create thin wrapper that calls Python

**Reduction:** 2 implementations → 1 (save 1 file)

---

### 3.3 Documentation in Code Directories

**Current State:**
- `definitions/managerial/QUICKSTART.md` (~200 lines)
- `definitions/managerial/COORDINATOR-AGENT-DESIGN.md` (~250 lines)
- `definitions/managerial/README.md` (427 lines)

**Why They Exist:**
Documentation was kept close to the code it documents.

**Why This Is Wrong:**
- Code directories should contain code
- Documentation belongs in `documentation/` or `1-docs/`
- Mixing docs and code makes both harder to find

**Consolidation Strategy:**
- Move design docs to `1-docs/engine/coordination-design.md`
- Move QUICKSTART to `documentation/coordinator-quickstart.md`
- Keep brief README.md in directory (standard practice)

**Reduction:** Move 2 files (no reduction, but proper organization)

---

### 3.4 Research Agent Overlap

**Current State:**
- `definitions/core/AnalystAgent.py` - Has research, data_analysis, competitive_analysis capabilities
- `definitions/specialists/research-specialist.yaml` - Technology evaluation, documentation research
- `definitions/sub-agents/research-agent/SUBAGENT.md` - BB5-specific external research

**Why They Exist:**
Different levels of research: general (AnalystAgent), specialist domain (research-specialist), BB5 improvement (research-agent).

**Why This Is Wrong:**
- Overlapping capabilities confuse which to use
- Research-specialist is just a subset of AnalystAgent capabilities
- Three ways to do research = decision fatigue

**Consolidation Strategy:**
- Merge `research-specialist.yaml` capabilities into `AnalystAgent.py`
- Keep `research-agent/SUBAGENT.md` as it's BB5-specific (different purpose)
- AnalystAgent becomes the general research agent

**Reduction:** 3 research definitions → 2 (save 1 file)

---

### 3.5 Naming Clarity

**Current State:**
- `bmad/` - BMAD = Business-Model-Architecture-Development (acronym)
- `sub-agents/` - Contains SUBAGENT.md specs, not actual agents
- `core/` - Contains executable agents

**Why These Names:**
Historical reasons. BMAD was the project name. "sub-agents" sounded right. "core" seemed appropriate for primary agents.

**Why This Is Wrong:**
- Acronyms require explanation
- "sub-agents" are actually specifications (confusing)
- "core" is vague (what makes them "core"?)

**Consolidation Strategy:**
- `bmad/` → `analysis-framework/` (descriptive)
- `sub-agents/` → `sub-agent-specs/` (accurate)
- `core/` → `executable/` (descriptive - they inherit BaseAgent)

**Reduction:** No file reduction, but clearer naming

---

## CATEGORY 4: Configuration Consolidation

### 4.1 Empty Config Directory

**Current State:**
- `configuration/` - Populated with configs
- `config/` - Empty directory (0 files)

**Why They Exist:**
During reorganization, `config/` was renamed to `configuration/`. The old directory wasn't deleted.

**Why This Is Wrong:**
- Two config locations = confusion
- Empty directory serves no purpose

**Consolidation Strategy:**
- Delete empty `config/` directory

**Reduction:** 1 empty directory → 0

---

### 4.2 Deprecated Config Files

**Current State:**
Per `configuration/agents/MIGRATION-GUIDE.md`, these configs were consolidated but files still exist:
- `default.yaml` - Legacy RALF defaults
- `api-config.yaml` - Component-specific
- `cli-config.yaml` - Component-specific
- `github-config.yaml` - Component-specific
- `alert-config.yaml` - Feature-specific
- `code-review-config.yaml` - Feature-specific
- `skill-registry.yaml` - Legacy skill definitions

**Why They Exist:**
The migration guide says configs were unified into `base.yaml` + `engine.yaml` + `schema.yaml`. But old files weren't deleted.

**Why This Is Wrong:**
- Migration was incomplete
- Files still present = confusion about which to use
- 7 files that should have been deleted

**Consolidation Strategy:**
- Delete all 7 deprecated config files
- Verify nothing imports them
- Update MIGRATION-GUIDE.md to show completion

**Reduction:** 7 files → 0 (save 7 files)

---

### 4.3 MCP Config Fragmentation

**Current State:**
- `configuration/mcp/` - Moltbot and OpenClaw configs
- `configuration/system/mcp-servers.json` - MCP server definitions
- `connections/mcp/` - MCP implementations
- `helpers/integrations/mcp/` - MCP utilities

**Why They Exist:**
Different aspects of MCP: configuration, server definitions, implementation, utilities.

**Why This Is Wrong:**
- MCP logic split across 4 locations
- Hard to understand the full MCP picture
- Changes require updates in multiple places

**Consolidation Strategy:**
- Keep `configuration/mcp/` for config files
- Merge `system/mcp-servers.json` into `configuration/mcp/servers.yaml`
- Keep `connections/mcp/` for implementation (separation of config/code is good)
- Merge `helpers/integrations/mcp/` into `connections/mcp/helpers/`

**Reduction:** 4 locations → 2 locations (config + implementation)

---

## CATEGORY 5: Empty Directory Cleanup

### 5.1 Infrastructure Directory

**Current State:**
- `infrastructure/memory-algorithms/` - Empty
- `infrastructure/memory-systems/` - Empty
- `infrastructure/memory-utils/` - Empty

**Why They Exist:**
Created during reorganization planning but never populated.

**Consolidation Strategy:**
- Delete entire `infrastructure/` directory
- When infrastructure files exist, create proper structure

**Reduction:** 3 empty directories → 0

---

### 5.2 MCP Directory (Root Level)

**Current State:**
- `2-engine/mcp/` - Empty directory

**Why It Exists:**
Leftover from reorganization. `connections/mcp/` is the actual location.

**Consolidation Strategy:**
- Delete empty `mcp/` directory

**Reduction:** 1 empty directory → 0

---

### 5.3 Hooks Empty Version Directories

**Current State:**
- `connections/hooks/pipeline/*/versions/v1/` - 14 empty directories

**Why They Exist:**
Versioning structure created but v1 never populated.

**Consolidation Strategy:**
- Delete all 14 empty version directories
- Create version directories when actually versioning

**Reduction:** 14 empty directories → 0

---

### 5.4 Documentation Empty Directories

**Current State:**
- `documentation/memory/` - Empty
- `documentation/autonomous/` - Empty

**Consolidation Strategy:**
- Delete both empty directories

**Reduction:** 2 empty directories → 0

---

## CATEGORY 6: Broken Code Fixes

### 6.1 Interface Broken Imports

**Current State:**
`interface/cli/bb5.py` imports:
```python
from infrastructure.main import get_blackbox5
```

But `infrastructure/` is empty (no main.py).

**Why This Exists:**
Code was written when infrastructure/ had content. After reorganization, infrastructure/ became empty but imports weren't updated.

**Consolidation Strategy:**
- Fix import to point to correct location
- Or remove the functionality if no longer needed
- Or delete bb5.py if it's replaced by newer CLI

**Reduction:** Fix 1 file

---

### 6.2 Connections Hook Broken Path

**Current State:**
`connections/hooks/active/github-auto-push.sh`:
```bash
source "${SCRIPT_DIR}/../../lib/paths.sh"
```

But `lib/` was moved to `helpers/`.

**Consolidation Strategy:**
- Fix path to `../../helpers/legacy/paths.sh` (if that's correct)
- Or delete hook if no longer used

**Reduction:** Fix or delete 1 file

---

### 6.3 Broken Executable Stubs

**Current State:**
Three executables are bash stubs:
- `executables/scout-intelligent.py`
- `executables/improvement-loop.py`
- `executables/planner-prioritize.py`

Each contains:
```bash
#!/bin/bash
exec python3 /Users/shaansisodia/.blackbox5/5-project-memory/blackbox5/.autonomous/bin/[script].py "$@"
```

But those paths may not exist.

**Why They Exist:**
Attempt to wrap project-memory scripts as engine executables.

**Consolidation Strategy:**
- Verify if target scripts exist
- If yes: fix paths or create proper Python wrappers
- If no: delete the stubs

**Reduction:** 3 broken stubs → 0 or 3 working wrappers

---

## CATEGORY 7: Test Organization

### 7.1 Safety Tests in Wrong Place

**Current State:**
- `safety/tests/` contains test files
- `tests/` is the main test directory

**Why This Exists:**
Safety tests were kept with safety code for proximity.

**Why This Is Wrong:**
- Tests scattered across codebase
- pytest expects tests in one location (or configured multiple)
- `safety/tests/` has nested structure: `safety/tests/blackbox5/2-engine/01-core/safety/` (crazy deep)

**Consolidation Strategy:**
- Move `safety/tests/test_*.py` to `tests/unit/safety/`
- Move `safety/tests/.pytest_cache/` to `.gitignore`
- Delete deeply nested artifact directories

**Reduction:** Consolidate test locations

---

### 7.2 Legacy Tests

**Current State:**
7 test files in `helpers/legacy/`:
- `test_decision_registry.py`
- `test_memory.py`
- `test_session_tracker.py`
- `test_state_machine.py`
- `test_workspace.py`
- `test_paths.py`
- `test_workflow_loader.py`

**Consolidation Strategy:**
- If testing legacy code that we're keeping: move to `tests/unit/legacy/`
- If testing legacy code that we're deleting: delete tests too

**Reduction:** Move or delete 7 files

---

## CATEGORY 8: Documentation Consolidation

### 8.1 Completion Reports

**Current State:**
- `documentation/completions/` - 14 completion report files

**Why They Exist:**
Historical record of completed phases.

**Why This Is Wrong:**
- 14 files = clutter
- Historical records belong in project memory, not active engine
- Git history already tracks what was completed when

**Consolidation Strategy:**
- Move to `5-project-memory/blackbox5/documentation/completions/`
- Or consolidate into single `COMPLETIONS.md` summary
- Or delete (git has the history)

**Reduction:** 14 files → 1 file or 0 files

---

### 8.2 Design Docs in Code Directories

**Current State:**
- `interface/INTEGRATION-IDEAS.md`
- `interface/AGENT-OUTPUT-BUS-DESIGN.md`

**Consolidation Strategy:**
- Move to `documentation/design/` or `1-docs/engine/design/`

**Reduction:** Move 2 files

---

## Summary Table

| Category | Current | After | Savings |
|----------|---------|-------|---------|
| **Duplicate Prompts** | 15 files | 5 files | 10 files |
| **Outdated Versions** | 12 dirs | 6 dirs | 6 dirs |
| **Small Directories** | 3 dirs (8 files) | 1 dir (3 files) | 5 files |
| **Git Helpers** | 3 files | 1 file | 2 files |
| **Legacy Helpers** | 38 files | 10 files | 28 files |
| **Empty Directories** | 20+ dirs | 0 dirs | 20+ dirs |
| **Deprecated Configs** | 7 files | 0 files | 7 files |
| **Empty/Placeholder** | 2 dirs | 0 dirs | 2 dirs |
| **Duplicate Coordinator** | 2 files | 1 file | 1 file |
| **Research Overlap** | 3 files | 2 files | 1 file |
| **Documentation** | 14 files | 1 file | 13 files |
| **Broken Stubs** | 3 files | 0 files | 3 files |
| **Test Organization** | 7 files | consolidated | 7 files |
| **TOTAL ESTIMATED** | **~522 files** | **~250-300 files** | **~220-270 files** |

---

## Implementation Order

### Phase 1: Fix Broken (High Risk)
1. Fix `helpers/core/registry.py` imports
2. Fix `helpers/integrations/vibe/__init__.py` import
3. Fix or delete broken executable stubs (3 files)
4. Fix `interface/cli/bb5.py` imports
5. Fix or delete broken hook script

### Phase 2: Delete Empty (Low Risk)
6. Delete empty `config/` directory
7. Delete empty `mcp/` directory
8. Delete empty `infrastructure/` directory
9. Delete empty `agents/runtime/` directory
10. Delete empty `agents/definitions/improvement/` directory
11. Delete 14 empty hook version directories
12. Delete empty documentation directories

### Phase 3: Archive Outdated (Medium Risk)
13. Archive v1 and v2 prompt versions
14. Archive root ralf-*.md files
15. Archive system/*-identity.md files
16. Delete deprecated config files (verify no imports first)

### Phase 4: Consolidate (Medium Risk)
17. Merge 3 scout prompts → 1
18. Merge 3 git helpers → 1
19. Merge procedures/, context/, exit/ → guides/
20. Move workflow YAMLs to workflows/definitions/
21. Delete coordinator shell script
22. Merge research-specialist into AnalystAgent

### Phase 5: Move/Organize (Low Risk)
23. Move design docs to documentation/
24. Move completion reports to project memory
25. Move safety tests to tests/
26. Move legacy tests to tests/ or delete
27. Consolidate MCP config locations

### Phase 6: Rename (Low Risk)
28. Rename directories for clarity (bmad → analysis-framework, etc.)

---

## Risk Assessment

| Action | Risk | Mitigation |
|--------|------|------------|
| Delete files | Medium | Check imports first with grep |
| Archive prompts | Low | Git history preserves them |
| Merge helpers | Medium | Run tests after merge |
| Move directories | Low | Update any hardcoded paths |
| Fix imports | Low | Verify imports work after fix |

---

## Verification Steps

After each phase:
1. Run `find . -type f -name "*.py" | xargs grep "from.*import" | grep -v "__pycache__"` to check imports
2. Run `python -m py_compile` on modified Python files
3. Run pytest to verify tests still pass
4. Check for broken symlinks: `find . -type l ! -exec test -e {} \; -print`
