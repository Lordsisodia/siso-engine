"""
Enhanced Production Memory System for BlackBox5

Extends ProductionMemorySystem with semantic retrieval and importance scoring.

Based on industry research from 2025-2026:
- mem0.ai: 90% token reduction through semantic retrieval
- Agentic RAG: Retrieve by relevance, not just recency
- REMem: Episodic memory with semantic indexing
- Importance scoring: Prioritize valuable memories over noise

Enhancements over base ProductionMemorySystem:
1. Semantic retrieval - find relevant past context by meaning
2. Importance scoring - prioritize valuable messages
3. Hybrid strategy - mix of recent + semantically relevant + important messages
4. Backward compatible - all existing code still works
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict, field
from collections import deque
import threading
import sqlite3
import sys
import os

# Import base classes
try:
    # Relative import from engine/memory/
    from .ProductionMemorySystem import (
        Message,
        WorkingMemory,
        PersistentMemory,
        ProductionMemorySystem
    )
    from .SummaryTier import SummaryTier, ConsolidatedSummary
    from .importance.ImportanceScorer import ImportanceScorer, ImportanceConfig
    from .consolidation.MemoryConsolidation import MemoryConsolidation, ConsolidationConfig
    from .episodic.EpisodicMemory import EpisodicMemory
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(Path(__file__).parent))
    from ProductionMemorySystem import (
        Message,
        WorkingMemory,
        PersistentMemory,
        ProductionMemorySystem
    )
    from SummaryTier import SummaryTier, ConsolidatedSummary
    from importance.ImportanceScorer import ImportanceScorer, ImportanceConfig
    from consolidation.MemoryConsolidation import MemoryConsolidation, ConsolidationConfig
    from episodic.EpisodicMemory import EpisodicMemory


@dataclass
class MemoryScore:
    """Score for a memory message"""
    message: Message
    relevance_score: float  # 0.0 to 1.0
    recency_score: float    # 0.0 to 1.0
    importance_score: float  # 0.0 to 1.0
    combined_score: float   # weighted combination


class SemanticWorkingMemory(WorkingMemory):
    """
    Enhanced working memory with semantic retrieval and importance scoring.

    Extends WorkingMemory with:
    - Semantic search integration
    - Importance scoring
    - Hybrid retrieval strategies
    - Relevance + importance + recency scoring
    """

    def __init__(self, max_messages: int = 100, importance_config: ImportanceConfig = None):
        super().__init__(max_messages)
        # Lazy load semantic search
        self._semantic_search = None
        # Initialize importance scorer
        self._importance_scorer = None
        self._importance_config = importance_config

    @property
    def semantic_search(self):
        """Lazy load semantic search service"""
        if self._semantic_search is None:
            try:
                # Import SemanticContextSearch
                semantic_search_path = (
                    Path(__file__).parent.parent.parent /
                    "memory" / "extended" / "services" / "semantic-search.py"
                )
                if semantic_search_path.exists():
                    # Add to path and import
                    import_path = str(semantic_search_path.parent.parent)
                    if import_path not in sys.path:
                        sys.path.insert(0, import_path)

                    from memory.extended.services.semantic_search import SemanticContextSearch
                    self._semantic_search = SemanticContextSearch()
            except Exception as e:
                # Semantic search not available, fall back to keyword matching
                print(f"Warning: Semantic search not available: {e}")
                self._semantic_search = False

        return self._semantic_search

    @property
    def importance_scorer(self):
        """Lazy load importance scorer"""
        if self._importance_scorer is None:
            self._importance_scorer = ImportanceScorer(self._importance_config)
        return self._importance_scorer

    def _calculate_importance_score(self, message: Message) -> float:
        """
        Calculate importance score for a message.

        Returns score between 0.0 and 1.0.
        """
        return self.importance_scorer.calculate_importance(
            role=message.role,
            content=message.content,
            timestamp=message.timestamp,
            metadata=getattr(message, 'metadata', None)
        )

    def _calculate_recency_score(self, message: Message) -> float:
        """
        Calculate recency score for a message.

        Recent messages (within last hour) get higher scores.
        Returns score between 0.0 and 1.0.
        """
        try:
            msg_time = datetime.fromisoformat(message.timestamp)
            hours_ago = (datetime.now() - msg_time).total_seconds() / 3600

            # Exponential decay: 1.0 at 0 hours, 0.5 at 1 hour, 0.1 at 3 hours
            score = 1.0 / (1.0 + hours_ago)
            return min(score, 1.0)
        except:
            return 0.5  # Default for unparseable timestamps

    def _calculate_keyword_relevance(
        self,
        query: str,
        message: Message
    ) -> float:
        """
        Calculate keyword-based relevance score.

        Simple fallback when semantic search is unavailable.
        Returns score between 0.0 and 1.0.
        """
        query_lower = query.lower()
        content_lower = message.content.lower()

        # Extract keywords from query
        query_words = set(query_lower.split())

        # Count matches
        matches = sum(1 for word in query_words if word in content_lower)

        # Score based on match ratio
        if len(query_words) == 0:
            return 0.0

        return min(matches / len(query_words), 1.0)

    def _calculate_semantic_relevance(
        self,
        query: str,
        message: Message
    ) -> float:
        """
        Calculate semantic relevance using SemanticContextSearch.

        Returns score between 0.0 and 1.0.
        """
        if not self.semantic_search:
            return self._calculate_keyword_relevance(query, message)

        try:
            # Search for relevant context
            results = self.semantic_search.search(query, max_results=100)

            # Check if this message appears in results
            # by looking for matching content in tasks, contexts, or timeline
            relevance = 0.0

            # Check tasks
            for task in results.get("relevant_tasks", []):
                if message.content.lower() in task.get("title", "").lower():
                    relevance = max(relevance, task.get("relevance_score", 0))
                if message.content.lower() in task.get("description", "").lower():
                    relevance = max(relevance, task.get("relevance_score", 0))

            # Check contexts
            for context in results.get("similar_contexts", []):
                if message.task_id == context.get("task_id"):
                    relevance = max(relevance, context.get("relevance_score", 0))

            return relevance

        except Exception as e:
            # Fall back to keyword matching
            return self._calculate_keyword_relevance(query, message)

    def get_messages(
        self,
        limit: Optional[int] = None,
        role: Optional[str] = None,
        task_id: Optional[str] = None,
        query: Optional[str] = None,
        strategy: str = "recent",
        min_importance: float = 0.0
    ) -> List[Message]:
        """
        Retrieve messages with optional filtering and semantic retrieval.

        Args:
            limit: Maximum number of messages to return
            role: Filter by role (user, assistant, system, tool)
            task_id: Filter by task ID
            query: Query string for semantic search
            strategy: Retrieval strategy
                - "recent": Most recent messages (default)
                - "semantic": Semantically relevant to query
                - "hybrid": Mix of recent (50%) + semantic (30%) + importance (20%)
                - "importance": Ranked by importance score only
            min_importance: Minimum importance threshold (0.0 to 1.0)

        Returns:
            List of messages sorted by relevance
        """
        with self._lock:
            all_messages = list(self._messages)

        # Apply basic filters
        if role:
            all_messages = [m for m in all_messages if m.role == role]
        if task_id:
            all_messages = [m for m in all_messages if m.task_id == task_id]

        # Consolidated single-pass filtering and scoring
        scored_messages = []

        for msg in all_messages:
            # Early exit: check minimum importance filter first (cheap calculation)
            if min_importance > 0:
                importance = self._calculate_importance_score(msg)
                if importance < min_importance:
                    continue
            else:
                importance = 0.0  # Placeholder, will calculate if needed

            # Calculate scores based on strategy
            if strategy == "recent" or not query:
                # For recent strategy, no scoring needed - use natural order
                continue

            elif strategy == "semantic":
                relevance = self._calculate_semantic_relevance(query, msg)
                if relevance > 0.1:  # Minimum relevance threshold
                    if min_importance == 0.0:
                        importance = self._calculate_importance_score(msg)
                    scored_messages.append(MemoryScore(
                        message=msg,
                        relevance_score=relevance,
                        recency_score=0.0,
                        importance_score=importance,
                        combined_score=relevance
                    ))

            elif strategy == "hybrid":
                recency = self._calculate_recency_score(msg)
                relevance = self._calculate_semantic_relevance(query, msg)
                if min_importance == 0.0:
                    importance = self._calculate_importance_score(msg)
                combined = (0.5 * recency) + (0.3 * relevance) + (0.2 * importance)
                scored_messages.append(MemoryScore(
                    message=msg,
                    relevance_score=relevance,
                    recency_score=recency,
                    importance_score=importance,
                    combined_score=combined
                ))

            elif strategy == "importance":
                if min_importance == 0.0:
                    importance = self._calculate_importance_score(msg)
                scored_messages.append(MemoryScore(
                    message=msg,
                    relevance_score=0.0,
                    recency_score=0.0,
                    importance_score=importance,
                    combined_score=importance
                ))

        # Return results based on strategy
        if strategy == "recent" or not query or strategy not in ["semantic", "hybrid", "importance"]:
            # Return recent messages in natural order
            messages = all_messages
            if limit:
                messages = messages[-limit:]
        else:
            # Sort by combined score and return top N
            scored_messages.sort(key=lambda x: x.combined_score, reverse=True)
            messages = [sm.message for sm in scored_messages[:limit]] if limit else [sm.message for sm in scored_messages]

        return messages

    def get_context(
        self,
        limit: int = 10,
        include_system: bool = True,
        query: Optional[str] = None,
        strategy: str = "recent"
    ) -> str:
        """
        Get formatted context for LLM consumption with semantic retrieval.

        Args:
            limit: Maximum number of messages to include
            include_system: Whether to include system messages
            query: Query for semantic retrieval
            strategy: Retrieval strategy (recent, semantic, hybrid)

        Returns:
            Formatted context string
        """
        messages = self.get_messages(
            limit=limit,
            query=query,
            strategy=strategy
        )

        context_parts = []
        for msg in messages:
            if not include_system and msg.role == 'system':
                continue
            context_parts.append(f"{msg.role}: {msg.content}")

        return "\n".join(context_parts)


class EnhancedProductionMemorySystem(ProductionMemorySystem):
    """
    Enhanced production memory system with three-tier hierarchy, semantic retrieval and importance scoring.

    Drop-in replacement for ProductionMemorySystem with additional features:
    - Three-tier memory hierarchy (WorkingMemory → SummaryTier → PersistentMemory)
    - Semantic memory retrieval
    - Importance scoring and filtering
    - Hybrid retrieval strategies (recency + relevance + importance)
    - Context-aware message selection

    Three-Tier Architecture:
    - Tier 1: WorkingMemory (last 10 messages, immediate context)
    - Tier 2: SummaryTier (last 10 consolidation cycles, mid-term context)
    - Tier 3: PersistentMemory (all messages, long-term storage)

    Usage:
        # Old API still works
        memory = EnhancedProductionMemorySystem(project_path)
        context = memory.get_context(limit=10)

        # New semantic retrieval with importance
        context = memory.get_context(
            query="authentication issues",
            limit=10,
            strategy="hybrid",
            min_importance=0.5
        )

        # Three-tier context (includes summaries)
        context = memory.get_three_tier_context(limit=10)
    """

    def __init__(
        self,
        project_path: Path,
        max_working_messages: int = 100,
        project_name: str = "default",
        importance_config: ImportanceConfig = None,
        enable_consolidation: bool = False,
        consolidation_config: ConsolidationConfig = None,
        enable_episodic: bool = False,
        max_summaries: int = 10  # SummaryTier configuration
    ):
        # Initialize parent
        super().__init__(project_path, max_working_messages, project_name)

        # Replace working memory with enhanced version
        self.working = SemanticWorkingMemory(
            max_messages=max_working_messages,
            importance_config=importance_config
        )

        # Initialize SummaryTier (middle tier)
        self.summary_tier = SummaryTier(max_summaries=max_summaries)

        # Initialize consolidation if enabled
        self._consolidation = None
        if enable_consolidation:
            self._consolidation = MemoryConsolidation(
                self,
                config=consolidation_config or ConsolidationConfig()
            )

        # Initialize episodic memory if enabled
        self._episodic = None
        if enable_episodic:
            episodic_path = self.memory_dir / "episodes"
            self._episodic = EpisodicMemory(storage_path=episodic_path)

    def add(self, message: Message) -> None:
        """
        Add message to both working and persistent memory.

        Triggers consolidation if enabled and threshold exceeded.

        Args:
            message: Message to add
        """
        # Add to both memories
        self.working.add_message(message)
        self.persistent.store_message(message)

        # Trigger consolidation if enabled
        if self._consolidation:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule consolidation in background
                    asyncio.create_task(self._consolidation.on_message_added(message))
                else:
                    # No loop running, skip async consolidation
                    pass
            except:
                # No event loop, skip
                pass

    async def consolidate(self) -> Dict[str, Any]:
        """
        Manually trigger memory consolidation.

        Returns:
            Consolidation result
        """
        if not self._consolidation:
            return {
                "status": "error",
                "message": "Consolidation not enabled"
            }

        return await self._consolidation.consolidate()

    def force_consolidate(self) -> Dict[str, Any]:
        """
        Force consolidation to run synchronously.

        Returns:
            Consolidation result
        """
        if not self._consolidation:
            return {
                "status": "error",
                "message": "Consolidation not enabled"
            }

        return self._consolidation.force_consolidate()

    def get_consolidation_stats(self) -> Dict[str, Any]:
        """
        Get consolidation statistics.

        Returns:
            Statistics dictionary
        """
        if not self._consolidation:
            return {
                "enabled": False
            }

        return self._consolidation.get_stats()

    # Episodic memory methods

    def create_episode(
        self,
        title: str,
        messages: List[Any] = None,
        description: str = ""
    ):
        """
        Create an episode from messages.

        Args:
            title: Episode title
            messages: List of messages (uses working memory if not provided)
            description: Optional description

        Returns:
            Created episode or None if episodic memory not enabled
        """
        if not self._episodic:
            return None

        # Use working memory messages if not provided
        if messages is None:
            messages = list(self.working._messages)

        if not messages:
            return None

        return self._episodic.create_episode(title, messages, description)

    def get_episode(self, episode_id: str):
        """
        Get an episode by ID.

        Args:
            episode_id: Episode ID

        Returns:
            Episode or None if not found
        """
        if not self._episodic:
            return None

        return self._episodic.get_episode(episode_id)

    def find_related_episodes(self, episode_id: str, limit: int = 5) -> List:
        """
        Find episodes related to the given episode.

        Args:
            episode_id: Episode ID
            limit: Maximum results

        Returns:
            List of related episodes
        """
        if not self._episodic:
            return []

        episode = self._episodic.get_episode(episode_id)
        if not episode:
            return []

        return self._episodic.find_related_episodes(episode, limit)

    def search_episodes(self, query: str, limit: int = 10) -> List:
        """
        Search for episodes by content.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching episodes
        """
        if not self._episodic:
            return []

        return self._episodic.search_episodes(query, limit)

    def get_episodes_for_task(self, task_id: str) -> List:
        """
        Get all episodes related to a task.

        Args:
            task_id: Task ID

        Returns:
            List of related episodes
        """
        if not self._episodic:
            return []

        return self._episodic.get_episodes_for_task(task_id)

    def get_recent_episodes(self, hours: int = 24, limit: int = 10) -> List:
        """
        Get episodes from the last N hours.

        Args:
            hours: Number of hours to look back
            limit: Maximum results

        Returns:
            List of recent episodes
        """
        if not self._episodic:
            return []

        return self._episodic.get_recent_episodes(hours, limit)

    def add_episode_outcome(self, episode_id: str, outcome: str) -> bool:
        """
        Add outcome to an episode.

        Args:
            episode_id: Episode ID
            outcome: Outcome description

        Returns:
            True if successful
        """
        if not self._episodic:
            return False

        return self._episodic.add_outcome(episode_id, outcome)

    def add_episode_lesson(self, episode_id: str, lesson: str) -> bool:
        """
        Add a learned lesson to an episode.

        Args:
            episode_id: Episode ID
            lesson: Lesson learned

        Returns:
            True if successful
        """
        if not self._episodic:
            return False

        return self._episodic.add_learned_lesson(episode_id, lesson)

    def get_episodic_stats(self) -> Dict[str, Any]:
        """
        Get episodic memory statistics.

        Returns:
            Statistics dictionary
        """
        if not self._episodic:
            return {
                "enabled": False
            }

        return self._episodic.get_stats()

    # Three-tier memory methods

    def get_three_tier_context(
        self,
        limit: int = 10,
        include_summaries: bool = True,
        query: Optional[str] = None,
        strategy: str = "recent",
        min_importance: float = 0.0
    ) -> str:
        """
        Get context from all three tiers (WorkingMemory → SummaryTier → PersistentMemory).

        This provides the full memory hierarchy:
        1. WorkingMemory: Last N messages (immediate context)
        2. SummaryTier: Last N consolidation summaries (mid-term context)
        3. PersistentMemory: All messages (long-term storage, optional)

        Args:
            limit: Maximum messages from WorkingMemory
            include_summaries: Include SummaryTier summaries
            query: Query for semantic retrieval
            strategy: Retrieval strategy (recent, semantic, hybrid)
            min_importance: Minimum importance threshold

        Returns:
            Formatted context string with all three tiers
        """
        context_parts = []

        # Tier 1: WorkingMemory (immediate context)
        working_context = self.working.get_context(
            limit=limit,
            include_system=False,
            query=query,
            strategy=strategy
        )
        if working_context:
            context_parts.append("=== IMMEDIATE CONTEXT (WorkingMemory) ===")
            context_parts.append(working_context)

        # Tier 2: SummaryTier (mid-term context)
        if include_summaries:
            summary_context = self.summary_tier.get_context_string()
            if summary_context:
                context_parts.append("\n=== MID-TERM CONTEXT (SummaryTier) ===")
                context_parts.append(summary_context)

        return "\n\n".join(context_parts)

    def get_summary_tier_stats(self) -> Dict[str, Any]:
        """
        Get SummaryTier statistics.

        Returns:
            Statistics dictionary
        """
        return self.summary_tier.get_stats()

    def get_summary_tier_summaries(
        self,
        limit: Optional[int] = None,
        after_timestamp: Optional[str] = None
    ) -> List[ConsolidatedSummary]:
        """
        Get summaries from SummaryTier.

        Args:
            limit: Maximum number of summaries
            after_timestamp: Only return summaries after this timestamp

        Returns:
            List of ConsolidatedSummary objects
        """
        return self.summary_tier.get_summaries(
            limit=limit,
            after_timestamp=after_timestamp
        )

    def search_summaries(self, query: str, limit: int = 5) -> List[ConsolidatedSummary]:
        """
        Search SummaryTier for relevant summaries.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of relevant ConsolidatedSummary objects
        """
        return self.summary_tier.find_relevant_summaries(query, limit)

    def get_context(
        self,
        limit: int = 10,
        include_persistent: bool = False,
        query: Optional[str] = None,
        strategy: str = "recent",
        min_importance: float = 0.0
    ) -> str:
        """
        Get context for LLM consumption with semantic retrieval and importance filtering.

        Args:
            limit: Maximum messages to include
            include_persistent: Include persistent memory messages
            query: Query for semantic retrieval (enables semantic strategies)
            strategy: Retrieval strategy
                - "recent": Most recent messages (default, backward compatible)
                - "semantic": Semantically relevant to query
                - "hybrid": Mix of recent (50%) + semantic (30%) + importance (20%)
                - "importance": Ranked by importance score only
            min_importance: Minimum importance threshold (0.0 to 1.0)

        Returns:
            Formatted context string
        """
        if include_persistent:
            # Combine working and persistent memory
            working_msgs = self.working.get_messages(
                limit=limit,
                query=query,
                strategy=strategy,
                min_importance=min_importance
            )

            # For persistent memory, we need to apply semantic filtering too
            if query and strategy in ["semantic", "hybrid"]:
                persistent_msgs = self._search_persistent(query, limit=limit)
            else:
                persistent_msgs = self.persistent.get_messages(limit=limit)

            # Apply importance filter to persistent messages
            if min_importance > 0:
                filtered_persistent = []
                for msg in persistent_msgs:
                    importance = self.working._calculate_importance_score(msg)
                    if importance >= min_importance:
                        filtered_persistent.append(msg)
                persistent_msgs = filtered_persistent

            # Deduplicate by hash
            seen = {m.get_hash() for m in working_msgs}
            unique_persistent = [m for m in persistent_msgs if m.get_hash() not in seen]

            # Merge and deduplicate
            all_msgs = working_msgs + unique_persistent

            # Remove duplicates while preserving order
            seen_hashes = set()
            unique_msgs = []
            for msg in all_msgs:
                h = msg.get_hash()
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    unique_msgs.append(msg)

            all_msgs = unique_msgs[:limit]

            context_parts = [f"{m.role}: {m.content}" for m in all_msgs]
            return "\n".join(context_parts)
        else:
            # Working memory only with semantic retrieval and importance filtering
            messages = self.working.get_messages(
                limit=limit,
                query=query,
                strategy=strategy,
                min_importance=min_importance
            )

            context_parts = []
            for msg in messages:
                if msg.role != 'system':  # Skip system messages by default
                    context_parts.append(f"{msg.role}: {msg.content}")

            return "\n".join(context_parts)

    def get_messages(
        self,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
        query: Optional[str] = None,
        strategy: str = "recent"
    ) -> List[Message]:
        """
        Get messages with optional filtering and semantic retrieval.

        Args:
            task_id: Filter by task ID
            agent_id: Filter by agent ID
            limit: Maximum messages to return
            query: Query for semantic retrieval
            strategy: Retrieval strategy

        Returns:
            List of messages
        """
        if task_id or agent_id:
            # For filtered queries, use persistent memory
            return self.persistent.get_messages(
                task_id=task_id,
                agent_id=agent_id,
                limit=limit
            )
        else:
            # Working memory with semantic retrieval
            return self.working.get_messages(
                limit=limit,
                query=query,
                strategy=strategy
            )

    def search(
        self,
        query: str,
        limit: int = 10,
        strategy: str = "hybrid"
    ) -> List[Message]:
        """
        Search for relevant messages.

        Args:
            query: Search query
            limit: Maximum results
            strategy: Search strategy (recent, semantic, hybrid)

        Returns:
            List of relevant messages
        """
        return self.working.get_messages(
            limit=limit,
            query=query,
            strategy=strategy
        )

    def _search_persistent(self, query: str, limit: int = 100) -> List[Message]:
        """
        Search persistent memory for relevant messages.

        Uses semantic search if available, otherwise keyword matching.
        """
        all_messages = self.persistent.get_messages(limit=1000)

        # Try semantic search first
        if self.working.semantic_search:
            try:
                results = self.working.semantic_search.search(query, max_results=limit)

                # Extract relevant task IDs and context
                relevant_task_ids = set()
                for task in results.get("relevant_tasks", []):
                    relevant_task_ids.add(task.get("id"))

                # Filter messages by relevance
                relevant_messages = []
                for msg in all_messages:
                    if msg.task_id in relevant_task_ids:
                        relevant_messages.append(msg)
                    elif query.lower() in msg.content.lower():
                        relevant_messages.append(msg)

                    if len(relevant_messages) >= limit:
                        break

                return relevant_messages[:limit]

            except Exception as e:
                print(f"Semantic search failed, falling back to keyword: {e}")

        # Fall back to keyword search
        query_lower = query.lower()
        results = [
            msg for msg in all_messages
            if query_lower in msg.content.lower()
        ][:limit]

        return results

    def get_semantic_summary(self, query: str) -> Dict[str, Any]:
        """
        Get semantic search summary for a query.

        Provides overview of relevant:
        - Tasks
        - Contexts
        - Artifacts
        - Expert agents

        Args:
            query: Search query

        Returns:
            Semantic search summary
        """
        if not self.working.semantic_search:
            return {
                "error": "Semantic search not available",
                "query": query
            }

        try:
            return self.working.semantic_search.search(query, max_results=10)
        except Exception as e:
            return {
                "error": f"Semantic search failed: {e}",
                "query": query
            }


# Enhanced convenience functions

def create_enhanced_memory_system(
    project_path: Path,
    project_name: str = "default",
    importance_config: ImportanceConfig = None,
    enable_consolidation: bool = False,
    consolidation_config: ConsolidationConfig = None,
    enable_episodic: bool = False,
    max_summaries: int = 10
) -> EnhancedProductionMemorySystem:
    """
    Get or create enhanced memory system for a project.

    Args:
        project_path: Path to project
        project_name: Name of project
        importance_config: Optional importance scoring configuration
        enable_consolidation: Enable automatic memory consolidation
        consolidation_config: Optional consolidation configuration
        enable_episodic: Enable episodic memory linking
        max_summaries: Maximum summaries in SummaryTier

    Returns:
        Enhanced production memory system with three-tier memory
    """
    return EnhancedProductionMemorySystem(
        project_path=project_path,
        project_name=project_name,
        importance_config=importance_config,
        enable_consolidation=enable_consolidation,
        consolidation_config=consolidation_config,
        enable_episodic=enable_episodic,
        max_summaries=max_summaries
    )


def get_memory_system(
    project_path: Path,
    project_name: str = "default",
    enhanced: bool = True,
    importance_config: ImportanceConfig = None,
    enable_consolidation: bool = False,
    consolidation_config: ConsolidationConfig = None,
    enable_episodic: bool = False,
    max_summaries: int = 10
) -> ProductionMemorySystem:
    """
    Get memory system (enhanced or base).

    Args:
        project_path: Path to project
        project_name: Name of project
        enhanced: Use enhanced system with semantic retrieval
        importance_config: Optional importance scoring configuration
        enable_consolidation: Enable automatic memory consolidation
        consolidation_config: Optional consolidation configuration
        enable_episodic: Enable episodic memory linking
        max_summaries: Maximum summaries in SummaryTier

    Returns:
        ProductionMemorySystem or EnhancedProductionMemorySystem
    """
    if enhanced:
        return create_enhanced_memory_system(
            project_path,
            project_name,
            importance_config,
            enable_consolidation,
            consolidation_config,
            enable_episodic,
            max_summaries
        )
    else:
        # Import base class
        from .ProductionMemorySystem import ProductionMemorySystem as BaseSystem
        return BaseSystem(project_path, project_name)
