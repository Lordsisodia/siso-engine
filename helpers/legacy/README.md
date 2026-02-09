# Legacy Helpers (Deprecated)

> Deprecated utilities being migrated to the new structure

## WARNING

**This directory contains deprecated code.** Do not use for new development. These modules are being actively migrated to the new helper structure.

## Overview

The legacy/ directory contains older BlackBox5 utilities that are gradually being replaced by modern equivalents in `helpers/core/`, `helpers/git/`, and `helpers/integrations/`.

## Files

### Core Utilities

| File | Purpose | Status | Replacement |
|------|---------|--------|-------------|
| `paths.py` | Path resolution system | Deprecated | Use `helpers.core.registry` |
| `paths.sh` | Shell path utilities | Deprecated | Use Python path resolver |
| `memory.py` | File-based memory system | Deprecated | Use `2-engine/runtime/memory/` |
| `workspace.py` | Workspace management | Deprecated | Use new workspace module |

### Decision & State Management

| File | Purpose | Status | Replacement |
|------|---------|--------|-------------|
| `decision_registry.py` | Decision tracking with reversibility | Migrating | `helpers/core/decisions/` |
| `state_machine.py` | Task state transitions | Deprecated | Use task registry |
| `phase_gates.py` | Phase gate enforcement | Deprecated | Use new phase system |
| `context_budget.py` | Context window management | Deprecated | Integrated into core |

### Workflow & Routing

| File | Purpose | Status | Replacement |
|------|---------|--------|-------------|
| `skill_router.py` | Automatic skill routing | Active (Legacy) | Being refactored |
| `workflow_loader.py` | Workflow YAML loader | Deprecated | Use new workflow system |
| `generate_workflows.py` | Workflow generation | Deprecated | Use workflow templates |
| `roadmap_sync.py` | Roadmap state synchronization | Active (Legacy) | Being migrated |

### Monitoring & Metrics

| File | Purpose | Status | Replacement |
|------|---------|--------|-------------|
| `alert_manager.py` | Alert configuration and delivery | Deprecated | Use monitoring service |
| `anomaly_detector.py` | Performance anomaly detection | Deprecated | Use monitoring service |
| `metrics_collector.py` | Metrics collection | Deprecated | Use metrics service |
| `performance_reporter.py` | Performance reporting | Deprecated | Use reporting service |
| `historical_analyzer.py` | Historical data analysis | Deprecated | Use analytics service |
| `log_ingestor.py` | Log ingestion | Deprecated | Use logging service |
| `event_logger.py` | Event logging | Deprecated | Use event service |

### Session & Tracking

| File | Purpose | Status | Replacement |
|------|---------|--------|-------------|
| `session_tracker.py` | Session tracking | Deprecated | Use new tracking system |
| `unified_config.py` | Configuration management | Deprecated | Use config service |

### API & Integration

| File | Purpose | Status | Replacement |
|------|---------|--------|-------------|
| `api_server.py` | Legacy API server | Deprecated | Use new API gateway |
| `api_auth.py` | API authentication | Deprecated | Use auth service |
| `webhook_receiver.py` | Webhook handling | Deprecated | Use webhook service |
| `integration_test.py` | Integration testing | Deprecated | Use test framework |

### Connectors Directory

| File | Purpose | Status | Replacement |
|------|---------|--------|-------------|
| `connectors/base_connector.py` | Base connector class | Deprecated | Use `helpers/integrations/` |
| `connectors/slack_connector.py` | Slack integration | Deprecated | Use `helpers/integrations/slack/` |
| `connectors/jira_connector.py` | Jira integration | Deprecated | Use `helpers/integrations/jira/` |
| `connectors/trello_connector.py` | Trello integration | Deprecated | Use `helpers/integrations/trello/` |

### Testing

| File | Purpose | Status |
|------|---------|--------|
| `test_*.py` | Unit tests for legacy modules | Deprecated |

### Scripts

| File | Purpose | Status |
|------|---------|--------|
| `dry_run.sh` | Dry run testing script | Deprecated |
| `ralf_hooks.sh` | RALF hook utilities | Deprecated |

## Migration Guide

### Path Resolution

**Old (Legacy):**
```python
from helpers.legacy.paths import get_path_resolver
resolver = get_path_resolver()
path = resolver.get_project_path()
```

**New:**
```python
from helpers.core.registry import ToolRegistry
# Use registry-based path resolution
```

### Git Operations

**Old (Legacy):**
```python
# Legacy git utilities were scattered
```

**New:**
```python
from helpers.git.git_ops import GitOps
git = GitOps()
git.create_commit(message="Update", type_="feat")
```

### Memory System

**Old (Legacy):**
```python
from helpers.legacy.memory import MemorySystem
memory = MemorySystem()
memory.save_decision("key", data)
```

**New:**
```python
# Use 2-engine/runtime/memory/ extended memory system
```

### Connectors

**Old (Legacy):**
```python
from helpers.legacy.connectors.slack_connector import SlackConnector
```

**New:**
```python
from helpers.integrations.slack import SlackHelper
```

## Active Legacy Components

Some components are still actively used during migration:

### skill_router.py
Still used for automatic skill routing based on task keywords. Routes to BMAD skills (pm, architect, analyst, etc.).

### roadmap_sync.py
Synchronizes roadmap STATE.yaml when tasks complete. Updates plan status and unblocks dependencies.

## Development Guidelines

1. **Do not add new code here** - Use the new structure in `helpers/core/`, `helpers/git/`, or `helpers/integrations/`
2. **Do not import from here in new code** - Use modern equivalents
3. **Migrate when touching legacy code** - Move functionality to new structure
4. **Maintain backwards compatibility** - When migrating, keep old imports working temporarily

## Related

- [Core Helpers](../core/) - Modern base utilities
- [Git Helpers](../git/) - Modern git operations
- [Integrations](../integrations/) - Modern service connectors
- [Engine Root](../../) - Parent directory
