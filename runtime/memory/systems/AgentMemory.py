"""
Agent Memory System for BlackBox5
==================================

A simplified persistent memory system adapted from Auto-Claude's Graphiti integration.
Each agent gets its own isolated memory environment using JSON files for storage.

This provides:
- Session tracking (tasks and results)
- Insight storage (learned patterns and discoveries)
- Context accumulation (cross-session knowledge)
- Pattern recognition (what works and what doesn't)

Memory is stored per-agent in .blackbox5/data/memory/{agent_id}/
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from threading import Lock


@dataclass
class MemorySession:
    """A single execution session stored in memory."""
    session_id: str
    timestamp: str
    task: str
    result: str
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    duration_seconds: Optional[float] = None


@dataclass
class MemoryInsight:
    """An insight learned during execution."""
    insight_id: str
    timestamp: str
    content: str
    category: str  # pattern, gotcha, discovery, optimization
    confidence: float = 1.0  # 0.0 to 1.0
    source_session: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryContext:
    """Accumulated context for an agent."""
    context_id: str
    agent_id: str
    created_at: str
    updated_at: str
    patterns: list[str] = field(default_factory=list)
    gotchas: list[str] = field(default_factory=list)
    discoveries: list[str] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)


class AgentMemory:
    """
    Persistent memory manager for BlackBox5 agents.

    Each agent gets its own isolated memory environment with:
    - Sessions: Track task executions and results
    - Insights: Store learned patterns and discoveries
    - Context: Accumulate knowledge across sessions

    Memory is persisted to JSON files in .blackbox5/data/memory/{agent_id}/

    Usage:
        memory = AgentMemory(agent_id="my-agent")
        memory.add_session("Build feature", "Feature built successfully")
        memory.add_insight("Use TypeScript for type safety", "pattern")
        context = memory.get_context()
    """

    def __init__(
        self,
        agent_id: str,
        memory_base_path: Optional[Path] = None,
        auto_save: bool = True
    ):
        """
        Initialize agent memory.

        Args:
            agent_id: Unique identifier for this agent
            memory_base_path: Base path for memory storage (default: .blackbox5/data/memory)
            auto_save: Automatically save after each operation (default: True)
        """
        self.agent_id = agent_id
        self.auto_save = auto_save
        self._lock = Lock()

        # Set up memory paths
        if memory_base_path is None:
            # Default to .blackbox5/data/memory relative to project root
            project_root = Path.cwd()
            while project_root != project_root.parent:
                if (project_root / "blackbox5").exists():
                    break
                project_root = project_root.parent
            memory_base_path = project_root / "blackbox5" / "data" / "memory"

        self.memory_path = memory_base_path / agent_id
        self.memory_path.mkdir(parents=True, exist_ok=True)

        # File paths
        self.sessions_file = self.memory_path / "sessions.json"
        self.insights_file = self.memory_path / "insights.json"
        self.context_file = self.memory_path / "context.json"

        # In-memory storage
        self.sessions: list[MemorySession] = []
        self.insights: list[MemoryInsight] = []
        self.context: Optional[MemoryContext] = None

        # Load existing data
        self._load()

    def _load(self) -> None:
        """Load existing memory from disk."""
        with self._lock:
            # Load sessions
            if self.sessions_file.exists():
                try:
                    with open(self.sessions_file, 'r') as f:
                        data = json.load(f)
                        self.sessions = [
                            MemorySession(**s) for s in data
                        ]
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Warning: Failed to load sessions: {e}")
                    self.sessions = []

            # Load insights
            if self.insights_file.exists():
                try:
                    with open(self.insights_file, 'r') as f:
                        data = json.load(f)
                        self.insights = [
                            MemoryInsight(**i) for i in data
                        ]
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Warning: Failed to load insights: {e}")
                    self.insights = []

            # Load or create context
            if self.context_file.exists():
                try:
                    with open(self.context_file, 'r') as f:
                        data = json.load(f)
                        self.context = MemoryContext(**data)
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Warning: Failed to load context: {e}")
                    self.context = None

            # Create context if it doesn't exist
            if self.context is None:
                self.context = MemoryContext(
                    context_id=self._generate_id("context"),
                    agent_id=self.agent_id,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    updated_at=datetime.now(timezone.utc).isoformat(),
                    statistics={
                        "total_sessions": 0,
                        "successful_sessions": 0,
                        "failed_sessions": 0,
                        "total_insights": 0
                    }
                )

    def _save(self) -> None:
        """Save memory to disk."""
        with self._lock:
            try:
                # Save sessions
                with open(self.sessions_file, 'w') as f:
                    data = [asdict(s) for s in self.sessions]
                    json.dump(data, f, indent=2)

                # Save insights
                with open(self.insights_file, 'w') as f:
                    data = [asdict(i) for i in self.insights]
                    json.dump(data, f, indent=2)

                # Save context
                if self.context:
                    self.context.updated_at = datetime.now(timezone.utc).isoformat()
                    with open(self.context_file, 'w') as f:
                        json.dump(asdict(self.context), f, indent=2)

            except OSError as e:
                print(f"Warning: Failed to save memory: {e}")

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        hash_suffix = hashlib.md5(
            f"{self.agent_id}{timestamp}".encode()
        ).hexdigest()[:8]
        return f"{prefix}_{timestamp}_{hash_suffix}"

    def add_session(
        self,
        task: str,
        result: str,
        success: bool = True,
        duration_seconds: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Store an execution session.

        Args:
            task: Description of the task performed
            result: Result of the task execution
            success: Whether the task was successful
            duration_seconds: How long the task took (optional)
            metadata: Additional session metadata (optional)

        Returns:
            session_id: Unique identifier for the session
        """
        session_id = self._generate_id("session")

        session = MemorySession(
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            task=task,
            result=result,
            success=success,
            duration_seconds=duration_seconds,
            metadata=metadata or {}
        )

        with self._lock:
            self.sessions.append(session)

            # Update context statistics
            if self.context:
                self.context.statistics["total_sessions"] = (
                    self.context.statistics.get("total_sessions", 0) + 1
                )
                if success:
                    self.context.statistics["successful_sessions"] = (
                        self.context.statistics.get("successful_sessions", 0) + 1
                    )
                else:
                    self.context.statistics["failed_sessions"] = (
                        self.context.statistics.get("failed_sessions", 0) + 1
                    )

        if self.auto_save:
            self._save()

        return session_id

    def add_insight(
        self,
        content: str,
        category: str,
        confidence: float = 1.0,
        source_session: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Store a learned insight.

        Args:
            content: The insight content
            category: Category (pattern, gotcha, discovery, optimization)
            confidence: Confidence level (0.0 to 1.0)
            source_session: Session ID that generated this insight (optional)
            metadata: Additional insight metadata (optional)

        Returns:
            insight_id: Unique identifier for the insight
        """
        if category not in ["pattern", "gotcha", "discovery", "optimization"]:
            raise ValueError(
                f"Invalid category: {category}. "
                "Must be: pattern, gotcha, discovery, or optimization"
            )

        insight_id = self._generate_id("insight")

        insight = MemoryInsight(
            insight_id=insight_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            content=content,
            category=category,
            confidence=confidence,
            source_session=source_session,
            metadata=metadata or {}
        )

        with self._lock:
            self.insights.append(insight)

            # Update context
            if self.context:
                if category == "pattern" and content not in self.context.patterns:
                    self.context.patterns.append(content)
                elif category == "gotcha" and content not in self.context.gotchas:
                    self.context.gotchas.append(content)
                elif category == "discovery" and content not in self.context.discoveries:
                    self.context.discoveries.append(content)

                self.context.statistics["total_insights"] = (
                    self.context.statistics.get("total_insights", 0) + 1
                )

        if self.auto_save:
            self._save()

        return insight_id

    def get_context(self) -> dict[str, Any]:
        """
        Retrieve accumulated context.

        Returns:
            Dictionary with patterns, gotchas, discoveries, and statistics
        """
        if not self.context:
            return {}

        return {
            "patterns": self.context.patterns.copy(),
            "gotchas": self.context.gotchas.copy(),
            "discoveries": self.context.discoveries.copy(),
            "preferences": self.context.preferences.copy(),
            "statistics": self.context.statistics.copy(),
            "created_at": self.context.created_at,
            "updated_at": self.context.updated_at
        }

    def update_context(self, updates: dict[str, Any]) -> None:
        """
        Update accumulated context.

        Args:
            updates: Dictionary with fields to update (patterns, gotchas, etc.)
        """
        with self._lock:
            if not self.context:
                return

            if "patterns" in updates:
                new_patterns = [p for p in updates["patterns"]
                              if p not in self.context.patterns]
                self.context.patterns.extend(new_patterns)

            if "gotchas" in updates:
                new_gotchas = [g for g in updates["gotchas"]
                             if g not in self.context.gotchas]
                self.context.gotchas.extend(new_gotchas)

            if "discoveries" in updates:
                new_discoveries = [d for d in updates["discoveries"]
                                 if d not in self.context.discoveries]
                self.context.discoveries.extend(new_discoveries)

            if "preferences" in updates:
                self.context.preferences.update(updates["preferences"])

            if "statistics" in updates:
                self.context.statistics.update(updates["statistics"])

        if self.auto_save:
            self._save()

    def get_sessions(
        self,
        limit: Optional[int] = None,
        successful_only: bool = False
    ) -> list[dict[str, Any]]:
        """
        Retrieve execution sessions.

        Args:
            limit: Maximum number of sessions to return (most recent first)
            successful_only: Only return successful sessions

        Returns:
            List of session dictionaries
        """
        sessions = self.sessions.copy()

        if successful_only:
            sessions = [s for s in sessions if s.success]

        # Sort by timestamp (most recent first)
        sessions.sort(key=lambda s: s.timestamp, reverse=True)

        if limit:
            sessions = sessions[:limit]

        return [asdict(s) for s in sessions]

    def get_insights(
        self,
        category: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """
        Retrieve learned insights.

        Args:
            category: Filter by category (pattern, gotcha, discovery, optimization)
            min_confidence: Minimum confidence threshold
            limit: Maximum number of insights to return

        Returns:
            List of insight dictionaries
        """
        insights = self.insights.copy()

        if category:
            insights = [i for i in insights if i.category == category]

        insights = [i for i in insights if i.confidence >= min_confidence]

        # Sort by confidence and timestamp
        insights.sort(key=lambda i: (i.confidence, i.timestamp), reverse=True)

        if limit:
            insights = insights[:limit]

        return [asdict(i) for i in insights]

    def search_insights(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Search insights by content (simple keyword search).

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of matching insight dictionaries
        """
        query_lower = query.lower()

        matching = [
            i for i in self.insights
            if query_lower in i.content.lower()
        ]

        # Sort by confidence
        matching.sort(key=lambda i: i.confidence, reverse=True)

        if limit:
            matching = matching[:limit]

        return [asdict(i) for i in matching]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get memory usage statistics.

        Returns:
            Dictionary with statistics about sessions, insights, and storage
        """
        sessions = self.sessions
        insights = self.insights

        total_duration = sum(
            s.duration_seconds for s in sessions
            if s.duration_seconds is not None
        )

        success_rate = 0.0
        if sessions:
            successful = sum(1 for s in sessions if s.success)
            success_rate = successful / len(sessions)

        return {
            "agent_id": self.agent_id,
            "memory_path": str(self.memory_path),
            "total_sessions": len(sessions),
            "successful_sessions": sum(1 for s in sessions if s.success),
            "failed_sessions": sum(1 for s in sessions if not s.success),
            "success_rate": success_rate,
            "total_duration_seconds": total_duration,
            "avg_duration_seconds": (
                total_duration / len(sessions) if sessions else 0
            ),
            "total_insights": len(insights),
            "insights_by_category": {
                "pattern": sum(1 for i in insights if i.category == "pattern"),
                "gotcha": sum(1 for i in insights if i.category == "gotcha"),
                "discovery": sum(1 for i in insights if i.category == "discovery"),
                "optimization": sum(1 for i in insights if i.category == "optimization"),
            },
            "context_size": {
                "patterns": len(self.context.patterns) if self.context else 0,
                "gotchas": len(self.context.gotchas) if self.context else 0,
                "discoveries": len(self.context.discoveries) if self.context else 0,
            }
        }

    def clear_memory(self, keep_context: bool = True) -> None:
        """
        Clear all memory data.

        Args:
            keep_context: If True, preserves accumulated context
        """
        with self._lock:
            self.sessions.clear()
            self.insights.clear()

            if not keep_context and self.context:
                self.context.patterns.clear()
                self.context.gotchas.clear()
                self.context.discoveries.clear()
                self.context.statistics = {
                    "total_sessions": 0,
                    "successful_sessions": 0,
                    "failed_sessions": 0,
                    "total_insights": 0
                }

        self._save()

    def export_memory(self) -> dict[str, Any]:
        """
        Export all memory data as a dictionary.

        Returns:
            Complete memory data
        """
        return {
            "agent_id": self.agent_id,
            "sessions": [asdict(s) for s in self.sessions],
            "insights": [asdict(i) for i in self.insights],
            "context": asdict(self.context) if self.context else None,
            "statistics": self.get_statistics()
        }

    def import_memory(self, data: dict[str, Any], merge: bool = True) -> None:
        """
        Import memory data from a dictionary.

        Args:
            data: Memory data dictionary (from export_memory)
            merge: If True, merges with existing data; if False, replaces
        """
        with self._lock:
            if not merge:
                self.sessions.clear()
                self.insights.clear()

            # Import sessions
            for session_data in data.get("sessions", []):
                session = MemorySession(**session_data)
                if merge and session.session_id in [s.session_id for s in self.sessions]:
                    continue  # Skip duplicates when merging
                self.sessions.append(session)

            # Import insights
            for insight_data in data.get("insights", []):
                insight = MemoryInsight(**insight_data)
                if merge and insight.insight_id in [i.insight_id for i in self.insights]:
                    continue  # Skip duplicates when merging
                self.insights.append(insight)

            # Import context
            if data.get("context"):
                imported_context = MemoryContext(**data["context"])
                if not merge or not self.context:
                    self.context = imported_context
                else:
                    # Merge context
                    self.context.patterns.extend([
                        p for p in imported_context.patterns
                        if p not in self.context.patterns
                    ])
                    self.context.gotchas.extend([
                        g for g in imported_context.gotchas
                        if g not in self.context.gotchas
                    ])
                    self.context.discoveries.extend([
                        d for d in imported_context.discoveries
                        if d not in self.context.discoveries
                    ])
                    self.context.preferences.update(imported_context.preferences)

        self._save()
