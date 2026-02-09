"""
BlackBox5 MCP Integration System
=================================

Manages Model Context Protocol (MCP) server discovery, initialization,
and tool management for BlackBox5 agents.

Adapted from Auto-Claude's MCP integration with simplified architecture
for BlackBox5's modular design.

Key Features:
- Discover MCP servers from configuration files
- Start/stop MCP servers dynamically
- Query available tools from servers
- Validate server configurations for security
- Support for both command-based and HTTP-based MCP servers
"""

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

# Use absolute import to avoid conflicts with local logging.py
import logging as logger_module

logger = logger_module.getLogger(__name__)


class MCPServerConfig:
    """
    Configuration for a single MCP server.

    Supports two types of MCP servers:
    1. Command-based: Executed as subprocess (e.g., npx, python)
    2. HTTP-based: Communicate via HTTP/HTTPS endpoint
    """

    def __init__(
        self,
        server_id: str,
        name: str,
        server_type: str = "command",
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        env: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
    ):
        """
        Initialize MCP server configuration.

        Args:
            server_id: Unique identifier for this server
            name: Human-readable name
            server_type: Type of server ("command" or "http")
            command: Command to execute (for command-based servers)
            args: Arguments for the command
            url: HTTP/HTTPS endpoint (for HTTP-based servers)
            headers: HTTP headers (for HTTP-based servers)
            env: Environment variables for the command
            description: Optional description

        Raises:
            ValueError: If configuration is invalid
        """
        self.server_id = server_id
        self.name = name
        self.server_type = server_type
        self.command = command
        self.args = args or []
        self.url = url
        self.headers = headers or {}
        self.env = env or {}
        self.description = description

        self._validate()

    def _validate(self) -> None:
        """Validate server configuration."""
        if not self.server_id or not isinstance(self.server_id, str):
            raise ValueError("server_id must be a non-empty string")

        if not self.name or not isinstance(self.name, str):
            raise ValueError("name must be a non-empty string")

        if self.server_type not in ("command", "http"):
            raise ValueError(f"Invalid server_type: {self.server_type}")

        if self.server_type == "command":
            if not self.command:
                raise ValueError("command-based servers require a command")
        elif self.server_type == "http":
            if not self.url:
                raise ValueError("http-based servers require a url")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            "id": self.server_id,
            "name": self.name,
            "type": self.server_type,
        }

        if self.server_type == "command":
            result["command"] = self.command
            result["args"] = self.args
            if self.env:
                result["env"] = self.env
        elif self.server_type == "http":
            result["url"] = self.url
            if self.headers:
                result["headers"] = self.headers

        if self.description:
            result["description"] = self.description

        return result

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "MCPServerConfig":
        """Create MCPServerConfig from dictionary."""
        return cls(
            server_id=config.get("id", ""),
            name=config.get("name", ""),
            server_type=config.get("type", "command"),
            command=config.get("command"),
            args=config.get("args"),
            url=config.get("url"),
            headers=config.get("headers"),
            env=config.get("env"),
            description=config.get("description"),
        )


class MCPManager:
    """
    Manages MCP server lifecycle and tool discovery.

    Provides:
    - Server discovery from configuration files
    - Dynamic server start/stop
    - Tool enumeration
    - Security validation
    """

    def __init__(self, config_path: Optional[Path] = None, enable_crash_prevention: bool = True):
        """
        Initialize MCP Manager.

        Args:
            config_path: Path to MCP configuration file (JSON format).
                        If None, looks for .mcp.json in current directory.
            enable_crash_prevention: Whether to enable crash prevention monitoring
        """
        self.config_path = config_path or Path.cwd() / ".mcp.json"
        self.servers: Dict[str, MCPServerConfig] = {}
        self.running_servers: Dict[str, Any] = {}
        self.server_lock = threading.Lock()

        # Crash prevention
        self._crash_prevention = None
        self._enable_crash_prevention = enable_crash_prevention

        self._load_servers()

        if self._enable_crash_prevention:
            self._init_crash_prevention()

    def _load_servers(self) -> None:
        """Load MCP server configurations from file."""
        if not self.config_path.exists():
            logger.info(f"No MCP config file found at {self.config_path}")
            return

        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)

            mcp_servers = config.get("mcpServers", {})
            for server_id, server_config in mcp_servers.items():
                try:
                    # Add ID to config if not present
                    server_config["id"] = server_id
                    # Use name from config or fallback to ID
                    server_config["name"] = server_config.get("name", server_id)

                    server = MCPServerConfig.from_dict(server_config)
                    self.servers[server_id] = server
                    logger.info(f"Loaded MCP server: {server_id}")
                except ValueError as e:
                    logger.warning(f"Invalid MCP server config {server_id}: {e}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MCP config file: {e}")
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")

    def _init_crash_prevention(self) -> None:
        """Initialize crash prevention system."""
        try:
            # Lazy import to avoid dependency issues
            from .mcp_crash_prevention import get_crash_prevention

            self._crash_prevention = get_crash_prevention(
                mcp_manager=self,
                health_monitor=None  # Can be set later
            )
            logger.info("MCP crash prevention initialized")
        except ImportError as e:
            logger.warning(f"Could not import crash prevention: {e}")
            self._enable_crash_prevention = False
        except Exception as e:
            logger.error(f"Failed to initialize crash prevention: {e}")
            self._enable_crash_prevention = False

    async def start_crash_prevention(self) -> None:
        """Start crash prevention monitoring (async)."""
        if self._crash_prevention:
            await self._crash_prevention.start()

    async def stop_crash_prevention(self) -> None:
        """Stop crash prevention monitoring (async)."""
        if self._crash_prevention:
            await self._crash_prevention.stop()

    def get_crash_prevention_status(self) -> Optional[Dict[str, Any]]:
        """Get crash prevention status."""
        if self._crash_prevention:
            return self._crash_prevention.get_status_summary()
        return None

    def _check_server_limits(self, server_id: str) -> bool:
        """
        Check if starting a server would exceed limits.

        Args:
            server_id: ID of server to check

        Returns:
            True if within limits, False otherwise
        """
        if not self._crash_prevention:
            return True

        # Get current metrics
        metrics = self._crash_prevention.get_metrics()

        # Check if this server type would exceed max instances
        server = self.servers.get(server_id)
        if not server:
            return True

        # Extract server type from command
        server_type = None
        if server.command == "npx" and server.args:
            for arg in server.args:
                if "mcp" in arg.lower():
                    # Simple type extraction
                    if "chrome" in arg.lower():
                        server_type = "chrome-devtools"
                    elif "playwright" in arg.lower():
                        server_type = "playwright"
                    elif "fetch" in arg.lower():
                        server_type = "fetch"
                    elif "filesystem" in arg.lower():
                        server_type = "filesystem"
                    break

        if server_type:
            current_count = metrics["server_type_counts"].get(server_type, 0)
            max_instances = self._crash_prevention.config.max_instances_per_type

            if current_count >= max_instances:
                logger.warning(
                    f"Cannot start {server_id}: {server_type} already has {current_count} instances (max: {max_instances})"
                )
                return False

        return True

    def discover_mcp_servers(self) -> List[Dict[str, Any]]:
        """
        Discover and list all configured MCP servers.

        Returns:
            List of server information dictionaries
        """
        servers = []
        for server_id, server in self.servers.items():
            info = {
                "id": server.server_id,
                "name": server.name,
                "type": server.server_type,
                "description": server.description,
                "running": server_id in self.running_servers,
            }

            if server.server_type == "command":
                info["command"] = server.command
            elif server.server_type == "http":
                info["url"] = server.url

            servers.append(info)

        return servers

    def start_server(self, server_id: str) -> bool:
        """
        Start an MCP server.

        Args:
            server_id: ID of the server to start

        Returns:
            True if server started successfully, False otherwise
        """
        if server_id not in self.servers:
            logger.error(f"Unknown server: {server_id}")
            return False

        if server_id in self.running_servers:
            logger.warning(f"Server {server_id} is already running")
            return True

        # Check crash prevention limits
        if not self._check_server_limits(server_id):
            logger.warning(f"Server {server_id} blocked by crash prevention limits")
            return False

        server = self.servers[server_id]

        try:
            if server.server_type == "command":
                return self._start_command_server(server)
            elif server.server_type == "http":
                # HTTP servers don't need to be "started" - they're endpoints
                with self.server_lock:
                    self.running_servers[server_id] = {"type": "http"}
                logger.info(f"Registered HTTP server: {server_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to start server {server_id}: {e}")
            return False

        return False

    def _start_command_server(self, server: MCPServerConfig) -> bool:
        """
        Start a command-based MCP server.

        Args:
            server: MCPServerConfig instance

        Returns:
            True if started successfully
        """
        try:
            cmd = [server.command] + server.args

            # Prepare environment
            env = os.environ.copy()
            if server.env:
                env.update(server.env)

            # Start subprocess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
            )

            with self.server_lock:
                self.running_servers[server.server_id] = {
                    "type": "command",
                    "process": process,
                }

            logger.info(f"Started MCP server {server.server_id} with PID {process.pid}")
            return True

        except FileNotFoundError:
            logger.error(f"Command not found: {server.command}")
            return False
        except Exception as e:
            logger.error(f"Failed to start server {server.server_id}: {e}")
            return False

    def stop_server(self, server_id: str) -> bool:
        """
        Stop a running MCP server.

        Args:
            server_id: ID of the server to stop

        Returns:
            True if stopped successfully
        """
        if server_id not in self.running_servers:
            logger.warning(f"Server {server_id} is not running")
            return False

        try:
            server_info = self.running_servers[server_id]

            if server_info["type"] == "command":
                process = server_info["process"]
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

                logger.info(f"Stopped MCP server {server_id}")

            with self.server_lock:
                del self.running_servers[server_id]

            return True

        except Exception as e:
            logger.error(f"Failed to stop server {server_id}: {e}")
            return False

    def stop_all_servers(self) -> None:
        """Stop all running MCP servers."""
        server_ids = list(self.running_servers.keys())
        for server_id in server_ids:
            self.stop_server(server_id)

    def get_server_tools(self, server_id: str) -> List[str]:
        """
        Get list of tools available from a server.

        Note: This is a simplified implementation. In a full MCP integration,
        this would communicate with the server to enumerate its tools.

        Args:
            server_id: ID of the server

        Returns:
            List of tool names (simplified - returns empty list for now)
        """
        if server_id not in self.servers:
            logger.warning(f"Unknown server: {server_id}")
            return []

        # In a full implementation, this would query the MCP server
        # For now, return empty list as placeholder
        logger.info(f"Tools for {server_id}: (not yet implemented)")
        return []

    def get_server_config(self, server_id: str) -> Optional[MCPServerConfig]:
        """
        Get configuration for a specific server.

        Args:
            server_id: ID of the server

        Returns:
            MCPServerConfig or None if not found
        """
        return self.servers.get(server_id)

    def validate_server(self, server_id: str) -> bool:
        """
        Validate a server configuration.

        Args:
            server_id: ID of the server to validate

        Returns:
            True if server configuration is valid
        """
        server = self.servers.get(server_id)
        if not server:
            return False

        try:
            server._validate()
            return True
        except ValueError:
            return False

    def get_running_servers(self) -> List[str]:
        """
        Get list of currently running server IDs.

        Returns:
            List of server IDs
        """
        return list(self.running_servers.keys())

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup servers."""
        self.stop_all_servers()


# =============================================================================
# Convenience Functions
# =============================================================================

def create_mcp_manager(config_path: Optional[Path] = None) -> MCPManager:
    """
    Create an MCP Manager instance.

    Args:
        config_path: Path to MCP configuration file

    Returns:
        MCPManager instance
    """
    return MCPManager(config_path)


def discover_servers(config_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Quick function to discover MCP servers without creating a manager.

    Args:
        config_path: Path to MCP configuration file

    Returns:
        List of server information dictionaries
    """
    with MCPManager(config_path) as manager:
        return manager.discover_mcp_servers()
