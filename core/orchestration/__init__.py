"""
Resilience Module - Circuit breaker and atomic commit patterns
"""

# Try to import the full version, fall back to standalone
try:
    from .circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerError
except ImportError:
    from .circuit_breaker_standalone import CircuitBreaker, CircuitState, CircuitBreakerError

try:
    from .atomic_commit_manager import AtomicCommitManager
except ImportError:
    from .atomic_commit_standalone import AtomicCommitManager

__all__ = ['CircuitBreaker', 'CircuitState', 'CircuitBreakerError', 'AtomicCommitManager']
