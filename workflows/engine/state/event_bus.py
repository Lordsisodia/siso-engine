"""
Event Bus System for Blackbox5

Provides async event-driven communication between components.
Supports both in-memory and Redis-backed implementations.
"""

import json
import asyncio
import logging
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Any,
    Awaitable,
    Set
)
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Standard event types in the system."""

    # Agent lifecycle events
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    AGENT_THINKING = "agent.thinking"

    # Task events
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    # System events
    SYSTEM_INITIALIZED = "system.initialized"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"

    # Custom events
    CUSTOM = "custom"


@dataclass
class Event:
    """
    Represents an event in the system.

    Attributes:
        type: Event type from EventType enum or custom string
        data: Event payload (any JSON-serializable data)
        source: Source of the event (e.g., agent name, system component)
        timestamp: When the event occurred
        event_id: Unique identifier for the event
        metadata: Additional metadata about the event
        correlation_id: ID to correlate related events
    """

    type: str
    data: Dict[str, Any]
    source: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Create event from JSON string."""
        return cls.from_dict(json.loads(json_str))


EventHandler = Callable[[Event], Awaitable[None]]


@dataclass
class EventBusConfig:
    """Configuration for event bus."""

    # Redis configuration (supports both naming conventions)
    redis_host: str = "localhost"
    host: str = "localhost"  # Alias for redis_host
    redis_port: int = 6379
    port: int = 6379  # Alias for redis_port
    redis_db: int = 0
    db: int = 0  # Alias for redis_db
    redis_password: Optional[str] = None
    password: Optional[str] = None  # Alias for redis_password

    # Event bus settings
    use_redis: bool = False  # If False, uses in-memory implementation
    max_queue_size: int = 10000
    enable_persistence: bool = False
    enable_reconnection: bool = True  # Auto-reconnect on failure

    # Performance settings
    batch_size: int = 100
    flush_interval: float = 1.0  # seconds

    def __post_init__(self):
        """Normalize alias parameters."""
        # Use the alias if set, otherwise use the primary name
        if self.host != "localhost":
            self.redis_host = self.host
        if self.port != 6379:
            self.redis_port = self.port
        if self.db != 0:
            self.redis_db = self.db
        if self.password is not None:
            self.redis_password = self.password


class EventBus:
    """
    In-memory event bus implementation.

    Provides simple async pub/sub messaging within a single process.
    """

    def __init__(self, config: Optional[EventBusConfig] = None):
        """
        Initialize the event bus.

        Args:
            config: Event bus configuration
        """
        self.config = config or EventBusConfig()
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue(
            maxsize=self.config.max_queue_size
        )
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        logger.info("EventBus initialized (in-memory mode)")

    async def subscribe(
        self,
        event_type: str,
        handler: EventHandler
    ) -> Callable[[], Awaitable[None]]:
        """
        Subscribe to events of a specific type.

        Args:
            event_type: Type of event to subscribe to (use ".*" for all)
            handler: Async function to call when event occurs

        Returns:
            Unsubscribe function
        """
        async with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            self._subscribers[event_type].append(handler)

            logger.debug(f"Subscribed to {event_type}: {handler.__name__}")

        async def unsubscribe():
            async with self._lock:
                if event_type in self._subscribers:
                    self._subscribers[event_type].remove(handler)

        return unsubscribe

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event: Event to publish
        """
        try:
            await self._event_queue.put(event)
            logger.debug(f"Event queued: {event.type} ({event.event_id})")
        except asyncio.QueueFull:
            logger.error(f"Event queue full, dropping event: {event.type}")

    async def _process_event(self, event: Event) -> None:
        """
        Process a single event by notifying all subscribers.

        Args:
            event: Event to process
        """
        # Find matching subscribers
        matching_handlers: List[EventHandler] = []

        async with self._lock:
            # Exact match
            if event.type in self._subscribers:
                matching_handlers.extend(self._subscribers[event.type])

            # Wildcard match
            if ".*" in self._subscribers:
                matching_handlers.extend(self._subscribers[".*"])

        # Notify all handlers concurrently
        if matching_handlers:
            tasks = [
                self._safe_call(handler, event)
                for handler in matching_handlers
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_call(self, handler: EventHandler, event: Event) -> None:
        """
        Safely call an event handler.

        Args:
            handler: Handler function
            event: Event to pass to handler
        """
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                f"Error in event handler {handler.__name__}: {e}",
                exc_info=True
            )

    async def _event_loop(self) -> None:
        """
        Main event processing loop.
        """
        logger.info("Event loop started")

        while self._running:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=self.config.flush_interval
                )
                await self._process_event(event)

            except asyncio.TimeoutError:
                # Timeout is expected, continue loop
                continue
            except Exception as e:
                logger.error(f"Error in event loop: {e}", exc_info=True)

        logger.info("Event loop stopped")

    async def start(self) -> None:
        """
        Start the event bus.
        """
        if self._running:
            logger.warning("EventBus already running")
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._event_loop())

        logger.info("EventBus started")

    async def stop(self) -> None:
        """
        Stop the event bus.
        """
        if not self._running:
            return

        self._running = False

        # Wait for worker task
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        # Process remaining events
        while not self._event_queue.empty():
            event = await self._event_queue.get()
            await self._process_event(event)

        logger.info("EventBus stopped")

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get event bus statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "running": self._running,
            "subscribers": {
                event_type: len(handlers)
                for event_type, handlers in self._subscribers.items()
            },
            "queue_size": self._event_queue.qsize(),
            "queue_max_size": self.config.max_queue_size,
        }


class RedisEventBus(EventBus):
    """
    Redis-backed event bus implementation.

    Provides distributed pub/sub messaging across multiple processes.
    Falls back to in-memory if Redis is not available.
    """

    def __init__(self, config: Optional[EventBusConfig] = None):
        """
        Initialize the Redis event bus.

        Args:
            config: Event bus configuration
        """
        super().__init__(config)
        self._redis_client = None
        self._pubsub = None
        self._listener_task: Optional[asyncio.Task] = None
        self._connection_state = "disconnected"

        # Try to connect to Redis
        if self.config.use_redis:
            self._connect_redis()

    @property
    def state(self) -> type("State"):  # type: ignore
        """Get connection state."""
        class State:
            value = self._connection_state

        return State()

    def connect(self) -> None:
        """
        Connect to the event bus.

        Synchronous connection method for compatibility.
        Actual connection happens when start() is called.
        """
        if self.config.use_redis and self._redis_client:
            self._connection_state = "connected"
            logger.info("EventBus connected (synchronous)")
        else:
            self._connection_state = "in_memory"
            logger.info("EventBus using in-memory mode")

    def _connect_redis(self) -> None:
        """
        Connect to Redis server.

        Note: This requires the redis package. Falls back to in-memory
        if redis is not available.
        """
        try:
            import redis.asyncio as aioredis

            self._redis_client = aioredis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=True
            )

            logger.info(
                f"Redis event bus configured: "
                f"{self.config.redis_host}:{self.config.redis_port}"
            )

        except ImportError:
            logger.warning(
                "redis package not available, falling back to in-memory event bus"
            )
            self.config.use_redis = False

    async def publish(self, event: Event) -> None:
        """
        Publish an event.

        If Redis is available, publishes to Redis channel.
        Otherwise, uses in-memory queue.

        Args:
            event: Event to publish
        """
        if self.config.use_redis and self._redis_client:
            try:
                # Publish to Redis
                channel = f"events:{event.type}"
                await self._redis_client.publish(channel, event.to_json())

                logger.debug(
                    f"Published to Redis: {channel} ({event.event_id})"
                )

            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}")
                # Fall back to in-memory
                await super().publish(event)
        else:
            # Use in-memory
            await super().publish(event)

    async def _redis_listener(self) -> None:
        """
        Listen for events from Redis.
        """
        if not self._redis_client:
            return

        try:
            self._pubsub = self._redis_client.pubsub()
            await self._pubsub.subscribe("events:*")

            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    try:
                        event = Event.from_json(message["data"])
                        await self._process_event(event)
                    except Exception as e:
                        logger.error(f"Error processing Redis event: {e}")

        except Exception as e:
            logger.error(f"Redis listener error: {e}")

    async def start(self) -> None:
        """
        Start the Redis event bus.
        """
        await super().start()

        if self.config.use_redis and self._redis_client:
            self._listener_task = asyncio.create_task(self._redis_listener())
            logger.info("Redis listener started")

    async def stop(self) -> None:
        """
        Stop the Redis event bus.
        """
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._pubsub:
            await self._pubsub.unsubscribe("events:*")
            await self._pubsub.close()

        if self._redis_client:
            await self._redis_client.close()

        await super().stop()
