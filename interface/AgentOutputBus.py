"""
Agent Output Bus - Central Router for Agent Outputs

This module provides a single entry point for all agent outputs,
routing structured outputs to appropriate systems based on their content.

Usage:
    from client.AgentOutputBus import AgentOutputBus

    bus = AgentOutputBus()
    bus.initialize()

    # When agent completes task
    agent_output = agent.execute(task)

    # Send to bus (auto-routes to Kanban, Scheduler, DB)
    bus.receive(agent_output)
"""

import logging
import json
import sqlite3
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Import our parser
try:
    from client.AgentOutputParser import (
        parse_agent_output,
        ParsedAgentOutput,
        AgentOutputParserError
    )
except ImportError:
    # Fallback for standalone usage
    sys.path.insert(0, str(Path(__file__).parent))
    from AgentOutputParser import (
        parse_agent_output,
        ParsedAgentOutput,
        AgentOutputParserError
    )

logger = logging.getLogger(__name__)


class OutputStatus(Enum):
    """Agent output status"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class OutputEvent:
    """An agent output event."""
    agent_name: str
    task_id: str
    status: OutputStatus
    summary: str
    deliverables: List[str]
    next_steps: List[str]
    metadata: Dict[str, Any]
    human_content: str
    raw_output: str
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_success(self) -> bool:
        return self.status == OutputStatus.SUCCESS

    @property
    def is_partial(self) -> bool:
        return self.status == OutputStatus.PARTIAL

    @property
    def is_failed(self) -> bool:
        return self.status == OutputStatus.FAILED


class HandlerResult:
    """Result from a handler execution."""
    def __init__(self, success: bool, message: str, data: Any = None):
        self.success = success
        self.message = message
        self.data = data


class OutputHandler:
    """Base class for output handlers."""

    def __init__(self, name: str):
        self.name = name

    def handle(self, event: OutputEvent) -> HandlerResult:
        """
        Handle an agent output event.

        Args:
            event: The parsed output event

        Returns:
            HandlerResult with success status and message
        """
        raise NotImplementedError(f"{self.name}.handle() not implemented")


class AgentOutputBus:
    """
    Central bus for routing agent outputs to appropriate systems.

    This is the main entry point for all agent outputs. It:
    1. Receives raw agent output
    2. Parses structured format
    3. Routes to handlers based on content
    4. Aggregates results
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the Agent Output Bus.

        Args:
            db_path: Path to SQLite database for logging (optional)
        """
        self.db_path = db_path or Path.cwd() / "agent_outputs.db"
        self._handlers: List[OutputHandler] = []
        self._lock = threading.RLock()
        self._initialized = False

        logger.info(f"AgentOutputBus created (db: {self.db_path})")

    def initialize(self) -> None:
        """Initialize the bus and all handlers."""
        with self._lock:
            if self._initialized:
                logger.warning("AgentOutputBus already initialized")
                return

            # Initialize database
            self._init_database()

            # Register handlers (will be added separately)
            logger.info(f"AgentOutputBus initialized with {len(self._handlers)} handlers")

            self._initialized = True

    def register_handler(self, handler: OutputHandler) -> None:
        """Register a handler to receive events."""
        with self._lock:
            self._handlers.append(handler)
            logger.info(f"Registered handler: {handler.name}")

    def _init_database(self) -> None:
        """Initialize SQLite database for logging."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                agent_name TEXT NOT NULL,
                task_id TEXT,
                status TEXT NOT NULL,
                summary TEXT,
                deliverables TEXT,
                next_steps TEXT,
                metadata TEXT,
                human_content TEXT,
                raw_output TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_outputs_timestamp
            ON agent_outputs(timestamp DESC)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_outputs_agent
            ON agent_outputs(agent_name)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_outputs_status
            ON agent_outputs(status)
        """)
        conn.commit()
        conn.close()

        logger.info(f"Database initialized at {self.db_path}")

    def receive(self, raw_output: str) -> Dict[str, Any]:
        """
        Receive and process an agent output.

        This is the main entry point. Call this whenever an agent completes a task.

        Args:
            raw_output: Raw string output from agent

        Returns:
            Dictionary with processing results
        """
        if not self._initialized:
            logger.warning("AgentOutputBus not initialized, initializing now")
            self.initialize()

        logger.info(f"AgentOutputBus receiving output ({len(raw_output)} chars)")

        # Parse the output
        try:
            parsed = parse_agent_output(raw_output)
            event = OutputEvent(
                agent_name=parsed.metadata.get('agent', 'unknown'),
                task_id=parsed.metadata.get('task_id', 'unknown'),
                status=OutputStatus(parsed.status),
                summary=parsed.summary,
                deliverables=parsed.deliverables,
                next_steps=parsed.next_steps,
                metadata=parsed.metadata,
                human_content=parsed.human_content,
                raw_output=raw_output
            )
        except AgentOutputParserError as e:
            logger.error(f"Failed to parse agent output: {e}")
            return {
                "success": False,
                "error": f"Parse failed: {e}",
                "handlers": []
            }

        # Log to database
        try:
            self._log_to_database(event)
        except Exception as e:
            logger.error(f"Database logging failed: {e}")

        # Route to handlers
        handler_results = []
        for handler in self._handlers:
            try:
                result = handler.handle(event)
                handler_results.append({
                    "handler": handler.name,
                    "success": result.success,
                    "message": result.message,
                    "data": result.data
                })

                # Log handler result
                if result.success:
                    logger.info(f"✓ Handler {handler.name}: {result.message}")
                else:
                    logger.warning(f"✗ Handler {handler.name}: {result.message}")

            except Exception as e:
                logger.error(f"Handler {handler.name} crashed: {e}")
                handler_results.append({
                    "handler": handler.name,
                    "success": False,
                    "error": str(e)
                })

        # Return summary
        return {
            "success": True,
            "event": {
                "agent": event.agent_name,
                "task": event.task_id,
                "status": event.status.value,
                "summary": event.summary,
                "deliverables_count": len(event.deliverables),
                "next_steps_count": len(event.next_steps)
            },
            "handlers": handler_results
        }

    def _log_to_database(self, event: OutputEvent) -> None:
        """Log event to database for analytics."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO agent_outputs
            (timestamp, agent_name, task_id, status, summary, deliverables, next_steps, metadata, human_content, raw_output)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.timestamp.isoformat(),
            event.agent_name,
            event.task_id,
            event.status.value,
            event.summary,
            json.dumps(event.deliverables),
            json.dumps(event.next_steps),
            json.dumps(event.metadata),
            event.human_content,
            event.raw_output
        ))
        conn.commit()
        conn.close()

    def get_recent_outputs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent agent outputs from database.

        Args:
            limit: Maximum number of outputs to return

        Returns:
            List of recent outputs
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT * FROM agent_outputs
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_agent_stats(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for agent outputs.

        Args:
            agent_name: Filter by specific agent (optional)

        Returns:
            Statistics dictionary
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        if agent_name:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status = 'partial' THEN 1 ELSE 0 END) as partial_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
                FROM agent_outputs
                WHERE agent_name = ?
            """, (agent_name,))
        else:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status = 'partial' THEN 1 ELSE 0 END) as partial_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
                FROM agent_outputs
            """)

        stats = cursor.fetchone()
        conn.close()

        if not stats or stats[0] == 0:
            return {"total": 0, "success_rate": 0}

        return {
            "total": stats[0],
            "success_count": stats[1] or 0,
            "partial_count": stats[2] or 0,
            "failed_count": stats[3] or 0,
            "success_rate": (stats[1] or 0) / stats[0] if stats[0] > 0 else 0
        }

    def get_recent_deliverables(self, limit: int = 20) -> List[str]:
        """Get list of recent deliverables."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT deliverables FROM agent_outputs
            WHERE deliverables IS NOT NULL AND deliverables != '[]'
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        results = []
        for row in cursor.fetchall():
            try:
                deliverables = json.loads(row[0])
                results.extend(deliverables)
            except (json.JSONDecodeError, TypeError, KeyError):
                continue

        conn.close()
        return results[:limit]

    def clear_old_logs(self, days_to_keep: int = 30) -> int:
        """
        Clear old logs from database.

        Args:
            days_to_keep: Number of days of history to keep

        Returns:
            Number of rows deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            DELETE FROM agent_outputs
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        """, (days_to_keep,))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Cleared {deleted} old log entries (kept {days_to_keep} days)")
        return deleted


# Global singleton instance
_global_bus: Optional[AgentOutputBus] = None
_bus_lock = threading.Lock()


def get_agent_output_bus(db_path: Optional[Path] = None) -> AgentOutputBus:
    """
    Get the global AgentOutputBus instance.

    Args:
        db_path: Optional database path (uses default if not provided)

    Returns:
        AgentOutputBus instance
    """
    global _global_bus

    with _bus_lock:
        if _global_bus is None:
            _global_bus = AgentOutputBus(db_path=db_path)
            _global_bus.initialize()

        return _global_bus


# Convenience function
def send_agent_output(raw_output: str, db_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Send an agent output to the bus.

    Args:
        raw_output: Raw string output from agent
        db_path: Optional database path

    Returns:
        Processing results
    """
    bus = get_agent_output_bus(db_path)
    return bus.receive(raw_output)
