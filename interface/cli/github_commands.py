#!/usr/bin/env python3
"""
GitHub Commands for BlackBox5 CLI
==================================

Command layer for GitHub sync operations.

Provides CLI commands for:
- `bb5 github:sync-epic` - Sync epic from PRD file
- `bb5 github:sync-task` - Sync single task file
- `bb5 github:status` - Check GitHub sync status
- `bb5 github:update` - Update issue progress

Based on BlackBox5 Week 2, Workstream 2C requirements.
"""

import os
import sys
import logging
from typing import Optional, List
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from integrations.github.github_sync_manager import (
    GitHubSyncManager,
    create_sync_manager_from_env
)
from integration.github.GitHubManager import GitHubManager

logger = logging.getLogger(__name__)


class GitHubSyncEpicCommand:
    """
    Command to sync epic from PRD file to GitHub.

    Usage:
        bb5 github:sync-epic <prd-file> [options]

    Options:
        --dry-run: Parse without creating issues
        --no-tasks: Create epic without tasks
        --token: GitHub token (overrides env var)
        --repo: Repository (overrides auto-detect)
    """

    name = "github:sync-epic"
    description = "Sync epic from PRD file to GitHub issues"

    def __init__(self):
        self.sync_manager = None

    def run(self, args: List[str]) -> int:
        """
        Execute the sync epic command.

        Args:
            args: Command line arguments

        Returns:
            Exit code (0 = success, 1 = failure)
        """
        import argparse

        parser = argparse.ArgumentParser(
            description=self.description,
            usage="bb5 github:sync-epic <prd-file> [options]"
        )
        parser.add_argument(
            "prd_file",
            help="Path to PRD file"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse file without creating issues"
        )
        parser.add_argument(
            "--no-tasks",
            action="store_true",
            help="Create epic without task sub-issues"
        )
        parser.add_argument(
            "--token",
            help="GitHub token (overrides GITHUB_TOKEN env var)"
        )
        parser.add_argument(
            "--repo",
            help="Repository (owner/repo)"
        )

        try:
            parsed_args = parser.parse_args(args)
        except SystemExit as e:
            return e.code

        # Validate PRD file
        prd_file = parsed_args.prd_file
        if not Path(prd_file).exists():
            print(f"❌ PRD file not found: {prd_file}")
            return 1

        # Initialize sync manager
        try:
            self.sync_manager = GitHubSyncManager(
                token=parsed_args.token,
                repo=parsed_args.repo
            )
        except Exception as e:
            print(f"❌ Failed to initialize GitHub sync: {e}")
            return 1

        # Sync epic
        print(f"📋 Syncing epic from: {prd_file}")

        result = self.sync_manager.sync_epic(
            prd_file=prd_file,
            create_tasks=not parsed_args.no_tasks,
            dry_run=parsed_args.dry_run
        )

        # Display results
        return self._display_results(result, parsed_args.dry_run)

    def _display_results(self, result, dry_run: bool) -> int:
        """Display sync results."""
        if dry_run:
            print("✅ Dry run completed - no issues created")
            return 0

        if result.success:
            print(f"✅ Epic synced successfully!")
            print(f"   Epic: #{result.epic_issue.number}")
            print(f"   URL: {result.epic_issue.html_url}")
            print(f"   Tasks: {len(result.task_issues)}")

            if result.task_issues:
                print("\n   Tasks created:")
                for task in result.task_issues:
                    print(f"     - #{task.number}: {task.title}")

            return 0
        else:
            print("❌ Failed to sync epic")
            for error in result.errors:
                print(f"   Error: {error}")
            return 1


class GitHubSyncTaskCommand:
    """
    Command to sync single task file to GitHub.

    Usage:
        bb5 github:sync-task <task-file> [options]

    Options:
        --epic-number: Parent epic issue number
        --dry-run: Parse without creating issues
        --token: GitHub token (overrides env var)
        --repo: Repository (overrides auto-detect)
    """

    name = "github:sync-task"
    description = "Sync single task file to GitHub issue"

    def __init__(self):
        self.sync_manager = None

    def run(self, args: List[str]) -> int:
        """Execute the sync task command."""
        import argparse

        parser = argparse.ArgumentParser(
            description=self.description,
            usage="bb5 github:sync-task <task-file> [options]"
        )
        parser.add_argument(
            "task_file",
            help="Path to task file"
        )
        parser.add_argument(
            "--epic-number",
            type=int,
            help="Parent epic issue number"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse file without creating issues"
        )
        parser.add_argument(
            "--token",
            help="GitHub token (overrides GITHUB_TOKEN env var)"
        )
        parser.add_argument(
            "--repo",
            help="Repository (owner/repo)"
        )

        try:
            parsed_args = parser.parse_args(args)
        except SystemExit as e:
            return e.code

        # Validate task file
        task_file = parsed_args.task_file
        if not Path(task_file).exists():
            print(f"❌ Task file not found: {task_file}")
            return 1

        # Initialize sync manager
        try:
            self.sync_manager = GitHubSyncManager(
                token=parsed_args.token,
                repo=parsed_args.repo
            )
        except Exception as e:
            print(f"❌ Failed to initialize GitHub sync: {e}")
            return 1

        # Sync task
        print(f"📝 Syncing task from: {task_file}")

        if parsed_args.epic_number:
            print(f"   Linking to epic: #{parsed_args.epic_number}")

        issue = self.sync_manager.sync_task(
            task_file=task_file,
            epic_number=parsed_args.epic_number,
            dry_run=parsed_args.dry_run
        )

        # Display results
        if parsed_args.dry_run:
            print("✅ Dry run completed - no issue created")
            return 0

        if issue:
            print(f"✅ Task synced successfully!")
            print(f"   Issue: #{issue.number}")
            print(f"   URL: {issue.html_url}")
            return 0
        else:
            print("❌ Failed to sync task")
            return 1


class GitHubStatusCommand:
    """
    Command to check GitHub sync status.

    Usage:
        bb5 github:status [issue-number]

    Displays:
    - Repository information
    - Issue details (if number provided)
    - Linked tasks (if epic)
    - Recent activity
    """

    name = "github:status"
    description = "Check GitHub sync status"

    def __init__(self):
        self.github_manager = None

    def run(self, args: List[str]) -> int:
        """Execute the status command."""
        import argparse

        parser = argparse.ArgumentParser(
            description=self.description,
            usage="bb5 github:status [issue-number] [options]"
        )
        parser.add_argument(
            "issue_number",
            nargs="?",
            type=int,
            help="Issue number to check"
        )
        parser.add_argument(
            "--token",
            help="GitHub token (overrides GITHUB_TOKEN env var)"
        )
        parser.add_argument(
            "--repo",
            help="Repository (owner/repo)"
        )

        try:
            parsed_args = parser.parse_args(args)
        except SystemExit as e:
            return e.code

        # Initialize GitHub manager
        try:
            self.github_manager = GitHubManager(
                token=parsed_args.token,
                repo=parsed_args.repo
            )
        except Exception as e:
            print(f"❌ Failed to initialize GitHub: {e}")
            return 1

        # Display status
        return self._display_status(parsed_args.issue_number)

    def _display_status(self, issue_number: Optional[int]) -> int:
        """Display status information."""
        print(f"📊 GitHub Sync Status")
        print(f"   Repository: {self.github_manager.repo}")
        print(f"   Safe Mode: {'✅' if self.github_manager.check_repository_safe() else '❌'}")

        if issue_number:
            print(f"\n📋 Issue #{issue_number}")

            try:
                issue = self.github_manager.get_issue(issue_number)

                print(f"   Title: {issue.title}")
                print(f"   State: {issue.state}")
                print(f"   URL: {issue.html_url}")
                print(f"   Labels: {', '.join(issue.labels)}")

                # Check if epic
                if "epic" in issue.labels:
                    print(f"\n   📦 This is an epic issue")
                    # Could fetch linked tasks here

            except Exception as e:
                print(f"❌ Failed to fetch issue: {e}")
                return 1

        return 0


class GitHubUpdateCommand:
    """
    Command to update issue progress.

    Usage:
        bb5 github:update <issue-number> [options]

    Options:
        --progress: Progress message
        --status: Status label
        --close: Close epic (requires --summary)
        --summary: Completion summary (for closing)
    """

    name = "github:update"
    description = "Update GitHub issue progress"

    def __init__(self):
        self.sync_manager = None

    def run(self, args: List[str]) -> int:
        """Execute the update command."""
        import argparse

        parser = argparse.ArgumentParser(
            description=self.description,
            usage="bb5 github:update <issue-number> [options]"
        )
        parser.add_argument(
            "issue_number",
            type=int,
            help="Issue number to update"
        )
        parser.add_argument(
            "--progress",
            help="Progress message"
        )
        parser.add_argument(
            "--status",
            help="Status label (e.g., 'in-progress', 'blocked')"
        )
        parser.add_argument(
            "--close",
            action="store_true",
            help="Close the issue"
        )
        parser.add_argument(
            "--summary",
            help="Completion summary (required with --close)"
        )
        parser.add_argument(
            "--token",
            help="GitHub token (overrides GITHUB_TOKEN env var)"
        )
        parser.add_argument(
            "--repo",
            help="Repository (owner/repo)"
        )

        try:
            parsed_args = parser.parse_args(args)
        except SystemExit as e:
            return e.code

        # Initialize sync manager
        try:
            self.sync_manager = GitHubSyncManager(
                token=parsed_args.token,
                repo=parsed_args.repo
            )
        except Exception as e:
            print(f"❌ Failed to initialize GitHub sync: {e}")
            return 1

        # Handle close operation
        if parsed_args.close:
            if not parsed_args.summary:
                print("❌ --summary required with --close")
                return 1

            print(f"🎉 Closing epic #{parsed_args.issue_number}")

            success = self.sync_manager.close_epic(
                epic_number=parsed_args.issue_number,
                completion_summary=parsed_args.summary
            )

            if success:
                print("✅ Epic closed successfully")
                return 0
            else:
                print("❌ Failed to close epic")
                return 1

        # Handle progress update
        if parsed_args.progress:
            print(f"📝 Updating issue #{parsed_args.issue_number}")

            success = self.sync_manager.update_progress(
                issue_number=parsed_args.issue_number,
                progress=parsed_args.progress,
                status=parsed_args.status
            )

            if success:
                print("✅ Progress updated successfully")
                return 0
            else:
                print("❌ Failed to update progress")
                return 1

        print("❌ No action specified. Use --progress or --close")
        return 1


# -------------------------------------------------------------------------
# Command Registry
# -------------------------------------------------------------------------

# Map command names to command classes
GITHUB_COMMANDS = {
    "github:sync-epic": GitHubSyncEpicCommand,
    "github:sync-task": GitHubSyncTaskCommand,
    "github:status": GitHubStatusCommand,
    "github:update": GitHubUpdateCommand,
}


def get_command(command_name: str):
    """
    Get command instance by name.

    Args:
        command_name: Command name (e.g., "github:sync-epic")

    Returns:
        Command instance or None if not found
    """
    command_class = GITHUB_COMMANDS.get(command_name)
    if command_class:
        return command_class()
    return None


def list_commands() -> List[str]:
    """List all available GitHub commands."""
    return list(GITHUB_COMMANDS.keys())


def main():
    """Main entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="BlackBox5 GitHub Commands"
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
    return command.run(remaining)


if __name__ == "__main__":
    sys.exit(main())
