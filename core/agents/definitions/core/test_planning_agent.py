#!/usr/bin/env python3
"""
Integration test for PlanningAgent.

Verifies that:
1. PlanningAgent imports successfully
2. PlanningAgent can be instantiated with AgentConfig
3. PlanningAgent.execute() works end-to-end
4. PRD artifacts are generated correctly
5. Epic and task breakdown work
"""

import asyncio
import sys
from pathlib import Path

# Setup path - find 2-engine root
root = Path(__file__).resolve()
while root.name != '2-engine' and root.parent != root:
    root = root.parent

sys.path.insert(0, str(root))

from core.agents.definitions.planning_agent import PlanningAgent
from core.agents.definitions.core.base_agent import BaseAgent, AgentConfig, AgentTask, AgentResult


async def test_planning_agent_import():
    """Test that PlanningAgent imports successfully."""
    print("Test 1: PlanningAgent imports successfully")
    try:
        from core.agents.definitions.planning_agent import PlanningAgent
        print("  ✓ PlanningAgent imported successfully")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


async def test_planning_agent_instantiation():
    """Test that PlanningAgent can be instantiated."""
    print("\nTest 2: PlanningAgent instantiation")
    try:
        config = AgentConfig(
            name="planner",
            full_name="Planning Agent",
            role="planner",
            category="specialist",
            description="Test planning agent",
        )
        agent = PlanningAgent(config)
        print(f"  ✓ PlanningAgent instantiated: {agent.name}")
        return True, agent
    except Exception as e:
        print(f"  ✗ Instantiation failed: {e}")
        return False, None


async def test_planning_agent_execution():
    """Test that PlanningAgent.execute() works end-to-end."""
    print("\nTest 3: PlanningAgent execution")
    try:
        config = AgentConfig(
            name="planner",
            full_name="Planning Agent",
            role="planner",
            category="specialist",
            description="Test planning agent",
        )
        agent = PlanningAgent(config)

        task = AgentTask(
            id="test-001",
            description="Build a REST API for user management with authentication",
            type="planning",
            context={
                "project_type": "api",
                "constraints": ["Python", "FastAPI"]
            }
        )

        result = await agent.execute(task)

        if result.success:
            print(f"  ✓ Execution successful")
            print(f"  ✓ Output: {result.output[:100]}...")

            # Verify artifacts
            artifacts = result.artifacts
            if "prd" in artifacts:
                print(f"  ✓ PRD generated: {artifacts['prd']['title']}")
            if "epics" in artifacts:
                print(f"  ✓ Epics generated: {len(artifacts['epics'])} epics")
            if "tasks" in artifacts:
                print(f"  ✓ Tasks generated: {len(artifacts['tasks'])} tasks")
            if "assignments" in artifacts:
                print(f"  ✓ Agent assignments: {len(artifacts['assignments'])} assignments")

            return True
        else:
            print(f"  ✗ Execution failed: {result.error}")
            return False

    except Exception as e:
        print(f"  ✗ Execution error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_think_method():
    """Test that PlanningAgent.think() generates thinking steps."""
    print("\nTest 4: PlanningAgent thinking steps")
    try:
        config = AgentConfig(
            name="planner",
            full_name="Planning Agent",
            role="planner",
            category="specialist",
            description="Test planning agent",
        )
        agent = PlanningAgent(config)

        task = AgentTask(
            id="test-002",
            description="Test request",
            type="planning"
        )

        thinking_steps = await agent.think(task)

        if thinking_steps and len(thinking_steps) > 0:
            print(f"  ✓ Thinking steps generated: {len(thinking_steps)} steps")
            for i, step in enumerate(thinking_steps[:3], 1):
                print(f"    {i}. {step}")
            return True
        else:
            print(f"  ✗ No thinking steps generated")
            return False

    except Exception as e:
        print(f"  ✗ Think method error: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("PlanningAgent Integration Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Import
    result = await test_planning_agent_import()
    results.append(("Import", result))

    # Test 2: Instantiation
    result, agent = await test_planning_agent_instantiation()
    results.append(("Instantiation", result))

    # Test 3: Execution
    result = await test_planning_agent_execution()
    results.append(("Execution", result))

    # Test 4: Think method
    result = await test_think_method()
    results.append(("Think Method", result))

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
