#!/usr/bin/env python3
"""
Test script for Tier 2 Agent Skills integration.

Verifies that:
1. Tier 2 skills are discovered from ~/.claude/skills/
2. YAML frontmatter is parsed correctly
3. Skill content is accessible
4. Tags are indexed
5. Progressive disclosure works
"""

import asyncio
import sys
from pathlib import Path

# Add the engine directory to the path
engine_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(engine_path))

from agents.core.skill_manager import SkillManager


async def test_tier2_skills():
    """Test Tier 2 skills loading and functionality."""

    print("\n" + "=" * 70)
    print("Black Box 5 - Tier 2 Skills Integration Test")
    print("=" * 70)

    # Initialize SkillManager
    print("\n1. Initializing SkillManager...")
    skill_manager = SkillManager()
    print(f"   ✓ Tier 1 path: {skill_manager.skills_path}")
    print(f"   ✓ Tier 2 path: {skill_manager._tier2_skills_path}")

    # Check if Tier 2 directory exists
    if not skill_manager._tier2_skills_path.exists():
        print(f"\n   ✗ Tier 2 skills directory not found!")
        print(f"   Create it with: mkdir -p {skill_manager._tier2_skills_path}")
        return False

    # Load all skills
    print("\n2. Loading skills (Tier 1 + Tier 2)...")
    await skill_manager.load_all()

    tier1_count = len(skill_manager.list_tier1_skills())
    tier2_count = len(skill_manager.list_tier2_skills())

    print(f"   ✓ Tier 1 skills loaded: {tier1_count}")
    print(f"   ✓ Tier 2 skills loaded: {tier2_count}")

    # Test specific skill
    print("\n3. Testing 'test-skill'...")
    test_skill = skill_manager.get_skill("test-skill")

    if test_skill is None:
        print("   ✗ test-skill not found!")
        print(f"   Expected at: {skill_manager._tier2_skills_path / 'test-skill' / 'SKILL.md'}")
        return False

    print(f"   ✓ Found: {test_skill.name}")
    print(f"   ✓ Description: {test_skill.description}")
    print(f"   ✓ Tags: {', '.join(test_skill.tags)}")
    print(f"   ✓ Author: {test_skill.author or 'N/A'}")
    print(f"   ✓ Version: {test_skill.version or 'N/A'}")

    # Test progressive disclosure
    print("\n4. Testing progressive disclosure...")
    summary = skill_manager.get_skill_content("test-skill", use_progressive=True)
    print(f"   ✓ Summary (first 200 chars):")
    print(f"     {summary[:200]}...")

    full_content = skill_manager.get_skill_content("test-skill", use_progressive=False)
    print(f"   ✓ Full content length: {len(full_content)} chars")

    # Test tag search
    print("\n5. Testing tag search...")
    test_skills = skill_manager.search_skills_by_tag("test")
    print(f"   ✓ Found {len(test_skills)} skills with tag 'test'")
    for skill in test_skills:
        print(f"     - {skill.name}")

    # List all Tier 2 skills
    print("\n6. Listing all Tier 2 skills...")
    all_skills = skill_manager.list_all_skills()
    print(f"   Tier 1: {all_skills['tier1']}")
    print(f"   Tier 2: {all_skills['tier2']}")

    # Test summary
    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)

    success = True

    checks = [
        ("Tier 2 directory exists", skill_manager._tier2_skills_path.exists()),
        ("test-skill found", test_skill is not None),
        ("YAML frontmatter parsed", test_skill and test_skill.description != ""),
        ("Tags indexed", test_skill and len(test_skill.tags) > 0),
        ("Content accessible", test_skill and len(test_skill.content) > 0),
        ("Progressive disclosure works", summary is not None and len(summary) > 0),
        ("Full content available", full_content is not None and len(full_content) > 0),
    ]

    for check_name, check_result in checks:
        status = "✓ PASS" if check_result else "✗ FAIL"
        print(f"   {status}: {check_name}")
        if not check_result:
            success = False

    print("=" * 70)

    if success:
        print("\n🎉 All tests passed! Tier 2 skills integration is working!")
        print("\nNext steps:")
        print("  1. Convert supabase-operations skill")
        print("  2. Convert siso-tasks-cli skill")
        print("  3. Convert feedback-triage skill")
        print("  4. Test with agents")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")

    return success


async def main():
    """Main entry point."""
    try:
        success = await test_tier2_skills()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
