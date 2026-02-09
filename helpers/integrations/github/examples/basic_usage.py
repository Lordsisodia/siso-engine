#!/usr/bin/env python3
"""
Basic Usage Example for GitHub Issues Integration
=================================================

This example shows how to use the GitHub Issues integration
for everyday task management.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from integrations.github import (
    GitHubIssuesIntegration,
    TaskOutcome,
    TaskSpec,
)


async def example_1_create_task():
    """Example 1: Create a new task."""
    print("\n=== Example 1: Create a Task ===\n")

    # Initialize integration
    integration = GitHubIssuesIntegration()

    # Define your task
    spec = TaskSpec(
        title="Add user authentication",
        description="Implement OAuth2 login with GitHub",
        acceptance_criteria=[
            "User can login with GitHub account",
            "User session is persisted in secure storage",
            "Logout functionality works correctly",
        ],
        labels=["type:feature", "priority:high"],
        # assignees=["username"],  # Optional
    )

    # Create the task
    issue = await integration.create_task(spec)

    print(f"✅ Created issue #{issue.number}")
    print(f"   URL: {issue.url}")
    print(f"   Local context: memory/working/tasks/{issue.number}/")


async def example_2_sync_progress():
    """Example 2: Sync progress updates."""
    print("\n=== Example 2: Sync Progress ===\n")

    integration = GitHubIssuesIntegration()

    # Assume task_id is the issue number from Example 1
    task_id = 123  # Replace with actual issue number

    # Update local progress file
    # Edit: memory/working/tasks/123/progress.md
    # Then sync to GitHub
    synced = await integration.sync_progress(task_id)

    if synced:
        print(f"✅ Progress synced to issue #{task_id}")
    else:
        print(f"ℹ️  No new updates to sync for issue #{task_id}")


async def example_3_complete_task():
    """Example 3: Complete a task."""
    print("\n=== Example 3: Complete a Task ===\n")

    integration = GitHubIssuesIntegration()

    task_id = 123  # Replace with actual issue number

    # Define outcome with learnings
    outcome = TaskOutcome(
        success=True,
        # Patterns discovered (good practices)
        patterns=[
            "Use OAuth2 for authentication",
            "Store tokens in secure HttpOnly cookies",
            "Implement session refresh tokens",
        ],
        # Gotchas (pitfalls to avoid)
        gotchas=[
            "Never store tokens in localStorage",
            "Don't log sensitive authentication data",
            "Always validate tokens server-side",
        ],
        # What was delivered
        deliverables=[
            "OAuth login component",
            "Session management system",
            "Logout functionality",
        ],
        # Testing status
        unit_test_status="passing",
        integration_test_status="passing",
        manual_test_status="passed",
        # Documentation status
        documentation_status="complete",
    )

    # Complete the task
    await integration.complete_task(task_id, outcome)

    print(f"✅ Task #{task_id} completed")
    print("   - Completion comment posted to GitHub")
    print("   - Patterns and gotchas stored in brain")
    print("   - Issue closed")


async def example_4_list_tasks():
    """Example 4: List and filter tasks."""
    print("\n=== Example 4: List Tasks ===\n")

    from integrations.github import IssueState

    integration = GitHubIssuesIntegration()

    # List all open issues
    open_issues = await integration.list_issues(state=IssueState.OPEN)

    print(f"Found {len(open_issues)} open issues:")
    for issue in open_issues[:5]:  # Show first 5
        labels_str = ", ".join(issue.labels[:3])  # Show first 3 labels
        print(f"  #{issue.number}: {issue.title}")
        print(f"    Labels: {labels_str}")
        print(f"    Status: {issue.state.value}")

    # Filter by labels
    print("\n--- High Priority Features ---")
    high_priority_features = await integration.list_issues(
        state=IssueState.OPEN,
        labels=["priority:high", "type:feature"],
    )

    for issue in high_priority_features[:3]:
        print(f"  #{issue.number}: {issue.title}")


async def example_5_full_workflow():
    """Example 5: Complete workflow from start to finish."""
    print("\n=== Example 5: Full Workflow ===\n")

    integration = GitHubIssuesIntegration()

    # Step 1: Create task
    print("\n📝 Creating task...")
    spec = TaskSpec(
        title="Implement rate limiting",
        description="Add rate limiting to API endpoints",
        acceptance_criteria=[
            "API endpoints have rate limiting",
            "Rate limit headers are returned",
            "Rate limit errors are handled gracefully",
        ],
        labels=["type:feature", "priority:medium"],
    )

    issue = await integration.create_task(spec)
    print(f"✅ Created issue #{issue.number}")

    # Simulate some work...

    # Step 2: Sync progress (in-progress)
    print("\n🔄 Syncing progress...")
    from integrations.github.sync.ccpm_sync import TaskProgress

    progress = TaskProgress(
        completed=["API rate limiting implemented", "Headers added"],
        in_progress=["Error handling in progress"],
        technical_notes=["Using Redis for rate limit storage"],
        acceptance_criteria={
            "API endpoints have rate limiting": "completed",
            "Rate limit headers are returned": "completed",
            "Rate limit errors are handled gracefully": "in-progress",
        },
        completion=66,
    )

    integration.sync.update_task_progress(issue.number, progress)
    await integration.sync_progress(issue.number)
    print(f"✅ Progress synced to issue #{issue.number}")

    # Simulate more work...

    # Step 3: Complete task
    print("\n✅ Completing task...")
    outcome = TaskOutcome(
        success=True,
        patterns=["Redis-based rate limiting is efficient"],
        gotchas=["Rate limit headers must be on ALL responses"],
        deliverables=["Rate limiting middleware", "Error handlers"],
        unit_test_status="passing",
        integration_test_status="passing",
        manual_test_status="passed",
        documentation_status="complete",
    )

    await integration.complete_task(issue.number, outcome)
    print(f"✅ Issue #{issue.number} completed")


async def main():
    """Run examples."""
    print("\n🚀 GitHub Issues Integration - Usage Examples")
    print("=" * 60)

    print("\nChoose an example to run:")
    print("1. Create a task")
    print("2. Sync progress")
    print("3. Complete a task")
    print("4. List and filter tasks")
    print("5. Full workflow (demo)")
    print("0. Exit")

    while True:
        choice = input("\nEnter choice (0-5): ").strip()

        if choice == "0":
            print("\n👋 Goodbye!")
            break
        elif choice == "1":
            await example_1_create_task()
        elif choice == "2":
            await example_2_sync_progress()
        elif choice == "3":
            await example_3_complete_task()
        elif choice == "4":
            await example_4_list_tasks()
        elif choice == "5":
            confirm = input("This will create a real issue. Continue? (y/N): ").strip().lower()
            if confirm == 'y':
                await example_5_full_workflow()
            else:
                print("Cancelled.")
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
