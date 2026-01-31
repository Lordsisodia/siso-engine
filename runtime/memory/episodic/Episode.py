"""
Episode Data Structures for BlackBox5

Based on industry research from 2025-2026:
- REMem framework: Two-phase episodic construction
- Link related tasks, decisions, outcomes
- Enable "what happened when we did X?" queries

This module provides:
1. Episode dataclass for representing linked events
2. Episode relationship tracking
3. Temporal episode organization
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid


@dataclass
class Episode:
    """
    A linked sequence of related events across time.

    Episodes group related messages, tasks, and outcomes
    to enable cross-temporal queries and learning.
    """

    # Identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""

    # Temporal bounds
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str = field(default_factory=lambda: datetime.now().isoformat())

    # Content
    task_ids: List[str] = field(default_factory=list)
    messages: List[Any] = field(default_factory=list)  # List of Message objects

    # Relationships
    related_episodes: List[str] = field(default_factory=list)  # Episode IDs
    parent_episode: Optional[str] = None  # Parent episode ID

    # Outcomes
    outcome: str = ""  # What was achieved
    learned_lessons: List[str] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def duration_hours(self) -> float:
        """Calculate episode duration in hours."""
        try:
            start = datetime.fromisoformat(self.start_time)
            end = datetime.fromisoformat(self.end_time)
            return (end - start).total_seconds() / 3600
        except ValueError:
            # Invalid ISO format string
            return 0.0

    def message_count(self) -> int:
        """Get total number of messages in episode."""
        return len(self.messages)

    def task_count(self) -> int:
        """Get total number of tasks in episode."""
        return len(self.task_ids)

    def add_message(self, message) -> None:
        """Add a message to the episode."""
        self.messages.append(message)

        # Update temporal bounds
        if hasattr(message, 'timestamp'):
            try:
                msg_time = datetime.fromisoformat(message.timestamp)
                start = datetime.fromisoformat(self.start_time)
                end = datetime.fromisoformat(self.end_time)

                if msg_time < start:
                    self.start_time = message.timestamp
                if msg_time > end:
                    self.end_time = message.timestamp
            except ValueError:
                # Invalid timestamp format, skip updating bounds
                pass

    def add_task(self, task_id: str) -> None:
        """Add a task ID to the episode."""
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)

    def link_episode(self, episode_id: str) -> None:
        """Link to another related episode."""
        if episode_id not in self.related_episodes:
            self.related_episodes.append(episode_id)

    def add_lesson(self, lesson: str) -> None:
        """Add a learned lesson from this episode."""
        if lesson and lesson not in self.learned_lessons:
            self.learned_lessons.append(lesson)

    def get_summary(self) -> str:
        """Get a summary of the episode."""
        parts = [
            f"Episode: {self.title}",
            f"Duration: {self.duration_hours():.1f} hours",
            f"Messages: {self.message_count()}",
            f"Tasks: {self.task_count()}",
        ]

        if self.outcome:
            parts.append(f"Outcome: {self.outcome}")

        if self.learned_lessons:
            parts.append(f"Lessons: {len(self.learned_lessons)} learned")

        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert episode to dictionary."""
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Episode':
        """Create episode from dictionary."""
        return cls(**data)

    @classmethod
    def create(
        cls,
        title: str,
        messages: List[Any],
        description: str = ""
    ) -> 'Episode':
        """
        Create a new episode from messages.

        Args:
            title: Episode title
            messages: List of messages
            description: Optional description

        Returns:
            New Episode instance
        """
        if not messages:
            raise ValueError("Cannot create episode from empty message list")

        # Extract timestamps
        timestamps = []
        for msg in messages:
            if hasattr(msg, 'timestamp') and msg.timestamp:
                try:
                    datetime.fromisoformat(msg.timestamp)
                    timestamps.append(msg.timestamp)
                except ValueError:
                    # Invalid timestamp format, skip this message
                    pass

        if not timestamps:
            # Use current time if no valid timestamps
            now = datetime.now().isoformat()
            start_time = now
            end_time = now
        else:
            start_time = min(timestamps)
            end_time = max(timestamps)

        # Extract task IDs
        task_ids = []
        for msg in messages:
            if hasattr(msg, 'task_id') and msg.task_id:
                if msg.task_id not in task_ids:
                    task_ids.append(msg.task_id)

        return cls(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            task_ids=task_ids,
            messages=messages
        )
