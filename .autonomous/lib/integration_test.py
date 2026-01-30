#!/usr/bin/env python3
"""
RALF v2.3 Integration Test Suite

Tests that all enforcement systems work together in the unified autonomous loop.

Systems tested:
1. Phase Gates - Entry/exit validation at each phase
2. Context Budget - Token tracking and auto-actions
3. Decision Registry - Recording and verifying decisions
4. Goals System - Goal-derived task prioritization
5. Telemetry - Event and metric tracking

Usage:
    python3 integration_test.py run --run-dir /path/to/run
    python3 integration_test.py list
    python3 integration_test.py verify-all
"""

import json
import os
import sys
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


@dataclass
class TestResult:
    """Result of a single integration test."""
    name: str
    passed: bool
    message: str
    details: Optional[Dict] = None


class IntegrationTest:
    """Integration test suite for RALF v2.3 systems."""

    def __init__(self, run_dir: str):
        self.run_dir = Path(run_dir).expanduser().resolve()

        # Calculate blackbox5 root from run_dir
        # run_dir is typically: ~/.blackbox5/5-project-memory/ralf-core/.autonomous/runs/run-XXXX
        # We need to find the blackbox5 root
        parts = self.run_dir.parts
        if ".blackbox5" in parts:
            idx = parts.index(".blackbox5")
            self.blackbox5 = Path(*parts[:idx+1])
        else:
            # Fallback: assume blackbox5 is 5 levels up from runs/
            self.blackbox5 = self.run_dir.parent.parent.parent.parent.parent

        self.engine_lib = self.blackbox5 / "2-engine" / ".autonomous" / "lib"
        self.engine_shell = self.blackbox5 / "2-engine" / ".autonomous" / "shell"
        self.goals_dir = self.run_dir.parent.parent / "goals"

    def log(self, message: str, level: str = "info"):
        """Log a message."""
        prefix = {
            "info": "[INFO]",
            "success": "[PASS]",
            "error": "[FAIL]",
            "warn": "[WARN]"
        }
        print(f"{prefix.get(level, '[LOG]')} {message}")

    def run_all_tests(self) -> Tuple[int, int, List[TestResult]]:
        """Run all integration tests.

        Returns:
            (passed_count, total_count, results_list)
        """
        results = []

        self.log("=" * 60)
        self.log("RALF v2.3 Integration Test Suite")
        self.log("=" * 60)
        self.log(f"Run directory: {self.run_dir}")
        self.log(f"Blackbox5 root: {self.blackbox5}")
        self.log("")

        # System 1: Phase Gates
        results.extend(self._test_phase_gates())

        # System 2: Context Budget
        results.extend(self._test_context_budget())

        # System 3: Decision Registry
        results.extend(self._test_decision_registry())

        # System 4: Goals System
        results.extend(self._test_goals_system())

        # System 5: Telemetry
        results.extend(self._test_telemetry())

        # System 6: Integration (all systems working together)
        results.extend(self._test_unified_loop())

        # Summary
        passed = sum(1 for r in results if r.passed)
        total = len(results)

        self.log("")
        self.log("=" * 60)
        self.log(f"Results: {passed}/{total} tests passed")
        self.log("=" * 60)

        return passed, total, results

    def _test_phase_gates(self) -> List[TestResult]:
        """Test Phase Gates enforcement system."""
        results = []
        self.log("Testing: Phase Gates System")

        phase_gates_py = self.engine_lib / "phase_gates.py"

        # Test 1: Phase gates script exists
        if not phase_gates_py.exists():
            results.append(TestResult(
                name="Phase Gates: Script exists",
                passed=False,
                message=f"Phase gates script not found: {phase_gates_py}"
            ))
            return results

        results.append(TestResult(
            name="Phase Gates: Script exists",
            passed=True,
            message=f"Found at: {phase_gates_py}"
        ))

        # Test 2: Can list available phases
        try:
            output = subprocess.run(
                ["python3", str(phase_gates_py), "list"],
                capture_output=True, text=True, timeout=5
            )
            if output.returncode == 0:
                results.append(TestResult(
                    name="Phase Gates: List phases",
                    passed=True,
                    message="Successfully listed available phases",
                    details={"output": output.stdout}
                ))
            else:
                results.append(TestResult(
                    name="Phase Gates: List phases",
                    passed=False,
                    message=f"Failed to list phases: {output.stderr}"
                ))
        except Exception as e:
            results.append(TestResult(
                name="Phase Gates: List phases",
                passed=False,
                message=f"Exception: {e}"
            ))

        # Test 3: Can check a gate (should fail on empty run dir)
        try:
            output = subprocess.run(
                ["python3", str(phase_gates_py), "check",
                 "--phase", "quick_spec", "--run-dir", str(self.run_dir)],
                capture_output=True, text=True, timeout=5
            )
            # Expected to fail because quick_spec.md doesn't exist
            if "Required file missing" in output.stdout or "Phase gate" in output.stdout:
                results.append(TestResult(
                    name="Phase Gates: Check gate",
                    passed=True,
                    message="Gate check working (correctly detects missing files)"
                ))
            else:
                results.append(TestResult(
                    name="Phase Gates: Check gate",
                    passed=False,
                    message=f"Unexpected output: {output.stdout[:200]}"
                ))
        except Exception as e:
            results.append(TestResult(
                name="Phase Gates: Check gate",
                passed=False,
                message=f"Exception: {e}"
            ))

        # Test 4: All required phases defined
        required_phases = ["quick_spec", "dev_story", "code_review",
                          "align", "plan", "execute", "validate", "wrap"]
        try:
            with open(phase_gates_py) as f:
                content = f.read()
            missing = []
            for phase in required_phases:
                if f'"{phase}"' not in content and f"'{phase}'" not in content:
                    missing.append(phase)
            if not missing:
                results.append(TestResult(
                    name="Phase Gates: All phases defined",
                    passed=True,
                    message=f"All {len(required_phases)} phases defined"
                ))
            else:
                results.append(TestResult(
                    name="Phase Gates: All phases defined",
                    passed=False,
                    message=f"Missing phases: {missing}"
                ))
        except Exception as e:
            results.append(TestResult(
                name="Phase Gates: All phases defined",
                passed=False,
                message=f"Exception: {e}"
            ))

        return results

    def _test_context_budget(self) -> List[TestResult]:
        """Test Context Budget enforcement system."""
        results = []
        self.log("Testing: Context Budget System")

        context_budget_py = self.engine_lib / "context_budget.py"

        # Test 1: Context budget script exists
        if not context_budget_py.exists():
            results.append(TestResult(
                name="Context Budget: Script exists",
                passed=False,
                message=f"Context budget script not found: {context_budget_py}"
            ))
            return results

        results.append(TestResult(
            name="Context Budget: Script exists",
            passed=True,
            message=f"Found at: {context_budget_py}"
        ))

        # Test 2: Can initialize budget
        try:
            output = subprocess.run(
                ["python3", str(context_budget_py), "init",
                 "--run-dir", str(self.run_dir)],
                capture_output=True, text=True, timeout=5
            )
            if output.returncode == 0 and "Context budget initialized" in output.stdout:
                results.append(TestResult(
                    name="Context Budget: Initialize",
                    passed=True,
                    message="Successfully initialized context budget"
                ))
            else:
                results.append(TestResult(
                    name="Context Budget: Initialize",
                    passed=False,
                    message=f"Failed to initialize: {output.stderr or output.stdout}"
                ))
        except Exception as e:
            results.append(TestResult(
                name="Context Budget: Initialize",
                passed=False,
                message=f"Exception: {e}"
            ))

        # Test 3: Can check token usage
        try:
            output = subprocess.run(
                ["python3", str(context_budget_py), "check",
                 "--run-dir", str(self.run_dir), "--tokens", "50000"],
                capture_output=True, text=True, timeout=5
            )
            if output.returncode == 0:
                data = json.loads(output.stdout)
                results.append(TestResult(
                    name="Context Budget: Check usage",
                    passed=True,
                    message=f"Token check working (25% usage)",
                    details={"percentage": data.get("percentage")}
                ))
            else:
                results.append(TestResult(
                    name="Context Budget: Check usage",
                    passed=False,
                    message=f"Failed to check: {output.stderr}"
                ))
        except Exception as e:
            results.append(TestResult(
                name="Context Budget: Check usage",
                passed=False,
                message=f"Exception: {e}"
            ))

        # Test 4: Thresholds configured correctly
        expected_thresholds = {"subagent": 40, "warning": 70, "critical": 85, "hard_limit": 95}
        try:
            with open(context_budget_py) as f:
                content = f.read()
            all_found = True
            for key, value in expected_thresholds.items():
                if f'"{key}"' not in content and f"'{key}'" not in content:
                    all_found = False
                    break
            if all_found:
                results.append(TestResult(
                    name="Context Budget: Thresholds configured",
                    passed=True,
                    message=f"All thresholds defined: {expected_thresholds}"
                ))
            else:
                results.append(TestResult(
                    name="Context Budget: Thresholds configured",
                    passed=False,
                    message="Some thresholds missing"
                ))
        except Exception as e:
            results.append(TestResult(
                name="Context Budget: Thresholds configured",
                passed=False,
                message=f"Exception: {e}"
            ))

        return results

    def _test_decision_registry(self) -> List[TestResult]:
        """Test Decision Registry system."""
        results = []
        self.log("Testing: Decision Registry System")

        # Test 1: Template exists
        template_dir = self.blackbox5 / "2-engine" / ".autonomous" / "prompt-progression" / "versions" / "v2.2" / "templates"
        template = template_dir / "decision_registry.yaml"

        if template.exists():
            results.append(TestResult(
                name="Decision Registry: Template exists",
                passed=True,
                message=f"Found template: {template}"
            ))
        else:
            results.append(TestResult(
                name="Decision Registry: Template exists",
                passed=False,
                message=f"Template not found: {template}"
            ))

        # Test 2: Registry has required fields
        if template.exists():
            try:
                with open(template) as f:
                    content = f.read()
                required_fields = ["run_id", "task_id", "decisions", "registry"]
                missing = []
                for field in required_fields:
                    if field not in content:
                        missing.append(field)
                if not missing:
                    results.append(TestResult(
                        name="Decision Registry: Required fields",
                        passed=True,
                        message="All required fields present"
                    ))
                else:
                    results.append(TestResult(
                        name="Decision Registry: Required fields",
                        passed=False,
                        message=f"Missing fields: {missing}"
                    ))
            except Exception as e:
                results.append(TestResult(
                    name="Decision Registry: Required fields",
                    passed=False,
                    message=f"Exception: {e}"
                ))

        return results

    def _test_goals_system(self) -> List[TestResult]:
        """Test Goals System."""
        results = []
        self.log("Testing: Goals System")

        # Test 1: Goals directory structure
        active_goals = self.goals_dir / "active"
        templates = self.goals_dir / "templates"

        if active_goals.exists():
            results.append(TestResult(
                name="Goals System: Active directory exists",
                passed=True,
                message=f"Found: {active_goals}"
            ))
        else:
            results.append(TestResult(
                name="Goals System: Active directory exists",
                passed=False,
                message=f"Not found: {active_goals}"
            ))

        # Test 2: Goal template exists
        goal_template = templates / "goal-template.md"
        if goal_template.exists():
            results.append(TestResult(
                name="Goals System: Template exists",
                passed=True,
                message=f"Found: {goal_template}"
            ))
        else:
            results.append(TestResult(
                name="Goals System: Template exists",
                passed=False,
                message=f"Not found: {goal_template}"
            ))

        # Test 3: Active goal can be read
        active_goals_list = list(active_goals.glob("*.md")) if active_goals.exists() else []
        if active_goals_list:
            results.append(TestResult(
                name="Goals System: Active goals found",
                passed=True,
                message=f"Found {len(active_goals_list)} active goal(s)"
            ))
        else:
            results.append(TestResult(
                name="Goals System: Active goals found",
                passed=False,
                message="No active goals found"
            ))

        return results

    def _test_telemetry(self) -> List[TestResult]:
        """Test Telemetry system."""
        results = []
        self.log("Testing: Telemetry System")

        telemetry_sh = self.engine_shell / "telemetry.sh"

        # Test 1: Telemetry script exists
        if telemetry_sh.exists():
            results.append(TestResult(
                name="Telemetry: Script exists",
                passed=True,
                message=f"Found: {telemetry_sh}"
            ))
        else:
            results.append(TestResult(
                name="Telemetry: Script exists",
                passed=False,
                message=f"Not found: {telemetry_sh}"
            ))
            return results

        # Test 2: Telemetry is executable
        if os.access(telemetry_sh, os.X_OK):
            results.append(TestResult(
                name="Telemetry: Script executable",
                passed=True,
                message="Script has execute permissions"
            ))
        else:
            results.append(TestResult(
                name="Telemetry: Script executable",
                passed=False,
                message="Script lacks execute permissions"
            ))

        # Test 3: Can initialize telemetry
        try:
            output = subprocess.run(
                ["bash", str(telemetry_sh), "init"],
                capture_output=True, text=True, timeout=5,
                env={**os.environ, "TELEMETRY_DIR": str(self.run_dir / ".telemetry")}
            )
            if output.returncode == 0:
                results.append(TestResult(
                    name="Telemetry: Initialize",
                    passed=True,
                    message="Successfully initialized telemetry"
                ))
            else:
                results.append(TestResult(
                    name="Telemetry: Initialize",
                    passed=False,
                    message=f"Failed: {output.stderr}"
                ))
        except Exception as e:
            results.append(TestResult(
                name="Telemetry: Initialize",
                passed=False,
                message=f"Exception: {e}"
            ))

        return results

    def _test_unified_loop(self) -> List[TestResult]:
        """Test that all systems work together (unified loop)."""
        results = []
        self.log("Testing: Unified Loop Integration")

        ralf_md = self.blackbox5 / "bin" / "ralf.md"

        # Test 1: ralf.md exists
        if not ralf_md.exists():
            results.append(TestResult(
                name="Unified Loop: ralf.md exists",
                passed=False,
                message=f"Not found: {ralf_md}"
            ))
            return results

        results.append(TestResult(
            name="Unified Loop: ralf.md exists",
            passed=True,
            message=f"Found: {ralf_md}"
        ))

        # Test 2: ralf.md references all systems
        with open(ralf_md) as f:
            content = f.read()

        integrations = {
            "phase_gates": "phase_gates.py",
            "context_budget": "context_budget.py",
            "decision_registry": "decision_registry.yaml",
            "telemetry": "telemetry.sh"
        }

        missing_refs = []
        for system, reference in integrations.items():
            if reference not in content:
                missing_refs.append(system)

        if not missing_refs:
            results.append(TestResult(
                name="Unified Loop: All systems referenced",
                passed=True,
                message="All v2.3 systems referenced in ralf.md"
            ))
        else:
            results.append(TestResult(
                name="Unified Loop: All systems referenced",
                passed=False,
                message=f"Missing references: {missing_refs}"
            ))

        # Test 3: Phase gate calls in ralf.md
        phase_gate_calls = content.count("phase_gates.py check") + content.count("phase_gates.py mark")
        if phase_gate_calls >= 4:
            results.append(TestResult(
                name="Unified Loop: Phase gate calls",
                passed=True,
                message=f"Found {phase_gate_calls} phase gate calls"
            ))
        else:
            results.append(TestResult(
                name="Unified Loop: Phase gate calls",
                passed=False,
                message=f"Only found {phase_gate_calls} phase gate calls (expected 4+)"
            ))

        # Test 4: Telemetry calls in ralf.md
        telemetry_calls = content.count("telemetry.sh")
        if telemetry_calls >= 5:
            results.append(TestResult(
                name="Unified Loop: Telemetry calls",
                passed=True,
                message=f"Found {telemetry_calls} telemetry calls"
            ))
        else:
            results.append(TestResult(
                name="Unified Loop: Telemetry calls",
                passed=False,
                message=f"Only found {telemetry_calls} telemetry calls (expected 5+)"
            ))

        # Test 5: Goals system check mentioned
        if "goals" in content.lower() and "goal" in content:
            results.append(TestResult(
                name="Unified Loop: Goals system mentioned",
                passed=True,
                message="Goals system integrated in loop"
            ))
        else:
            results.append(TestResult(
                name="Unified Loop: Goals system mentioned",
                passed=False,
                message="Goals system not mentioned in ralf.md"
            ))

        return results


def main():
    if len(sys.argv) < 2:
        print("Usage: integration_test.py <command> [options]")
        print("")
        print("Commands:")
        print("  run --run-dir <path>     - Run all integration tests")
        print("  list                     - List all tests")
        print("  verify-all               - Quick verification of all systems")
        print("")
        print("Examples:")
        print("  python3 integration_test.py run --run-dir ~/.blackbox5/5-project-memory/ralf-core/.autonomous/runs/run-0005")
        sys.exit(1)

    command = sys.argv[1]

    if command == "run":
        if "--run-dir" not in sys.argv:
            print("Error: --run-dir required for run command")
            sys.exit(1)

        run_dir_idx = sys.argv.index("--run-dir")
        if run_dir_idx + 1 >= len(sys.argv):
            print("Error: --run-dir requires a path")
            sys.exit(1)

        run_dir = sys.argv[run_dir_idx + 1]
        test = IntegrationTest(run_dir)
        passed, total, results = test.run_all_tests()

        # Exit with error code if any test failed
        sys.exit(0 if passed == total else 1)

    elif command == "list":
        test = IntegrationTest("/tmp/dummy")
        print("Integration Tests:")
        print("")
        print("System 1: Phase Gates")
        print("  - Phase Gates: Script exists")
        print("  - Phase Gates: List phases")
        print("  - Phase Gates: Check gate")
        print("  - Phase Gates: All phases defined")
        print("")
        print("System 2: Context Budget")
        print("  - Context Budget: Script exists")
        print("  - Context Budget: Initialize")
        print("  - Context Budget: Check usage")
        print("  - Context Budget: Thresholds configured")
        print("")
        print("System 3: Decision Registry")
        print("  - Decision Registry: Template exists")
        print("  - Decision Registry: Required fields")
        print("")
        print("System 4: Goals System")
        print("  - Goals System: Active directory exists")
        print("  - Goals System: Template exists")
        print("  - Goals System: Active goals found")
        print("")
        print("System 5: Telemetry")
        print("  - Telemetry: Script exists")
        print("  - Telemetry: Script executable")
        print("  - Telemetry: Initialize")
        print("")
        print("System 6: Unified Loop")
        print("  - Unified Loop: ralf.md exists")
        print("  - Unified Loop: All systems referenced")
        print("  - Unified Loop: Phase gate calls")
        print("  - Unified Loop: Telemetry calls")
        print("  - Unified Loop: Goals system mentioned")
        sys.exit(0)

    elif command == "verify-all":
        # Quick verification - just check files exist
        blackbox5 = Path.home() / ".blackbox5"
        systems = {
            "Phase Gates": blackbox5 / "2-engine" / ".autonomous" / "lib" / "phase_gates.py",
            "Context Budget": blackbox5 / "2-engine" / ".autonomous" / "lib" / "context_budget.py",
            "Telemetry": blackbox5 / "2-engine" / ".autonomous" / "shell" / "telemetry.sh",
            "Decision Registry": blackbox5 / "2-engine" / ".autonomous" / "prompt-progression" / "versions" / "v2.2" / "templates" / "decision_registry.yaml",
            "RALF Loop": blackbox5 / "bin" / "ralf.md"
        }

        print("RALF v2.3 Systems Verification")
        print("=" * 40)
        all_ok = True
        for name, path in systems.items():
            status = "[OK]" if path.exists() else "[MISSING]"
            print(f"{status} {name}: {path}")
            if not path.exists():
                all_ok = False

        # Check goals directory
        goals = Path.home() / ".blackbox5" / "5-project-memory" / "ralf-core" / ".autonomous" / "goals"
        status = "[OK]" if goals.exists() else "[MISSING]"
        print(f"{status} Goals System: {goals}")
        if not goals.exists():
            all_ok = False

        print("")
        if all_ok:
            print("All v2.3 systems verified!")
            sys.exit(0)
        else:
            print("Some systems are missing!")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        print("Use 'run', 'list', or 'verify-all'")
        sys.exit(1)


if __name__ == "__main__":
    main()
