#!/usr/bin/env python3
"""
RALF CLI - Main Entry Point
============================

Unified command-line interface for RALF operations.

Usage:
    ralf task list
    ralf queue show
    ralf agent status
    ralf system health
    ralf config get <key>

Author: RALF System
Version: 1.0.0 (Feature F-016)
"""

import click
import sys
import os

# Add CLI lib to path
cli_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cli_dir)

from lib.output import get_formatter
from lib.context import get_context


@click.group()
@click.option("--project-dir", type=click.Path(exists=True), help="RALF project directory")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.pass_context
def ralf_cli(ctx, project_dir, json_mode, debug):
    """
    RALF CLI - Unified command-line interface for RALF operations.

    RALF (Recursive Autonomous Learning Framework) is an autonomous
    agent system for software development and operations.

    \b
    Common commands:
      ralf task list      List active tasks
      ralf queue show     Show task queue
      ralf agent status   Show agent status
      ralf system health  Show system health

    \b
    For help on specific commands:
      ralf <command> --help
    """
    # Set up context
    ctx.ensure_object(dict)

    try:
        context = get_context(project_dir)
        ctx.obj["context"] = context
    except Exception as e:
        formatter = get_formatter(json_mode)
        formatter.error(f"Failed to initialize context: {e}")
        formatter.info("Set RALF_PROJECT_DIR environment variable or run from project directory")
        ctx.exit(1)

    ctx.obj["json_mode"] = json_mode
    ctx.obj["debug"] = debug


# Import command groups
from commands.task import task_cli
from commands.queue import queue_cli
from commands.agent import agent_cli
from commands.system import system_cli
from commands.config import config_cli


# Register command groups
ralf_cli.add_command(task_cli)
ralf_cli.add_command(queue_cli)
ralf_cli.add_command(agent_cli)
ralf_cli.add_command(system_cli)
ralf_cli.add_command(config_cli)


@ralf_cli.command()
@click.pass_context
def version(ctx):
    """Show RALF version information."""
    json_mode = ctx.obj.get("json_mode", False)
    formatter = get_formatter(json_mode)

    version_info = {
        "system": "RALF (Recursive Autonomous Learning Framework)",
        "version": "2.0.0",
        "cli_version": "1.0.0",
        "feature": "F-016 (CLI Interface & Tooling Suite)"
    }

    if json_mode:
        formatter.json(version_info)
    else:
        formatter.panel("RALF CLI", border_style="cyan")
        formatter.key_value(version_info)


@ralf_cli.command()
@click.pass_context
def info(ctx):
    """Show RALF system information."""
    json_mode = ctx.obj.get("json_mode", False)
    context = ctx.obj.get("context")
    formatter = get_formatter(json_mode)

    info = {
        "system": "RALF (Recursive Autonomous Learning Framework)",
        "version": "2.0.0",
        "project_dir": str(context.project_dir),
        "autonomous_dir": str(context.autonomous_dir),
        "engine_dir": str(context.engine_dir),
        "runs_dir": str(context.runs_dir),
    }

    # Count runs
    if context.executor_runs_dir.exists():
        executor_runs = len(list(context.executor_runs_dir.glob("run-*")))
        info["executor_runs"] = executor_runs

    if context.planner_runs_dir.exists():
        planner_runs = len(list(context.planner_runs_dir.glob("run-*")))
        info["planner_runs"] = planner_runs

    if json_mode:
        formatter.json(info)
    else:
        formatter.panel("RALF System Information", border_style="cyan")
        formatter.key_value(info)


def main():
    """Main entry point."""
    ralf_cli(obj={})


if __name__ == "__main__":
    main()
