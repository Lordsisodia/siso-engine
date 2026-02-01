#!/usr/bin/env python3
"""
 =============================================================================
 ROADMAP STATE SYNC LIBRARY
 =============================================================================
 Purpose: Automatically synchronize roadmap STATE.yaml when tasks complete
 Author: RALF Executor
 Version: 1.0.0
 =============================================================================

 This library provides functions to keep the roadmap STATE.yaml in sync with
 actual task completion. When a task completes, it updates the associated plan
 status, unblocks dependent plans, and updates next_action.

 USAGE:
     from roadmap_sync import sync_roadmap_on_task_completion

     result = sync_roadmap_on_task_completion(
         task_id="TASK-1769911101",
         state_yaml_path="/path/to/STATE.yaml"
     )

     if result["success"]:
         print(f"Updated plan {result['plan_id']}")
     else:
         print(f"Sync failed: {result['error']}")

 DESIGN PRINCIPLES:
 1. Non-blocking: If sync fails, log error but do not fail task completion
 2. Idempotent: Can run multiple times safely
 3. Validated: Prevent corruption with validation checks
 4. Logged: All changes are logged for audit trail
 5. Safe: Creates backup before modifying STATE.yaml

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
# CLI INTERFACE
# =============================================================================

def main():
    """CLI interface for manual testing"""
    if len(sys.argv) < 3:
        print("Usage: python roadmap_sync.py <task_id> <state_yaml_path> [--dry-run]")
        print("\nExample:")
        print('  python roadmap_sync.py TASK-1769911101 /workspaces/blackbox5/6-roadmap/STATE.yaml')
        print('  python roadmap_sync.py TASK-1769911101 /workspaces/blackbox5/6-roadmap/STATE.yaml --dry-run')
        sys.exit(1)

    task_id = sys.argv[1]
    state_yaml_path = sys.argv[2]
    dry_run = "--dry-run" in sys.argv

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

    print(f"\n{'='*70}\n")

    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
