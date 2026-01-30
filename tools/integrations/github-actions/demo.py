#!/usr/bin/env python3
"""
GitHub Actions Integration Demo
===============================

Demonstrates basic usage of the GitHub Actions integration.

Usage:
    python demo.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# Note: This is a synchronous library using requests, not async
# But we'll structure it similarly to the template for consistency
def main():
    """Run demo."""

    # Check for token
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("   Get your token at: https://github.com/settings/tokens")
        print("   Required scopes: repo, workflow")
        return

    # Repository to work with
    owner = os.environ.get("GITHUB_OWNER", input("Enter repository owner: "))
    repo = os.environ.get("GITHUB_REPO", input("Enter repository name: "))

    print("🚀 GitHub Actions Integration Demo")
    print("=" * 50)

    # Import and initialize manager
    from integration.github_actions import GitHubActionsManager

    with GitHubActionsManager(owner=owner, repo=repo) as manager:
        # Check connection
        print("\n1. Checking connection...")
        if manager.check_connection():
            print("   ✅ Connected successfully")
        else:
            print("   ❌ Connection failed")
            return

        # List workflows
        print("\n2. Listing workflows...")
        try:
            workflows = manager.list_workflows()
            print(f"   Found {len(workflows)} workflows:")
            for wf in workflows[:5]:  # Show first 5
                dispatch_status = "✓" if wf.workflow_dispatch else "✗"
                print(f"   - {wf.name} (ID: {wf.id}, dispatch: {dispatch_status})")
        except Exception as e:
            print(f"   ❌ Error listing workflows: {e}")

        # List recent workflow runs
        print("\n3. Listing recent workflow runs...")
        try:
            runs = manager.list_workflow_runs(per_page=5)
            print(f"   Found {len(runs)} recent runs:")
            for run in runs:
                conclusion = run.conclusion or "running"
                print(f"   - {run.name} ({run.run_number}): {conclusion}")
        except Exception as e:
            print(f"   ❌ Error listing runs: {e}")

        # Trigger a workflow (if available)
        print("\n4. Trigger workflow (interactive)...")
        trigger = input("   Do you want to trigger a workflow? (y/N): ").lower()

        if trigger == "y":
            print("\n   Available workflows with workflow_dispatch:")
            dispatch_workflows = [wf for wf in workflows if wf.workflow_dispatch]

            if not dispatch_workflows:
                print("   ⚠️  No workflows with workflow_dispatch found")
            else:
                for i, wf in enumerate(dispatch_workflows, 1):
                    print(f"   {i}. {wf.name} (ID: {wf.id})")

                choice = input("\n   Enter workflow number: ")
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(dispatch_workflows):
                        wf = dispatch_workflows[idx]
                        ref = input(f"   Enter branch (default: main): ") or "main"

                        print(f"\n   Triggering {wf.name} on {ref}...")
                        success = manager.trigger_workflow(wf.id, ref)

                        if success:
                            print("   ✅ Workflow triggered successfully")

                            # Option to wait for completion
                            wait = input("\n   Wait for completion? (y/N): ").lower()
                            if wait == "y":
                                print("\n   Waiting for run to complete...")
                                try:
                                    # Get the latest run
                                    runs = manager.list_workflow_runs(
                                        branch=ref, per_page=1
                                    )
                                    if runs:
                                        latest_run = runs[0]
                                        completed = manager.wait_for_deployment(
                                            latest_run.id, timeout=300
                                        )
                                        print(
                                            f"   ✅ Run completed: {completed.conclusion}"
                                        )

                                        # Option to download logs
                                        download = input(
                                            "\n   Download logs? (y/N): "
                                        ).lower()
                                        if download == "y":
                                            log_path = manager.download_logs(
                                                latest_run.id, output_path="./logs"
                                            )
                                            print(f"   ✅ Logs downloaded to {log_path}")
                                except TimeoutError:
                                    print("   ⏱️  Timeout waiting for completion")
                                except Exception as e:
                                    print(f"   ❌ Error: {e}")
                        else:
                            print("   ❌ Failed to trigger workflow")
                    else:
                        print("   ❌ Invalid choice")
                except ValueError:
                    print("   ❌ Invalid input")
        else:
            print("   Skipping workflow trigger")

        # List artifacts from recent runs
        print("\n5. Listing artifacts...")
        try:
            if runs:
                latest_run = runs[0]
                artifacts = manager.list_artifacts(run_id=latest_run.id)
                if artifacts:
                    print(f"   Found {len(artifacts)} artifacts:")
                    for art in artifacts:
                        size_mb = art.size_in_bytes / (1024 * 1024)
                        print(f"   - {art.name} ({size_mb:.2f} MB)")
                else:
                    print("   ℹ️  No artifacts found for latest run")
            else:
                print("   ℹ️  No runs found")
        except Exception as e:
            print(f"   ❌ Error listing artifacts: {e}")

        # Show rate limit info
        print("\n6. Rate limit status...")
        rate_limit = manager.get_rate_limit()
        if rate_limit:
            print(f"   Remaining: {rate_limit.remaining}/{rate_limit.limit}")
            print(f"   Used: {rate_limit.used}")
            print(f"   Resets at: {rate_limit.reset_at}")
        else:
            print("   ℹ️  No rate limit info available")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
