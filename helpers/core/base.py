"""
Black Box 5 Engine - Tool Base Interface

Defines the base interface for all tools that agents can use.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class ToolRisk(Enum):
    """Risk level for tool execution"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ToolParameter:
    """Definition of a tool parameter"""
    name: str
    type: str  # str, int, bool, list, dict
    description: str
    required: bool = True
    default: Any = None
    # Validation constraints
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None


@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata or {}
        }


class BaseTool(ABC):
    """
    Base class for all tools.

    Tools are composable capabilities that agents can use to perform
    specific actions like reading files, running commands, etc.
    """

    # Tool metadata (should be overridden by subclasses)
    name: str = "base_tool"
    description: str = "Base tool interface"
    risk: ToolRisk = ToolRisk.LOW
    parameters: List[ToolParameter] = []

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the tool.

        Args:
            config: Optional tool configuration
        """
        self.config = config or {}

    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        """
        Execute the tool with the given parameters.

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution outcome
        """
        pass

    def validate_parameters(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Validate tool parameters.

        Args:
            params: Parameters to validate

        Returns:
            Error message if validation fails, None otherwise
        """
        # Check required parameters
        for param in self.parameters:
            if param.required and param.name not in params:
                return f"Missing required parameter: {param.name}"

            # Skip validation if parameter not provided
            if param.name not in params:
                continue

            value = params[param.name]

            # Type validation
            expected_type = self._get_python_type(param.type)
            if not isinstance(value, expected_type):
                return f"Parameter '{param.name}' must be of type {param.type}"

            # String length validation
            if param.type == "str" and isinstance(value, str):
                if param.min_length and len(value) < param.min_length:
                    return f"Parameter '{param.name}' must be at least {param.min_length} characters"
                if param.max_length and len(value) > param.max_length:
                    return f"Parameter '{param.name}' must be at most {param.max_length} characters"

            # Pattern validation
            if param.pattern and isinstance(value, str):
                import re
                if not re.match(param.pattern, value):
                    return f"Parameter '{param.name}' does not match required pattern"

            # Allowed values validation
            if param.allowed_values and value not in param.allowed_values:
                return f"Parameter '{param.name}' must be one of {param.allowed_values}"

        return None

    def _get_python_type(self, type_str: str) -> type:
        """Convert string type to Python type"""
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "any": object
        }
        return type_map.get(type_str, object)

    def get_info(self) -> Dict[str, Any]:
        """
        Get tool information.

        Returns:
            Dictionary with tool metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "risk": self.risk.value,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default
                }
                for p in self.parameters
            ],
            "config": self.config
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
