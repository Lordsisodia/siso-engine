#!/usr/bin/env python3
"""
Phase Gate Enforcement System for Agent-2.2

Validates that phase exit criteria are met before allowing progression.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Phase gate definitions
PHASE_GATES = {
    "quick_spec": {
        "required_files": ["quick_spec.md"],
        "exit_criteria": [
            "all_target_files_read",
            "tests_identified",
            "rollback_strategy_defined"
        ],
        "on_failure": "cannot_proceed"
    },
    "dev_story": {
        "entry_check": "quick_spec",
        "required_files": [],
        "exit_criteria": [
            "all_files_modified",
            "tests_pass",
            "commits_atomic"
        ],
        "on_failure": "rollback_and_retry"
    },
    "code_review": {
        "entry_check": "dev_story",
        "required_files": ["code_review.md"],
        "exit_criteria": [
            "conventions_followed",
            "tests_pass",
            "no_regressions"
        ],
        "on_failure": "return_to_dev_story"
    },
    "align": {
        "required_files": ["align.md"],
        "exit_criteria": [
            "problem_statement_clear",
            "success_metrics_defined",
            "mvp_scope_documented"
        ],
        "on_failure": "cannot_proceed"
    },
    "plan": {
        "entry_check": "align",
        "required_files": ["plan.md", "decision_registry.yaml"],
        "exit_criteria": [
            "architecture_decisions_documented",
            "alternatives_considered",
            "rollback_plan_specified"
        ],
        "on_failure": "cannot_proceed"
    },
    "execute": {
        "entry_check": "plan",
        "required_files": [],
        "exit_criteria": [
            "all_steps_completed",
            "tests_pass",
            "code_review_passed"
        ],
        "on_failure": "rollback_to_plan"
    },
    "validate": {
        "entry_check": "execute",
        "required_files": ["validation_report.md"],
        "exit_criteria": [
            "functional_validation_passed",
            "code_quality_check_passed",
            "regression_check_passed"
        ],
        "on_failure": "rollback_to_execute"
    },
    "wrap": {
        "entry_check": "validate",
        "required_files": [
            "THOUGHTS.md",
            "DECISIONS.md",
            "ASSUMPTIONS.md",
            "LEARNINGS.md",
            "RESULTS.md"
        ],
        "exit_criteria": [
            "all_documentation_complete",
            "retrospective_written",
            "task_status_updated"
        ],
        "on_failure": "cannot_complete"
    }
}


def check_file_exists(run_dir: str, filename: str) -> bool:
    """Check if a required file exists in the run directory."""
    file_path = Path(run_dir) / filename
    return file_path.exists()


def check_entry_gate(run_dir: str, phase: str) -> Tuple[bool, Optional[str]]:
    """Check if the entry gate (previous phase) passed."""
    gate_config = PHASE_GATES.get(phase)
    if not gate_config:
        return False, f"Unknown phase: {phase}"

    entry_check = gate_config.get("entry_check")
    if not entry_check:
        # No entry check required (first phase)
        return True, None

    # Check if entry gate passed by looking for a marker file
    marker_file = Path(run_dir) / f".gate_{entry_check}_passed"
    if marker_file.exists():
        return True, None

    return False, f"Entry gate '{entry_check}' not passed. Complete previous phase first."


def validate_phase_gate(run_dir: str, phase: str) -> Tuple[bool, List[str]]:
    """
    Validate that a phase gate criteria are met.

    Returns:
        (passed, missing_items)
    """
    gate_config = PHASE_GATES.get(phase)
    if not gate_config:
        return False, [f"Unknown phase: {phase}"]

    missing = []

    # Check entry gate
    entry_passed, entry_error = check_entry_gate(run_dir, phase)
    if not entry_passed:
        missing.append(entry_error)

    # Check required files
    for filename in gate_config.get("required_files", []):
        if not check_file_exists(run_dir, filename):
            missing.append(f"Required file missing: {filename}")

    # Check exit criteria (these are manual checks - agent must confirm)
    criteria_file = Path(run_dir) / f".phase_{phase}_criteria"
    if criteria_file.exists():
        # Agent has marked criteria as complete
        pass
    else:
        # Add criteria as items to complete
        for criterion in gate_config.get("exit_criteria", []):
            missing.append(f"Exit criterion not verified: {criterion}")

    return len(missing) == 0, missing


def mark_gate_passed(run_dir: str, phase: str):
    """Mark a phase gate as passed."""
    marker_file = Path(run_dir) / f".gate_{phase}_passed"
    marker_file.touch()
    print(f"✓ Phase gate '{phase}' passed")


def mark_criteria_complete(run_dir: str, phase: str):
    """Mark phase criteria as manually verified."""
    criteria_file = Path(run_dir) / f".phase_{phase}_criteria"
    criteria_file.touch()


def main():
    if len(sys.argv) < 2:
        print("Usage: phase_gates.py <command> [options]")
        print("Commands:")
        print("  check --phase <phase> --run-dir <run_dir>")
        print("  mark --phase <phase> --run-dir <run_dir>")
        sys.exit(1)

    command = sys.argv[1]

    # Parse arguments
    args = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i].startswith("--"):
            key = sys.argv[i][2:]
            if i + 1 < len(sys.argv):
                args[key] = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        else:
            i += 1

    run_dir = args.get("run-dir") or args.get("run_dir")
    phase = args.get("phase")

    if not run_dir or not phase:
        print("Error: --phase and --run-dir are required")
        sys.exit(1)

    if command == "check":
        passed, missing = validate_phase_gate(run_dir, phase)

        if passed:
            print(f"✓ Phase gate '{phase}' validation passed")
            print("  You may proceed to the next phase.")
            sys.exit(0)
        else:
            print(f"✗ Phase gate '{phase}' validation FAILED")
            print("\nMissing requirements:")
            for item in missing:
                print(f"  - {item}")
            print(f"\nCannot proceed to next phase until resolved.")
            sys.exit(1)

    elif command == "mark":
        mark_criteria_complete(run_dir, phase)
        mark_gate_passed(run_dir, phase)
        print(f"Marked phase '{phase}' as complete")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
