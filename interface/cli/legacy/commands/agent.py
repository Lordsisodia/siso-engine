#!/usr/bin/env python3
"""
RALF CLI Agent Commands
========================

Commands for monitoring RALF agents:
- status: Show agent status
- start: Start an agent (placeholder)
- stop: Stop an agent (placeholder)
- restart: Restart an agent (placeholder)

Author: RALF System
Version: 1.0.0 (Feature F-016)
"""

import click
import yaml
from datetime import datetime
from ..lib.output import get_formatter
from ..lib.context import get_context


@click.group(name="agent")
def agent_cli():
    """Agent management commands."""
    pass


@agent_cli.command(name="status")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def agent_status(json_mode: bool):
    """Show agent status."""
    formatter = get_formatter(json_mode)
    context = get_context()

    # Read heartbeat file
    heartbeat_file = context.heartbeat_file

    if not heartbeat_file.exists():
        formatter.error(f"Heartbeat file not found: {heartbeat_file}")
        return

    try:
        with open(heartbeat_file) as f:
            heartbeat_data = yaml.safe_load(f)

        if not heartbeat_data or "heartbeats" not in heartbeat_data:
            formatter.warning("No heartbeat data available")
            return

        agents = heartbeat_data["heartbeats"]

        if json_mode:
            formatter.json(agents)
        else:
            formatter.panel("Agent Status", border_style="cyan")
            formatter.agent_status(agents)

            # Calculate time since last seen
            current_time = datetime.utcnow()
            for agent_name, agent_data in agents.items():
                last_seen_str = agent_data.get("last_seen", "")
                if last_seen_str:
                    try:
                        last_seen = datetime.fromisoformat(last_seen_str.replace("Z", "+00:00"))
                        time_diff = (current_time - last_seen.replace(tzinfo=None)).total_seconds()

                        if time_diff < 60:
                            status_str = f"({int(time_diff)}s ago)"
                            formatter.print(f"  Time: {status_str}", color="green")
                        elif time_diff < 300:
                            status_str = f"({int(time_diff // 60)}m ago)"
                            formatter.print(f"  Time: {status_str}", color="yellow")
                        else:
                            status_str = f"({int(time_diff // 60)}m ago - STALE)"
                            formatter.print(f"  Time: {status_str}", color="red")
                    except:
                        pass

    except Exception as e:
        formatter.error(f"Failed to read heartbeat: {e}")


@agent_cli.command(name="health")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def agent_health(json_mode: bool):
    """Show detailed agent health information."""
    formatter = get_formatter(json_mode)
    context = get_context()

    # Read heartbeat file
    heartbeat_file = context.heartbeat_file

    if not heartbeat_file.exists():
        formatter.error(f"Heartbeat file not found: {heartbeat_file}")
        return

    try:
        with open(heartbeat_file) as f:
            heartbeat_data = yaml.safe_load(f)

        if not heartbeat_data or "heartbeats" not in heartbeat_data:
            formatter.warning("No heartbeat data available")
            return

        agents = heartbeat_data["heartbeats"]
        metadata = heartbeat_data.get("metadata", {})

        if json_mode:
            formatter.json({"agents": agents, "metadata": metadata})
        else:
            formatter.panel("Agent Health", border_style="cyan")

            for agent_name, agent_data in agents.items():
                status = agent_data.get("status", "unknown")
                action = agent_data.get("current_action", "idle")
                loop = agent_data.get("loop_number", "N/A")
                run = agent_data.get("run_number", "N/A")

                formatter.print(f"\n[bold]{agent_name.upper()}[/]", color="cyan")

                # Status with color
                if status == "running":
                    formatter.print(f"  Status: {status}", color="green")
                elif status in ["stopped", "failed"]:
                    formatter.print(f"  Status: {status}", color="red")
                else:
                    formatter.print(f"  Status: {status}", color="yellow")

                formatter.print(f"  Action: {action}")
                formatter.print(f"  Loop: {loop}")
                formatter.print(f"  Run: {run}")

            # Show metadata
            if metadata:
                timeout = metadata.get("timeout_seconds", "N/A")
                updated = metadata.get("last_updated", "N/A")
                notes = metadata.get("notes", "")

                formatter.print(f"\n[bold]METADATA[/]", color="blue")
                formatter.print(f"  Timeout: {timeout}s")
                formatter.print(f"  Last Updated: {updated}")
                if notes:
                    formatter.print(f"  Notes: {notes[:100]}")

    except Exception as e:
        formatter.error(f"Failed to read heartbeat: {e}")


@agent_cli.command(name="start")
@click.argument("agent_name", type=click.Choice(["planner", "executor"]))
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def start_agent(agent_name: str, json_mode: bool):
    """Start an agent (placeholder)."""
    formatter = get_formatter(json_mode)

    formatter.info(f"Starting {agent_name} agent...")
    formatter.warning("Agent start not yet implemented through CLI")
    formatter.info("Use the automation scripts to start agents")


@agent_cli.command(name="stop")
@click.argument("agent_name", type=click.Choice(["planner", "executor"]))
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def stop_agent(agent_name: str, json_mode: bool):
    """Stop an agent (placeholder)."""
    formatter = get_formatter(json_mode)

    formatter.info(f"Stopping {agent_name} agent...")
    formatter.warning("Agent stop not yet implemented through CLI")
    formatter.info("Use the automation scripts to stop agents")


@agent_cli.command(name="restart")
@click.argument("agent_name", type=click.Choice(["planner", "executor"]))
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def restart_agent(agent_name: str, json_mode: bool):
    """Restart an agent (placeholder)."""
    formatter = get_formatter(json_mode)

    formatter.info(f"Restarting {agent_name} agent...")
    formatter.warning("Agent restart not yet implemented through CLI")
    formatter.info("Use the automation scripts to restart agents")


if __name__ == "__main__":
    agent_cli()
