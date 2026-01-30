"""
SQLite-based task store for production deployment.

ACID-compliant task persistence with zero configuration.
Ideal for production and single-server deployments.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from ..schemas.task import Task, TaskState


class SQLiteTaskStore:
    """SQLite-based task storage with ACID guarantees"""

    def __init__(self, db_path: str = "tasks/tasks.db"):
        """
        Initialize SQLite task store.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Create tasks table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                type TEXT,
                priority INTEGER DEFAULT 5,
                tags TEXT,
                state TEXT NOT NULL,
                assignee TEXT,
                created_at TEXT,
                assigned_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                depends_on TEXT,
                blocks TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                error_log TEXT,
                checkpoint_data TEXT,
                checkpoint_timestamp TEXT,
                result TEXT,
                artifacts TEXT,
                schema_version TEXT DEFAULT '2.0'
            )
        """)

        # Create indexes for common queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_state
            ON tasks(state)
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_assignee
            ON tasks(assignee)
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_type
            ON tasks(type)
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_priority
            ON tasks(priority)
        """)

        # Create events table for audit log
        cur.execute("""
            CREATE TABLE IF NOT EXISTS task_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                data TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_task
            ON task_events(task_id)
        """)

        conn.commit()
        conn.close()

    def save(self, task: Task):
        """
        Save task to database.

        Args:
            task: Task object to save
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Serialize complex fields
        tags_json = json.dumps(task.tags) if task.tags else None
        depends_on_json = json.dumps(task.depends_on) if task.depends_on else None
        blocks_json = json.dumps(task.blocks) if task.blocks else None
        error_log_json = json.dumps(task.error_log) if task.error_log else None
        checkpoint_json = json.dumps(task.checkpoint_data) if task.checkpoint_data else None
        result_json = json.dumps(task.result) if task.result else None
        artifacts_json = json.dumps(task.artifacts) if task.artifacts else None

        # Insert or replace
        cur.execute("""
            INSERT OR REPLACE INTO tasks (
                id, title, description, type, priority, tags, state, assignee,
                created_at, assigned_at, started_at, completed_at,
                depends_on, blocks, retry_count, max_retries, error_log,
                checkpoint_data, checkpoint_timestamp, result, artifacts,
                schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.id,
            task.title,
            task.description,
            task.type,
            task.priority,
            tags_json,
            task.state.value,
            task.assignee,
            task.created_at.isoformat() if task.created_at else None,
            task.assigned_at.isoformat() if task.assigned_at else None,
            task.started_at.isoformat() if task.started_at else None,
            task.completed_at.isoformat() if task.completed_at else None,
            depends_on_json,
            blocks_json,
            task.retry_count,
            task.max_retries,
            error_log_json,
            checkpoint_json,
            task.checkpoint_timestamp.isoformat() if task.checkpoint_timestamp else None,
            result_json,
            artifacts_json,
            task.schema_version
        ))

        conn.commit()
        conn.close()

    def load(self, task_id: str) -> Optional[Task]:
        """
        Load task from database.

        Args:
            task_id: Task ID to load

        Returns:
            Task object or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()

        conn.close()

        if not row:
            return None

        return self._row_to_task(row)

    def load_all(self) -> List[Task]:
        """
        Load all tasks from database.

        Returns:
            List of all tasks
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("SELECT * FROM tasks")
        rows = cur.fetchall()

        conn.close()

        return [self._row_to_task(row) for row in rows]

    def delete(self, task_id: str):
        """
        Delete task from database.

        Args:
            task_id: Task ID to delete
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        cur.execute("DELETE FROM task_events WHERE task_id = ?", (task_id,))

        conn.commit()
        conn.close()

    def query(self, **filters) -> List[Task]:
        """
        Query tasks by filters.

        Args:
            **filters: Field=value pairs to filter by

        Returns:
            List of matching tasks
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Build query
        where_clause = " AND ".join([f"{k} = ?" for k in filters.keys()])
        sql = f"SELECT * FROM tasks WHERE {where_clause}"

        cur.execute(sql, tuple(filters.values()))
        rows = cur.fetchall()

        conn.close()

        return [self._row_to_task(row) for row in rows]

    def get_by_state(self, state: str) -> List[Task]:
        """
        Get all tasks in a specific state.

        Args:
            state: Task state value

        Returns:
            List of tasks in the given state
        """
        return self.query(state=state)

    def get_by_assignee(self, assignee: str) -> List[Task]:
        """
        Get all tasks assigned to an agent.

        Args:
            assignee: Agent ID

        Returns:
            List of tasks assigned to the agent
        """
        return self.query(assignee=assignee)

    def get_by_type(self, task_type: str) -> List[Task]:
        """
        Get all tasks of a specific type.

        Args:
            task_type: Task type

        Returns:
            List of tasks of the given type
        """
        return self.query(type=task_type)

    def log_event(self, task_id: str, event_type: str, data: dict):
        """
        Log task event for audit trail.

        Args:
            task_id: Task ID
            event_type: Event type (created, assigned, started, completed, etc.)
            data: Event data
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO task_events (task_id, timestamp, event_type, data)
            VALUES (?, ?, ?, ?)
        """, (
            task_id,
            datetime.now().isoformat(),
            event_type,
            json.dumps(data)
        ))

        conn.commit()
        conn.close()

    def get_events(self, task_id: str) -> List[dict]:
        """
        Get all events for a task.

        Args:
            task_id: Task ID

        Returns:
            List of event dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            SELECT timestamp, event_type, data
            FROM task_events
            WHERE task_id = ?
            ORDER BY timestamp ASC
        """, (task_id,))

        rows = cur.fetchall()
        conn.close()

        return [
            {
                "timestamp": row[0],
                "event_type": row[1],
                "data": json.loads(row[2]) if row[2] else None
            }
            for row in rows
        ]

    def _row_to_task(self, row) -> Task:
        """Convert database row to Task object"""
        # Column order from CREATE TABLE statement
        task_dict = {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "type": row[3],
            "priority": row[4],
            "tags": json.loads(row[5]) if row[5] else [],
            "state": row[6],
            "assignee": row[7],
            "created_at": datetime.fromisoformat(row[8]) if row[8] else None,
            "assigned_at": datetime.fromisoformat(row[9]) if row[9] else None,
            "started_at": datetime.fromisoformat(row[10]) if row[10] else None,
            "completed_at": datetime.fromisoformat(row[11]) if row[11] else None,
            "depends_on": json.loads(row[12]) if row[12] else [],
            "blocks": json.loads(row[13]) if row[13] else [],
            "retry_count": row[14],
            "max_retries": row[15],
            "error_log": json.loads(row[16]) if row[16] else [],
            "checkpoint_data": json.loads(row[17]) if row[17] else {},
            "checkpoint_timestamp": datetime.fromisoformat(row[18]) if row[18] else None,
            "result": json.loads(row[19]) if row[19] else None,
            "artifacts": json.loads(row[20]) if row[20] else [],
            "schema_version": row[21],
        }

        return Task.from_dict(task_dict)

    def transaction(self):
        """
        Get transaction context for atomic operations.

        Usage:
            with store.transaction():
                store.save(task1)
                store.save(task2)
        """
        return TransactionContext(self.db_path)


class TransactionContext:
    """Context manager for SQLite transactions"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()
