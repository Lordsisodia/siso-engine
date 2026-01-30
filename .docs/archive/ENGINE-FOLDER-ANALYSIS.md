# Engine Folder Analysis - Complete Overview

## Overview of All Engine Folders

```
2-engine/
├── 01-core/          # 84 files   - Core behaviors and infrastructure
├── 02-agents/        # 460 files  - Agent implementations (LARGEST)
├── 03-knowledge/     # 160 files  - Knowledge systems and memory
├── 04-work/          # 161 files  - Work definitions and workflows
├── 05-tools/         # 25 files   - Tool primitives
├── 06-integrations/  # 76 files   - External integrations
├── 07-operations/    # 668 files  - Runtime and scripts (LARGEST)
├── 08-development/   # 110 files  - Tests and development tools
└── README.md
```

**Total**: 1,744 files across 8 categories

---

## 01-core/ - Core Behaviors (84 files)

### Purpose: WHAT the system does (system-level behaviors)

### Structure:
```
01-core/
├── client/              # Agent client implementation
├── communication/       # Communication protocols
├── infrastructure/      # Infrastructure components
├── interface/           # User/agent interfaces
│   ├── api/            # REST API (server.py, main.py)
│   ├── cli/            # CLI commands (bb5.py, prd_commands.py, epic_commands.py, task_commands.py, github_commands.py)
│   ├── integrations/   # Integration interfaces
│   └── spec_driven/    # Spec-driven agents (prd_agent.py, epic_agent.py, task_agent.py)
├── middleware/          # Middleware components
│   ├── token_compressor.py
│   ├── context_extractor.py
│   └── guide_middleware.py
├── orchestration/      # Orchestration logic
│   ├── Orchestrator.py
│   └── orchestrator_deviation_integration.py
├── pipeline/           # Pipeline implementations
│   ├── bb5-pipeline.py
│   ├── unified_pipeline.py
│   ├── feature_pipeline.py
│   └── testing_pipeline.py
├── resilience/         # Resilience patterns
│   ├── circuit_breaker.py
│   ├── circuit_breaker_types.py
│   ├── atomic_commit_manager.py
│   └── anti_pattern_detector.py
├── routing/            # Task routing
│   └── task_router_examples.py
├── state/              # State management
│   ├── state_manager.py
│   └── state_manager_demo.py
└── tracking/           # Tracking and monitoring
    ├── todo_manager.py
    ├── manifest.py
    └── deviation_handler.py
```

### Analysis:
- ✅ **Correct placement**: All core system behaviors
- ✅ **Clean structure**: Well-organized by function
- ✅ **No duplicates**: Each component has clear purpose
- ⚠️ **Note**: `interface/` contains both API and CLI - this is correct (both are interfaces)

---

## 02-agents/ - Agent Implementations (460 files)

### Purpose: WHO does the work

### Structure:
```
02-agents/
├── capabilities/        # What agents CAN do (skills)
│   ├── .skills-new/    # New skills system
│   ├── skills-cap/     # Skills capabilities
│   └── workflows-cap/  # Workflow capabilities
├── implementations/     # Agent implementations
│   ├── 01-core/
│   │   └── 1-core/     # Nested! (see below)
│   ├── 02-bmad/
│   ├── 03-research/
│   ├── 04-specialists/
│   ├── 05-enhanced/
│   └── custom/
└── legacy-skills/       # Legacy skills (should be deleted?)
    ├── verify/
    └── workflow/
```

### Nested Structure Issue:
```
implementations/01-core/1-core/
├── classification-options/
├── manager/
├── orchestrator/
├── prompt.md
├── README.md
├── review-verification/
├── selection-planner/
└── templates/
```

### Analysis:
- ❌ **CRITICAL**: Double nesting: `implementations/01-core/1-core/`
- ❌ **ISSUE**: Why both `01-core` (numbered) and `1-core` (nested)?
- ❌ **ISSUE**: `legacy-skills/` - is this deprecated? Should it be deleted?
- ⚠️ **Question**: Are `.skills-new/` and `skills-cap/` duplicates?

---

## 03-knowledge/ - Knowledge Systems (160 files)

### Purpose: WHAT agents know

### Structure:
```
03-knowledge/
├── guides/             # Step-by-step instructions
│   └── guides/        # Nested! (see below)
├── memory/             # Short-term memory
│   └── memory/        # Nested! (see below)
├── schemas/            # Data structures
│   └── schemas/       # Nested! (see below)
├── semantic/           # Semantic search (empty)
└── storage/            # Long-term storage
    ├── brain/         # Knowledge storage infrastructure
    │   ├── api/
    │   ├── databases/ # Docker configs for Neo4j/PostgreSQL
    │   ├── ingest/
    │   ├── metadata/
    │   └── query/
    ├── consolidation/  # Memory consolidation
    ├── episodic/       # Episodic memory
    ├── importance/     # Importance scoring
    ├── tests/          # Memory tests
    ├── EnhancedProductionMemorySystem.py
    ├── ProductionMemorySystem.py
    └── validate_production.py
```

### Nested Structures:
```
guides/guides/
memory/memory/
schemas/schemas/
```

### Analysis:
- ❌ **CRITICAL**: Triple nesting in multiple folders
- ✅ **storage/brain/` - Contains infrastructure (Docker, SQL schemas) - should this be in engine or project memory?
- ⚠️ **semantic/** - Empty folder, prepared for future use
- ✅ **Memory implementations** correctly placed here

---

## 04-work/ - Work Definitions (161 files)

### Purpose: WHAT agents work on

### Structure:
```
04-work/
├── frameworks/         # Framework definitions
│   └── frameworks/    # Nested!
├── modules/            # Work modules
│   └── modules/       # Nested!
├── planning/           # Planning system
├── tasks/              # Task management
│   └── task_management/
└── workflows/          # Workflow definitions
```

### Analysis:
- ❌ **ISSUE**: Double nesting: `frameworks/frameworks/`, `modules/modules/`
- ⚠️ **Question**: What's the difference between `frameworks/` and `modules/`?

---

## 05-tools/ - Tool Primitives (25 files)

### Purpose: Building blocks for agents

### Structure:
```
05-tools/
└── tools/
    ├── data_tools/    # Data manipulation tools
    ├── maintenance/   # Maintenance tools
    ├── migration/     # Migration tools
    ├── tools/         # Nested! (see below)
    └── validation/    # Validation tools
```

### Analysis:
- ❌ **ISSUE**: Double nesting: `tools/tools/`
- ✅ **Small and focused**: Only 25 files, well-scoped

---

## 06-integrations/ - External Integrations (76 files)

### Purpose: WHAT we can connect to

### Structure:
```
06-integrations/
├── _template/         # Integration template
│   └── tests/
├── cloudflare/        # Cloudflare integration
│   └── tests/
├── github/            # GitHub integration
├── github-actions/    # GitHub Actions integration
├── mcp/               # MCP integration
├── notion/            # Notion integration
│   └── tests/
├── obsidian/          # Obsidian integration
│   └── tests/
├── supabase/          # Supabase integration
│   └── tests/
├── vercel/            # Vercel integration
└── vibe/              # Vibe integration
```

### Analysis:
- ✅ **Clean structure**: Each integration is self-contained
- ✅ **Consistent**: Each has tests/ folder
- ✅ **Template system**: `_template/` for new integrations
- ✅ **No duplicates**: Clear separation of concerns

---

## 07-operations/ - Runtime & Scripts (668 files - LARGEST)

### Purpose: HOW we run things

### Structure:
```
07-operations/
├── runtime/           # Runtime scripts and data
│   └── runtime/       # Nested! (LARGEST: 141 shell scripts, 122 Python files)
│       ├── agents/    # Agent management scripts
│       ├── hooks/     # Git hooks
│       ├── integration/ # Integration scripts
│       ├── integrations/ # More integration scripts
│       ├── *.sh       # 141 shell scripts total
│       └── *.py       # 122 Python files
└── scripts/           # Utility scripts
    ├── tools/         # Tool scripts
    └── utility-scripts/ # Utility scripts
```

### Analysis:
- ❌ **CRITICAL**: Double nesting: `runtime/runtime/`
- ❌ **ISSUE**: This folder is MASSIVE (668 files) - too large?
- ❌ **ISSUE**: Mix of scripts and runtime data
- ❌ **ISSUE**: `integration/` and `integrations/` - duplicates?
- ⚠️ **Question**: Should runtime data be in project memory, not engine?

### Files in runtime/runtime/ (sample):
- `agent-status.sh`
- `analyze-response.sh`
- `autonomous-loop.sh`
- `autonomous-run.sh`
- `circuit-breaker.sh`
- `generate-prd.sh`
- `intervene.sh`
- Plus 130+ more scripts

---

## 08-development/ - Tests & Development (110 files)

### Purpose: Verification and development tools

### Structure:
```
08-development/
├── api/               # API documentation/examples
│   └── api/
├── development-tools/  # Development tools
│   ├── examples/      # Example specs
│   │   └── specs/prds/
│   ├── framework-research/ # Framework research
│   ├── frameworks/    # Framework templates (bmad, speckit, metagpt, swarm)
│   ├── scripts/       # Development scripts
│   ├── templates/     # General templates
│   │   ├── general/github/
│   │   └── specs/ (epics, prds, tasks)
│   └── tests/         # Test suite
│       ├── .pytest_cache/ # ← Should be deleted!
│       ├── integrations/
│       ├── spec_driven/
│       └── test_*.py  # 20+ test files
├── examples/          # More examples
└── tests/             # More tests
    ├── numbers/       # Numbered tests (10+ test files)
    │   └── test_*.py
    └── test_*.py      # Additional test files
```

### Analysis:
- ❌ **CRITICAL**: Double nesting: `api/api/`
- ❌ **ISSUE**: Multiple test locations: `tests/`, `development-tools/tests/`
- ❌ **ISSUE**: `.pytest_cache/` should be in .gitignore
- ❌ **ISSUE**: `frameworks/` - is this development or work definitions?
- ⚠️ **Question**: Should framework research be in roadmap?

---

## Critical Issues Found:

### 1. **Systematic Double Nesting**
Multiple folders have nested structures with same names:
- `02-agents/implementations/01-core/1-core/`
- `03-knowledge/guides/guides/`
- `03-knowledge/memory/memory/`
- `03-knowledge/schemas/schemas/`
- `04-work/frameworks/frameworks/`
- `04-work/modules/modules/`
- `05-tools/tools/tools/`
- `07-operations/runtime/runtime/`
- `08-development/api/api/`

### 2. **Duplicate Test Locations**
Tests scattered across multiple locations:
- `08-development/tests/`
- `08-development/development-tools/tests/`
- `03-knowledge/storage/tests/`

### 3. **Massive Folder Size**
- `07-operations/` has 668 files (too large?)
- `02-agents/` has 460 files

### 4. **Legacy Code**
- `02-agents/legacy-skills/` - should this be deleted?

### 5. **Potential Duplicates**
- `07-operations/runtime/runtime/integration/` vs `integrations/`
- `02-agents/.skills-new/` vs `skills-cap/`

---

## Recommendations:

### High Priority:
1. **Fix double nesting** - Remove redundant nested folders
2. **Consolidate tests** - Single location for all tests
3. **Clean 07-operations** - Separate scripts from runtime data
4. **Remove .pytest_cache** - Add to .gitignore

### Medium Priority:
1. **Review legacy-skills** - Delete if deprecated
2. **Check skill duplicates** - Merge if needed
3. **Review framework placement** - Should be in 04-work/ or roadmap?

### Low Priority:
1. **Review brain folder** - Infrastructure vs project-specific
2. **Consolidate integration folders** - Merge duplicates

---

## Next Steps:

1. Fix double nesting in all folders
2. Consolidate test locations
3. Clean up 07-operations
4. Review legacy code for deletion
