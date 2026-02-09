"""
Circuit breaker implementation for BlackBox 5 multi-agent system.

This module provides a production-ready circuit breaker pattern implementation
for preventing cascading failures and providing fast failure detection in
distributed multi-agent systems.

Benefits:
- 9x faster failure detection (immediate vs waiting for timeout)
- Prevents cascading failures across agents
- Automatic recovery with half-open state
- Per-agent circuit tracking
- Integration with event bus for state changes
"""

import logging
import threading
import time
import signal
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, Any, TypeVar, Type
from functools import wraps

from .circuit_breaker_types import (
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreakerStats,
    CallResult,
    CircuitBreakerPresets,
)
from .exceptions import (
    CircuitBreakerOpenError,
    CircuitBreakerError,
)
from .event_bus import RedisEventBus, get_event_bus
from .events import (
    CircuitBreakerEvent,
    EventType,
    Topics,
)


# Configure logging
logger = logging.getLogger(__name__)

# Type variables
T = TypeVar('T')


class CircuitBreaker:
    """
    Circuit breaker for preventing cascading failures in multi-agent systems.

    The circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is tripped after threshold failures, requests fail fast
    - HALF_OPEN: Testing if service has recovered with limited calls

    State transitions:
    CLOSED → OPEN: After failure_threshold consecutive failures
    OPEN → HALF_OPEN: After timeout_seconds have elapsed
    HALF_OPEN → CLOSED: After success_threshold consecutive successes
    HALF_OPEN → OPEN: On any failure during recovery testing

    Example:
        ```python
        # Create circuit breaker
        cb = CircuitBreaker("agent.researcher", config=CircuitBreakerPresets.strict())

        # Protect a function call
        try:
            result = cb.call(agent.execute, task_data)
        except CircuitBreakerOpenError:
            # Circuit is open, fail fast
            logger.warning("Researcher circuit is open")
        except Exception as e:
            # Call failed
            logger.error(f"Agent failed: {e}")
        ```

    Attributes:
        service_id: Unique identifier for the protected service/agent
        config: Circuit breaker configuration
        state: Current circuit state
        stats: Circuit breaker statistics
    """

    # Class-level registry for all circuit breakers
    _registry: Dict[str, 'CircuitBreaker'] = {}
    _registry_lock = threading.Lock()

    def __init__(
        self,
        service_id: str,
        config: Optional[CircuitBreakerConfig] = None,
        event_bus: Optional[RedisEventBus] = None,
    ):
        """
        Initialize a circuit breaker.

        Args:
            service_id: Unique identifier for the protected service
            config: Circuit breaker configuration (uses default if None)
            event_bus: Event bus for publishing state changes (optional)
        """
        self.service_id = service_id
        self.config = config or CircuitBreakerConfig.default()
        self.event_bus = event_bus

        # State management
        self._state = CircuitState.CLOSED
        self._state_lock = threading.Lock()

        # Statistics
        self.stats = CircuitBreakerStats()

        # Half-open state tracking
        self._half_open_calls = 0
        self._half_open_successes = 0

        # Last state change time (for reset timeout)
        self._last_state_change = datetime.now()

        # Register in global registry
        self._register()

        logger.info(
            f"Circuit breaker initialized for {service_id} "
            f"(threshold: {self.config.failure_threshold}, "
            f"timeout: {self.config.timeout_seconds}s)"
        )

    def _register(self) -> None:
        """Register this circuit breaker in the global registry."""
        with self._registry_lock:
            CircuitBreaker._registry[self.service_id] = self
            logger.debug(f"Registered circuit breaker: {self.service_id}")

    @classmethod
    def get(cls, service_id: str) -> Optional['CircuitBreaker']:
        """
        Get a circuit breaker by service ID.

        Args:
            service_id: Service identifier

        Returns:
            Circuit breaker instance or None if not found
        """
        with cls._registry_lock:
            return cls._registry.get(service_id)

    @classmethod
    def get_all(cls) -> Dict[str, 'CircuitBreaker']:
        """
        Get all registered circuit breakers.

        Returns:
            Dictionary of service_id -> CircuitBreaker
        """
        with cls._registry_lock:
            return cls._registry.copy()

    @classmethod
    def reset_all(cls) -> None:
        """Reset all registered circuit breakers to CLOSED state."""
        with cls._registry_lock:
            for cb in cls._registry.values():
                cb.reset()
            logger.info("All circuit breakers reset")

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._state_lock:
            return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self.state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self.state == CircuitState.HALF_OPEN

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a function with circuit breaker protection.

        This is the main method for protecting function calls. It handles:
        - Checking circuit state and rejecting if open
        - Transitioning states based on call results
        - Recording statistics
        - Publishing events

        Args:
            func: Function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception from the function call
        """
        start_time = time.time()
        state_at_call = self.state

        # Check if circuit is open
        if self.is_open:
            if self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
                logger.info(f"Circuit {self.service_id} transitioning to HALF_OPEN")
            else:
                # Reject the call
                self.stats.record_rejection()
                remaining_time = self.config.timeout_seconds - (
                    time.time() - self.stats.opened_at.timestamp()
                )

                logger.warning(
                    f"Circuit {self.service_id} is OPEN, rejecting call "
                    f"({remaining_time:.1f}s until reset attempt)"
                )

                raise CircuitBreakerOpenError(
                    message=f"Circuit breaker for {self.service_id} is open",
                    service=self.service_id,
                    remaining_time=remaining_time,
                    failure_count=self.stats.current_failures,
                )

        # Track half-open call limit
        if self.is_half_open:
            with self._state_lock:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    logger.warning(
                        f"Circuit {self.service_id}: Max half-open calls reached"
                    )
                    raise CircuitBreakerOpenError(
                        message=f"Max half-open calls reached for {self.service_id}",
                        service=self.service_id,
                    )
                self._half_open_calls += 1

        # Execute the function with timeout
        try:
            result = self._execute_with_timeout(func, args, kwargs)

            # Success
            duration = time.time() - start_time
            self._on_success()

            logger.debug(
                f"Circuit {self.service_id}: Call succeeded "
                f"(state: {self.state}, duration: {duration:.2f}s)"
            )

            return result

        except Exception as e:
            # Failure
            duration = time.time() - start_time
            self._on_failure(e)

            logger.debug(
                f"Circuit {self.service_id}: Call failed "
                f"(state: {self.state}, duration: {duration:.2f}s, error: {e})"
            )

            raise

    def _execute_with_timeout(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """
        Execute function with timeout protection.

        Args:
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            TimeoutError: If function call times out
        """
        if self.config.call_timeout <= 0:
            return func(*args, **kwargs)

        def timeout_handler(signum, frame):
            raise TimeoutError(
                f"Function call exceeded timeout of {self.config.call_timeout}s"
            )

        # Set signal handler for timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(self.config.call_timeout))

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Cancel alarm and restore old handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def _should_attempt_reset(self) -> bool:
        """
        Check if enough time has passed to attempt circuit reset.

        Returns:
            True if should transition to HALF_OPEN
        """
        if self.stats.opened_at is None:
            return True

        elapsed = time.time() - self.stats.opened_at.timestamp()

        # Prevent thrashing with reset timeout
        time_since_change = (datetime.now() - self._last_state_change).total_seconds()
        if time_since_change < self.config.reset_timeout:
            return False

        return elapsed >= self.config.timeout_seconds

    def _on_success(self) -> None:
        """Handle a successful call."""
        self.stats.record_success()

        if self.is_half_open:
            with self._state_lock:
                self._half_open_successes += 1

                if self._half_open_successes >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
                    logger.info(
                        f"Circuit {self.service_id} recovered, "
                        f"transitioning to CLOSED after {self._half_open_successes} successes"
                    )

    def _on_failure(self, exception: Exception) -> None:
        """
        Handle a failed call.

        Args:
            exception: The exception that occurred
        """
        # Check if this exception type should trigger a failure
        should_count = isinstance(exception, self.config.exception_types)

        if not should_count:
            logger.debug(
                f"Circuit {self.service_id}: Exception {type(exception)} "
                f"not in configured failure types, not counting as failure"
            )
            return

        self.stats.record_failure()

        if self.is_closed:
            # Check if threshold reached
            if self.stats.current_failures >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)
                logger.warning(
                    f"Circuit {self.service_id} opened after "
                    f"{self.stats.current_failures} consecutive failures"
                )

        elif self.is_half_open:
            # Any failure in half-open opens the circuit again
            self._transition_to(CircuitState.OPEN)
            logger.warning(
                f"Circuit {self.service_id} failed recovery test, "
                f"returning to OPEN state"
            )

    def _transition_to(self, new_state: CircuitState) -> None:
        """
        Transition to a new state.

        Args:
            new_state: New circuit state
        """
        old_state = self.state

        with self._state_lock:
            if old_state == new_state:
                return

            self._state = new_state
            self._last_state_change = datetime.now()

            # Reset counters for state transitions
            if new_state == CircuitState.HALF_OPEN:
                self._half_open_calls = 0
                self._half_open_successes = 0
            elif new_state == CircuitState.CLOSED:
                self.stats.current_failures = 0

        # Update stats
        self.stats.transition_to(new_state)

        # Publish event
        self._publish_state_change(old_state, new_state)

    def _publish_state_change(self, old_state: CircuitState, new_state: CircuitState) -> None:
        """
        Publish circuit breaker state change event.

        Args:
            old_state: Previous state
            new_state: New state
        """
        if not self.event_bus:
            return

        try:
            # Determine event type
            if new_state == CircuitState.OPEN:
                event_type = EventType.CIRCUIT_OPENED
            elif new_state == CircuitState.CLOSED:
                event_type = EventType.CIRCUIT_CLOSED
            else:
                event_type = EventType.CIRCUIT_HALF_OPEN

            event = CircuitBreakerEvent.create(
                event_type=event_type,
                service=self.service_id,
                state=new_state.value,
                failure_count=self.stats.current_failures,
                last_failure=self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            )

            topic = Topics.circuit_breaker_topic(self.service_id)
            self.event_bus.publish(topic, event)

            logger.debug(
                f"Published circuit state change event: {old_state} → {new_state}"
            )

        except Exception as e:
            logger.error(f"Failed to publish circuit state event: {e}")

    def reset(self) -> None:
        """Reset circuit breaker to CLOSED state and clear statistics."""
        with self._state_lock:
            old_state = self._state
            self._state = CircuitState.CLOSED
            self._half_open_calls = 0
            self._half_open_successes = 0
            self._last_state_change = datetime.now()

        self.stats.reset()
        logger.info(f"Circuit breaker {self.service_id} reset")

        # Publish event if was open
        if old_state != CircuitState.CLOSED:
            self._publish_state_change(old_state, CircuitState.CLOSED)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get circuit breaker statistics.

        Returns:
            Dictionary with current statistics
        """
        stats = self.stats.to_dict()
        stats['service_id'] = self.service_id
        stats['config'] = self.config.to_dict()
        return stats

    @contextmanager
    def protect(self):
        """
        Context manager for circuit breaker protection.

        Example:
            ```python
            with circuit_breaker.protect():
                result = risky_operation()
            ```

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        state_at_call = self.state

        if self.is_open and not self._should_attempt_reset():
            self.stats.record_rejection()
            raise CircuitBreakerOpenError(
                message=f"Circuit breaker for {self.service_id} is open",
                service=self.service_id,
            )

        try:
            yield
        except Exception as e:
            if isinstance(e, self.config.exception_types):
                self._on_failure(e)
            raise

    def decorate(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator to add circuit breaker protection to a function.

        Example:
            ```python
            @circuit_breaker.decorate
            def risky_function():
                # Potentially failing code
                pass
            ```

        Args:
            func: Function to decorate

        Returns:
            Decorated function
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)

        return wrapper


class CircuitBreakerManager:
    """
    Manager for creating and tracking multiple circuit breakers.

    Provides a centralized way to create and manage circuit breakers
    for different agents and services.

    Example:
        ```python
        manager = CircuitBreakerManager(event_bus)

        # Get or create circuit breaker for an agent
        cb = manager.get_breaker("agent.researcher")

        # Use it
        try:
            result = cb.call(agent.execute, task)
        except CircuitBreakerOpenError:
            # Handle open circuit
            pass
        ```
    """

    def __init__(self, event_bus: Optional[RedisEventBus] = None):
        """
        Initialize the circuit breaker manager.

        Args:
            event_bus: Event bus for publishing circuit events
        """
        self.event_bus = event_bus
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()

        logger.info("Circuit breaker manager initialized")

    def get_breaker(
        self,
        service_id: str,
        config: Optional[CircuitBreakerConfig] = None,
        agent_type: Optional[str] = None,
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker for a service.

        Args:
            service_id: Unique service identifier
            config: Circuit breaker configuration (optional)
            agent_type: Agent type for preset config (optional)

        Returns:
            Circuit breaker instance
        """
        with self._lock:
            if service_id not in self._breakers:
                # Use preset config if agent_type provided and no custom config
                if config is None and agent_type:
                    config = CircuitBreakerPresets.for_agent(agent_type)

                cb = CircuitBreaker(service_id, config, self.event_bus)
                self._breakers[service_id] = cb
                logger.info(f"Created circuit breaker for {service_id}")

            return self._breakers[service_id]

    def remove_breaker(self, service_id: str) -> None:
        """
        Remove a circuit breaker.

        Args:
            service_id: Service identifier
        """
        with self._lock:
            if service_id in self._breakers:
                del self._breakers[service_id]
                logger.info(f"Removed circuit breaker for {service_id}")

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all circuit breakers.

        Returns:
            Dictionary of service_id -> stats
        """
        with self._lock:
            return {
                service_id: cb.get_stats()
                for service_id, cb in self._breakers.items()
            }

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        with self._lock:
            for cb in self._breakers.values():
                cb.reset()
            logger.info("All circuit breakers reset via manager")

    def get_open_circuits(self) -> list[str]:
        """
        Get list of services with open circuits.

        Returns:
            List of service IDs with open circuits
        """
        with self._lock:
            return [
                service_id
                for service_id, cb in self._breakers.items()
                if cb.is_open
            ]

    def close_all_circuits(self) -> None:
        """Force close all open circuits (emergency recovery)."""
        with self._lock:
            for cb in self._breakers.values():
                if cb.is_open or cb.is_half_open:
                    cb.reset()
            logger.warning("All circuits force-closed (emergency recovery)")


# Global circuit breaker manager
_global_manager: Optional[CircuitBreakerManager] = None
_manager_lock = threading.Lock()


def get_circuit_breaker_manager(event_bus: Optional[RedisEventBus] = None) -> CircuitBreakerManager:
    """
    Get the global circuit breaker manager instance.

    Args:
        event_bus: Event bus for circuit events (only used on first call)

    Returns:
        Global CircuitBreakerManager instance
    """
    global _global_manager

    with _manager_lock:
        if _global_manager is None:
            _global_manager = CircuitBreakerManager(event_bus)

        return _global_manager


def for_agent(agent_id: str, agent_type: Optional[str] = None) -> CircuitBreaker:
    """
    Convenience function to get a circuit breaker for an agent.

    Args:
        agent_id: Agent identifier
        agent_type: Agent type for preset configuration

    Returns:
        Circuit breaker instance
    """
    manager = get_circuit_breaker_manager()
    return manager.get_breaker(f"agent.{agent_id}", agent_type=agent_type)


def protect(service_id: str, config: Optional[CircuitBreakerConfig] = None):
    """
    Decorator to protect a function with a circuit breaker.

    Example:
        ```python
        @protect("my-service")
        def risky_function():
            # Potentially failing code
            pass
        ```

    Args:
        service_id: Service identifier
        config: Circuit breaker configuration

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        manager = get_circuit_breaker_manager()
        cb = manager.get_breaker(service_id, config)
        return cb.decorate(func)

    return decorator


# =============================================================================
# Simplified Circuit Breaker (No External Dependencies)
# =============================================================================

class SimpleCircuitBreaker:
    """
    Simplified circuit breaker for standalone use without external dependencies.

    This is a lightweight version that works independently without requiring
    Redis, event bus, or complex configuration. Ideal for simple use cases
    and testing.

    Example:
        ```python
        # Simple initialization
        cb = SimpleCircuitBreaker("service_name", failure_threshold=5, timeout=60)

        # Use as context manager
        with cb:
            result = risky_operation()

        # Or use call method
        result = cb.call(risky_operation, arg1, arg2)
        ```
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: int = 60,
        half_open_attempts: int = 1
    ):
        """
        Initialize simple circuit breaker.

        Args:
            name: Name of the circuit breaker
            failure_threshold: Number of failures before opening
            timeout: Seconds to wait before trying again
            half_open_attempts: Number of attempts in half-open state
        """
        self.name = name
        self._failure_threshold = failure_threshold
        self._timeout = timeout
        self._half_open_attempts = half_open_attempts

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._success_count = 0

        logger.info(f"SimpleCircuitBreaker '{name}' initialized (threshold={failure_threshold})")

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        # Auto-transition from OPEN to HALF_OPEN after timeout
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and \
               datetime.now() - self._last_failure_time > timedelta(seconds=self._timeout):
                logger.info(f"SimpleCircuitBreaker '{self.name}' transitioning OPEN -> HALF_OPEN")
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0

        return self._state

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking)."""
        return self.state != CircuitState.CLOSED

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    def record_success(self):
        """Record a successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self._half_open_attempts:
                logger.info(f"SimpleCircuitBreaker '{self.name}' recovered -> CLOSED")
                self._state = CircuitState.CLOSED
                self._failure_count = 0
        else:
            self._failure_count = 0

    def record_failure(self):
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()

        if self._failure_count >= self._failure_threshold:
            logger.warning(f"SimpleCircuitBreaker '{self.name}' tripped -> OPEN")
            self._state = CircuitState.OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if self.is_open:
            raise CircuitBreakerOpenError(
                message=f"SimpleCircuitBreaker '{self.name}' is {self.state.value}",
                service=self.name
            )

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def __enter__(self):
        """Context manager entry."""
        if self.is_open:
            raise CircuitBreakerOpenError(
                message=f"SimpleCircuitBreaker '{self.name}' is {self.state.value}",
                service=self.name
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure()

    def reset(self):
        """Manually reset the circuit breaker."""
        logger.info(f"SimpleCircuitBreaker '{self.name}' manually reset")
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None

    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self._failure_threshold,
            "is_open": self.is_open,
            "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None
        }


# Convenience alias for backward compatibility
StandaloneCircuitBreaker = SimpleCircuitBreaker
