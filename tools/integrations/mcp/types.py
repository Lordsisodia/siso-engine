"""
MCP Integration Type Definitions

This module contains all data types used by the MCP integration.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class MCPServer:
    """Represents an MCP server connection."""
    name: str
    status: str
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    capabilities: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MCPMessage:
    """Represents an MCP message."""
    role: str
    content: Dict[str, Any]
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MCPResponse:
    """Represents an MCP response."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MCPError:
    """Represents an MCP error."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MCPTool:
    """Represents an MCP tool/capability."""
    name: str
    description: str
    input_schema: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MCPResource:
    """Represents an MCP resource."""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MCPSession:
    """Represents an MCP session."""
    session_id: str
    server_name: str
    status: str
    created_at: Optional[str] = None
    last_activity: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


__all__ = [
    'MCPServer',
    'MCPMessage',
    'MCPResponse',
    'MCPError',
    'MCPTool',
    'MCPResource',
    'MCPSession',
]
