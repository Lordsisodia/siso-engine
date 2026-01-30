"""
Redis coordination layer for autonomous agent system.

Provides event-driven coordination with sub-millisecond latency.
"""

from .coordinator import RedisCoordinator, RedisConfig, RedisLatencyTest

__all__ = ['RedisCoordinator', 'RedisConfig', 'RedisLatencyTest']
