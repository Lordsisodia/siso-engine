#!/usr/bin/env python3
"""
RALF CLI System Commands
========================

Commands for system monitoring:
- health: Show system health
- metrics: Show performance metrics
- logs: View system logs (placeholder)
- version: Show version info

Author: RALF System
Version: 1.0.0 (Feature F-016)
"""

import click
import yaml
from pathlib import Path
from datetime import datetime
from ..lib.output import get_formatter
from ..lib.context import get_context


@click.group(name="system")
def system_cli():
    """System monitoring commands."""
    pass


@system_cli.command(name="health")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def system_health(json_mode: bool):
    """Show overall system health."""
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

        # Calculate overall health
        all_healthy = all(
            agent.get("status") == "running"
            for agent in agents.values()
        )

        health_status = "healthy" if all_healthy else "degraded"

        if json_mode:
            formatter.json({
                "status": health_status,
                "agents": agents,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            formatter.panel("System Health", border_style="cyan")

            # Overall status
            if health_status == "healthy":
                formatter.health_status("HEALTHY", {"all_agents": "running"})
            else:
                formatter.health_status("DEGRADED", {"some_agents": "not running"})

            # Individual agent status
            for agent_name, agent_data in agents.items():
                status = agent_data.get("status", "unknown")
                action = agent_data.get("current_action", "idle")
                formatter.print(f"\n[bold]{agent_name.upper()}[/]")
                formatter.health_status(status, {"action": action})

            # Queue info
            queue_file = context.queue_file
            if queue_file.exists():
                try:
                    with open(queue_file) as f:
                        queue_data = yaml.safe_load(f)

                    if queue_data and "queue" in queue_data:
                        queue = queue_data["queue"]
                        metadata = queue_data.get("metadata", {})

                        pending = len([t for t in queue if t.get("status") == "pending"])
                        in_progress = len([t for t in queue if t.get("status") == "in_progress"])
                        completed = len([t for t in queue if t.get("status") == "completed"])

                        formatter.print(f"\n[bold]QUEUE[/]")
                        formatter.print(f"  Pending: {pending}")
                        formatter.print(f"  In Progress: {in_progress}")
                        formatter.print(f"  Completed: {completed}")
                        formatter.print(f"  Depth: {metadata.get('current_depth', 'N/A')}")
                except:
                    pass

    except Exception as e:
        formatter.error(f"Failed to check system health: {e}")


@system_cli.command(name="metrics")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def system_metrics(json_mode: bool):
    """Show performance metrics."""
    formatter = get_formatter(json_mode)
    context = get_context()

    # Analyze executor runs
    executor_runs_dir = context.executor_runs_dir

    if not executor_runs_dir.exists():
        formatter.warning(f"Executor runs directory not found: {executor_runs_dir}")
        return

    try:
        runs = list(executor_runs_dir.glob("run-*"))

        if not runs:
            formatter.info("No executor runs found")
            return

        # Count runs and calculate stats
        total_runs = len(runs)

        # Count completed tasks
        completed_count = 0
        total_duration = 0

        for run_dir in runs:
            metadata_file = run_dir / "metadata.yaml"
            if metadata_file.exists():
                try:
                    with open(metadata_file) as f:
                        metadata = yaml.safe_load(f)

                    if metadata and metadata.get("state", {}).get("task_status") == "completed":
                        completed_count += 1

                    duration = metadata.get("loop", {}).get("duration_seconds", 0)
                    if duration:
                        total_duration += duration
                except:
                    pass

        avg_duration = total_duration / completed_count if completed_count > 0 else 0
        success_rate = (completed_count / total_runs * 100) if total_runs > 0 else 0

        metrics = {
            "total_runs": total_runs,
            "completed_tasks": completed_count,
            "success_rate": f"{success_rate:.1f}%",
            "avg_duration_seconds": f"{avg_duration:.1f}",
            "total_execution_time_seconds": f"{total_duration:.1f}"
        }

        if json_mode:
            formatter.json(metrics)
        else:
            formatter.panel("Performance Metrics", border_style="cyan")
            formatter.key_value(metrics)

    except Exception as e:
        formatter.error(f"Failed to calculate metrics: {e}")


@system_cli.command(name="logs")
@click.option("--tail", type=int, default=10, help="Number of lines to show")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def system_logs(tail: int, json_mode: bool):
    """View system logs (placeholder)."""
    formatter = get_formatter(json_mode)

    formatter.info(f"Showing last {tail} log lines...")
    formatter.warning("Log viewing not yet implemented through CLI")
    formatter.info("Check runs/executor/run-NNNN/ for execution logs")
    formatter.info("Check runs/planner/run-NNNN/ for planning logs")


@system_cli.command(name="version")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def system_version(json_mode: bool):
    """Show version information."""
    formatter = get_formatter(json_mode)

    version_info = {
        "system": "RALF (Recursive Autonomous Learning Framework)",
        "version": "2.0.0",
        "cli_version": "1.0.0 (Feature F-016)",
        "features": "12+ features delivered",
        "status": "active"
    }

    if json_mode:
        formatter.json(version_info)
    else:
        formatter.panel("RALF Version", border_style="cyan")
        formatter.key_value(version_info)


@system_cli.command(name="info")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def system_info(json_mode: bool):
    """Show detailed system information."""
    formatter = get_formatter(json_mode)
    context = get_context()

    info = {
        "project_dir": str(context.project_dir),
        "autonomous_dir": str(context.autonomous_dir),
        "engine_dir": str(context.engine_dir),
        "runs_dir": str(context.runs_dir),
        "executor_runs": len(list(context.executor_runs_dir.glob("run-*"))) if context.executor_runs_dir.exists() else 0,
        "planner_runs": len(list(context.planner_runs_dir.glob("run-*"))) if context.planner_runs_dir.exists() else 0,
    }

    if json_mode:
        formatter.json(info)
    else:
        formatter.panel("System Information", border_style="cyan")
        formatter.key_value(info)


if __name__ == "__main__":
    system_cli()
