#!/usr/bin/env python3
"""
Demonstration of AgentMemory System

Shows how to use the persistent memory system for BlackBox5 agents.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engine.memory.AgentMemory import AgentMemory


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def demo_basic_usage():
    """Demonstrate basic memory usage."""
    print_section("1. Basic Usage - Creating Memory")

    # Create memory for an agent
    memory = AgentMemory(agent_id="demo-agent")
    print(f"✓ Created memory for agent: {memory.agent_id}")
    print(f"  Memory path: {memory.memory_path}")

    # Add a session
    session_id = memory.add_session(
        task="Build user authentication feature",
        result="Successfully implemented login with JWT tokens",
        success=True,
        duration_seconds=180.5
    )
    print(f"\n✓ Added session: {session_id}")

    # Add insights
    memory.add_insight(
        "Use JWT tokens for stateless authentication",
        category="pattern",
        confidence=0.9
    )
    memory.add_insight(
        "Always validate JWT signature on each request",
        category="gotcha",
        confidence=1.0
    )
    memory.add_insight(
        "bcrypt is slower than SHA256 but more secure for passwords",
        category="discovery",
        confidence=0.8
    )
    print("✓ Added 3 insights (pattern, gotcha, discovery)")

    # Get context
    context = memory.get_context()
    print(f"\n✓ Retrieved context:")
    print(f"  - Patterns: {len(context['patterns'])}")
    print(f"  - Gotchas: {len(context['gotchas'])}")
    print(f"  - Discoveries: {len(context['discoveries'])}")

    return memory


def demo_persistence():
    """Demonstrate memory persistence across instances."""
    print_section("2. Persistence - Memory Survives Restart")

    # Create first instance
    memory1 = AgentMemory(agent_id="persistent-agent")
    memory1.add_session(
        task="Database migration",
        result="Migrated 1000 records successfully"
    )
    memory1.add_insight(
        "Always backup database before migration",
        category="pattern"
    )
    print("✓ Created memory1 and added data")

    # Create second instance (simulating restart)
    memory2 = AgentMemory(agent_id="persistent-agent")
    sessions = memory2.get_sessions()
    insights = memory2.get_insights()

    print(f"\n✓ Created memory2 (new instance)")
    print(f"  - Sessions loaded: {len(sessions)}")
    print(f"  - Insights loaded: {len(insights)}")
    print(f"  - Session task: {sessions[0]['task']}")
    print(f"  - Insight: {insights[0]['content']}")


def demo_search():
    """Demonstrate search functionality."""
    print_section("3. Search - Finding Relevant Insights")

    memory = AgentMemory(agent_id="search-agent")

    # Add various insights
    insights = [
        ("Use React hooks for state management", "pattern"),
        ("Python async/await for concurrent operations", "pattern"),
        ("TypeScript prevents type errors at compile time", "pattern"),
        ("Never commit secrets to git repository", "gotcha"),
        ("GraphQL provides flexible querying", "discovery"),
    ]

    for content, category in insights:
        memory.add_insight(content, category)

    print(f"✓ Added {len(insights)} insights")

    # Search for different topics
    searches = ["React", "TypeScript", "git", "concurrent"]
    for query in searches:
        results = memory.search_insights(query, limit=2)
        print(f"\n  Search '{query}': {len(results)} results")
        for result in results:
            print(f"    - {result['content'][:60]}...")


def demo_agent_isolation():
    """Demonstrate agent memory isolation."""
    print_section("4. Agent Isolation - Separate Memory Spaces")

    # Create two different agents
    frontend_agent = AgentMemory(agent_id="frontend-developer")
    backend_agent = AgentMemory(agent_id="backend-developer")

    # Each agent learns different things
    frontend_agent.add_insight(
        "Use React hooks for component state",
        category="pattern"
    )
    backend_agent.add_insight(
        "Use Flask blueprints for API modularization",
        category="pattern"
    )

    print("✓ frontend-agent learned React pattern")
    print("✓ backend-agent learned Flask pattern")

    # Verify isolation
    frontend_insights = frontend_agent.get_insights()
    backend_insights = backend_agent.get_insights()

    print(f"\n✓ Frontend insights: {len(frontend_insights)}")
    print(f"  Content: {frontend_insights[0]['content']}")

    print(f"\n✓ Backend insights: {len(backend_insights)}")
    print(f"  Content: {backend_insights[0]['content']}")

    print("\n✓ Agents have completely isolated memory!")


def demo_statistics():
    """Demonstrate statistics and reporting."""
    print_section("5. Statistics - Performance Tracking")

    memory = AgentMemory(agent_id="stats-agent")

    # Add various sessions
    sessions_data = [
        ("Task 1", "Success", True, 100),
        ("Task 2", "Failure", False, 50),
        ("Task 3", "Success", True, 150),
        ("Task 4", "Success", True, 120),
    ]

    for task, result, success, duration in sessions_data:
        memory.add_session(task, result, success, duration)

    # Add insights
    memory.add_insight("Pattern 1", "pattern")
    memory.add_insight("Gotcha 1", "gotcha")
    memory.add_insight("Discovery 1", "discovery")

    print("✓ Added 4 sessions and 3 insights")

    # Get statistics
    stats = memory.get_statistics()

    print(f"\n✓ Statistics:")
    print(f"  - Total sessions: {stats['total_sessions']}")
    print(f"  - Success rate: {stats['success_rate']:.1%}")
    print(f"  - Avg duration: {stats['avg_duration_seconds']:.1f}s")
    print(f"  - Total insights: {stats['total_insights']}")
    print(f"  - Insights by category:")
    for category, count in stats['insights_by_category'].items():
        if count > 0:
            print(f"    • {category}: {count}")


def demo_export_import():
    """Demonstrate memory export and import."""
    print_section("6. Export/Import - Memory Transfer")

    # Create memory and add data
    memory1 = AgentMemory(agent_id="export-agent")
    memory1.add_session("Export task", "Completed")
    memory1.add_insight("Exportable pattern", "pattern")

    print("✓ Created memory1 with data")

    # Export
    exported = memory1.export_memory()
    print(f"✓ Exported memory:")
    print(f"  - Sessions: {len(exported['sessions'])}")
    print(f"  - Insights: {len(exported['insights'])}")
    print(f"  - Statistics: {exported['statistics']['total_sessions']} sessions")

    # Import to new agent
    memory2 = AgentMemory(agent_id="import-agent")
    memory2.import_memory(exported, merge=False)

    print(f"\n✓ Imported to memory2")
    print(f"  - Sessions: {len(memory2.sessions)}")
    print(f"  - Insights: {len(memory2.insights)}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("  AgentMemory System Demonstration")
    print("  BlackBox5 Persistent Memory for AI Agents")
    print("=" * 60)

    try:
        demo_basic_usage()
        demo_persistence()
        demo_search()
        demo_agent_isolation()
        demo_statistics()
        demo_export_import()

        print_section("✓ All Demonstrations Complete")
        print("\n  Memory files created in:")
        print(f"  {Path.cwd()}/.blackbox5/data/memory/")
        print("\n  Each agent has its own isolated memory directory!")
        print()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
