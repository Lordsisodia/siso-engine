# Infrastructure

System initialization and main entry point for BlackBox5.

## Overview

This module provides the singleton `BlackBox5` class that initializes and manages core system components including agents, skill managers, and guide registries.

## Files

| File | Purpose |
|------|---------|
| `main.py` | Core BlackBox5 class with initialization and request processing |
| `__init__.py` | Module initialization |

## Key Components

### BlackBox5 Class

The main system interface that provides:
- Agent management and loading
- Skill manager initialization
- Guide registry setup
- Request processing with routing
- Async/await pattern for non-blocking operations

## Usage

```python
from infrastructure.main import get_blackbox5

# Get singleton instance
bb5 = await get_blackbox5()

# Process a request
result = await bb5.process_request(
    query="Your task here",
    session_id="optional-session-id",
    context={"strategy": "auto"}
)
```

## Architecture

```
┌─────────────────────────────────────┐
│           BlackBox5                 │
│  ┌─────────┐  ┌─────────┐          │
│  │ Agents  │  │ Skills  │          │
│  └─────────┘  └─────────┘          │
│  ┌─────────┐  ┌─────────┐          │
│  │ Guides  │  │ Router  │          │
│  └─────────┘  └─────────┘          │
└─────────────────────────────────────┘
```

## Initialization Flow

1. **Load Configuration** - Read agent-config.yaml
2. **Initialize Agent Loader** - Load all available agents
3. **Setup Skill Manager** - Initialize composable skills
4. **Create Guide Registry** - Load guides and documentation
5. **Mark as Ready** - System is ready to process requests

## Configuration

Configuration is loaded from `../config/agent-config.yaml`:
```yaml
agents:
  default: "developer"
  available:
    - developer
    - architect
    - tester

skills:
  auto_load: true
  paths:
    - "../modules/skills"
```

## Related

- [Agents](../agents/) - Agent definitions
- [Configuration](../configuration/) - System configuration
- [Interface](../interface/) - CLI and API interfaces
