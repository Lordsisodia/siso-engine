# Unified Configuration Migration Guide

**Version:** 2.0.0
**Date:** 2026-02-06
**Task:** TASK-ARCH-016

---

## Overview

The BlackBox5 configuration system has been unified from 20+ scattered config files into a single hierarchical system with 5 core files.

### Before (20+ files)
- `config_manager.py` - Runtime config loading
- `default.yaml` - RALF defaults
- `base.yaml` - Base defaults (separate from RALF)
- `api-config.yaml` - API Gateway config
- `cli-config.yaml` - CLI settings
- `github-config.yaml` - GitHub integration
- `alert-config.yaml` - Alert thresholds
- `code-review-config.yaml` - Code review settings
- `skill-registry.yaml` - Skill definitions
- `routes.yaml` (multiple) - Routing configs
- Multiple `skill-usage.yaml` files
- And more...

### After (5 files)
1. `base.yaml` - Base defaults (lowest precedence)
2. `engine.yaml` - Engine-specific overrides
3. `project.yaml` - Project-specific overrides
4. `user.yaml` - User-specific overrides
5. `schema.yaml` - Validation schema

---

## Configuration Hierarchy

Configuration is loaded in this order (highest to lowest precedence):

```
1. Environment Variables (deployment-specific)
2. User Config (~/.blackbox5/config/user.yaml)
3. Project Config (5-project-memory/[project]/.autonomous/config/project.yaml)
4. Engine Config (2-engine/.autonomous/config/engine.yaml)
5. Base Defaults (2-engine/.autonomous/config/base.yaml)
```

Each level overrides the previous one.

---

## Quick Start

### For Users

1. **Create user config** (optional):
   ```bash
   mkdir -p ~/.blackbox5/config
   cp ~/.blackbox5/2-engine/.autonomous/config/base.yaml ~/.blackbox5/config/user.yaml
   ```

2. **Edit user.yaml** with your preferences:
   ```yaml
   system:
     log_level: "DEBUG"

   cli:
     editor:
       default: "code"
   ```

3. **Use environment variables** for deployment-specific values:
   ```bash
   export BB5_LOG_LEVEL=DEBUG
   export GITHUB_TOKEN=ghp_xxx
   ```

### For Developers

1. **Import the unified config**:
   ```python
   from unified_config import get_config, get_path_resolver

   config = get_config()
   log_level = config.get('system.log_level')
   ```

2. **Resolve paths** without hardcoding:
   ```python
   resolver = get_path_resolver()
   engine_path = resolver.engine_root
   project_path = resolver.get_project_path('myproject')
   ```

---

## Migration Examples

### Python Code Migration

#### Old Way (Deprecated)
```python
from config_manager import get_config

config = get_config()
value = config.get('thresholds.skill_invocation_confidence')
```

#### New Way
```python
from unified_config import get_config

config = get_config()
value = config.get('thresholds.skill_invocation_confidence')
```

### Hardcoded Path Migration

#### Old Way
```python
import os

project_dir = os.path.expanduser("~/.blackbox5/5-project-memory/blackbox5")
```

#### New Way
```python
import os
from unified_config import get_path_resolver

# Option 1: Use path resolver
resolver = get_path_resolver()
project_dir = resolver.get_project_path('blackbox5')

# Option 2: Use environment variable
project_dir = os.environ.get('BB5_PROJECT_DIR', os.path.expanduser('~/.blackbox5/5-project-memory/blackbox5'))
```

### Shell Script Migration

#### Old Way
```bash
PROJECT_DIR="$HOME/.blackbox5/5-project-memory/blackbox5"
```

#### New Way
```bash
PROJECT_DIR="${BB5_PROJECT_DIR:-$HOME/.blackbox5/5-project-memory/blackbox5}"
```

---

## Environment Variables

The unified config recognizes these environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `BLACKBOX5_HOME` | BlackBox5 root directory | `~/.blackbox5` |
| `BB5_HOME` | Alias for BLACKBOX5_HOME | `~/.blackbox5` |
| `BB5_PROJECT` | Current project name | `blackbox5` |
| `BB5_PROJECT_ROOT` | Project root path | `~/.blackbox5/5-project-memory/blackbox5` |
| `BB5_ENGINE_ROOT` | Engine root path | `~/.blackbox5/2-engine` |
| `BB5_LOG_LEVEL` | Logging level | `DEBUG` |
| `BB5_DEBUG` | Enable debug mode | `true` |
| `GITHUB_TOKEN` | GitHub API token | `ghp_xxx` |
| `SLACK_WEBHOOK_URL` | Slack webhook | `https://hooks.slack.com/...` |

---

## Configuration Schema

All configuration values are validated against `schema.yaml`. Common types:

- `string` - Text values
- `int` - Integer values
- `bool` - Boolean (true/false)
- `list` - Array values
- `dict` - Nested objects

### Validation Rules

- `required: true` - Field must be present
- `default` - Default value if not specified
- `pattern` - Regex pattern for validation
- `min`/`max` - Numeric range limits

---

## Backward Compatibility

The old `config_manager.py` has been updated to delegate to `unified_config.py`:

- Existing code using `config_manager` will continue to work
- A deprecation warning is issued
- All methods are mapped to the new unified config

### Deprecation Timeline

- **Now:** Both systems work, deprecation warning shown
- **v2.1:** ConfigManager enters maintenance mode
- **v3.0:** ConfigManager removed (breaking change)

---

## Consolidated Configs

The following configs have been consolidated into the unified system:

| Old Config | New Location | Notes |
|------------|--------------|-------|
| `default.yaml` | `base.yaml` | Merged into unified base |
| `api-config.yaml` | `base.yaml` under `api:` | Consolidated |
| `cli-config.yaml` | `base.yaml` under `cli:` | Consolidated |
| `github-config.yaml` | `base.yaml` under `integrations.github:` | Consolidated |
| `alert-config.yaml` | `base.yaml` under `alerts:` | Consolidated |
| `code-review-config.yaml` | `base.yaml` under `code_review:` | Consolidated |
| `skill-registry.yaml` | `base.yaml` under `skills:` | Consolidated |
| `routes.yaml` | `base.yaml` under `routing:` | Consolidated |
| Multiple `skill-usage.yaml` | Single location | Deduplicated |

---

## Troubleshooting

### Config not loading

Check that config files exist:
```bash
ls -la ~/.blackbox5/config/user.yaml
ls -la ~/.blackbox5/2-engine/.autonomous/config/base.yaml
```

### Environment variables not applying

Verify variable names match exactly (case-sensitive):
```bash
echo $BB5_LOG_LEVEL
echo $GITHUB_TOKEN
```

### Validation errors

Check `schema.yaml` for valid values:
```bash
cat ~/.blackbox5/2-engine/.autonomous/config/schema.yaml
```

### Path resolution issues

Test path resolution:
```python
from unified_config import get_path_resolver
resolver = get_path_resolver()
print(f"Engine: {resolver.engine_root}")
print(f"Memory: {resolver.memory_root}")
```

---

## Files Created/Modified

### New Files
- `2-engine/.autonomous/lib/unified_config.py` - New config manager
- `2-engine/.autonomous/config/engine.yaml` - Engine config
- `2-engine/.autonomous/config/schema.yaml` - Validation schema
- `5-project-memory/blackbox5/.autonomous/config/project.yaml` - Project config
- `~/.blackbox5/config/user.yaml` - User config

### Modified Files
- `2-engine/.autonomous/lib/config_manager.py` - Now delegates to unified_config
- `2-engine/.autonomous/config/base.yaml` - Consolidated all base config

### Deprecated (but preserved)
- `2-engine/.autonomous/config/default.yaml` - Use base.yaml
- `2-engine/.autonomous/config/api-config.yaml` - Use base.yaml
- `2-engine/.autonomous/config/cli-config.yaml` - Use base.yaml
- `2-engine/.autonomous/config/github-config.yaml` - Use base.yaml
- `2-engine/.autonomous/config/alert-config.yaml` - Use base.yaml
- `2-engine/.autonomous/config/code-review-config.yaml` - Use base.yaml

---

## Success Criteria Checklist

- [x] Single unified config hierarchy implemented
- [x] All 20+ config files consolidated to 5 or fewer
- [x] Zero hardcoded paths (all use config)
- [x] Config validation enforced at load time
- [x] Environment variable override works
- [x] Backward compatibility maintained
- [x] Migration guide documented
- [x] All tests pass

---

## Support

For issues or questions:
1. Check this migration guide
2. Review the unified config source: `2-engine/.autonomous/lib/unified_config.py`
3. Examine the schema: `2-engine/.autonomous/config/schema.yaml`
4. Test with: `python3 2-engine/.autonomous/lib/unified_config.py`
