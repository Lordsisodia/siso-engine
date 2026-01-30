#!/usr/bin/env python3
"""
Phase Gate Enforcement System for Agent-2.3

Validates that phase exit criteria are met before allowing progression.
Provides detailed, actionable feedback when gates fail.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class GateStatus(Enum):
    """Status of a phase gate check."""
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class GateCheckResult:
    """Result of a phase gate validation."""
    status: GateStatus
    phase: str
    missing_items: List[str]
    suggestions: List[str]
    examples: Dict[str, str]
    next_steps: List[str]


def get_phase_gate_config(phase: str) -> Optional[Dict]:
    """Get configuration for a phase gate."""
    return PHASE_GATES.get(phase)


# Phase gate definitions with detailed feedback configuration
PHASE_GATES = {
    "quick_spec": {
        "required_files": ["quick_spec.md"],
        "exit_criteria": [
            "all_target_files_read",
            "tests_identified",
            "rollback_strategy_defined"
        ],
        "on_failure": "cannot_proceed",
        "feedback": {
            "all_target_files_read": {
                "description": "All target files must be read before making changes",
                "suggestion": "Use Read or Task tools to read all files you plan to modify",
                "example": "Read(file_path='/path/to/file.py') before proposing changes"
            },
            "tests_identified": {
                "description": "Tests for the changes must be identified",
                "suggestion": "Look for existing test files or identify where new tests should go",
                "example": "Find tests in: tests/, test_*.py, *_test.py, or co-located with source"
            },
            "rollback_strategy_defined": {
                "description": "A rollback strategy must be defined for risky changes",
                "suggestion": "Document how to undo changes if something goes wrong",
                "example": "Rollback: git checkout -- <files> or restore from backup branch"
            }
        },
        "quick_spec_template": """# Quick Spec: [Brief Description]

## Files to Modify
- [ ] `path/to/file1.py` - [purpose]
- [ ] `path/to/file2.py` - [purpose]

## Tests
- [ ] Existing tests: `path/to/test_file.py`
- [ ] New tests needed: [yes/no]

## Rollback Strategy
- Backup branch: `git checkout -b backup/[timestamp]`
- Or: `git checkout -- <files>` to discard changes

## Risk Level
- [ ] LOW - Simple change, easy to undo
- [ ] MEDIUM - Moderate impact, needs testing
- [ ] HIGH - Breaking change, careful review needed
"""
    },
    "dev_story": {
        "entry_check": "quick_spec",
        "required_files": [],
        "exit_criteria": [
            "all_files_modified",
            "tests_pass",
            "commits_atomic"
        ],
        "on_failure": "rollback_and_retry",
        "feedback": {
            "all_files_modified": {
                "description": "All planned file modifications must be complete",
                "suggestion": "Check quick_spec.md and ensure all listed files are modified",
                "example": "If quick_spec lists 3 files, all 3 should have changes"
            },
            "tests_pass": {
                "description": "All tests must pass before proceeding",
                "suggestion": "Run tests and fix any failures",
                "example": "pytest tests/ or npm test - all green before proceeding"
            },
            "commits_atomic": {
                "description": "Changes must be committed atomically",
                "suggestion": "Each logical change should be a separate commit",
                "example": "git add file.py && git commit -m 'specific change description'"
            }
        }
    },
    "code_review": {
        "entry_check": "dev_story",
        "required_files": ["code_review.md"],
        "exit_criteria": [
            "conventions_followed",
            "tests_pass",
            "no_regressions"
        ],
        "on_failure": "return_to_dev_story",
        "feedback": {
            "conventions_followed": {
                "description": "Code must follow project conventions",
                "suggestion": "Check style guide, naming conventions, and patterns",
                "example": "Follow existing patterns in the codebase"
            },
            "tests_pass": {
                "description": "All tests must still pass",
                "suggestion": "Run full test suite to verify no regressions",
                "example": "pytest tests/ -v to see all test results"
            },
            "no_regressions": {
                "description": "No functionality should be broken",
                "suggestion": "Test manually if needed to verify behavior",
                "example": "Run the application and verify core features work"
            }
        }
    },
    "align": {
        "required_files": ["align.md"],
        "exit_criteria": [
            "problem_statement_clear",
            "success_metrics_defined",
            "mvp_scope_documented"
        ],
        "on_failure": "cannot_proceed",
        "feedback": {
            "problem_statement_clear": {
                "description": "The problem being solved must be clearly stated",
                "suggestion": "Write 1-2 sentences describing what problem this solves",
                "example": "Problem: Users cannot export data, causing manual work"
            },
            "success_metrics_defined": {
                "description": "Success must be measurable",
                "suggestion": "Define specific, measurable success criteria",
                "example": "Success: Export completes in < 2 seconds, supports CSV and JSON"
            },
            "mvp_scope_documented": {
                "description": "Minimum viable scope must be defined",
                "suggestion": "List what is IN scope and what is OUT of scope",
                "example": "IN: CSV export, basic filtering. OUT: Excel, advanced filters"
            }
        },
        "align_template": """# ALIGN: [Feature Name]

## Problem Statement
[Clear 1-2 sentence description of the problem]

## Users Affected
- [User type 1]: [how they are affected]
- [User type 2]: [how they are affected]

## MVP Scope
### IN Scope
- [Feature 1]
- [Feature 2]

### OUT of Scope (Future)
- [Feature 3]
- [Feature 4]

## Success Metrics
- [ ] [Metric 1]: [target]
- [ ] [Metric 2]: [target]

## Constraints & Risks
- Constraint: [limitation]
- Risk: [potential issue] → Mitigation: [how to address]
"""
    },
    "plan": {
        "entry_check": "align",
        "required_files": ["plan.md", "decision_registry.yaml"],
        "exit_criteria": [
            "architecture_decisions_documented",
            "alternatives_considered",
            "rollback_plan_specified"
        ],
        "on_failure": "cannot_proceed",
        "feedback": {
            "architecture_decisions_documented": {
                "description": "Key architecture decisions must be documented",
                "suggestion": "Document WHY choices were made, not just WHAT",
                "example": "Decision: Use PostgreSQL over MongoDB. Rationale: ACID compliance needed."
            },
            "alternatives_considered": {
                "description": "Alternatives must be considered and documented",
                "suggestion": "List at least 2 alternatives for major decisions",
                "example": "Considered: A) REST API, B) GraphQL, C) gRPC. Chose: A."
            },
            "rollback_plan_specified": {
                "description": "A rollback plan must be specified",
                "suggestion": "Document how to undo the implementation if needed",
                "example": "Rollback: 1) Run migration down, 2) Revert commits, 3) Update config"
            }
        },
        "plan_template": """# PLAN: [Feature Name]

## Architecture Decisions

### Decision 1: [What was decided]
- **Rationale**: [Why this choice]
- **Alternatives Considered**:
  - Option A: [description] → [why rejected]
  - Option B: [description] → [why rejected]
- **Reversibility**: [HIGH/MEDIUM/LOW]

## Implementation Steps
1. [Step 1 with specific details]
2. [Step 2 with specific details]
3. [Step 3 with specific details]

## Risk Mitigation
- Risk: [description] → Mitigation: [action]

## Testing Strategy
- Unit tests: [what to test]
- Integration tests: [what to test]
- Manual testing: [what to verify]

## Rollback Plan
1. [Step 1 to rollback]
2. [Step 2 to rollback]
"""
    },
    "execute": {
        "entry_check": "plan",
        "required_files": [],
        "exit_criteria": [
            "all_steps_completed",
            "tests_pass",
            "code_review_passed"
        ],
        "on_failure": "rollback_to_plan",
        "feedback": {
            "all_steps_completed": {
                "description": "All implementation steps must be completed",
                "suggestion": "Check plan.md and ensure all steps are done",
                "example": "If plan lists 5 steps, all 5 should be checked off"
            },
            "tests_pass": {
                "description": "All tests must pass",
                "suggestion": "Run tests after each change, fix failures immediately",
                "example": "pytest tests/ -x (stop on first failure)"
            },
            "code_review_passed": {
                "description": "Code review must be completed",
                "suggestion": "Self-review or peer review the changes",
                "example": "Check: conventions, tests, documentation, edge cases"
            }
        }
    },
    "validate": {
        "entry_check": "execute",
        "required_files": ["validation_report.md"],
        "exit_criteria": [
            "functional_validation_passed",
            "code_quality_check_passed",
            "regression_check_passed"
        ],
        "on_failure": "rollback_to_execute",
        "feedback": {
            "functional_validation_passed": {
                "description": "Functional validation must pass",
                "suggestion": "Test that the feature works as specified",
                "example": "Run through user scenarios, verify expected behavior"
            },
            "code_quality_check_passed": {
                "description": "Code quality checks must pass",
                "suggestion": "Run linters, type checkers, and coverage tools",
                "example": "flake8, mypy, pytest --cov - all should pass"
            },
            "regression_check_passed": {
                "description": "No regressions must be introduced",
                "suggestion": "Test existing functionality to ensure nothing broke",
                "example": "Run full test suite, manual smoke tests"
            }
        }
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
        "on_failure": "cannot_complete",
        "feedback": {
            "all_documentation_complete": {
                "description": "All required documentation must be complete",
                "suggestion": "Create all 5 required documentation files",
                "example": "THOUGHTS.md, DECISIONS.md, ASSUMPTIONS.md, LEARNINGS.md, RESULTS.md"
            },
            "retrospective_written": {
                "description": "A retrospective must be written",
                "suggestion": "Reflect on what went well and what could improve",
                "example": "What worked? What didn't? What would you do differently?"
            },
            "task_status_updated": {
                "description": "Task status must be updated",
                "suggestion": "Mark task as complete and move to completed folder",
                "example": "Update task file status and move to tasks/completed/"
            }
        },
        "documentation_templates": {
            "THOUGHTS.md": """# Thoughts

## Initial Understanding
[What I understood about the problem]

## Approach
[How I decided to solve it]

## Key Decisions
[Important decisions made during execution]

## Challenges
[What was difficult and how I addressed it]
""",
            "DECISIONS.md": """# Decisions

## DEC-001: [Decision Title]
- **Context**: [What led to this decision]
- **Decision**: [What was decided]
- **Rationale**: [Why this choice]
- **Consequences**: [Impact of this decision]
""",
            "ASSUMPTIONS.md": """# Assumptions

## Verified
- [ASSUMPTION-001]: [Statement] → Verified by: [how]

## Pending Verification
- [ASSUMPTION-002]: [Statement] → Verify by: [when/how]

## Proven Wrong
- [ASSUMPTION-003]: [Statement] → Actually: [what was true]
""",
            "LEARNINGS.md": """# Learnings

## Technical
- [What I learned technically]

## Process
- [What I learned about the process]

## Surprises
- [Unexpected discoveries]
""",
            "RESULTS.md": """# Results

## What Was Delivered
- [List of deliverables]

## Validation Results
- Tests: [X/Y passed]
- Coverage: [Z%]
- Manual testing: [results]

## Known Issues
- [Any issues or limitations]
"""
        }
    }
}


def check_file_exists(run_dir: str, filename: str) -> bool:
    """Check if a required file exists in the run directory."""
    file_path = Path(run_dir) / filename
    return file_path.exists()


def check_entry_gate(run_dir: str, phase: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if the entry gate (previous phase) passed.

    Returns:
        (passed, error_message, suggestion)
    """
    gate_config = PHASE_GATES.get(phase)
    if not gate_config:
        return False, f"Unknown phase: {phase}", "Check phase name and try again"

    entry_check = gate_config.get("entry_check")
    if not entry_check:
        # No entry check required (first phase)
        return True, None, None

    # Check if entry gate passed by looking for a marker file
    marker_file = Path(run_dir) / f".gate_{entry_check}_passed"
    if marker_file.exists():
        return True, None, None

    suggestion = f"Complete the '{entry_check}' phase first by running:\n"
    suggestion += f"  python3 phase_gates.py mark --phase {entry_check} --run-dir {run_dir}"

    return False, f"Entry gate '{entry_check}' not passed", suggestion


def get_detailed_feedback(phase: str, missing_criteria: List[str]) -> Tuple[List[str], Dict[str, str], List[str]]:
    """
    Get detailed feedback for missing criteria.

    Returns:
        (suggestions, examples, next_steps)
    """
    gate_config = PHASE_GATES.get(phase, {})
    feedback_config = gate_config.get("feedback", {})

    suggestions = []
    examples = {}
    next_steps = []

    for criterion in missing_criteria:
        # Extract criterion name from message like "Exit criterion not verified: criterion_name"
        if "Exit criterion not verified:" in criterion:
            criterion_name = criterion.split("Exit criterion not verified:")[1].strip()
        elif "Required file missing:" in criterion:
            filename = criterion.split("Required file missing:")[1].strip()
            suggestions.append(f"Create the required file: {filename}")
            if filename.endswith('.md'):
                template_key = filename.replace('.md', '_template')
                if template_key in gate_config:
                    examples[filename] = gate_config[template_key]
            continue
        else:
            criterion_name = criterion

        if criterion_name in feedback_config:
            config = feedback_config[criterion_name]
            suggestions.append(f"{config['description']}: {config['suggestion']}")
            examples[criterion_name] = config['example']
            next_steps.append(config['suggestion'])
        else:
            # Generic feedback
            suggestions.append(f"Complete: {criterion_name}")
            next_steps.append(f"Address: {criterion_name}")

    return suggestions, examples, next_steps


def validate_phase_gate(run_dir: str, phase: str) -> GateCheckResult:
    """
    Validate that a phase gate criteria are met with detailed feedback.

    Returns:
        GateCheckResult with full details
    """
    gate_config = PHASE_GATES.get(phase)
    if not gate_config:
        return GateCheckResult(
            status=GateStatus.FAILED,
            phase=phase,
            missing_items=[f"Unknown phase: {phase}"],
            suggestions=["Check the phase name is correct"],
            examples={"valid_phases": ", ".join(PHASE_GATES.keys())},
            next_steps=["Use a valid phase name from the list"]
        )

    missing = []

    # Check entry gate
    entry_passed, entry_error, entry_suggestion = check_entry_gate(run_dir, phase)
    if not entry_passed:
        missing.append(entry_error)
        if entry_suggestion:
            missing.append(f"Suggestion: {entry_suggestion}")

    # Check required files
    for filename in gate_config.get("required_files", []):
        if not check_file_exists(run_dir, filename):
            missing.append(f"Required file missing: {filename}")

    # Check exit criteria (these are manual checks - agent must confirm)
    criteria_file = Path(run_dir) / f".phase_{phase}_criteria"
    if not criteria_file.exists():
        # Add criteria as items to complete
        for criterion in gate_config.get("exit_criteria", []):
            missing.append(f"Exit criterion not verified: {criterion}")

    # Get detailed feedback
    suggestions, examples, next_steps = get_detailed_feedback(phase, missing)

    if len(missing) == 0:
        return GateCheckResult(
            status=GateStatus.PASSED,
            phase=phase,
            missing_items=[],
            suggestions=[],
            examples={},
            next_steps=[]
        )

    # Build comprehensive next steps
    comprehensive_next_steps = []

    # Add file creation steps first
    for filename in gate_config.get("required_files", []):
        if not check_file_exists(run_dir, filename):
            comprehensive_next_steps.append(f"Create '{filename}' with required content")
            template_key = filename.replace('.md', '_template')
            if template_key in gate_config:
                comprehensive_next_steps.append(f"  (Use template provided in examples below)")

    # Add criteria verification steps
    criteria_file_missing = not (Path(run_dir) / f".phase_{phase}_criteria").exists()
    if criteria_file_missing and gate_config.get("exit_criteria"):
        comprehensive_next_steps.append(f"Verify all exit criteria are met:")
        for criterion in gate_config.get("exit_criteria", []):
            comprehensive_next_steps.append(f"  - {criterion}")
        comprehensive_next_steps.append(f"Then mark criteria complete with:")
        comprehensive_next_steps.append(f"  python3 phase_gates.py mark --phase {phase} --run-dir {run_dir}")

    # Add entry gate completion if needed
    if not entry_passed and gate_config.get("entry_check"):
        comprehensive_next_steps.insert(0, f"Complete the '{gate_config['entry_check']}' phase first")

    return GateCheckResult(
        status=GateStatus.FAILED,
        phase=phase,
        missing_items=missing,
        suggestions=suggestions,
        examples=examples,
        next_steps=comprehensive_next_steps if comprehensive_next_steps else next_steps
    )


def format_gate_result(result: GateCheckResult) -> str:
    """Format a gate check result as a human-readable string."""
    lines = []

    if result.status == GateStatus.PASSED:
        lines.append(f"✓ Phase gate '{result.phase}' validation PASSED")
        lines.append("  You may proceed to the next phase.")
        return "\n".join(lines)

    # Failed status
    lines.append(f"✗ Phase gate '{result.phase}' validation FAILED")
    lines.append("")

    # Missing requirements section
    lines.append("=" * 60)
    lines.append("MISSING REQUIREMENTS")
    lines.append("=" * 60)

    for i, item in enumerate(result.missing_items, 1):
        lines.append(f"\n{i}. {item}")

    # Suggestions section
    if result.suggestions:
        lines.append("")
        lines.append("=" * 60)
        lines.append("SUGGESTIONS")
        lines.append("=" * 60)
        for suggestion in result.suggestions:
            lines.append(f"  • {suggestion}")

    # Next steps section
    if result.next_steps:
        lines.append("")
        lines.append("=" * 60)
        lines.append("NEXT STEPS")
        lines.append("=" * 60)
        for i, step in enumerate(result.next_steps, 1):
            lines.append(f"  {i}. {step}")

    # Examples section
    if result.examples:
        lines.append("")
        lines.append("=" * 60)
        lines.append("EXAMPLES")
        lines.append("=" * 60)
        for name, example in result.examples.items():
            lines.append(f"\n--- {name} ---")
            lines.append(example)

    # Command reference
    lines.append("")
    lines.append("=" * 60)
    lines.append("COMMANDS")
    lines.append("=" * 60)
    lines.append(f"Check gate status:")
    lines.append(f"  python3 phase_gates.py check --phase {result.phase} --run-dir <path>")
    lines.append("")
    lines.append(f"Mark gate as passed (when ready):")
    lines.append(f"  python3 phase_gates.py mark --phase {result.phase} --run-dir <path>")

    return "\n".join(lines)


def mark_gate_passed(run_dir: str, phase: str):
    """Mark a phase gate as passed."""
    marker_file = Path(run_dir) / f".gate_{phase}_passed"
    marker_file.touch()
    print(f"✓ Phase gate '{phase}' marked as passed")


def mark_criteria_complete(run_dir: str, phase: str):
    """Mark phase criteria as manually verified."""
    criteria_file = Path(run_dir) / f".phase_{phase}_criteria"
    criteria_file.touch()
    print(f"✓ Phase '{phase}' criteria marked as complete")


def main():
    if len(sys.argv) < 2:
        print("Usage: phase_gates.py <command> [options]")
        print("")
        print("Commands:")
        print("  check --phase <phase> --run-dir <run_dir>")
        print("  mark --phase <phase> --run-dir <run_dir>")
        print("  list")
        print("")
        print("Phases:")
        print("  Quick Flow: quick_spec → dev_story → code_review")
        print("  Full BMAD:  align → plan → execute → validate → wrap")
        print("")
        print("Examples:")
        print("  python3 phase_gates.py check --phase quick_spec --run-dir ./run-001")
        print("  python3 phase_gates.py mark --phase plan --run-dir ./run-001")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        print("Available phase gates:")
        print("")
        print("Quick Flow:")
        print("  1. quick_spec - Initial specification")
        print("  2. dev_story  - Implementation")
        print("  3. code_review - Code review")
        print("")
        print("Full BMAD:")
        print("  1. align     - Problem alignment")
        print("  2. plan      - Architecture planning")
        print("  3. execute   - Implementation")
        print("  4. validate  - Validation")
        print("  5. wrap      - Documentation")
        sys.exit(0)

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
        result = validate_phase_gate(run_dir, phase)
        print(format_gate_result(result))

        if result.status == GateStatus.PASSED:
            sys.exit(0)
        else:
            sys.exit(1)

    elif command == "mark":
        # First check if gate can be marked
        result = validate_phase_gate(run_dir, phase)

        if result.status != GateStatus.PASSED:
            print("⚠ Cannot mark gate as passed - requirements not met:")
            print(format_gate_result(result))
            sys.exit(1)

        mark_criteria_complete(run_dir, phase)
        mark_gate_passed(run_dir, phase)
        print(f"\n✓ Phase '{phase}' is now complete. You may proceed to the next phase.")

    else:
        print(f"Unknown command: {command}")
        print("Use 'check', 'mark', or 'list'")
        sys.exit(1)


if __name__ == "__main__":
    main()
