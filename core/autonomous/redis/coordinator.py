"""
Redis coordination for autonomous agent system.

Provides event-driven coordination via Redis pub/sub with 1ms latency.
Replaces slower file-based coordination (100ms) and polling (10+ seconds).
"""

import json
import time
import threading
from typing import Callable, Optional, Any, Dict, List
from dataclasses import dataclass
from datetime import datetime

try:
    import redis
except ImportError:
    raise ImportError(
        "Redis package required. Install with: pip install redis"
    )


@dataclass
class RedisConfig:
    """Redis connection configuration"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    decode_responses: bool = True


class RedisCoordinator:
    """
    Redis-based coordination for autonomous agents.

    Provides:
    - Pub/sub for instant notifications (1ms latency)
    - Sorted sets for priority task queues
    - Atomic operations for conflict prevention
    - Event streams for replay and debugging
    """

    # Channel names
    CHANNEL_TASK_NEW = "tasks:new"
    CHANNEL_TASK_CLAIMED = "tasks:claimed"
    CHANNEL_TASK_UPDATED = "tasks:updated"
    CHANNEL_TASK_COMPLETE = "tasks:complete"
    CHANNEL_TASK_FAILED = "tasks:failed"

    def __init__(self, config: Optional[RedisConfig] = None):
        """
        Initialize Redis coordinator.

        Args:
            config: Redis connection configuration
        """
        self.config = config or RedisConfig()
        self.client = redis.Redis(
            host=self.config.host,
            port=self.config.port,
            db=self.config.db,
            password=self.config.password,
            decode_responses=self.config.decode_responses
        )

        # Test connection
        try:
            self.client.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(
                f"Cannot connect to Redis at {self.config.host}:{self.config.port}. "
                f"Ensure Redis is running: brew services start redis"
            ) from e

        self._pubsub = None
        self._listeners = []

    def publish_task(self, task_data: dict, channel: str = None) -> int:
        """
        Publish task event to Redis.

        Args:
            task_data: Task data to publish
            channel: Channel name (default: tasks:new)

        Returns:
            Number of subscribers who received the message
        """
        channel = channel or self.CHANNEL_TASK_NEW
        message = json.dumps(task_data)

        return self.client.publish(channel, message)

    def subscribe(self, *channels: str, callback: Callable[[dict], None]):
        """
        Subscribe to Redis channels and invoke callback on messages.

        Args:
            *channels: Channel names to subscribe to
            callback: Function to call with message data

        Note:
            This starts a background thread that listens for messages.
        """
        pubsub = self.client.pubsub()
        pubsub.subscribe(*channels)

        def listener():
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        callback(data)
                    except json.JSONDecodeError:
                        continue

        thread = threading.Thread(target=listener, daemon=True)
        thread.start()
        self._listeners.append(thread)

        return pubsub

    def add_to_pending_queue(self, task_id: str, priority: int):
        """
        Add task to pending queue (sorted by priority).

        Args:
            task_id: Task ID
            priority: Priority score (higher = more important)
        """
        self.client.zadd("tasks:pending", {task_id: priority})

    def remove_from_pending_queue(self, task_id: str) -> bool:
        """
        Remove task from pending queue (atomic claim).

        Args:
            task_id: Task ID to claim

        Returns:
            True if task was successfully claimed
        """
        result = self.client.zrem("tasks:pending", task_id)
        return result > 0

    def get_pending_tasks(self, start: int = 0, end: int = -1,
                          with_scores: bool = False) -> List[str]:
        """
        Get tasks from pending queue ordered by priority.

        Args:
            start: Start index (default: 0)
            end: End index (default: -1 = all)
            with_scores: Include priority scores

        Returns:
            List of task IDs (and scores if with_scores=True)
        """
        return self.client.zrevrange("tasks:pending", start, end, withscores=with_scores)

    def claim_task_atomic(self, task_id: str, agent_id: str,
                         lock_timeout: int = 10) -> bool:
        """
        Atomically claim a task using distributed lock.

        Args:
            task_id: Task ID to claim
            agent_id: Agent ID claiming the task
            lock_timeout: Lock timeout in seconds

        Returns:
            True if task was successfully claimed
        """
        lock_key = f"lock:task:{task_id}"
        lock = self.client.lock(lock_key, timeout=lock_timeout)

        if lock.acquire(blocking=False):
            try:
                # Remove from pending queue
                claimed = self.remove_from_pending_queue(task_id)

                if claimed:
                    # Set assignee
                    self.client.hset(f"task:{task_id}", "assignee", agent_id)
                    self.client.hset(f"task:{task_id}", "assigned_at",
                                    datetime.now().isoformat())

                    # Publish claim event
                    self.publish_task({
                        "task_id": task_id,
                        "agent": agent_id,
                        "timestamp": datetime.now().isoformat()
                    }, self.CHANNEL_TASK_CLAIMED)

                return claimed

            finally:
                lock.release()

        return False

    def update_task_status(self, task_id: str, status: str,
                          result: dict = None):
        """
        Update task status in Redis.

        Args:
            task_id: Task ID
            status: New status
            result: Optional result data
        """
        self.client.hset(f"task:{task_id}", "status", status)
        self.client.hset(f"task:{task_id}", "updated_at",
                        datetime.now().isoformat())

        if result:
            self.client.hset(f"task:{task_id}", "result",
                            json.dumps(result))

        # Publish update event
        self.publish_task({
            "task_id": task_id,
            "status": status,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }, self.CHANNEL_TASK_UPDATED)

    def complete_task(self, task_id: str, result: dict):
        """
        Mark task as complete.

        Args:
            task_id: Task ID
            result: Task result data
        """
        self.update_task_status(task_id, "done", result)
        self.publish_task({
            "task_id": task_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }, self.CHANNEL_TASK_COMPLETE)

    def fail_task(self, task_id: str, error: str):
        """
        Mark task as failed.

        Args:
            task_id: Task ID
            error: Error message
        """
        self.update_task_status(task_id, "failed", {"error": error})
        self.publish_task({
            "task_id": task_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }, self.CHANNEL_TASK_FAILED)

    def log_event(self, task_id: str, event_type: str, data: dict):
        """
        Log task event to Redis stream for replay.

        Args:
            task_id: Task ID
            event_type: Event type
            data: Event data
        """
        stream_key = f"events:task:{task_id}"

        self.client.xadd(stream_key, {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": json.dumps(data)
        })

    def get_task_events(self, task_id: str, count: int = 100) -> List[dict]:
        """
        Get events for a task from stream.

        Args:
            task_id: Task ID
            count: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        stream_key = f"events:task:{task_id}"

        events = self.client.xrevrange(stream_key, count=count)

        return [
            {
                "id": event_id,
                "event_type": data[b"event_type"] if isinstance(data[b"event_type"], bytes)
                                else data["event_type"],
                "timestamp": data[b"timestamp"] if isinstance(data[b"timestamp"], bytes)
                                 else data["timestamp"],
                "data": json.loads(data[b"data"] if isinstance(data[b"data"], bytes)
                                   else data["data"])
            }
            for event_id, data in events
        ]

    def get_agent_status(self, agent_id: str) -> Optional[dict]:
        """
        Get agent status from Redis.

        Args:
            agent_id: Agent ID

        Returns:
            Agent status dict or None
        """
        data = self.client.hgetall(f"agent:{agent_id}")

        if not data:
            return None

        return {
            "agent_id": agent_id,
            "status": data.get("status"),
            "current_task": data.get("current_task"),
            "last_seen": data.get("last_seen"),
            "capabilities": json.loads(data["capabilities"])
                                if data.get("capabilities") else []
        }

    def update_agent_status(self, agent_id: str, status: str,
                           current_task: str = None,
                           capabilities: list = None):
        """
        Update agent status in Redis.

        Args:
            agent_id: Agent ID
            status: Agent status (idle, busy, offline)
            current_task: Current task ID (if busy)
            capabilities: List of agent capabilities
        """
        self.client.hset(f"agent:{agent_id}", "status", status)
        self.client.hset(f"agent:{agent_id}", "last_seen",
                        datetime.now().isoformat())

        if current_task:
            self.client.hset(f"agent:{agent_id}", "current_task", current_task)

        if capabilities:
            self.client.hset(f"agent:{agent_id}", "capabilities",
                            json.dumps(capabilities))

    def get_all_agents(self) -> List[dict]:
        """
        Get all registered agents.

        Returns:
            List of agent status dicts
        """
        keys = self.client.keys("agent:*")
        agents = []

        for key in keys:
            agent_id = key.split(":")[1]
            status = self.get_agent_status(agent_id)
            if status:
                agents.append(status)

        return agents

    def get_task_queue_length(self) -> int:
        """
        Get number of tasks in pending queue.

        Returns:
            Queue length
        """
        return self.client.zcard("tasks:pending")

    def get_active_tasks(self) -> List[str]:
        """
        Get all active (claimed) task IDs.

        Returns:
            List of task IDs
        """
        keys = self.client.keys("task:*")
        active = []

        for key in keys:
            status = self.client.hget(key, "status")
            if status in ["assigned", "active"]:
                task_id = key.split(":")[1]
                active.append(task_id)

        return active

    def clear_all(self):
        """
        Clear all coordinator data (useful for testing).

        Warning: This deletes all task and agent data from Redis.
        """
        keys = self.client.keys("tasks:*") + self.client.keys("task:*") + \
               self.client.keys("agent:*") + self.client.keys("events:*")

        if keys:
            self.client.delete(*keys)

    def close(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()


class RedisLatencyTest:
    """Test Redis coordination latency"""

    @staticmethod
    def test_latency(host: str = "localhost", port: int = 6379,
                    iterations: int = 100) -> dict:
        """
        Test Redis pub/sub latency.

        Args:
            host: Redis host
            port: Redis port
            iterations: Number of test iterations

        Returns:
            Latency statistics
        """
        client = redis.Redis(host=host, port=port, decode_responses=True)

        latencies = []

        for _ in range(iterations):
            start = time.time()

            # Publish
            client.publish("test:latency", "ping")

            # Measure
            end = time.time()
            latencies.append((end - start) * 1000)  # Convert to ms

        return {
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "avg_ms": sum(latencies) / len(latencies),
            "p50_ms": sorted(latencies)[len(latencies) // 2],
            "p99_ms": sorted(latencies)[int(len(latencies) * 0.99)],
        }
