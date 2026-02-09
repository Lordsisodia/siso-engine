#!/usr/bin/env python3
"""
Vibe Kanban Integration Demo
==============================

Demonstrates the Vibe Kanban integration with BlackBox5.
This shows the same patterns as CCPM's GitHub integration.
"""

import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from integration.vibe import (
    VibeKanbanManager,
    CardSpec,
    CardStatus,
    Column,
    STATUS_TO_COLUMN,
)


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"✅ {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"ℹ️  {message}")


async def demo_basic_operations():
    """Demonstrate basic card operations."""
    print_section("1. Basic Card Operations")

    # Initialize manager
    manager = VibeKanbanManager(
        api_url="http://localhost:3001",
        memory_path="/tmp/vibe_demo_memory",
    )

    print_info("VibeKanbanManager initialized")
    print_info(f"API URL: {manager.api_url}")
    print_info(f"Memory path: {manager.memory_path}")

    # Note: In a real scenario, you would create a card:
    # card = await manager.create_card(
    #     title="Fix authentication bug",
    #     description="Users cannot login",
    #     column=Column.DOING
    # )

    print_info("To create a real card, ensure Vibe Kanban is running:")
    print_info("  docker-compose -f docker-compose.vibe-kanban-local.yml up -d")

    await manager.close()


def demo_status_mapping():
    """Demonstrate status to column mapping."""
    print_section("2. Status to Column Mapping")

    print_info("Status to Column Mapping (CCPM pattern):")
    for status, column in STATUS_TO_COLUMN.items():
        print(f"  {status.value:15} → {column.value}")

    print_success("Status mapping maintains consistency across operations")


def demo_card_spec():
    """Demonstrate card specification."""
    print_section("3. Card Specification (CCPM-style)")

    spec = CardSpec(
        title="Implement OAuth2 authentication",
        description="Add Google and GitHub OAuth login",
        acceptance_criteria=[
            "User can login with Google",
            "User can login with GitHub",
            "Session persists across restarts",
            "Logout functionality works",
        ],
        labels=["priority:high", "type:feature"],
        epic_link="#123",
        spec_link="/docs/specs/auth.md",
        related_cards=[456, 789],
    )

    print_info("Card Specification:")
    print(f"  Title: {spec.title}")
    print(f"  Description: {spec.description}")
    print(f"  Acceptance Criteria: {len(spec.acceptance_criteria)} items")
    print(f"  Labels: {spec.labels}")
    print(f"  Epic: {spec.epic_link}")
    print(f"  Spec: {spec.spec_link}")
    print(f"  Related Cards: {spec.related_cards}")

    print_success("CardSpec follows CCPM structure")


async def demo_workflow():
    """Demonstrate complete workflow."""
    print_section("4. Complete Workflow")

    print_info("Typical workflow:")
    print("  1. Create card in backlog")
    print("  2. Move to doing (in_progress)")
    print("  3. Add progress comments")
    print("  4. Move to review (in_review)")
    print("  5. Move to done")

    print("\nCode example:")
    print("""
    manager = VibeKanbanManager()

    # Create in backlog
    card = await manager.create_card(
        title="Fix bug",
        description="Critical issue",
        column=Column.BACKLOG
    )

    # Start working
    card = await manager.update_card_status(
        card.id,
        CardStatus.IN_PROGRESS
    )

    # Add progress
    await manager.add_comment(
        card.id,
        "Implemented fix, testing now"
    )

    # Ready for review
    card = await manager.update_card_status(
        card.id,
        CardStatus.IN_REVIEW
    )

    # Complete
    card = await manager.update_card_status(
        card.id,
        CardStatus.DONE
    )
    """)

    print_success("Workflow mirrors GitHub Issues pattern")


def demo_sync_patterns():
    """Demonstrate CCPM sync patterns."""
    print_section("5. CCPM Sync Patterns")

    print_info("Incremental Sync (prevents duplicate comments):")
    print("  - Only posts if there's new content")
    print("  - Tracks last sync timestamp")
    print("  - Checks file modification time")

    print("\nMemory Integration:")
    print("  - Stores card context in working memory")
    print("  - Tracks progress in markdown files")
    print("  - Maintains sync markers")

    print("\nProgress Comments:")
    print("  - Structured CCPM format")
    print("  - Includes completed/in-progress sections")
    print("  - Adds timestamps and metadata")

    print_success("Follows proven CCPM sync patterns")


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("  VIBE KANBAN INTEGRATION DEMO")
    print("  BlackBox5 + CCPM Patterns")
    print("=" * 60)

    await demo_basic_operations()
    demo_status_mapping()
    demo_card_spec()
    await demo_workflow()
    demo_sync_patterns()

    print_section("Summary")
    print_success("VibeKanbanManager created successfully")
    print_info("Location: .blackbox5/integration/vibe/VibeKanbanManager.py")
    print_info("Test file: .blackbox5/tests/test_vibe_integration.py")
    print_info("Documentation: .blackbox5/integration/vibe/README.md")

    print("\n🎯 Key Features:")
    print("  ✓ Create cards in different columns")
    print("  ✓ Move cards between columns")
    print("  ✓ Update status with automatic column mapping")
    print("  ✓ Add comments to cards")
    print("  ✓ CCPM-style incremental sync")
    print("  ✓ Local memory integration")

    print("\n📚 Next Steps:")
    print("  1. Start Vibe Kanban: docker-compose -f docker-compose.vibe-kanban-local.yml up -d")
    print("  2. Run tests: pytest .blackbox5/tests/test_vibe_integration.py")
    print("  3. Read docs: .blackbox5/integration/vibe/README.md")

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
