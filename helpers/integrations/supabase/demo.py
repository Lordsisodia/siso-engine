#!/usr/bin/env python3
"""
Supabase Integration Demo
==========================

Demonstrates basic usage of the Supabase integration.

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

from integration.supabase import SupabaseManager
from integration.supabase.config import SupabaseConfig


async def main():
    """Run demo."""

    # Check for credentials
    project_ref = os.environ.get("SUPABASE_PROJECT_REF")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not project_ref or not service_role_key:
        print("❌ Error: Supabase credentials not set")
        print("   Set SUPABASE_PROJECT_REF and SUPABASE_SERVICE_ROLE_KEY env vars")
        print("   Get these from: https://supabase.com/dashboard/project/_/settings/api")
        return

    print("🚀 Supabase Integration Demo")
    print("=" * 50)

    # Initialize manager
    config = SupabaseConfig(
        project_ref=project_ref,
        service_role_key=service_role_key,
    )

    async with SupabaseManager(config) as manager:
        # Check connection
        print("\n1. Checking connection...")
        if await manager.check_connection():
            print("   ✅ Connected successfully")
        else:
            print("   ❌ Connection failed")
            return

        # Example 1: Query a table
        print("\n2. Querying a table...")
        try:
            # Replace 'users' with your actual table name
            users = await manager.query(
                "users",
                columns=["id", "email", "created_at"],
                limit=5,
            )
            print(f"   Found {len(users)} users")
            for user in users:
                print(f"   - {user.get('email', 'N/A')}")
        except Exception as e:
            print(f"   ⚠️  Query failed (table may not exist): {e}")

        # Example 2: Insert data
        print("\n3. Inserting data...")
        try:
            # Replace with your actual table name and data
            result = await manager.insert(
                "demo_table",
                {
                    "name": "BlackBox5 Demo",
                    "status": "active",
                    "metadata": {"source": "integration_demo"},
                },
            )
            print(f"   ✅ Inserted record: {result.data[0].get('id')}")
        except Exception as e:
            print(f"   ⚠️  Insert failed (table may not exist): {e}")

        # Example 3: Upload file to storage
        print("\n4. Uploading file to storage...")
        try:
            content = b"Hello from BlackBox5 Supabase Integration!"
            result = await manager.upload_file(
                bucket="demo-bucket",
                path="test/hello.txt",
                content=content,
                content_type="text/plain",
                upsert=True,
            )
            print(f"   ✅ Uploaded file")

            # Get public URL
            url = await manager.get_public_url("demo-bucket", "test/hello.txt")
            print(f"   Public URL: {url}")
        except Exception as e:
            print(f"   ⚠️  Upload failed (bucket may not exist): {e}")

        # Example 4: Invoke Edge Function
        print("\n5. Invoking Edge Function...")
        try:
            result = await manager.invoke_function(
                name="hello-world",
                body={"name": "BlackBox5"},
            )
            if result.error:
                print(f"   ⚠️  Function error: {result.error}")
            else:
                print(f"   ✅ Function result: {result.data}")
        except Exception as e:
            print(f"   ⚠️  Function invocation failed (function may not exist): {e}")

        # Example 5: Query with filters
        print("\n6. Querying with filters...")
        try:
            results = await manager.query(
                "users",
                filters={
                    "status": "active",
                    "created_at": {"gte": "2024-01-01"},
                },
                limit=3,
            )
            print(f"   Found {len(results)} active users created since 2024")
        except Exception as e:
            print(f"   ⚠️  Filtered query failed: {e}")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
