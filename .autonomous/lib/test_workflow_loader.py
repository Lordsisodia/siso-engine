"""
Unit tests for workflow_loader.py
"""

import unittest
import tempfile
import json
from pathlib import Path
from workflow_loader import (
    WorkflowLoader, Workflow, WorkflowStep, WorkflowComplexity,
    APCMenuConfig, WIPTrackingConfig, WorkflowOutput, load_workflow, load_by_command
)


class TestWorkflowStep(unittest.TestCase):
    """Test WorkflowStep dataclass."""

    def test_from_dict(self):
        data = {
            "name": "discovery",
            "title": "Discovery",
            "description": "Understand the problem",
            "actions": ["Action 1", "Action 2"]
        }
        step = WorkflowStep.from_dict(data)
        self.assertEqual(step.name, "discovery")
        self.assertEqual(step.title, "Discovery")
        self.assertEqual(step.description, "Understand the problem")
        self.assertEqual(len(step.actions), 2)

    def test_from_dict_minimal(self):
        data = {"name": "test", "title": "Test"}
        step = WorkflowStep.from_dict(data)
        self.assertEqual(step.name, "test")
        self.assertEqual(step.actions, [])


class TestWorkflow(unittest.TestCase):
    """Test Workflow dataclass."""

    def test_from_dict(self):
        data = {
            "name": "test-workflow",
            "command": "TW",
            "description": "Test workflow",
            "skill": "bmad-test",
            "agent": "TestAgent",
            "complexity": "simple",
            "steps": [
                {"name": "step1", "title": "Step 1", "description": "First step", "actions": ["Do something"]}
            ],
            "verification": ["Check this"],
            "party_mode_agents": ["agent1", "agent2"]
        }
        workflow = Workflow.from_dict(data)
        self.assertEqual(workflow.name, "test-workflow")
        self.assertEqual(workflow.command, "TW")
        self.assertEqual(workflow.complexity, WorkflowComplexity.SIMPLE)
        self.assertEqual(len(workflow.steps), 1)

    def test_get_step(self):
        data = {
            "name": "test",
            "command": "TE",
            "description": "Test",
            "skill": "bmad-test",
            "agent": "Test",
            "complexity": "simple",
            "steps": [
                {"name": "step1", "title": "Step 1", "description": "First"},
                {"name": "step2", "title": "Step 2", "description": "Second"}
            ]
        }
        workflow = Workflow.from_dict(data)
        step = workflow.get_step("step2")
        self.assertIsNotNone(step)
        self.assertEqual(step.title, "Step 2")

        missing = workflow.get_step("nonexistent")
        self.assertIsNone(missing)

    def test_get_step_names(self):
        data = {
            "name": "test",
            "command": "TE",
            "description": "Test",
            "skill": "bmad-test",
            "agent": "Test",
            "complexity": "simple",
            "steps": [
                {"name": "step1", "title": "Step 1", "description": "First"},
                {"name": "step2", "title": "Step 2", "description": "Second"}
            ]
        }
        workflow = Workflow.from_dict(data)
        names = workflow.get_step_names()
        self.assertEqual(names, ["step1", "step2"])

    def test_get_total_actions(self):
        data = {
            "name": "test",
            "command": "TE",
            "description": "Test",
            "skill": "bmad-test",
            "agent": "Test",
            "complexity": "simple",
            "steps": [
                {"name": "step1", "title": "Step 1", "description": "First", "actions": ["a", "b"]},
                {"name": "step2", "title": "Step 2", "description": "Second", "actions": ["c"]}
            ]
        }
        workflow = Workflow.from_dict(data)
        self.assertEqual(workflow.get_total_actions(), 3)

    def test_invalid_complexity_defaults_to_medium(self):
        data = {
            "name": "test",
            "command": "TE",
            "description": "Test",
            "skill": "bmad-test",
            "agent": "Test",
            "complexity": "invalid",
            "steps": []
        }
        workflow = Workflow.from_dict(data)
        self.assertEqual(workflow.complexity, WorkflowComplexity.MEDIUM)


class TestWorkflowLoader(unittest.TestCase):
    """Test WorkflowLoader class."""

    def setUp(self):
        self.loader = WorkflowLoader()
        self.loader.load_all()

    def test_load_all(self):
        workflows = self.loader.load_all()
        self.assertGreater(len(workflows), 0)
        # Should have 30 workflows based on previous test
        self.assertEqual(len(workflows), 30)

    def test_get_workflow(self):
        workflow = self.loader.get_workflow("create-prd")
        self.assertIsNotNone(workflow)
        self.assertEqual(workflow.command, "CP")

    def test_get_by_command(self):
        workflow = self.loader.get_by_command("CP")
        self.assertIsNotNone(workflow)
        self.assertEqual(workflow.name, "create-prd")

    def test_get_by_skill(self):
        workflows = self.loader.get_by_skill("bmad-pm")
        self.assertGreater(len(workflows), 0)
        for w in workflows:
            self.assertEqual(w.skill, "bmad-pm")

    def test_list_workflows(self):
        names = self.loader.list_workflows()
        self.assertIn("create-prd", names)
        self.assertIn("dev-story", names)

    def test_list_commands(self):
        commands = self.loader.list_commands()
        self.assertIn("CP", commands)
        self.assertIn("DS", commands)

    def test_filter_by_complexity(self):
        complex_workflows = self.loader.filter_by_complexity(WorkflowComplexity.COMPLEX)
        self.assertGreater(len(complex_workflows), 0)
        for w in complex_workflows:
            self.assertEqual(w.complexity, WorkflowComplexity.COMPLEX)

    def test_validate_workflow_valid(self):
        data = {
            "name": "valid",
            "command": "VA",
            "description": "Valid workflow",
            "skill": "bmad-test",
            "agent": "Test",
            "complexity": "simple",
            "steps": [{"name": "step1", "title": "Step 1", "description": "First"}]
        }
        workflow = Workflow.from_dict(data)
        errors = self.loader.validate_workflow(workflow)
        self.assertEqual(errors, [])

    def test_validate_workflow_invalid(self):
        data = {
            "name": "",
            "command": "INVALID",
            "description": "",
            "skill": "",
            "agent": "",
            "complexity": "simple",
            "steps": []
        }
        workflow = Workflow.from_dict(data)
        errors = self.loader.validate_workflow(workflow)
        self.assertGreater(len(errors), 0)
        self.assertIn("Workflow name is required", errors)
        self.assertIn("Command must be 2 letters, got: INVALID", errors)

    def test_validate_all(self):
        errors = self.loader.validate_all()
        # All 30 workflows should be valid
        self.assertEqual(len(errors), 0)

    def test_get_statistics(self):
        stats = self.loader.get_statistics()
        self.assertIn("total_workflows", stats)
        self.assertIn("by_complexity", stats)
        self.assertIn("by_skill", stats)
        self.assertIn("total_steps", stats)
        self.assertIn("total_actions", stats)
        self.assertEqual(stats["total_workflows"], 30)

    def test_export_to_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)

        try:
            self.loader.export_to_json(temp_path)
            self.assertTrue(temp_path.exists())

            with open(temp_path, 'r') as f:
                data = json.load(f)

            self.assertIn("create-prd", data)
            self.assertEqual(data["create-prd"]["command"], "CP")
        finally:
            temp_path.unlink()


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def test_load_workflow(self):
        workflow = load_workflow("create-prd")
        self.assertIsNotNone(workflow)
        self.assertEqual(workflow.name, "create-prd")

    def test_load_by_command(self):
        workflow = load_by_command("CP")
        self.assertIsNotNone(workflow)
        self.assertEqual(workflow.command, "CP")


class TestWorkflowOutput(unittest.TestCase):
    """Test WorkflowOutput dataclass."""

    def test_from_dict(self):
        data = {"type": "prd", "location": "./prd.md", "format": "markdown"}
        output = WorkflowOutput.from_dict(data)
        self.assertEqual(output.type, "prd")
        self.assertEqual(output.location, "./prd.md")
        self.assertEqual(output.format, "markdown")


class TestAPCMenuConfig(unittest.TestCase):
    """Test APCMenuConfig dataclass."""

    def test_from_dict(self):
        data = {
            "enabled": True,
            "options": {
                "advanced": {"label": "Advanced", "description": "Full workflow"},
                "party": {"label": "Party", "description": "Multi-agent"}
            }
        }
        config = APCMenuConfig.from_dict(data)
        self.assertTrue(config.enabled)
        self.assertEqual(len(config.options), 2)
        self.assertEqual(config.options["advanced"].label, "Advanced")


class TestWIPTrackingConfig(unittest.TestCase):
    """Test WIPTrackingConfig dataclass."""

    def test_from_dict(self):
        data = {
            "enabled": True,
            "directory": "./wip",
            "filename_pattern": "{command}-{name}.md"
        }
        config = WIPTrackingConfig.from_dict(data)
        self.assertTrue(config.enabled)
        self.assertEqual(config.directory, "./wip")
        self.assertEqual(config.filename_pattern, "{command}-{name}.md")


if __name__ == "__main__":
    unittest.main()
