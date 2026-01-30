"""
Episodic Memory Management for BlackBox5

Based on industry research from 2025-2026:
- REMem framework: Two-phase episodic construction
- Link related tasks, decisions, outcomes
- Enable "what happened when we did X?" queries

This module provides:
1. Episode creation and management
2. Episode relationship tracking
3. Cross-episode queries
4. Temporal episode organization
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from dataclasses import asdict
from threading import Lock
import re

try:
    from .Episode import Episode
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from Episode import Episode


class EpisodicMemory:
    """
    Manages episodes and their relationships.

    Provides:
    - Episode creation from messages
    - Relationship tracking
    - Cross-episode search
    - Temporal queries
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize episodic memory.

        Args:
            storage_path: Path to store episode data (optional)
        """
        self.storage_path = storage_path
        self._lock = Lock()

        # Episode storage
        self.episodes: Dict[str, Episode] = {}
        self.message_to_episode: Dict[str, str] = {}  # Message hash → Episode ID
        self.task_to_episodes: Dict[str, Set[str]] = {}  # Task ID → Set of Episode IDs

        # Load existing episodes if storage path provided
        if storage_path and storage_path.exists():
            self._load_episodes()

    def create_episode(
        self,
        title: str,
        messages: List[Any],
        description: str = ""
    ) -> Episode:
        """
        Create a new episode from messages.

        Args:
            title: Episode title
            messages: List of messages
            description: Optional description

        Returns:
            Created Episode
        """
        if not messages:
            raise ValueError("Cannot create episode from empty message list")

        episode = Episode.create(title, messages, description)

        with self._lock:
            # Store episode
            self.episodes[episode.id] = episode

            # Index messages
            for msg in messages:
                if hasattr(msg, 'get_hash'):
                    msg_hash = msg.get_hash()
                    self.message_to_episode[msg_hash] = episode.id

            # Index tasks
            for task_id in episode.task_ids:
                if task_id not in self.task_to_episodes:
                    self.task_to_episodes[task_id] = set()
                self.task_to_episodes[task_id].add(episode.id)

            # Auto-link related episodes
            self._auto_link_episode(episode)

            # Save if storage path provided
            if self.storage_path:
                self._save_episode(episode)

        return episode

    def get_episode(self, episode_id: str) -> Optional[Episode]:
        """
        Get an episode by ID.

        Args:
            episode_id: Episode ID

        Returns:
            Episode or None if not found
        """
        return self.episodes.get(episode_id)

    def get_episodes_for_task(self, task_id: str) -> List[Episode]:
        """
        Get all episodes related to a task.

        Args:
            task_id: Task ID

        Returns:
            List of related episodes
        """
        episode_ids = self.task_to_episodes.get(task_id, set())
        return [self.episodes[eid] for eid in episode_ids if eid in self.episodes]

    def get_episodes_for_message(self, message) -> Optional[Episode]:
        """
        Get the episode containing a message.

        Args:
            message: Message object

        Returns:
            Episode or None if not found
        """
        if not hasattr(message, 'get_hash'):
            return None

        msg_hash = message.get_hash()
        episode_id = self.message_to_episode.get(msg_hash)

        if episode_id:
            return self.episodes.get(episode_id)

        return None

    def find_related_episodes(
        self,
        episode: Episode,
        limit: int = 5
    ) -> List[Episode]:
        """
        Find episodes related to this one.

        Args:
            episode: Episode to find relations for
            limit: Maximum number of results

        Returns:
            List of related episodes sorted by similarity
        """
        related = []

        for other_id, other in self.episodes.items():
            if other_id == episode.id:
                continue

            # Check explicit links
            if other_id in episode.related_episodes:
                related.append((1.0, other))  # Explicit links get highest score
                continue

            # Calculate similarity
            similarity = self._calculate_similarity(episode, other)
            if similarity > 0.3:  # Minimum similarity threshold
                related.append((similarity, other))

        # Sort by similarity and return top N
        related.sort(key=lambda x: x[0], reverse=True)
        return [ep for score, ep in related[:limit]]

    def search_episodes(
        self,
        query: str,
        limit: int = 10
    ) -> List[Episode]:
        """
        Search for episodes by content.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching episodes
        """
        query_lower = query.lower()
        scored = []

        for episode in self.episodes.values():
            score = 0.0

            # Match in title
            if query_lower in episode.title.lower():
                score += 0.5

            # Match in description
            if episode.description and query_lower in episode.description.lower():
                score += 0.3

            # Match in outcome
            if episode.outcome and query_lower in episode.outcome.lower():
                score += 0.4

            # Match in messages
            for msg in episode.messages:
                if hasattr(msg, 'content') and query_lower in msg.content.lower():
                    score += 0.1
                    break  # Only count once per episode

            # Match in lessons
            for lesson in episode.learned_lessons:
                if query_lower in lesson.lower():
                    score += 0.3
                    break

            if score > 0:
                scored.append((score, episode))

        # Sort by score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for score, ep in scored[:limit]]

    def get_recent_episodes(
        self,
        hours: int = 24,
        limit: int = 10
    ) -> List[Episode]:
        """
        Get episodes from the last N hours.

        Args:
            hours: Number of hours to look back
            limit: Maximum results

        Returns:
            List of recent episodes
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = []

        for episode in self.episodes.values():
            try:
                end_time = datetime.fromisoformat(episode.end_time)
                if end_time >= cutoff:
                    recent.append(episode)
            except:
                pass

        # Sort by end time (newest first)
        recent.sort(key=lambda e: e.end_time, reverse=True)
        return recent[:limit]

    def link_episodes(self, episode_id_1: str, episode_id_2: str) -> bool:
        """
        Link two episodes as related.

        Args:
            episode_id_1: First episode ID
            episode_id_2: Second episode ID

        Returns:
            True if successful
        """
        if episode_id_1 not in self.episodes or episode_id_2 not in self.episodes:
            return False

        ep1 = self.episodes[episode_id_1]
        ep2 = self.episodes[episode_id_2]

        # Add bidirectional links
        if episode_id_2 not in ep1.related_episodes:
            ep1.related_episodes.append(episode_id_2)

        if episode_id_1 not in ep2.related_episodes:
            ep2.related_episodes.append(episode_id_1)

        # Save changes
        if self.storage_path:
            self._save_episode(ep1)
            self._save_episode(ep2)

        return True

    def add_outcome(self, episode_id: str, outcome: str) -> bool:
        """
        Add outcome to an episode.

        Args:
            episode_id: Episode ID
            outcome: Outcome description

        Returns:
            True if successful
        """
        episode = self.episodes.get(episode_id)
        if not episode:
            return False

        episode.outcome = outcome

        if self.storage_path:
            self._save_episode(episode)

        return True

    def add_learned_lesson(self, episode_id: str, lesson: str) -> bool:
        """
        Add a learned lesson to an episode.

        Args:
            episode_id: Episode ID
            lesson: Lesson learned

        Returns:
            True if successful
        """
        episode = self.episodes.get(episode_id)
        if not episode:
            return False

        episode.add_lesson(lesson)

        if self.storage_path:
            self._save_episode(episode)

        return True

    def _calculate_similarity(self, ep1: Episode, ep2: Episode) -> float:
        """
        Calculate similarity between two episodes.

        Returns score between 0.0 and 1.0.
        """
        similarity = 0.0

        # Same task IDs
        tasks1 = set(ep1.task_ids)
        tasks2 = set(ep2.task_ids)

        if tasks1 and tasks2:
            intersection = tasks1 & tasks2
            union = tasks1 | tasks2
            if union:
                similarity += 0.5 * (len(intersection) / len(union))

        # Similar keywords in titles
        words1 = set(self._extract_keywords(ep1.title))
        words2 = set(self._extract_keywords(ep2.title))

        if words1 and words2:
            intersection = words1 & words2
            if intersection:
                similarity += 0.3 * (len(intersection) / min(len(words1), len(words2)))

        # Time proximity (episodes close in time might be related)
        try:
            end1 = datetime.fromisoformat(ep1.end_time)
            end2 = datetime.fromisoformat(ep2.end_time)
            hours_diff = abs((end1 - end2).total_seconds() / 3600)

            if hours_diff < 1:  # Within 1 hour
                similarity += 0.2
            elif hours_diff < 24:  # Within 1 day
                similarity += 0.1
        except:
            pass

        return min(similarity, 1.0)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple word extraction, filtering common words
        words = re.findall(r'\w+', text.lower())

        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is'
        }

        return [w for w in words if len(w) > 3 and w not in stop_words]

    def _auto_link_episode(self, episode: Episode) -> None:
        """Automatically link episode to related existing episodes."""
        # Find similar episodes and link them
        similar = self.find_related_episodes(episode, limit=3)

        for other in similar:
            if other.id not in episode.related_episodes:
                episode.related_episodes.append(other.id)

    def _save_episode(self, episode: Episode) -> None:
        """Save episode to storage."""
        if not self.storage_path:
            return

        self.storage_path.mkdir(parents=True, exist_ok=True)

        episode_file = self.storage_path / f"{episode.id}.json"
        with open(episode_file, 'w') as f:
            json.dump(episode.to_dict(), f, indent=2)

    def _load_episodes(self) -> None:
        """Load episodes from storage."""
        if not self.storage_path or not self.storage_path.exists():
            return

        for episode_file in self.storage_path.glob("*.json"):
            try:
                with open(episode_file, 'r') as f:
                    data = json.load(f)
                    episode = Episode.from_dict(data)

                    # Restore to memory
                    self.episodes[episode.id] = episode

                    # Rebuild indexes
                    for msg in episode.messages:
                        if hasattr(msg, 'get_hash'):
                            self.message_to_episode[msg.get_hash()] = episode.id

                    for task_id in episode.task_ids:
                        if task_id not in self.task_to_episodes:
                            self.task_to_episodes[task_id] = set()
                        self.task_to_episodes[task_id].add(episode.id)
            except Exception as e:
                print(f"Failed to load episode from {episode_file}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get episodic memory statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_episodes": len(self.episodes),
            "indexed_messages": len(self.message_to_episode),
            "indexed_tasks": len(self.task_to_episodes),
            "recent_24h": len(self.get_recent_episodes(hours=24)),
            "storage_path": str(self.storage_path) if self.storage_path else None
        }


# Convenience function

def create_episodic_memory(
    storage_path: Optional[Path] = None
) -> EpisodicMemory:
    """
    Create episodic memory instance.

    Args:
        storage_path: Optional path to store episode data

    Returns:
        EpisodicMemory instance
    """
    return EpisodicMemory(storage_path)
