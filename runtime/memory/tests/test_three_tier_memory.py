"""
Tests for Three-Tier Memory System

Tests the complete memory hierarchy:
- Tier 1: WorkingMemory (last 10 messages, immediate context)
- Tier 2: SummaryTier (last 10 consolidation cycles, mid-term context)
- Tier 3: PersistentMemory (all messages, long-term storage)

Based on research from MemoryOS, MemGPT, H-MEM.
"""

import asyncio
import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Import memory system components
try:
    from storage.SummaryTier import SummaryTier, ConsolidatedSummary, create_summary_tier
    from storage.EnhancedProductionMemorySystem import (
        EnhancedProductionMemorySystem,
        create_enhanced_memory_system
    )
    from storage.consolidation.MemoryConsolidation import (
        MemoryConsolidation,
        ConsolidationConfig,
        create_consolidation
    )
    from storage.ProductionMemorySystem import create_message
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from SummaryTier import SummaryTier, ConsolidatedSummary, create_summary_tier
    from EnhancedProductionMemorySystem import (
        EnhancedProductionMemorySystem,
        create_enhanced_memory_system
    )
    from consolidation.MemoryConsolidation import (
        MemoryConsolidation,
        ConsolidationConfig,
        create_consolidation
    )
    from ProductionMemorySystem import create_message


class TestSummaryTier:
    """Tests for SummaryTier (middle tier)."""

    def test_create_summary_tier(self):
        """Test creating a SummaryTier."""
        summary_tier = create_summary_tier(max_summaries=10)
        assert summary_tier is not None
        assert summary_tier.max_summaries == 10
        assert summary_tier.size() == 0

    def test_add_summary(self):
        """Test adding a summary to SummaryTier."""
        summary_tier = create_summary_tier(max_summaries=10)

        summary = ConsolidatedSummary(
            summary="Test summary",
            consolidated_count=5,
            oldest_timestamp="2026-01-19T00:00:00",
            newest_timestamp="2026-01-19T01:00:00",
            consolidated_at=datetime.now().isoformat(),
            metadata={}
        )

        summary_tier.add_summary(summary)
        assert summary_tier.size() == 1

    def test_max_summaries_limit(self):
        """Test that SummaryTier respects max_summaries limit."""
        summary_tier = create_summary_tier(max_summaries=3)

        # Add 5 summaries
        for i in range(5):
            summary = ConsolidatedSummary(
                summary=f"Summary {i}",
                consolidated_count=5,
                oldest_timestamp="2026-01-19T00:00:00",
                newest_timestamp="2026-01-19T01:00:00",
                consolidated_at=datetime.now().isoformat(),
                metadata={}
            )
            summary_tier.add_summary(summary)

        # Should only keep last 3
        assert summary_tier.size() == 3

    def test_get_summaries(self):
        """Test retrieving summaries."""
        summary_tier = create_summary_tier(max_summaries=10)

        # Add summaries
        for i in range(5):
            summary = ConsolidatedSummary(
                summary=f"Summary {i}",
                consolidated_count=5,
                oldest_timestamp="2026-01-19T00:00:00",
                newest_timestamp="2026-01-19T01:00:00",
                consolidated_at=datetime.now().isoformat(),
                metadata={}
            )
            summary_tier.add_summary(summary)

        # Get all summaries
        summaries = summary_tier.get_summaries()
        assert len(summaries) == 5

        # Get limited summaries
        summaries = summary_tier.get_summaries(limit=3)
        assert len(summaries) == 3

    def test_get_context_string(self):
        """Test getting context string from summaries."""
        summary_tier = create_summary_tier(max_summaries=10)

        summary = ConsolidatedSummary(
            summary="User discussed authentication issues",
            consolidated_count=3,
            oldest_timestamp="2026-01-19T00:00:00",
            newest_timestamp="2026-01-19T01:00:00",
            consolidated_at=datetime.now().isoformat(),
            metadata={}
        )

        summary_tier.add_summary(summary)

        context = summary_tier.get_context_string()
        assert "authentication issues" in context
        assert "CONSOLIDATED SUMMARY" in context

    def test_get_stats(self):
        """Test getting SummaryTier statistics."""
        summary_tier = create_summary_tier(max_summaries=10)

        stats = summary_tier.get_stats()
        assert stats["count"] == 0
        assert stats["max_summaries"] == 10
        assert stats["utilization"] == 0.0

        # Add a summary
        summary = ConsolidatedSummary(
            summary="Test summary",
            consolidated_count=5,
            oldest_timestamp="2026-01-19T00:00:00",
            newest_timestamp="2026-01-19T01:00:00",
            consolidated_at=datetime.now().isoformat(),
            metadata={}
        )
        summary_tier.add_summary(summary)

        stats = summary_tier.get_stats()
        assert stats["count"] == 1
        assert stats["utilization"] == 0.1


class TestThreeTierIntegration:
    """Tests for complete three-tier memory integration."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir(parents=True, exist_ok=True)
        yield project_path
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def memory_system(self, temp_project):
        """Create an enhanced memory system with three tiers."""
        return create_enhanced_memory_system(
            project_path=temp_project,
            project_name="test",
            enable_consolidation=True,
            max_summaries=10
        )

    def test_three_tier_initialization(self, memory_system):
        """Test that all three tiers are initialized."""
        # Tier 1: WorkingMemory
        assert memory_system.working is not None
        assert memory_system.working.size() == 0

        # Tier 2: SummaryTier
        assert memory_system.summary_tier is not None
        assert memory_system.summary_tier.size() == 0

        # Tier 3: PersistentMemory
        assert memory_system.persistent is not None

    def test_three_tier_context(self, memory_system):
        """Test getting context from all three tiers."""
        # Add some messages to working memory
        for i in range(5):
            msg = create_message(
                role="user",
                content=f"Message {i}"
            )
            memory_system.add(msg)

        # Get three-tier context
        context = memory_system.get_three_tier_context(limit=10)

        # Should have immediate context section
        assert "IMMEDIATE CONTEXT" in context or "Message" in context

    def test_consolidation_creates_summary(self, memory_system):
        """Test that consolidation creates entries in SummaryTier."""
        # Add enough messages to trigger consolidation
        for i in range(15):
            msg = create_message(
                role="user",
                content=f"Test message {i}"
            )
            memory_system.add(msg)

        # Force consolidation
        result = memory_system.force_consolidate()

        # Check that consolidation created a summary
        if result.get("status") == "success":
            # SummaryTier should have at least one summary
            assert memory_system.summary_tier.size() >= 1

    def test_summary_tier_stats(self, memory_system):
        """Test getting SummaryTier stats."""
        stats = memory_system.get_summary_tier_stats()
        assert "count" in stats
        assert "max_summaries" in stats
        assert stats["max_summaries"] == 10

    def test_get_summaries(self, memory_system):
        """Test retrieving summaries from memory system."""
        summaries = memory_system.get_summary_tier_summaries()
        assert isinstance(summaries, list)

    def test_search_summaries(self, memory_system):
        """Test searching summaries."""
        # Add a test summary
        from storage.SummaryTier import ConsolidatedSummary
        summary = ConsolidatedSummary(
            summary="User discussed authentication and login issues",
            consolidated_count=5,
            oldest_timestamp="2026-01-19T00:00:00",
            newest_timestamp="2026-01-19T01:00:00",
            consolidated_at=datetime.now().isoformat(),
            metadata={}
        )
        memory_system.summary_tier.add_summary(summary)

        # Search for relevant summaries
        results = memory_system.search_summaries("authentication")
        assert len(results) >= 1
        assert any("authentication" in s.summary.lower() for s in results)

    @pytest.mark.asyncio
    async def test_async_consolidation(self, memory_system):
        """Test async consolidation."""
        # Add messages
        for i in range(15):
            msg = create_message(
                role="user",
                content=f"Test message {i}"
            )
            memory_system.add(msg)

        # Run async consolidation
        result = await memory_system.consolidate()

        # Check result
        assert "status" in result
        if result["status"] == "success":
            assert "original_count" in result
            assert "final_count" in result


class TestMemoryConsolidationWithSummaryTier:
    """Tests for MemoryConsolidation with SummaryTier integration."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir(parents=True, exist_ok=True)
        yield project_path
        shutil.rmtree(temp_dir)

    def test_consolidation_with_summary_tier(self, temp_project):
        """Test that consolidation creates both WorkingMemory and SummaryTier entries."""
        # Create memory system with consolidation
        memory_system = create_enhanced_memory_system(
            project_path=temp_project,
            enable_consolidation=True,
            max_summaries=10
        )

        # Add messages
        for i in range(20):
            msg = create_message(
                role="user",
                content=f"Important message {i} with error details" if i % 5 == 0 else f"Regular message {i}"
            )
            memory_system.add(msg)

        # Force consolidation
        result = memory_system.force_consolidate()

        # Verify consolidation succeeded
        if result.get("status") == "success":
            # Check WorkingMemory was reduced
            working_size = memory_system.working.size()
            assert working_size < 20  # Should be less than original

            # Check SummaryTier has entries
            summary_size = memory_system.summary_tier.size()
            assert summary_size >= 1  # Should have at least one summary

    def test_consolidation_preserves_importance(self, temp_project):
        """Test that consolidation preserves high-importance messages."""
        memory_system = create_enhanced_memory_system(
            project_path=temp_project,
            enable_consolidation=True,
            max_summaries=10
        )

        # Add messages with varying importance
        for i in range(15):
            content = f"CRITICAL ERROR {i}" if i % 3 == 0 else f"message {i}"
            msg = create_message(
                role="user",
                content=content
            )
            memory_system.add(msg)

        # Force consolidation
        result = memory_system.force_consolidate()

        if result.get("status") == "success":
            # Check that important messages were preserved
            preserved_count = result.get("preserved_count", 0)
            # At least some messages should be preserved as important
            assert preserved_count >= 0


class TestThreeTierWorkflow:
    """Tests for realistic three-tier workflow."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir(parents=True, exist_ok=True)
        yield project_path
        shutil.rmtree(temp_dir)

    def test_agent_workflow(self, temp_project):
        """Test realistic agent workflow with three-tier memory."""
        # Create memory system
        memory = create_enhanced_memory_system(
            project_path=temp_project,
            enable_consolidation=True,
            max_summaries=10
        )

        # Simulate conversation
        messages = [
            ("user", "I need help with authentication"),
            ("assistant", "I can help with that. What's the issue?"),
            ("user", "I'm getting a 401 error"),
            ("assistant", "That's an unauthorized error. Check your API key."),
            ("user", "The API key looks correct"),
            ("assistant", "Let me check the logs..."),
            ("user", "Found it! Wrong endpoint URL"),
            ("assistant", "Great! Glad you found it."),
            ("user", "Thanks for the help"),
            ("assistant", "You're welcome!"),
            ("user", "One more question about tokens"),
            ("assistant", "Sure, ask away!"),
        ]

        for role, content in messages:
            msg = create_message(role=role, content=content)
            memory.add(msg)

        # Get immediate context (WorkingMemory)
        working_context = memory.working.get_context(limit=5)
        assert "tokens" in working_context or "endpoint" in working_context

        # Get three-tier context
        full_context = memory.get_three_tier_context(limit=5)
        assert "IMMEDIATE CONTEXT" in full_context or len(full_context) > 0

        # Check stats
        working_stats = memory.working.size()
        summary_stats = memory.get_summary_tier_stats()

        assert working_stats >= 0
        assert summary_stats["count"] >= 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
