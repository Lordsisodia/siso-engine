"""
Black Box 5 Engine - Tool Registry

Central registry for managing available tools.
"""

from typing import Dict, Type, List, Optional, Any
import logging

from .base import BaseTool

logger = logging.getLogger("ToolRegistry")


class ToolRegistry:
    """
    Central registry for managing tools.

    Tools can be registered, retrieved, and listed through this registry.
    """

    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._instances: Dict[str, BaseTool] = {}

    def register(self, tool_class: Type[BaseTool], name: Optional[str] = None) -> None:
        """
        Register a tool class.

        Args:
            tool_class: Tool class to register
            name: Optional custom name (defaults to tool.name)
        """
        tool_name = name or tool_class.name

        if tool_name in self._tools:
            logger.warning(f"Tool '{tool_name}' already registered, overwriting")

        self._tools[tool_name] = tool_class
        logger.info(f"Registered tool: {tool_name}")

    def register_instance(self, instance: BaseTool, name: Optional[str] = None) -> None:
        """
        Register a tool instance.

        Args:
            instance: Tool instance to register
            name: Optional custom name (defaults to tool.name)
        """
        tool_name = name or instance.name

        if tool_name in self._instances:
            logger.warning(f"Tool instance '{tool_name}' already registered, overwriting")

        self._instances[tool_name] = instance
        logger.info(f"Registered tool instance: {tool_name}")

    def get(self, name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseTool]:
        """
        Get a tool instance by name.

        Args:
            name: Tool name
            config: Optional tool configuration

        Returns:
            Tool instance or None if not found
        """
        # Check for pre-configured instance first
        if name in self._instances:
            return self._instances[name]

        # Create new instance from class
        if name in self._tools:
            tool_class = self._tools[name]
            return tool_class(config=config)

        logger.warning(f"Tool not found: {name}")
        return None

    def list_tools(self) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        all_tools = set(self._tools.keys()) | set(self._instances.keys())
        return sorted(list(all_tools))

    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a tool.

        Args:
            name: Tool name

        Returns:
            Tool information dictionary or None
        """
        tool = self.get(name)
        if tool:
            return tool.get_info()
        return None

    def get_all_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered tools.

        Returns:
            Dictionary mapping tool names to their info
        """
        all_tools = set(self._tools.keys()) | set(self._instances.keys())

        info = {}
        for tool_name in all_tools:
            tool_info = self.get_tool_info(tool_name)
            if tool_info:
                info[tool_name] = tool_info

        return info

    def has_tool(self, name: str) -> bool:
        """
        Check if a tool is registered.

        Args:
            name: Tool name

        Returns:
            True if tool exists
        """
        return name in self._tools or name in self._instances

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.

        Args:
            name: Tool name

        Returns:
            True if tool was unregistered
        """
        removed = False

        if name in self._tools:
            del self._tools[name]
            removed = True

        if name in self._instances:
            del self._instances[name]
            removed = True

        if removed:
            logger.info(f"Unregistered tool: {name}")

        return removed

    def clear(self) -> None:
        """Clear all registered tools"""
        self._tools.clear()
        self._instances.clear()
        logger.info("Cleared all tools from registry")


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.

    Returns:
        Global ToolRegistry instance
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = ToolRegistry()
        _register_default_tools(_global_registry)

    return _global_registry


def _register_default_tools(registry: ToolRegistry) -> None:
    """Register default tools"""
    # TODO: Create the following tool files and uncomment the imports below:
    # - file_tools.py (FileReadTool, FileWriteTool)
    # - bash_tool.py (BashExecuteTool)
    # - search_tool.py (SearchTool)
    
    # from .file_tools import FileReadTool, FileWriteTool
    # from .bash_tool import BashExecuteTool
    # from .search_tool import SearchTool

    # registry.register(FileReadTool)
    # registry.register(FileWriteTool)
    # registry.register(BashExecuteTool)
    # registry.register(SearchTool)
    pass  # No default tools registered until tool files are created


# Convenience functions

def get_tool(name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseTool]:
    """
    Get a tool from the global registry.

    Args:
        name: Tool name
        config: Optional tool configuration

    Returns:
        Tool instance or None
    """
    registry = get_global_registry()
    return registry.get(name, config=config)


def register_tool(tool_class: Type[BaseTool], name: Optional[str] = None) -> None:
    """
    Register a tool in the global registry.

    Args:
        tool_class: Tool class to register
        name: Optional custom name
    """
    registry = get_global_registry()
    registry.register(tool_class, name=name)


def list_tools() -> List[str]:
    """
    List all tools in the global registry.

    Returns:
        List of tool names
    """
    registry = get_global_registry()
    return registry.list_tools()


def get_tool_info(name: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a tool.

    Args:
        name: Tool name

    Returns:
        Tool information or None
    """
    registry = get_global_registry()
    return registry.get_tool_info(name)


def get_all_tools_info() -> Dict[str, Dict[str, Any]]:
    """
    Get information about all tools.

    Returns:
        Dictionary of tool information
    """
    registry = get_global_registry()
    return registry.get_all_info()
