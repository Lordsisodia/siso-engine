"""
SummaryTier - Three-Tier Memory Layer

This is the middle tier in the three-tier memory hierarchy:
- Tier 1: WorkingMemory (recent messages, detailed)
- Tier 2: SummaryTier (consolidated summaries, mid-term) ⭐ THIS
- Tier 3: PersistentMemory (all messages, long-term)

Based on research from:
- MemoryOS (2025) - Three-tier hierarchy
- MemGPT - OS-inspired memory management
- H-MEM - Hierarchical memory for agents

Updated: 2026-01-19
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from collections import deque
import threading
import json


@dataclass
class ConsolidatedSummary:
    """
    A consolidated summary from memory consolidation.

    Contains:
    - Summary of consolidated messages
    - Metadata about the consolidation
    - Timestamp information
    """
    summary: str
    consolidated_count: int
    oldest_timestamp: str
    newest_timestamp: str
    consolidated_at: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConsolidatedSummary':
        return cls(**data)


class SummaryTier:
    """
    SummaryTier - Middle layer of three-tier memory hierarchy.

    Stores the last N consolidation cycles as summaries.
    Provides fast access to mid-term memory without hitting persistent storage.

    Pattern:
    - WorkingMemory: Last 10 messages (immediate context)
    - SummaryTier: Last 10 summaries (mid-term context)
    - PersistentMemory: All messages ever (long-term storage)

    Benefits:
    - Faster than querying persistent storage
    - Compressed (saves tokens)
    - Maintains conversation thread
    - Research-validated approach
    """

    def __init__(self, max_summaries: int = 10):
        """
        Initialize SummaryTier.

        Args:
            max_summaries: Maximum number of summaries to keep (default: 10)
                           When exceeded, oldest summary is removed.
        """
        self.max_summaries = max_summaries
        self._summaries: deque[ConsolidatedSummary] = deque(maxlen=max_summaries)
        self._lock = threading.Lock()

    def add_summary(self, summary: ConsolidatedSummary) -> None:
        """
        Add a consolidated summary to the summary tier.

        Args:
            summary: ConsolidatedSummary to add
        """
        with self._lock:
            self._summaries.append(summary)

    def get_summaries(
        self,
        limit: Optional[int] = None,
        after_timestamp: Optional[str] = None
    ) -> List[ConsolidatedSummary]:
        """
        Retrieve summaries from the summary tier.

        Args:
            limit: Maximum number of summaries to return
            after_timestamp: Only return summaries after this timestamp

        Returns:
            List of ConsolidatedSummary objects
        """
        with self._lock:
            summaries = list(self._summaries)

        # Filter by timestamp if specified
        if after_timestamp:
            summaries = [
                s for s in summaries
                if s.consolidated_at > after_timestamp
            ]

        # Apply limit
        if limit:
            summaries = summaries[-limit:]

        return summaries

    def get_latest_summary(self) -> Optional[ConsolidatedSummary]:
        """
        Get the most recent summary.

        Returns:
            Latest ConsolidatedSummary or None if empty
        """
        with self._lock:
            if self._summaries:
                return self._summaries[-1]
        return None

    def get_context_string(self, limit: Optional[int] = None) -> str:
        """
        Get formatted context string from summaries.

        Args:
            limit: Maximum number of summaries to include

        Returns:
            Formatted context string for LLM consumption
        """
        summaries = self.get_summaries(limit=limit)

        if not summaries:
            return ""

        context_parts = []
        for i, summary in enumerate(summaries, 1):
            context_parts.append(
                f"[CONSOLIDATED SUMMARY {i}] "
                f"({summary.consolidated_count} messages from {summary.oldest_timestamp} to {summary.newest_timestamp})\n"
                f"{summary.summary}"
            )

        return "\n\n".join(context_parts)

    def size(self) -> int:
        """
        Get current number of summaries.

        Returns:
            Number of summaries currently stored
        """
        with self._lock:
            return len(self._summaries)

    def clear(self) -> None:
        """
        Clear all summaries from the summary tier.
        """
        with self._lock:
            self._summaries.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the summary tier.

        Returns:
            Dictionary with statistics
        """
        with self._lock:
            if not self._summaries:
                return {
                    "count": 0,
                    "max_summaries": self.max_summaries,
                    "utilization": 0.0
                }

            # Calculate stats
            total_consolidated = sum(s.consolidated_count for s in self._summaries)

            return {
                "count": len(self._summaries),
                "max_summaries": self.max_summaries,
                "utilization": len(self._summaries) / self.max_summaries,
                "total_messages_consolidated": total_consolidated,
                "oldest_summary": self._summaries[0].consolidated_at,
                "newest_summary": self._summaries[-1].consolidated_at,
            }

    def find_relevant_summaries(
        self,
        query: str,
        limit: int = 5
    ) -> List[ConsolidatedSummary]:
        """
        Find summaries relevant to a query (simple keyword matching).

        Note: This is a simple implementation. For advanced semantic search,
        integrate with vector embeddings when available.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of relevant ConsolidatedSummary objects
        """
        summaries = self.get_summaries()
        query_lower = query.lower()

        # Simple keyword matching
        scored = []
        for summary in summaries:
            score = 0.0

            # Check summary content
            if query_lower in summary.summary.lower():
                score += 1.0

            # Check metadata
            metadata_str = str(summary.metadata).lower()
            if query_lower in metadata_str:
                score += 0.5

            if score > 0:
                scored.append((score, summary))

        # Sort by score and return top N
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:limit]]

    def to_dict_list(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Convert summaries to list of dictionaries.

        Args:
            limit: Maximum number of summaries to convert

        Returns:
            List of dictionaries
        """
        summaries = self.get_summaries(limit=limit)
        return [s.to_dict() for s in summaries]


def create_summary_from_messages(
    messages: List,
    summary_text: str,
    consolidated_at: Optional[str] = None
) -> ConsolidatedSummary:
    """
    Create a ConsolidatedSummary from a list of messages.

    Args:
        messages: List of messages that were consolidated
        summary_text: Generated summary text
        consolidated_at: When consolidation happened (default: now)

    Returns:
        ConsolidatedSummary object
    """
    if not messages:
        return ConsolidatedSummary(
            summary=summary_text,
            consolidated_count=0,
            oldest_timestamp="",
            newest_timestamp="",
            consolidated_at=consolidated_at or datetime.now().isoformat(),
            metadata={}
        )

    # Get timestamp range
    timestamps = [m.timestamp for m in messages if hasattr(m, 'timestamp')]
    if timestamps:
        oldest = min(timestamps)
        newest = max(timestamps)
    else:
        oldest = datetime.now().isoformat()
        newest = datetime.now().isoformat()

    # Extract metadata
    task_ids = list(set(m.task_id for m in messages if hasattr(m, 'task_id') and m.task_id))
    agent_ids = list(set(m.agent_id for m in messages if hasattr(m, 'agent_id') and m.agent_id))

    return ConsolidatedSummary(
        summary=summary_text,
        consolidated_count=len(messages),
        oldest_timestamp=oldest,
        newest_timestamp=newest,
        consolidated_at=consolidated_at or datetime.now().isoformat(),
        metadata={
            "task_ids": task_ids,
            "agent_ids": agent_ids,
            "message_count": len(messages)
        }
    )


# Convenience functions

def create_summary_tier(max_summaries: int = 10) -> SummaryTier:
    """
    Create a SummaryTier instance.

    Args:
        max_summaries: Maximum number of summaries to keep

    Returns:
        SummaryTier instance
    """
    return SummaryTier(max_summaries=max_summaries)


def get_summary_tier_stats(summary_tier: SummaryTier) -> Dict[str, Any]:
    """
    Get statistics from a SummaryTier.

    Args:
        summary_tier: SummaryTier instance

    Returns:
        Statistics dictionary
    """
    return summary_tier.get_stats()


# Example usage
if __name__ == "__main__":
    # Create summary tier
    summary_tier = create_summary_tier(max_summaries=10)

    # Add some test summaries
    from ProductionMemorySystem import create_message

    messages = [
        create_message(role="user", content="Hello"),
        create_message(role="assistant", content="Hi there!"),
    ]

    summary = create_summary_from_messages(
        messages,
        "User greeted assistant"
    )

    summary_tier.add_summary(summary)

    # Check stats
    print("SummaryTier Stats:")
    print(json.dumps(summary_tier.get_stats(), indent=2))

    # Get context
    print("\nContext:")
    print(summary_tier.get_context_string())
