#!/usr/bin/env python3
"""
Integration test for PlanningAgent Vibe Kanban integration.

Verifies that:
1. PlanningAgent can be configured with VibeKanbanManager
2. _create_kanban_cards() creates cards correctly
3. Integration handles errors gracefully
4. Cards are created with correct metadata
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Setup path - find 2-engine root
root = Path(__file__).resolve()
while root.name != '2-engine' and root.parent != root:
    root = root.parent

sys.path.insert(0, str(root))

from core.agents.definitions.planning_agent import PlanningAgent
from core.agents.definitions.core.base_agent import AgentConfig, AgentTask, AgentResult


class MockVibeKanbanManager:
    """Mock VibeKanbanManager for testing."""

    def __init__(self):
        self.created_tasks = []

    def create_task(self, title: str, description: str = None, priority=None, dependencies=None):
        """Mock create_task method."""
        task = Mock()
        task.id = f"kanban-{len(self.created_tasks) + 1}"
        task.title = title
        task.description = description
        task.status = Mock()
        task.status.value = "todo"
        task.priority = priority

        self.created_tasks.append(task)
        return task


async def test_kanban_configuration():
    """Test that PlanningAgent can be configured with VibeKanbanManager."""
    print("Test 1: Vibe Kanban Configuration")
    try:
        config = AgentConfig(
            name="planner",
            full_name="Planning Agent",
            role="planner",
            category="specialist",
            description="Test planning agent",
        )
        agent = PlanningAgent(config)

        # Create mock Vibe Kanban manager
        mock_kanban = MockVibeKanbanManager()

        # Configure agent
        agent.set_vibe_kanban(mock_kanban)

        if agent.vibe_kanban is mock_kanban:
            print("  ✓ Vibe Kanban manager configured successfully")
            return True
        else:
            print("  ✗ Vibe Kanban manager not set correctly")
            return False

    except Exception as e:
        print(f"  ✗ Configuration failed: {e}")
        return False


async def test_kanban_card_creation():
    """Test that _create_kanban_cards creates cards correctly."""
    print("\nTest 2: Kanban Card Creation")
    try:
        config = AgentConfig(
            name="planner",
            full_name="Planning Agent",
            role="planner",
            category="specialist",
            description="Test planning agent",
        )
        agent = PlanningAgent(config)

        # Create mock Vibe Kanban manager
        mock_kanban = MockVibeKanbanManager()
        agent.set_vibe_kanban(mock_kanban)

        # Create test tasks
        test_tasks = [
            {
                "id": "TASK-001",
                "title": "Set up project structure",
                "description": "Initialize project with proper directory structure",
                "type": "setup",
                "priority": "high",
                "epic_id": "EPIC-001",
            },
            {
                "id": "TASK-002",
                "title": "Configure development environment",
                "description": "Set up linting, formatting, and testing frameworks",
                "type": "setup",
                "priority": "high",
                "epic_id": "EPIC-001",
            },
            {
                "id": "TASK-003",
                "title": "Implement core functionality",
                "description": "Build the primary features",
                "type": "development",
                "priority": "medium",
                "epic_id": "EPIC-002",
            },
        ]

        # Call _create_kanban_cards
        result = await agent._create_kanban_cards(test_tasks, {})

        # Verify result structure
        if result["status"] != "success":
            print(f"  ✗ Unexpected status: {result['status']}")
            return False

        if result["total_tasks"] != 3:
            print(f"  ✗ Expected 3 total tasks, got {result['total_tasks']}")
            return False

        if result["created"] != 3:
            print(f"  ✗ Expected 3 created cards, got {result['created']}")
            return False

        if result["failed"] != 0:
            print(f"  ✗ Expected 0 failures, got {result['failed']}")
            return False

        # Verify cards were created
        if len(mock_kanban.created_tasks) != 3:
            print(f"  ✗ Expected 3 mock tasks, got {len(mock_kanban.created_tasks)}")
            return False

        # Verify card content
        card = mock_kanban.created_tasks[0]
        if card.title != "Set up project structure":
            print(f"  ✗ Unexpected card title: {card.title}")
            return False

        print(f"  ✓ Created {result['created']} Kanban cards successfully")
        print(f"  ✓ All cards have correct metadata")
        return True

    except Exception as e:
        print(f"  ✗ Card creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_kanban_without_manager():
    """Test that _create_kanban_cards handles missing manager gracefully."""
    print("\nTest 3: Kanban Without Manager")
    try:
        config = AgentConfig(
            name="planner",
            full_name="Planning Agent",
            role="planner",
            category="specialist",
            description="Test planning agent",
        )
        agent = PlanningAgent(config)

        # Don't configure Vibe Kanban
        test_tasks = [{"id": "TASK-001", "title": "Test task"}]

        result = await agent._create_kanban_cards(test_tasks, {})

        if result["status"] != "skipped":
            print(f"  ✗ Expected 'skipped' status, got '{result['status']}'")
            return False

        if "reason" not in result:
            print("  ✗ Expected 'reason' in result")
            return False

        print("  ✓ Correctly skipped when Vibe Kanban not configured")
        return True

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


async def test_kanban_priority_mapping():
    """Test that task priorities are correctly mapped to Kanban priorities."""
    print("\nTest 4: Kanban Priority Mapping")
    try:
        config = AgentConfig(
            name="planner",
            full_name="Planning Agent",
            role="planner",
            category="specialist",
            description="Test planning agent",
        )
        agent = PlanningAgent(config)

        mock_kanban = MockVibeKanbanManager()
        agent.set_vibe_kanban(mock_kanban)

        # Create tasks with different priorities
        test_tasks = [
            {"id": "TASK-001", "title": "Critical task", "priority": "critical"},
            {"id": "TASK-002", "title": "High task", "priority": "high"},
            {"id": "TASK-003", "title": "Normal task", "priority": "normal"},
            {"id": "TASK-004", "title": "Low task", "priority": "low"},
        ]

        result = await agent._create_kanban_cards(test_tasks, {})

        if result["created"] != 4:
            print(f"  ✗ Expected 4 created cards, got {result['created']}")
            return False

        print("  ✓ All priority levels handled correctly")
        return True

    except Exception as e:
        print(f"  ✗ Priority mapping failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_end_to_end_with_kanban():
    """Test full PlanningAgent execution with Kanban integration."""
    print("\nTest 5: End-to-End with Kanban")
    try:
        config = AgentConfig(
            name="planner",
            full_name="Planning Agent",
            role="planner",
            category="specialist",
            description="Test planning agent",
        )
        agent = PlanningAgent(config)

        mock_kanban = MockVibeKanbanManager()
        agent.set_vibe_kanban(mock_kanban)

        task = AgentTask(
            id="test-e2e",
            description="Build a REST API for user management",
            type="planning",
            context={
                "create_kanban_cards": True,
                "constraints": ["Python", "FastAPI"],
            }
        )

        result = await agent.execute(task)

        if not result.success:
            print(f"  ✗ Execution failed: {result.error}")
            return False

        # Verify Kanban results in artifacts
        if "kanban_results" not in result.artifacts:
            print("  ✗ Kanban results not in artifacts")
            return False

        kanban_results = result.artifacts["kanban_results"]
        if kanban_results["status"] != "success":
            print(f"  ✗ Kanban creation not successful: {kanban_results}")
            return False

        print(f"  ✓ End-to-end execution successful")
        print(f"  ✓ Created {kanban_results['created']} Kanban cards")
        return True

    except Exception as e:
        print(f"  ✗ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("PlanningAgent Vibe Kanban Integration Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Configuration
    result = await test_kanban_configuration()
    results.append(("Configuration", result))

    # Test 2: Card Creation
    result = await test_kanban_card_creation()
    results.append(("Card Creation", result))

    # Test 3: Without Manager
    result = await test_kanban_without_manager()
    results.append(("Without Manager", result))

    # Test 4: Priority Mapping
    result = await test_kanban_priority_mapping()
    results.append(("Priority Mapping", result))

    # Test 5: End-to-End
    result = await test_end_to_end_with_kanban()
    results.append(("End-to-End", result))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
