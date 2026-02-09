#!/usr/bin/env python3
"""
RALF CLI Task Commands
======================

Commands for managing RALF tasks:
- list: List active tasks
- show: Show task details
- claim: Claim a task
- complete: Mark task complete

Author: RALF System
Version: 1.0.0 (Feature F-016)
"""

import click
import yaml
from pathlib import Path
from typing import Optional
from ..lib.output import get_formatter
from ..lib.context import get_context


@click.group(name="task")
def task_cli():
    """Task management commands."""
    pass


@task_cli.command(name="list")
@click.option("--status", type=click.Choice(["pending", "in_progress", "completed", "all"]), default="all", help="Filter by status")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def list_tasks(status: str, json_mode: bool):
    """List active tasks."""
    formatter = get_formatter(json_mode)
    context = get_context()

    # Read active tasks directory
    active_dir = context.active_tasks_dir
    completed_dir = context.completed_tasks_dir

    tasks = []

    # Read active tasks
    if status in ["pending", "in_progress", "all"]:
        if active_dir.exists():
            for task_file in active_dir.glob("TASK-*.md"):
                task_data = _parse_task_file(task_file)
                if task_data:
                    if status == "all" or task_data.get("status", "pending") == status:
                        tasks.append(task_data)

    # Read completed tasks
    if status in ["completed", "all"]:
        if completed_dir.exists():
            for task_file in completed_dir.glob("TASK-*.md"):
                task_data = _parse_task_file(task_file)
                if task_data and task_data.get("status") == "completed":
                    tasks.append(task_data)

    # Sort by task ID
    tasks.sort(key=lambda x: x.get("task_id", ""))

    formatter.task_list(tasks)


@task_cli.command(name="show")
@click.argument("task_id")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def show_task(task_id: str, json_mode: bool):
    """Show task details."""
    formatter = get_formatter(json_mode)
    context = get_context()

    # Find task file
    task_file = _find_task_file(context, task_id)

    if not task_file:
        formatter.error(f"Task not found: {task_id}")
        return

    # Parse task file
    task_data = _parse_task_file(task_file)

    if not task_data:
        formatter.error(f"Failed to parse task: {task_id}")
        return

    # Display task details
    if json_mode:
        formatter.json(task_data)
    else:
        formatter.panel(f"Task: {task_id}", border_style="cyan")
        formatter.key_value(task_data)


@task_cli.command(name="claim")
@click.argument("task_id")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def claim_task(task_id: str, json_mode: bool):
    """Claim a task manually."""
    formatter = get_formatter(json_mode)
    context = get_context()

    # Find task file
    task_file = _find_task_file(context, task_id)

    if not task_file:
        formatter.error(f"Task not found: {task_id}")
        return

    formatter.info(f"Task {task_id} found at: {task_file}")
    formatter.info("To claim this task, update the task status to 'in_progress' in the file.")


@task_cli.command(name="complete")
@click.argument("task_id")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def complete_task(task_id: str, json_mode: bool):
    """Mark a task as complete."""
    formatter = get_formatter(json_mode)
    context = get_context()

    # Find task file
    task_file = _find_task_file(context, task_id)

    if not task_file:
        formatter.error(f"Task not found: {task_id}")
        return

    formatter.info(f"Task {task_id} found at: {task_file}")
    formatter.info("To complete this task:")
    formatter.info("1. Update task status to 'completed' in the file")
    formatter.info("2. Move the file to tasks/completed/ directory")


def _parse_task_file(task_file: Path) -> Optional[dict]:
    """Parse task file and extract metadata."""
    try:
        content = task_file.read_text()

        # Extract task ID from filename or content
        task_id = task_file.stem

        # Extract title (first line after #)
        lines = content.split("\n")
        title = ""
        for line in lines:
            if line.strip().startswith("#"):
                title = line.strip().lstrip("#").strip()
                break

        # Extract status
        status = "pending"
        for line in lines:
            if line.strip().startswith("**Status:**"):
                status = line.split(":")[1].strip().lower()
                break

        # Extract priority
        priority = "medium"
        for line in lines:
            if line.strip().startswith("**Priority:**"):
                priority = line.split(":")[1].strip().lower()
                break

        # Extract feature ID
        feature_id = "N/A"
        for line in lines:
            if "Feature" in line and "F-" in line:
                parts = line.split("F-")
                if len(parts) > 1:
                    feature_id = "F-" + parts[1].split()[0].strip(")")
                break

        return {
            "task_id": task_id,
            "title": title,
            "status": status,
            "priority": priority,
            "feature_id": feature_id,
            "file_path": str(task_file)
        }
    except Exception as e:
        return None


def _find_task_file(context, task_id: str) -> Optional[Path]:
    """Find task file by ID."""
    # Check active tasks
    active_dir = context.active_tasks_dir
    if active_dir.exists():
        for task_file in active_dir.glob(f"{task_id}.md"):
            return task_file

    # Check completed tasks
    completed_dir = context.completed_tasks_dir
    if completed_dir.exists():
        for task_file in completed_dir.glob(f"{task_id}.md"):
            return task_file

    return None


if __name__ == "__main__":
    task_cli()
