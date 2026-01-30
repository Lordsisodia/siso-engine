#!/usr/bin/env python3
"""
Test script for Managerial Agent System

This script tests all components of the managerial agent system.
"""

import sys
import os

# Add path
sys.path.insert(0, '~/.blackbox5/2-engine/01-core')

from agents.managerial import (
    VibeKanbanManager,
    TaskStatus,
    Priority,
    get_lifecycle_manager,
    TaskPlan,
    get_dashboard,
    get_management_memory,
    EventType
)


def test_vibe_kanban_manager():
    """Test Vibe Kanban Manager"""
    print("=" * 80)
    print("Testing VibeKanbanManager")
    print("=" * 80)

    manager = VibeKanbanManager()

    # List tasks
    tasks = manager.list_tasks()
    print(f"✓ Listed {len(tasks)} tasks")

    # Get metrics
    metrics = manager.get_metrics()
    print(f"✓ Got metrics: {metrics.total_tasks} total, {metrics.in_review} in review")

    # Get specific task
    if tasks:
        task = manager.get_task(tasks[0].id)
        print(f"✓ Got task: {task.title}")

    print()


def test_management_memory():
    """Test Management Memory"""
    print("=" * 80)
    print("Testing ManagementMemory")
    print("=" * 80)

    memory = get_management_memory()

    # Record event
    event = memory.record_event(
        EventType.TASK_CREATED,
        task_title="Test task"
    )
    print(f"✓ Recorded event: {event.event_type.value}")

    # Get events
    events = memory.get_events(limit=5)
    print(f"✓ Got {len(events)} events")

    # Get metrics history
    history = memory.get_metrics_history(limit=5)
    print(f"✓ Got {len(history)} metrics snapshots")

    print()


def test_task_lifecycle():
    """Test Task Lifecycle Manager"""
    print("=" * 80)
    print("Testing TaskLifecycleManager")
    print("=" * 80)

    lifecycle = get_lifecycle_manager()

    # Plan a task
    plan = lifecycle.plan_task(
        title="TEST-001: Test Task",
        description="This is a test task for the managerial agent",
        priority=Priority.NORMAL,
        estimated_duration=30
    )
    print(f"✓ Created plan: {plan.title}")

    print()


def test_team_dashboard():
    """Test Team Dashboard"""
    print("=" * 80)
    print("Testing TeamDashboard")
    print("=" * 80)

    dashboard = get_dashboard()

    # Get snapshot
    snapshot = dashboard.get_snapshot()
    print(f"✓ Got snapshot at {snapshot['timestamp']}")

    # Get agent statuses
    agents = dashboard.get_agent_statuses()
    print(f"✓ Got {len(agents)} agent statuses")

    # Get queue status
    queue = dashboard.get_queue_status()
    print(f"✓ Queue: {queue.pending} pending, {queue.in_progress} in progress")

    # Generate alerts
    alerts = dashboard.generate_alerts()
    print(f"✓ Generated {len(alerts)} alerts")

    # Render dashboard
    text_dashboard = dashboard.render_text()
    print(f"✓ Rendered text dashboard ({len(text_dashboard)} chars)")

    print()


def test_integration():
    """Test full integration"""
    print("=" * 80)
    print("Testing Full Integration")
    print("=" * 80)

    # Get all components
    manager = VibeKanbanManager()
    memory = get_management_memory()
    lifecycle = get_lifecycle_manager()
    dashboard = get_dashboard()

    print("✓ All components initialized")

    # Test coordinated workflow
    tasks = manager.list_tasks(status=TaskStatus.IN_REVIEW)
    print(f"✓ Found {len(tasks)} tasks in review")

    if tasks:
        # Record in memory
        for task in tasks:
            memory.record_event(
                EventType.REVIEW_REQUESTED,
                task_id=task.id,
                task_title=task.title
            )
        print(f"✓ Recorded {len(tasks)} events in memory")

    # Get metrics
    metrics = manager.get_metrics()
    memory.record_metrics({
        "total_tasks": metrics.total_tasks,
        "in_progress": metrics.in_progress,
        "in_review": metrics.in_review,
        "completed": metrics.completed
    })
    print("✓ Recorded metrics in memory")

    print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "MANAGERIAL AGENT TEST SUITE" + " " * 34 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")

    try:
        test_vibe_kanban_manager()
        test_management_memory()
        test_task_lifecycle()
        test_team_dashboard()
        test_integration()

        print("=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print("\nThe Managerial Agent system is fully functional!")
        print("\nQuick start:")
        print("  from agents.managerial import get_dashboard")
        print("  dashboard = get_dashboard()")
        print("  print(dashboard.render_text())")
        print("\n")

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
