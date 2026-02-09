#!/usr/bin/env python3
"""
Event Logger - Unified Agent Communication Module

Provides event logging to events.yaml for Python agents.
Matches the format used by bash agents for unified communication.

Usage:
    from event_logger import log_event, log_start, log_complete, log_error

    log_event(
        agent="scout-intelligent",
        event_type="start",
        message="Analysis started",
        run_dir="/path/to/run"
    )
"""

import os
import sys
import yaml
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add unified_config to path for path resolution
sys.path.insert(0, str(Path(__file__).parent))
from unified_config import get_path_resolver


def _get_events_file_path() -> Path:
    """Get the path to the events.yaml file."""
    path_resolver = get_path_resolver()
    project_dir = path_resolver.get_project_path()

    # Try project-level events.yaml first
    events_file = project_dir / ".autonomous" / "agents" / "communications" / "events.yaml"

    if events_file.exists():
        return events_file

    # Fall back to engine-level events.yaml
    engine_dir = path_resolver.engine_root
    events_file = engine_dir / ".autonomous" / "communications" / "events.yaml"

    return events_file


def _ensure_events_file_exists(events_file: Path) -> None:
    """Ensure the events.yaml file and its parent directories exist."""
    events_file.parent.mkdir(parents=True, exist_ok=True)

    if not events_file.exists():
        # Create initial events.yaml with header
        header = """# events.yaml - Event log for the autonomous system
# Written by: Both Planner and Executor (and Python agents)
# Purpose: Audit trail of all significant events
#
# This is an APPEND-ONLY log. Never delete or modify existing entries.

version: "1.0"

# =============================================================================
# EVENT STRUCTURE
# =============================================================================
#
# Each event has:
# - timestamp: ISO 8601 format
# - type: Event category
# - task_id: Related task (if applicable)
# - agent: Which agent generated it (planner/executor/architect)
# - run_id: Which run generated it
# - data: Additional structured data

# =============================================================================
# EVENT TYPES
# =============================================================================
#
# task_created     - New task added to tasks.yaml
# task_ready       - Task unblocked and ready for queue
# task_started     - Executor claimed task from queue
# task_completed   - Executor finished task
# task_blocked     - Task hit a blocker
# task_failed      - Task failed, needs replanning
# queue_updated    - Planner changed next_task
# discovery        - New information found during execution
# decision_made    - Significant decision recorded
# error            - System error occurred
# idle             - Executor had no work
# start            - Agent started execution
# complete         - Agent completed execution
# in_progress      - Agent is working on task

# =============================================================================
# EVENT LOG (append only)
# =============================================================================

events: []
"""
        with open(events_file, 'w') as f:
            f.write(header)


def _lock_file(f) -> None:
    """Acquire an exclusive lock on the file for thread-safe writes."""
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    except (ImportError, AttributeError):
        # fcntl not available on Windows, skip locking
        pass


def _unlock_file(f) -> None:
    """Release the lock on the file."""
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (ImportError, AttributeError):
        # fcntl not available on Windows, skip unlocking
        pass


def log_event(
    agent: str,
    event_type: str,
    message: str = "",
    run_dir: Optional[str] = None,
    task_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Log an event to events.yaml.

    Args:
        agent: Name of the agent (e.g., "scout-intelligent", "executor-implement")
        event_type: Type of event (e.g., "start", "complete", "error", "task_started")
        message: Human-readable message describing the event
        run_dir: Path to the run directory (optional)
        task_id: Related task ID (optional)
        data: Additional structured data (optional)

    Returns:
        True if event was logged successfully, False otherwise
    """
    try:
        # Get events file path
        events_file = _get_events_file_path()
        _ensure_events_file_exists(events_file)

        # Build event data
        event = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "type": event_type,
        }

        if message:
            event["message"] = message

        if run_dir:
            event["run_dir"] = str(run_dir)

        if task_id:
            event["task_id"] = task_id

        if data:
            event["data"] = data

        # Read existing events
        with open(events_file, 'r') as f:
            _lock_file(f)
            content = f.read()
            _unlock_file(f)

        # Parse YAML to find events list
        events = []
        try:
            yaml_content = yaml.safe_load(content) or {}
            if isinstance(yaml_content, dict):
                raw_events = yaml_content.get('events', [])
                if isinstance(raw_events, list):
                    events = raw_events
                elif raw_events is None:
                    events = []
        except yaml.YAMLError:
            events = []

        # Append new event
        events.append(event)

        # Write back with proper YAML structure
        # We need to preserve the header comments, so we reconstruct carefully
        with open(events_file, 'w') as f:
            _lock_file(f)

            # Write header (everything before "events:")
            header_end = content.find("events:")
            if header_end >= 0:
                f.write(content[:header_end])
                f.write("events:\n")
            else:
                f.write("events:\n")

            # Write all events
            for evt in events:
                f.write("\n")
                f.write(f"  - timestamp: \"{evt['timestamp']}\"\n")
                f.write(f"    agent: {evt['agent']}\n")
                f.write(f"    type: {evt['type']}\n")

                if 'message' in evt:
                    # Escape quotes in message
                    msg = evt['message'].replace('"', '\\"')
                    f.write(f"    message: \"{msg}\"\n")

                if 'run_dir' in evt:
                    f.write(f"    run_dir: {evt['run_dir']}\n")

                if 'task_id' in evt:
                    f.write(f"    task_id: {evt['task_id']}\n")

                if 'data' in evt and evt['data']:
                    f.write("    data:\n")
                    _write_yaml_data(f, evt['data'], indent_level=3)

            _unlock_file(f)

        return True

    except Exception as e:
        print(f"Warning: Failed to log event: {e}", file=sys.stderr)
        return False


def _write_yaml_data(f, data: Any, indent_level: int = 0) -> None:
    """Write data as YAML with proper indentation."""
    indent = "  " * indent_level

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                f.write(f"{indent}{key}:\n")
                _write_yaml_data(f, value, indent_level + 1)
            elif isinstance(value, list):
                f.write(f"{indent}{key}:\n")
                for item in value:
                    if isinstance(item, dict):
                        f.write(f"{indent}-\n")
                        _write_yaml_data(f, item, indent_level + 1)
                    else:
                        f.write(f"{indent}- {item}\n")
            else:
                # Escape quotes in string values
                if isinstance(value, str):
                    value = value.replace('"', '\\"')
                    f.write(f"{indent}{key}: \"{value}\"\n")
                else:
                    f.write(f"{indent}{key}: {value}\n")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                f.write(f"{indent}-\n")
                _write_yaml_data(f, item, indent_level + 1)
            else:
                f.write(f"{indent}- {item}\n")


def log_start(agent: str, message: str = "Agent started", run_dir: Optional[str] = None, task_id: Optional[str] = None) -> bool:
    """Log an agent start event."""
    return log_event(agent, "start", message, run_dir, task_id)


def log_complete(agent: str, message: str = "Agent completed", run_dir: Optional[str] = None, task_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> bool:
    """Log an agent completion event."""
    return log_event(agent, "complete", message, run_dir, task_id, data)


def log_error(agent: str, message: str, run_dir: Optional[str] = None, task_id: Optional[str] = None, error_details: Optional[str] = None) -> bool:
    """Log an agent error event."""
    data = {}
    if error_details:
        data["error_details"] = error_details
    return log_event(agent, "error", message, run_dir, task_id, data if data else None)


def log_task_started(agent: str, task_id: str, message: str = "Task started", run_dir: Optional[str] = None) -> bool:
    """Log a task started event."""
    return log_event(agent, "task_started", message, run_dir, task_id)


def log_task_completed(agent: str, task_id: str, message: str = "Task completed", run_dir: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> bool:
    """Log a task completed event."""
    return log_event(agent, "task_completed", message, run_dir, task_id, data)


def log_task_failed(agent: str, task_id: str, message: str = "Task failed", run_dir: Optional[str] = None, error_details: Optional[str] = None) -> bool:
    """Log a task failed event."""
    data = {}
    if error_details:
        data["error_details"] = error_details
    return log_event(agent, "task_failed", message, run_dir, task_id, data if data else None)


def log_in_progress(agent: str, message: str = "Agent in progress", run_dir: Optional[str] = None, task_id: Optional[str] = None) -> bool:
    """Log an agent in-progress event."""
    return log_event(agent, "in_progress", message, run_dir, task_id)


if __name__ == "__main__":
    # Test the module
    print("Testing event_logger module...")

    # Test basic logging
    success = log_start("test-agent", "Test start event")
    print(f"Start event logged: {success}")

    success = log_complete("test-agent", "Test complete event", data={"test": True})
    print(f"Complete event logged: {success}")

    success = log_error("test-agent", "Test error event", error_details="Something went wrong")
    print(f"Error event logged: {success}")

    print("Test complete. Check events.yaml for logged events.")
