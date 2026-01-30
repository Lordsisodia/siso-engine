#!/usr/bin/env python3
"""
Obsidian Integration Demo
=========================

Demonstrates basic usage of the Obsidian integration.

Usage:
    python demo.py
"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from integration.obsidian import ObsidianExporter
from integration.obsidian.types import (
    ContextData,
    InsightData,
    PlanData,
    SessionData,
)


def main():
    """Run demo."""

    # For demo purposes, use a temporary directory
    # In production, use your actual Obsidian vault path
    vault_path = os.path.expanduser("~/Documents/ObsidianVault")
    demo_vault = os.path.expanduser("~/Documents/DemoObsidianVault")

    # Use demo vault if it exists or main vault if not
    actual_vault = demo_vault if os.path.exists(demo_vault) else vault_path

    print("Obsidian Integration Demo")
    print("=" * 60)
    print(f"Target vault: {actual_vault}")
    print()

    # Check if vault exists
    if not os.path.exists(actual_vault):
        print("Note: Vault directory doesn't exist. Creating for demo...")
        os.makedirs(actual_vault, exist_ok=True)

    # Initialize exporter
    print("1. Initializing ObsidianExporter...")
    exporter = ObsidianExporter(
        vault_path=actual_vault,
        create_folders=True,
    )
    print("   Exporter initialized")
    print()

    # Export a session
    print("2. Exporting an agent session...")
    session_data = SessionData(
        agent_id="agent_001",
        agent_name="ResearchAgent",
        session_id="sess_20250119_research",
        start_time=datetime.now() - timedelta(hours=2),
        end_time=datetime.now() - timedelta(hours=1),
        goal="Research best practices for Python API development",
        outcome="Identified 5 key patterns and created comprehensive documentation",
        steps=[
            {"title": "Literature Review", "description": "Reviewed 10 articles", "status": "complete"},
            {"title": "Code Analysis", "description": "Analyzed 5 repositories", "status": "complete"},
            {"title": "Documentation", "description": "Created summary report", "status": "complete"},
        ],
        tags=["research", "python", "api"],
        related_notes=["Python Best Practices", "API Design Patterns"],
    )

    session_result = exporter.export_session(session_data)
    if session_result.success:
        print(f"   Session exported: {session_result.file_path}")
    else:
        print(f"   Error: {session_result.error}")
    print()

    # Export an insight
    print("3. Exporting an insight...")
    insight_data = InsightData(
        title="Python Context Managers for Resource Management",
        content="""
Context managers are essential for proper resource management in Python.

## Key Benefits

1. **Automatic Cleanup**: Resources are always properly released
2. **Cleaner Code**: Reduces boilerplate for setup/teardown
3. **Exception Safety**: Guarantees cleanup even if errors occur

## Implementation Pattern

```python
from contextlib import contextmanager

@contextmanager
def managed_resource():
    # Setup
    resource = acquire_resource()
    try:
        yield resource
    finally:
        # Cleanup
        release_resource(resource)
```

## Best Practices

- Always use context managers for file I/O
- Use them for database connections
- Implement custom context managers for reusable setup/teardown logic
        """.strip(),
        category="Best Practice",
        source_session=session_data.session_id,
        tags=["python", "pattern", "resource-management"],
        related_notes=["Python Best Practices"],
    )

    insight_result = exporter.export_insight(insight_data)
    if insight_result.success:
        print(f"   Insight exported: {insight_result.file_path}")
    else:
        print(f"   Error: {insight_result.error}")
    print()

    # Export context
    print("4. Exporting agent context...")
    context_data = ContextData(
        agent_id="agent_001",
        agent_name="ResearchAgent",
        context_type="working",
        content="""
## Current State

The ResearchAgent is currently focused on Python development patterns.

## Active Projects

1. API Development Best Practices
2. Async/Await Patterns
3. Type Hints and Validation

## Memory Context

Recent interactions have focused on:
- FastAPI implementation patterns
- Pydantic for data validation
- Testing strategies for async code

## Next Steps

- Complete async patterns research
- Begin testing framework comparison
        """.strip(),
        tags=["agent", "research", "python"],
        related_notes=["Python Best Practices", "API Design Patterns"],
    )

    context_result = exporter.export_context(context_data)
    if context_result.success:
        print(f"   Context exported: {context_result.file_path}")
    else:
        print(f"   Error: {context_result.error}")
    print()

    # Export a plan
    print("5. Exporting a plan...")
    plan_data = PlanData(
        title="Python Async Patterns Research",
        description="Comprehensive research into async/await patterns in Python",
        status="planning",
        steps=[
            {
                "title": "Literature Review",
                "description": "Review Python async documentation and tutorials",
                "status": "pending",
            },
            {
                "title": "Code Analysis",
                "description": "Analyze real-world async implementations",
                "status": "pending",
            },
            {
                "title": "Pattern Catalog",
                "description": "Document common async patterns",
                "status": "pending",
            },
            {
                "title": "Performance Testing",
                "description": "Benchmark async vs sync approaches",
                "status": "pending",
            },
        ],
        tags=["research", "python", "async"],
        related_notes=["Python Best Practices"],
    )

    plan_result = exporter.export_plan(plan_data)
    if plan_result.success:
        print(f"   Plan exported: {plan_result.file_path}")
    else:
        print(f"   Error: {plan_result.error}")
    print()

    # Generate index
    print("6. Generating note index...")
    index_result = exporter.generate_index()
    if index_result.success:
        print(f"   Index created: {index_result.file_path}")
    else:
        print(f"   Error: {index_result.error}")
    print()

    print("Demo complete!")
    print()
    print("Summary:")
    print(f"  - Session: {'Exported' if session_result.success else 'Failed'}")
    print(f"  - Insight: {'Exported' if insight_result.success else 'Failed'}")
    print(f"  - Context: {'Exported' if context_result.success else 'Failed'}")
    print(f"  - Plan: {'Exported' if plan_result.success else 'Failed'}")
    print(f"  - Index: {'Generated' if index_result.success else 'Failed'}")
    print()
    print(f"Check your Obsidian vault at: {actual_vault}")
    print(f"Notes are in: blackbox5/ folder")


if __name__ == "__main__":
    main()
