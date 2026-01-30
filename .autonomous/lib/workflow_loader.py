"""
Workflow Loader Library for BMAD

Loads and validates workflow YAML files from the workflows/ directory.
Provides programmatic access to workflow definitions.
Part of Agent-2.3 automatic workflow management.
"""

import yaml
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json

logger = logging.getLogger(__name__)


class WorkflowComplexity(Enum):
    """Workflow complexity levels."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    name: str
    title: str
    description: str
    actions: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStep":
        """Create a WorkflowStep from a dictionary."""
        return cls(
            name=data.get("name", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            actions=data.get("actions", [])
        )


@dataclass
class APCMenuOption:
    """A/P/C menu option configuration."""
    label: str
    description: str

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "APCMenuOption":
        """Create an APCMenuOption from a dictionary."""
        return cls(
            label=data.get("label", ""),
            description=data.get("description", "")
        )


@dataclass
class APCMenuConfig:
    """A/P/C menu configuration."""
    enabled: bool
    options: Dict[str, APCMenuOption] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APCMenuConfig":
        """Create an APCMenuConfig from a dictionary."""
        options = {}
        if "options" in data:
            for key, opt_data in data["options"].items():
                options[key] = APCMenuOption.from_dict(opt_data)
        return cls(
            enabled=data.get("enabled", False),
            options=options
        )


@dataclass
class WIPTrackingConfig:
    """WIP tracking configuration."""
    enabled: bool
    directory: str
    filename_pattern: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WIPTrackingConfig":
        """Create a WIPTrackingConfig from a dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            directory=data.get("directory", "./wip"),
            filename_pattern=data.get("filename_pattern", "{command}-{timestamp}.md")
        )


@dataclass
class WorkflowOutput:
    """Workflow output artifact definition."""
    type: str
    location: str
    format: str

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "WorkflowOutput":
        """Create a WorkflowOutput from a dictionary."""
        return cls(
            type=data.get("type", ""),
            location=data.get("location", ""),
            format=data.get("format", "markdown")
        )


@dataclass
class Workflow:
    """Complete workflow definition."""
    name: str
    command: str
    description: str
    skill: str
    agent: str
    complexity: WorkflowComplexity
    steps: List[WorkflowStep] = field(default_factory=list)
    apc_menu: Optional[APCMenuConfig] = None
    wip_tracking: Optional[WIPTrackingConfig] = None
    outputs: List[WorkflowOutput] = field(default_factory=list)
    verification: List[str] = field(default_factory=list)
    party_mode_agents: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """Create a Workflow from a dictionary."""
        complexity_str = data.get("complexity", "medium")
        try:
            complexity = WorkflowComplexity(complexity_str)
        except ValueError:
            complexity = WorkflowComplexity.MEDIUM

        steps = [WorkflowStep.from_dict(step) for step in data.get("steps", [])]

        apc_menu = None
        if "apc_menu" in data:
            apc_menu = APCMenuConfig.from_dict(data["apc_menu"])

        wip_tracking = None
        if "wip_tracking" in data:
            wip_tracking = WIPTrackingConfig.from_dict(data["wip_tracking"])

        outputs = [WorkflowOutput.from_dict(out) for out in data.get("outputs", [])]

        return cls(
            name=data.get("name", ""),
            command=data.get("command", ""),
            description=data.get("description", ""),
            skill=data.get("skill", ""),
            agent=data.get("agent", ""),
            complexity=complexity,
            steps=steps,
            apc_menu=apc_menu,
            wip_tracking=wip_tracking,
            outputs=outputs,
            verification=data.get("verification", []),
            party_mode_agents=data.get("party_mode_agents", []),
            raw_data=data
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow back to dictionary."""
        return {
            "name": self.name,
            "command": self.command,
            "description": self.description,
            "skill": self.skill,
            "agent": self.agent,
            "complexity": self.complexity.value,
            "steps": [
                {
                    "name": step.name,
                    "title": step.title,
                    "description": step.description,
                    "actions": step.actions
                }
                for step in self.steps
            ],
            "apc_menu": {
                "enabled": self.apc_menu.enabled if self.apc_menu else False,
                "options": {
                    key: {"label": opt.label, "description": opt.description}
                    for key, opt in (self.apc_menu.options.items() if self.apc_menu else {})
                }
            } if self.apc_menu else None,
            "wip_tracking": {
                "enabled": self.wip_tracking.enabled if self.wip_tracking else False,
                "directory": self.wip_tracking.directory if self.wip_tracking else "./wip",
                "filename_pattern": self.wip_tracking.filename_pattern if self.wip_tracking else ""
            } if self.wip_tracking else None,
            "outputs": [
                {"type": out.type, "location": out.location, "format": out.format}
                for out in self.outputs
            ],
            "verification": self.verification,
            "party_mode_agents": self.party_mode_agents
        }

    def get_step(self, name: str) -> Optional[WorkflowStep]:
        """Get a step by name."""
        for step in self.steps:
            if step.name == name:
                return step
        return None

    def get_step_names(self) -> List[str]:
        """Get list of all step names."""
        return [step.name for step in self.steps]

    def get_total_actions(self) -> int:
        """Get total number of actions across all steps."""
        return sum(len(step.actions) for step in self.steps)


class WorkflowLoader:
    """Loads and manages workflow definitions from YAML files."""

    def __init__(self, workflows_dir: Optional[Path] = None):
        """
        Initialize the workflow loader.

        Args:
            workflows_dir: Directory containing workflow YAML files.
                         Defaults to ../workflows relative to this file.
        """
        if workflows_dir is None:
            # Default to workflows directory relative to this file
            self.workflows_dir = Path(__file__).parent.parent / "workflows"
        else:
            self.workflows_dir = Path(workflows_dir)

        self._workflows: Dict[str, Workflow] = {}
        self._by_command: Dict[str, Workflow] = {}
        self._by_skill: Dict[str, List[Workflow]] = {}

    def load_all(self) -> Dict[str, Workflow]:
        """
        Load all workflow YAML files from the workflows directory.

        Returns:
            Dictionary mapping workflow names to Workflow objects.
        """
        self._workflows = {}
        self._by_command = {}
        self._by_skill = {}

        if not self.workflows_dir.exists():
            logger.error(f"Workflows directory not found: {self.workflows_dir}")
            return self._workflows

        for yaml_file in self.workflows_dir.glob("*.yaml"):
            try:
                workflow = self.load_file(yaml_file)
                if workflow:
                    self._workflows[workflow.name] = workflow
                    self._by_command[workflow.command] = workflow

                    # Index by skill
                    if workflow.skill not in self._by_skill:
                        self._by_skill[workflow.skill] = []
                    self._by_skill[workflow.skill].append(workflow)

            except Exception as e:
                logger.error(f"Failed to load workflow from {yaml_file}: {e}")

        logger.info(f"Loaded {len(self._workflows)} workflows from {self.workflows_dir}")
        return self._workflows

    def load_file(self, filepath: Path) -> Optional[Workflow]:
        """
        Load a single workflow from a YAML file.

        Args:
            filepath: Path to the YAML file.

        Returns:
            Workflow object or None if loading failed.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data:
                logger.warning(f"Empty workflow file: {filepath}")
                return None

            workflow = Workflow.from_dict(data)
            logger.debug(f"Loaded workflow: {workflow.name} ({workflow.command})")
            return workflow

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {filepath}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading workflow from {filepath}: {e}")
            return None

    def get_workflow(self, name: str) -> Optional[Workflow]:
        """
        Get a workflow by name.

        Args:
            name: Workflow name (e.g., "create-prd").

        Returns:
            Workflow object or None if not found.
        """
        if not self._workflows:
            self.load_all()
        return self._workflows.get(name)

    def get_by_command(self, command: str) -> Optional[Workflow]:
        """
        Get a workflow by its 2-letter command code.

        Args:
            command: 2-letter command code (e.g., "CP").

        Returns:
            Workflow object or None if not found.
        """
        if not self._by_command:
            self.load_all()
        return self._by_command.get(command)

    def get_by_skill(self, skill: str) -> List[Workflow]:
        """
        Get all workflows for a specific skill.

        Args:
            skill: Skill name (e.g., "bmad-pm").

        Returns:
            List of Workflow objects.
        """
        if not self._by_skill:
            self.load_all()
        return self._by_skill.get(skill, [])

    def list_workflows(self) -> List[str]:
        """
        Get a list of all workflow names.

        Returns:
            List of workflow names.
        """
        if not self._workflows:
            self.load_all()
        return list(self._workflows.keys())

    def list_commands(self) -> List[str]:
        """
        Get a list of all workflow commands.

        Returns:
            List of 2-letter command codes.
        """
        if not self._by_command:
            self.load_all()
        return list(self._by_command.keys())

    def filter_by_complexity(self, complexity: WorkflowComplexity) -> List[Workflow]:
        """
        Get workflows filtered by complexity.

        Args:
            complexity: Complexity level to filter by.

        Returns:
            List of Workflow objects.
        """
        if not self._workflows:
            self.load_all()
        return [w for w in self._workflows.values() if w.complexity == complexity]

    def validate_workflow(self, workflow: Workflow) -> List[str]:
        """
        Validate a workflow definition.

        Args:
            workflow: Workflow to validate.

        Returns:
            List of validation errors (empty if valid).
        """
        errors = []

        if not workflow.name:
            errors.append("Workflow name is required")

        if not workflow.command:
            errors.append("Workflow command is required")
        elif len(workflow.command) != 2:
            errors.append(f"Command must be 2 letters, got: {workflow.command}")

        if not workflow.skill:
            errors.append("Workflow skill is required")

        if not workflow.agent:
            errors.append("Workflow agent is required")

        if not workflow.steps:
            errors.append("Workflow must have at least one step")

        for i, step in enumerate(workflow.steps):
            if not step.name:
                errors.append(f"Step {i}: name is required")
            if not step.title:
                errors.append(f"Step {i}: title is required")

        return errors

    def validate_all(self) -> Dict[str, List[str]]:
        """
        Validate all loaded workflows.

        Returns:
            Dictionary mapping workflow names to lists of validation errors.
        """
        if not self._workflows:
            self.load_all()

        results = {}
        for name, workflow in self._workflows.items():
            errors = self.validate_workflow(workflow)
            if errors:
                results[name] = errors

        return results

    def export_to_json(self, output_path: Path) -> None:
        """
        Export all workflows to a JSON file.

        Args:
            output_path: Path to write the JSON file.
        """
        if not self._workflows:
            self.load_all()

        data = {
            name: workflow.to_dict()
            for name, workflow in self._workflows.items()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(data)} workflows to {output_path}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded workflows.

        Returns:
            Dictionary with workflow statistics.
        """
        if not self._workflows:
            self.load_all()

        stats = {
            "total_workflows": len(self._workflows),
            "by_complexity": {
                "simple": 0,
                "medium": 0,
                "complex": 0
            },
            "by_skill": {},
            "total_steps": 0,
            "total_actions": 0,
            "with_apc_menu": 0,
            "with_wip_tracking": 0
        }

        for workflow in self._workflows.values():
            stats["by_complexity"][workflow.complexity.value] += 1
            stats["total_steps"] += len(workflow.steps)
            stats["total_actions"] += workflow.get_total_actions()

            if workflow.apc_menu and workflow.apc_menu.enabled:
                stats["with_apc_menu"] += 1

            if workflow.wip_tracking and workflow.wip_tracking.enabled:
                stats["with_wip_tracking"] += 1

            skill = workflow.skill
            if skill not in stats["by_skill"]:
                stats["by_skill"][skill] = 0
            stats["by_skill"][skill] += 1

        return stats


# Global loader instance for convenience
_default_loader: Optional[WorkflowLoader] = None


def get_loader() -> WorkflowLoader:
    """Get the default workflow loader instance."""
    global _default_loader
    if _default_loader is None:
        _default_loader = WorkflowLoader()
    return _default_loader


def load_workflow(name: str) -> Optional[Workflow]:
    """Convenience function to load a workflow by name."""
    return get_loader().get_workflow(name)


def load_by_command(command: str) -> Optional[Workflow]:
    """Convenience function to load a workflow by command."""
    return get_loader().get_by_command(command)


if __name__ == "__main__":
    # Simple CLI for testing
    import sys

    logging.basicConfig(level=logging.INFO)

    loader = WorkflowLoader()
    workflows = loader.load_all()

    if len(sys.argv) > 1:
        command = sys.argv[1]
        workflow = loader.get_by_command(command)
        if workflow:
            print(f"\nWorkflow: {workflow.name}")
            print(f"Command: {workflow.command}")
            print(f"Agent: {workflow.agent}")
            print(f"Complexity: {workflow.complexity.value}")
            print(f"Steps: {len(workflow.steps)}")
            for step in workflow.steps:
                print(f"  - {step.title}: {len(step.actions)} actions")
        else:
            print(f"Workflow not found: {command}")
    else:
        print(f"\nLoaded {len(workflows)} workflows:")
        for name, workflow in sorted(workflows.items()):
            print(f"  {workflow.command}: {name} ({workflow.agent})")

        print("\nStatistics:")
        stats = loader.get_statistics()
        print(f"  Total: {stats['total_workflows']}")
        print(f"  Steps: {stats['total_steps']}")
        print(f"  Actions: {stats['total_actions']}")
        print(f"  With A/P/C menu: {stats['with_apc_menu']}")
