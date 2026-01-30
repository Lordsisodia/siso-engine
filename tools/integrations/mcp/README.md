# MCP Integration for BlackBox5

Model Context Protocol (MCP) integration for connecting AI models to external data sources and tools.

## Overview

MCP is an open protocol that enables AI models to securely connect to external data sources and tools. This integration provides:

- **Server Management**: Start, stop, and monitor MCP servers
- **Tool Execution**: Execute tools provided by MCP servers
- **Resource Access**: Access resources through MCP protocol
- **Crash Prevention**: Robust error handling and recovery
- **Session Management**: Manage persistent connections to MCP servers

## Features

### Core Capabilities

- **Server Lifecycle**: Start, stop, and restart MCP servers
- **Tool Discovery**: List available tools from connected servers
- **Tool Execution**: Execute tools with proper parameter handling
- **Resource Access**: Access and query MCP resources
- **Error Recovery**: Automatic crash prevention and recovery
- **Health Monitoring**: Track server health and connection status

## Installation

### Requirements

```bash
# MCP SDK (if needed)
pip install mcp
```

### Configuration

MCP servers are configured in `.config/mcp-servers.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

## Quick Start

### Basic Usage

```python
from blackbox5.engine.integrations.mcp import MCPManager

# Initialize manager
manager = MCPManager()

# List available servers
servers = manager.list_servers()
for server in servers:
    print(f"{server.name}: {server.status}")

# Connect to a server
server = manager.connect_server("filesystem")

# List available tools
tools = manager.list_tools(server)
for tool in tools:
    print(f"{tool.name}: {tool.description}")

# Execute a tool
result = manager.execute_tool(
    server_name="filesystem",
    tool_name="read_file",
    arguments={"path": "/path/to/file"}
)

# Access resources
resources = manager.list_resources(server)
```

### Advanced Usage

#### Crash Prevention

```python
from blackbox5.engine.integrations.mcp import MCPManager

manager = MCPManager()

# Enable crash prevention
manager.enable_crash_prevention(
    max_retries=3,
    retry_delay=1.0,
    health_check_interval=30
)

# Servers will auto-recover from crashes
server = manager.connect_server("unstable-server")
```

#### Session Management

```python
# Create persistent session
session = manager.create_session("filesystem")

# Execute tools in session context
result = manager.execute_tool(
    server_name="filesystem",
    tool_name="read_file",
    arguments={"path": "config.json"},
    session_id=session.session_id
)

# Check session status
status = manager.get_session_status(session.session_id)
print(f"Session: {status}")

# Close session when done
manager.close_session(session.session_id)
```

#### Resource Access

```python
# List all resources
resources = manager.list_resources(server)
for resource in resources:
    print(f"{resource.name}: {resource.uri}")
    print(f"  Type: {resource.mime_type}")

# Read resource content
content = manager.read_resource(
    server_name="filesystem",
    resource_uri="file:///path/to/file.txt"
)
print(content)
```

## API Reference

### MCPManager

Main class for MCP operations.

#### Methods

##### `list_servers() -> List[MCPServer]`

List all configured MCP servers.

##### `connect_server(server_name: str) -> MCPServer`

Connect to an MCP server.

##### `disconnect_server(server_name: str)`

Disconnect from a server.

##### `list_tools(server: MCPServer) -> List[MCPTool]`

List available tools from a server.

##### `execute_tool(server_name: str, tool_name: str, arguments: dict, session_id: Optional[str] = None) -> MCPResponse`

Execute a tool on a server.

##### `list_resources(server: MCPServer) -> List[MCPResource]`

List available resources from a server.

##### `read_resource(server_name: str, resource_uri: str) -> str`

Read a resource's content.

##### `create_session(server_name: str) -> MCPSession`

Create a new session with a server.

##### `close_session(session_id: str)`

Close a session.

##### `enable_crash_prevention(max_retries: int = 3, retry_delay: float = 1.0, health_check_interval: int = 30)`

Enable crash prevention and recovery.

### Data Classes

#### `MCPServer`

```python
@dataclass
class MCPServer:
    name: str
    status: str
    command: Optional[str]
    args: Optional[List[str]]
    env: Optional[Dict[str, str]]
    capabilities: Optional[Dict[str, Any]]
```

#### `MCPTool`

```python
@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: Optional[Dict[str, Any]]
```

#### `MCPResource`

```python
@dataclass
class MCPResource:
    uri: str
    name: str
    description: Optional[str]
    mime_type: Optional[str]
```

## Configuration

### Server Configuration

Servers are configured in `.config/mcp-servers.json`:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "executable",
      "args": ["--arg1", "--arg2"],
      "env": {
        "ENV_VAR": "value"
      }
    }
  }
}
```

### Environment Variables

- `MCP_CONFIG_PATH`: Path to MCP config file (default: `.config/mcp-servers.json`)
- `MCP_LOG_LEVEL`: Logging level (default: `INFO`)

## Examples

### Example 1: Filesystem Access

```python
from blackbox5.engine.integrations.mcp import MCPManager

manager = MCPManager()
server = manager.connect_server("filesystem")

# List directory
result = manager.execute_tool(
    server_name="filesystem",
    tool_name="list_directory",
    arguments={"path": "/projects"}
)

# Read file
content = manager.execute_tool(
    server_name="filesystem",
    tool_name="read_file",
    arguments={"path": "/projects/README.md"}
)
```

### Example 2: GitHub Integration

```python
from blackbox5.engine.integrations.mcp import MCPManager

manager = MCPManager()
server = manager.connect_server("github")

# List repositories
result = manager.execute_tool(
    server_name="github",
    tool_name="list_repositories",
    arguments={"owner": "myorg"}
)

# Create issue
result = manager.execute_tool(
    server_name="github",
    tool_name="create_issue",
    arguments={
        "owner": "myorg",
        "repo": "myrepo",
        "title": "Bug: Authentication fails",
        "body": "Detailed description..."
    }
)
```

### Example 3: Multiple Servers

```python
from blackbox5.engine.integrations.mcp import MCPManager

manager = MCPManager()

# Connect to multiple servers
servers = [
    manager.connect_server("filesystem"),
    manager.connect_server("github"),
    manager.connect_server("database")
]

# Execute operations across servers
for server in servers:
    tools = manager.list_tools(server)
    print(f"{server.name}: {len(tools)} tools available")
```

## Error Handling

```python
from blackbox5.engine.integrations.mcp import MCPManager, MCPError

manager = MCPManager()

try:
    result = manager.execute_tool(
        server_name="filesystem",
        tool_name="read_file",
        arguments={"path": "/nonexistent/file"}
    )
except MCPError as e:
    print(f"MCP Error: {e.message}")
    print(f"Details: {e.details}")
```

## Crash Prevention

The MCP integration includes robust crash prevention:

- **Automatic Recovery**: Servers auto-restart on crash
- **Health Checks**: Periodic health monitoring
- **Circuit Breaker**: Prevents cascading failures
- **Retry Logic**: Configurable retry attempts

```python
manager = MCPManager()

# Enable with custom settings
manager.enable_crash_prevention(
    max_retries=5,
    retry_delay=2.0,
    health_check_interval=60
)
```

## Testing

```bash
# Run tests
pytest 06-integrations/mcp/tests/ -v

# Run with coverage
pytest 06-integrations/mcp/tests/ --cov=06-integrations/mcp --cov-report=html
```

## Troubleshooting

### Common Issues

**Issue**: Server fails to start
- **Solution**: Check command and args in config file
- Verify executable is in PATH

**Issue**: Tools not found
- **Solution**: Ensure server is connected and running
- Check server capabilities

**Issue**: Connection timeout
- **Solution**: Increase timeout in server config
- Check network/firewall settings

**Issue**: Frequent crashes
- **Solution**: Enable crash prevention
- Check server logs for errors

## See Also

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Engine docs: `../../engine/docs/integrations/`

## Contributing

When contributing to the MCP integration:

1. Follow MCP specification
2. Add tests for new features
3. Update documentation
4. Test with real MCP servers

## License

Part of BlackBox5. See main project LICENSE.
