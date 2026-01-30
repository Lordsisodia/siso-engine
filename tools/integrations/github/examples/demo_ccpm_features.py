#!/usr/bin/env python3
"""
Demonstration of CCPM-Style GitHub Integration Features
=========================================================

This script demonstrates the enhanced CCPM-style features including:
- Structured progress comments
- Sub-issue creation
- Epic linking
- Bulk issue creation
- Incremental sync

Usage:
    python3 demo_ccpm_features.py
"""

import asyncio
import sys
from pathlib import Path

# Add engine directory to path
engine_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(engine_dir))

from integrations.github import (
    GitHubIssuesIntegration,
    TaskOutcome,
    TaskSpec,
)
from integrations.github.sync.ccpm_sync import TaskProgress
from integrations.github.sync.comment_formatter import (
    FormatProgressComment,
    FormatCompletionComment,
    FormatIssueBody,
)


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def print_example(title: str, content: str) -> None:
    """Print an example with syntax highlighting."""
    print(f"\n### {title}")
    print("-" * 70)
    print(content)
    print("-" * 70)


# -------------------------------------------------------------------------
# Example 1: Structured Progress Comments
# -------------------------------------------------------------------------


def example_progress_comment():
    """Demonstrate structured progress comment formatting."""
    print_section("Example 1: Structured Progress Comments")

    formatter = FormatProgressComment()

    comment = formatter.format(
        completed=[
            "Implemented user authentication with OAuth2",
            "Added Google and GitHub providers",
            "Created login page UI",
        ],
        in_progress=[
            "Testing session persistence",
            "Adding logout functionality",
        ],
        technical_notes=[
            "Using NextAuth.js for authentication",
            "Sessions stored in Redis for performance",
            "JWT tokens for stateless authentication",
            "OAuth2 state parameter to prevent CSRF",
        ],
        acceptance_criteria={
            "User can login with Google": "completed",
            "User can login with GitHub": "completed",
            "Session is persisted across page reloads": "in-progress",
            "Logout functionality works correctly": "pending",
        },
        commits=[
            {
                "sha": "a1b2c3d4e5f6",
                "message": "feat: add OAuth2 authentication flow",
            },
            {
                "sha": "b2c3d4e5f6a7",
                "message": "feat: add Google OAuth2 provider",
            },
            {
                "sha": "c3d4e5f6a7b8",
                "message": "feat: add GitHub OAuth2 provider",
            },
        ],
        next_steps=[
            "Complete session persistence testing",
            "Implement logout with session cleanup",
            "Write unit tests for auth module",
            "Add integration tests for OAuth flow",
        ],
        blockers=[
            "Waiting for environment variables from DevOps",
        ],
        completion=65,
    )

    print_example("Progress Comment", comment)


# -------------------------------------------------------------------------
# Example 2: Completion Comments
# -------------------------------------------------------------------------


def example_completion_comment():
    """Demonstrate completion comment formatting."""
    print_section("Example 2: Completion Comments")

    formatter = FormatCompletionComment()

    comment = formatter.format(
        success=True,
        deliverables=[
            "User authentication system with OAuth2",
            "Google and GitHub OAuth2 providers",
            "Session management with Redis",
            "Login and logout functionality",
            "Comprehensive unit and integration tests",
            "API documentation",
        ],
        patterns=[
            "NextAuth.js provides excellent OAuth2 abstraction",
            "Redis session storage improves performance significantly",
            "JWT tokens enable stateless authentication",
            "OAuth2 state parameter is critical for security",
        ],
        gotchas=[
            "Never store OAuth tokens in plaintext - always encrypt",
            "Session timeout must be shorter than token expiry",
            "Handle OAuth errors gracefully with user-friendly messages",
            "Test OAuth flow in both development and production environments",
            "Environment variables must be set before deployment",
        ],
        unit_test_status="passed",
        integration_test_status="passed",
        manual_test_status="passed",
        documentation_status="complete",
        duration="3 days",
    )

    print_example("Completion Comment", comment)


# -------------------------------------------------------------------------
# Example 3: Issue Body Formatting
# -------------------------------------------------------------------------


def example_issue_body():
    """Demonstrate issue body formatting."""
    print_section("Example 3: Issue Body Formatting")

    formatter = FormatIssueBody()

    body = formatter.format(
        title="Implement User Authentication System",
        description=(
            "Add comprehensive user authentication system supporting OAuth2 "
            "with multiple providers (Google, GitHub). System should include "
            "session management, secure token handling, and graceful error handling."
        ),
        acceptance_criteria=[
            "User can authenticate with Google OAuth2",
            "User can authenticate with GitHub OAuth2",
            "Sessions are persisted across page reloads",
            "Sessions expire after configurable timeout",
            "Logout functionality clears sessions properly",
            "OAuth2 errors are handled gracefully",
            "Authentication state is accessible throughout app",
            "Unauthenticated users are redirected to login",
        ],
        epic_link="#123 (Epic: User Management System)",
        spec_link="https://docs.example.com/specs/auth-system",
        related_issues=[
            "#124 (User Profile Management)",
            "#125 (Authorization & Permissions)",
        ],
        labels=["type:feature", "priority:high", "complexity:medium"],
        assignees=["@frontend-team", "@backend-team"],
    )

    print_example("Issue Body", body)


# -------------------------------------------------------------------------
# Example 4: Incremental Sync
# -------------------------------------------------------------------------


async def example_incremental_sync():
    """Demonstrate incremental sync functionality."""
    print_section("Example 4: Incremental Sync")

    print("""
The incremental sync system prevents duplicate comments by tracking updates:

1. First sync: Creates progress comment
2. Second sync (no changes): Skips (returns False)
3. After local changes: Creates new progress comment

This keeps GitHub issues clean while maintaining full progress history.
    """)

    print("### Sync Flow")
    print("-" * 70)
    print("""
# Initial state
progress = TaskProgress(
    completed=["Initial setup"],
    completion=20,
)

# First sync: Posts comment to GitHub
sync.update_task_progress(123, progress)
synced = await integration.sync_progress(123)
# Result: True (comment posted)

# Second sync (no changes): Skips
synced = await integration.sync_progress(123)
# Result: False (no new content, skipped)

# Update local progress
progress.completed.append("Added feature X")
progress.completion = 50
sync.update_task_progress(123, progress)

# Third sync: Posts new comment
synced = await integration.sync_progress(123)
# Result: True (new comment posted)
    """)
    print("-" * 70)


# -------------------------------------------------------------------------
# Example 5: Sub-Issue Creation
# -------------------------------------------------------------------------


async def example_sub_issue_creation():
    """Demonstrate sub-issue creation."""
    print_section("Example 5: Sub-Issue Creation")

    print("""
Sub-issues allow you to create hierarchical task structures:

    # Parent issue
    parent_spec = TaskSpec(
        title="Implement User Authentication",
        description="Complete authentication system",
        labels=["type:feature", "priority:high"],
    )
    parent = await integration.create_task(parent_spec)

    # Create sub-issue
    sub_issue = await provider.create_sub_issue(
        parent_issue_number=parent.number,
        title="Add OAuth2 Login",
        description="Implement OAuth2 with Google and GitHub",
        labels=["type:feature"],
    )

This creates:
1. A sub-issue linked to the parent
2. A comment on the parent linking to the sub-issue
3. Parent reference in the sub-issue body
    """)


# -------------------------------------------------------------------------
# Example 6: Epic Linking
# -------------------------------------------------------------------------


async def example_epic_linking():
    """Demonstrate epic linking."""
    print_section("Example 6: Epic Linking")

    print("""
Epic linking allows you to organize related issues:

    # Create epic
    epic_spec = TaskSpec(
        title="Epic: User Management System",
        description="Complete user management",
        labels=["type:epic"],
    )
    epic = await integration.create_task(epic_spec)

    # Create and link task
    task_spec = TaskSpec(
        title="Add user authentication",
        description="Implement login",
    )
    task = await integration.create_task(task_spec)

    # Link to epic
    await provider.link_epic(
        issue_number=task.number,
        epic_number=epic.number,
        epic_title=epic.title,
    )

This creates bidirectional links between epic and task.
    """)


# -------------------------------------------------------------------------
# Example 7: Bulk Issue Creation
# -------------------------------------------------------------------------


async def example_bulk_creation():
    """Demonstrate bulk issue creation."""
    print_section("Example 7: Bulk Issue Creation")

    print("""
Bulk creation allows you to create multiple issues at once:

    issues = [
        {
            "title": "Add unit tests for auth",
            "body": "Write comprehensive unit tests",
            "labels": ["type:test"],
        },
        {
            "title": "Add integration tests",
            "body": "Test end-to-end authentication",
            "labels": ["type:test"],
        },
        {
            "title": "Document authentication API",
            "body": "Write API documentation",
            "labels": ["type:docs"],
        },
    ]

    created = await provider.bulk_create_issues(issues)
    print(f"Created {len(created)} issues")

This is useful for breaking down large tasks into smaller issues.
    """)


# -------------------------------------------------------------------------
# Example 8: Epic with Subtasks
# -------------------------------------------------------------------------


async def example_epic_with_subtasks():
    """Demonstrate epic with subtasks creation."""
    print_section("Example 8: Epic with Subtasks")

    print("""
Create an epic with multiple subtasks in one call:

    result = await provider.create_epic_with_subtasks(
        epic_title="Epic: User Authentication",
        epic_description="Implement complete authentication system",
        epic_labels=["type:epic", "priority:high"],
        subtasks=[
            {
                "title": "Add OAuth2 login",
                "body": "Implement OAuth2 with Google and GitHub",
                "labels": ["type:feature"],
            },
            {
                "title": "Add session management",
                "body": "Implement session persistence",
                "labels": ["type:feature"],
            },
            {
                "title": "Add logout functionality",
                "body": "Implement logout with cleanup",
                "labels": ["type:feature"],
            },
        ],
    )

    epic = result["epic_issue"]
    subtasks = result["sub_issues"]

This creates:
1. An epic issue
2. Multiple sub-issues linked to the epic
3. Bidirectional links between epic and sub-issues
    """)


# -------------------------------------------------------------------------
# Main Demo
# -------------------------------------------------------------------------


async def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  CCPM-Style GitHub Integration - Feature Demonstration")
    print("=" * 70)

    # Synchronous examples
    example_progress_comment()
    example_completion_comment()
    example_issue_body()

    # Asynchronous examples
    await example_incremental_sync()
    await example_sub_issue_creation()
    await example_epic_linking()
    await example_bulk_creation()
    await example_epic_with_subtasks()

    # Summary
    print_section("Summary")
    print("""
The enhanced CCPM-style GitHub integration provides:

✅ Structured Comments
   - Progress updates with clear sections
   - Completion summaries with outcomes
   - Formatted issue bodies with context

✅ Sub-Issue Support
   - Create hierarchical task structures
   - Automatic linking between parent and child
   - Bidirectional references

✅ Epic Linking
   - Organize related issues
   - Bidirectional epic links
   - Clear task hierarchy

✅ Bulk Operations
   - Create multiple issues at once
   - Create epic with subtasks in one call
   - Efficient batch processing

✅ Incremental Sync
   - Prevent duplicate comments
   - Track local changes
   - Only sync when content changes

✅ Repository Protection
   - Prevent writes to template repos
   - Safety checks built-in
   - Clear error messages

For more details, see:
- CCPM-ENHANCEMENTS.md
- tests/test_ccpm_sync.py
- examples/basic_usage.py
    """)

    print("\n" + "=" * 70)
    print("  End of Demonstration")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
