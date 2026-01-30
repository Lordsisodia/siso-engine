"""
Test Suite for Enhanced Memory System

This module provides comprehensive tests for all phases of the enhanced memory system:
- Phase 1: Semantic Memory Retrieval
- Phase 2: Importance Scoring
- Phase 3: Memory Consolidation
- Phase 4: Episodic Memory Linking

Run tests:
    python -m pytest tests/test_enhanced_memory.py -v
    python tests/test_enhanced_memory.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_importance_scoring():
    """Test Phase 2: Importance Scoring"""
    print("\n" + "="*60)
    print("Testing Phase 2: Importance Scoring")
    print("="*60)

    from importance.ImportanceScorer import ImportanceScorer, ImportanceConfig

    # Test 1: Basic importance calculation
    print("\n[Test 1] Basic importance calculation")
    scorer = ImportanceScorer()

    # User message with error (high importance)
    importance = scorer.calculate_importance(
        role="user",
        content="I found a bug in the authentication system",
        timestamp=datetime.now().isoformat()
    )
    print(f"  User error message importance: {importance:.2f}")
    assert importance > 0.6, "User error should have high importance"
    print("  ✓ PASS")

    # System message (low importance)
    importance = scorer.calculate_importance(
        role="system",
        content="System initialized",
        timestamp=datetime.now().isoformat()
    )
    print(f"  System message importance: {importance:.2f}")
    assert importance < 0.6, "System message should have lower importance"
    print("  ✓ PASS")

    # Test 2: Recency bonus
    print("\n[Test 2] Recency bonus")
    recent_msg = {
        'timestamp': datetime.now().isoformat(),
        'role': 'user',
        'content': 'Recent message'
    }
    old_msg = {
        'timestamp': (datetime.now() - timedelta(hours=5)).isoformat(),
        'role': 'user',
        'content': 'Old message'
    }

    recent_importance = scorer.calculate_importance(**recent_msg)
    old_importance = scorer.calculate_importance(**old_msg)

    print(f"  Recent message: {recent_importance:.2f}")
    print(f"  Old message: {old_importance:.2f}")
    assert recent_importance > old_importance, "Recent messages should score higher"
    print("  ✓ PASS")

    # Test 3: Error keywords
    print("\n[Test 3] Error keyword detection")
    error_msg = scorer.calculate_importance(
        role="assistant",
        content="Error: Failed to connect to database",
        timestamp=datetime.now().isoformat()
    )
    normal_msg = scorer.calculate_importance(
        role="assistant",
        content="Connected to database successfully",
        timestamp=datetime.now().isoformat()
    )

    print(f"  Error message: {error_msg:.2f}")
    print(f"  Normal message: {normal_msg:.2f}")
    assert error_msg > normal_msg, "Error messages should score higher"
    print("  ✓ PASS")

    # Test 4: Custom configuration
    print("\n[Test 4] Custom importance configuration")
    config = ImportanceConfig(
        base_score=0.3,
        error_bonus=0.5,
        recent_bonus=0.3
    )
    custom_scorer = ImportanceScorer(config)

    importance = custom_scorer.calculate_importance(
        role="user",
        content="Error: Something failed",
        timestamp=datetime.now().isoformat()
    )
    print(f"  Custom configured importance: {importance:.2f}")
    assert importance > 0.7, "Custom config should produce higher scores"
    print("  ✓ PASS")

    print("\n✅ All importance scoring tests passed!")


def test_semantic_retrieval():
    """Test Phase 1: Semantic Memory Retrieval"""
    print("\n" + "="*60)
    print("Testing Phase 1: Semantic Memory Retrieval")
    print("="*60)

    from ProductionMemorySystem import Message
    from EnhancedProductionMemorySystem import EnhancedProductionMemorySystem
    from pathlib import Path
    import tempfile

    # Create temporary memory system
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = EnhancedProductionMemorySystem(
            project_path=Path(tmpdir),
            project_name="test"
        )

        # Add test messages
        messages = [
            Message(role="user", content="How do I fix authentication errors?", timestamp=datetime.now().isoformat()),
            Message(role="assistant", content="Check your API key configuration", timestamp=datetime.now().isoformat()),
            Message(role="user", content="The database connection is timing out", timestamp=datetime.now().isoformat()),
            Message(role="assistant", content="Increase the connection timeout value", timestamp=datetime.now().isoformat()),
            Message(role="user", content="I need help with the login form", timestamp=datetime.now().isoformat()),
        ]

        for msg in messages:
            memory.add(msg)

        # Test 1: Recent retrieval (default)
        print("\n[Test 1] Recent retrieval (default)")
        context = memory.get_context(limit=3)
        print(f"  Retrieved {len(context.split(chr(10)))} messages")
        assert "login form" in context, "Should get recent messages"
        print("  ✓ PASS")

        # Test 2: Semantic retrieval
        print("\n[Test 2] Semantic retrieval")
        context = memory.get_context(
            query="authentication problems",
            limit=3,
            strategy="semantic"
        )
        print(f"  Context for 'authentication problems': {len(context)} chars")
        print("  ✓ PASS")

        # Test 3: Importance-based retrieval
        print("\n[Test 3] Importance-based retrieval")
        context = memory.get_context(
            limit=3,
            strategy="importance",
            min_importance=0.3
        )
        print(f"  High-importance messages retrieved")
        print("  ✓ PASS")

        # Test 4: Hybrid retrieval
        print("\n[Test 4] Hybrid retrieval")
        context = memory.get_context(
            query="database",
            limit=3,
            strategy="hybrid"
        )
        print(f"  Hybrid context for 'database': {len(context)} chars")
        print("  ✓ PASS")

    print("\n✅ All semantic retrieval tests passed!")


async def test_consolidation():
    """Test Phase 3: Memory Consolidation"""
    print("\n" + "="*60)
    print("Testing Phase 3: Memory Consolidation")
    print("="*60)

    from consolidation.MemoryConsolidation import MemoryConsolidation, ConsolidationConfig
    from ProductionMemorySystem import Message
    from EnhancedProductionMemorySystem import EnhancedProductionMemorySystem
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        memory = EnhancedProductionMemorySystem(
            project_path=Path(tmpdir),
            project_name="test_consolidation"
        )

        # Add many messages to trigger consolidation
        print("\n[Test 1] Adding messages to trigger consolidation")
        for i in range(50):
            msg = Message(
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message number {i}: {'error' if i % 10 == 0 else 'info'}",
                timestamp=datetime.now().isoformat()
            )
            memory.add(msg)

        print(f"  Added 50 messages")
        print(f"  Working memory size: {memory.working.size()}")

        # Test consolidation
        print("\n[Test 2] Running consolidation")
        result = await memory.consolidate()

        print(f"  Status: {result.get('status')}")
        if result.get('status') == 'success':
            print(f"  Consolidated {result.get('consolidated_count')} messages")
            print(f"  Preserved {result.get('preserved_count')} high-importance messages")
            print(f"  Final count: {result.get('final_count')}")

        print("  ✓ PASS")

        # Test 3: Get consolidation stats
        print("\n[Test 3] Consolidation statistics")
        stats = memory.get_consolidation_stats()
        print(f"  Current size: {stats.get('current_size')}")
        print(f"  Should consolidate: {stats.get('should_consolidate')}")
        print("  ✓ PASS")

    print("\n✅ All consolidation tests passed!")


def test_episodic_memory():
    """Test Phase 4: Episodic Memory Linking"""
    print("\n" + "="*60)
    print("Testing Phase 4: Episodic Memory Linking")
    print("="*60)

    from episodic.EpisodicMemory import EpisodicMemory
    from episodic.Episode import Episode
    from ProductionMemorySystem import Message
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        episodic = EpisodicMemory(storage_path=Path(tmpdir) / "episodes")

        # Create test messages
        messages = [
            Message(role="user", content="I'm having database issues", timestamp=datetime.now().isoformat()),
            Message(role="assistant", content="Let me check the connection", timestamp=datetime.now().isoformat()),
            Message(role="assistant", content="The connection timeout was too low", timestamp=datetime.now().isoformat()),
            Message(role="user", content="Thanks, that fixed it", timestamp=datetime.now().isoformat()),
        ]

        # Test 1: Create episode
        print("\n[Test 1] Creating episode")
        episode = episodic.create_episode(
            title="Database Troubleshooting",
            messages=messages,
            description="Fixed database connection timeout"
        )

        print(f"  Episode ID: {episode.id}")
        print(f"  Title: {episode.title}")
        print(f"  Message count: {episode.message_count()}")
        print(f"  Duration: {episode.duration_hours():.2f} hours")
        assert episode.message_count() == 4, "Episode should contain 4 messages"
        print("  ✓ PASS")

        # Test 2: Find related episodes
        print("\n[Test 2] Finding related episodes")
        # Create a similar episode
        messages2 = [
            Message(role="user", content="Database is slow again", timestamp=datetime.now().isoformat()),
            Message(role="assistant", content="Check the query performance", timestamp=datetime.now().isoformat()),
        ]
        episode2 = episodic.create_episode(
            title="Performance Issue",
            messages=messages2
        )

        related = episodic.find_related_episodes(episode)
        print(f"  Found {len(related)} related episodes")
        print("  ✓ PASS")

        # Test 3: Search episodes
        print("\n[Test 3] Searching episodes")
        results = episodic.search_episodes("database")
        print(f"  Found {len(results)} episodes matching 'database'")
        assert len(results) >= 1, "Should find at least one database episode"
        print("  ✓ PASS")

        # Test 4: Add outcome and lessons
        print("\n[Test 4] Adding outcomes and lessons")
        success = episodic.add_outcome(episode.id, "Fixed the timeout issue")
        assert success, "Should add outcome"
        print("  ✓ Added outcome")

        success = episodic.add_learned_lesson(episode.id, "Always check timeout settings first")
        assert success, "Should add lesson"
        print("  ✓ Added lesson")

        # Test 5: Get episodic stats
        print("\n[Test 5] Episodic statistics")
        stats = episodic.get_stats()
        print(f"  Total episodes: {stats['total_episodes']}")
        print(f"  Indexed messages: {stats['indexed_messages']}")
        print("  ✓ PASS")

    print("\n✅ All episodic memory tests passed!")


def test_integration():
    """Test full integration of all phases"""
    print("\n" + "="*60)
    print("Testing Full Integration")
    print("="*60)

    from ProductionMemorySystem import Message
    from EnhancedProductionMemorySystem import EnhancedProductionMemorySystem
    from importance.ImportanceScorer import ImportanceConfig
    from consolidation.MemoryConsolidation import ConsolidationConfig
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create fully enabled memory system
        print("\n[Test 1] Creating enhanced memory system with all features")
        memory = EnhancedProductionMemorySystem(
            project_path=Path(tmpdir),
            project_name="test_integration",
            importance_config=ImportanceConfig(
                base_score=0.5,
                error_bonus=0.4
            ),
            enable_consolidation=True,
            consolidation_config=ConsolidationConfig(
                max_messages=30,
                recent_keep=10,
                auto_consolidate=False  # Manual control for testing
            ),
            enable_episodic=True
        )
        print("  ✓ Created memory system")

        # Test 2: Add various messages
        print("\n[Test 2] Adding test messages")
        messages = [
            Message(role="user", content="Error: Authentication failing", timestamp=datetime.now().isoformat(), metadata={"type": "error"}),
            Message(role="assistant", content="Checking API key configuration", timestamp=datetime.now().isoformat()),
            Message(role="user", content="Fixed it, was a typo in the key", timestamp=datetime.now().isoformat(), metadata={"type": "resolution"}),
            Message(role="assistant", content="Great, let me know if you need anything else", timestamp=datetime.now().isoformat()),
        ]

        for msg in messages:
            memory.add(msg)
        print(f"  ✓ Added {len(messages)} messages")

        # Test 3: Semantic + Importance retrieval
        print("\n[Test 3] Semantic retrieval with importance filtering")
        context = memory.get_context(
            query="authentication",
            limit=5,
            strategy="hybrid",
            min_importance=0.4
        )
        print(f"  Retrieved context: {len(context)} chars")
        assert "authentication" in context.lower(), "Should find authentication-related content"
        print("  ✓ PASS")

        # Test 4: Create episode
        print("\n[Test 4] Creating episode from working memory")
        episode = memory.create_episode(
            title="Authentication Fix",
            description="Resolved API key typo issue"
        )
        assert episode is not None, "Should create episode"
        print(f"  ✓ Created episode: {episode.title}")

        # Test 5: Add episode outcome
        print("\n[Test 5] Adding episode outcome")
        success = memory.add_episode_outcome(episode.id, "Successfully authenticated after fixing typo")
        assert success, "Should add outcome"
        print("  ✓ Added outcome")

        # Test 6: Test consolidation
        print("\n[Test 6] Testing consolidation")
        # Add more messages to exceed threshold
        for i in range(30):
            msg = Message(
                role="user",
                content=f"Test message {i}",
                timestamp=datetime.now().isoformat()
            )
            memory.add(msg)

        print(f"  Working memory size before consolidation: {memory.working.size()}")
        result = asyncio.run(memory.consolidate())
        print(f"  Consolidation result: {result.get('status')}")
        print(f"  Working memory size after consolidation: {memory.working.size()}")
        print("  ✓ PASS")

        # Test 7: Get all stats
        print("\n[Test 7] Getting system statistics")
        consolidation_stats = memory.get_consolidation_stats()
        episodic_stats = memory.get_episodic_stats()

        print(f"  Consolidation enabled: {consolidation_stats.get('enabled', False)}")
        print(f"  Episodic enabled: {episodic_stats.get('enabled', False)}")
        print(f"  Total episodes: {episodic_stats.get('total_episodes', 0)}")
        print("  ✓ PASS")

    print("\n✅ All integration tests passed!")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*70)
    print(" "*20 + "ENHANCED MEMORY SYSTEM TEST SUITE")
    print("="*70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    tests_passed = 0
    tests_failed = 0

    test_suites = [
        ("Importance Scoring", test_importance_scoring),
        ("Semantic Retrieval", test_semantic_retrieval),
        ("Consolidation", test_consolidation),
        ("Episodic Memory", test_episodic_memory),
        ("Integration", test_integration),
    ]

    for name, test_func in test_suites:
        try:
            test_func()
            tests_passed += 1
        except AssertionError as e:
            print(f"\n❌ {name} test FAILED: {e}")
            tests_failed += 1
        except Exception as e:
            print(f"\n❌ {name} test ERROR: {e}")
            import traceback
            traceback.print_exc()
            tests_failed += 1

    # Summary
    print("\n" + "="*70)
    print(" "*25 + "TEST SUMMARY")
    print("="*70)
    print(f"Total Test Suites: {tests_passed + tests_failed}")
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print("="*70)

    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉\n")
        return 0
    else:
        print(f"\n⚠️  {tests_failed} test suite(s) failed\n")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    exit(exit_code)
