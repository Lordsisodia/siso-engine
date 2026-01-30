"""
Base Command Infrastructure for BlackBox5 CLI

This module provides the abstract base class for all CLI commands,
including common execution interfaces, error handling, and logging setup.
"""

import logging
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Dict, Optional, List


class CommandError(Exception):
    """Base exception for command execution errors."""

    def __init__(self, message: str, exit_code: int = 1, details: Optional[Dict[str, Any]] = None):
        """
        Initialize command error.

        Args:
            message: Human-readable error message
            exit_code: Process exit code to use
            details: Additional error context
        """
        self.message = message
        self.exit_code = exit_code
        self.details = details or {}
        super().__init__(self.message)


class BaseCommand(ABC):
    """
    Abstract base class for all CLI commands.

    All commands must inherit from this class and implement the execute() method.
    Provides common functionality for logging, error handling, and validation.
    """

    # Command metadata (to be overridden by subclasses)
    name: str = ""
    description: str = ""
    aliases: List[str] = []

    def __init__(self, config: Optional[Any] = None):
        """
        Initialize the command.

        Args:
            config: Optional configuration object
        """
        self.config = config
        self.logger = logging.getLogger(f"cli.{self.name or self.__class__.__name__}")

    @abstractmethod
    def execute(self, args: Dict[str, Any]) -> int:
        """
        Execute the command with given arguments.

        This method must be implemented by all command subclasses.

        Args:
            args: Parsed command-line arguments as a dictionary

        Returns:
            int: Exit code (0 for success, non-zero for failure)

        Raises:
            CommandError: If command execution fails
        """
        pass

    def validate_args(self, args: Dict[str, Any]) -> None:
        """
        Validate command arguments before execution.

        Override this method to add custom validation logic.

        Args:
            args: Parsed command-line arguments

        Raises:
            ValueError: If arguments are invalid
        """
        pass

    def pre_execute(self, args: Dict[str, Any]) -> None:
        """
        Hook called before command execution.

        Override this method to add pre-execution logic like
        setup, validation, or logging.

        Args:
            args: Parsed command-line arguments
        """
        self.logger.info(f"Executing command: {self.name}")
        if self.config and hasattr(self.config, 'debug') and self.config.debug:
            self.logger.debug(f"Arguments: {args}")

    def post_execute(self, result: int, args: Dict[str, Any]) -> None:
        """
        Hook called after command execution.

        Override this method to add post-execution logic like
        cleanup, reporting, or notifications.

        Args:
            result: Exit code from command execution
            args: Parsed command-line arguments
        """
        if result == 0:
            self.logger.info(f"Command '{self.name}' completed successfully")
        else:
            self.logger.warning(f"Command '{self.name}' completed with exit code {result}")

    def run(self, args: Dict[str, Any]) -> int:
        """
        Run the command with full lifecycle hooks.

        This method wraps execute() with validation, pre/post hooks,
        and error handling.

        Args:
            args: Parsed command-line arguments

        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        try:
            # Validate arguments
            self.validate_args(args)

            # Pre-execution hook
            self.pre_execute(args)

            # Execute the command
            result = self.execute(args)

            # Post-execution hook
            self.post_execute(result, args)

            return result

        except CommandError as e:
            self.logger.error(f"Command error: {e.message}")
            if e.details:
                self.logger.debug(f"Error details: {e.details}")
            return e.exit_code

        except Exception as e:
            self.logger.exception(f"Unexpected error in command '{self.name}': {e}")
            return 1

    def get_help(self) -> str:
        """
        Get help text for this command.

        Returns:
            str: Help text describing the command
        """
        help_text = f"{self.name}: {self.description}\n"
        if self.aliases:
            help_text += f"Aliases: {', '.join(self.aliases)}\n"
        return help_text


def handle_errors(func):
    """
    Decorator for handling command execution errors.

    Catches exceptions and converts them to appropriate exit codes.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CommandError as e:
            logging.error(f"Command failed: {e.message}")
            return e.exit_code
        except KeyboardInterrupt:
            logging.info("Command interrupted by user")
            return 130  # Standard exit code for SIGINT
        except Exception as e:
            logging.exception(f"Unexpected error: {e}")
            return 1

    return wrapper


def setup_command_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    """
    Set up logging for CLI commands.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Optional custom format string
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        force=True  # Override any existing configuration
    )
