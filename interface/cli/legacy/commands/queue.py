#!/usr/bin/env python3
"""
RALF CLI Queue Commands
========================

Commands for managing RALF task queue:
- show: Display queue with priority scores
- add: Add task from backlog
- remove: Remove task from queue
- reorder: Reorder by priority

Author: RALF System
Version: 1.0.0 (Feature F-016)
"""

import click
import yaml
from pathlib import Path
from typing import Optional
from ..lib.output import get_formatter
from ..lib.context import get_context


@click.group(name="queue")
def queue_cli():
    """Queue management commands."""
    pass


@queue_cli.command(name="show")
@click.option("--status", type=click.Choice(["pending", "completed", "all"]), default="pending", help="Filter by status")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def show_queue(status: str, json_mode: bool):
    """Show task queue with priorities."""
    formatter = get_formatter(json_mode)
    context = get_context()

    # Read queue file
    queue_file = context.queue_file

    if not queue_file.exists():
        formatter.error(f"Queue file not found: {queue_file}")
        return

    try:
        with open(queue_file) as f:
            queue_data = yaml.safe_load(f)

        if not queue_data or "queue" not in queue_data:
            formatter.warning("Queue is empty or malformed")
            return

        # Filter by status
        queue = queue_data["queue"]
        if status != "all":
            queue = [t for t in queue if t.get("status") == status]

        if not queue:
            formatter.info(f"No tasks with status: {status}")
            return

        # Display queue
        if json_mode:
            formatter.json(queue)
        else:
            formatter.panel(f"Task Queue ({len(queue)} tasks)", border_style="cyan")

            # Convert to table format
            table_data = []
            for task in queue:
                table_data.append({
                    "Task ID": task.get("task_id", "N/A"),
                    "Feature": task.get("feature_id", "N/A"),
                    "Title": task.get("title", "")[:50],
                    "Status": task.get("status", "unknown"),
                    "Priority": task.get("priority", "medium"),
                    "Score": task.get("priority_score", 0)
                })

            formatter.table(table_data, title="Queue", columns=[
                "Task ID", "Feature", "Title", "Status", "Priority", "Score"
            ])

            # Show metadata
            metadata = queue_data.get("metadata", {})
            if metadata:
                formatter.info(f"Queue depth: {metadata.get('current_depth', 'N/A')} (target: {metadata.get('queue_depth_target', 'N/A')})")

    except Exception as e:
        formatter.error(f"Failed to read queue: {e}")


@queue_cli.command(name="add")
@click.argument("feature_id")
@click.option("--priority", type=click.Choice(["critical", "high", "medium", "low"]), default="medium", help="Task priority")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def add_to_queue(feature_id: str, priority: str, json_mode: bool):
    """Add task from backlog to queue."""
    formatter = get_formatter(json_mode)
    context = get_context()

    formatter.info(f"Adding feature {feature_id} to queue with priority {priority}")
    formatter.info("Note: This requires updating queue.yaml. Manual editing currently required.")


@queue_cli.command(name="remove")
@click.argument("task_id")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def remove_from_queue(task_id: str, json_mode: bool):
    """Remove task from queue."""
    formatter = get_formatter(json_mode)
    context = get_context()

    formatter.info(f"Removing task {task_id} from queue")
    formatter.info("Note: This requires updating queue.yaml. Manual editing currently required.")


@queue_cli.command(name="reorder")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def reorder_queue(json_mode: bool):
    """Reorder queue by priority score."""
    formatter = get_formatter(json_mode)
    context = get_context()

    # Read queue file
    queue_file = context.queue_file

    if not queue_file.exists():
        formatter.error(f"Queue file not found: {queue_file}")
        return

    try:
        with open(queue_file) as f:
            queue_data = yaml.safe_load(f)

        if not queue_data or "queue" not in queue_data:
            formatter.warning("Queue is empty or malformed")
            return

        # Sort queue by priority score (descending)
        queue = queue_data["queue"]
        queue.sort(key=lambda x: x.get("priority_score", 0), reverse=True)

        # Update queue data
        queue_data["queue"] = queue

        formatter.success("Queue reordered by priority score (highest first)")
        formatter.info("Note: Saving changes requires write access to queue.yaml")

    except Exception as e:
        formatter.error(f"Failed to reorder queue: {e}")


@queue_cli.command(name="stats")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def queue_stats(json_mode: bool):
    """Show queue statistics."""
    formatter = get_formatter(json_mode)
    context = get_context()

    # Read queue file
    queue_file = context.queue_file

    if not queue_file.exists():
        formatter.error(f"Queue file not found: {queue_file}")
        return

    try:
        with open(queue_file) as f:
            queue_data = yaml.safe_load(f)

        if not queue_data or "queue" not in queue_data:
            formatter.warning("Queue is empty or malformed")
            return

        queue = queue_data["queue"]

        # Calculate statistics
        total = len(queue)
        pending = len([t for t in queue if t.get("status") == "pending"])
        in_progress = len([t for t in queue if t.get("status") == "in_progress"])
        completed = len([t for t in queue if t.get("status") == "completed"])

        # Priority breakdown
        high_priority = len([t for t in queue if t.get("priority") in ["critical", "high"]])

        stats = {
            "total_tasks": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "high_priority": high_priority,
            "completion_rate": f"{(completed / total * 100):.1f}%" if total > 0 else "N/A"
        }

        if json_mode:
            formatter.json(stats)
        else:
            formatter.panel("Queue Statistics", border_style="cyan")
            formatter.key_value(stats)

    except Exception as e:
        formatter.error(f"Failed to calculate stats: {e}")


if __name__ == "__main__":
    queue_cli()
