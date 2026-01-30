"""
Orchestration Module - Multi-agent coordination and workflow management
"""

# Optional resilience components - only import if available
try:
    from .resilience.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerError
except ImportError:
    CircuitBreaker = None
    CircuitState = None
    CircuitBreakerError = None

try:
    from .resilience.atomic_commit_manager import AtomicCommitManager
except ImportError:
    AtomicCommitManager = None

# Core orchestration components are always available
__all__ = []  # Components should be imported directly from their modules
