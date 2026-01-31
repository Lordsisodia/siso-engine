"""
Memory Importance Scoring for BlackBox5

Based on industry research from 2025-2026:
- mem0.ai: Importance scores prioritize valuable memories
- Attention mechanisms: Recent interactions weighted higher
- User decisions: Higher importance than system messages
- Errors and fixes: Highest importance for learning

This module provides:
1. Automatic importance scoring for messages
2. Configurable scoring heuristics
3. Importance-aware retrieval
4. Integration with enhanced memory system
"""

from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ImportanceConfig:
    """Configuration for importance scoring heuristics."""

    # Base scores
    base_score: float = 0.5

    # Recency bonuses
    recent_hours: float = 1.0  # Hours considered "recent"
    recent_bonus: float = 0.2  # Bonus for recent messages

    # Role bonuses
    user_bonus: float = 0.1  # User messages matter more
    assistant_penalty: float = -0.05  # Assistant responses slightly less
    system_penalty: float = -0.1  # System messages lowest

    # Content patterns
    error_keywords: list = None
    error_bonus: float = 0.3
    fix_keywords: list = None
    fix_bonus: float = 0.2
    decision_keywords: list = None
    decision_bonus: float = 0.2

    # Metadata bonuses
    decision_type_bonus: float = 0.2  # Messages with type="decision"
    artifact_bonus: float = 0.15  # Messages about artifacts
    task_completion_bonus: float = 0.1  # Task completions

    # Message characteristics
    length_factor: float = 0.05  # Slight boost for longer messages (more context)
    question_bonus: float = 0.1  # Questions are important

    def __post_init__(self):
        """Initialize default keyword lists."""
        if self.error_keywords is None:
            self.error_keywords = [
                'error', 'exception', 'failed', 'failure',
                'bug', 'issue', 'problem', 'crash',
                'traceback', 'warning'
            ]
        if self.fix_keywords is None:
            self.fix_keywords = [
                'fix', 'fixed', 'resolved', 'solution',
                'patch', 'corrected', 'repaired'
            ]
        if self.decision_keywords is None:
            self.decision_keywords = [
                'decided', 'chosen', 'selected', 'approved',
                'rejected', 'accepted', 'plan', 'approach'
            ]


class ImportanceScorer:
    """
    Calculate importance scores for messages.

    Importance scores range from 0.0 to 1.0 and are used to:
    - Prioritize valuable memories in retrieval
    - Filter out noise from context
    - Optimize token usage
    - Improve relevance of retrieved context
    """

    def __init__(self, config: Optional[ImportanceConfig] = None):
        """
        Initialize importance scorer.

        Args:
            config: Scoring configuration (uses defaults if not provided)
        """
        self.config = config or ImportanceConfig()

    def calculate_importance(
        self,
        role: str,
        content: str,
        timestamp: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate importance score for a message.

        Args:
            role: Message role (user, assistant, system, tool)
            content: Message content
            timestamp: ISO format timestamp
            metadata: Optional metadata dictionary

        Returns:
            Importance score between 0.0 and 1.0
        """
        score = self.config.base_score

        # Apply recency bonus
        score += self._calculate_recency_bonus(timestamp)

        # Apply role bonus/penalty
        score += self._calculate_role_bonus(role)

        # Apply content pattern bonuses
        score += self._calculate_content_bonus(content)

        # Apply metadata bonuses
        score += self._calculate_metadata_bonus(content, metadata)

        # Apply message characteristic bonuses
        score += self._calculate_characteristic_bonus(content)

        # Clamp to valid range
        return max(0.0, min(1.0, score))

    def _calculate_recency_bonus(self, timestamp: str) -> float:
        """Calculate bonus for recent messages."""
        try:
            msg_time = datetime.fromisoformat(timestamp)
            hours_ago = (datetime.now() - msg_time).total_seconds() / 3600

            if hours_ago < self.config.recent_hours:
                # Linear decay: full bonus at 0 hours, 0 at recent_hours
                decay = 1.0 - (hours_ago / self.config.recent_hours)
                return self.config.recent_bonus * decay
            return 0.0
        except (ValueError, TypeError):
            return 0.0

    def _calculate_role_bonus(self, role: str) -> float:
        """Calculate bonus/penalty based on role."""
        role_lower = role.lower()

        if role_lower == 'user':
            return self.config.user_bonus
        elif role_lower == 'assistant':
            return self.config.assistant_penalty
        elif role_lower == 'system':
            return self.config.system_penalty
        elif role_lower == 'tool':
            return 0.0  # Neutral
        else:
            return 0.0

    def _calculate_content_bonus(self, content: str) -> float:
        """Calculate bonus based on content patterns."""
        content_lower = content.lower()
        bonus = 0.0

        # Error keywords (highest bonus)
        for keyword in self.config.error_keywords:
            if keyword in content_lower:
                bonus += self.config.error_bonus
                break  # Only apply once

        # Fix keywords
        for keyword in self.config.fix_keywords:
            if keyword in content_lower:
                bonus += self.config.fix_bonus
                break

        # Decision keywords
        for keyword in self.config.decision_keywords:
            if keyword in content_lower:
                bonus += self.config.decision_bonus
                break

        return bonus

    def _calculate_metadata_bonus(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate bonus based on metadata."""
        if not metadata:
            return 0.0

        bonus = 0.0

        # Decision type
        if metadata.get('type') == 'decision':
            bonus += self.config.decision_type_bonus

        # Artifact-related
        if metadata.get('artifacts') or metadata.get('artifact'):
            bonus += self.config.artifact_bonus

        # Task completion
        if metadata.get('status') == 'complete' or metadata.get('completed'):
            bonus += self.config.task_completion_bonus

        return bonus

    def _calculate_characteristic_bonus(self, content: str) -> float:
        """Calculate bonus based on message characteristics."""
        bonus = 0.0

        # Length factor (slight boost for longer messages)
        words = len(content.split())
        if words > 50:
            bonus += self.config.length_factor

        # Question bonus
        if '?' in content:
            bonus += self.config.question_bonus

        return bonus

    def score_message(self, message) -> float:
        """
        Score a message object.

        This is a convenience method that works with Message dataclass.

        Args:
            message: Message object with role, content, timestamp, metadata

        Returns:
            Importance score
        """
        return self.calculate_importance(
            role=message.role,
            content=message.content,
            timestamp=message.timestamp,
            metadata=getattr(message, 'metadata', None)
        )

    def filter_by_importance(
        self,
        messages: list,
        min_importance: float = 0.3
    ) -> list:
        """
        Filter messages by minimum importance score.

        Args:
            messages: List of messages to filter
            min_importance: Minimum importance threshold (0.0 to 1.0)

        Returns:
            Filtered list of messages
        """
        scored = []

        for msg in messages:
            score = self.score_message(msg)
            if score >= min_importance:
                # Attach score for potential sorting
                if hasattr(msg, 'importance'):
                    msg.importance = score
                scored.append((score, msg))

        # Sort by score (highest first) and return messages
        scored.sort(key=lambda x: x[0], reverse=True)
        return [msg for score, msg in scored]

    def get_top_n(
        self,
        messages: list,
        n: int = 10
    ) -> list:
        """
        Get top N most important messages.

        Args:
            messages: List of messages to rank
            n: Number of top messages to return

        Returns:
            Top N messages sorted by importance
        """
        scored = []

        for msg in messages:
            score = self.score_message(msg)
            scored.append((score, msg))

        # Sort by score and return top N
        scored.sort(key=lambda x: x[0], reverse=True)
        return [msg for score, msg in scored[:n]]


# Convenience function for quick scoring

def score_message(
    role: str,
    content: str,
    timestamp: str,
    metadata: Optional[Dict[str, Any]] = None,
    config: Optional[ImportanceConfig] = None
) -> float:
    """
    Quick importance score calculation.

    Args:
        role: Message role
        content: Message content
        timestamp: ISO timestamp
        metadata: Optional metadata
        config: Optional scoring config

    Returns:
        Importance score 0.0 to 1.0
    """
    scorer = ImportanceScorer(config)
    return scorer.calculate_importance(role, content, timestamp, metadata)
