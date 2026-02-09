#!/usr/bin/env python3
"""
Unit tests for Decision Registry Library

Tests the decision tracking with reversibility assessment system.
Run with: pytest test_decision_registry.py -v
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent))

from decision_registry import DecisionRegistry


class TestDecisionRegistry(unittest.TestCase):
    """Test cases for DecisionRegistry class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.registry_path = Path(self.temp_dir) / "decision_registry.yaml"
        self.template_path = Path(self.temp_dir) / "template.yaml"

        # Create a minimal template
        self._create_template()

    def tearDown(self):
        """Clean up test fixtures."""
        if self.registry_path.exists():
            self.registry_path.unlink()
        if self.template_path.exists():
            self.template_path.unlink()
        os.rmdir(self.temp_dir)

    def _create_template(self):
        """Create a template file for testing."""
        template_content = """run_id: "RUN-ID-PLACEHOLDER"
task_id: "TASK-ID-PLACEHOLDER"
created_at: "TIMESTAMP-PLACEHOLDER"

registry:
  total_decisions: 0
  reversible_decisions: 0
  irreversible_decisions: 0
  pending_verification: 0
  verified_decisions: 0
  rolled_back_decisions: 0

decisions: []
"""
        with open(self.template_path, 'w') as f:
            f.write(template_content)

    def test_init_creates_new_registry(self):
        """Test that initializing creates a new registry."""
        registry = DecisionRegistry(str(self.registry_path))
        self.assertEqual(registry._data, {"decisions": []})

    def test_initialize_from_template(self):
        """Test initializing from template."""
        registry = DecisionRegistry(str(self.registry_path))
        registry.initialize_from_template(
            str(self.template_path),
            run_id="run-123",
            task_id="task-456"
        )

        self.assertEqual(registry._data["run_id"], "run-123")
        self.assertEqual(registry._data["task_id"], "task-456")
        self.assertIn("created_at", registry._data)
        self.assertEqual(registry._data["decisions"], [])

    def test_record_minimal_decision(self):
        """Test recording a minimal decision."""
        registry = DecisionRegistry(str(self.registry_path))

        decision = {
            "phase": "PLAN",
            "context": "Test decision"
        }

        decision_id = registry.record_decision(decision)

        self.assertIsNotNone(decision_id)
        self.assertTrue(decision_id.startswith("DEC-"))

        # Verify decision was saved
        retrieved = registry.get_decision(decision_id)
        self.assertEqual(retrieved["context"], "Test decision")
        self.assertEqual(retrieved["status"], "DECIDED")

    def test_record_full_decision(self):
        """Test recording a full decision with all fields."""
        registry = DecisionRegistry(str(self.registry_path))

        decision = {
            "phase": "PLAN",
            "context": "Choosing database approach",
            "options_considered": [
                {
                    "id": "OPT-001",
                    "description": "PostgreSQL",
                    "pros": ["ACID compliant", "Reliable"],
                    "cons": ["More complex"]
                },
                {
                    "id": "OPT-002",
                    "description": "SQLite",
                    "pros": ["Simple", "Embedded"],
                    "cons": ["No concurrent writes"]
                }
            ],
            "selected_option": "OPT-001",
            "rationale": "Better for production scale",
            "assumptions": [
                {
                    "id": "ASM-001",
                    "statement": "Query volume will exceed 10k/min",
                    "risk_level": "MEDIUM",
                    "verification_method": "Load testing",
                    "status": "PENDING_VERIFICATION"
                }
            ],
            "reversibility": "MEDIUM",
            "rollback_complexity": "Requires migration",
            "rollback_steps": [
                "Create migration script",
                "Update API layer"
            ],
            "verification": {
                "required": True,
                "criteria": ["Query performance < 100ms p95"]
            }
        }

        decision_id = registry.record_decision(decision)

        retrieved = registry.get_decision(decision_id)
        self.assertEqual(retrieved["selected_option"], "OPT-001")
        self.assertEqual(len(retrieved["options_considered"]), 2)
        self.assertEqual(len(retrieved["assumptions"]), 1)
        self.assertEqual(retrieved["reversibility"], "MEDIUM")

    def test_record_decision_with_custom_id(self):
        """Test recording a decision with custom ID."""
        registry = DecisionRegistry(str(self.registry_path))

        decision = {
            "id": "DEC-CUSTOM-001",
            "phase": "ALIGN",
            "context": "Custom ID decision"
        }

        decision_id = registry.record_decision(decision)
        self.assertEqual(decision_id, "DEC-CUSTOM-001")

    def test_validate_decision_missing_required_field(self):
        """Test validation fails with missing required field."""
        registry = DecisionRegistry(str(self.registry_path))

        decision = {
            "context": "Test"  # Missing phase
        }

        with self.assertRaises(ValueError) as cm:
            registry.record_decision(decision)
        self.assertIn("phase", str(cm.exception))

    def test_validate_decision_invalid_phase(self):
        """Test validation fails with invalid phase."""
        registry = DecisionRegistry(str(self.registry_path))

        decision = {
            "phase": "INVALID_PHASE",
            "context": "Test"
        }

        with self.assertRaises(ValueError) as cm:
            registry.record_decision(decision)
        self.assertIn("phase", str(cm.exception))

    def test_verify_decision(self):
        """Test verifying a decision."""
        registry = DecisionRegistry(str(self.registry_path))

        # First record a decision
        decision = {
            "phase": "PLAN",
            "context": "Test decision",
            "assumptions": [
                {
                    "id": "ASM-001",
                    "statement": "Test assumption",
                    "risk_level": "LOW",
                    "verification_method": "Unit test"
                }
            ],
            "verification": {"required": True}
        }
        decision_id = registry.record_decision(decision)

        # Verify the decision
        verification = {
            "verified_by": "TestAgent",
            "results": {
                "ASM-001": "PASS"
            }
        }
        registry.verify_decision(decision_id, verification)

        # Check status updated
        retrieved = registry.get_decision(decision_id)
        self.assertEqual(retrieved["status"], "VERIFIED")
        self.assertEqual(retrieved["assumptions"][0]["status"], "VERIFIED")
        self.assertEqual(retrieved["verification"]["verified_by"], "TestAgent")

    def test_verify_decision_with_failure(self):
        """Test verifying a decision with failed assumption."""
        registry = DecisionRegistry(str(self.registry_path))

        decision = {
            "phase": "PLAN",
            "context": "Test decision",
            "assumptions": [
                {
                    "id": "ASM-001",
                    "statement": "Test assumption",
                    "risk_level": "HIGH",
                    "verification_method": "Load test"
                }
            ]
        }
        decision_id = registry.record_decision(decision)

        verification = {
            "verified_by": "TestAgent",
            "results": {
                "ASM-001": "FAIL"
            }
        }
        registry.verify_decision(decision_id, verification)

        retrieved = registry.get_decision(decision_id)
        self.assertEqual(retrieved["assumptions"][0]["status"], "FAILED")

    def test_get_decision_not_found(self):
        """Test getting non-existent decision raises error."""
        registry = DecisionRegistry(str(self.registry_path))

        with self.assertRaises(ValueError) as cm:
            registry.get_decision("DEC-NONEXISTENT")
        self.assertIn("not found", str(cm.exception))

    def test_list_decisions_no_filter(self):
        """Test listing all decisions."""
        registry = DecisionRegistry(str(self.registry_path))

        registry.record_decision({"phase": "PLAN", "context": "Decision 1"})
        registry.record_decision({"phase": "EXECUTE", "context": "Decision 2"})

        decisions = registry.list_decisions()
        self.assertEqual(len(decisions), 2)

    def test_list_decisions_filter_by_status(self):
        """Test listing decisions filtered by status."""
        registry = DecisionRegistry(str(self.registry_path))

        d1 = registry.record_decision({"phase": "PLAN", "context": "Decision 1"})
        d2 = registry.record_decision({"phase": "PLAN", "context": "Decision 2", "status": "PROPOSED"})

        decided = registry.list_decisions(status="DECIDED")
        proposed = registry.list_decisions(status="PROPOSED")

        self.assertEqual(len(decided), 1)
        self.assertEqual(len(proposed), 1)

    def test_list_decisions_filter_by_phase(self):
        """Test listing decisions filtered by phase."""
        registry = DecisionRegistry(str(self.registry_path))

        registry.record_decision({"phase": "PLAN", "context": "Decision 1"})
        registry.record_decision({"phase": "EXECUTE", "context": "Decision 2"})

        plan_decisions = registry.list_decisions(phase="PLAN")
        execute_decisions = registry.list_decisions(phase="EXECUTE")

        self.assertEqual(len(plan_decisions), 1)
        self.assertEqual(len(execute_decisions), 1)

    def test_get_rollback_plan(self):
        """Test getting rollback plan."""
        registry = DecisionRegistry(str(self.registry_path))

        decision = {
            "phase": "PLAN",
            "context": "Database schema choice",
            "selected_option": "OPT-001",
            "reversibility": "MEDIUM",
            "rollback_complexity": "Requires migration",
            "rollback_steps": [
                "Create migration script",
                "Update API layer"
            ]
        }
        decision_id = registry.record_decision(decision)

        plan = registry.get_rollback_plan(decision_id)

        self.assertEqual(plan["decision_id"], decision_id)
        self.assertEqual(plan["reversibility"], "MEDIUM")
        self.assertEqual(plan["can_rollback"], True)
        self.assertEqual(len(plan["rollback_steps"]), 2)

    def test_get_rollback_plan_irreversible(self):
        """Test rollback plan for irreversible decision."""
        registry = DecisionRegistry(str(self.registry_path))

        decision = {
            "phase": "EXECUTE",
            "context": "Delete production data",
            "selected_option": "DELETE",
            "reversibility": "HIGH",  # Irreversible
            "rollback_steps": ["Cannot rollback"]
        }
        decision_id = registry.record_decision(decision)

        plan = registry.get_rollback_plan(decision_id)
        self.assertEqual(plan["can_rollback"], False)

    def test_finalize(self):
        """Test finalizing registry."""
        registry = DecisionRegistry(str(self.registry_path))

        registry.record_decision({"phase": "PLAN", "context": "Decision 1"})
        registry.record_decision({"phase": "EXECUTE", "context": "Decision 2"})

        summary = registry.finalize()

        self.assertEqual(summary["registry"]["total_decisions"], 2)
        self.assertIn("completeness", summary)
        self.assertIn("decisions_by_status", summary)
        self.assertIn("decisions_by_phase", summary)

    def test_finalize_with_issues(self):
        """Test finalizing detects incomplete verifications."""
        registry = DecisionRegistry(str(self.registry_path))

        decision = {
            "phase": "PLAN",
            "context": "Decision requiring verification",
            "assumptions": [
                {
                    "id": "ASM-001",
                    "statement": "Unverified assumption",
                    "risk_level": "MEDIUM"
                }
            ],
            "verification": {"required": True}
        }
        registry.record_decision(decision)

        summary = registry.finalize()

        self.assertEqual(summary["completeness"], "INVALID")
        self.assertTrue(len(summary["issues"]) > 0)
        self.assertTrue(any("pending verification" in i.lower() for i in summary["issues"]))

    def test_metadata_updates(self):
        """Test metadata is updated correctly."""
        registry = DecisionRegistry(str(self.registry_path))

        # Record various decisions
        registry.record_decision({
            "phase": "PLAN",
            "context": "Reversible decision",
            "reversibility": "LOW"
        })
        registry.record_decision({
            "phase": "PLAN",
            "context": "Irreversible decision",
            "reversibility": "HIGH"
        })

        summary = registry.finalize()

        self.assertEqual(summary["registry"]["total_decisions"], 2)
        self.assertEqual(summary["registry"]["reversible_decisions"], 1)
        self.assertEqual(summary["registry"]["irreversible_decisions"], 1)


class TestCLI(unittest.TestCase):
    """Test CLI interface."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.registry_path = Path(self.temp_dir) / "decision_registry.yaml"
        self.template_path = Path(self.temp_dir) / "template.yaml"
        self._create_template()

    def tearDown(self):
        """Clean up."""
        for f in [self.registry_path, self.template_path]:
            if f.exists():
                f.unlink()
        os.rmdir(self.temp_dir)

    def _create_template(self):
        """Create template file."""
        template_content = """run_id: "RUN-ID-PLACEHOLDER"
task_id: "TASK-ID-PLACEHOLDER"
created_at: "TIMESTAMP-PLACEHOLDER"
registry:
  total_decisions: 0
  reversible_decisions: 0
  irreversible_decisions: 0
  pending_verification: 0
  verified_decisions: 0
  rolled_back_decisions: 0
decisions: []
"""
        with open(self.template_path, 'w') as f:
            f.write(template_content)

    def test_cli_init(self):
        """Test CLI init command."""
        from decision_registry import cli_init
        import argparse

        args = argparse.Namespace(
            run_dir=self.temp_dir,
            template=str(self.template_path),
            run_id="run-test",
            task_id="task-test"
        )

        cli_init(args)

        # Verify registry was created
        self.assertTrue(self.registry_path.exists())

        registry = DecisionRegistry(str(self.registry_path))
        self.assertEqual(registry._data["run_id"], "run-test")

    def test_cli_record(self):
        """Test CLI record command."""
        from decision_registry import cli_record
        import argparse

        # First initialize
        registry = DecisionRegistry(str(self.registry_path))
        registry.initialize_from_template(str(self.template_path))

        decision = json.dumps({
            "phase": "PLAN",
            "context": "CLI test decision"
        })

        args = argparse.Namespace(
            registry=str(self.registry_path),
            decision=decision
        )

        cli_record(args)

        # Verify decision was recorded
        registry = DecisionRegistry(str(self.registry_path))
        decisions = registry.list_decisions()
        self.assertEqual(len(decisions), 1)

    def test_cli_verify(self):
        """Test CLI verify command."""
        from decision_registry import cli_verify
        import argparse

        # Setup
        registry = DecisionRegistry(str(self.registry_path))
        registry.initialize_from_template(str(self.template_path))
        decision_id = registry.record_decision({
            "phase": "PLAN",
            "context": "Test",
            "assumptions": [
                {"id": "ASM-001", "statement": "Test", "risk_level": "LOW"}
            ]
        })

        results = json.dumps({"ASM-001": "PASS"})

        args = argparse.Namespace(
            registry=str(self.registry_path),
            id=decision_id,
            verified_by="CLI-Test",
            results=results,
            notes=None
        )

        cli_verify(args)

        # Verify
        registry = DecisionRegistry(str(self.registry_path))
        decision = registry.get_decision(decision_id)
        self.assertEqual(decision["status"], "VERIFIED")

    def test_cli_list(self):
        """Test CLI list command."""
        from decision_registry import cli_list
        import argparse
        from io import StringIO
        import sys as sys_module

        # Setup
        registry = DecisionRegistry(str(self.registry_path))
        registry.initialize_from_template(str(self.template_path))
        registry.record_decision({"phase": "PLAN", "context": "Decision 1"})
        registry.record_decision({"phase": "EXECUTE", "context": "Decision 2"})

        args = argparse.Namespace(
            registry=str(self.registry_path),
            status=None,
            phase=None,
            verbose=False
        )

        # Capture output
        old_stdout = sys_module.stdout
        captured_output = StringIO()
        sys_module.stdout = captured_output

        cli_list(args)

        output = captured_output.getvalue()
        sys_module.stdout = old_stdout

        self.assertIn("Decisions: 2", output)

    def test_cli_rollback(self):
        """Test CLI rollback command."""
        from decision_registry import cli_rollback
        import argparse
        from io import StringIO
        import sys as sys_module

        # Setup
        registry = DecisionRegistry(str(self.registry_path))
        registry.initialize_from_template(str(self.template_path))
        decision_id = registry.record_decision({
            "phase": "PLAN",
            "context": "Test decision",
            "selected_option": "OPT-001",
            "reversibility": "MEDIUM",
            "rollback_complexity": "Simple",
            "rollback_steps": ["Undo the change"]
        })

        args = argparse.Namespace(
            registry=str(self.registry_path),
            id=decision_id
        )

        # Capture output
        old_stdout = sys_module.stdout
        sys_module.stdout = StringIO()

        cli_rollback(args)

        output = sys_module.stdout.getvalue()
        sys_module.stdout = old_stdout

        self.assertIn("Rollback Plan", output)
        self.assertIn("MEDIUM", output)

    def test_cli_finalize(self):
        """Test CLI finalize command."""
        from decision_registry import cli_finalize
        import argparse
        from io import StringIO
        import sys as sys_module

        # Setup
        registry = DecisionRegistry(str(self.registry_path))
        registry.initialize_from_template(str(self.template_path))
        registry.record_decision({"phase": "PLAN", "context": "Decision 1"})

        args = argparse.Namespace(
            registry=str(self.registry_path)
        )

        # Capture output
        old_stdout = sys_module.stdout
        sys_module.stdout = StringIO()

        cli_finalize(args)

        output = sys_module.stdout.getvalue()
        sys_module.stdout = old_stdout

        self.assertIn("Total Decisions: 1", output)
        self.assertIn("PLAN: 1", output)


if __name__ == "__main__":
    unittest.main()
