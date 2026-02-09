"""
Type definitions for BlackBox 5 circuit breaker system.

This module provides the core types and enums used by the circuit breaker
implementation for state management and configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from threading import Lock


class CircuitState(str, Enum):
    """
    Circuit breaker states following the standard circuit breaker pattern.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is tripped, requests fail fast
    - HALF_OPEN: Testing if service has recovered
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __str__(self) -> str:
        return self.value


@dataclass
class CircuitBreakerConfig:
    """
    Configuration for a circuit breaker instance.

    Attributes:
        failure_threshold: Number of consecutive failures before opening
        timeout_seconds: Seconds to wait before transitioning from OPEN to HALF_OPEN
        success_threshold: Number of successes needed in HALF_OPEN to close circuit
        call_timeout: Maximum seconds to wait for a call to complete
        half_open_max_calls: Max calls allowed in HALF_OPEN state (default: 1)
        reset_timeout: Seconds before allowing another reset attempt (prevents thrashing)
        sliding_window_size: Number of recent calls to track for statistics
        exception_types: Tuple of exception types that should trigger failures
    """

    failure_threshold: int = 5
    timeout_seconds: float = 60.0
    success_threshold: int = 2
    call_timeout: float = 30.0
    half_open_max_calls: int = 1
    reset_timeout: float = 10.0
    sliding_window_size: int = 100

    # Exception types to catch
    exception_types: tuple = (Exception,)

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if self.timeout_seconds < 0:
            raise ValueError("timeout_seconds must be >= 0")
        if self.success_threshold < 1:
            raise ValueError("success_threshold must be >= 1")
        if self.call_timeout < 0:
            raise ValueError("call_timeout must be >= 0")
        if self.half_open_max_calls < 1:
            raise ValueError("half_open_max_calls must be >= 1")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'failure_threshold': self.failure_threshold,
            'timeout_seconds': self.timeout_seconds,
            'success_threshold': self.success_threshold,
            'call_timeout': self.call_timeout,
            'half_open_max_calls': self.half_open_max_calls,
            'reset_timeout': self.reset_timeout,
            'sliding_window_size': self.sliding_window_size,
        }


@dataclass
class CircuitBreakerStats:
    """
    Statistics for a circuit breaker instance.

    Attributes:
        total_calls: Total number of calls made
        successful_calls: Number of successful calls
        failed_calls: Number of failed calls
        current_failures: Current consecutive failure count
        last_failure_time: Timestamp of last failure
        last_success_time: Timestamp of last success
        state_transitions: Number of state transitions
        opened_at: When the circuit was opened (None if CLOSED)
        current_state: Current circuit state
        rejection_count: Number of calls rejected due to open circuit
    """

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    current_failures: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_transitions: int = 0
    opened_at: Optional[datetime] = None
    current_state: CircuitState = CircuitState.CLOSED
    rejection_count: int = 0

    # Thread safety
    _lock: Lock = field(default_factory=Lock)

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)."""
        with self._lock:
            if self.total_calls == 0:
                return 1.0
            return self.successful_calls / self.total_calls

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate (0.0 to 1.0)."""
        with self._lock:
            if self.total_calls == 0:
                return 0.0
            return self.failed_calls / self.total_calls

    @property
    def time_since_last_failure(self) -> Optional[float]:
        """Seconds since last failure."""
        with self._lock:
            if self.last_failure_time is None:
                return None
            return (datetime.now() - self.last_failure_time).total_seconds()

    @property
    def time_since_opened(self) -> Optional[float]:
        """Seconds since circuit was opened."""
        with self._lock:
            if self.opened_at is None:
                return None
            return (datetime.now() - self.opened_at).total_seconds()

    def record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            self.total_calls += 1
            self.successful_calls += 1
            self.current_failures = 0
            self.last_success_time = datetime.now()

    def record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            self.total_calls += 1
            self.failed_calls += 1
            self.current_failures += 1
            self.last_failure_time = datetime.now()

    def record_rejection(self) -> None:
        """Record a rejected call (circuit open)."""
        with self._lock:
            self.rejection_count += 1

    def transition_to(self, new_state: CircuitState) -> None:
        """Record a state transition."""
        with self._lock:
            if self.current_state != new_state:
                self.state_transitions += 1
                self.current_state = new_state

                # Track when circuit was opened
                if new_state == CircuitState.OPEN:
                    self.opened_at = datetime.now()
                elif new_state == CircuitState.CLOSED:
                    self.opened_at = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        with self._lock:
            return {
                'total_calls': self.total_calls,
                'successful_calls': self.successful_calls,
                'failed_calls': self.failed_calls,
                'current_failures': self.current_failures,
                'success_rate': self.success_rate,
                'failure_rate': self.failure_rate,
                'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
                'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None,
                'state_transitions': self.state_transitions,
                'opened_at': self.opened_at.isoformat() if self.opened_at else None,
                'current_state': self.current_state.value,
                'rejection_count': self.rejection_count,
                'time_since_last_failure': self.time_since_last_failure,
                'time_since_opened': self.time_since_opened,
            }

    def reset(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self.total_calls = 0
            self.successful_calls = 0
            self.failed_calls = 0
            self.current_failures = 0
            self.last_failure_time = None
            self.last_success_time = None
            self.state_transitions = 0
            self.opened_at = None
            self.rejection_count = 0


@dataclass
class CallResult:
    """
    Result of a circuit breaker protected call.

    Attributes:
        success: Whether the call succeeded
        exception: Exception if call failed
        duration_seconds: Time taken for the call
        was_rejected: Whether the call was rejected (circuit open)
        state_at_call: Circuit state when call was made
    """

    success: bool
    exception: Optional[Exception] = None
    duration_seconds: float = 0.0
    was_rejected: bool = False
    state_at_call: CircuitState = CircuitState.CLOSED

    @property
    def failed(self) -> bool:
        """Whether the call failed."""
        return not self.success and not self.was_rejected

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'success': self.success,
            'failed': self.failed,
            'was_rejected': self.was_rejected,
            'duration_seconds': self.duration_seconds,
            'state_at_call': self.state_at_call.value,
            'exception': str(self.exception) if self.exception else None,
        }


# Preset configurations for common use cases
class CircuitBreakerPresets:
    """Predefined circuit breaker configurations."""

    @staticmethod
    def default() -> CircuitBreakerConfig:
        """Default configuration for general use."""
        return CircuitBreakerConfig(
            failure_threshold=5,
            timeout_seconds=60.0,
            success_threshold=2,
            call_timeout=30.0,
        )

    @staticmethod
    def strict() -> CircuitBreakerConfig:
        """Strict configuration - opens faster, waits longer."""
        return CircuitBreakerConfig(
            failure_threshold=3,
            timeout_seconds=120.0,
            success_threshold=3,
            call_timeout=10.0,
        )

    @staticmethod
    def lenient() -> CircuitBreakerConfig:
        """Lenient configuration - tolerates more failures."""
        return CircuitBreakerConfig(
            failure_threshold=10,
            timeout_seconds=30.0,
            success_threshold=1,
            call_timeout=60.0,
        )

    @staticmethod
    def fast_recovery() -> CircuitBreakerConfig:
        """Fast recovery configuration - attempts recovery quickly."""
        return CircuitBreakerConfig(
            failure_threshold=5,
            timeout_seconds=10.0,
            success_threshold=1,
            call_timeout=30.0,
        )

    @staticmethod
    def for_agent(agent_type: str) -> CircuitBreakerConfig:
        """Get configuration based on agent type."""
        # AI/LLM agents - stricter timeout
        if agent_type in ('llm', 'ai', 'researcher', 'writer'):
            return CircuitBreakerConfig(
                failure_threshold=3,
                timeout_seconds=90.0,
                success_threshold=2,
                call_timeout=120.0,  # LLM calls can be slow
            )

        # I/O agents - tolerate temporary failures
        if agent_type in ('file', 'database', 'api'):
            return CircuitBreakerConfig(
                failure_threshold=5,
                timeout_seconds=30.0,
                success_threshold=2,
                call_timeout=15.0,
            )

        # Default
        return CircuitBreakerConfig.default()
