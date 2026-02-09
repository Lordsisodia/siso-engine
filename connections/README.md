# Connections

External integrations for the BB5 engine including communications, hooks, and MCP (Model Context Protocol) connections.

## Overview

This directory manages all external connectivity for the BB5 engine:
- **Communications** - Internal messaging, task queues, event logging
- **Hooks** - Lifecycle hooks for session management
- **MCP** - Model Context Protocol bridges and servers

## Directory Structure

```
connections/
├── communications/     # Internal messaging system
│   ├── chat-log.yaml
│   ├── queue.yaml
│   └── tasks.yaml
├── hooks/             # Lifecycle hooks (see hooks/README.md)
│   ├── active/
│   ├── archive/
│   └── pipeline/
└── mcp/               # Model Context Protocol
    ├── bridges/       # Bridge implementations
    ├── clients/       # MCP clients
    └── servers/       # MCP servers
```

## Communications

YAML-based internal communication system:
- `chat-log.yaml` - Conversation history tracking
- `queue.yaml` - Task queue management
- `tasks.yaml` - Active task registry

## MCP (Model Context Protocol)

Bridges BB5 to external MCP servers:

### Bridges
- `mcp-macmini-bridge.py` - SSH bridge to Mac Mini OpenClaw
- `archive/` - Historical bridge implementations

### Servers
- `mcp-server-moltbot.py` - Moltbot integration server
- `mcp-server-ralf.py` - RALF system server
- `mcp-telegram-bridge.py` - Telegram messaging bridge

### Clients
- `mcp-openclaw-direct.py` - Direct OpenClaw client

## Usage

### Using MCP Bridges
```python
# Bridges expose tools via stdio JSON-RPC
python connections/mcp/bridges/mcp-macmini-bridge.py
```

### Communication Events
Events are logged to `communications/events.yaml` for agent coordination.
