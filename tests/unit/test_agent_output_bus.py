#!/usr/bin/env python3
"""
Test Agent Output Bus - End-to-End Integration Tests

Tests the complete Agent Output Bus system with all handlers.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from AgentOutputBus import (
    AgentOutputBus,
    OutputEvent,
    OutputStatus,
    get_agent_output_bus,
    send_agent_output
)
from AgentOutputParser import create_agent_output, parse_agent_output

# Import handlers that are always available
from handlers.database_handler import DatabaseHandler
from handlers.notification_handler import NotificationHandler

# Import handlers that may have dependencies
try:
    from handlers.vibe_handler import VibeKanbanHandler
except ImportError:
    VibeKanbanHandler = None

try:
    from handlers.scheduler_handler import SchedulerHandler
except ImportError:
    SchedulerHandler = None


def create_sample_output(
    status: str = "success",
    agent_name: str = "test-agent",
    summary: str = "Test task completed"
) -> str:
    """Create a sample agent output for testing."""
    return create_agent_output(
        status=status,
        summary=summary,
        deliverables=["file1.py", "file2.ts"] if status == "success" else [],
        next_steps=["Review the changes", "Run tests"] if status == "success" else ["Retry with different approach"],
        human_content=f"This is the human-readable content from {agent_name}.",
        agent_name=agent_name,
        task_id="test-task-123"
    )


def test_bus_creation():
    """Test 1: Create and initialize AgentOutputBus."""
    print("=" * 70)
    print("TEST 1: Create AgentOutputBus")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        bus = AgentOutputBus(db_path=db_path)
        bus.initialize()

        print(f"✅ AgentOutputBus created")
        print(f"   DB path: {db_path}")
        print(f"   Initialized: {bus._initialized}")

        # Test global singleton
        global_bus = get_agent_output_bus(db_path=db_path)
        print(f"✅ Global singleton retrieved: {global_bus is not None}")

        return True


def test_basic_receive():
    """Test 2: Receive and parse agent output."""
    print("\n" + "=" * 70)
    print("TEST 2: Receive Agent Output")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        bus = AgentOutputBus(db_path=db_path)
        bus.initialize()

        # Create sample output
        output = create_sample_output(
            status="success",
            agent_name="coder",
            summary="Created API endpoint"
        )

        print("Sending output to bus...")
        result = bus.receive(output)

        print(f"✅ Output processed")
        print(f"   Success: {result['success']}")
        print(f"   Agent: {result['event']['agent']}")
        print(f"   Status: {result['event']['status']}")
        print(f"   Summary: {result['event']['summary']}")
        print(f"   Deliverables: {result['event']['deliverables_count']}")
        print(f"   Next Steps: {result['event']['next_steps_count']}")

        # Check database
        recent = bus.get_recent_outputs(limit=1)
        print(f"✅ Database entry created: {len(recent)} record(s)")

        return result['success']


def test_notification_handler():
    """Test 3: Test notification handler."""
    print("\n" + "=" * 70)
    print("TEST 3: Notification Handler")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        bus = AgentOutputBus(db_path=db_path)

        # Register notification handler
        notification_handler = NotificationHandler(
            notify_on_failure=True,
            notify_on_partial=True,
            notify_on_success=True
        )
        bus.register_handler(notification_handler)
        bus.initialize()

        # Test failure notification
        print("\n--- Testing Failure Notification ---")
        failed_output = create_sample_output(
            status="failed",
            agent_name="tester",
            summary="Test execution failed"
        )
        result = bus.receive(failed_output)
        print(f"✅ Failure handled: {result['success']}")
        for handler_result in result['handlers']:
            if handler_result['handler'] == 'NotificationHandler':
                print(f"   {handler_result['message']}")

        # Test partial notification
        print("\n--- Testing Partial Notification ---")
        partial_output = create_sample_output(
            status="partial",
            agent_name="builder",
            summary="Partial build completed"
        )
        result = bus.receive(partial_output)
        print(f"✅ Partial handled: {result['success']}")
        for handler_result in result['handlers']:
            if handler_result['handler'] == 'NotificationHandler':
                print(f"   {handler_result['message']}")

        # Test success notification
        print("\n--- Testing Success Notification ---")
        success_output = create_sample_output(
            status="success",
            agent_name="deployer",
            summary="Deployment successful"
        )
        result = bus.receive(success_output)
        print(f"✅ Success handled: {result['success']}")
        for handler_result in result['handlers']:
            if handler_result['handler'] == 'NotificationHandler':
                print(f"   {handler_result['message']}")

        return True


def test_database_handler():
    """Test 4: Test database handler."""
    print("\n" + "=" * 70)
    print("TEST 4: Database Handler")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        bus = AgentOutputBus(db_path=db_path)

        # Register custom database handler
        custom_db_handler = DatabaseHandler(
            db_path=db_path,
            custom_table_name="custom_outputs"
        )
        bus.register_handler(custom_db_handler)
        bus.initialize()

        # Send multiple outputs
        outputs = [
            create_sample_output("success", "agent-1", "Task 1 complete"),
            create_sample_output("partial", "agent-2", "Task 2 partial"),
            create_sample_output("failed", "agent-3", "Task 3 failed"),
        ]

        for output in outputs:
            bus.receive(output)

        print(f"✅ Sent {len(outputs)} outputs")

        # Query stats
        stats = bus.get_agent_stats()
        print(f"\n📊 Overall Stats:")
        print(f"   Total: {stats['total']}")
        print(f"   Success: {stats['success_count']}")
        print(f"   Partial: {stats['partial_count']}")
        print(f"   Failed: {stats['failed_count']}")
        print(f"   Success Rate: {stats['success_rate']:.1%}")

        # Query by agent
        agent_stats = bus.get_agent_stats("agent-1")
        print(f"\n📊 Agent-1 Stats:")
        print(f"   Total: {agent_stats['total']}")
        print(f"   Success Rate: {agent_stats['success_rate']:.1%}")

        # Recent deliverables
        deliverables = bus.get_recent_deliverables(limit=10)
        print(f"\n📦 Recent Deliverables: {len(deliverables)}")
        for d in deliverables[:5]:
            print(f"   - {d}")

        # Custom handler stats
        custom_stats = custom_db_handler.get_stats()
        print(f"\n📊 Custom DB Stats:")
        print(f"   Total: {custom_stats['total']}")
        print(f"   Success Rate: {custom_stats['success_rate']:.1%}")

        return True


def test_convenience_function():
    """Test 5: Test convenience function."""
    print("\n" + "=" * 70)
    print("TEST 5: Convenience Function")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Use convenience function
        output = create_sample_output(
            status="success",
            agent_name="convenience-test",
            summary="Testing send_agent_output()"
        )

        result = send_agent_output(output, db_path=db_path)

        print(f"✅ Convenience function works")
        print(f"   Success: {result['success']}")
        print(f"   Agent: {result['event']['agent']}")
        print(f"   Status: {result['event']['status']}")

        return result['success']


def test_end_to_end_workflow():
    """Test 6: End-to-end workflow simulating real agent coordination."""
    print("\n" + "=" * 70)
    print("TEST 6: End-to-End Agent Coordination Workflow")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        bus = AgentOutputBus(db_path=db_path)

        # Register all handlers
        notification_handler = NotificationHandler(
            notify_on_failure=True,
            notify_on_partial=False,
            notify_on_success=False
        )
        custom_db_handler = DatabaseHandler(
            db_path=db_path,
            custom_table_name="workflow_outputs"
        )

        bus.register_handler(notification_handler)
        bus.register_handler(custom_db_handler)
        bus.initialize()

        # Simulate a workflow: Architect → Coder → Tester → Deployer
        workflow = [
            {
                "agent": "architect",
                "status": "success",
                "summary": "Designed REST API architecture",
                "deliverables": ["api-design.md", "database-schema.sql"]
            },
            {
                "agent": "coder",
                "status": "success",
                "summary": "Implemented REST API endpoints",
                "deliverables": ["api/users.py", "api/auth.py"]
            },
            {
                "agent": "tester",
                "status": "partial",
                "summary": "Tests passing with minor issues",
                "deliverables": ["tests/test_users.py"],
                "next_steps": ["Fix edge case in user deletion", "Add integration tests"]
            },
            {
                "agent": "deployer",
                "status": "success",
                "summary": "Deployed to staging environment",
                "deliverables": ["deployment/staging-config.yaml"],
                "next_steps": ["Monitor staging metrics", "Prepare production deployment"]
            }
        ]

        print("\nExecuting workflow...")
        for step in workflow:
            output = create_agent_output(
                status=step["status"],
                summary=step["summary"],
                deliverables=step.get("deliverables", []),
                next_steps=step.get("next_steps", []),
                human_content=f"Details from {step['agent']}",
                agent_name=step["agent"],
                task_id=f"workflow-{step['agent']}"
            )

            result = bus.receive(output)
            print(f"\n{step['agent'].upper()}: {result['event']['status']} - {step['summary']}")

        # Get final stats
        stats = bus.get_agent_stats()
        print(f"\n📊 Workflow Complete:")
        print(f"   Total tasks: {stats['total']}")
        print(f"   Success: {stats['success_count']}")
        print(f"   Partial: {stats['partial_count']}")
        print(f"   Failed: {stats['failed_count']}")

        # Show all deliverables
        deliverables = bus.get_recent_deliverables(limit=20)
        print(f"\n📦 All Deliverables: {len(deliverables)}")
        for d in deliverables:
            print(f"   - {d}")

        return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("AGENT OUTPUT BUS - END-TO-END INTEGRATION TESTS")
    print("=" * 70)

    tests = [
        ("Create Bus", test_bus_creation),
        ("Receive Output", test_basic_receive),
        ("Notification Handler", test_notification_handler),
        ("Database Handler", test_database_handler),
        ("Convenience Function", test_convenience_function),
        ("End-to-End Workflow", test_end_to_end_workflow),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\n{passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 All tests passed! Agent Output Bus is working.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
