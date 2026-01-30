#!/usr/bin/env python3
"""
Memory System

Persists learnings, decisions, and insights across runs.
Simple file-based memory (no external dependencies).
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import json
import yaml


class MemorySystem:
    """
    Simple file-based memory system for Legacy.

    Stores:
    - Decisions: Why we made choices
    - Insights: Patterns learned
    - Context: Summaries of loaded context
    """

    def __init__(self, memory_base_path: Optional[Path] = None):
        """
        Initialize memory system.

        Args:
            memory_base_path: Path to memory folder (default: .Autonomous/memory)
        """
        if memory_base_path is None:
            script_dir = Path(__file__).parent.parent
            memory_base_path = script_dir / "memory"

        self.base_path = memory_base_path
        self.decisions_path = self.base_path / "decisions"
        self.insights_path = self.base_path / "insights"
        self.context_path = self.base_path / "context"

        # Ensure directories exist
        self.decisions_path.mkdir(parents=True, exist_ok=True)
        self.insights_path.mkdir(parents=True, exist_ok=True)
        self.context_path.mkdir(parents=True, exist_ok=True)

    def record_decision(
        self,
        title: str,
        context: str,
        options: List[str],
        decision: str,
        rationale: str,
        run_id: Optional[str] = None
    ) -> Path:
        """
        Record a decision.

        Args:
            title: Short decision title
            context: What was the situation
            options: What options were considered
            decision: What was decided
            rationale: Why this decision
            run_id: Associated run

        Returns:
            Path to decision file
        """
        timestamp = datetime.now(timezone.utc)
        decision_id = f"DEC-{timestamp.strftime('%Y%m%d-%H%M%S')}"

        decision_data = {
            "id": decision_id,
            "title": title,
            "date": timestamp.isoformat(),
            "run_id": run_id,
            "context": context,
            "options_considered": options,
            "decision": decision,
            "rationale": rationale
        }

        file_path = self.decisions_path / f"{decision_id}.md"

        # Write as markdown for readability
        content = f"""# Decision: {title}

**ID:** {decision_id}
**Date:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC
**Run:** {run_id or 'N/A'}

## Context

{context}

## Options Considered

"""
        for i, option in enumerate(options, 1):
            content += f"{i}. {option}\n"

        content += f"""
## Decision

{decision}

## Rationale

{rationale}

---

*Recorded by Legacy Memory System*
"""

        file_path.write_text(content)
        return file_path

    def record_insight(
        self,
        content: str,
        category: str = "pattern",
        confidence: float = 1.0,
        source_run: Optional[str] = None,
        related_files: Optional[List[str]] = None
    ) -> Path:
        """
        Record an insight or learned pattern.

        Args:
            content: The insight content
            category: Type (pattern, gotcha, optimization, discovery)
            confidence: How confident (0.0 to 1.0)
            source_run: Which run this came from
            related_files: Files this insight relates to

        Returns:
            Path to insight file
        """
        timestamp = datetime.now(timezone.utc)
        insight_id = f"INSIGHT-{timestamp.strftime('%Y%m%d-%H%M%S')}"

        insight_data = {
            "id": insight_id,
            "date": timestamp.isoformat(),
            "category": category,
            "confidence": confidence,
            "source_run": source_run,
            "content": content,
            "related_files": related_files or []
        }

        file_path = self.insights_path / f"{insight_id}.md"

        # Write as markdown
        md_content = f"""# Insight: {category.title()}

**ID:** {insight_id}
**Date:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC
**Category:** {category}
**Confidence:** {confidence:.0%}
**Source:** {source_run or 'N/A'}

## Content

{content}

"""
        if related_files:
            md_content += "## Related Files\n\n"
            for f in related_files:
                md_content += f"- `{f}`\n"

        md_content += """
---

*Recorded by Legacy Memory System*
"""

        file_path.write_text(md_content)
        return file_path

    def save_context_summary(
        self,
        name: str,
        summary: str,
        source_files: List[str],
        run_id: Optional[str] = None
    ) -> Path:
        """
        Save a summary of loaded context.

        Args:
            name: Name of the context (e.g., "PRD-user-profile")
            summary: Summarized content
            source_files: Original files summarized
            run_id: Associated run

        Returns:
            Path to context file
        """
        timestamp = datetime.now(timezone.utc)

        context_data = {
            "name": name,
            "date": timestamp.isoformat(),
            "run_id": run_id,
            "summary": summary,
            "source_files": source_files
        }

        file_path = self.context_path / f"{name}.yaml"
        file_path.write_text(yaml.dump(context_data, default_flow_style=False))

        return file_path

    def get_recent_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent decisions."""
        decisions = []

        for file_path in sorted(self.decisions_path.glob("DEC-*.md"), reverse=True)[:limit]:
            # Parse markdown to extract key info
            content = file_path.read_text()

            decision = {
                "id": file_path.stem,
                "file": str(file_path),
                "title": "",
                "date": ""
            }

            # Extract title
            if "# Decision:" in content:
                decision["title"] = content.split("# Decision:")[1].split("\n")[0].strip()

            # Extract date
            if "**Date:**" in content:
                decision["date"] = content.split("**Date:**")[1].split("  ")[0].strip()

            decisions.append(decision)

        return decisions

    def get_insights_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get insights filtered by category."""
        insights = []

        for file_path in self.insights_path.glob("INSIGHT-*.md"):
            content = file_path.read_text()

            # Check category
            if f"**Category:** {category}" in content:
                insight = {
                    "id": file_path.stem,
                    "file": str(file_path),
                    "category": category,
                    "content": ""
                }

                # Extract content
                if "## Content" in content:
                    insight["content"] = content.split("## Content")[1].split("---")[0].strip()

                insights.append(insight)

        return insights

    def search_memories(self, query: str) -> Dict[str, List[Path]]:
        """
        Simple search across all memories.

        Args:
            query: Search term

        Returns:
            Dictionary of memory type -> matching files
        """
        results = {
            "decisions": [],
            "insights": [],
            "context": []
        }

        query_lower = query.lower()

        # Search decisions
        for file_path in self.decisions_path.glob("*.md"):
            if query_lower in file_path.read_text().lower():
                results["decisions"].append(file_path)

        # Search insights
        for file_path in self.insights_path.glob("*.md"):
            if query_lower in file_path.read_text().lower():
                results["insights"].append(file_path)

        # Search context
        for file_path in self.context_path.glob("*.yaml"):
            if query_lower in file_path.read_text().lower():
                results["context"].append(file_path)

        return results


def create_memory() -> MemorySystem:
    """Create a memory system instance."""
    return MemorySystem()


if __name__ == "__main__":
    # Test
    memory = create_memory()

    # Record a decision
    decision_file = memory.record_decision(
        title="Use YAML over JSON for config",
        context="Need to choose config format for task tracking",
        options=["JSON", "YAML", "TOML"],
        decision="Use YAML",
        rationale="Human readable, supports comments, widely used",
        run_id="run-001"
    )
    print(f"Recorded decision: {decision_file}")

    # Record an insight
    insight_file = memory.record_insight(
        content="Always validate task dependencies before starting",
        category="pattern",
        confidence=0.95,
        source_run="run-001"
    )
    print(f"Recorded insight: {insight_file}")

    # Get recent decisions
    print("\nRecent decisions:")
    for d in memory.get_recent_decisions():
        print(f"  - {d['id']}: {d['title']}")
