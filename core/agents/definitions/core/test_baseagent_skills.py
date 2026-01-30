#!/usr/bin/env python3
"""
Test script for BaseAgent Tier 2 skills integration.

Verifies that:
1. Agents can load skills on-demand
2. Progressive disclosure works
3. Full skill loading works
4. Skill context management
5. Token usage tracking
6. Skill unloading
"""

import asyncio
import sys
from pathlib import Path

# Add the engine directory to the path
# Find blackbox5 root
root = Path(__file__).resolve()
while root.name != 'blackbox5' and root.parent != root:
    root = root.parent

engine_path = root / '2-engine' / '01-core'
sys.path.insert(0, str(engine_path))

from agents.core.base_agent import BaseAgent, AgentConfig, AgentTask


class TestAgent(BaseAgent):
    """Simple test agent for skill loading."""

    async def execute(self, task: AgentTask) -> 'AgentResult':
        """Execute task with skills."""
        from agents.core.base_agent import AgentResult

        # Load required skill
        skill_name = task.context.get('skill', 'test-skill')
        await self.load_skill(skill_name)

        # Use the skill
        skill_content = await self.use_skill(skill_name)

        return AgentResult(
            success=True,
            output=f"Executed task using skill: {skill_name}",
            metadata={
                "skill_content_length": len(skill_content) if skill_content else 0,
                "loaded_skills": self.list_loaded_skills(),
            }
        )

    async def think(self, task: AgentTask) -> list:
        """Generate thinking steps."""
        return [
            f"Understanding task: {task.description}",
            "Loading required skills",
            "Executing with skill context",
        ]


async def test_baseagent_skills():
    """Test BaseAgent skill loading functionality."""

    print("\n" + "=" * 70)
    print("Black Box 5 - BaseAgent Tier 2 Skills Integration Test")
    print("=" * 70)

    # Create test agent
    print("\n1. Creating TestAgent...")
    config = AgentConfig(
        name="test-agent",
        full_name="Test Agent",
        role="tester",
        category="testing",
        description="Agent for testing skill loading",
        tools=["test-skill"]  # Pre-configure skill
    )

    agent = TestAgent(config)
    print(f"   ✓ Agent created: {agent.name}")
    print(f"   ✓ Configured skills: {agent.get_skills()}")

    # Test 1: List available skills
    print("\n2. Listing available skills...")
    available = await agent.list_available_skills()
    print(f"   ✓ Tier 1 skills: {len(available['tier1'])}")
    print(f"   ✓ Tier 2 skills: {len(available['tier2'])}")
    print(f"   ✓ Tier 2: {available['tier2'][:5]}...")  # First 5

    # Test 2: Load skill with progressive disclosure
    print("\n3. Loading skill with progressive disclosure...")
    success = await agent.load_skill("test-skill", force_full=False)
    print(f"   ✓ Load success: {success}")

    loaded = agent.get_loaded_skill("test-skill")
    print(f"   ✓ Content loaded: {len(loaded) if loaded else 0} chars")
    print(f"   ✓ Preview (first 150 chars): {loaded[:150]}...")

    # Test 3: Load full skill
    print("\n4. Loading full skill content...")
    success = await agent.load_skill_full("test-skill")
    print(f"   ✓ Full load success: {success}")

    full_content = agent.get_loaded_skill("test-skill")
    print(f"   ✓ Full content: {len(full_content) if full_content else 0} chars")

    # Test 4: Use skill
    print("\n5. Using skill...")
    skill_content = await agent.use_skill("test-skill")
    print(f"   ✓ Skill used: {skill_content[:100] if skill_content else 'None'}...")

    # Test 5: List loaded skills
    print("\n6. Listing loaded skills...")
    loaded_skills = agent.list_loaded_skills()
    print(f"   ✓ Loaded skills: {loaded_skills}")

    # Test 6: Token usage
    print("\n7. Getting token usage...")
    usage = agent.get_token_usage()
    print(f"   ✓ Loaded skills: {usage['loaded_skills_count']}")
    print(f"   ✓ Total characters: {usage['total_characters']}")
    print(f"   ✓ Estimated tokens: {usage['estimated_tokens']}")

    # Test 7: Execute task with skill
    print("\n8. Executing task with skill...")
    task = AgentTask(
        id="test-001",
        description="Test skill loading",
        context={"skill": "test-skill"}
    )

    result = await agent.execute(task)
    print(f"   ✓ Task success: {result.success}")
    print(f"   ✓ Output: {result.output}")
    print(f"   ✓ Metadata: {result.metadata}")

    # Test 8: Unload skill
    print("\n9. Unloading skill...")
    unloaded = agent.unload_skill("test-skill")
    print(f"   ✓ Unloaded: {unloaded}")
    print(f"   ✓ Remaining loaded skills: {agent.list_loaded_skills()}")

    # Test 9: Unload all skills
    print("\n10. Unloading all skills...")
    # Load a few skills first
    await agent.load_skill("test-skill")
    await agent.load_skill("notion")
    print(f"   ✓ Loaded skills before unload: {agent.list_loaded_skills()}")

    count = agent.unload_all_skills()
    print(f"   ✓ Unloaded {count} skills")
    print(f"   ✓ Remaining loaded skills: {agent.list_loaded_skills()}")

    # Summary
    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)

    all_tests = [
        ("Agent created", agent is not None),
        ("Configured skills loaded", len(agent.get_skills()) > 0),
        ("Available skills listed", len(available['tier2']) > 0),
        ("Progressive disclosure works", success and "Use `load_skill_full`" in loaded),
        ("Full content loaded", len(full_content) >= 200),  # Full skill has more content
        ("Skill usage works", skill_content is not None),
        ("Loaded skills tracked", len(loaded_skills) > 0),
        ("Token usage calculated", usage['estimated_tokens'] > 0),
        ("Task execution with skill", result.success),
        ("Skill unloading works", unloaded and len(agent.list_loaded_skills()) == 0),
    ]

    passed = sum(1 for _, result in all_tests if result)
    total = len(all_tests)

    for test_name, result in all_tests:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"   {status}: {test_name}")

    print("=" * 70)
    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! BaseAgent skills integration is working!")
        print("\nNext steps:")
        print("  1. Integrate with real agents (Amelia, Mary, Alex, John)")
        print("  2. Test skill caching with ContextManager")
        print("  3. Measure token efficiency in real scenarios")
    else:
        print("\n⚠️  Some tests failed.")

    return passed == total


async def main():
    """Main entry point."""
    try:
        success = await test_baseagent_skills()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
