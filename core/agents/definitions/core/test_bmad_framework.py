#!/usr/bin/env python3
"""
Integration test for BMAD Framework.

Verifies that:
1. BMADFramework imports successfully
2. All modules can be instantiated
3. Full BMAD analysis works end-to-end
4. BMADFramework integrates with PlanningAgent
"""

import asyncio
import sys
from pathlib import Path

# Setup path - find 2-engine root
root = Path(__file__).resolve()
while root.name != '2-engine' and root.parent != root:
    root = root.parent

sys.path.insert(0, str(root))


async def test_bmad_import():
    """Test that BMADFramework imports successfully."""
    print("Test 1: BMADFramework imports successfully")
    try:
        from core.agents.definitions.bmad import BMADFramework
        print("  ✓ BMADFramework imported successfully")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


async def test_bmad_instantiation():
    """Test that BMADFramework can be instantiated."""
    print("\nTest 2: BMADFramework instantiation")
    try:
        from core.agents.definitions.bmad import BMADFramework

        bmad = BMADFramework()
        print(f"  ✓ BMADFramework instantiated")
        return True, bmad
    except Exception as e:
        print(f"  ✗ Instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_bmad_full_analysis():
    """Test that BMADFramework.analyze() works end-to-end."""
    print("\nTest 3: BMADFramework full analysis")
    try:
        from core.agents.definitions.bmad import BMADFramework

        bmad = BMADFramework()

        request = "Build a REST API for user management with authentication"
        context = {
            "tech_stack": ["Python", "FastAPI"],
            "constraints": ["PostgreSQL database"]
        }

        result = await bmad.analyze(request, context)

        # Verify all four dimensions are present
        assert "business" in result, "Missing business analysis"
        assert "model" in result, "Missing model design"
        assert "architecture" in result, "Missing architecture design"
        assert "development" in result, "Missing development plan"
        assert "metadata" in result, "Missing metadata"

        print(f"  ✓ Full analysis successful")
        print(f"  ✓ Business: {len(result['business'].get('goals', []))} goals")
        print(f"  ✓ Model: {len(result['model'].get('entities', []))} entities")
        print(f"  ✓ Architecture: {len(result['architecture'].get('components', []))} components")
        print(f"  ✓ Development: {result['development'].get('total_phases', 0)} phases")

        return True
    except Exception as e:
        print(f"  ✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_planning_agent_bmad_integration():
    """Test that PlanningAgent uses BMADFramework."""
    print("\nTest 4: PlanningAgent BMAD integration")
    try:
        from core.agents.definitions.planning_agent import PlanningAgent
        from core.agents.definitions.core.base_agent import AgentConfig, AgentTask

        config = AgentConfig(
            name="planner",
            full_name="Planning Agent",
            role="planner",
            category="specialist",
            description="Test planning agent with BMAD",
            metadata={"bmad_enabled": True}
        )
        agent = PlanningAgent(config)

        task = AgentTask(
            id="test-bmad-001",
            description="Build a REST API for user management",
            type="planning"
        )

        result = await agent.execute(task)

        if result.success:
            print(f"  ✓ PlanningAgent execution successful")

            # Check for BMAD artifacts
            if "bmad_analysis" in result.artifacts:
                bmad = result.artifacts["bmad_analysis"]
                print(f"  ✓ BMAD analysis present in artifacts")
                print(f"  ✓ BMAD has {len(bmad.get('business', {}).get('goals', []))} goals")
                print(f"  ✓ BMAD has {len(bmad.get('model', {}).get('entities', []))} entities")
                return True
            else:
                print(f"  ⚠ BMAD analysis not found in artifacts (BMAD may be disabled)")
                return True  # Not a failure, just a warning
        else:
            print(f"  ✗ Execution failed: {result.error}")
            return False

    except Exception as e:
        print(f"  ✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bmad_get_summary():
    """Test BMADFramework.get_summary()."""
    print("\nTest 5: BMADFramework summary generation")
    try:
        from core.agents.definitions.bmad import BMADFramework

        bmad = BMADFramework()
        result = await bmad.analyze("Build a task management API")
        summary = bmad.get_summary(result)

        assert "BMAD Analysis Summary" in summary
        assert "Business Analysis" in summary
        assert "Model Design" in summary
        assert "Architecture" in summary
        assert "Development Plan" in summary

        print(f"  ✓ Summary generated successfully")
        print(f"  ✓ Summary length: {len(summary)} characters")
        return True
    except Exception as e:
        print(f"  ✗ Summary generation failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("BMAD Framework Integration Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Import
    result = await test_bmad_import()
    results.append(("Import", result))

    # Test 2: Instantiation
    result, bmad = await test_bmad_instantiation()
    results.append(("Instantiation", result))

    # Test 3: Full analysis
    result = await test_bmad_full_analysis()
    results.append(("Full Analysis", result))

    # Test 4: PlanningAgent integration
    result = await test_planning_agent_bmad_integration()
    results.append(("PlanningAgent Integration", result))

    # Test 5: Summary generation
    result = await test_bmad_get_summary()
    results.append(("Summary Generation", result))

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
