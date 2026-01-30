#!/usr/bin/env python3
"""
UI Cycle Validation Script

Validates that a UI Adaptive Development Cycle run has all required artifacts,
follows proper structure, and meets quality gates.

Usage:
  python scripts/validate-ui-cycle.py --run .runs/ui-cycle-20250113_1430
  python scripts/validate-ui-cycle.py --run .runs/ui-cycle-20250113_1430 --strict
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class UIColorValidation:
    def __init__(self, run_path: str, strict: bool = False):
        self.run_path = Path(run_path)
        self.strict = strict
        self.errors = []
        self.warnings = []
        self.passed = []
        self.results = {}

    def validate(self) -> bool:
        """Run all validations and return True if all pass."""
        print(f"Validating UI Cycle: {self.run_path}")
        print("=" * 60)

        # Structure validation
        self.validate_directory_structure()

        # Metadata validation
        self.validate_cycle_metadata()

        # Phase artifacts validation
        self.validate_phase_artifacts()

        # Screenshot validation
        self.validate_screenshots()

        # Log validation
        self.validate_logs()

        # Quality gate validation
        self.validate_quality_gates()

        # Print results
        self.print_results()

        return len(self.errors) == 0

    def validate_directory_structure(self):
        """Validate required directory structure exists."""
        required_dirs = [
            "artifacts",
            "screenshots/before",
            "screenshots/after",
            "logs",
        ]

        for dir_path in required_dirs:
            full_path = self.run_path / dir_path
            if full_path.exists() and full_path.is_dir():
                self.passed.append(f"Directory exists: {dir_path}/")
            else:
                self.errors.append(f"Missing directory: {dir_path}/")

        # Check for cycle.md and cycle.json
        if (self.run_path / "cycle.md").exists():
            self.passed.append("File exists: cycle.md")
        else:
            self.errors.append("Missing file: cycle.md")

        if (self.run_path / "cycle.json").exists():
            self.passed.append("File exists: cycle.json")
        else:
            self.warnings.append("Missing file: cycle.json (metadata)")

    def validate_cycle_metadata(self):
        """Validate cycle.json contains required fields."""
        cycle_json = self.run_path / "cycle.json"

        if not cycle_json.exists():
            return

        try:
            with open(cycle_json, 'r') as f:
                metadata = json.load(f)

            required_fields = ["cycle_id", "started_at", "task", "url", "component"]
            for field in required_fields:
                if field in metadata:
                    self.passed.append(f"Metadata field: {field}")
                else:
                    self.errors.append(f"Missing metadata field: {field}")

            # Validate format
            if "url" in metadata:
                url = metadata["url"]
                if url.startswith("http://") or url.startswith("https://"):
                    self.passed.append(f"Valid URL format: {url}")
                else:
                    self.warnings.append(f"Invalid URL format: {url}")

        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in cycle.json: {e}")
        except Exception as e:
            self.errors.append(f"Error reading cycle.json: {e}")

    def validate_phase_artifacts(self):
        """Validate artifacts for each phase."""
        artifacts_dir = self.run_path / "artifacts"

        if not artifacts_dir.exists():
            return

        # Phase 2: Define
        required_artifacts = {
            "success-criteria.md": "Phase 2 (Define) success criteria",
            "acceptance.test.ts": "Phase 2 (Define) acceptance test",
        }

        for artifact, description in required_artifacts.items():
            artifact_path = artifacts_dir / artifact
            if artifact_path.exists():
                self.passed.append(f"Artifact: {artifact} ({description})")
            else:
                phase = "Should-Have" if artifact == "success-criteria.md" else "Must-Have"
                if self.strict or phase == "Must-Have":
                    self.errors.append(f"Missing artifact: {artifact} ({description})")
                else:
                    self.warnings.append(f"Missing artifact: {artifact} ({description})")

        # Check for backup files (Phase 3: Build)
        backups = list(artifacts_dir.glob("*.backup"))
        if backups:
            self.passed.append(f"Backup files: {len(backups)} found")
        else:
            self.warnings.append("No backup files found (Phase 3)")

    def validate_screenshots(self):
        """Validate required screenshots exist."""
        screenshots_dir = self.run_path / "screenshots"

        if not screenshots_dir.exists():
            return

        # Before screenshots (Phase 1)
        before_dir = screenshots_dir / "before"
        required_before = ["mobile.png", "tablet.png", "desktop.png"]

        if before_dir.exists():
            for screenshot in required_before:
                screenshot_path = before_dir / screenshot
                if screenshot_path.exists():
                    # Check file size (should be > 1KB)
                    size = screenshot_path.stat().st_size
                    if size > 1024:
                        self.passed.append(f"Screenshot: before/{screenshot} ({size} bytes)")
                    else:
                        self.warnings.append(f"Screenshot too small: before/{screenshot} ({size} bytes)")
                else:
                    self.warnings.append(f"Missing screenshot: before/{screenshot}")
        else:
            self.errors.append("Missing screenshot directory: before/")

        # After screenshots (Phase 4)
        after_dir = screenshots_dir / "after"
        if after_dir.exists():
            after_screenshots = list(after_dir.glob("*.png"))
            if after_screenshots:
                self.passed.append(f"After screenshots: {len(after_screenshots)} found")
            else:
                self.warnings.append("No after screenshots found (Phase 4)")
        else:
            self.warnings.append("Missing screenshot directory: after/")

        # Production screenshot (Phase 5)
        production_screenshot = screenshots_dir / "production.png"
        if production_screenshot.exists():
            self.passed.append("Screenshot: production.png (Phase 5)")
        else:
            self.warnings.append("Missing screenshot: production.png (Phase 5)")

    def validate_logs(self):
        """Validate required log files exist."""
        logs_dir = self.run_path / "logs"

        if not logs_dir.exists():
            return

        required_logs = {
            "before-console.json": "Phase 1 (Observe)",
            "after-console.json": "Phase 4 (Verify)",
            "test-results.json": "Phase 4 (Verify)",
        }

        for log_file, phase in required_logs.items():
            log_path = logs_dir / log_file
            if log_path.exists():
                # Validate JSON format
                try:
                    with open(log_path, 'r') as f:
                        data = json.load(f)
                    self.passed.append(f"Log: {log_file} ({phase})")
                except json.JSONDecodeError:
                    self.errors.append(f"Invalid JSON: {log_file}")
            else:
                self.warnings.append(f"Missing log: {log_file} ({phase})")

        # Check for build logs (Phase 3)
        build_logs = ["typecheck.log", "lint.log", "build.log"]
        found_build_logs = 0
        for log_file in build_logs:
            if (logs_dir / log_file).exists():
                found_build_logs += 1

        if found_build_logs > 0:
            self.passed.append(f"Build logs: {found_build_logs}/{len(build_logs)} found")
        else:
            self.warnings.append("No build logs found (Phase 3)")

    def validate_quality_gates(self):
        """Validate quality gate results from logs."""
        logs_dir = self.run_path / "logs"

        if not logs_dir.exists():
            return

        # Check console logs for errors
        for log_name in ["before-console.json", "after-console.json"]:
            log_path = logs_dir / log_name
            if not log_path.exists():
                continue

            try:
                with open(log_path, 'r') as f:
                    data = json.load(f)

                # Check for error logs
                error_count = 0
                if isinstance(data, list):
                    error_count = sum(1 for entry in data if isinstance(entry, dict) and entry.get("type") == "error")
                elif isinstance(data, dict) and "logs" in data:
                    error_count = sum(1 for entry in data["logs"] if isinstance(entry, dict) and entry.get("type") == "error")

                if error_count == 0:
                    self.passed.append(f"Quality gate: No console errors in {log_name}")
                else:
                    if log_name == "after-console.json":
                        self.errors.append(f"Quality gate failed: {error_count} console errors in {log_name}")
                    else:
                        self.warnings.append(f"Quality gate warning: {error_count} console errors in {log_name} (baseline)")

            except (json.JSONDecodeError, KeyError, TypeError):
                self.warnings.append(f"Could not validate console errors in {log_name}")

        # Check test results
        test_results = logs_dir / "test-results.json"
        if test_results.exists():
            try:
                with open(test_results, 'r') as f:
                    data = json.load(f)

                # Check for test status (various formats)
                passed = True
                if isinstance(data, dict):
                    if "status" in data and data["status"] == "failed":
                        passed = False
                    if "stats" in data and "failed" in data["stats"] and data["stats"]["failed"] > 0:
                        passed = False

                if passed:
                    self.passed.append("Quality gate: All tests passed")
                else:
                    self.errors.append("Quality gate failed: Tests did not pass")

            except (json.JSONDecodeError, KeyError):
                self.warnings.append("Could not validate test results")

    def print_results(self):
        """Print validation results."""
        print()

        if self.passed:
            print(f"✅ Passed ({len(self.passed)})")
            for item in self.passed:
                print(f"   {item}")
            print()

        if self.warnings:
            print(f"⚠️  Warnings ({len(self.warnings)})")
            for item in self.warnings:
                print(f"   {item}")
            print()

        if self.errors:
            print(f"❌ Errors ({len(self.errors)})")
            for item in self.errors:
                print(f"   {item}")
            print()

        print("=" * 60)

        if self.errors:
            print("❌ Validation FAILED")
            print(f"   Errors: {len(self.errors)}")
            print(f"   Warnings: {len(self.warnings)}")
            print(f"   Passed: {len(self.passed)}")
        elif self.warnings:
            print("⚠️  Validation PASSED with warnings")
            print(f"   Warnings: {len(self.warnings)}")
            print(f"   Passed: {len(self.passed)}")
        else:
            print("✅ Validation PASSED")
            print(f"   All checks passed: {len(self.passed)}")

        # Store results
        self.results = {
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "passed": len(self.passed),
            "success": len(self.errors) == 0,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Validate UI Adaptive Development Cycle runs"
    )
    parser.add_argument(
        "--run",
        required=True,
        help="Path to UI Cycle run directory (e.g., .runs/ui-cycle-20250113_1430)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode (treat warnings as errors)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    # Resolve path
    run_path = args.run
    if not os.path.isabs(run_path):
        # If relative, check if it's from current dir or Blackbox3 root
        if os.path.exists(run_path):
            run_path = os.path.abspath(run_path)
        else:
            # Try from Blackbox3 root
            script_dir = os.path.dirname(os.path.abspath(__file__))
            box_root = os.path.dirname(script_dir)
            run_path = os.path.join(box_root, run_path)

    if not os.path.exists(run_path):
        print(f"Error: Run directory not found: {run_path}", file=sys.stderr)
        sys.exit(1)

    # Run validation
    validator = UIColorValidation(run_path, strict=args.strict)
    success = validator.validate()

    # Output JSON if requested
    if args.json:
        print()
        print(json.dumps(validator.results, indent=2))

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
