#!/usr/bin/env python3
"""
BMAD Workflow Generator

Generates workflow YAML files from routes.yaml definitions.
Uses templates and skill files to create complete workflow definitions.
"""

import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class WorkflowGenerator:
    """Generate BMAD workflow YAML files."""

    def __init__(self, engine_path: Path):
        self.engine_path = engine_path
        self.workflows_dir = engine_path / "workflows"
        self.skills_dir = engine_path / "skills"
        self.routes_file = engine_path / "routes.yaml"

    def load_routes(self) -> Dict:
        """Load routes.yaml configuration."""
        with open(self.routes_file, "r") as f:
            return yaml.safe_load(f)

    def generate_workflows(self) -> List[str]:
        """Generate all workflow YAML files from routes.yaml."""
        routes = self.load_routes()
        commands = routes.get("bmad", {}).get("commands", {})

        generated = []

        for command, config in commands.items():
            skill_name = config.get("skill")
            workflow_name = config.get("workflow")
            description = config.get("description", "")

            # Generate workflow YAML
            output_file = self.workflows_dir / f"{workflow_name}.yaml"
            self.generate_workflow_file(
                command=command,
                skill_name=skill_name,
                workflow_name=workflow_name,
                description=description,
                output_file=output_file
            )
            generated.append(str(output_file))

        return generated

    def generate_workflow_file(
        self,
        command: str,
        skill_name: str,
        workflow_name: str,
        description: str,
        output_file: Path
    ):
        """Generate a single workflow YAML file."""

        # Load skill file to get agent info
        skill_file = self.skills_dir / f"{skill_name}.md"
        agent, complexity = self.get_agent_from_skill(skill_file)

        # Get workflow steps from skill
        steps = self.get_steps_from_workflow(skill_file, workflow_name, command)

        # Build workflow YAML
        workflow = {
            "name": workflow_name,
            "command": command,
            "description": description,
            "skill": skill_name,
            "agent": agent,
            "complexity": complexity,
            "steps": steps,
            "apc_menu": self.get_apc_menu_config(),
            "wip_tracking": self.get_wip_config(command),
            "outputs": self.get_outputs(workflow_name),
            "verification": self.get_verification(skill_name),
        }

        # Add party mode agents if complex
        if complexity == "complex":
            workflow["party_mode_agents"] = self.get_party_agents(skill_name)

        # Write YAML file
        with open(output_file, "w") as f:
            f.write(f"# Workflow: {workflow_name.replace('-', ' ').title()}\n")
            f.write(f"# {description}\n\n")
            yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)

    def get_agent_from_skill(self, skill_file: Path) -> tuple:
        """Extract agent name and complexity from skill file."""
        if not skill_file.exists():
            return "Unknown", "medium"

        content = skill_file.read_text()

        # Extract agent name from persona section
        agent = "Unknown"
        for line in content.split("\n"):
            if line.strip().startswith("**Name:**"):
                agent = line.split("**Name:**")[1].strip().strip("*,")
                break

        # Determine complexity from skill
        complexity = "medium"
        if "pm" in skill_file.name or "architect" in skill_file.name:
            complexity = "complex"
        elif "quick" in skill_file.name:
            complexity = "simple"

        return agent, complexity

    def get_steps_from_workflow(
        self, skill_file: Path, workflow_name: str, command: str
    ) -> List[Dict]:
        """Extract steps from skill file for specific workflow."""

        # Default steps based on command
        default_steps = {
            "CP": self.get_create_prd_steps(),
            "VP": self.get_validate_prd_steps(),
            "EP": self.get_edit_prd_steps(),
            "CE": self.get_create_epics_steps(),
            "CA": self.get_create_architecture_steps(),
            "VA": self.get_validate_architecture_steps(),
            "EA": self.get_edit_architecture_steps(),
            "DS": self.get_dev_story_steps(),
            "CR": self.get_code_review_steps(),
            "TS": self.get_tech_spec_steps(),
            "QD": self.get_quick_dev_steps(),
        }

        # Get steps, default to generic if not found
        steps = default_steps.get(
            command,
            self.get_generic_steps(workflow_name)
        )

        return steps

    def get_create_prd_steps(self) -> List[Dict]:
        """Steps for CP (Create PRD) workflow."""
        return [
            {
                "name": "discovery",
                "title": "Discovery",
                "description": "Understand product idea, users, market, and constraints",
                "actions": [
                    "Interview user about problem and solution ideas",
                    "Define target users and user segments",
                    "Identify market context and competition",
                    "Document constraints and assumptions"
                ]
            },
            {
                "name": "success-criteria",
                "title": "Success Criteria",
                "description": "Define user, business, and technical success metrics",
                "actions": [
                    "Define user success metrics",
                    "Define business success metrics",
                    "Define technical success metrics",
                    "Document how success will be measured"
                ]
            },
            {
                "name": "user-journeys",
                "title": "User Journeys",
                "description": "Map narrative journeys for all user types",
                "actions": [
                    "Map user personas and their goals",
                    "Define primary user flows",
                    "Document edge cases and error scenarios",
                    "Identify user pain points to address"
                ]
            },
            {
                "name": "domain-requirements",
                "title": "Domain Requirements",
                "description": "Capture domain-specific needs and constraints",
                "actions": [
                    "Identify domain-specific constraints",
                    "Document regulatory or compliance requirements",
                    "Define domain terminology and vocabulary"
                ]
            },
            {
                "name": "functional-requirements",
                "title": "Functional Requirements",
                "description": "Define THE CAPABILITY CONTRACT",
                "actions": [
                    "List all functional capabilities needed",
                    "Group related capabilities into feature areas",
                    "Prioritize requirements by value and dependency"
                ]
            },
            {
                "name": "non-functional-requirements",
                "title": "Non-Functional Requirements",
                "description": "Define performance, security, and reliability requirements",
                "actions": [
                    "Define performance requirements",
                    "Define security requirements",
                    "Define reliability requirements",
                    "Define scalability requirements"
                ]
            },
            {
                "name": "polish",
                "title": "Polish",
                "description": "Optimize document for flow and readability",
                "actions": [
                    "Review document for clarity and consistency",
                    "Check for redundancy and contradictions",
                    "Ensure professional presentation"
                ]
            },
            {
                "name": "complete",
                "title": "Complete",
                "description": "Finalize PRD and suggest next steps",
                "actions": [
                    "Final review of complete PRD",
                    "Update WIP status to completed",
                    "Archive WIP file",
                    "Output final PRD",
                    "Suggest next steps"
                ]
            }
        ]

    def get_validate_prd_steps(self) -> List[Dict]:
        """Steps for VP (Validate PRD) workflow."""
        return [
            {
                "name": "load-prd",
                "title": "Load PRD",
                "description": "Load and parse the PRD document",
                "actions": ["Read PRD file", "Parse structure", "Identify sections"]
            },
            {
                "name": "check-problem-statement",
                "title": "Check Problem Statement",
                "description": "Verify clear problem statement exists",
                "actions": ["Problem is clearly defined", "Target users identified", "Impact quantified"]
            },
            {
                "name": "check-requirements",
                "title": "Check Requirements",
                "description": "Verify requirements are complete and well-defined",
                "actions": ["Functional requirements sufficient", "NFRs defined", "Success criteria measurable"]
            },
            {
                "name": "check-user-journeys",
                "title": "Check User Journeys",
                "description": "Verify user journeys cover all user types",
                "actions": ["All user types covered", "Edge cases addressed", "Flow is logical"]
            },
            {
                "name": "generate-report",
                "title": "Generate Validation Report",
                "description": "Create validation report with findings",
                "actions": ["List gaps and issues", "Provide recommendations", "Rate overall completeness"]
            }
        ]

    def get_edit_prd_steps(self) -> List[Dict]:
        """Steps for EP (Edit PRD) workflow."""
        return [
            {
                "name": "load-prd",
                "title": "Load PRD",
                "description": "Load existing PRD for editing",
                "actions": ["Read PRD file", "Understand current state", "Identify edit scope"]
            },
            {
                "name": "apply-edits",
                "title": "Apply Edits",
                "description": "Apply requested edits to PRD",
                "actions": ["Update sections", "Add new requirements", "Remove deprecated content"]
            },
            {
                "name": "validate-changes",
                "title": "Validate Changes",
                "description": "Ensure changes maintain PRD integrity",
                "actions": ["Check consistency", "Verify no contradictions", "Ensure completeness"]
            },
            {
                "name": "save-updated-prd",
                "title": "Save Updated PRD",
                "description": "Save the updated PRD",
                "actions": ["Write updated file", "Create changelog", "Archive version"]
            }
        ]

    def get_create_epics_steps(self) -> List[Dict]:
        """Steps for CE (Create Epics) workflow."""
        return [
            {
                "name": "analyze-prd",
                "title": "Analyze PRD",
                "description": "Read and understand the PRD",
                "actions": ["Read PRD file", "Identify capability areas", "Understand requirements"]
            },
            {
                "name": "group-capabilities",
                "title": "Group Capabilities",
                "description": "Group related capabilities into epics",
                "actions": ["Identify natural groupings", "Create epic themes", "Assign capabilities"]
            },
            {
                "name": "break-down-stories",
                "title": "Break Down Stories",
                "description": "Break epics into implementable stories",
                "actions": ["Define story scope", "Estimate complexity", "Identify dependencies"]
            },
            {
                "name": "prioritize",
                "title": "Prioritize",
                "description": "Prioritize epics and stories",
                "actions": ["Value vs effort analysis", "Dependency ordering", "MVP identification"]
            },
            {
                "name": "output-plan",
                "title": "Output Plan",
                "description": "Create epics and stories document",
                "actions": ["Generate epic list", "Generate story backlog", "Define sprint cadence"]
            }
        ]

    def get_create_architecture_steps(self) -> List[Dict]:
        """Steps for CA (Create Architecture) workflow."""
        return [
            {
                "name": "analyze-requirements",
                "title": "Analyze Requirements",
                "description": "Analyze PRD and derive architectural requirements",
                "actions": ["Read PRD", "Identify key constraints", "Extract technical requirements"]
            },
            {
                "name": "design-components",
                "title": "Design Components",
                "description": "Design system components and boundaries",
                "actions": ["Define components", "Establish boundaries", "Identify interfaces"]
            },
            {
                "name": "design-data-model",
                "title": "Design Data Model",
                "description": "Design database schema and data flow",
                "actions": ["Define entities", "Design relationships", "Plan data access patterns"]
            },
            {
                "name": "design-apis",
                "title": "Design APIs",
                "description": "Design API contracts and endpoints",
                "actions": ["Define endpoints", "Specify contracts", "Document authentication"]
            },
            {
                "name": "consider-nsqrs",
                "title": "Consider NFRs",
                "description": "Address non-functional requirements",
                "actions": ["Performance strategy", "Security measures", "Reliability patterns"]
            },
            {
                "name": "create-adrs",
                "title": "Create ADRs",
                "description": "Document architectural decisions",
                "actions": ["Record key decisions", "Document alternatives", "Explain trade-offs"]
            },
            {
                "name": "output-architecture",
                "title": "Output Architecture",
                "description": "Generate architecture documentation",
                "actions": ["Create architecture doc", "Generate diagrams", "Document decisions"]
            }
        ]

    def get_validate_architecture_steps(self) -> List[Dict]:
        """Steps for VA (Validate Architecture) workflow."""
        return [
            {
                "name": "load-architecture",
                "title": "Load Architecture",
                "description": "Load and parse architecture document",
                "actions": ["Read architecture doc", "Understand design", "Identify scope"]
            },
            {
                "name": "check-coverage",
                "title": "Check Coverage",
                "description": "Verify architecture covers all requirements",
                "actions": ["Functional coverage", "NFR coverage", "Edge cases"]
            },
            {
                "name": "check-feasibility",
                "title": "Check Feasibility",
                "description": "Verify design is implementable",
                "actions": ["Technical feasibility", "Resource requirements", "Timeline realism"]
            },
            {
                "name": "check-consistency",
                "title": "Check Consistency",
                "description": "Verify design is internally consistent",
                "actions": ["Interface consistency", "Data flow consistency", "Pattern consistency"]
            },
            {
                "name": "generate-report",
                "title": "Generate Report",
                "description": "Create validation report",
                "actions": ["List issues", "Provide recommendations", "Rate completeness"]
            }
        ]

    def get_edit_architecture_steps(self) -> List[Dict]:
        """Steps for EA (Edit Architecture) workflow."""
        return [
            {
                "name": "load-architecture",
                "title": "Load Architecture",
                "description": "Load existing architecture",
                "actions": ["Read architecture doc", "Understand current design"]
            },
            {
                "name": "apply-changes",
                "title": "Apply Changes",
                "description": "Apply requested changes",
                "actions": ["Update components", "Modify data model", "Revise APIs"]
            },
            {
                "name": "validate-integrity",
                "title": "Validate Integrity",
                "description": "Ensure changes maintain integrity",
                "actions": ["Check consistency", "Verify interfaces", "Update ADRs"]
            },
            {
                "name": "save-changes",
                "title": "Save Changes",
                "description": "Save updated architecture",
                "actions": ["Write updated doc", "Document changes", "Version control"]
            }
        ]

    def get_dev_story_steps(self) -> List[Dict]:
        """Steps for DS (Dev Story) workflow."""
        return [
            {
                "name": "read-task",
                "title": "Read Task",
                "description": "Read and understand the task",
                "actions": ["Read task description", "Understand requirements", "Identify scope"]
            },
            {
                "name": "analyze-code",
                "title": "Analyze Code",
                "description": "Analyze existing codebase",
                "actions": ["Read relevant files", "Understand patterns", "Identify entry points"]
            },
            {
                "name": "plan-changes",
                "title": "Plan Changes",
                "description": "Plan implementation approach",
                "actions": ["Design solution", "Identify affected files", "Plan tests"]
            },
            {
                "name": "implement",
                "title": "Implement",
                "description": "Write code changes",
                "actions": ["Make atomic changes", "Follow patterns", "Add comments"]
            },
            {
                "name": "test",
                "title": "Test",
                "description": "Test the changes",
                "actions": ["Run tests", "Manual verification", "Edge cases"]
            },
            {
                "name": "commit",
                "title": "Commit",
                "description": "Commit changes",
                "actions": ["Stage files", "Write commit message", "Push changes"]
            }
        ]

    def get_code_review_steps(self) -> List[Dict]:
        """Steps for CR (Code Review) workflow."""
        return [
            {
                "name": "load-changes",
                "title": "Load Changes",
                "description": "Load code changes for review",
                "actions": ["Read diff", "Understand context", "Identify scope"]
            },
            {
                "name": "review-functionality",
                "title": "Review Functionality",
                "description": "Review functional correctness",
                "actions": ["Check logic", "Verify requirements met", "Check edge cases"]
            },
            {
                "name": "review-code-quality",
                "title": "Review Code Quality",
                "description": "Review code quality",
                "actions": ["Check naming", "Review structure", "Check for complexity"]
            },
            {
                "name": "review-tests",
                "title": "Review Tests",
                "description": "Review test coverage",
                "actions": ["Check test coverage", "Review test quality", "Verify assertions"]
            },
            {
                "name": "provide-feedback",
                "title": "Provide Feedback",
                "description": "Provide review feedback",
                "actions": ["List issues", "Suggest improvements", "Approve or request changes"]
            }
        ]

    def get_tech_spec_steps(self) -> List[Dict]:
        """Steps for TS (Tech Spec) workflow."""
        return [
            {
                "name": "read-task",
                "title": "Read Task",
                "description": "Read and understand task requirements",
                "actions": ["Read task description", "Clarify requirements", "Identify scope"]
            },
            {
                "name": "analyze-codebase",
                "title": "Analyze Codebase",
                "description": "Analyze relevant code",
                "actions": ["Find relevant files", "Understand patterns", "Identify integration points"]
            },
            {
                "name": "design-solution",
                "title": "Design Solution",
                "description": "Design implementation approach",
                "actions": ["Define approach", "Identify files to modify", "Plan changes"]
            },
            {
                "name": "identify-tests",
                "title": "Identify Tests",
                "description": "Identify tests needed",
                "actions": ["Find existing tests", "Plan new tests", "Identify edge cases"]
            },
            {
                "name": "assess-risk",
                "title": "Assess Risk",
                "description": "Assess implementation risk",
                "actions": ["Identify risks", "Plan mitigation", "Assess rollback strategy"]
            },
            {
                "name": "write-spec",
                "title": "Write Spec",
                "description": "Write technical specification",
                "actions": ["Document approach", "List files", "Specify tests", "Note risks"]
            }
        ]

    def get_quick_dev_steps(self) -> List[Dict]:
        """Steps for QD (Quick Dev) workflow."""
        return [
            {
                "name": "read-context",
                "title": "Read Context",
                "description": "Quickly read relevant context",
                "actions": ["Read task", "Scan relevant files", "Understand the fix"]
            },
            {
                "name": "implement",
                "title": "Implement",
                "description": "Make the change",
                "actions": ["Write code", "Follow existing patterns", "Keep it simple"]
            },
            {
                "name": "test",
                "title": "Test",
                "description": "Test the change",
                "actions": ["Quick manual test", "Run existing tests", "Verify fix"]
            },
            {
                "name": "verify",
                "title": "Verify",
                "description": "Verify no regressions",
                "actions": ["Check related functionality", "Run broader tests", "Verify edge cases"]
            },
            {
                "name": "ship",
                "title": "Ship",
                "description": "Commit and push",
                "actions": ["Stage files", "Commit with clear message", "Push changes"]
            }
        ]

    def get_generic_steps(self, workflow_name: str) -> List[Dict]:
        """Generate generic steps for unknown workflows."""
        title = workflow_name.replace("-", " ").title()
        return [
            {
                "name": "start",
                "title": "Start",
                "description": f"Start {title}",
                "actions": ["Initialize workflow", "Create WIP file"]
            },
            {
                "name": "execute",
                "title": "Execute",
                "description": f"Execute {title}",
                "actions": ["Perform main workflow", "Track progress"]
            },
            {
                "name": "complete",
                "title": "Complete",
                "description": f"Complete {title}",
                "actions": ["Finalize", "Update WIP", "Archive"]
            }
        ]

    def get_apc_menu_config(self) -> Dict:
        """Get A/P/C menu configuration."""
        return {
            "enabled": True,
            "options": {
                "advanced": {
                    "label": "Advanced",
                    "description": "Full workflow with all steps, detailed documentation"
                },
                "party": {
                    "label": "Party",
                    "description": "Multi-agent collaborative mode"
                },
                "continue": {
                    "label": "Continue",
                    "description": "Resume from last saved checkpoint"
                }
            }
        }

    def get_wip_config(self, command: str) -> Dict:
        """Get WIP tracking configuration."""
        return {
            "enabled": True,
            "directory": "./wip",
            "filename_pattern": f"{command.lower()}-{{name}}-{{timestamp}}.md"
        }

    def get_outputs(self, workflow_name: str) -> List[Dict]:
        """Get output artifacts for workflow."""
        return [
            {
                "type": "artifact",
                "location": f"./artifacts/{workflow_name}-{{name}}.md",
                "format": "markdown"
            },
            {
                "type": "wip",
                "location": "./wip/{command}-{name}-{timestamp}.md",
                "format": "markdown"
            }
        ]

    def get_verification(self, skill_name: str) -> List[str]:
        """Get verification checklist for skill."""
        base = [
            "WIP file created and updated",
            "All steps completed",
            "Output artifacts generated"
        ]

        skill_specific = {
            "bmad-pm": [
                "Problem statement clear",
                "Requirements complete",
                "User journeys documented",
                "Success criteria measurable"
            ],
            "bmad-dev": [
                "Code follows patterns",
                "Tests pass",
                "No regressions",
                "Changes committed"
            ],
            "bmad-qa": [
                "Tests cover requirements",
                "Test quality verified",
                "Coverage adequate",
                "Tests pass"
            ],
            "bmad-architect": [
                "Components defined",
                "Interfaces specified",
                "Data model designed",
                "NFRs addressed"
            ]
        }

        return base + skill_specific.get(skill_name, [])

    def get_party_agents(self, skill_name: str) -> List[str]:
        """Get recommended agents for party mode."""
        party_configs = {
            "bmad-pm": ["bmad-pm", "bmad-analyst", "bmad-architect"],
            "bmad-architect": ["bmad-architect", "bmad-dev", "bmad-qa"],
            "bmad-dev": ["bmad-dev", "bmad-qa"],
            "bmad-qa": ["bmad-qa", "bmad-dev"],
            "bmad-analyst": ["bmad-analyst", "bmad-pm"],
            "bmad-ux": ["bmad-ux", "bmad-pm", "bmad-dev"],
        }
        return party_configs.get(skill_name, [skill_name])


def main():
    """Generate all workflow YAML files."""
    import sys

    engine_path = Path(__file__).parent.parent
    generator = WorkflowGenerator(engine_path)

    print("Generating BMAD workflow YAML files...")
    generated = generator.generate_workflows()

    print(f"\nGenerated {len(generated)} workflow files:")
    for f in generated:
        print(f"  - {f}")

    print("\nDone!")


if __name__ == "__main__":
    main()
