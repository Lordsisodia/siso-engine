#!/usr/bin/env python3
"""
Tests for Cloudflare integration.

Run with:
    python test_integration.py
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))

from integration.cloudflare import CloudflareManager
from integration.cloudflare.types import (
    DNSRecordSpec,
    DNSRecordType,
)


async def test_connection():
    """Test API connection."""
    print("\n" + "=" * 50)
    print("TEST: Connection Check")
    print("=" * 50)

    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not token:
        print("SKIP: CLOUDFLARE_API_TOKEN not set")
        return

    manager = CloudflareManager(token=token)

    try:
        result = await manager.check_connection()
        if result:
            print("PASS: Connection successful")
        else:
            print("FAIL: Connection failed")
    finally:
        await manager.close()


async def test_list_zones():
    """Test listing zones."""
    print("\n" + "=" * 50)
    print("TEST: List Zones")
    print("=" * 50)

    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not token:
        print("SKIP: CLOUDFLARE_API_TOKEN not set")
        return

    manager = CloudflareManager(token=token)

    try:
        zones = await manager.list_zones()
        print(f"PASS: Found {len(zones)} zones")
        for zone in zones[:3]:
            print(f"  - {zone['name']}")
    except Exception as e:
        print(f"FAIL: {e}")
    finally:
        await manager.close()


async def test_dns_operations():
    """Test DNS operations."""
    print("\n" + "=" * 50)
    print("TEST: DNS Operations")
    print("=" * 50)

    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")

    if not token:
        print("SKIP: CLOUDFLARE_API_TOKEN not set")
        return

    if not zone_id:
        print("SKIP: CLOUDFLARE_ZONE_ID not set")
        return

    manager = CloudflareManager(token=token)

    try:
        # List records
        print("Listing DNS records...")
        records = await manager.dns_list_records(zone_id, limit=5)
        print(f"PASS: Found {len(records)} records")

        # Create a test record (will be cleaned up)
        test_name = f"test-blackbox5-{datetime.now().timestamp()}.example.com"
        spec = DNSRecordSpec(
            type=DNSRecordType.A,
            name=test_name,
            content="192.0.2.1",  # TEST-NET-1 IP
            ttl=1,
            proxied=False,  # Disable proxy for test
        )

        print(f"\nCreating test record: {test_name}")
        record = await manager.dns_create_record(zone_id, spec)
        if record:
            print(f"PASS: Created record {record.id}")

            # Update record
            print("\nUpdating test record...")
            spec.content = "192.0.2.2"
            updated = await manager.dns_update_record(zone_id, record.id, spec)
            if updated and updated.content == "192.0.2.2":
                print(f"PASS: Updated record to {updated.content}")

            # Delete record
            print("\nDeleting test record...")
            deleted = await manager.dns_delete_record(zone_id, record.id)
            if deleted:
                print("PASS: Deleted test record")
        else:
            print("FAIL: Could not create test record")

    except Exception as e:
        print(f"FAIL: {e}")
    finally:
        await manager.close()


async def test_workers_operations():
    """Test Workers operations."""
    print("\n" + "=" * 50)
    print("TEST: Workers Operations")
    print("=" * 50)

    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")

    if not token:
        print("SKIP: CLOUDFLARE_API_TOKEN not set")
        return

    if not account_id:
        print("SKIP: CLOUDFLARE_ACCOUNT_ID not set")
        return

    manager = CloudflareManager(token=token, account_id=account_id)

    try:
        # List workers
        print("Listing Workers...")
        workers = await manager.workers_list()
        print(f"PASS: Found {len(workers)} workers")

        # Deploy test worker
        test_script_name = f"test-worker-{datetime.now().timestamp()}"
        test_script = '''
export default {
  async fetch(request) {
    return new Response("Hello from BlackBox5 test!");
  }
}
'''

        print(f"\nDeploying test worker: {test_script_name}")
        result = await manager.workers_deploy(test_script_name, test_script)
        if result.success:
            print(f"PASS: Deployed worker {test_script_name}")

            # Delete test worker
            print("\nDeleting test worker...")
            deleted = await manager.workers_delete(test_script_name)
            if deleted:
                print("PASS: Deleted test worker")
        else:
            print(f"FAIL: Worker deployment failed: {result.errors}")

    except Exception as e:
        print(f"FAIL: {e}")
    finally:
        await manager.close()


async def main():
    """Run all tests."""
    print("\n" + "=" * 50)
    print("Cloudflare Integration Tests")
    print("=" * 50)

    await test_connection()
    await test_list_zones()
    await test_dns_operations()
    await test_workers_operations()

    print("\n" + "=" * 50)
    print("All tests complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
