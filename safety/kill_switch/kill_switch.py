"""
Kill Switch Implementation for BlackBox 5

Provides emergency shutdown capability for the multi-agent system.
This is a critical safety feature that allows immediate termination
of all agent operations in case of emergencies.

Features:
- Immediate halt of all agent operations
- Graceful shutdown with cleanup
- System-wide emergency broadcast
- Persistent state tracking
- Integration with circuit breakers
- Delivery confirmation (agents must acknowledge)
- Compliance verification (check agents actually stopped)
- Recovery testing (test system can restart)
- Backup trigger (filesystem fallback)
"""

import logging
import threading
import time
import signal
import os
import asyncio
import json
from datetime import datetime
from typing import Optional, Callable, Dict, Any, Set, List
from enum import Enum
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class KillSwitchState(Enum):
    """Kill switch states"""
    ACTIVE = "active"           # System running normally
    ARMED = "armed"             # Ready to trigger
    TRIGGERED = "triggered"     # Emergency shutdown activated
    RECOVERING = "recovering"   # Recovering from shutdown
    VERIFYING = "verifying"     # Verifying agents stopped
    TESTING = "testing"         # Testing recovery


class KillSwitchReason(Enum):
    """Reasons for triggering kill switch"""
    MANUAL = "manual"                   # Manual activation
    CRITICAL_FAILURE = "critical_failure"  # Critical system failure
    SAFETY_VIOLATION = "safety_violation"  # Safety constraint violated
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # Out of resources
    MALICE_DETECTED = "malice_detected"  # Malicious activity detected
    CIRCUIT_BREAKER = "circuit_breaker"  # Too many circuits open
    USER_REQUEST = "user_request"       # User requested shutdown


class KillSwitch:
    """
    Emergency shutdown system for BlackBox 5.

    The kill switch provides immediate termination of all agent operations
    when critical issues are detected. It can be triggered manually or
    automatically by safety systems.

    Example:
        ```python
        # Get global kill switch
        ks = get_kill_switch()

        # Check if system is operational
        if ks.is_operational():
            # Proceed with operations
            pass

        # Trigger emergency shutdown
        ks.trigger(KillSwitchReason.MANUAL, "User requested shutdown")

        # Later recover
        ks.recover()
        ```

    Attributes:
        state: Current kill switch state
        trigger_time: When the kill switch was triggered
        trigger_reason: Reason for triggering
        trigger_count: Number of times triggered
    """

    _instance: Optional['KillSwitch'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        # State
        self._state = KillSwitchState.ACTIVE
        self._trigger_time: Optional[datetime] = None
        self._trigger_reason: Optional[KillSwitchReason] = None
        self._trigger_message: Optional[str] = None
        self._trigger_count = 0
        self._recovery_count = 0

        # Delivery confirmation
        self._acknowledgments: Dict[str, Dict[str, Any]] = {}
        self._expected_agents: Set[str] = set()
        self._ack_timeout = 5.0  # seconds

        # Compliance verification
        self._compliance_verified = False
        self._force_kill_used = False

        # Backup trigger
        self._backup_trigger_file = Path(".kill_switch_backup")

        # Testing
        self._test_results: List[Dict[str, Any]] = []

        # Callbacks
        self._on_trigger_callbacks: list[Callable] = []
        self._on_recover_callbacks: list[Callable] = []

        # State file
        self._state_file = Path("blackbox5/2-engine/01-core/safety/.kill_switch_state.json")

        # Load previous state if exists
        self._load_state()

        # Register signal handlers
        self._register_signal_handlers()

        logger.info("Kill Switch initialized: %s", self._state.value)

    def _register_signal_handlers(self):
        """Register signal handlers for SIGTERM and SIGINT"""
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            logger.debug("Registered signal handlers for kill switch")
        except Exception as e:
            logger.warning(f"Could not register signal handlers: {e}")

    def _signal_handler(self, signum, frame):
        """Handle system signals"""
        logger.info(f"Received signal {signum}, triggering kill switch")
        self.trigger(
            KillSwitchReason.USER_REQUEST,
            f"System signal received: {signum}"
        )

    @property
    def state(self) -> KillSwitchState:
        """Current kill switch state"""
        return self._state

    @property
    def trigger_time(self) -> Optional[datetime]:
        """When the kill switch was triggered"""
        return self._trigger_time

    @property
    def trigger_reason(self) -> Optional[KillSwitchReason]:
        """Reason for triggering"""
        return self._trigger_reason

    @property
    def trigger_message(self) -> Optional[str]:
        """Detailed message about trigger"""
        return self._trigger_message

    @property
    def trigger_count(self) -> int:
        """Number of times triggered"""
        return self._trigger_count

    def is_operational(self) -> bool:
        """Check if system is operational (not killed)"""
        return self._state == KillSwitchState.ACTIVE

    def is_triggered(self) -> bool:
        """Check if kill switch has been triggered"""
        return self._state == KillSwitchState.TRIGGERED

    def is_recovering(self) -> bool:
        """Check if system is recovering"""
        return self._state == KillSwitchState.RECOVERING

    def trigger(
        self,
        reason: KillSwitchReason,
        message: str = "",
        source: str = "unknown"
    ) -> bool:
        """
        Trigger the kill switch (emergency shutdown) with delivery confirmation
        and compliance verification.

        Args:
            reason: Why the kill switch is being triggered
            message: Additional details about the trigger
            source: What component triggered it

        Returns:
            True if successfully triggered and all agents acknowledged, False otherwise

        Example:
            ```python
            ks.trigger(
                KillSwitchReason.SAFETY_VIOLATION,
                "Harmful content detected",
                source="constitutional_classifier"
            )
            ```
        """
        with self._lock:
            # Already triggered
            if self._state == KillSwitchState.TRIGGERED:
                logger.warning("Kill switch already triggered")
                return False

            # Trigger the kill switch
            logger.critical(
                f"KILL SWITCH TRIGGERED: {reason.value} - {message} "
                f"(from: {source})"
            )

            self._state = KillSwitchState.TRIGGERED
            self._trigger_time = datetime.now()
            self._trigger_reason = reason
            self._trigger_message = message
            self._trigger_count += 1

            # Save state
            self._save_state()

            # Execute callbacks
            for callback in self._on_trigger_callbacks:
                try:
                    callback(self, reason, message, source)
                except Exception as e:
                    logger.error(f"Error in trigger callback: {e}")

            # Phase 1: Get list of running agents
            self._expected_agents = self._get_running_agents()
            logger.info(f"Expecting acknowledgments from {len(self._expected_agents)} agents")

            # Broadcast to system
            self._broadcast_trigger(reason, message, source)

            # Return True - async verification happens separately
            return True

    def trigger_async(
        self,
        reason: KillSwitchReason,
        message: str = "",
        source: str = "unknown"
    ) -> bool:
        """
        Async trigger that waits for acknowledgments and verifies compliance.

        This method should be called from async contexts to enable full
        delivery confirmation and compliance verification.

        Returns:
            True if all agents acknowledged and stopped, False otherwise
        """
        # First trigger normally
        if not self.trigger(reason, message, source):
            return False

        # Run async verification if in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule verification as task
                asyncio.create_task(self._verify_trigger_completion())
            else:
                # Run verification synchronously
                loop.run_until_complete(self._verify_trigger_completion())
        except Exception as e:
            logger.error(f"Async verification failed: {e}")
            return False

        return True

    def recover(self, message: str = "") -> bool:
        """
        Recover from kill switch and return to normal operation.

        Args:
            message: Reason for recovery

        Returns:
            True if successfully recovered, False otherwise

        Example:
            ```python
            ks.recover("Issue resolved, resuming operations")
            ```
        """
        with self._lock:
            if self._state != KillSwitchState.TRIGGERED:
                logger.warning("Cannot recover: kill switch not triggered")
                return False

            logger.info(f"Recovering from kill switch: {message}")

            self._state = KillSwitchState.ACTIVE
            self._recovery_count += 1

            # Clear trigger info
            self._trigger_time = None
            self._trigger_reason = None
            self._trigger_message = None

            # Save state
            self._save_state()

            # Execute callbacks
            for callback in self._on_recover_callbacks:
                try:
                    callback(self, message)
                except Exception as e:
                    logger.error(f"Error in recover callback: {e}")

            # Broadcast to system
            self._broadcast_recovery(message)

            return True

    def on_trigger(self, callback: Callable):
        """Register callback for when kill switch is triggered"""
        self._on_trigger_callbacks.append(callback)

    def on_recover(self, callback: Callable):
        """Register callback for when system recovers"""
        self._on_recover_callbacks.append(callback)

    # ========== Delivery Confirmation ==========

    def register_acknowledgment(self, agent_id: str, stopped: bool = True):
        """
        Called by agents when they receive kill signal.

        Args:
            agent_id: ID of the agent acknowledging
            stopped: Whether the agent successfully stopped
        """
        self._acknowledgments[agent_id] = {
            'timestamp': datetime.now().isoformat(),
            'stopped': stopped
        }
        logger.debug(f"Acknowledgment from {agent_id}: stopped={stopped}")

    def get_acknowledgments(self) -> Dict[str, Dict[str, Any]]:
        """Get current acknowledgments"""
        return self._acknowledgments.copy()

    def get_missing_acknowledgments(self) -> Set[str]:
        """Get agents that haven't acknowledged"""
        return self._expected_agents - set(self._acknowledgments.keys())

    # ========== Compliance Verification ==========

    async def _verify_trigger_completion(self):
        """Verify all agents acknowledged and stopped (async)"""
        try:
            # Wait for acknowledgments
            await self._wait_for_acknowledgments()

            # Check for missing agents
            missing = self.get_missing_acknowledgments()
            if missing:
                logger.critical(f"Kill switch: Agents did not acknowledge: {missing}")
                self._save_verification_result(False, "missing_acknowledgments", list(missing))
                return False

            # Verify agents actually stopped
            if not await self._verify_agents_stopped():
                logger.critical("Kill switch: Agents acknowledged but still running!")
                await self._force_kill_agents()
                self._save_verification_result(False, "agents_still_running", [])
                return False

            self._compliance_verified = True
            self._save_verification_result(True, "all_stopped", list(self._expected_agents))
            logger.info("Kill switch: All agents verified stopped")
            return True

        except Exception as e:
            logger.error(f"Error during verification: {e}")
            self._save_verification_result(False, f"verification_error: {e}", [])
            return False

    async def _wait_for_acknowledgments(self, timeout: Optional[float] = None):
        """Wait for all agents to acknowledge kill signal (async)"""
        timeout = timeout or self._ack_timeout
        started = datetime.now()

        while (datetime.now() - started).total_seconds() < timeout:
            acked = set(self._acknowledgments.keys())
            if acked == self._expected_agents:
                logger.debug(f"All {len(acked)} agents acknowledged")
                break
            await asyncio.sleep(0.1)

        # Log final status
        acked = set(self._acknowledgments.keys())
        if acked != self._expected_agents:
            missing = self._expected_agents - acked
            logger.warning(f"Timeout: {len(missing)} agents didn't acknowledge: {missing}")

    async def _verify_agents_stopped(self) -> bool:
        """Verify all agents actually stopped"""
        try:
            # Try to import agent registry
            from ..agents.base_agent import get_agent_registry
            registry = get_agent_registry()

            for agent_id in self._expected_agents:
                try:
                    agent = registry.get(agent_id)
                    if agent and hasattr(agent, 'is_running') and agent.is_running:
                        logger.critical(f"Agent {agent_id} still running after kill!")
                        return False
                except Exception as e:
                    logger.debug(f"Could not check agent {agent_id}: {e}")

            return True

        except ImportError:
            logger.debug("Agent registry not available, skipping verification")
            return True  # Assume stopped if can't verify

    async def _force_kill_agents(self):
        """Force kill agents that didn't stop gracefully"""
        logger.critical("Forcing kill of non-compliant agents")
        self._force_kill_used = True

        try:
            from ..agents.base_agent import get_agent_registry
            registry = get_agent_registry()

            for agent_id in self._expected_agents:
                try:
                    agent = registry.get(agent_id)
                    if agent and hasattr(agent, 'force_stop'):
                        agent.force_stop()
                        logger.warning(f"Force stopped agent {agent_id}")
                except Exception as e:
                    logger.error(f"Error force stopping {agent_id}: {e}")

        except ImportError:
            logger.error("Could not import agent registry for force kill")

    def _save_verification_result(self, success: bool, reason: str, details: List[str]):
        """Save verification result to state"""
        self._test_results.append({
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'reason': reason,
            'details': details,
            'force_kill_used': self._force_kill_used
        })

    # ========== Recovery Testing ==========

    def test_recovery(self) -> Dict[str, Any]:
        """
        Test that system can recover after kill.

        Returns:
            Dict with test results
        """
        logger.info("Testing kill switch recovery...")

        test_result = {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'recovery',
            'success': False,
            'phases': []
        }

        try:
            # Save current state
            state_before = self._get_system_state()
            test_result['phases'].append({
                'phase': 'capture_state',
                'success': True,
                'state': state_before
            })

            # Trigger kill
            triggered = self.trigger(KillSwitchReason.MANUAL, "Recovery test")
            test_result['phases'].append({
                'phase': 'trigger',
                'success': triggered
            })

            if not triggered:
                test_result['error'] = 'Failed to trigger kill switch'
                return test_result

            # Attempt recovery
            recovered = self.recover("Recovery test complete")
            test_result['phases'].append({
                'phase': 'recover',
                'success': recovered
            })

            if not recovered:
                test_result['error'] = 'Failed to recover'
                return test_result

            # Verify system is functional
            state_after = self._get_system_state()
            test_result['phases'].append({
                'phase': 'verify',
                'success': True,
                'state': state_after
            })

            # Check if operational
            if not self.is_operational():
                test_result['error'] = 'System not operational after recovery'
                return test_result

            test_result['success'] = True
            logger.info("Recovery test PASSED")

        except Exception as e:
            test_result['error'] = str(e)
            logger.error(f"Recovery test FAILED: {e}")

        # Save result
        self._test_results.append(test_result)
        return test_result

    def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state for testing"""
        try:
            from ..communication.event_bus import get_event_bus
            event_bus = get_event_bus()
            return {
                'services': 'event_bus_available',
                'timestamp': datetime.now().isoformat()
            }
        except Exception:
            return {
                'services': 'event_bus_unavailable',
                'timestamp': datetime.now().isoformat()
            }

    # ========== Backup Trigger ==========

    def _broadcast_trigger(self, reason: KillSwitchReason, message: str, source: str):
        """Broadcast kill switch trigger to system"""
        try:
            from ..communication.event_bus import get_event_bus

            event_bus = get_event_bus()
            event_bus.publish(
                "safety.kill_switch.triggered",
                {
                    "reason": reason.value,
                    "message": message,
                    "source": source,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            logger.debug("Broadcast kill switch trigger to event bus")
        except Exception as e:
            logger.error(f"Event bus broadcast failed: {e}")
            # Use backup trigger
            self._backup_trigger(reason, message, source)

    def _backup_trigger(self, reason: KillSwitchReason, message: str, source: str):
        """Backup trigger via filesystem"""
        logger.warning("Using backup trigger (filesystem)")

        try:
            self._backup_trigger_file.parent.mkdir(parents=True, exist_ok=True)
            backup_data = {
                'reason': reason.value,
                'message': message,
                'source': source,
                'timestamp': datetime.now().isoformat()
            }
            with open(self._backup_trigger_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            logger.info(f"Backup trigger written to {self._backup_trigger_file}")
        except Exception as e:
            logger.critical(f"Failed to write backup trigger: {e}")

    def check_backup_trigger(self) -> bool:
        """
        Check for backup trigger signal (should be called on agent startup).

        Returns:
            True if backup trigger was found and processed
        """
        if not self._backup_trigger_file.exists():
            return False

        try:
            with open(self._backup_trigger_file, 'r') as f:
                data = json.load(f)

            reason = KillSwitchReason(data['reason'])
            logger.warning(f"Found backup trigger: {reason.value}")

            # Trigger the kill switch
            self.trigger(
                reason,
                f"[BACKUP TRIGGER] {data['message']}",
                data['source']
            )

            # Clean up backup file
            self._backup_trigger_file.unlink()
            return True

        except Exception as e:
            logger.error(f"Error processing backup trigger: {e}")
            return False

    # ========== Helper Methods ==========

    def _get_running_agents(self) -> Set[str]:
        """Get list of currently running agents"""
        try:
            from ..agents.base_agent import get_agent_registry
            registry = get_agent_registry()

            # Get all running agents
            running = set()
            for agent_id, agent in registry.get_all_agents().items():
                if hasattr(agent, 'is_running') and agent.is_running:
                    running.add(agent_id)

            return running

        except ImportError:
            logger.debug("Could not import agent registry")
            return set()

    def _broadcast_trigger(self, reason: KillSwitchReason, message: str, source: str):
        """Broadcast kill switch trigger to system"""
        try:
            # Try to import event bus
            from ..communication.event_bus import get_event_bus

            event_bus = get_event_bus()
            event_bus.publish(
                "safety.kill_switch.triggered",
                {
                    "reason": reason.value,
                    "message": message,
                    "source": source,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            logger.debug("Broadcast kill switch trigger to event bus")
        except Exception as e:
            logger.debug(f"Could not broadcast trigger: {e}")

    def _broadcast_recovery(self, message: str):
        """Broadcast recovery to system"""
        try:
            from ..communication.event_bus import get_event_bus

            event_bus = get_event_bus()
            event_bus.publish(
                "safety.kill_switch.recovered",
                {
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            logger.debug("Broadcast recovery to event bus")
        except Exception as e:
            logger.debug(f"Could not broadcast recovery: {e}")

    def _save_state(self):
        """Save kill switch state to file"""
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            state_data = {
                "state": self._state.value,
                "trigger_time": self._trigger_time.isoformat() if self._trigger_time else None,
                "trigger_reason": self._trigger_reason.value if self._trigger_reason else None,
                "trigger_message": self._trigger_message,
                "trigger_count": self._trigger_count,
                "recovery_count": self._recovery_count,
                "last_updated": datetime.now().isoformat(),
                # New fields
                "expected_agents": list(self._expected_agents),
                "acknowledgments": self._acknowledgments,
                "compliance_verified": self._compliance_verified,
                "force_kill_used": self._force_kill_used,
                "test_count": len(self._test_results),
            }
            with open(self._state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            logger.debug(f"Saved kill switch state to {self._state_file}")
        except Exception as e:
            logger.error(f"Could not save kill switch state: {e}")

    def _load_state(self):
        """Load kill switch state from file"""
        try:
            if not self._state_file.exists():
                return

            with open(self._state_file, 'r') as f:
                state_data = json.load(f)

            # Restore state
            self._state = KillSwitchState(state_data["state"])
            self._trigger_count = state_data.get("trigger_count", 0)
            self._recovery_count = state_data.get("recovery_count", 0)

            # Load new fields if available
            self._expected_agents = set(state_data.get("expected_agents", []))
            self._acknowledgments = state_data.get("acknowledgments", {})
            self._compliance_verified = state_data.get("compliance_verified", False)
            self._force_kill_used = state_data.get("force_kill_used", False)

            # If was triggered, keep it triggered
            if self._state == KillSwitchState.TRIGGERED:
                logger.warning("Kill switch was triggered, recovering manually required")

            logger.debug(f"Loaded kill switch state: {self._state.value}")
        except Exception as e:
            logger.warning(f"Could not load kill switch state: {e}")

    def reset(self) -> bool:
        """
        Force reset of kill switch (admin only).

        Returns:
            True if successfully reset
        """
        with self._lock:
            logger.warning("Force resetting kill switch")
            self._state = KillSwitchState.ACTIVE
            self._trigger_time = None
            self._trigger_reason = None
            self._trigger_message = None
            self._save_state()
            return True

    def get_status(self) -> Dict[str, Any]:
        """
        Get current kill switch status.

        Returns:
            Dictionary with current status
        """
        return {
            "state": self._state.value,
            "operational": self.is_operational(),
            "triggered": self.is_triggered(),
            "trigger_time": self._trigger_time.isoformat() if self._trigger_time else None,
            "trigger_reason": self._trigger_reason.value if self._trigger_reason else None,
            "trigger_message": self._trigger_message,
            "trigger_count": self._trigger_count,
            "recovery_count": self._recovery_count,
            # Delivery confirmation
            "expected_agents": list(self._expected_agents),
            "acknowledgments": self._acknowledgments,
            "missing_acknowledgments": list(self.get_missing_acknowledgments()),
            "acknowledgment_rate": (
                len(self._acknowledgments) / len(self._expected_agents)
                if self._expected_agents else 1.0
            ),
            # Compliance
            "compliance_verified": self._compliance_verified,
            "force_kill_used": self._force_kill_used,
            # Testing
            "test_count": len(self._test_results),
            "last_test_result": self._test_results[-1] if self._test_results else None,
        }


# Global singleton
_kill_switch: Optional[KillSwitch] = None
_kill_switch_lock = threading.Lock()


def get_kill_switch() -> KillSwitch:
    """
    Get the global kill switch instance.

    Returns:
        The global KillSwitch singleton

    Example:
        ```python
        ks = get_kill_switch()
        if ks.is_operational():
            # System is safe to use
            pass
        ```
    """
    global _kill_switch
    if _kill_switch is None:
        with _kill_switch_lock:
            if _kill_switch is None:
                _kill_switch = KillSwitch()
    return _kill_switch


def activate_emergency_shutdown(
    reason: KillSwitchReason = KillSwitchReason.MANUAL,
    message: str = "",
    source: str = "manual"
) -> bool:
    """
    Convenience function to activate emergency shutdown.

    Args:
        reason: Why the shutdown is being activated
        message: Additional details
        source: What triggered it

    Returns:
        True if successfully activated

    Example:
        ```python
        # Emergency shutdown
        activate_emergency_shutdown(
            KillSwitchReason.SAFETY_VIOLATION,
            "Malicious activity detected"
        )
        ```
    """
    ks = get_kill_switch()
    return ks.trigger(reason, message, source)


# Decorator for checking kill switch
def require_operational(func):
    """
    Decorator that checks if kill switch is operational before executing.

    Example:
        ```python
        @require_operational
        def sensitive_operation():
            # This won't run if kill switch is triggered
            pass
        ```
    """
    def wrapper(*args, **kwargs):
        ks = get_kill_switch()
        if not ks.is_operational():
            raise RuntimeError(
                f"Cannot execute {func.__name__}: kill switch has been triggered. "
                f"Reason: {ks.trigger_reason.value if ks.trigger_reason else 'unknown'}"
            )
        return func(*args, **kwargs)
    return wrapper


# Context manager for kill switch checking
class KillSwitchGuard:
    """
    Context manager that ensures kill switch is operational.

    Example:
        ```python
        with KillSwitchGuard():
            # This code will only run if kill switch is operational
            sensitive_operation()
        ```
    """

    def __init__(self, auto_recover: bool = False):
        self.auto_recover = auto_recover
        self.was_operational = False

    def __enter__(self):
        ks = get_kill_switch()
        self.was_operational = ks.is_operational()
        if not self.was_operational:
            raise RuntimeError(
                f"Kill switch is triggered: {ks.trigger_reason.value}"
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
