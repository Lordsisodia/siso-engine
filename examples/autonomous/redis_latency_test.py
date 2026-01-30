#!/usr/bin/env python3
"""
Redis latency test for autonomous agent coordination.

Tests the actual latency of Redis pub/sub in your environment.
Run this to verify Redis performance before deploying the system.
"""

import sys
from pathlib import Path

# Add core/autonomous to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "2-engine" / "core" / "autonomous"))

from redis.coordinator import RedisLatencyTest


def main():
    """Run Redis latency tests"""
    print("=" * 60)
    print("Redis Latency Test")
    print("=" * 60)
    print()
    print("Testing Redis pub/sub latency...")
    print("This will take a few seconds...")
    print()

    try:
        results = RedisLatencyTest.test_latency(
            host="localhost",
            port=6379,
            iterations=100
        )

        print("Results:")
        print("-" * 60)
        print(f"  Min:     {results['min_ms']:.3f} ms")
        print(f"  Max:     {results['max_ms']:.3f} ms")
        print(f"  Average: {results['avg_ms']:.3f} ms")
        print(f"  P50:     {results['p50_ms']:.3f} ms")
        print(f"  P99:     {results['p99_ms']:.3f} ms")
        print()

        # Evaluate results
        avg = results['avg_ms']

        if avg < 1:
            print("  ✓ Excellent! Sub-millisecond latency.")
            print("    Your Redis setup is ideal for autonomous agents.")
        elif avg < 10:
            print("  ✓ Good! Latency is under 10ms.")
            print("    Your Redis setup will work well for autonomous agents.")
        elif avg < 50:
            print("  ⚠ Acceptable. Latency is under 50ms.")
            print("    Redis performance is adequate but could be improved.")
        else:
            print("  ✗ High latency detected.")
            print("    Consider optimizing your Redis setup.")

        print()
        print("Comparison:")
        print("-" * 60)
        print(f"  Redis pub/sub:     {avg:.3f} ms")
        print(f"  File watching:     ~100 ms")
        print(f"  Polling (10s):     ~10000 ms")
        print()
        print(f"Speedup vs polling:  {10000/avg:.0f}x faster")
        print()

    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Make sure Redis is running:")
        print("  brew services start redis")
        print()
        print("Or install Redis:")
        print("  brew install redis")


if __name__ == "__main__":
    main()
