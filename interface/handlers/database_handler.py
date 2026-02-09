"""
Database Handler for Agent Output Bus

Receives agent outputs and logs them to a database for analytics.
This is built into AgentOutputBus by default, but can be customized.
"""

import logging
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import from parent directory
import sys
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from AgentOutputBus import OutputHandler, HandlerResult, OutputEvent

logger = logging.getLogger(__name__)


class DatabaseHandler(OutputHandler):
    """
    Handler for logging agent outputs to a database.

    This provides persistent storage and analytics capabilities.
    Note: AgentOutputBus has built-in database logging, this handler
    provides additional customization if needed.
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        custom_table_name: Optional[str] = None
    ):
        """
        Initialize database handler.

        Args:
            db_path: Path to SQLite database
            custom_table_name: Optional custom table name
        """
        super().__init__("DatabaseHandler")

        self.db_path = db_path or Path.cwd() / "agent_outputs.db"
        self.custom_table_name = custom_table_name or "agent_outputs_custom"

        # Initialize database
        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database for logging."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.custom_table_name} (
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
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self.custom_table_name}_timestamp
            ON {self.custom_table_name}(timestamp DESC)
        """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self.custom_table_name}_agent
            ON {self.custom_table_name}(agent_name)
        """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self.custom_table_name}_status
            ON {self.custom_table_name}(status)
        """)
        conn.commit()
        conn.close()

        logger.info(f"DatabaseHandler initialized at {self.db_path} (table: {self.custom_table_name})")

    def handle(self, event: OutputEvent) -> HandlerResult:
        """
        Handle agent output event by logging to database.

        Args:
            event: Parsed agent output event

        Returns:
            HandlerResult with success status
        """
        try:
            self._log_to_database(event)

            data = {
                "db_path": str(self.db_path),
                "table": self.custom_table_name,
                "timestamp": event.timestamp.isoformat()
            }

            return HandlerResult(
                success=True,
                message=f"Logged to {self.custom_table_name}",
                data=data
            )

        except Exception as e:
            logger.error(f"DatabaseHandler error: {e}")
            return HandlerResult(
                success=False,
                message=f"Failed to log to database: {e}",
                data=None
            )

    def _log_to_database(self, event: OutputEvent) -> None:
        """Log event to database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(f"""
            INSERT INTO {self.custom_table_name}
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

    def query_outputs(
        self,
        agent_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Query stored outputs.

        Args:
            agent_name: Filter by agent name
            status: Filter by status
            limit: Max results

        Returns:
            List of output dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        query = f"SELECT * FROM {self.custom_table_name}"
        conditions = []
        params = []

        if agent_name:
            conditions.append("agent_name = ?")
            params.append(agent_name)

        if status:
            conditions.append("status = ?")
            params.append(status)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'partial' THEN 1 ELSE 0 END) as partial_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
            FROM {self.custom_table_name}
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
