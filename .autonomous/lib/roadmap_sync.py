#!/usr/bin/env python3
"""
 =============================================================================
 ROADMAP STATE SYNC LIBRARY
 =============================================================================
 Purpose: Automatically synchronize roadmap STATE.yaml and improvement-backlog.yaml when tasks complete
 Author: RALF Executor
 Version: 2.0.0
 =============================================================================

 This library provides functions to keep the roadmap STATE.yaml and improvement-backlog.yaml
 in sync with actual task completion. When a task completes, it:
 1. Updates the associated plan status in STATE.yaml
 2. Unblocks dependent plans
 3. Updates next_action
 4. Updates improvement status in improvement-backlog.yaml (if applicable)

 USAGE:
     from roadmap_sync import sync_roadmap_on_task_completion, sync_improvement_backlog

     # Sync both roadmap and improvement backlog
     result = sync_roadmap_on_task_completion(
         task_id="TASK-1769911101",
         state_yaml_path="/path/to/STATE.yaml"
     )

     # Sync only improvement backlog
     result = sync_improvement_backlog(
         task_id="TASK-1769911101",
         improvement_backlog_path="/path/to/improvement-backlog.yaml"
     )

 DESIGN PRINCIPLES:
 1. Non-blocking: If sync fails, log error but do not fail task completion
 2. Idempotent: Can run multiple times safely
 3. Validated: Prevent corruption with validation checks
 4. Logged: All changes are logged for audit trail
 5. Safe: Creates backup before modifying files

 =============================================================================
"""
import os
import sys
import re
import yaml
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


# =============================================================================
# LOGGING
# =============================================================================

def log_message(message: str, level: str = "INFO") -> None:
    """Simple logging function"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{timestamp}] [{level}] ROADMAP_SYNC: {message}")


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_state_yaml(state_data: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate STATE.yaml structure before processing.

    Returns:
        (is_valid, error_message)
    """
    if not isinstance(state_data, dict):
        return False, "STATE.yaml root is not a dictionary"

    # Check for required top-level keys
    required_keys = ["plans", "next_action"]
    for key in required_keys:
        if key not in state_data:
            return False, f"Missing required key: {key}"

    # Validate plans structure
    if not isinstance(state_data["plans"], dict):
        return False, "plans section is not a dictionary"

    # Check for expected plan sections
    plan_sections = ["ready_to_start", "blocked", "completed"]
    for section in plan_sections:
        if section in state_data["plans"]:
            if not isinstance(state_data["plans"][section], list):
                return False, f"plans.{section} is not a list"

    return True, None


# =============================================================================
# PLAN FINDING FUNCTIONS
# =============================================================================

def extract_plan_id_from_task(task_id: str, task_content: str = None) -> Optional[str]:
    """
    Extract PLAN-ID from task content or title.

    Args:
        task_id: Task ID (e.g., "TASK-1769911101")
        task_content: Optional task file content to search

    Returns:
        Plan ID (e.g., "PLAN-003") or None if not found
    """
    # Method 1: Check if task_content is provided and search for PLAN-XXX pattern
    if task_content:
        # Look for "PLAN-XXX" patterns
        plan_matches = re.findall(r'PLAN-(\d{3})', task_content, re.IGNORECASE)
        if plan_matches:
            # Return the first (most likely) plan ID
            return f"PLAN-{plan_matches[0]}"

        # Look for "plan id: PLAN-XXX" pattern
        plan_id_match = re.search(r'plan[_\s]?id:\s*PLAN-(\d{3})', task_content, re.IGNORECASE)
        if plan_id_match:
            return f"PLAN-{plan_id_match.group(1)}"

    # Method 2: Check task ID itself (some tasks are named like TASK-XXX-plan-YYY)
    plan_match = re.search(r'PLAN-(\d{3})', task_id, re.IGNORECASE)
    if plan_match:
        return f"PLAN-{plan_match.group(1)}"

    # Method 3: Check task file name pattern
    filename_match = re.search(r'plan[_\s-]?0*(\d+)', task_id.lower())
    if filename_match:
        plan_num = filename_match.group(1).zfill(3)
        return f"PLAN-{plan_num}"

    return None


def find_plan_by_id(state_data: Dict, plan_id: str) -> Optional[Dict]:
    """
    Find a plan in STATE.yaml by its ID.

    Args:
        state_data: Parsed STATE.yaml content
        plan_id: Plan ID to find (e.g., "PLAN-003")

    Returns:
        Plan dictionary or None if not found
    """
    plan_id_normalized = plan_id.upper().strip()

    # Search in all plan sections
    for section in ["ready_to_start", "blocked", "completed"]:
        if section in state_data.get("plans", {}):
            for plan in state_data["plans"][section]:
                if plan.get("id", "").upper() == plan_id_normalized:
                    return plan

    return None


def find_plan_by_task_id(state_data: Dict, task_id: str) -> Optional[Dict]:
    """
    Find a plan in STATE.yaml by associated task ID.

    This searches for plans that reference the given task ID.
    Note: Current STATE.yaml structure does not store task_id in plans,
    so this function uses pattern matching on plan names.

    Args:
        state_data: Parsed STATE.yaml content
        task_id: Task ID to search for

    Returns:
        Plan dictionary or None if not found
    """
    # Extract potential plan ID from task ID
    potential_plan_id = extract_plan_id_from_task(task_id)
    if potential_plan_id:
        return find_plan_by_id(state_data, potential_plan_id)

    return None


# =============================================================================
# PLAN UPDATE FUNCTIONS
# =============================================================================

def move_plan_to_completed(state_data: Dict, plan: Dict, executed_by: str = "RALF") -> Dict:
    """
    Move a plan from its current section to "completed".

    Args:
        state_data: Parsed STATE.yaml content
        plan: Plan dictionary to move
        executed_by: Who executed this plan

    Returns:
        Updated plan dictionary with completion metadata
    """
    plan_id = plan.get("id", "UNKNOWN")

    # Remove plan from current section
    for section in ["ready_to_start", "blocked"]:
        if section in state_data.get("plans", {}):
            state_data["plans"][section] = [
                p for p in state_data["plans"][section]
                if p.get("id") != plan_id
            ]

    # Add completion metadata
    plan_updated = plan.copy()
    plan_updated["completed_at"] = datetime.utcnow().strftime("%Y-%m-%d")
    plan_updated["executed_by"] = executed_by

    # Add to completed section
    if "completed" not in state_data["plans"]:
        state_data["plans"]["completed"] = []
    state_data["plans"]["completed"].append(plan_updated)

    return plan_updated


def unblock_dependent_plans(state_data: Dict, completed_plan_id: str) -> List[str]:
    """
    Unblock plans that were waiting for the completed plan.

    Args:
        state_data: Parsed STATE.yaml content
        completed_plan_id: ID of the completed plan

    Returns:
        List of plan IDs that were unblocked
    """
    completed_plan_id_normalized = completed_plan_id.upper().strip()
    unblocked = []

    # Check all blocked plans
    if "blocked" in state_data.get("plans", {}):
        plans_to_move = []

        for plan in state_data["plans"]["blocked"]:
            dependencies = plan.get("dependencies", [])
            if isinstance(dependencies, list):
                # Remove completed plan from dependencies
                new_dependencies = [
                    d for d in dependencies
                    if str(d).upper() != completed_plan_id_normalized
                ]

                if len(new_dependencies) < len(dependencies):
                    # Dependency was removed
                    plan["dependencies"] = new_dependencies

                    # If no more dependencies, plan is ready to start
                    if not new_dependencies:
                        plans_to_move.append(plan)
                        unblocked.append(plan.get("id", "UNKNOWN"))

        # Move unblocked plans to ready_to_start
        for plan in plans_to_move:
            state_data["plans"]["blocked"].remove(plan)
            if "ready_to_start" not in state_data["plans"]:
                state_data["plans"]["ready_to_start"] = []
            state_data["plans"]["ready_to_start"].append(plan)

    return unblocked


def update_next_action(state_data: Dict) -> Optional[str]:
    """
    Update next_action to the first ready-to-start plan.

    Args:
        state_data: Parsed STATE.yaml content

    Returns:
        New next_action plan ID or None
    """
    ready_plans = state_data.get("plans", {}).get("ready_to_start", [])

    if ready_plans:
        # Sort by priority (high > medium > low > immediate)
        priority_order = {"immediate": 0, "critical": 0, "high": 1, "medium": 2, "low": 3}
        ready_plans.sort(key=lambda p: priority_order.get(p.get("priority", "low"), 99))

        next_plan = ready_plans[0]
        next_plan_id = next_plan.get("id")
        state_data["next_action"] = next_plan_id
        return next_plan_id

    # No ready plans, clear next_action
    state_data["next_action"] = None
    return None


# =============================================================================
# MAIN SYNC FUNCTION
# =============================================================================

def sync_roadmap_on_task_completion(
    task_id: str,
    state_yaml_path: str,
    task_content: str = None,
    executed_by: str = "RALF Executor",
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Update STATE.yaml when a task completes.

    This is the main entry point for roadmap synchronization.
    It finds the plan associated with the completed task, marks it as
    completed, unblocks dependent plans, and updates next_action.

    Args:
        task_id: Completed task ID (e.g., "TASK-1769911101")
        state_yaml_path: Full path to STATE.yaml
        task_content: Optional task file content for better plan detection
        executed_by: Agent/user who completed the task
        dry_run: If True, do not actually write changes

    Returns:
        {
            "success": bool,
            "plan_id": str or None,
            "changes": list of change descriptions,
            "error": str or None
        }
    """
    result = {
        "success": False,
        "plan_id": None,
        "changes": [],
        "error": None
    }

    try:
        # Step 1: Read STATE.yaml
        log_message(f"Reading STATE.yaml from {state_yaml_path}")

        if not os.path.exists(state_yaml_path):
            result["error"] = f"STATE.yaml not found at {state_yaml_path}"
            log_message(result["error"], "ERROR")
            return result

        with open(state_yaml_path, 'r') as f:
            state_data = yaml.safe_load(f)

        # Step 2: Validate STATE.yaml structure
        is_valid, error_msg = validate_state_yaml(state_data)
        if not is_valid:
            result["error"] = f"Invalid STATE.yaml structure: {error_msg}"
            log_message(result["error"], "ERROR")
            return result

        # Step 3: Find associated plan
        log_message(f"Looking for plan associated with task {task_id}")

        # First try to find by task content
        plan = find_plan_by_task_id(state_data, task_id)

        # If not found, try extracting plan ID from task_id itself
        if not plan and task_content:
            potential_plan_id = extract_plan_id_from_task(task_id, task_content)
            if potential_plan_id:
                plan = find_plan_by_id(state_data, potential_plan_id)

        # If still not found, try just the task_id pattern
        if not plan:
            potential_plan_id = extract_plan_id_from_task(task_id)
            if potential_plan_id:
                plan = find_plan_by_id(state_data, potential_plan_id)

        if not plan:
            result["error"] = f"No plan found associated with task {task_id}"
            log_message(result["error"], "WARN")
            # Not a failure - task might not be associated with a plan
            result["success"] = True
            return result

        plan_id = plan.get("id", "UNKNOWN")
        log_message(f"Found associated plan: {plan_id}")

        # Check if plan is already completed
        if plan.get("completed_at"):
            result["error"] = f"Plan {plan_id} is already marked as completed"
            log_message(result["error"], "WARN")
            result["success"] = True
            result["plan_id"] = plan_id
            return result

        # Step 4: Create backup
        if not dry_run:
            backup_path = f"{state_yaml_path}.backup.{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(state_yaml_path, backup_path)
            log_message(f"Created backup: {backup_path}")

        # Step 5: Move plan to completed
        log_message(f"Moving plan {plan_id} to completed")
        plan_updated = move_plan_to_completed(state_data, plan, executed_by)
        result["changes"].append(f"Moved plan {plan_id} to completed")
        result["plan_id"] = plan_id

        # Step 6: Unblock dependent plans
        log_message("Unblocking dependent plans")
        unblocked = unblock_dependent_plans(state_data, plan_id)
        if unblocked:
            result["changes"].append(f"Unblocked {len(unblocked)} plan(s): {', '.join(unblocked)}")
            log_message(f"Unblocked: {', '.join(unblocked)}")

        # Step 7: Update next_action
        log_message("Updating next_action")
        old_next_action = state_data.get("next_action")
        new_next_action = update_next_action(state_data)

        if new_next_action:
            result["changes"].append(f"Updated next_action to {new_next_action}")
            log_message(f"next_action: {old_next_action} -> {new_next_action}")
        elif old_next_action:
            result["changes"].append("Cleared next_action (no ready plans)")
            log_message("next_action cleared (no ready plans)")

        # Step 8: Write updated STATE.yaml
        if not dry_run:
            # Update system metadata
            state_data["system"]["updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            state_data["system"]["updated_by"] = executed_by

            # Update stats
            total_plans = (
                len(state_data.get("plans", {}).get("ready_to_start", [])) +
                len(state_data.get("plans", {}).get("blocked", [])) +
                len(state_data.get("plans", {}).get("completed", []))
            )
            completed_count = len(state_data.get("plans", {}).get("completed", []))

            if "stats" not in state_data:
                state_data["stats"] = {}
            state_data["stats"]["total"] = total_plans
            state_data["stats"]["completed"] = completed_count

            # Write to file
            with open(state_yaml_path, 'w') as f:
                yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

            log_message(f"Updated STATE.yaml written successfully")

        result["success"] = True
        log_message(f"Roadmap sync completed successfully for plan {plan_id}")

        return result

    except Exception as e:
        error_msg = f"Exception during roadmap sync: {str(e)}"
        result["error"] = error_msg
        log_message(error_msg, "ERROR")
        return result


# =============================================================================
# IMPROVEMENT BACKLOG SYNC FUNCTIONS
# =============================================================================

def extract_improvement_id_from_task(task_content: str) -> Optional[str]:
    """
    Extract IMP-ID from task content.

    Args:
        task_content: Task file content to search

    Returns:
        Improvement ID (e.g., "IMP-1769903001") or None if not found
    """
    # Look for "**Improvement:** IMP-XXX" pattern (markdown bold format in task files)
    improvement_match = re.search(r'\*\*[Ii]mprovement:\*\*\s*IMP-(\d+)', task_content, re.IGNORECASE)
    if improvement_match:
        return f"IMP-{improvement_match.group(1)}"

    # Look for "improvement: IMP-XXX" pattern (standard format)
    improvement_match = re.search(r'improvement:\s*IMP-(\d+)', task_content, re.IGNORECASE)
    if improvement_match:
        return f"IMP-{improvement_match.group(1)}"

    # Look for "Improvement:" or "Related Improvement:" patterns (non-bold)
    for pattern in [r'(?:Related )?[Ii]mprovement:\s*IMP-(\d+)', r'IMP-(\d+)']:
        matches = re.findall(pattern, task_content, re.IGNORECASE)
        if matches:
            return f"IMP-{matches[0]}"

    return None


def find_improvement_in_backlog(backlog_data: Dict, improvement_id: str) -> Optional[Dict]:
    """
    Find an improvement in improvement-backlog.yaml by its ID.

    Args:
        backlog_data: Parsed improvement-backlog.yaml content
        improvement_id: Improvement ID to find (e.g., "IMP-1769903001")

    Returns:
        Improvement dictionary or None if not found
    """
    improvement_id_normalized = improvement_id.upper().strip()

    # Search in all priority sections
    for section in ["high_priority", "medium_priority", "low_priority"]:
        if section in backlog_data.get("backlog", {}):
            for improvement in backlog_data["backlog"][section]:
                if improvement.get("id", "").upper() == improvement_id_normalized:
                    return improvement

    return None


def update_improvement_status(
    backlog_data: Dict,
    improvement: Dict,
    completed_at: str,
    completed_by: str
) -> Dict:
    """
    Update an improvement's status to completed.

    Args:
        backlog_data: Parsed improvement-backlog.yaml content
        improvement: Improvement dictionary to update
        completed_at: Timestamp of completion
        completed_by: Task or agent that completed it

    Returns:
        Updated improvement dictionary
    """
    improvement_id = improvement.get("id", "UNKNOWN")

    # Update improvement fields
    improvement["status"] = "completed"
    improvement["completed_at"] = completed_at
    improvement["completed_by"] = completed_by

    return improvement


def move_improvement_to_completed_section(
    backlog_data: Dict,
    improvement: Dict
) -> None:
    """
    Move an improvement from its priority section to a completed section.

    Note: This is a placeholder for future structural changes.
    Current improvement-backlog.yaml doesn't have a separate "completed" section,
    so improvements just get their status updated to "completed" in place.

    Args:
        backlog_data: Parsed improvement-backlog.yaml content
        improvement: Improvement dictionary to move
    """
    # Current structure keeps improvements in their priority sections
    # Just marking status as "completed" is sufficient
    pass


def sync_improvement_backlog(
    task_id: str,
    improvement_backlog_path: str,
    task_content: str = None,
    completed_at: str = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Update improvement-backlog.yaml when a task completes.

    This function updates the status of associated improvements when a task
    that implements them completes. It extracts the improvement ID from the
    task content and updates the backlog.

    Args:
        task_id: Completed task ID (e.g., "TASK-1769911101")
        improvement_backlog_path: Full path to improvement-backlog.yaml
        task_content: Task file content (required to extract improvement ID)
        completed_at: Timestamp of completion (defaults to now)
        dry_run: If True, do not actually write changes

    Returns:
        {
            "success": bool,
            "improvement_id": str or None,
            "changes": list of change descriptions,
            "error": str or None
        }
    """
    result = {
        "success": False,
        "improvement_id": None,
        "changes": [],
        "error": None
    }

    try:
        # Step 1: Set default completion timestamp
        if not completed_at:
            completed_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Step 2: Read improvement-backlog.yaml
        log_message(f"Reading improvement-backlog.yaml from {improvement_backlog_path}")

        if not os.path.exists(improvement_backlog_path):
            result["error"] = f"improvement-backlog.yaml not found at {improvement_backlog_path}"
            log_message(result["error"], "WARN")
            # Not a failure - task might not be associated with an improvement
            result["success"] = True
            return result

        with open(improvement_backlog_path, 'r') as f:
            backlog_data = yaml.safe_load(f)

        # Step 3: Validate improvement-backlog.yaml structure
        if "backlog" not in backlog_data:
            result["error"] = "Invalid improvement-backlog.yaml structure: missing 'backlog' key"
            log_message(result["error"], "WARN")
            result["success"] = True
            return result

        # Step 4: Extract improvement ID from task content
        if not task_content:
            result["error"] = "Task content required to extract improvement ID"
            log_message(result["error"], "WARN")
            result["success"] = True
            return result

        log_message(f"Extracting improvement ID from task {task_id}")
        improvement_id = extract_improvement_id_from_task(task_content)

        if not improvement_id:
            result["error"] = f"No improvement ID found in task {task_id}"
            log_message(result["error"], "WARN")
            # Not a failure - task might not implement an improvement
            result["success"] = True
            return result

        log_message(f"Found improvement ID: {improvement_id}")

        # Step 5: Find improvement in backlog
        improvement = find_improvement_in_backlog(backlog_data, improvement_id)

        if not improvement:
            result["error"] = f"Improvement {improvement_id} not found in backlog"
            log_message(result["error"], "WARN")
            result["success"] = True
            return result

        # Step 6: Check if already completed
        if improvement.get("status") == "completed":
            result["error"] = f"Improvement {improvement_id} is already marked as completed"
            log_message(result["error"], "WARN")
            result["success"] = True
            result["improvement_id"] = improvement_id
            return result

        # Step 7: Create backup
        if not dry_run:
            backup_path = f"{improvement_backlog_path}.backup.{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(improvement_backlog_path, backup_path)
            log_message(f"Created backup: {backup_path}")

        # Step 8: Update improvement status
        log_message(f"Updating improvement {improvement_id} status to completed")
        improvement_updated = update_improvement_status(
            backlog_data,
            improvement,
            completed_at,
            task_id
        )
        result["changes"].append(f"Marked improvement {improvement_id} as completed")
        result["improvement_id"] = improvement_id

        # Step 9: Write updated improvement-backlog.yaml
        if not dry_run:
            # Update metadata (add updated_at and updated_by if they don't exist)
            if "updated_at" not in backlog_data["backlog"]["metadata"]:
                backlog_data["backlog"]["metadata"]["updated_at"] = completed_at
            else:
                backlog_data["backlog"]["metadata"]["updated_at"] = completed_at
            if "updated_by" not in backlog_data["backlog"]["metadata"]:
                backlog_data["backlog"]["metadata"]["updated_by"] = task_id
            else:
                backlog_data["backlog"]["metadata"]["updated_by"] = task_id

            # Write to file
            with open(improvement_backlog_path, 'w') as f:
                f.write("# =============================================================================\n")
                f.write("# Improvement Backlog - Extracted from Learnings\n")
                f.write("# =============================================================================\n")
                f.write(f"# Last Updated: {completed_at}\n")
                f.write(f"# Updated By: {task_id}\n")
                f.write("# =============================================================================\n\n")
                yaml.dump(backlog_data, f, default_flow_style=False, sort_keys=False)

            log_message(f"Updated improvement-backlog.yaml written successfully")

        result["success"] = True
        log_message(f"Improvement backlog sync completed successfully for {improvement_id}")

        return result

    except Exception as e:
        error_msg = f"Exception during improvement backlog sync: {str(e)}"
        result["error"] = error_msg
        log_message(error_msg, "ERROR")
        return result


def sync_both_on_task_completion(
    task_id: str,
    state_yaml_path: str,
    improvement_backlog_path: str,
    task_content: str = None,
    executed_by: str = "RALF Executor",
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Update both STATE.yaml and improvement-backlog.yaml when a task completes.

    This is a convenience function that calls both sync functions.
    Returns combined results.

    Args:
        task_id: Completed task ID (e.g., "TASK-1769911101")
        state_yaml_path: Full path to STATE.yaml
        improvement_backlog_path: Full path to improvement-backlog.yaml
        task_content: Task file content (required for improvement sync)
        executed_by: Agent/user who completed the task
        dry_run: If True, do not actually write changes

    Returns:
        {
            "success": bool,
            "roadmap_sync": dict (roadmap sync result),
            "improvement_sync": dict (improvement sync result),
            "error": str or None
        }
    """
    result = {
        "success": True,
        "roadmap_sync": None,
        "improvement_sync": None,
        "error": None
    }

    # Sync roadmap STATE.yaml
    roadmap_result = sync_roadmap_on_task_completion(
        task_id=task_id,
        state_yaml_path=state_yaml_path,
        task_content=task_content,
        executed_by=executed_by,
        dry_run=dry_run
    )
    result["roadmap_sync"] = roadmap_result

    # Sync improvement backlog (if task content provided)
    if task_content:
        completed_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        improvement_result = sync_improvement_backlog(
            task_id=task_id,
            improvement_backlog_path=improvement_backlog_path,
            task_content=task_content,
            completed_at=completed_at,
            dry_run=dry_run
        )
        result["improvement_sync"] = improvement_result

    return result


def sync_all_on_task_completion(
    task_id: str,
    state_yaml_path: str,
    improvement_backlog_path: str,
    queue_path: str,
    active_dir: str,
    task_content: str = None,
    executed_by: str = "RALF Executor",
    dry_run: bool = False,
    duration_seconds: int = 0,
    run_number: int = 0,
    task_result: str = "success"
) -> Dict[str, Any]:
    """
    Update STATE.yaml, improvement-backlog.yaml, queue.yaml, and metrics dashboard when a task completes.

    This is a convenience function that calls all four sync functions.
    Returns combined results.

    Args:
        task_id: Completed task ID (e.g., "TASK-1769911101")
        state_yaml_path: Full path to STATE.yaml
        improvement_backlog_path: Full path to improvement-backlog.yaml
        queue_path: Full path to queue.yaml
        active_dir: Full path to active/ directory
        task_content: Task file content (required for improvement sync)
        executed_by: Agent/user who completed the task
        dry_run: If True, do not actually write changes
        duration_seconds: Task duration in seconds (for metrics update)
        run_number: Executor run number (for metrics update)
        task_result: Task result "success", "failure", or "partial" (for metrics update)

    Returns:
        {
            "success": bool,
            "roadmap_sync": dict (roadmap sync result),
            "improvement_sync": dict (improvement sync result),
            "queue_sync": dict (queue sync result),
            "metrics_sync": dict (metrics sync result),
            "error": str or None
        }
    """
    result = {
        "success": True,
        "roadmap_sync": None,
        "improvement_sync": None,
        "queue_sync": None,
        "metrics_sync": None,
        "error": None
    }

    # Sync roadmap STATE.yaml
    roadmap_result = sync_roadmap_on_task_completion(
        task_id=task_id,
        state_yaml_path=state_yaml_path,
        task_content=task_content,
        executed_by=executed_by,
        dry_run=dry_run
    )
    result["roadmap_sync"] = roadmap_result

    # Sync improvement backlog (if task content provided)
    if task_content:
        completed_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        improvement_result = sync_improvement_backlog(
            task_id=task_id,
            improvement_backlog_path=improvement_backlog_path,
            task_content=task_content,
            completed_at=completed_at,
            dry_run=dry_run
        )
        result["improvement_sync"] = improvement_result

    # Sync queue.yaml
    try:
        # Import queue_sync module
        import sys
        import os
        roadmap_sync_dir = os.path.dirname(os.path.abspath(__file__))
        if roadmap_sync_dir not in sys.path:
            sys.path.insert(0, roadmap_sync_dir)

        from queue_sync import sync_queue_on_task_completion

        queue_result = sync_queue_on_task_completion(
            queue_path=queue_path,
            active_dir=active_dir,
            dry_run=dry_run
        )
        result["queue_sync"] = queue_result

    except Exception as e:
        # Queue sync failure should not fail the entire operation
        log_message(f"Queue sync failed (non-critical): {str(e)}", "WARN")
        result["queue_sync"] = {
            "success": False,
            "error": str(e),
            "removed_count": 0
        }

    # Sync metrics dashboard
    try:
        # Import metrics_updater module
        import sys
        import os
        roadmap_sync_dir = os.path.dirname(os.path.abspath(__file__))
        if roadmap_sync_dir not in sys.path:
            sys.path.insert(0, roadmap_sync_dir)

        from metrics_updater import update_metrics_on_task_completion

        # Derive project_dir from state_yaml_path
        # state_yaml_path is like: /workspaces/blackbox5/6-roadmap/STATE.yaml
        # We need: /workspaces/blackbox5/5-project-memory/blackbox5
        # Use queue_path to derive: queue_path is like: /workspaces/blackbox5/5-project-memory/blackbox5/.autonomous/communications/queue.yaml
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(queue_path)))

        metrics_result = update_metrics_on_task_completion(
            project_dir=project_dir,
            task_id=task_id,
            duration_seconds=duration_seconds,
            result=task_result,
            run_number=run_number,
            dry_run=dry_run
        )
        result["metrics_sync"] = metrics_result

    except Exception as e:
        # Metrics sync failure should not fail the entire operation
        log_message(f"Metrics sync failed (non-critical): {str(e)}", "WARN")
        result["metrics_sync"] = {
            "success": False,
            "error": str(e),
            "updated_sections": []
        }

    return result


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """CLI interface for manual testing"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python roadmap_sync.py roadmap <task_id> <state_yaml_path> [--dry-run]")
        print("  python roadmap_sync.py improvement <task_id> <improvement_backlog_path> <task_file> [--dry-run]")
        print("  python roadmap_sync.py both <task_id> <state_yaml_path> <improvement_backlog_path> <task_file> [--dry-run]")
        print("  python roadmap_sync.py all <task_id> <state_yaml_path> <improvement_backlog_path> <queue_path> <active_dir> <task_file> [--dry-run]")
        print("\nExamples:")
        print('  python roadmap_sync.py roadmap TASK-1769911101 /workspaces/blackbox5/6-roadmap/STATE.yaml')
        print('  python roadmap_sync.py improvement TASK-1769911101 /workspaces/blackbox5/5-project-memory/blackbox5/operations/improvement-backlog.yaml task.md')
        print('  python roadmap_sync.py both TASK-1769911101 /workspaces/blackbox5/6-roadmap/STATE.yaml /workspaces/blackbox5/5-project-memory/blackbox5/operations/improvement-backlog.yaml task.md')
        print('  python roadmap_sync.py all TASK-1769911101 /workspaces/blackbox5/6-roadmap/STATE.yaml /workspaces/blackbox5/5-project-memory/blackbox5/operations/improvement-backlog.yaml /workspaces/blackbox5/5-project-memory/blackbox5/.autonomous/communications/queue.yaml /workspaces/blackbox5/5-project-memory/blackbox5/.autonomous/tasks/active task.md')
        sys.exit(1)

    mode = sys.argv[1].lower()
    dry_run = "--dry-run" in sys.argv

    if mode == "roadmap":
        if len(sys.argv) < 4:
            print("Error: roadmap mode requires <task_id> and <state_yaml_path>")
            sys.exit(1)

        task_id = sys.argv[2]
        state_yaml_path = sys.argv[3]

        print(f"\n{'='*70}")
        print(f"ROADMAP SYNC - {task_id}")
        print(f"{'='*70}\n")

        result = sync_roadmap_on_task_completion(
            task_id=task_id,
            state_yaml_path=state_yaml_path,
            executed_by="manual_cli",
            dry_run=dry_run
        )

        print(f"\n{'='*70}")
        print(f"RESULTS")
        print(f"{'='*70}\n")

        print(f"Success: {result['success']}")
        print(f"Plan ID: {result.get('plan_id', 'N/A')}")

        if result['changes']:
            print(f"\nChanges made:")
            for change in result['changes']:
                print(f"  - {change}")

        if result.get('error'):
            print(f"\nError: {result['error']}")

        sys.exit(0 if result['success'] else 1)

    elif mode == "improvement":
        if len(sys.argv) < 5:
            print("Error: improvement mode requires <task_id>, <improvement_backlog_path>, and <task_file>")
            sys.exit(1)

        task_id = sys.argv[2]
        improvement_backlog_path = sys.argv[3]
        task_file = sys.argv[4]

        # Read task file
        with open(task_file, 'r') as f:
            task_content = f.read()

        print(f"\n{'='*70}")
        print(f"IMPROVEMENT BACKLOG SYNC - {task_id}")
        print(f"{'='*70}\n")

        result = sync_improvement_backlog(
            task_id=task_id,
            improvement_backlog_path=improvement_backlog_path,
            task_content=task_content,
            dry_run=dry_run
        )

        print(f"\n{'='*70}")
        print(f"RESULTS")
        print(f"{'='*70}\n")

        print(f"Success: {result['success']}")
        print(f"Improvement ID: {result.get('improvement_id', 'N/A')}")

        if result['changes']:
            print(f"\nChanges made:")
            for change in result['changes']:
                print(f"  - {change}")

        if result.get('error'):
            print(f"\nError: {result['error']}")

        sys.exit(0 if result['success'] else 1)

    elif mode == "both":
        if len(sys.argv) < 6:
            print("Error: both mode requires <task_id>, <state_yaml_path>, <improvement_backlog_path>, and <task_file>")
            sys.exit(1)

        task_id = sys.argv[2]
        state_yaml_path = sys.argv[3]
        improvement_backlog_path = sys.argv[4]
        task_file = sys.argv[5]

        # Read task file
        with open(task_file, 'r') as f:
            task_content = f.read()

        print(f"\n{'='*70}")
        print(f"FULL SYNC (ROADMAP + IMPROVEMENT) - {task_id}")
        print(f"{'='*70}\n")

        result = sync_both_on_task_completion(
            task_id=task_id,
            state_yaml_path=state_yaml_path,
            improvement_backlog_path=improvement_backlog_path,
            task_content=task_content,
            executed_by="manual_cli",
            dry_run=dry_run
        )

        print(f"\n{'='*70}")
        print(f"RESULTS")
        print(f"{'='*70}\n")

        print(f"Overall Success: {result['success']}")

        if result.get('roadmap_sync'):
            print(f"\n--- Roadmap Sync ---")
            print(f"Success: {result['roadmap_sync']['success']}")
            print(f"Plan ID: {result['roadmap_sync'].get('plan_id', 'N/A')}")
            if result['roadmap_sync']['changes']:
                print(f"Changes:")
                for change in result['roadmap_sync']['changes']:
                    print(f"  - {change}")

        if result.get('improvement_sync'):
            print(f"\n--- Improvement Sync ---")
            print(f"Success: {result['improvement_sync']['success']}")
            print(f"Improvement ID: {result['improvement_sync'].get('improvement_id', 'N/A')}")
            if result['improvement_sync']['changes']:
                print(f"Changes:")
                for change in result['improvement_sync']['changes']:
                    print(f"  - {change}")

        sys.exit(0 if result['success'] else 1)

    elif mode == "all":
        if len(sys.argv) < 8:
            print("Error: all mode requires <task_id>, <state_yaml_path>, <improvement_backlog_path>, <queue_path>, <active_dir>, and <task_file>")
            print("Optional: <duration_seconds> <run_number> <task_result>")
            sys.exit(1)

        task_id = sys.argv[2]
        state_yaml_path = sys.argv[3]
        improvement_backlog_path = sys.argv[4]
        queue_path = sys.argv[5]
        active_dir = sys.argv[6]
        task_file = sys.argv[7]

        # Optional metrics parameters
        duration_seconds = int(sys.argv[8]) if len(sys.argv) > 8 else 0
        run_number = int(sys.argv[9]) if len(sys.argv) > 9 else 0
        task_result = sys.argv[10] if len(sys.argv) > 10 else "success"

        # Read task file
        with open(task_file, 'r') as f:
            task_content = f.read()

        print(f"\n{'='*70}")
        print(f"FULL SYNC (ROADMAP + IMPROVEMENT + QUEUE + METRICS) - {task_id}")
        print(f"{'='*70}\n")

        result = sync_all_on_task_completion(
            task_id=task_id,
            state_yaml_path=state_yaml_path,
            improvement_backlog_path=improvement_backlog_path,
            queue_path=queue_path,
            active_dir=active_dir,
            task_content=task_content,
            executed_by="manual_cli",
            dry_run=dry_run,
            duration_seconds=duration_seconds,
            run_number=run_number,
            task_result=task_result
        )

        print(f"\n{'='*70}")
        print(f"RESULTS")
        print(f"{'='*70}\n")

        print(f"Overall Success: {result['success']}")

        if result.get('roadmap_sync'):
            print(f"\n--- Roadmap Sync ---")
            print(f"Success: {result['roadmap_sync']['success']}")
            print(f"Plan ID: {result['roadmap_sync'].get('plan_id', 'N/A')}")
            if result['roadmap_sync']['changes']:
                print(f"Changes:")
                for change in result['roadmap_sync']['changes']:
                    print(f"  - {change}")

        if result.get('improvement_sync'):
            print(f"\n--- Improvement Sync ---")
            print(f"Success: {result['improvement_sync']['success']}")
            print(f"Improvement ID: {result['improvement_sync'].get('improvement_id', 'N/A')}")
            if result['improvement_sync']['changes']:
                print(f"Changes:")
                for change in result['improvement_sync']['changes']:
                    print(f"  - {change}")

        if result.get('queue_sync'):
            print(f"\n--- Queue Sync ---")
            print(f"Success: {result['queue_sync']['success']}")
            print(f"Tasks removed: {result['queue_sync'].get('removed_count', 0)}")
            print(f"Tasks remaining: {result['queue_sync'].get('remaining_count', 0)}")
            if result['queue_sync'].get('removed_tasks'):
                print(f"Removed tasks:")
                for task_id in result['queue_sync']['removed_tasks']:
                    print(f"  - {task_id}")

        if result.get('metrics_sync'):
            print(f"\n--- Metrics Sync ---")
            print(f"Success: {result['metrics_sync']['success']}")
            print(f"Updated sections: {', '.join(result['metrics_sync'].get('updated_sections', []))}")
            if result['metrics_sync'].get('changes'):
                print(f"Changes:")
                for change in result['metrics_sync']['changes']:
                    print(f"  - {change}")

        sys.exit(0 if result['success'] else 1)

    else:
        print(f"Error: Unknown mode '{mode}'. Use 'roadmap', 'improvement', 'both', or 'all'")
        sys.exit(1)


if __name__ == "__main__":
    main()
