"""
Circuit breaker examples for BlackBox 5 multi-agent system.

This module provides practical examples demonstrating circuit breaker usage
in various scenarios common to multi-agent systems.

Run examples:
    python -m blackbox5.engine.core.circuit_breaker_examples
"""

import logging
import time
import random
from typing import Optional

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    protect,
    for_agent,
)
from .circuit_breaker_types import (
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreakerPresets,
)
from .exceptions import CircuitBreakerOpenError


# Configure logging for examples
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Basic Usage
# ============================================================================

def example_1_basic_usage():
    """Demonstrate basic circuit breaker usage."""
    print("\n" + "=" * 70)
    print("Example 1: Basic Circuit Breaker Usage")
    print("=" * 70)

    # Create a circuit breaker with default config
    cb = CircuitBreaker(
        service_id="example.basic",
        config=CircuitBreakerConfig(
            failure_threshold=3,
            timeout_seconds=5.0,
            success_threshold=2,
        )
    )

    # Simulated function that can fail
    def unreliable_function(should_fail: bool = False):
        if should_fail:
            raise ValueError("Simulated failure")
        return "Success!"

    print("\n1. Testing successful calls (circuit CLOSED)...")
    for i in range(2):
        try:
            result = cb.call(unreliable_function, should_fail=False)
            print(f"   Call {i+1}: {result}")
        except Exception as e:
            print(f"   Call {i+1}: Failed - {e}")

    print(f"\n   Circuit state: {cb.state}")
    print(f"   Stats: {cb.get_stats()['current_failures']} failures")

    print("\n2. Triggering failures to open circuit...")
    for i in range(3):
        try:
            result = cb.call(unreliable_function, should_fail=True)
            print(f"   Call {i+1}: {result}")
        except Exception as e:
            print(f"   Call {i+1}: Failed - {e}")

    print(f"\n   Circuit state: {cb.state}")
    print(f"   Stats: {cb.get_stats()}")

    print("\n3. Attempting call while circuit is OPEN...")
    try:
        result = cb.call(unreliable_function, should_fail=False)
        print(f"   Call result: {result}")
    except CircuitBreakerOpenError as e:
        print(f"   Call rejected - Circuit is OPEN: {e.message}")
        print(f"   Details: {e.details}")

    print("\n4. Waiting for timeout and testing recovery...")
    print("   Waiting 6 seconds...")
    time.sleep(6)

    # This should transition to HALF_OPEN
    for i in range(2):
        try:
            result = cb.call(unreliable_function, should_fail=False)
            print(f"   Call {i+1}: {result}")
        except Exception as e:
            print(f"   Call {i+1}: Failed - {e}")
        print(f"   Circuit state after call {i+1}: {cb.state}")

    print(f"\n   Final circuit state: {cb.state}")
    print(f"   Final stats: {cb.get_stats()}")


# ============================================================================
# Example 2: Agent Execution with Circuit Breaker
# ============================================================================

class MockAgent:
    """Mock agent for demonstration."""

    def __init__(self, agent_id: str, failure_rate: float = 0.3):
        self.agent_id = agent_id
        self.failure_rate = failure_rate

    def execute(self, task: str) -> str:
        """Execute a task with potential failure."""
        if random.random() < self.failure_rate:
            raise RuntimeError(f"Agent {self.agent_id} failed on task: {task}")

        logger.info(f"Agent {self.agent_id} completed: {task}")
        return f"Task '{task}' completed by {self.agent_id}"


def example_2_agent_execution():
    """Demonstrate circuit breaker protecting agent execution."""
    print("\n" + "=" * 70)
    print("Example 2: Agent Execution with Circuit Breaker")
    print("=" * 70)

    # Create agent with high failure rate
    agent = MockAgent("researcher", failure_rate=0.7)

    # Create circuit breaker for this agent
    cb = CircuitBreaker(
        service_id="agent.researcher",
        config=CircuitBreakerConfig(
            failure_threshold=3,
            timeout_seconds=10.0,
            success_threshold=2,
            call_timeout=5.0,
        )
    )

    print("\n1. Executing tasks with circuit breaker protection...")
    tasks = [
        "Research market trends",
        "Analyze competitor data",
        "Compile report",
        "Search databases",
        "Summarize findings",
    ]

    for i, task in enumerate(tasks, 1):
        try:
            result = cb.call(agent.execute, task)
            print(f"   Task {i}: {result}")
        except CircuitBreakerOpenError as e:
            print(f"   Task {i}: BLOCKED - Circuit is open")
            print(f"      Agent {agent.agent_id} is failing too much")
            print(f"      Circuit will reset in {e.details.get('remaining_seconds', 0):.1f}s")
        except Exception as e:
            print(f"   Task {i}: FAILED - {e}")

        print(f"   Circuit state: {cb.state}")
        print(f"   Failure count: {cb.stats.current_failures}")
        print()

    print("\n2. Circuit breaker statistics:")
    stats = cb.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")


# ============================================================================
# Example 3: Custom Configuration
# ============================================================================

def example_3_custom_configuration():
    """Demonstrate different circuit breaker configurations."""
    print("\n" + "=" * 70)
    print("Example 3: Custom Circuit Breaker Configurations")
    print("=" * 70)

    # Create circuit breakers with different presets
    configs = {
        "strict": CircuitBreakerPresets.strict(),
        "lenient": CircuitBreakerPresets.lenient(),
        "fast_recovery": CircuitBreakerPresets.fast_recovery(),
    }

    print("\n1. Configuration comparison:")
    for name, config in configs.items():
        print(f"\n   {name.upper()} Configuration:")
        print(f"      Failure threshold: {config.failure_threshold}")
        print(f"      Timeout: {config.timeout_seconds}s")
        print(f"      Success threshold: {config.success_threshold}")
        print(f"      Call timeout: {config.call_timeout}s")

    # Test with strict configuration
    print("\n2. Testing strict configuration:")
    cb_strict = CircuitBreaker("test.strict", config=configs["strict"])

    def failing_function():
        raise ValueError("Always fails")

    # Trigger circuit open
    for i in range(5):
        try:
            cb_strict.call(failing_function)
        except Exception:
            pass

    print(f"   Circuit opened after {cb_strict.stats.current_failures} failures")
    print(f"   State: {cb_strict.state}")
    print(f"   Will wait {configs['strict'].timeout_seconds}s before retry")


# ============================================================================
# Example 4: Circuit State Monitoring
# ============================================================================

def example_4_state_monitoring():
    """Demonstrate circuit breaker state monitoring."""
    print("\n" + "=" * 70)
    print("Example 4: Circuit State Monitoring")
    print("=" * 70)

    cb = CircuitBreaker(
        "monitoring.example",
        config=CircuitBreakerConfig(
            failure_threshold=2,
            timeout_seconds=3.0,
        )
    )

    print("\n1. Monitoring circuit state over time:")

    def monitored_call(attempt: int):
        """Make a monitored call."""
        print(f"\n   Attempt {attempt}:")
        print(f"      State: {cb.state}")
        print(f"      Failures: {cb.stats.current_failures}")
        print(f"      Total calls: {cb.stats.total_calls}")
        print(f"      Success rate: {cb.stats.success_rate:.2%}")

        # Simulate a call
        should_fail = attempt < 2  # First two calls fail
        try:
            result = cb.call(lambda: "OK" if not should_fail else (_ for _ in ()).throw(ValueError("Fail")))
            print(f"      Result: {result}")
            return True
        except CircuitBreakerOpenError:
            print(f"      Result: BLOCKED (circuit open)")
            return False
        except Exception as e:
            print(f"      Result: FAILED - {e}")
            return False

    # Make several calls
    for i in range(1, 6):
        monitored_call(i)
        if i == 2:
            print("\n   Waiting 4 seconds for circuit reset...")
            time.sleep(4)

    print("\n2. Final statistics:")
    stats = cb.get_stats()
    print(f"   Total calls: {stats['total_calls']}")
    print(f"   Successful: {stats['successful_calls']}")
    print(f"   Failed: {stats['failed_calls']}")
    print(f"   Rejected: {stats['rejection_count']}")
    print(f"   State transitions: {stats['state_transitions']}")
    print(f"   Current state: {stats['current_state']}")


# ============================================================================
# Example 5: Half-Open State Recovery
# ============================================================================

def example_5_half_open_recovery():
    """Demonstrate half-open state and recovery process."""
    print("\n" + "=" * 70)
    print("Example 5: Half-Open State Recovery")
    print("=" * 70)

    # Flaky service - fails sometimes
    call_count = [0]

    def flaky_service():
        call_count[0] += 1
        # Fails on calls 1-3, succeeds on 4-5
        if call_count[0] <= 3:
            raise ConnectionError("Service unavailable")
        return f"Service response {call_count[0]}"

    cb = CircuitBreaker(
        "flaky.service",
        config=CircuitBreakerConfig(
            failure_threshold=2,
            timeout_seconds=2.0,
            success_threshold=2,  # Need 2 successes to close
            half_open_max_calls=3,  # Allow up to 3 test calls
        )
    )

    print("\n1. Triggering circuit to OPEN...")
    for i in range(3):
        try:
            cb.call(flaky_service)
        except Exception as e:
            print(f"   Call {i+1}: Failed - {e}")
        print(f"   State: {cb.state}, Failures: {cb.stats.current_failures}")

    print(f"\n   Circuit is now: {cb.state}")

    print("\n2. Waiting for timeout to enter HALF_OPEN...")
    time.sleep(2.5)

    print("\n3. Testing recovery in HALF_OPEN state...")
    for i in range(4):
        try:
            result = cb.call(flaky_service)
            print(f"   Test call {i+1}: SUCCESS - {result}")
        except CircuitBreakerOpenError:
            print(f"   Test call {i+1}: BLOCKED (circuit still open)")
        except Exception as e:
            print(f"   Test call {i+1}: FAILED - {e}")

        print(f"   State: {cb.state}")
        print(f"   Half-open successes: {cb._half_open_successes}/{cb.config.success_threshold}")

        if cb.is_closed:
            print("\n   Circuit recovered! State is CLOSED")
            break

    print(f"\n   Final state: {cb.state}")
    print(f"   Total calls: {cb.stats.total_calls}")
    print(f"   Success rate: {cb.stats.success_rate:.2%}")


# ============================================================================
# Example 6: Integration with Event Bus
# ============================================================================

def example_6_event_bus_integration():
    """Demonstrate circuit breaker event publishing."""
    print("\n" + "=" * 70)
    print("Example 6: Event Bus Integration")
    print("=" * 70)

    # Note: This example demonstrates the integration pattern
    # In production, you'd have an actual Redis event bus

    print("\n1. Creating circuit breaker with event bus integration:")
    print("   (In production, would publish to Redis event bus)")

    class EventTracker:
        """Mock event tracker for demonstration."""

        def __init__(self):
            self.events = []

        def track(self, event_type: str, service: str, state: str):
            """Track a circuit breaker event."""
            self.events.append({
                'type': event_type,
                'service': service,
                'state': state,
                'timestamp': time.time(),
            })
            print(f"   Event: {event_type} - {service} → {state}")

    tracker = EventTracker()

    # Create circuit breaker and override event publishing for demo
    cb = CircuitBreaker("demo.service")

    # Monkey-patch for demonstration
    original_publish = cb._publish_state_change

    def mock_publish(old_state, new_state):
        event_type = f"CIRCUIT_{new_state.name}"
        tracker.track(event_type, cb.service_id, new_state.value)

    cb._publish_state_change = mock_publish

    print("\n2. Triggering state transitions to see events:")

    def failing_call():
        raise ValueError("Simulated failure")

    # Trigger CLOSED -> OPEN
    print("\n   Triggering failures...")
    for i in range(3):
        try:
            cb.call(failing_call)
        except Exception:
            pass

    print(f"\n   State: {cb.state}")

    # Trigger OPEN -> HALF_OPEN -> CLOSED
    print("\n   Waiting for timeout...")
    time.sleep(3)

    print("\n   Attempting recovery...")
    for i in range(2):
        try:
            cb.call(lambda: "OK")
        except Exception:
            pass

    print(f"\n   Final state: {cb.state}")

    print("\n3. Events captured:")
    for event in tracker.events:
        print(f"   {event}")


# ============================================================================
# Example 7: Timeout Handling
# ============================================================================

def example_7_timeout_handling():
    """Demonstrate timeout protection in circuit breaker."""
    print("\n" + "=" * 70)
    print("Example 7: Timeout Handling")
    print("=" * 70)

    def slow_function(seconds: float):
        """Function that takes a long time."""
        print(f"   Starting slow operation ({seconds}s)...")
        time.sleep(seconds)
        return "Completed"

    # Create circuit breaker with 2-second timeout
    cb = CircuitBreaker(
        "slow.service",
        config=CircuitBreakerConfig(
            failure_threshold=2,
            call_timeout=2.0,  # 2 second timeout
        )
    )

    print("\n1. Testing timeout protection:")

    # Fast call - should succeed
    print("\n   Call 1: Fast operation (1s)")
    try:
        result = cb.call(slow_function, 1.0)
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Error: {e}")

    # Slow call - should timeout
    print("\n   Call 2: Slow operation (3s)")
    try:
        result = cb.call(slow_function, 3.0)
        print(f"   Result: {result}")
    except TimeoutError as e:
        print(f"   Timeout: {e}")
        print(f"   This counts as a failure!")

    print(f"\n   Circuit state: {cb.state}")
    print(f"   Failure count: {cb.stats.current_failures}")

    # Another slow call to trigger circuit open
    print("\n   Call 3: Another slow operation")
    try:
        result = cb.call(slow_function, 3.0)
        print(f"   Result: {result}")
    except TimeoutError as e:
        print(f"   Timeout: {e}")

    print(f"\n   Circuit state: {cb.state}")
    print(f"   Failure count: {cb.stats.current_failures}")


# ============================================================================
# Example 8: Multiple Agents with Independent Circuits
# ============================================================================

def example_8_multiple_agents():
    """Demonstrate managing multiple circuit breakers for different agents."""
    print("\n" + "=" * 70)
    print("Example 8: Multiple Agents with Independent Circuits")
    print("=" * 70)

    # Create circuit breaker manager
    manager = CircuitBreakerManager()

    # Create multiple agents with different failure rates
    agents = {
        "coder": MockAgent("coder", failure_rate=0.1),  # Reliable
        "writer": MockAgent("writer", failure_rate=0.5),  # Flaky
        "researcher": MockAgent("researcher", failure_rate=0.8),  # Very flaky
    }

    print("\n1. Creating circuit breakers for each agent:")
    for agent_id, agent in agents.items():
        # Get circuit breaker with agent-type-specific config
        cb = manager.get_breaker(f"agent.{agent_id}", agent_type=agent_id)
        print(f"   {agent_id}: {cb.service_id}")
        print(f"      Threshold: {cb.config.failure_threshold}")
        print(f"      Timeout: {cb.config.timeout_seconds}s")

    print("\n2. Executing tasks across all agents:")
    tasks = ["Task A", "Task B", "Task C", "Task D", "Task E"]

    for i, task in enumerate(tasks, 1):
        print(f"\n   Round {i}: {task}")

        for agent_id, agent in agents.items():
            cb = manager.get_breaker(f"agent.{agent_id}")
            try:
                result = cb.call(agent.execute, task)
                print(f"      {agent_id}: {result}")
            except CircuitBreakerOpenError:
                print(f"      {agent_id}: BLOCKED (circuit open)")
            except Exception as e:
                print(f"      {agent_id}: Failed")

    print("\n3. Circuit breaker states:")
    all_stats = manager.get_all_stats()
    for service_id, stats in all_stats.items():
        print(f"\n   {service_id}:")
        print(f"      State: {stats['current_state']}")
        print(f"      Total calls: {stats['total_calls']}")
        print(f"      Success rate: {stats['success_rate']:.2%}")
        print(f"      Rejections: {stats['rejection_count']}")

    print("\n4. Open circuits:")
    open_circuits = manager.get_open_circuits()
    if open_circuits:
        print(f"   {len(open_circuits)} circuits are open:")
        for service in open_circuits:
            print(f"      - {service}")
    else:
        print("   No circuits are open")


# ============================================================================
# Example 9: Decorator Usage
# ============================================================================

def example_9_decorator_usage():
    """Demonstrate using circuit breaker as a decorator."""
    print("\n" + "=" * 70)
    print("Example 9: Decorator Usage")
    print("=" * 70)

    # Create circuit breaker
    cb = CircuitBreaker("decorator.example")

    print("\n1. Using circuit breaker as a decorator:")

    @cb.decorate
    def protected_function(value: int) -> int:
        """Function protected by circuit breaker."""
        if value < 0:
            raise ValueError("Value must be positive")
        return value * 2

    # Test the decorated function
    print("\n   Calling with positive value:")
    try:
        result = protected_function(5)
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n   Calling with negative value (will fail):")
    for i in range(3):
        try:
            result = protected_function(-1)
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   Error: {e}")

    print(f"\n   Circuit state: {cb.state}")

    print("\n2. Using the @protect decorator:")

    @protect("decorator.service", config=CircuitBreakerConfig(failure_threshold=2))
    def another_protected_function(x: int) -> int:
        if x == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return 100 // x

    for i in [5, 0, 0]:
        try:
            result = another_protected_function(i)
            print(f"   {result}")
        except Exception as e:
            print(f"   Error: {e}")


# ============================================================================
# Example 10: Context Manager Usage
# ============================================================================

def example_10_context_manager():
    """Demonstrate using circuit breaker as a context manager."""
    print("\n" + "=" * 70)
    print("Example 10: Context Manager Usage")
    print("=" * 70)

    cb = CircuitBreaker(
        "context.example",
        config=CircuitBreakerConfig(failure_threshold=2)
    )

    print("\n1. Using circuit breaker as context manager:")

    def risky_operation():
        raise RuntimeError("Operation failed")

    # Successful usage
    print("\n   Attempting operation with context manager:")
    try:
        with cb.protect():
            print("   Executing operation...")
            # This would succeed if we had a real operation
            print("   Operation completed")
    except Exception as e:
        print(f"   Error: {e}")

    print(f"   State: {cb.state}")

    # Failed usage
    print("\n   Triggering failures:")
    for i in range(3):
        try:
            with cb.protect():
                risky_operation()
        except Exception as e:
            print(f"   Error: {e}")
        print(f"   State: {cb.state}")


# ============================================================================
# Main runner
# ============================================================================

def run_all_examples():
    """Run all circuit breaker examples."""
    print("\n" + "=" * 70)
    print("BlackBox 5 Circuit Breaker Examples")
    print("=" * 70)

    examples = [
        ("Basic Usage", example_1_basic_usage),
        ("Agent Execution", example_2_agent_execution),
        ("Custom Configuration", example_3_custom_configuration),
        ("State Monitoring", example_4_state_monitoring),
        ("Half-Open Recovery", example_5_half_open_recovery),
        ("Event Bus Integration", example_6_event_bus_integration),
        ("Timeout Handling", example_7_timeout_handling),
        ("Multiple Agents", example_8_multiple_agents),
        ("Decorator Usage", example_9_decorator_usage),
        ("Context Manager", example_10_context_manager),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"   {i}. {name}")

    print("\n" + "-" * 70)

    # Run all examples
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            logger.error(f"Example '{name}' failed: {e}", exc_info=True)

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_examples()
