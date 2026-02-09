#!/usr/bin/env python3
"""
PRD Commands for BlackBox5 CLI
================================

Command layer for PRD (Product Requirements Document) operations.

Provides CLI commands for:
- `bb5 prd:new` - Create new PRD interactively
- `bb5 prd:parse` - Parse PRD file and display structure
- `bb5 prd:validate` - Validate PRD completeness
- `bb5 prd:list` - List all PRDs

Based on BlackBox5 Week 1, Workstream 1B requirements.
"""

import os
import sys
import logging
from typing import Optional, List
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from engine.cli.base import BaseCommand, CommandError
from engine.spec_driven.prd_agent import PRDAgent, PRDData
from engine.spec_driven.config import load_config
from engine.spec_driven.exceptions import PRDValidationError

logger = logging.getLogger(__name__)


class PRDNewCommand(BaseCommand):
    """
    Command to create a new PRD interactively.

    Usage:
        bb5 prd:new [options]

    Options:
        --title: PRD title (if not provided, will prompt)
        --author: PRD author (if not provided, will prompt)
        --non-interactive: Skip prompts, use defaults
        --output: Output file path
    """

    name = "prd:new"
    description = "Create a new PRD interactively with first principles analysis"
    aliases = ["prd:create", "new-prd"]

    def execute(self, args: dict) -> int:
        """Execute the PRD new command."""
        try:
            # Load configuration
            config = load_config()

            # Initialize PRD agent
            agent = PRDAgent(config.paths.prds_dir)

            # Get title and author
            title = args.get('title')
            author = args.get('author', os.getenv('USER', 'Unknown'))

            if not title:
                if args.get('non_interactive'):
                    raise CommandError("Title required in non-interactive mode")
                title = input("PRD Title: ")

            if not author:
                author = input(f"Author [{author}]: ") or author

            print(f"\n{'='*60}")
            print(f"Creating PRD: {title}")
            print(f"Author: {author}")
            print(f"{'='*60}\n")

            # Check if interactive mode
            if args.get('interactive') and not args.get('non_interactive'):
                print("Starting interactive PRD creation with first principles analysis...")
                print("(Press Enter with empty line to finish each section)\n")

                # Guide user through first principles
                problem = self._prompt_section(
                    "PROBLEM STATEMENT",
                    "What problem are we trying to solve?",
                    multiline=True
                )

                print("\nFUNDAMENTAL TRUTHS (observable, verifiable facts):")
                truths = []
                while True:
                    truth = input(f"  Truth {len(truths) + 1} (empty to finish): ")
                    if not truth:
                        break
                    truths.append(truth)

                print("\nASSUMPTIONS (what we believe but need to verify):")
                assumptions = []
                while True:
                    assumption = input(f"  Assumption {len(assumptions) + 1} (empty to finish): ")
                    if not assumption:
                        break
                    verification = input("    How to verify? ")
                    assumptions.append({
                        'assumption': assumption,
                        'verified': 'No',
                        'verification_method': verification
                    })

                print("\nREAL CONSTRAINTS (laws of physics, time, resources):")
                real_constraints = []
                while True:
                    constraint = input(f"  Constraint {len(real_constraints) + 1} (empty to finish): ")
                    if not constraint:
                        break
                    real_constraints.append(constraint)

                print("\nSOLUTION FROM FIRST PRINCIPLES:")
                print("What's the minimal solution building from ground up?")
                solution_elements = []
                while True:
                    element = input(f"  Element {len(solution_elements) + 1} (empty to finish): ")
                    if not element:
                        break
                    solution_elements.append(element)

                print("\nFUNCTIONAL REQUIREMENTS:")
                functional_requirements = []
                while True:
                    fr = input(f"  FR-{len(functional_requirements) + 1} (empty to finish): ")
                    if not fr:
                        break
                    acceptance = input("    Acceptance criteria: ")
                    functional_requirements.append({
                        'id': f'FR-{len(functional_requirements)}',
                        'requirement': fr,
                        'acceptance_criteria': acceptance
                    })

                print("\nUSER STORIES:")
                print("Format: As a [role], I want [feature], so that [benefit]")
                user_stories = []
                while True:
                    story = input(f"  Story {len(user_stories) + 1} (empty to finish): ")
                    if not story:
                        break
                    user_stories.append(story)

            # Create PRD file from template
            output_path = args.get('output')
            if output_path:
                output_path = Path(output_path)
            else:
                # Generate filename from title
                safe_title = title.lower().replace(' ', '-').replace('/', '-')
                output_path = config.paths.prds_dir / f"{safe_title}.md"

            # Check if file exists
            if output_path.exists():
                if not args.get('force'):
                    response = input(f"File {output_path} exists. Overwrite? [y/N]: ")
                    if response.lower() != 'y':
                        print("Aborted.")
                        return 1

            # Load template
            template_path = config.paths.templates_dir / "prd_first_principles.md"
            if not template_path.exists():
                # Use default template
                template_path = Path(__file__).parent.parent.parent / "specs" / "prds" / "TEMPLATE.md"

            if not template_path.exists():
                raise CommandError(f"Template not found: {template_path}")

            # Read template
            template_content = template_path.read_text()

            # Replace placeholders
            prd_content = template_content.replace("[Skill/Agent Name]", title)
            prd_content = prd.replace("YYYY-MM-DD", datetime.now().strftime("%Y-%m-%d"))
            prd_content = prd_content.replace("[Your Name]", author)

            # Write PRD file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(prd_content)

            print(f"\n✅ PRD created successfully!")
            print(f"   Location: {output_path}")
            print(f"\nNext steps:")
            print(f"   1. Edit the PRD to add details")
            print(f"   2. Validate with: bb5 prd:validate {output_path.name}")
            print(f"   3. Parse with: bb5 prd:parse {output_path.name}")

            return 0

        except Exception as e:
            logger.exception(f"Error creating PRD: {e}")
            raise CommandError(f"Failed to create PRD: {e}")

    def _prompt_section(self, title: str, prompt: str, multiline: bool = False) -> str:
        """Prompt user for input section."""
        print(f"\n{title}")
        print("-" * 60)
        print(prompt)

        if multiline:
            print("(Enter empty line to finish)")
            lines = []
            while True:
                line = input("> ")
                if not line:
                    break
                lines.append(line)
            return "\n".join(lines)
        else:
            return input("> ")


class PRDParseCommand(BaseCommand):
    """
    Command to parse PRD file and display structure.

    Usage:
        bb5 prd:parse <prd-file> [options]

    Options:
        --format: Output format (text, json, yaml)
        --output: Save parsed data to file
    """

    name = "prd:parse"
    description = "Parse PRD file and display structured data"
    aliases = ["parse-prd"]

    def execute(self, args: dict) -> int:
        """Execute the PRD parse command."""
        try:
            # Load configuration
            config = load_config()

            # Initialize PRD agent
            agent = PRDAgent(config.paths.prds_dir)

            # Get PRD file
            prd_file = args.get('prd_file')
            if not prd_file:
                raise CommandError("PRD file path required")

            prd_path = Path(prd_file)
            if not prd_path.exists():
                # Try in PRDs directory
                prd_path = config.paths.prds_dir / prd_file
                if not prd_path.exists():
                    raise CommandError(f"PRD file not found: {prd_file}")

            print(f"📋 Parsing PRD: {prd_path}")

            # Parse PRD
            prd = agent.load_prd(prd_path.stem)

            # Display parsed data
            format_type = args.get('format', 'text')

            if format_type == 'json':
                import json
                output = json.dumps(prd.__dict__, indent=2, default=str)
            elif format_type == 'yaml':
                import yaml
                output = yaml.dump(prd.__dict__, default_flow_style=False)
            else:
                output = self._format_prd_text(prd)

            # Save to file if requested
            output_file = args.get('output')
            if output_file:
                Path(output_file).write_text(output)
                print(f"\n✅ Parsed data saved to: {output_file}")
            else:
                print(output)

            return 0

        except PRDValidationError as e:
            logger.error(f"Validation error: {e.message}")
            return 1
        except Exception as e:
            logger.exception(f"Error parsing PRD: {e}")
            raise CommandError(f"Failed to parse PRD: {e}")

    def _format_prd_text(self, prd: PRDData) -> str:
        """Format PRD data as readable text."""
        lines = [
            f"{'='*60}",
            f"PRD: {prd.title}",
            f"{'='*60}",
            "",
            f"Status: {prd.status}",
            f"Created: {prd.created}",
            f"Author: {prd.author}",
            f"ID: {prd.prd_id}",
            "",
            f"{'='*60}",
            "FIRST PRINCIPLES ANALYSIS",
            f"{'='*60}",
            "",
            "Problem:",
            f"  {prd.problem.get('what_problem_are_we_trying_to_solve', 'Not defined')}",
            "",
            f"Fundamental Truths: {len(prd.truths.get('fundamental_truths', []))}",
            f"Assumptions: {len(prd.truths.get('assumptions', []))}",
            "",
            f"{'='*60}",
            "REQUIREMENTS",
            f"{'='*60}",
            "",
            f"Functional Requirements: {len(prd.functional_requirements)}",
        ]

        for fr in prd.functional_requirements[:5]:  # Show first 5
            lines.append(f"  - {fr['id']}: {fr['description'][:60]}...")

        if len(prd.functional_requirements) > 5:
            lines.append(f"  ... and {len(prd.functional_requirements) - 5} more")

        lines.extend([
            "",
            f"Non-Functional Requirements: {len(prd.non_functional_requirements)}",
            "",
            f"{'='*60}",
            "USER STORIES & METRICS",
            f"{'='*60}",
            "",
            f"User Stories: {len(prd.user_stories)}",
            "",
            f"Success Metrics:",
            f"  Quantitative: {len(prd.success_metrics.get('quantitative', []))}",
            f"  Qualitative: {len(prd.success_metrics.get('qualitative', []))}",
            "",
            f"{'='*60}",
            "ACCEPTANCE CRITERIA",
            f"{'='*60}",
            "",
            f"Total Criteria: {len(prd.acceptance_criteria)}",
        ])

        for ac in prd.acceptance_criteria[:5]:  # Show first 5
            lines.append(f"  - {ac[:70]}")

        if len(prd.acceptance_criteria) > 5:
            lines.append(f"  ... and {len(prd.acceptance_criteria) - 5} more")

        lines.extend([
            "",
            f"{'='*60}",
            "RISKS",
            f"{'='*60}",
            "",
            f"Total Risks: {len(prd.risks)}",
        ])

        for risk in prd.risks[:3]:  # Show first 3
            lines.append(f"  - [{risk.get('likelihood', 'N/A')}/{risk.get('impact', 'N/A')}] {risk.get('risk', 'Unknown')}")

        if len(prd.risks) > 3:
            lines.append(f"  ... and {len(prd.risks) - 3} more")

        return "\n".join(lines)


class PRDValidateCommand(BaseCommand):
    """
    Command to validate PRD completeness.

    Usage:
        bb5 prd:validate <prd-file> [options]

    Options:
        --strict: Enable strict validation mode
        --fix: Attempt to fix common issues
    """

    name = "prd:validate"
    description = "Validate PRD completeness and quality"
    aliases = ["validate-prd"]

    def execute(self, args: dict) -> int:
        """Execute the PRD validate command."""
        try:
            # Load configuration
            config = load_config()

            # Initialize PRD agent
            agent = PRDAgent(config.paths.prds_dir)

            # Get PRD file
            prd_file = args.get('prd_file')
            if not prd_file:
                raise CommandError("PRD file path required")

            prd_path = Path(prd_file)
            if not prd_path.exists():
                # Try in PRDs directory
                prd_path = config.paths.prds_dir / prd_file
                if not prd_path.exists():
                    raise CommandError(f"PRD file not found: {prd_file}")

            print(f"🔍 Validating PRD: {prd_path}")

            # Validate PRD
            result = agent.validate_prd(prd_path.stem)

            # Display results
            print(f"\n{'='*60}")
            print("VALIDATION RESULTS")
            print(f"{'='*60}\n")

            print(f"Valid: {'✅ YES' if result['valid'] else '❌ NO'}")
            print(f"Completion: {result['completion_percent']:.1f}%")

            if result['errors']:
                print(f"\n❌ ERRORS ({len(result['errors'])}):")
                for error in result['errors']:
                    print(f"  - {error}")

            if result['warnings']:
                print(f"\n⚠️  WARNINGS ({len(result['warnings'])}):")
                for warning in result['warnings']:
                    print(f"  - {warning}")

            if result['valid']:
                print(f"\n✅ PRD is valid and ready for development!")
                return 0
            else:
                print(f"\n❌ PRD has errors that must be fixed before proceeding.")
                return 1

        except PRDValidationError as e:
            logger.error(f"Validation error: {e.message}")
            if e.details:
                print(f"Details: {e.details}")
            return 1
        except Exception as e:
            logger.exception(f"Error validating PRD: {e}")
            raise CommandError(f"Failed to validate PRD: {e}")


class PRDListCommand(BaseCommand):
    """
    Command to list all PRDs.

    Usage:
        bb5 prd:list [options]

    Options:
        --status: Filter by status (Draft, In Review, Approved)
        --format: Output format (text, json, markdown)
    """

    name = "prd:list"
    description = "List all PRDs in the specs directory"
    aliases = ["list-prds"]

    def execute(self, args: dict) -> int:
        """Execute the PRD list command."""
        try:
            # Load configuration
            config = load_config()

            # Initialize PRD agent
            agent = PRDAgent(config.paths.prds_dir)

            # Get status filter
            status_filter = args.get('status')

            print(f"📚 Listing PRDs...")
            if status_filter:
                print(f"   Filter: {status_filter}")

            # List PRDs
            prds = agent.list_prds(status=status_filter)

            if not prds:
                print("\nNo PRDs found.")
                return 0

            # Format output
            format_type = args.get('format', 'text')

            if format_type == 'json':
                import json
                output = json.dumps(prds, indent=2, default=str)
                print(output)
            elif format_type == 'markdown':
                output = self._format_list_markdown(prds)
                print(output)
            else:
                output = self._format_list_text(prds)
                print(output)

            return 0

        except Exception as e:
            logger.exception(f"Error listing PRDs: {e}")
            raise CommandError(f"Failed to list PRDs: {e}")

    def _format_list_text(self, prds: list) -> str:
        """Format PRD list as text."""
        lines = [
            f"\n{'='*60}",
            f"Found {len(prds)} PRD(s)",
            f"{'='*60}\n"
        ]

        for prd in prds:
            lines.append(f"📄 {prd['title']}")
            lines.append(f"   ID: {prd['id']}")
            lines.append(f"   Status: {prd['status']}")
            lines.append(f"   Created: {prd['created']}")
            lines.append("")

        return "\n".join(lines)

    def _format_list_markdown(self, prds: list) -> str:
        """Format PRD list as markdown."""
        lines = [
            f"# PRDs ({len(prds)})\n",
            "| Title | ID | Status | Created |",
            "|-------|-----|--------|---------|"
        ]

        for prd in prds:
            lines.append(
                f"| {prd['title']} | {prd['id']} | {prd['status']} | {prd['created']} |"
            )

        return "\n".join(lines)


# -------------------------------------------------------------------------
# Command Registry
# -------------------------------------------------------------------------

# Map command names to command classes
PRD_COMMANDS = {
    "prd:new": PRDNewCommand,
    "prd:parse": PRDParseCommand,
    "prd:validate": PRDValidateCommand,
    "prd:list": PRDListCommand,
}


def get_command(command_name: str) -> Optional[BaseCommand]:
    """
    Get PRD command instance by name.

    Args:
        command_name: Command name (e.g., "prd:new")

    Returns:
        Command instance or None if not found
    """
    command_class = PRD_COMMANDS.get(command_name)
    if command_class:
        config = load_config()
        return command_class(config)
    return None


def list_commands() -> List[str]:
    """List all available PRD commands."""
    return list(PRD_COMMANDS.keys())


def main():
    """Main entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="BlackBox5 PRD Commands"
    )
    parser.add_argument(
        "command",
        choices=list_commands(),
        help="Command to run"
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Command arguments"
    )

    args, remaining = parser.parse_known_args()

    # Get command
    command = get_command(args.command)
    if not command:
        print(f"❌ Unknown command: {args.command}")
        return 1

    # Run command
    return command.run({'args': remaining})


if __name__ == "__main__":
    sys.exit(main())
