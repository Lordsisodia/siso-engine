"""
Command Routing and Registration System

This module provides the command registry and routing infrastructure
for the BlackBox5 CLI, including command discovery and execution.
"""

import inspect
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Any

from .base import BaseCommand, CommandError


class CommandRegistry:
    """
    Registry for all available CLI commands.

    Commands are registered by name and can be discovered automatically
    from the commands directory.
    """

    def __init__(self):
        """Initialize an empty command registry."""
        self._commands: Dict[str, Type[BaseCommand]] = {}
        self.logger = logging.getLogger("cli.registry")

    def register(self, command_class: Type[BaseCommand]) -> None:
        """
        Register a command class with the registry.

        Args:
            command_class: Command class to register (not instance)

        Raises:
            ValueError: If command is invalid or already registered
        """
        # Validate command class
        if not inspect.isclass(command_class):
            raise ValueError(f"Command must be a class, got {type(command_class)}")

        if not issubclass(command_class, BaseCommand):
            raise ValueError(f"Command must inherit from BaseCommand")

        if not command_class.name:
            raise ValueError(f"Command class must define a 'name' attribute")

        # Check for duplicate registration
        if command_class.name in self._commands:
            self.logger.warning(f"Command '{command_class.name}' already registered, skipping")
            return

        # Register the command
        self._commands[command_class.name] = command_class
        self.logger.debug(f"Registered command: {command_class.name}")

        # Register aliases
        for alias in command_class.aliases:
            if alias in self._commands:
                self.logger.warning(f"Alias '{alias}' already registered, skipping")
                continue
            self._commands[alias] = command_class
            self.logger.debug(f"Registered alias '{alias}' for command {command_class.name}")

    def unregister(self, command_name: str) -> None:
        """
        Unregister a command from the registry.

        Args:
            command_name: Name of the command to unregister
        """
        if command_name in self._commands:
            command_class = self._commands[command_name]
            del self._commands[command_name]

            # Remove aliases
            aliases_to_remove = [
                alias for alias, cmd in self._commands.items()
                if cmd == command_class and alias != command_name
            ]
            for alias in aliases_to_remove:
                del self._commands[alias]

            self.logger.debug(f"Unregistered command: {command_name}")

    def get(self, command_name: str) -> Optional[Type[BaseCommand]]:
        """
        Get a command class by name.

        Args:
            command_name: Name of the command to retrieve

        Returns:
            Command class or None if not found
        """
        return self._commands.get(command_name)

    def create_command(self, command_name: str, config: Optional[Any] = None) -> BaseCommand:
        """
        Create an instance of a command.

        Args:
            command_name: Name of the command to create
            config: Optional configuration to pass to command

        Returns:
            Command instance

        Raises:
            CommandError: If command not found
        """
        command_class = self.get(command_name)
        if not command_class:
            raise CommandError(
                f"Unknown command: {command_name}",
                exit_code=2,  # Standard exit code for command not found
                details={"available_commands": list(self.list_commands().keys())}
            )

        return command_class(config)

    def list_commands(self) -> Dict[str, str]:
        """
        List all registered commands with their descriptions.

        Returns:
            Dictionary mapping command names to descriptions
        """
        commands = {}
        for name, cls in self._commands.items():
            # Only include primary names, not aliases
            if name == cls.name:
                commands[name] = cls.description
        return commands

    def discover_commands(self, commands_dir: Path) -> None:
        """
        Automatically discover and register commands from a directory.

        Args:
            commands_dir: Path to directory containing command modules
        """
        if not commands_dir.exists():
            self.logger.warning(f"Commands directory does not exist: {commands_dir}")
            return

        if not commands_dir.is_dir():
            self.logger.error(f"Commands path is not a directory: {commands_dir}")
            return

        # Add commands directory to Python path
        import sys
        if str(commands_dir.parent) not in sys.path:
            sys.path.insert(0, str(commands_dir.parent))

        # Import all Python modules in the commands directory
        for module_path in commands_dir.glob("*.py"):
            if module_path.name.startswith("_"):
                continue  # Skip __init__.py and other private modules

            module_name = module_path.stem

            try:
                # Import the module
                module = __import__(f"cli.commands.{module_name}", fromlist=[""])

                # Find all BaseCommand subclasses in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                        issubclass(obj, BaseCommand) and
                        obj is not BaseCommand and
                        hasattr(obj, 'name') and obj.name):

                        self.register(obj)
                        self.logger.info(f"Discovered command '{obj.name}' from {module_name}")

            except ImportError as e:
                self.logger.error(f"Failed to import command module {module_name}: {e}")
            except Exception as e:
                self.logger.error(f"Error discovering commands from {module_name}: {e}")

    def clear(self) -> None:
        """Clear all registered commands."""
        self._commands.clear()
        self.logger.debug("Cleared all registered commands")


# Global command registry instance
_registry: Optional[CommandRegistry] = None


def get_registry() -> CommandRegistry:
    """
    Get the global command registry instance.

    Returns:
        CommandRegistry: The global registry
    """
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
    return _registry


def register_command(command_class: Type[BaseCommand]) -> None:
    """
    Register a command with the global registry.

    Args:
        command_class: Command class to register
    """
    registry = get_registry()
    registry.register(command_class)


def execute_command(command_name: str, args: Dict[str, Any], config: Optional[Any] = None) -> int:
    """
    Execute a command by name.

    Args:
        command_name: Name of the command to execute
        args: Command arguments
        config: Optional configuration

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    registry = get_registry()
    command = registry.create_command(command_name, config)
    return command.run(args)


def discover_commands(commands_dir: Optional[Path] = None) -> None:
    """
    Discover and register commands from the commands directory.

    Args:
        commands_dir: Path to commands directory (default: cli/commands/)
    """
    if commands_dir is None:
        # Default to cli/commands relative to the blackbox root
        commands_dir = Path(__file__).parent.parent.parent / "cli" / "commands"

    registry = get_registry()
    registry.discover_commands(commands_dir)
