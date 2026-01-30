"""
MCP Integration Demo

Demonstrates basic usage of the MCP integration.
"""

import asyncio
from blackbox5.engine.integrations.mcp import MCPManager


def demo_list_servers():
    """Demo: List available MCP servers."""
    print("=== Available MCP Servers ===\n")

    manager = MCPManager()
    servers = manager.list_servers()

    for server in servers:
        print(f"Server: {server.name}")
        print(f"  Status: {server.status}")
        print(f"  Command: {server.command}")
        print(f"  Args: {server.args}")
        print()


def demo_connect_and_list_tools():
    """Demo: Connect to server and list tools."""
    print("=== Connect and List Tools ===\n")

    manager = MCPManager()

    # Connect to a server
    server = manager.connect_server("filesystem")
    print(f"Connected to: {server.name}")

    # List available tools
    tools = manager.list_tools(server)
    print(f"\nAvailable tools ({len(tools)}):")

    for tool in tools:
        print(f"  - {tool.name}")
        print(f"    {tool.description}")
        if tool.input_schema:
            print(f"    Schema: {tool.input_schema}")
    print()


def demo_execute_tool():
    """Demo: Execute a tool."""
    print("=== Execute Tool ===\n")

    manager = MCPManager()

    # Execute a tool
    result = manager.execute_tool(
        server_name="filesystem",
        tool_name="read_file",
        arguments={"path": "/path/to/file.txt"}
    )

    if result.success:
        print("Tool executed successfully")
        print(f"Result: {result.data}")
    else:
        print(f"Tool execution failed: {result.error}")
    print()


def demo_list_resources():
    """Demo: List server resources."""
    print("=== List Resources ===\n")

    manager = MCPManager()
    server = manager.connect_server("filesystem")

    # List resources
    resources = manager.list_resources(server)
    print(f"Available resources ({len(resources)}):")

    for resource in resources:
        print(f"  - {resource.name}")
        print(f"    URI: {resource.uri}")
        print(f"    Type: {resource.mime_type}")
        if resource.description:
            print(f"    Description: {resource.description}")
    print()


def demo_session_management():
    """Demo: Create and manage sessions."""
    print("=== Session Management ===\n")

    manager = MCPManager()

    # Create a session
    session = manager.create_session("filesystem")
    print(f"Created session: {session.session_id}")
    print(f"Server: {session.server_name}")
    print(f"Status: {session.status}")

    # Execute tool in session
    result = manager.execute_tool(
        server_name="filesystem",
        tool_name="read_file",
        arguments={"path": "config.json"},
        session_id=session.session_id
    )

    print(f"Result: {result.success}")

    # Close session
    manager.close_session(session.session_id)
    print("Session closed")
    print()


def demo_crash_prevention():
    """Demo: Enable crash prevention."""
    print("=== Crash Prevention ===\n")

    manager = MCPManager()

    # Enable crash prevention
    manager.enable_crash_prevention(
        max_retries=3,
        retry_delay=1.0,
        health_check_interval=30
    )

    print("Crash prevention enabled")
    print("  Max retries: 3")
    print("  Retry delay: 1.0s")
    print("  Health check interval: 30s")
    print()


def main():
    """Run all demos."""
    print("\n" + "="*50)
    print("MCP Integration Demo")
    print("="*50 + "\n")

    try:
        demo_list_servers()
        demo_connect_and_list_tools()
        demo_execute_tool()
        demo_list_resources()
        demo_session_management()
        demo_crash_prevention()

        print("="*50)
        print("All demos completed successfully!")
        print("="*50 + "\n")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
