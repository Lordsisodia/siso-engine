#!/usr/bin/env python3
"""
SERVICE_NAME Integration Demo
==============================

Demonstrates basic usage of the SERVICE_NAME integration.

TODO: Replace SERVICE_NAME with actual service name.

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

from manager import TemplateManager


async def main():
    """Run demo."""

    # Check for token
    # TODO: Replace SERVICE_NAME_TOKEN with actual env var name
    token = os.environ.get("SERVICE_NAME_TOKEN")
    if not token:
        print("❌ Error: SERVICE_NAME_TOKEN environment variable not set")
        print("   Get your token at: https://example.com")
        return

    print("🚀 SERVICE_NAME Integration Demo")
    print("=" * 50)

    # Initialize manager
    async with TemplateManager() as manager:
        # Check connection
        print("\n1. Checking connection...")
        if await manager.check_connection():
            print("   ✅ Connected successfully")
        else:
            print("   ❌ Connection failed")
            return

        # Example operation 1
        print("\n2. Performing operation...")
        result = await manager.some_operation(param1="value")
        print(f"   Result: {result}")

        # Example operation 2
        print("\n3. Listing entities...")
        entities = await manager.list_entities(limit=5)
        print(f"   Found {len(entities)} entities")
        for entity in entities:
            print(f"   - {entity.name} ({entity.status})")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
