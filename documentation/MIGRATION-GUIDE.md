# BlackBox5 Engine Migration Guide

**For developers migrating from the old 2-engine structure**

---

## Overview

### What Changed

The 2-engine directory was reorganized from 10,234+ files of mixed legacy/active code to a clean, purpose-based structure with approximately 522 files.

**Key improvements:**
- Clear purpose-based directory naming
- Unified agent framework (consolidated from 3 parallel systems)
- Separation of engine code from project-specific data
- Removed deprecated and duplicate code

### Why It Changed

1. **Technical debt accumulation** - Years of legacy files mixed with active code
2. **Confusing structure** - Multiple naming conventions (lib/, core/, .autonomous/)
3. **Duplicate systems** - 3 different agent implementations in parallel
4. **Mixed concerns** - Runtime data stored with engine code

### Timeline

| Date | Milestone |
|------|-----------|
| 2026-02-07 | Reorganization completed |
| 2026-02-07 | New structure active in main branch |
| 2026-02-07 | Migration guide published |

---

## Path Changes

### Directory Mapping

| Old Path | New Path | Notes |
|----------|----------|-------|
| `.autonomous/bin/` | `executables/` | CLI tools and agent scripts |
| `core/agents/definitions/` | `agents/definitions/` | Agent type definitions |
| `core/agents/framework/` | `agents/framework/` | BaseAgent, loader, skills |
| `lib/` | `helpers/` | Shared utility libraries |
| `prompts/` | `instructions/` | Agent prompts and instructions |
| `config/` | `configuration/` | System and agent configuration |
| `runtime/memory/` | `5-project-memory/blackbox5/data/` | Runtime data, brain, episodes |
| `core/orchestration/` | `workflows/` | Workflow definitions |
| `mcp/` | `connections/` | External service connections |
| `tools/` | `helpers/integrations/` | Integration utilities |

### File Location Examples

| Old Location | New Location |
|--------------|--------------|
| `.autonomous/bin/executor-implement.py` | `executables/executor-implement.py` |
| `.autonomous/bin/scout-analyze.py` | `executables/scout-analyze.py` |
| `core/agents/definitions/architect/` | `agents/definitions/architect/` |
| `lib/alert_manager.py` | `helpers/integrations/alert_manager.py` |
| `lib/log_ingestor.py` | `helpers/core/log_ingestor.py` |
| `prompts/agents/executor.md` | `instructions/agents/executor.md` |
| `config/agents/` | `configuration/agents/` |
| `runtime/memory/brain/` | `5-project-memory/blackbox5/data/brain/` |
| `runtime/memory/episodes/` | `5-project-memory/blackbox5/data/episodes/` |

---

## Import Updates

### Python Import Changes

#### Agent Imports

```python
# OLD
from core.agents.definitions.architect import ArchitectAgent
from core.agents.framework import BaseAgent

# NEW
from agents.definitions.architect import ArchitectAgent
from agents.framework import BaseAgent
```

#### Helper/Library Imports

```python
# OLD
from lib.alert_manager import AlertManager
from lib.log_ingestor import LogIngestor
from lib.metrics_collector import MetricsCollector

# NEW
from helpers.integrations.alert_manager import AlertManager
from helpers.core.log_ingestor import LogIngestor
from helpers.core.metrics_collector import MetricsCollector
```

#### Configuration Imports

```python
# OLD
from config.agents.executor import ExecutorConfig
from config.system.settings import SystemSettings

# NEW
from configuration.agents.executor import ExecutorConfig
from configuration.system.settings import SystemSettings
```

### Shell Script Path Updates

```bash
# OLD
source "$ENGINE_ROOT/lib/ralf_hooks.sh"
python3 "$ENGINE_ROOT/.autonomous/bin/executor-implement.py"

# NEW
source "$ENGINE_ROOT/helpers/legacy/ralf_hooks.sh"
python3 "$ENGINE_ROOT/executables/executor-implement.py"
```

### Configuration File References

```yaml
# OLD
prompt_path: "prompts/agents/executor.md"
config_path: "config/agents/executor.yaml"

# NEW
prompt_path: "instructions/agents/executor.md"
config_path: "configuration/agents/executor.yaml"
```

---

## Breaking Changes

### Deleted Directories

The following directories have been completely removed:

| Directory | Replacement | Action Required |
|-----------|-------------|-----------------|
| `.autonomous/` (9,500+ files) | `executables/`, `agents/` | Update all references |
| `core/` (consolidated) | `agents/`, `helpers/` | Update imports |
| `runtime/` | `5-project-memory/blackbox5/data/` | Update data paths |
| `tools/` | `helpers/integrations/` | Update imports |
| `02-agents/` (duplicate) | `agents/` | Remove references |
| `.config/` (temp) | `configuration/` | Update references |
| `.docs/` (temp) | `documentation/` | Update references |

### Consolidated Modules

| Old Modules | New Module | Notes |
|-------------|------------|-------|
| `agents/improvement-scout.md` | `instructions/agents/scout.md` | Single scout with mode parameter |
| `agents/intelligent-scout.md` | `instructions/agents/scout.md` | Consolidated |
| `ralf-scout-improve.md` | `instructions/agents/scout.md` | Consolidated |
| `system/identity.md` | Embedded in versioned prompts | Identity now built-in |
| `system/planner-identity.md` | Embedded in `instructions/planner/` | Identity now built-in |
| `system/executor-identity.md` | Embedded in `instructions/executor/` | Identity now built-in |

### Renamed Files

| Old Name | New Name | Location |
|----------|----------|----------|
| `bin/bb5` | `bb5` | `executables/` |
| `bin/ralf` | `ralf` | `executables/` |
| `lib/ralf_hooks.sh` | `ralf_hooks.sh` | `helpers/legacy/` |
| `ralf.md` (root) | Archived | `instructions/archive/` |
| `ralf-executor.md` (root) | Archived | `instructions/archive/` |

### Agent System Changes

**Before:** 3 parallel agent systems
- `core/agents/definitions/` - Framework with BaseAgent
- `core/autonomous/agents/` - Redis-based runtime
- `.autonomous/bin/` - Standalone scripts

**After:** 1 unified system
- `agents/framework/` - BaseAgent, agent_loader, skill_manager
- `agents/definitions/` - All agent definitions
- `executables/` - Refactored scripts using BaseAgent

**Migration:** Scripts using old standalone approach need to inherit from BaseAgent.

---

## Quick Reference

### Where to Find Common Components

| Component | New Location |
|-----------|--------------|
| **Agent definitions** | `agents/definitions/[agent-type]/` |
| **BaseAgent framework** | `agents/framework/` |
| **Agent prompts** | `instructions/agents/` |
| **Agent configuration** | `configuration/agents/` |
| **CLI executables** | `executables/` |
| **Core helpers** | `helpers/core/` |
| **Git helpers** | `helpers/git/` |
| **Integration helpers** | `helpers/integrations/` |
| **Legacy helpers** | `helpers/legacy/` |
| **Workflow definitions** | `workflows/` |
| **MCP connections** | `connections/mcp/` |
| **System configuration** | `configuration/system/` |
| **Runtime data** | `5-project-memory/blackbox5/data/` |
| **Brain/memory state** | `5-project-memory/blackbox5/data/brain/` |
| **Episode storage** | `5-project-memory/blackbox5/data/episodes/` |
| **Vector embeddings** | `5-project-memory/blackbox5/data/embeddings/` |

### How to Update Existing Scripts

#### Step 1: Update Shebang and Imports

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script description
"""

# Update these imports
from agents.framework import BaseAgent  # Was: from core.agents.framework
from helpers.core.logging import get_logger  # Was: from lib.logging
from configuration.system import settings  # Was: from config.system
```

#### Step 2: Update File Paths

```python
import os

ENGINE_ROOT = os.path.expanduser("~/.blackbox5/2-engine")

# Update path references
EXECUTABLES_DIR = os.path.join(ENGINE_ROOT, "executables")  # Was: .autonomous/bin
INSTRUCTIONS_DIR = os.path.join(ENGINE_ROOT, "instructions")  # Was: prompts
HELPERS_DIR = os.path.join(ENGINE_ROOT, "helpers")  # Was: lib
```

#### Step 3: Update Configuration References

```yaml
# Update YAML configs
system:
  instructions_path: "instructions/agents/"  # Was: prompts/agents/
  helpers_path: "helpers/"  # Was: lib/
  executables_path: "executables/"  # Was: .autonomous/bin/
```

#### Step 4: Test the Migration

```bash
# Run the script to verify it works
python3 /Users/shaansisodia/.blackbox5/2-engine/executables/your-script.py

# Check for import errors
# Check for file not found errors
```

### Migration Checklist

- [ ] Identify all scripts using old paths
- [ ] Update Python imports (core.agents → agents, lib → helpers)
- [ ] Update shell script paths (.autonomous/bin → executables)
- [ ] Update configuration file references (config → configuration, prompts → instructions)
- [ ] Update runtime data paths (runtime/memory → 5-project-memory/blackbox5/data)
- [ ] Test each updated script
- [ ] Update documentation references
- [ ] Notify team members of changes

---

## Getting Help

### Resources

1. **Reorganization Summary**: `/Users/shaansisodia/.blackbox5/2-engine/REORGANIZATION_SUMMARY.md`
2. **Consolidation Analysis**: `/Users/shaansisodia/.blackbox5/2-engine/CONSOLIDATION_ANALYSIS.md`
3. **Detailed Plan**: `/Users/shaansisodia/.blackbox5/2-engine/CONSOLIDATION_PLAN_DETAILED.md`

### Directory Structure Reference

```
2-engine/
├── agents/              # Unified agent framework
│   ├── framework/       # BaseAgent, loader, skills
│   └── definitions/     # Agent definitions by type
├── helpers/             # Shared utilities
│   ├── core/            # Core helpers
│   ├── git/             # Git operations
│   ├── integrations/    # External service helpers
│   └── legacy/          # Legacy compatibility
├── configuration/       # System configuration
│   ├── agents/          # Agent configs
│   ├── mcp/             # MCP server configs
│   └── system/          # System-wide settings
├── instructions/        # Agent instructions
│   ├── agents/          # Agent-specific prompts
│   ├── system/          # System prompts
│   └── archive/         # Legacy prompts
├── workflows/           # Workflow definitions
├── connections/         # External integrations
├── interface/           # User interfaces
├── safety/              # Guardrails, validation
├── executables/         # CLI executables
├── documentation/       # Engine docs
├── tests/               # Test suite
├── infrastructure/      # Docker, deployment
├── modules/             # Optional modules
└── examples/            # Usage examples
```

---

## Version Information

- **Migration Guide Version**: 1.0
- **Effective Date**: 2026-02-07
- **Applies To**: BlackBox5 Engine 2.x
- **Last Updated**: 2026-02-07
