"""
Epic CLI Commands

Provides command-line interface for Epic management:
- bb5 epic:create - Create epic from PRD
- bb5 epic:validate - Validate epic
- bb5 epic:list - List all epics
"""

import sys
from pathlib import Path
from typing import Optional

from ..spec_driven import EpicAgent, EpicStatus


class EpicCreateCommand:
    """Create a new Epic from a PRD."""

    name = "epic:create"
    help = "Create a technical Epic from a PRD"

    def __init__(self, specs_root: Optional[Path] = None):
        """
        Initialize command.

        Args:
            specs_root: Root directory for spec files
        """
        self.specs_root = specs_root

    def execute(self, prd_id: str, title: Optional[str] = None, output: Optional[str] = None) -> int:
        """
        Execute the command.

        Args:
            prd_id: PRD identifier
            title: Optional epic title
            output: Optional output file path

        Returns:
            Exit code (0 = success, 1 = failure)
        """
        try:
            agent = EpicAgent(specs_root=self.specs_root)

            output_path = Path(output) if output else None
            epic = agent.create_epic(prd_id, title=title, output_path=output_path)

            print(f"\n{'='*60}")
            print(f"Epic Created Successfully!")
            print(f"{'='*60}")
            print(f"ID:          {epic.epic_id}")
            print(f"Title:       {epic.title}")
            print(f"Status:      {epic.status}")
            print(f"From PRD:    {prd_id}")
            print(f"Components:  {len(epic.components)}")
            print(f"Phases:      {len(epic.phases)}")
            print(f"Decisions:   {len(epic.technical_decisions)}")
            print(f"{'='*60}\n")

            return 0

        except Exception as e:
            print(f"Error creating epic: {e}", file=sys.stderr)
            return 1


class EpicValidateCommand:
    """Validate an Epic."""

    name = "epic:validate"
    help = "Validate an Epic for completeness and quality"

    def __init__(self, specs_root: Optional[Path] = None):
        """
        Initialize command.

        Args:
            specs_root: Root directory for spec files
        """
        self.specs_root = specs_root

    def execute(self, epic_id: str, verbose: bool = False) -> int:
        """
        Execute the command.

        Args:
            epic_id: Epic identifier
            verbose: Show detailed validation output

        Returns:
            Exit code (0 = valid, 1 = invalid)
        """
        try:
            agent = EpicAgent(specs_root=self.specs_root)
            result = agent.validate_epic(epic_id)

            print(f"\n{'='*60}")
            print(f"Epic Validation: {epic_id}")
            print(f"{'='*60}")
            print(f"Status:      {'✅ VALID' if result['valid'] else '❌ INVALID'}")
            print(f"Complete:    {result['completion_percent']:.0f}%")
            print(f"\nErrors ({len(result['errors'])}):")
            for error in result['errors']:
                print(f"  ❌ {error}")

            print(f"\nWarnings ({len(result['warnings'])}):")
            for warning in result['warnings']:
                print(f"  ⚠️  {warning}")

            if verbose and result['errors']:
                print(f"\nDetailed Error Information:")
                for error in result['errors']:
                    print(f"  - {error}")

            print(f"{'='*60}\n")

            return 0 if result['valid'] else 1

        except Exception as e:
            print(f"Error validating epic: {e}", file=sys.stderr)
            return 1


class EpicListCommand:
    """List all Epics."""

    name = "epic:list"
    help = "List all Epics with optional filtering"

    def __init__(self, specs_root: Optional[Path] = None):
        """
        Initialize command.

        Args:
            specs_root: Root directory for spec files
        """
        self.specs_root = specs_root

    def execute(self, status: Optional[str] = None) -> int:
        """
        Execute the command.

        Args:
            status: Optional status filter (draft, in_review, approved, in_progress, done)

        Returns:
            Exit code (0 = success)
        """
        try:
            agent = EpicAgent(specs_root=self.specs_root)
            epics = agent.list_epics(status=status)

            print(f"\n{'='*80}")
            print(f"Epics")
            if status:
                print(f"Status Filter: {status}")
            print(f"{'='*80}")

            if not epics:
                print("No epics found.")
                return 0

            # Header
            print(f"{'ID':<20} {'Title':<30} {'Status':<15} {'PRD':<15} {'Created':<12}")
            print("-" * 80)

            # Rows
            for epic in epics:
                print(f"{epic['id']:<20} {epic['title'][:30]:<30} {epic['status']:<15} "
                      f"{epic['prd_id']:<15} {epic['created']:<12}")

            print(f"{'='*80}")
            print(f"Total: {len(epics)} epic(s)\n")

            return 0

        except Exception as e:
            print(f"Error listing epics: {e}", file=sys.stderr)
            return 1


class EpicShowCommand:
    """Show details of an Epic."""

    name = "epic:show"
    help = "Show detailed information about an Epic"

    def __init__(self, specs_root: Optional[Path] = None):
        """
        Initialize command.

        Args:
            specs_root: Root directory for spec files
        """
        self.specs_root = specs_root

    def execute(self, epic_id: str) -> int:
        """
        Execute the command.

        Args:
            epic_id: Epic identifier

        Returns:
            Exit code (0 = success, 1 = failure)
        """
        try:
            agent = EpicAgent(specs_root=self.specs_root)
            summary = agent.get_epic_summary(epic_id)

            print(f"\n{'='*60}")
            print(f"Epic: {summary['title']}")
            print(f"{'='*60}")
            print(f"ID:              {summary['id']}")
            print(f"Status:          {summary['status']}")
            print(f"PRD:             {summary['prd_id']}")
            print(f"PRD Title:       {summary['prd_title']}")
            print(f"Created:         {summary['created']}")
            print(f"Updated:         {summary['updated']}")
            print(f"\nComponents:      {summary['components_count']}")
            print(f"Phases:          {summary['phases_count']}")
            print(f"Decisions:       {summary['decisions_count']}")
            print(f"Risks:           {summary['risks_count']}")
            print(f"Open Questions:  {summary['open_questions_count']}")
            print(f"{'='*60}\n")

            return 0

        except Exception as e:
            print(f"Error showing epic: {e}", file=sys.stderr)
            return 1


def main_create():
    """Entry point for epic:create command."""
    import argparse

    parser = argparse.ArgumentParser(description="Create an Epic from a PRD")
    parser.add_argument("prd_id", help="PRD identifier (e.g., PRD-001)")
    parser.add_argument("--title", help="Epic title (optional)")
    parser.add_argument("--output", "-o", help="Output file path (optional)")

    args = parser.parse_args()

    cmd = EpicCreateCommand()
    return cmd.execute(args.prd_id, title=args.title, output=args.output)


def main_validate():
    """Entry point for epic:validate command."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate an Epic")
    parser.add_argument("epic_id", help="Epic identifier (e.g., EPIC-001)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    cmd = EpicValidateCommand()
    return cmd.execute(args.epic_id, verbose=args.verbose)


def main_list():
    """Entry point for epic:list command."""
    import argparse

    parser = argparse.ArgumentParser(description="List all Epics")
    parser.add_argument("--status", "-s", help="Filter by status", choices=[
        "draft", "in_review", "approved", "in_progress", "done"
    ])

    args = parser.parse_args()

    cmd = EpicListCommand()
    return cmd.execute(status=args.status)


def main_show():
    """Entry point for epic:show command."""
    import argparse

    parser = argparse.ArgumentParser(description="Show Epic details")
    parser.add_argument("epic_id", help="Epic identifier (e.g., EPIC-001)")

    args = parser.parse_args()

    cmd = EpicShowCommand()
    return cmd.execute(args.epic_id)


if __name__ == "__main__":
    sys.exit(main_create(sys.argv[1:]))
