#!/usr/bin/env python3
"""
Vercel Integration Demo
========================

Demonstrates basic usage of the Vercel integration.

Usage:
    python demo.py
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from integration.vercel import VercelManager


async def main():
    """Run demo."""

    # Check for token
    token = os.environ.get("VERCEL_TOKEN")
    if not token:
        print("❌ Error: VERCEL_TOKEN environment variable not set")
        print("   Get your token at: https://vercel.com/account/tokens")
        return

    print("🚀 Vercel Integration Demo")
    print("=" * 50)

    # Initialize manager
    async with VercelManager() as manager:
        # Check connection
        print("\n1. Checking connection...")
        if await manager.check_connection():
            print("   ✅ Connected successfully")
        else:
            print("   ❌ Connection failed")
            return

        # List projects
        print("\n2. Listing projects...")
        projects = await manager.list_projects(limit=5)
        print(f"   Found {len(projects)} projects")
        for project in projects[:3]:
            print(f"   - {project.get('name', 'Unknown')} ({project.get('id', 'No ID')})")

        if not projects:
            print("\n   No projects found. Create a project first.")
            print("   Visit: https://vercel.com/new")
            return

        # Get first project ID
        project_id = projects[0].get("id")
        project_name = projects[0].get("name", "unknown")

        print(f"\n3. Using project: {project_name}")

        # List deployments
        print("\n4. Listing recent deployments...")
        deployments = await manager.list_deployments(project_id=project_id, limit=5)
        print(f"   Found {len(deployments)} deployments")
        for deployment in deployments[:3]:
            status = deployment.ready_state
            url = deployment.url or "No URL"
            print(f"   - {deployment.id[:8]}... [{status}] {url}")

        # Example: Create a deployment (commented out - requires git repo)
        print("\n5. Deployment creation example (skipped):")
        print("   To create a deployment, use:")
        print("   >>> deployment = await manager.create_deployment(")
        print("   ...     project_name='my-app',")
        print("   ...     git_repo='https://github.com/user/repo',")
        print("   ...     ref='main'")
        print("   ... )")
        print("   >>> await manager.wait_for_deployment(deployment.id)")

        # Environment variables example
        print("\n6. Environment variables...")
        env_vars = await manager.get_env_variables(project_id)
        print(f"   Found {len(env_vars)} environment variables")
        for env in env_vars[:3]:
            key = env.get("key", "Unknown")
            print(f"   - {key}")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
