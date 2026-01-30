#!/usr/bin/env python3
"""
Basic demonstration of the autonomous agent system.

This example shows:
1. Supervisor creating tasks from a goal
2. Autonomous agents claiming and executing tasks
3. Interface agent providing status reports
"""

import sys
import os
import time
from pathlib import Path

# Add core/autonomous to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "2-engine" / "core" / "autonomous"))

from schemas.task import TaskRegistry
from stores.sqlite_store import SQLiteTaskStore
from redis.coordinator import RedisCoordinator, RedisConfig
from agents import SupervisorAgent, AutonomousAgent, InterfaceAgent


class AutonomousAgentPool:
    """Pool of autonomous agents for demonstration"""

    def __init__(self, registry, redis):
        self.registry = registry
        self.redis = redis
        self.agents = []

    def add_agent(self, agent_id, capabilities, execution_fn):
        """Add an agent to the pool"""
        agent = AutonomousAgent(
            agent_id=agent_id,
            capabilities=capabilities,
            task_registry=self.registry,
            redis_coordinator=self.redis,
            execution_fn=execution_fn
        )
        self.agents.append(agent)

    def start_all(self):
        """Start all agents"""
        for agent in self.agents:
            agent.start()

    def stop_all(self):
        """Stop all agents"""
        for agent in self.agents:
            agent.stop()


def mock_task_execution(task):
    """
    Mock task execution for demonstration.

    In production, this would be actual task execution logic.
    """
    print(f"  → Executing: {task.title}")

    # Simulate work
    time.sleep(1)

    return {
        "status": "success",
        "message": f"Completed {task.title}",
        "artifacts": []
    }


def main():
    """Run the autonomous system demonstration"""
    print("=" * 60)
    print("Autonomous Agent System - Basic Demo")
    print("=" * 60)
    print()

    # Initialize components
    print("Initializing system...")

    # Task registry with SQLite backend
    registry = TaskRegistry(backend="sqlite")

    # Redis coordinator
    try:
        redis_config = RedisConfig(host="localhost", port=6379)
        redis = RedisCoordinator(redis_config)
        print("  ✓ Redis connected")
    except Exception as e:
        print(f"  ✗ Redis connection failed: {e}")
        print("  Ensure Redis is running: brew services start redis")
        return

    # Create agents
    supervisor = SupervisorAgent(registry, redis)
    interface = InterfaceAgent(registry, redis)

    # Create autonomous agents with different capabilities
    pool = AutonomousAgentPool(registry, redis)
    pool.add_agent("dev-1", ["development", "frontend"], mock_task_execution)
    pool.add_agent("dev-2", ["development", "backend"], mock_task_execution)
    pool.add_agent("tester-1", ["testing"], mock_task_execution)

    print("  ✓ Agents created")
    print()

    # Start autonomous agents
    print("Starting autonomous agents...")
    pool.start_all()
    print("  ✓ All agents started")
    print()

    # Submit a goal to the supervisor
    goal = "Build user authentication system"
    print(f"Submitting goal: {goal}")
    print()

    supervisor.execute_goal(goal)

    # Wait for tasks to be claimed and executed
    print("Waiting for execution...")
    time.sleep(5)

    # Show status
    print()
    print(interface.format_status_report())
    print()

    # Create a manual task
    print("Creating manual task...")
    task_id = interface.create_task(
        title="Write documentation",
        description="Document the authentication system",
        type="development",
        priority=7
    )
    print(f"  ✓ Created task: {task_id}")
    print()

    # Wait for execution
    time.sleep(3)

    # Final status
    print()
    print("=" * 60)
    print("Final Status:")
    print("=" * 60)
    print(interface.format_status_report())
    print()

    # Show recent activity
    print("Recent Activity:")
    print("-" * 60)
    for activity in interface.get_recent_activity():
        print(f"  {activity}")
    print()

    # Shutdown
    print("Shutting down...")
    pool.stop_all()
    supervisor.shutdown()
    redis.close()

    print("  ✓ Shutdown complete")
    print()
    print("Demo complete!")


if __name__ == "__main__":
    main()
