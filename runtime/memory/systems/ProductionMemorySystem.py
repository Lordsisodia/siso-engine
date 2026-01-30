"""
Production Memory System for BlackBox5

Based on first-principles analysis of production AI systems:
- LangChain: ConversationBufferMemory (simple list of messages)
- AutoGen: List-based message history
- OpenAI Assistants: Built-in context management
- 90% of memory needs solved by simple buffers + persistence

This implementation prioritizes:
1. Simplicity - Easy to understand and maintain
2. Performance - Fast reads with minimal overhead
3. Reliability - Battle-tested patterns from production
4. Flexibility - Easy to extend when needed

NOT implementing (academic over-engineering not used in production):
- Capability-based memory protection
- Hardware enclaves
- Cryptographic hash chains
- Complex memory hierarchies
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterator
from dataclasses import dataclass, asdict
from collections import deque
import threading
import sqlite3

@dataclass
class Message:
    """A single message in the conversation"""
    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    timestamp: str
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        return cls(**data)

    def get_hash(self) -> str:
        """Generate content hash for deduplication"""
        content_str = f"{self.role}:{self.content}:{self.timestamp}"
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]


class WorkingMemory:
    """
    Fast in-memory conversation buffer with sliding window.

    Based on:
    - LangChain ConversationBufferMemory
    - AutoGen message history
    - OpenAI Assistants context management

    Pattern: Fixed-size deque with automatic eviction
    """

    def __init__(self, max_messages: int = 100):
        self.max_messages = max_messages
        self._messages: deque[Message] = deque(maxlen=max_messages)
        self._lock = threading.Lock()

    def add_message(self, message: Message) -> None:
        """Add a message to working memory"""
        with self._lock:
            self._messages.append(message)

    def get_messages(
        self,
        limit: Optional[int] = None,
        role: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> List[Message]:
        """Retrieve messages with optional filtering"""
        with self._lock:
            messages = list(self._messages)

        if role:
            messages = [m for m in messages if m.role == role]
        if task_id:
            messages = [m for m in messages if m.task_id == task_id]
        if limit:
            messages = messages[-limit:]

        return messages

    def get_context(
        self,
        limit: int = 10,
        include_system: bool = True
    ) -> str:
        """Get formatted context for LLM consumption"""
        messages = self.get_messages(limit=limit)

        context_parts = []
        for msg in messages:
            if not include_system and msg.role == 'system':
                continue
            context_parts.append(f"{msg.role}: {msg.content}")

        return "\n".join(context_parts)

    def clear(self) -> None:
        """Clear all messages"""
        with self._lock:
            self._messages.clear()

    def size(self) -> int:
        """Get current number of messages"""
        return len(self._messages)


class PersistentMemory:
    """
    SQLite-based persistent storage for long-term memory.

    Based on production patterns:
    - PostgreSQL episodes (ChatGPT)
    - Redis persistence (AutoGen)
    - SQLite for local-first (LangChain)

    Pattern: Append-only log with indexing
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    agent_id TEXT,
                    task_id TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_id
                ON messages(task_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_id
                ON messages(agent_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON messages(timestamp DESC)
            """)

            conn.commit()

    def store_message(self, message: Message) -> bool:
        """Store message in persistent storage (deduplicated)"""
        msg_hash = message.get_hash()

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO messages
                    (hash, role, content, timestamp, agent_id, task_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        msg_hash,
                        message.role,
                        message.content,
                        message.timestamp,
                        message.agent_id,
                        message.task_id,
                        json.dumps(message.metadata) if message.metadata else None
                    )
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Failed to store message: {e}")
            return False

    def get_messages(
        self,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Message]:
        """Retrieve messages from persistent storage"""
        query = "SELECT role, content, timestamp, agent_id, task_id, metadata FROM messages WHERE 1=1"
        params = []

        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                messages = []
                for row in cursor.fetchall():
                    messages.append(Message(
                        role=row[0],
                        content=row[1],
                        timestamp=row[2],
                        agent_id=row[3],
                        task_id=row[4],
                        metadata=json.loads(row[5]) if row[5] else None
                    ))
                return messages[::-1]  # Return in chronological order
        except Exception as e:
            print(f"Failed to retrieve messages: {e}")
            return []


class ProductionMemorySystem:
    """
    Main memory system combining working and persistent memory.

    This is the production-grade implementation that matches what
    actual AI systems use in production:

    1. Fast in-memory buffer for recent context
    2. Persistent storage for long-term memory
    3. Simple API that covers 90% of use cases
    4. Easy to extend when needed

    Usage:
        memory = ProductionMemorySystem(project_path)
        memory.add(Message(role="user", content="Hello"))
        context = memory.get_context(limit=10)
    """

    def __init__(
        self,
        project_path: Path,
        max_working_messages: int = 100,
        project_name: str = "default"
    ):
        self.project_name = project_name
        self.memory_dir = project_path / "blackbox5" / "memory" / project_name
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Initialize working memory (fast, limited)
        self.working = WorkingMemory(max_messages=max_working_messages)

        # Initialize persistent memory (slow, unlimited)
        db_path = self.memory_dir / "messages.db"
        self.persistent = PersistentMemory(db_path)

    def add(self, message: Message) -> None:
        """Add message to both working and persistent memory"""
        self.working.add_message(message)
        self.persistent.store_message(message)

    def get_context(
        self,
        limit: int = 10,
        include_persistent: bool = False
    ) -> str:
        """Get context for LLM consumption"""
        if include_persistent:
            # Combine working and persistent memory
            working_msgs = self.working.get_messages()
            persistent_msgs = self.persistent.get_messages(limit=limit)

            # Deduplicate by hash
            seen = {m.get_hash() for m in working_msgs}
            unique_persistent = [m for m in persistent_msgs if m.get_hash() not in seen]

            all_msgs = working_msgs + unique_persistent
            all_msgs = all_msgs[-limit:]

            context_parts = [f"{m.role}: {m.content}" for m in all_msgs]
            return "\n".join(context_parts)
        else:
            return self.working.get_context(limit=limit)

    def get_messages(
        self,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Message]:
        """Get messages with optional filtering"""
        if task_id or agent_id:
            return self.persistent.get_messages(
                task_id=task_id,
                agent_id=agent_id,
                limit=limit
            )
        else:
            return self.working.get_messages(limit=limit)

    def search(self, query: str, limit: int = 10) -> List[Message]:
        """Simple keyword search (can be upgraded to vector search later)"""
        all_messages = self.persistent.get_messages(limit=1000)

        query_lower = query.lower()
        results = [
            msg for msg in all_messages
            if query_lower in msg.content.lower()
        ][:limit]

        return results

    def clear_working(self) -> None:
        """Clear working memory (persistent storage remains)"""
        self.working.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "working_memory_size": self.working.size(),
            "memory_directory": str(self.memory_dir),
            "database_path": str(self.memory_dir / "messages.db"),
            "project_name": self.project_name
        }


# Convenience functions for quick integration

def create_message(
    role: str,
    content: str,
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Message:
    """Create a message with current timestamp"""
    return Message(
        role=role,
        content=content,
        timestamp=datetime.now().isoformat(),
        agent_id=agent_id,
        task_id=task_id,
        metadata=metadata
    )


def get_memory_system(project_path: Path, project_name: str = "default") -> ProductionMemorySystem:
    """Get or create memory system for a project"""
    return ProductionMemorySystem(
        project_path=project_path,
        project_name=project_name
    )
