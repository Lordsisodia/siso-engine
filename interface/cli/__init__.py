"""
CLI Infrastructure

This module provides the command-line interface infrastructure for BlackBox5,
including command routing, execution, and error handling.
"""

from .base import BaseCommand, CommandError, handle_errors, setup_command_logging
from .router import CommandRegistry, register_command, execute_command, discover_commands, get_registry
from .bb5 import cli, main

__all__ = [
    "BaseCommand",
    "CommandError",
    "handle_errors",
    "setup_command_logging",
    "CommandRegistry",
    "register_command",
    "execute_command",
    "discover_commands",
    "get_registry",
    "cli",
    "main",
]
