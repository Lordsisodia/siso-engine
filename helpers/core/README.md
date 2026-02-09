# Core Helpers

Framework-agnostic utilities for BlackBox5.

## Overview

This directory contains base classes and utilities used throughout the BlackBox5 engine. These are foundational components that other modules depend on.

## Files

| File | Purpose |
|------|---------|
| `base.py` | Base tool interface with risk levels, parameters, and results |
| `registry.py` | Central tool registry for managing available tools |

## Key Classes

### BaseTool
Abstract base class for all tools in the system.

```python
from helpers.core.base import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"
    risk_level = ToolRisk.LOW

    async def execute(self, **params):
        # Implementation
        return ToolResult(success=True, data={"result": "value"})
```

### ToolRegistry
Central registry for tool registration and discovery.

```python
from helpers.core.registry import ToolRegistry

registry = ToolRegistry()
registry.register(MyTool)
tool = registry.get("my_tool")
```

### ToolRisk
Risk level enumeration:
- `LOW` - Safe operations (reading files)
- `MEDIUM` - Moderate risk (writing files)
- `HIGH` - Destructive operations (deleting, git operations)
- `CRITICAL` - System-level changes (deployments)

### ToolParameter
Parameter definition for tool inputs:
```python
param = ToolParameter(
    name="file_path",
    type="string",
    description="Path to the file",
    required=True
)
```

### ToolResult
Standardized result format:
```python
result = ToolResult(
    success=True,
    data={"content": "file contents"},
    error=None
)
```

## Usage

All tools in the system should inherit from `BaseTool` and register with `ToolRegistry`:

```python
from helpers.core.base import BaseTool, ToolRisk, ToolParameter, ToolResult
from helpers.core.registry import ToolRegistry

class FileReaderTool(BaseTool):
    name = "file_reader"
    description = "Reads file contents"
    risk_level = ToolRisk.LOW
    parameters = [
        ToolParameter(name="path", type="string", required=True)
    ]

    async def execute(self, path: str):
        try:
            with open(path) as f:
                content = f.read()
            return ToolResult(success=True, data={"content": content})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

# Register the tool
registry = ToolRegistry()
registry.register(FileReaderTool)
```

## Related

- [Git Helpers](../git/) - Git-specific utilities
- [Legacy Helpers](../legacy/) - Deprecated utilities
- [Agents](../../agents/) - Tool consumers
