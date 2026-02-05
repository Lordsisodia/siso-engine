#!/usr/bin/env python3
"""
Verifier Agent - Validate Improvement Implementations

Validates that executed improvements were implemented correctly.
Part of the Agent Improvement Loop: Scout → Planner → Executor → Verifier

Usage:
    verifier-validate.py --executor-report FILE
    verifier-validate.py --latest
"""

import argparse
import json
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Configuration
PROJECT_DIR = Path.home() / ".blackbox5" / "5-project-memory" / "blackbox5"
ENGINE_DIR = Path.home() / ".blackbox5" / "2-engine"
EXECUTOR_REPORT_DIR = PROJECT_DIR / ".autonomous" / "analysis" / "executor-reports"


@dataclass
class ValidationResult:
    """Result of validating an improvement."""
    task_id: str
    validated: bool
    validation_method: str
    expected_state: str
    actual_state: str
    checks_passed: int
    checks_failed: int
    details: List[str]
    recommendation: str


class VerifierAgent:
    """
    Verifier Agent that validates improvement implementations.
    """

    def __init__(self):
        self.results: List[ValidationResult] = []

    def load_executor_report(self, report_path: Path) -> Optional[Dict[str, Any]]:
        """Load an executor report."""
        if not report_path.exists():
            print(f"❌ Report not found: {report_path}")
            return None

        try:
            with open(report_path, 'r') as f:
                if report_path.suffix == '.json':
                    return json.load(f)
                else:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Error loading report: {e}")
            return None

    def validate_threshold_fix(self, task_result: Dict[str, Any]) -> ValidationResult:
        """
        Validate: Skill confidence threshold was lowered to 60%.
        """
        task_id = task_result.get("task_id", "unknown")
        file_path = PROJECT_DIR / "operations" / "skill-selection.yaml"

        checks_passed = 0
        checks_failed = 0
        details = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Check 1: Threshold is 60
            if 'threshold: 60' in content:
                checks_passed += 1
                details.append("✅ Threshold value is 60")
            else:
                checks_failed += 1
                details.append("❌ Threshold value is not 60")

            # Check 2: Documentation updated
            if 'confidence >= 60%' in content:
                checks_passed += 1
                details.append("✅ Documentation reflects 60% threshold")
            else:
                checks_failed += 1
                details.append("❌ Documentation not updated")

            # Check 3: File is valid YAML
            try:
                yaml.safe_load(content)
                checks_passed += 1
                details.append("✅ File is valid YAML")
            except yaml.YAMLError:
                checks_failed += 1
                details.append("❌ File has YAML syntax errors")

            validated = checks_failed == 0

            return ValidationResult(
                task_id=task_id,
                validated=validated,
                validation_method="File content verification",
                expected_state="threshold: 60",
                actual_state="threshold: 60" if 'threshold: 60' in content else "threshold: 70",
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                details=details,
                recommendation="No action needed" if validated else "Re-run executor with --fix flag"
            )

        except Exception as e:
            return ValidationResult(
                task_id=task_id,
                validated=False,
                validation_method="File content verification",
                expected_state="threshold: 60",
                actual_state="error",
                checks_passed=0,
                checks_failed=1,
                details=[f"❌ Error during validation: {e}"],
                recommendation="Check file permissions and re-run"
            )

    def validate_engine_path_fix(self, task_result: Dict[str, Any]) -> ValidationResult:
        """
        Validate: Engine path was fixed from '01-core' to 'core'.
        """
        task_id = task_result.get("task_id", "unknown")
        file_path = PROJECT_DIR / "bin" / "blackbox.py"

        checks_passed = 0
        checks_failed = 0
        details = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Check 1: No '01-core' references
            if '01-core' not in content:
                checks_passed += 1
                details.append("✅ No '01-core' references found")
            else:
                checks_failed += 1
                details.append("❌ Still has '01-core' references")

            # Check 2: Has 'core' references
            if 'core' in content:
                checks_passed += 1
                details.append("✅ 'core' references present")
            else:
                checks_failed += 1
                details.append("⚠️ No 'core' references found (may be OK if file doesn't reference engine)")

            validated = checks_failed == 0

            return ValidationResult(
                task_id=task_id,
                validated=validated,
                validation_method="File content verification",
                expected_state="path contains 'core' not '01-core'",
                actual_state="path fixed" if '01-core' not in content else "path not fixed",
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                details=details,
                recommendation="No action needed" if validated else "Re-run executor"
            )

        except Exception as e:
            return ValidationResult(
                task_id=task_id,
                validated=False,
                validation_method="File content verification",
                expected_state="path fixed",
                actual_state=f"error: {e}",
                checks_passed=0,
                checks_failed=1,
                details=[f"❌ Error: {e}"],
                recommendation="Check file existence and permissions"
            )

    def validate_task(self, task_result: Dict[str, Any]) -> ValidationResult:
        """Validate a specific task implementation."""
        task_id = task_result.get("task_id", "unknown")

        print(f"\n🔍 Validating: {task_id}")

        # Route to appropriate validator
        if task_id == "TASK-SKIL-005" or "threshold" in task_result.get("action_taken", "").lower():
            return self.validate_threshold_fix(task_result)
        elif task_id == "TASK-ARCH-012" or "engine path" in task_result.get("action_taken", "").lower():
            return self.validate_engine_path_fix(task_result)
        else:
            return ValidationResult(
                task_id=task_id,
                validated=False,
                validation_method="Unknown",
                expected_state="unknown",
                actual_state="unknown",
                checks_passed=0,
                checks_failed=1,
                details=["No validator available for this task type"],
                recommendation="Manual validation required"
            )

    def validate_all(self, report: Dict[str, Any]) -> List[ValidationResult]:
        """Validate all tasks in an executor report."""
        results_data = report.get("executor_report", {}).get("results", [])

        # Only validate successful executions
        successful = [r for r in results_data if r.get("success", False)]

        print(f"\n📋 Found {len(successful)} successful implementations to validate")

        results = []
        for task_result in successful:
            result = self.validate_task(task_result)
            results.append(result)

        return results

    def save_validation_report(self, results: List[ValidationResult]) -> Path:
        """Save validation results to a report."""
        report_dir = PROJECT_DIR / ".autonomous" / "analysis" / "verifier-reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        report_id = f"VALIDATE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        validated_count = len([r for r in results if r.validated])
        failed_count = len([r for r in results if not r.validated])

        report = {
            "verifier_report": {
                "id": report_id,
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_validated": len(results),
                    "passed": validated_count,
                    "failed": failed_count,
                    "success_rate": f"{validated_count / len(results) * 100:.1f}%" if results else "N/A"
                },
                "validations": [asdict(r) for r in results]
            }
        }

        # Save YAML
        yaml_file = report_dir / f"{report_id}.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)

        # Save JSON
        json_file = report_dir / f"{report_id}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n✅ Validation report saved:")
        print(f"   YAML: {yaml_file}")
        print(f"   JSON: {json_file}")

        return yaml_file

    def print_summary(self, results: List[ValidationResult]):
        """Print validation summary."""
        print("\n" + "="*60)
        print("VERIFIER AGENT - VALIDATION SUMMARY")
        print("="*60)

        passed = [r for r in results if r.validated]
        failed = [r for r in results if not r.validated]

        print(f"\n📊 Validation Summary:")
        print(f"   Total validations: {len(results)}")
        print(f"   ✅ Passed: {len(passed)}")
        print(f"   ❌ Failed: {len(failed)}")

        if passed:
            print(f"\n✅ Passed Validations:")
            for r in passed:
                print(f"   • {r.task_id}: {r.checks_passed}/{r.checks_passed + r.checks_failed} checks passed")

        if failed:
            print(f"\n❌ Failed Validations:")
            for r in failed:
                print(f"   • {r.task_id}: {r.checks_passed}/{r.checks_passed + r.checks_failed} checks passed")
                print(f"     Recommendation: {r.recommendation}")

        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Verifier Agent - Validate improvements"
    )
    parser.add_argument(
        "--executor-report",
        type=Path,
        help="Path to executor report file"
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Use the latest executor report"
    )

    args = parser.parse_args()

    # Determine report path
    if args.latest:
        reports = sorted(EXECUTOR_REPORT_DIR.glob("EXEC-*.yaml"), reverse=True)
        if not reports:
            print("❌ No executor reports found")
            return 1
        report_path = reports[0]
        print(f"📄 Using latest report: {report_path.name}")
    elif args.executor_report:
        report_path = args.executor_report
    else:
        print("❌ Please specify --executor-report or --latest")
        return 1

    # Initialize verifier
    verifier = VerifierAgent()

    # Load executor report
    report = verifier.load_executor_report(report_path)
    if not report:
        return 1

    # Validate all tasks
    results = verifier.validate_all(report)

    # Save validation report
    if results:
        verifier.save_validation_report(results)
        verifier.print_summary(results)

    return 0 if all(r.validated for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
