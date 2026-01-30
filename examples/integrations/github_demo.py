#!/usr/bin/env python3
"""
GitHub Manager Demo
===================

Demonstrates the GitHub integration system adapted from CCPM.

This script shows how to use GitHubManager to:
- Create issues with labels
- Add progress comments
- Create pull requests
- Update issue status

Usage:
    # Set your GitHub credentials
    export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
    export GITHUB_REPO="owner/repo"

    # Run demo
    python .blackbox5/integration/github/demo.py
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from integration.github.GitHubManager import GitHubManager, create_manager_from_env


def demo_create_issue(manager: GitHubManager):
    """Demonstrate issue creation."""
    print("\n" + "="*60)
    print("DEMO 1: Creating an Issue")
    print("="*60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    title = f"Demo Issue: Test GitHub Integration {timestamp}"
    body = """# Demo Issue

## Purpose
This is a demonstration issue created by BlackBox5's GitHubManager.

## Description
Testing the GitHub integration system adapted from CCPM's GitHub sync patterns.

## Acceptance Criteria
- [ ] Issue created successfully
- [ ] Labels applied correctly
- [ ] Comment added
- [ ] Status updated

## Technical Details
- Created by: GitHubManager
- Pattern: CCPM-style issue creation
- Integration: Python requests library
"""

    print(f"Creating issue: {title}")
    issue = manager.create_issue(
        title=title,
        body=body,
        labels=["demo", "automated", "blackbox5"]
    )

    print(f"✅ Created issue #{issue.number}")
    print(f"   URL: {issue.html_url}")
    print(f"   State: {issue.state}")
    print(f"   Labels: {', '.join(issue.labels)}")

    return issue


def demo_add_comment(manager: GitHubManager, issue_number: int):
    """Demonstrate adding comments (CCPM progress pattern)."""
    print("\n" + "="*60)
    print("DEMO 2: Adding Progress Comment (CCPM Pattern)")
    print("="*60)

    comment = f"""## 🔄 Progress Update - {datetime.now().isoformat()}

### ✅ Completed Work
- Created demonstration issue
- Applied labels for categorization
- Verified GitHub API integration

### 🔄 In Progress
- Adding progress update comment
- Testing issue status updates

### 📝 Technical Notes
- Using Python requests library for HTTP calls
- Token-based authentication (PAT)
- Following CCPM patterns for consistency

### 📊 Acceptance Criteria Status
- ✅ Issue created successfully
- ✅ Labels applied correctly
- 🔄 Comment being added
- □ Status update pending

### 🚀 Next Steps
- Update issue status
- Test pull request creation
- Verify all operations

---
*Progress: 75% | Synced from BlackBox5 GitHubManager demo at {datetime.now().isoformat()}*
"""

    print(f"Adding comment to issue #{issue_number}")
    response = manager.add_comment(issue_number, comment)
    print(f"✅ Comment added (ID: {response.get('id', 'N/A')})")


def demo_update_status(manager: GitHubManager, issue_number: int):
    """Demonstrate status updates."""
    print("\n" + "="*60)
    print("DEMO 3: Updating Issue Status")
    print("="*60)

    print(f"Updating issue #{issue_number} to 'closed'")
    updated = manager.update_status(issue_number, "closed")
    print(f"✅ Issue status updated: {updated.state}")


def demo_epic_task_pattern(manager: GitHubManager):
    """Demonstrate CCPM epic/task pattern."""
    print("\n" + "="*60)
    print("DEMO 4: CCPM Epic/Task Pattern")
    print("="*60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    epic_name = f"demo-feature-{timestamp}"

    # Create epic
    epic_body = f"""# Epic: Demo Feature {timestamp}

## Overview
A demonstration epic showing CCPM-style issue organization in BlackBox5.

## Key Decisions
- Use GitHub Issues as source of truth
- Follow CCPM patterns for consistency
- Maintain audit trail via comments

## Components
1. Issue creation
2. Progress tracking
3. Status updates
4. Label management

## Stats
Total tasks: 3
Parallel tasks: 2 (can be worked on simultaneously)
Sequential tasks: 1 (has dependencies)
Estimated total effort: 2 hours
"""

    print(f"Creating epic: {epic_body.split(chr(10))[0]}")
    epic = manager.create_issue(
        title=f"Epic: Demo Feature {timestamp}",
        body=epic_body,
        labels=["epic", f"epic:{epic_name}", "feature"]
    )

    print(f"✅ Created epic #{epic.number}")

    # Create sub-tasks
    tasks = [
        {
            "title": f"Task: Implement core functionality {timestamp}",
            "body": "# Task: Implement Core\n\n## Specification\nImplement the core demo functionality.\n\n## Acceptance Criteria\n- [x] Functionality works\n- [x] Tests pass",
            "labels": ["task", f"epic:{epic_name}", "implementation"]
        },
        {
            "title": f"Task: Add tests {timestamp}",
            "body": "# Task: Add Tests\n\n## Specification\nAdd comprehensive tests.\n\n## Acceptance Criteria\n- [x] Unit tests\n- [x] Integration tests",
            "labels": ["task", f"epic:{epic_name}", "testing"]
        },
        {
            "title": f"Task: Update documentation {timestamp}",
            "body": "# Task: Update Docs\n\n## Specification\nUpdate all documentation.\n\n## Acceptance Criteria\n- [x] README updated\n- [x] API docs complete",
            "labels": ["task", f"epic:{epic_name}", "documentation"]
        }
    ]

    task_numbers = []
    for task_spec in tasks:
        task = manager.create_issue(**task_spec)
        task_numbers.append(task.number)
        print(f"✅ Created task #{task.number}: {task.title}")

    # Link tasks to epic
    epic_comment = f"## Tasks Created\n\n"
    for i, task_num in enumerate(task_numbers, 1):
        epic_comment += f"{i}. [ ] #{task_num}\n"

    epic_comment += f"\n**Total:** {len(task_numbers)} tasks\n"
    epic_comment += f"**Parallel:** 2 tasks\n"
    epic_comment += f"**Sequential:** 1 task\n"

    manager.add_comment(epic.number, epic_comment)
    print(f"✅ Linked {len(task_numbers)} tasks to epic #{epic.number}")

    # Close demo issues
    print("\nCleaning up demo issues...")
    for task_num in task_numbers:
        manager.update_status(task_num, "closed")
    manager.update_status(epic.number, "closed")
    print("✅ All demo issues closed")


def main():
    """Run all demonstrations."""
    print("\n" + "="*60)
    print("BlackBox5 GitHub Integration Demo")
    print("="*60)
    print("\nThis demo showcases the GitHub integration adapted from CCPM.")
    print("It will create, update, and close issues on your repository.")

    # Check environment
    if not os.environ.get("GITHUB_TOKEN"):
        print("\n❌ Error: GITHUB_TOKEN environment variable not set")
        print("\nTo run this demo:")
        print("1. Create a GitHub Personal Access Token at:")
        print("   https://github.com/settings/tokens")
        print("2. Export your token:")
        print("   export GITHUB_TOKEN='ghp_xxxxxxxxxxxx'")
        print("3. Set your test repository:")
        print("   export GITHUB_REPO='owner/repo'")
        print("4. Run this script again")
        return 1

    if not os.environ.get("GITHUB_REPO"):
        print("\n⚠️  Warning: GITHUB_REPO not set")
        print("Attempting to auto-detect from git config...")

    try:
        # Create manager
        print("\nInitializing GitHubManager...")
        manager = create_manager_from_env()
        print(f"✅ Connected to repository: {manager.repo}")

        # Check repository safety
        if not manager.check_repository_safe():
            print("\n⚠️  Warning: Repository may not be safe for modifications")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("Demo cancelled.")
                return 0

        # Run demos
        print("\n📋 Starting demonstrations...")

        # Demo 1-3: Basic issue workflow
        issue = demo_create_issue(manager)
        demo_add_comment(manager, issue.number)
        demo_update_status(manager, issue.number)

        # Demo 4: CCPM epic/task pattern
        print("\n⚠️  Demo 4 will create multiple issues. Continue? (y/N): ")
        if input().lower() == 'y':
            demo_epic_task_pattern(manager)

        print("\n" + "="*60)
        print("Demo Complete!")
        print("="*60)
        print("\n✅ All demonstrations completed successfully")
        print("\nCheck your GitHub repository to see the created issues:")
        print(f"   https://github.com/{manager.repo}/issues")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
