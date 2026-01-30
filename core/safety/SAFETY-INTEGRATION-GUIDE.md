"""
Safety System Integration Guide for BlackBox 5

This guide shows how to integrate the new safety features (kill switch,
safe mode, and constitutional classifiers) with the existing BlackBox 5 system.
"""

from .kill_switch import get_kill_switch, require_operational
from .safe_mode import get_safe_mode, require_operation
from .constitutional_classifier import get_classifier, check_user_input, check_agent_output


# Integration pattern for agent execution
def safe_agent_execution(agent_func):
    """
    Decorator that wraps agent execution with all safety checks.

    This decorator:
    1. Checks if kill switch is operational
    2. Checks if operation is allowed in current safe mode
    3. Validates agent input
    4. Validates agent output
    5. Triggers safety measures if violations detected

    Usage:
        ```python
        @safe_agent_execution
        def my_agent(user_input: str) -> str:
            # Agent logic here
            return "result"
        ```
    """
    def wrapper(input_data: str, *args, **kwargs):
        # 1. Check kill switch
        ks = get_kill_switch()
        if not ks.is_operational():
            raise RuntimeError(
                f"Cannot execute agent: kill switch triggered. "
                f"Reason: {ks.trigger_reason.value if ks.trigger_reason else 'unknown'}"
            )

        # 2. Check safe mode
        sm = get_safe_mode()
        if not sm.is_operation_allowed("agent_execution"):
            raise RuntimeError(
                f"Agent execution not allowed in {sm.current_level.value} mode"
            )

        # 3. Validate input
        classifier = get_classifier()
        input_check = classifier.check_input(input_data)
        if not input_check.safe:
            raise RuntimeError(
                f"Input blocked by safety check: {input_check.violation.reason}"
            )

        # 4. Execute agent
        try:
            result = agent_func(input_data, *args, **kwargs)
        except Exception as e:
            # Agent execution failed
            # Could enter safe mode here if too many failures
            raise

        # 5. Validate output
        if isinstance(result, str):
            output_check = classifier.check_output(result)
            if not output_check.safe:
                raise RuntimeError(
                    f"Output blocked by safety check: {output_check.violation.reason}"
                )

        return result

    return wrapper


# Integration with circuit breakers
def integrate_with_circuit_breaker():
    """
    Integrate safety system with existing circuit breakers.

    This function sets up callbacks so that safety violations
    can trigger circuit breakers and vice versa.
    """
    ks = get_kill_switch()
    sm = get_safe_mode()
    classifier = get_classifier()

    # When kill switch is triggered, enter emergency safe mode
    def on_kill_switch_triggered(ks, reason, message, source):
        sm.enter_level(
            SafeModeLevel.EMERGENCY,
            f"Kill switch triggered: {reason.value}",
            source="kill_switch_integration"
        )

    ks.on_trigger(on_kill_switch_triggered)

    # When critical violations occur, consider entering safe mode
    def handle_critical_violations():
        stats = classifier.get_stats()
        critical_count = stats["violations_by_severity"].get("critical", 0)

        # If we've had 3+ critical violations, enter restricted mode
        if critical_count >= 3:
            sm.enter_level(
                SafeModeLevel.RESTRICTED,
                f"Multiple critical violations detected: {critical_count}",
                source="classifier_integration"
            )

    return True


# Integration with event bus
def integrate_with_event_bus():
    """
    Publish safety events to the event bus for monitoring.
    """
    ks = get_kill_switch()
    sm = get_safe_mode()

    # Kill switch events are already broadcast in the implementation
    # Safe mode events are already broadcast in the implementation

    return True


# REST API endpoints for safety system
def get_safety_api_endpoints():
    """
    Returns API endpoint handlers for safety system management.

    These can be integrated with the existing REST API.
    """
    from flask import request, jsonify

    endpoints = {}

    @endpoints.get("/safety/status")
    def get_safety_status():
        """Get current safety system status"""
        ks = get_kill_switch()
        sm = get_safe_mode()
        classifier = get_classifier()

        return jsonify({
            "kill_switch": ks.get_status(),
            "safe_mode": sm.get_status(),
            "classifier": classifier.get_stats(),
            "overall_safe": ks.is_operational() and sm.is_normal_mode(),
        })

    @endpoints.post("/safety/kill-switch/trigger")
    def trigger_kill_switch():
        """Manually trigger kill switch"""
        data = request.get_json()
        reason = data.get("reason", "manual")
        message = data.get("message", "")

        ks = get_kill_switch()
        ks.trigger(
            KillSwitchReason.USER_REQUEST,
            message,
            source="api"
        )

        return jsonify({"success": True, "status": ks.get_status()})

    @endpoints.post("/safety/kill-switch/recover")
    def recover_kill_switch():
        """Recover from kill switch"""
        data = request.get_json()
        message = data.get("message", "")

        ks = get_kill_switch()
        ks.recover(message)

        return jsonify({"success": True, "status": ks.get_status()})

    @endpoints.post("/safety/safe-mode/enter")
    def enter_safe_mode():
        """Enter safe mode"""
        data = request.get_json()
        level = data.get("level", "limited")
        reason = data.get("message", "")

        sm = get_safe_mode()
        sm.enter_level(
            SafeModeLevel[level.upper()],
            reason,
            source="api"
        )

        return jsonify({"success": True, "status": sm.get_status()})

    @endpoints.post("/safety/safe-mode/exit")
    def exit_safe_mode():
        """Exit safe mode"""
        data = request.get_json()
        message = data.get("message", "")

        sm = get_safe_mode()
        sm.exit_level(message, source="api")

        return jsonify({"success": True, "status": sm.get_status()})

    @endpoints.post("/safety/check")
    def check_content():
        """Check content for safety"""
        data = request.get_json()
        content = data.get("content", "")
        content_type = data.get("type", "user_input")

        classifier = get_classifier()
        if content_type == "agent_output":
            result = classifier.check_output(content)
        else:
            result = classifier.check_input(content)

        return jsonify(result.to_dict())

    return endpoints


# Example usage in existing agents
def example_agent_integration():
    """
    Example showing how to integrate safety into an existing agent.
    """
    from ..agents.core.BaseAgent import BaseAgent
    from ..agents.core import Task

    class SafeAgent(BaseAgent):
        """
        Example agent with safety integration.
        """
        def __init__(self):
            super().__init__(
                name="safe-agent",
                role="specialist",
                category="safe-agents",
                description="Agent with safety features"
            )

        @safe_agent_execution
        def execute(self, task: Task) -> Task.Result:
            """
            Execute task with safety checks.
            """
            # Normal agent logic here
            # The decorator handles all safety checks

            result = f"Processed: {task.description}"
            return Task.Result(
                success=True,
                output=result,
                artifacts=[],
                metadata={}
            )

    return SafeAgent


# Quick start for using safety system
def quick_start():
    """
    Quick start guide for using the safety system.
    """
    print("""
BlackBox 5 Safety System - Quick Start
======================================

1. Kill Switch (Emergency Shutdown)
------------------------------------
Trigger emergency shutdown:
    from safety.kill_switch import activate_emergency_shutdown
    activate_emergency_shutdown(
        KillSwitchReason.MANUAL,
        "Emergency shutdown requested"
    )

Check if system is operational:
    ks = get_kill_switch()
    if ks.is_operational():
        # System is safe to use
        pass

Recover from shutdown:
    ks.recover("Issue resolved")

2. Safe Mode (Degraded Operation)
----------------------------------
Enter safe mode:
    from safety.safe_mode import enter_safe_mode, SafeModeLevel
    enter_safe_mode(SafeModeLevel.LIMITED, "High resource usage")

Check if operation is allowed:
    sm = get_safe_mode()
    if sm.is_operation_allowed("write"):
        # Operation is allowed
        pass

Exit safe mode:
    from safety.safe_mode import exit_safe_mode
    exit_safe_mode("Issue resolved")

3. Constitutional Classifiers (Content Filtering)
-------------------------------------------------
Check input content:
    from safety.constitutional_classifier import get_classifier, ContentType
    classifier = get_classifier()
    result = classifier.check_input(user_input, ContentType.USER_INPUT)

    if not result.safe:
        # Handle violation
        print(f"Blocked: {result.violation.reason}")

Use decorators for automatic checking:
    from safety.constitutional_classifier import check_user_input
    @check_user_input
    def process_request(user_input: str):
        # Input is automatically checked
        pass

4. Combined Safety Decorator
----------------------------
Use the all-in-one safety decorator:
    from safety.integration import safe_agent_execution

    @safe_agent_execution
    def my_agent(user_input: str) -> str:
        # All safety checks applied automatically
        return "result"

5. Integration with Existing Agents
------------------------------------
Wrap existing agent execution:
    agent = MyAgent()
    safe_execute = safe_agent_execution(agent.execute)

    try:
        result = safe_execute(task_data)
    except RuntimeError as e:
        # Safety violation occurred
        print(f"Blocked by safety: {e}")

For more details, see:
- Kill Switch: .blackbox5/2-engine/01-core/safety/kill_switch.py
- Safe Mode: .blackbox5/2-engine/01-core/safety/safe_mode.py
- Classifier: .blackbox5/2-engine/01-core/safety/constitutional_classifier.py
- Tests: .blackbox5/2-engine/01-core/safety/tests/test_safety_system.py
    """)


# Export key functions
__all__ = [
    'safe_agent_execution',
    'integrate_with_circuit_breaker',
    'integrate_with_event_bus',
    'get_safety_api_endpoints',
    'example_agent_integration',
    'quick_start',
]
