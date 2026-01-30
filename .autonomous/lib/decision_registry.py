#!/usr/bin/env python3
"""
Decision Registry Library for RALF Agent-2.3

Implements decision tracking with reversibility assessment as required
by the Agent-2.3 enforcement system.

Usage:
    from decision_registry import DecisionRegistry

    # Initialize from template
    registry = DecisionRegistry("/path/to/decision_registry.yaml")
    registry.initialize_from_template("/path/to/template.yaml")

    # Record a decision
    decision_id = registry.record_decision({
        "phase": "PLAN",
        "context": "Choosing implementation approach",
        "options_considered": [...],
        "selected_option": "OPT-001",
        "rationale": "...",
        "assumptions": [...],
        "reversibility": "MEDIUM",
        "rollback_complexity": "Requires migration",
        "rollback_steps": [...],
        "verification": {"required": True, "criteria": [...]}
    })

    # Verify assumptions after implementation
    registry.verify_decision(decision_id, {
        "verified_by": "Agent-2.3",
        "results": {"criterion_1": "PASS", ...}
    })

    # Get rollback plan
    rollback = registry.get_rollback_plan(decision_id)

CLI Usage:
    python decision_registry.py init --run-dir /path/to/run
    python decision_registry.py record --decision '{"..."}'
    python decision_registry.py verify --id DEC-001 --results '{"..."}'
    python decision_registry.py finalize
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class DecisionRegistry:
    """
    Manages decision tracking with reversibility assessment.

    Features:
    - Initialize from template
    - Record decisions with full context
    - Track assumptions and verification
    - Generate rollback plans
    - Validate completeness
    """

    VALID_PHASES = ["ALIGN", "PLAN", "EXECUTE", "VALIDATE", "WRAP"]
    VALID_RISK_LEVELS = ["LOW", "MEDIUM", "HIGH"]
    VALID_REVERSIBILITY = ["LOW", "MEDIUM", "HIGH"]
    VALID_DECISION_STATUS = ["PROPOSED", "DECIDED", "VERIFIED", "ROLLED_BACK"]
    VALID_ASSUMPTION_STATUS = ["PENDING_VERIFICATION", "VERIFIED", "FAILED"]

    def __init__(self, registry_path: str):
        """
        Initialize the DecisionRegistry.

        Args:
            registry_path: Path to the decision_registry.yaml file
        """
        self.registry_path = Path(registry_path)
        self._data = None
        self._load()

    def _load(self) -> None:
        """Load the registry file."""
        if self.registry_path.exists():
            import yaml
            with open(self.registry_path, 'r') as f:
                self._data = yaml.safe_load(f) or {}
        else:
            self._data = {"decisions": []}

    def _save(self) -> None:
        """Save the registry file."""
        import yaml
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            yaml.safe_dump(self._data, f, default_flow_style=False, sort_keys=False)

    def initialize_from_template(self, template_path: str, run_id: str = None, task_id: str = None) -> None:
        """
        Initialize registry from template.

        Args:
            template_path: Path to the decision_registry.yaml template
            run_id: Optional run ID to set
            task_id: Optional task ID to set
        """
        template_path = Path(template_path)
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        import yaml
        with open(template_path, 'r') as f:
            self._data = yaml.safe_load(f)

        # Update placeholders
        if run_id:
            self._data["run_id"] = run_id
        if task_id:
            self._data["task_id"] = task_id
        self._data["created_at"] = datetime.now(timezone.utc).isoformat()

        self._save()

    def record_decision(self, decision: Dict[str, Any]) -> str:
        """
        Record a new decision.

        Args:
            decision: Decision dictionary matching schema

        Returns:
            The decision ID

        Raises:
            ValueError: If decision is invalid
        """
        # Validate required fields
        self._validate_decision(decision)

        # Generate decision ID if not provided
        if "id" not in decision:
            run_num = self._data.get("run_id", "0").split("-")[-1]
            seq = len(self._data.get("decisions", [])) + 1
            decision["id"] = f"DEC-{run_num}-{seq:03d}"

        # Set timestamp if not provided
        if "timestamp" not in decision:
            decision["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Set default status
        if "status" not in decision:
            decision["status"] = "DECIDED"

        # Initialize decision if it was PROPOSED
        if decision["status"] == "PROPOSED":
            pass  # Keep as proposed
        else:
            # Mark assumptions as pending verification
            for asm in decision.get("assumptions", []):
                if "status" not in asm:
                    asm["status"] = "PENDING_VERIFICATION"

        # Add to registry
        if "decisions" not in self._data:
            self._data["decisions"] = []
        self._data["decisions"].append(decision)

        # Update metadata
        self._update_metadata()

        self._save()
        return decision["id"]

    def verify_decision(self, decision_id: str, verification: Dict[str, Any]) -> None:
        """
        Verify a decision's assumptions and update status.

        Args:
            decision_id: The decision ID to verify
            verification: Verification results with keys:
                - verified_by: Agent name
                - verified_at: Timestamp (optional, defaults to now)
                - results: Dict of assumption_id -> result (PASS/FAIL)
                - notes: Optional verification notes

        Raises:
            ValueError: If decision not found
        """
        decision = self.get_decision(decision_id)

        # Update verification info
        if "verification" not in decision:
            decision["verification"] = {}
        decision["verification"]["verified_by"] = verification.get("verified_by")
        decision["verification"]["verified_at"] = verification.get(
            "verified_at",
            datetime.now(timezone.utc).isoformat()
        )

        # Update assumption statuses
        results = verification.get("results", {})
        all_passed = True
        for asm in decision.get("assumptions", []):
            asm_id = asm.get("id")
            if asm_id in results:
                asm["status"] = "VERIFIED" if results[asm_id] == "PASS" else "FAILED"
                if results[asm_id] != "PASS":
                    all_passed = False

        # Update decision status
        if all_passed:
            decision["status"] = "VERIFIED"
        else:
            decision["status"] = "FAILED"  # Or keep status if partial failure

        self._save()

    def get_decision(self, decision_id: str) -> Dict[str, Any]:
        """
        Get a decision by ID.

        Args:
            decision_id: The decision ID

        Returns:
            The decision dictionary

        Raises:
            ValueError: If decision not found
        """
        for decision in self._data.get("decisions", []):
            if decision.get("id") == decision_id:
                return decision
        raise ValueError(f"Decision not found: {decision_id}")

    def list_decisions(self, status: str = None, phase: str = None) -> List[Dict[str, Any]]:
        """
        List decisions with optional filtering.

        Args:
            status: Optional status filter
            phase: Optional phase filter

        Returns:
            List of decisions matching filters
        """
        decisions = self._data.get("decisions", [])

        if status:
            decisions = [d for d in decisions if d.get("status") == status]
        if phase:
            decisions = [d for d in decisions if d.get("phase") == phase]

        return decisions

    def get_rollback_plan(self, decision_id: str) -> Dict[str, Any]:
        """
        Get rollback plan for a decision.

        Args:
            decision_id: The decision ID

        Returns:
            Dictionary with rollback information:
                - decision_id: The decision ID
                - reversibility: LOW/MEDIUM/HIGH
                - rollback_complexity: Description
                - rollback_steps: List of steps
                - can_rollback: Boolean indicating if rollback is feasible
        """
        decision = self.get_decision(decision_id)

        return {
            "decision_id": decision_id,
            "context": decision.get("context"),
            "selected_option": decision.get("selected_option"),
            "reversibility": decision.get("reversibility", "UNKNOWN"),
            "rollback_complexity": decision.get("rollback_complexity", "Not specified"),
            "rollback_steps": decision.get("rollback_steps", []),
            "can_rollback": decision.get("reversibility") in ["LOW", "MEDIUM"]
        }

    def finalize(self) -> Dict[str, Any]:
        """
        Finalize the registry and return summary.

        Returns:
            Summary dictionary with metadata
        """
        # Update metadata
        self._update_metadata()

        # Validate completeness
        issues = self._validate_completeness()

        summary = {
            "registry": self._data.get("registry", {}),
            "completeness": "VALID" if not issues else "INVALID",
            "issues": issues,
            "decisions_by_status": self._count_by_status(),
            "decisions_by_phase": self._count_by_phase()
        }

        self._save()
        return summary

    def _validate_decision(self, decision: Dict[str, Any]) -> None:
        """Validate decision structure."""
        required_fields = ["phase", "context"]
        for field in required_fields:
            if field not in decision:
                raise ValueError(f"Missing required field: {field}")

        if decision["phase"] not in self.VALID_PHASES:
            raise ValueError(f"Invalid phase: {decision['phase']}")

        # Validate options if provided
        if "options_considered" in decision:
            for opt in decision["options_considered"]:
                if "id" not in opt or "description" not in opt:
                    raise ValueError("Options must have id and description")

        # Validate assumptions if provided
        if "assumptions" in decision:
            for asm in decision["assumptions"]:
                if "id" not in asm or "statement" not in asm:
                    raise ValueError("Assumptions must have id and statement")
                if asm.get("risk_level") and asm["risk_level"] not in self.VALID_RISK_LEVELS:
                    raise ValueError(f"Invalid risk level: {asm['risk_level']}")

        # Validate reversibility
        if decision.get("reversibility") and decision["reversibility"] not in self.VALID_REVERSIBILITY:
            raise ValueError(f"Invalid reversibility: {decision['reversibility']}")

        # Validate status if provided
        if decision.get("status") and decision["status"] not in self.VALID_DECISION_STATUS:
            raise ValueError(f"Invalid status: {decision['status']}")

    def _update_metadata(self) -> None:
        """Update registry metadata."""
        decisions = self._data.get("decisions", [])

        reversible = sum(1 for d in decisions if d.get("reversibility") in ["LOW", "MEDIUM"])
        irreversible = sum(1 for d in decisions if d.get("reversibility") == "HIGH")
        pending_verify = sum(1 for d in decisions
                           for asm in d.get("assumptions", [])
                           if asm.get("status") == "PENDING_VERIFICATION")
        verified = sum(1 for d in decisions if d.get("status") == "VERIFIED")
        rolled_back = sum(1 for d in decisions if d.get("status") == "ROLLED_BACK")

        self._data["registry"] = {
            "total_decisions": len(decisions),
            "reversible_decisions": reversible,
            "irreversible_decisions": irreversible,
            "pending_verification": pending_verify,
            "verified_decisions": verified,
            "rolled_back_decisions": rolled_back
        }

    def _validate_completeness(self) -> List[str]:
        """Validate registry completeness and return list of issues."""
        issues = []

        # Check for decisions without verification that require it
        for decision in self._data.get("decisions", []):
            if decision.get("verification", {}).get("required") and decision.get("status") != "VERIFIED":
                issues.append(f"Decision {decision.get('id')} requires verification but is not verified")

            # Check for assumptions still pending
            for asm in decision.get("assumptions", []):
                if asm.get("status") == "PENDING_VERIFICATION":
                    issues.append(f"Assumption {asm.get('id')} in decision {decision.get('id')} is pending verification")

        return issues

    def _count_by_status(self) -> Dict[str, int]:
        """Count decisions by status."""
        counts = {}
        for decision in self._data.get("decisions", []):
            status = decision.get("status", "UNKNOWN")
            counts[status] = counts.get(status, 0) + 1
        return counts

    def _count_by_phase(self) -> Dict[str, int]:
        """Count decisions by phase."""
        counts = {}
        for decision in self._data.get("decisions", []):
            phase = decision.get("phase", "UNKNOWN")
            counts[phase] = counts.get(phase, 0) + 1
        return counts


def cli_init(args) -> None:
    """Initialize registry from template."""
    run_dir = Path(args.run_dir)
    template_path = Path(args.template) if args.template else Path(__file__).parent.parent / \
        "prompt-progression/versions/v2.3/templates/decision_registry.yaml"

    registry_path = run_dir / "decision_registry.yaml"

    # Get run_id and task_id from run_dir name or args
    run_id = args.run_id or run_dir.name
    task_id = args.task_id or f"TASK-{run_dir.name.split('-')[-1]}"

    registry = DecisionRegistry(str(registry_path))
    registry.initialize_from_template(str(template_path), run_id, task_id)

    print(f"Initialized decision registry at {registry_path}")
    print(f"  Run ID: {run_id}")
    print(f"  Task ID: {task_id}")


def cli_record(args) -> None:
    """Record a decision."""
    registry = DecisionRegistry(args.registry)

    decision = json.loads(args.decision)
    decision_id = registry.record_decision(decision)

    print(f"Recorded decision: {decision_id}")


def cli_verify(args) -> None:
    """Verify a decision."""
    registry = DecisionRegistry(args.registry)

    verification = {
        "verified_by": args.verified_by,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "results": json.loads(args.results)
    }

    if args.notes:
        verification["notes"] = args.notes

    registry.verify_decision(args.id, verification)

    print(f"Verified decision: {args.id}")


def cli_list(args) -> None:
    """List decisions."""
    registry = DecisionRegistry(args.registry)

    decisions = registry.list_decisions(status=args.status, phase=args.phase)

    print(f"Decisions: {len(decisions)}")
    for d in decisions:
        print(f"  {d.get('id')}: {d.get('context')} [{d.get('status')}] [{d.get('phase')}]")
        if args.verbose:
            print(f"    Selected: {d.get('selected_option')}")
            print(f"    Reversibility: {d.get('reversibility')}")


def cli_rollback(args) -> None:
    """Show rollback plan."""
    registry = DecisionRegistry(args.registry)

    plan = registry.get_rollback_plan(args.id)

    print(f"Rollback Plan for {args.id}:")
    print(f"  Context: {plan['context']}")
    print(f"  Selected Option: {plan['selected_option']}")
    print(f"  Reversibility: {plan['reversibility']}")
    print(f"  Can Rollback: {plan['can_rollback']}")
    print(f"  Complexity: {plan['rollback_complexity']}")
    print(f"  Steps:")
    for i, step in enumerate(plan['rollback_steps'], 1):
        print(f"    {i}. {step}")


def cli_finalize(args) -> None:
    """Finalize registry."""
    registry = DecisionRegistry(args.registry)

    summary = registry.finalize()

    print("Decision Registry Summary:")
    print(f"  Total Decisions: {summary['registry']['total_decisions']}")
    print(f"  Reversible: {summary['registry']['reversible_decisions']}")
    print(f"  Pending Verification: {summary['registry']['pending_verification']}")
    print(f"  Verified: {summary['registry']['verified_decisions']}")
    print(f"  Completeness: {summary['completeness']}")

    if summary['issues']:
        print("  Issues:")
        for issue in summary['issues']:
            print(f"    - {issue}")

    print("\n  By Status:")
    for status, count in summary['decisions_by_status'].items():
        print(f"    {status}: {count}")

    print("\n  By Phase:")
    for phase, count in summary['decisions_by_phase'].items():
        print(f"    {phase}: {count}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="RALF Decision Registry")
    parser.add_argument("--registry", default="decision_registry.yaml",
                       help="Path to decision registry file")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize from template")
    init_parser.add_argument("--run-dir", required=True, help="Run directory")
    init_parser.add_argument("--template", help="Template path")
    init_parser.add_argument("--run-id", help="Run ID")
    init_parser.add_argument("--task-id", help="Task ID")
    init_parser.set_defaults(func=cli_init)

    # record command
    record_parser = subparsers.add_parser("record", help="Record a decision")
    record_parser.add_argument("--decision", required=True, help="Decision JSON")
    record_parser.set_defaults(func=cli_record)

    # verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a decision")
    verify_parser.add_argument("--id", required=True, help="Decision ID")
    verify_parser.add_argument("--verified-by", required=True, help="Verifier name")
    verify_parser.add_argument("--results", required=True, help="Verification results JSON")
    verify_parser.add_argument("--notes", help="Verification notes")
    verify_parser.set_defaults(func=cli_verify)

    # list command
    list_parser = subparsers.add_parser("list", help="List decisions")
    list_parser.add_argument("--status", help="Filter by status")
    list_parser.add_argument("--phase", help="Filter by phase")
    list_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    list_parser.set_defaults(func=cli_list)

    # rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Show rollback plan")
    rollback_parser.add_argument("--id", required=True, help="Decision ID")
    rollback_parser.set_defaults(func=cli_rollback)

    # finalize command
    finalize_parser = subparsers.add_parser("finalize", help="Finalize registry")
    finalize_parser.set_defaults(func=cli_finalize)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
