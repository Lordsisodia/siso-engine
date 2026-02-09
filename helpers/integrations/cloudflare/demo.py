#!/usr/bin/env python3
"""
Cloudflare Integration Demo
============================

Demonstrates basic usage of the Cloudflare integration.

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

from integration.cloudflare import CloudflareManager
from integration.cloudflare.types import (
    DNSRecordSpec,
    DNSRecordType,
    KVOperation,
    R2UploadSpec,
)


async def main():
    """Run demo."""

    # Check for token and account_id
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")

    if not token:
        print("❌ Error: CLOUDFLARE_API_TOKEN environment variable not set")
        print("   Get your token at: https://dash.cloudflare.com/profile/api-tokens")
        return

    print("🚀 Cloudflare Integration Demo")
    print("=" * 50)

    # Initialize manager
    async with CloudflareManager(token=token, account_id=account_id) as manager:
        # Check connection
        print("\n1. Checking connection...")
        if await manager.check_connection():
            print("   ✅ Connected successfully")
        else:
            print("   ❌ Connection failed")
            return

        # List zones
        print("\n2. Listing zones...")
        zones = await manager.list_zones()
        print(f"   Found {len(zones)} zones")
        for zone in zones[:3]:
            print(f"   - {zone['name']} ({zone['id']})")

        # DNS operations (if zone_id provided)
        if zone_id:
            print("\n3. Listing DNS records...")
            records = await manager.dns_list_records(zone_id, limit=5)
            print(f"   Found {len(records)} records")
            for record in records[:3]:
                print(f"   - {record.name} ({record.type.value}): {record.content}")

            # Example: Create DNS record (commented out to avoid changes)
            # print("\n4. Creating DNS record...")
            # spec = DNSRecordSpec(
            #     type=DNSRecordType.A,
            #     name="demo.example.com",
            #     content="1.2.3.4",
            #     ttl=1,
            #     proxied=True,
            # )
            # record = await manager.dns_create_record(zone_id, spec)
            # if record:
            #     print(f"   ✅ Created record: {record.id}")
        else:
            print("\n3. DNS operations skipped (set CLOUDFLARE_ZONE_ID to enable)")
            print("   To get zone ID, visit your zone dashboard in Cloudflare")

        # Workers operations (if account_id provided)
        if account_id:
            print("\n4. Listing Workers...")
            try:
                workers = await manager.workers_list()
                print(f"   Found {len(workers)} workers")
                for worker in workers[:3]:
                    print(f"   - {worker.name}")
            except Exception as e:
                print(f"   ⚠️ Could not list workers: {e}")

            # Example: Deploy Worker (commented out to avoid changes)
            # print("\n5. Deploying Worker...")
            # worker_script = '''
            # export default {
            #   async fetch(request) {
            #     return new Response("Hello from BlackBox5!");
            #   }
            # }
            # '''
            # result = await manager.workers_deploy("demo-worker", worker_script)
            # if result.success:
            #     print(f"   ✅ Deployed worker: {result.script_name}")
            # else:
            #     print(f"   ❌ Worker deployment failed: {result.errors}")
        else:
            print("\n4. Workers operations skipped (set CLOUDFLARE_ACCOUNT_ID to enable)")

        # KV operations (if account_id and namespace_id provided)
        namespace_id = os.environ.get("CLOUDFLARE_KV_NAMESPACE_ID")
        if account_id and namespace_id:
            print("\n5. Writing to KV store...")
            try:
                await manager.kv_write(namespace_id, "demo_key", "demo_value")
                print("   ✅ Wrote to KV store")

                print("\n6. Reading from KV store...")
                value = await manager.kv_read(namespace_id, "demo_key")
                if value:
                    print(f"   ✅ Read value: {value}")
            except Exception as e:
                print(f"   ⚠️ KV operations failed: {e}")
        else:
            print("\n5. KV operations skipped (set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_KV_NAMESPACE_ID to enable)")

        # R2 operations (if account_id and R2 credentials provided)
        r2_access_key = os.environ.get("R2_ACCESS_KEY_ID")
        if account_id and r2_access_key:
            print("\n6. Uploading to R2...")
            try:
                content = b"Hello from BlackBox5 R2!"
                obj = await manager.r2_upload(
                    bucket_name="demo-bucket",
                    key="demo-file.txt",
                    content=content,
                    content_type="text/plain",
                )
                print(f"   ✅ Uploaded to R2: {obj.key}")
            except Exception as e:
                print(f"   ⚠️ R2 upload failed: {e}")
        else:
            print("\n6. R2 operations skipped (requires R2 credentials)")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
