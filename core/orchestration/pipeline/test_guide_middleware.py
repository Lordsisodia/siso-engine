#!/usr/bin/env python3
"""
Test script for Guide Middleware.

This demonstrates the "inverted intelligence" pattern where the system
is smart and proactive, while the agent can remain simple.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import get_guide_middleware, offer_guidance_before, offer_guidance_after, execute_guide


async def test_before_action():
    """Test guidance before agent action."""
    print("\n=== Test 1: Before Agent Action ===")

    # Simulate agent about to write a Python file
    context = {
        "file_path": "test_agent.py",
        "file_name": "test_agent.py",
        "agent_name": "test-agent"
    }

    suggestion = await offer_guidance_before("file_written", context)

    if suggestion:
        print(f"✓ System suggests: {suggestion['suggestion']}")
        print(f"  Guide: {suggestion['guide']}")
        print(f"  Confidence: {suggestion['confidence']}")
        print(f"  Time: {suggestion['estimated_time']}")
        print(f"  Difficulty: {suggestion['difficulty']}")
    else:
        print("✓ No suggestion (low confidence or disabled)")


async def test_after_action():
    """Test guidance after agent action."""
    print("\n=== Test 2: After Agent Action ===")

    # Simulate agent completing an action
    context = {
        "agent_name": "test-agent",
        "action": "write_file",
        "file_path": "app.py"
    }

    suggestions = await offer_guidance_after("agent_complete", context)

    if suggestions:
        print(f"✓ System found {len(suggestions)} follow-up suggestions:")
        for i, sugg in enumerate(suggestions, 1):
            print(f"  {i}. {sugg['suggestion']} (confidence: {sugg['confidence']})")
    else:
        print("✓ No follow-up suggestions")


async def test_guide_execution():
    """Test executing a guide."""
    print("\n=== Test 3: Guide Execution ===")

    # Simulate agent accepting a suggestion
    context = {
        "file_path": "test.py",
        "file_name": "test.py"
    }

    print("Executing guide: test_python_code")
    result = await execute_guide("test_python_code", context)

    if result.get("status") == "success":
        print("✓ Guide executed successfully")
        print(f"  Summary: {result['summary']}")
    else:
        print(f"✗ Guide execution failed: {result.get('error', 'Unknown error')}")


async def test_statistics():
    """Test statistics tracking."""
    print("\n=== Test 4: Statistics ===")

    middleware = get_guide_middleware()
    stats = middleware.get_statistics()

    print("Middleware Statistics:")
    print(f"  Enabled: {stats['enabled']}")
    print(f"  Suggestions Offered: {stats['suggestions_offered']}")
    print(f"  Suggestions Accepted: {stats['suggestions_accepted']}")
    print(f"  Guides Executed: {stats['guides_executed']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Acceptance Rate: {stats['acceptance_rate']:.1%}")


async def test_discovery():
    """Test guide discovery features."""
    print("\n=== Test 5: Guide Discovery ===")

    middleware = get_guide_middleware()

    # List all guides
    guides = middleware.list_available_guides()
    print(f"✓ Available guides: {len(guides)}")
    for guide in guides:
        print(f"  - {guide['name']}: {guide['description']}")

    # List categories
    categories = middleware.list_categories()
    print(f"\n✓ Categories: {', '.join(categories)}")

    # Search
    results = middleware.search_guides("test")
    print(f"\n✓ Search for 'test': {len(results)} results")
    for result in results[:3]:
        print(f"  - {result['guide']}: {result['description'][:60]}...")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Guide Middleware Test Suite")
    print("=" * 60)

    try:
        await test_before_action()
        await test_after_action()
        # Skip guide execution test as it requires actual files
        # await test_guide_execution()
        await test_statistics()
        await test_discovery()

        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
