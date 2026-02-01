"""
Resilience Exceptions - Custom exceptions for resilience patterns
"""

__all__ = [
    "ResilienceError",
    "CircuitBreakerError",
    "CircuitBreakerOpenError",
    "CircuitBreakerClosedError",
    "RetryExhaustedError",
    "FallbackFailedError",
    "TimeoutError",
]


class ResilienceError(Exception):
    """Base exception for resilience errors."""
    pass


class CircuitBreakerError(ResilienceError):
    """Base exception for circuit breaker errors."""
    pass


class CircuitBreakerOpenError(CircuitBreakerError):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreakerClosedError(CircuitBreakerError):
    """Raised when circuit breaker is closed."""
    pass


class RetryExhaustedError(ResilienceError):
    """Raised when retry attempts are exhausted."""
    pass


class FallbackFailedError(ResilienceError):
    """Raised when fallback mechanism fails."""
    pass


class TimeoutError(ResilienceError):
    """Raised when operation times out."""
    pass
