"""
Safe Mode Implementation for BlackBox 5

Provides degraded operation mode for the multi-agent system.
Safe mode allows limited operations when system is in a degraded state.

Features:
- Multiple safe mode levels (off, limited, restricted, emergency)
- Configurable operation limits per mode
- Automatic mode transitions
- Integration with kill switch
- Resource budgeting
"""

import logging
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class SafeModeLevel(Enum):
    """Safe mode levels"""
    OFF = "off"                   # Normal operation
    LIMITED = "limited"           # Reduced capabilities
    RESTRICTED = "restricted"     # Highly restricted operations
    EMERGENCY = "emergency"       # Emergency operations only


class SafeModeConfig:
    """Configuration for safe mode"""

    # Operation limits per mode
    MODE_LIMITS = {
        SafeModeLevel.OFF: {
            "max_concurrent_agents": 10,
            "max_memory_mb": 4096,
            "max_execution_time_seconds": 300,
            "allowed_operations": ["all"],
            "rate_limit_per_minute": 1000,
        },
        SafeModeLevel.LIMITED: {
            "max_concurrent_agents": 3,
            "max_memory_mb": 1024,
            "max_execution_time_seconds": 60,
            "allowed_operations": ["read", "simple_write", "query"],
            "rate_limit_per_minute": 100,
        },
        SafeModeLevel.RESTRICTED: {
            "max_concurrent_agents": 1,
            "max_memory_mb": 512,
            "max_execution_time_seconds": 30,
            "allowed_operations": ["read", "query"],
            "rate_limit_per_minute": 10,
        },
        SafeModeLevel.EMERGENCY: {
            "max_concurrent_agents": 1,
            "max_memory_mb": 256,
            "max_execution_time_seconds": 10,
            "allowed_operations": ["diagnostic", "status"],
            "rate_limit_per_minute": 5,
        },
    }


class SafeMode:
    """
    Safe mode manager for BlackBox 5.

    Safe mode allows the system to continue operating in a degraded
    state when issues are detected. Different levels provide
    different operational constraints.

    Example:
        ```python
        # Get global safe mode manager
        sm = get_safe_mode()

        # Enter safe mode
        sm.enter_level(SafeModeLevel.LIMITED, "High memory usage")

        # Check if operation is allowed
        if sm.is_operation_allowed("write"):
            # Proceed with operation
            pass

        # Exit safe mode
        sm.exit_level("Issue resolved")
        ```

    Attributes:
        current_level: Current safe mode level
        enter_time: When current mode was entered
        enter_reason: Reason for entering current mode
    """

    _instance: Optional['SafeMode'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        # State
        self._current_level = SafeModeLevel.OFF
        self._enter_time: Optional[datetime] = None
        self._enter_reason: Optional[str] = None
        self._history: List[Dict[str, Any]] = []

        # Callbacks
        self._on_enter_callbacks: List[callable] = []
        self._on_exit_callbacks: List[callable] = []

        # State file
        self._state_file = Path("blackbox5/2-engine/01-core/safety/.safe_mode_state.json")

        # Load previous state
        self._load_state()

        logger.info("Safe Mode initialized: %s", self._current_level.value)

    @property
    def current_level(self) -> SafeModeLevel:
        """Current safe mode level"""
        return self._current_level

    @property
    def enter_time(self) -> Optional[datetime]:
        """When current mode was entered"""
        return self._enter_time

    @property
    def enter_reason(self) -> Optional[str]:
        """Reason for entering current mode"""
        return self._enter_reason

    def is_normal_mode(self) -> bool:
        """Check if in normal (off) mode"""
        return self._current_level == SafeModeLevel.OFF

    def is_safe_mode(self) -> bool:
        """Check if in any safe mode"""
        return self._current_level != SafeModeLevel.OFF

    def enter_level(
        self,
        level: SafeModeLevel,
        reason: str = "",
        source: str = "unknown"
    ) -> bool:
        """
        Enter a specific safe mode level.

        Args:
            level: Safe mode level to enter
            reason: Why entering safe mode
            source: What component triggered it

        Returns:
            True if successfully entered

        Example:
            ```python
            sm.enter_level(
                SafeModeLevel.LIMITED,
                "High memory usage detected",
                source="monitor"
            )
            ```
        """
        with self._lock:
            # Already in this mode
            if self._current_level == level:
                logger.warning(f"Already in {level.value} mode")
                return False

            # More restrictive mode
            if level.value != "off" and (
                self._current_level != SafeModeLevel.OFF and
                list(SafeModeLevel).index(level) <= list(SafeModeLevel).index(self._current_level)
            ):
                logger.warning(
                    f"Cannot enter {level.value} mode from {self._current_level.value}"
                )
                return False

            logger.warning(
                f"Entering {level.value} mode: {reason} (from: {source})"
            )

            # Record transition
            self._history.append({
                "from_level": self._current_level.value,
                "to_level": level.value,
                "reason": reason,
                "source": source,
                "timestamp": datetime.now().isoformat(),
            })

            # Update state
            self._current_level = level
            self._enter_time = datetime.now()
            self._enter_reason = reason

            # Save state
            self._save_state()

            # Execute callbacks
            for callback in self._on_enter_callbacks:
                try:
                    callback(level, reason, source)
                except Exception as e:
                    logger.error(f"Error in enter callback: {e}")

            # Broadcast to system
            self._broadcast_enter(level, reason, source)

            return True

    def exit_level(self, reason: str = "", source: str = "unknown") -> bool:
        """
        Exit safe mode and return to normal operation.

        Args:
            reason: Why exiting safe mode
            source: What component triggered exit

        Returns:
            True if successfully exited

        Example:
            ```python
            sm.exit_level("Issue resolved", source="admin")
            ```
        """
        with self._lock:
            if self._current_level == SafeModeLevel.OFF:
                logger.warning("Already in normal mode")
                return False

            logger.info(f"Exiting {self._current_level.value} mode: {reason}")

            # Record transition
            self._history.append({
                "from_level": self._current_level.value,
                "to_level": "off",
                "reason": reason,
                "source": source,
                "timestamp": datetime.now().isoformat(),
            })

            # Update state
            prev_level = self._current_level
            self._current_level = SafeModeLevel.OFF
            self._enter_time = None
            self._enter_reason = None

            # Save state
            self._save_state()

            # Execute callbacks
            for callback in self._on_exit_callbacks:
                try:
                    callback(prev_level, reason, source)
                except Exception as e:
                    logger.error(f"Error in exit callback: {e}")

            # Broadcast to system
            self._broadcast_exit(prev_level, reason, source)

            return True

    def is_operation_allowed(self, operation: str) -> bool:
        """
        Check if an operation is allowed in current mode.

        Args:
            operation: Operation type (write, read, query, etc.)

        Returns:
            True if operation is allowed

        Example:
            ```python
            if sm.is_operation_allowed("write"):
                # Perform write operation
                pass
            ```
        """
        limits = SafeModeConfig.MODE_LIMITS[self._current_level]
        allowed = limits["allowed_operations"]

        # "all" means any operation is allowed
        if "all" in allowed:
            return True

        return operation in allowed

    def get_limits(self) -> Dict[str, Any]:
        """
        Get operation limits for current mode.

        Returns:
            Dictionary of current limits

        Example:
            ```python
            limits = sm.get_limits()
            max_agents = limits["max_concurrent_agents"]
            ```
        """
        return SafeModeConfig.MODE_LIMITS[self._current_level].copy()

    def get_status(self) -> Dict[str, Any]:
        """
        Get current safe mode status.

        Returns:
            Dictionary with current status
        """
        return {
            "current_level": self._current_level.value,
            "is_normal_mode": self.is_normal_mode(),
            "is_safe_mode": self.is_safe_mode(),
            "enter_time": self._enter_time.isoformat() if self._enter_time else None,
            "enter_reason": self._enter_reason,
            "limits": self.get_limits(),
            "history_count": len(self._history),
        }

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get mode transition history.

        Args:
            limit: Maximum number of history entries

        Returns:
            List of historical transitions
        """
        return self._history[-limit:]

    def on_enter(self, callback: callable):
        """Register callback for when entering safe mode"""
        self._on_enter_callbacks.append(callback)

    def on_exit(self, callback: callable):
        """Register callback for when exiting safe mode"""
        self._on_exit_callbacks.append(callback)

    def _broadcast_enter(self, level: SafeModeLevel, reason: str, source: str):
        """Broadcast safe mode entry to system"""
        try:
            from ..communication.event_bus import get_event_bus
            event_bus = get_event_bus()
            event_bus.publish(
                "safety.safe_mode.entered",
                {
                    "level": level.value,
                    "reason": reason,
                    "source": source,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            logger.debug(f"Could not broadcast safe mode enter: {e}")

    def _broadcast_exit(self, prev_level: SafeModeLevel, reason: str, source: str):
        """Broadcast safe mode exit to system"""
        try:
            from ..communication.event_bus import get_event_bus
            event_bus = get_event_bus()
            event_bus.publish(
                "safety.safe_mode.exited",
                {
                    "previous_level": prev_level.value,
                    "reason": reason,
                    "source": source,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            logger.debug(f"Could not broadcast safe mode exit: {e}")

    def _save_state(self):
        """Save safe mode state to file"""
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            import json
            state_data = {
                "current_level": self._current_level.value,
                "enter_time": self._enter_time.isoformat() if self._enter_time else None,
                "enter_reason": self._enter_reason,
                "history": self._history[-100:],  # Keep last 100
                "last_updated": datetime.now().isoformat(),
            }
            with open(self._state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save safe mode state: {e}")

    def _load_state(self):
        """Load safe mode state from file"""
        try:
            if not self._state_file.exists():
                return

            import json
            with open(self._state_file, 'r') as f:
                state_data = json.load(f)

            # Restore state
            self._current_level = SafeModeLevel(state_data["current_level"])
            self._enter_reason = state_data.get("enter_reason")
            self._history = state_data.get("history", [])

            # Restore enter time
            if state_data.get("enter_time"):
                self._enter_time = datetime.fromisoformat(state_data["enter_time"])

            logger.debug(f"Loaded safe mode state: {self._current_level.value}")
        except Exception as e:
            logger.warning(f"Could not load safe mode state: {e}")


# Global singleton
_safe_mode: Optional[SafeMode] = None
_safe_mode_lock = threading.Lock()


def get_safe_mode() -> SafeMode:
    """
    Get the global safe mode instance.

    Returns:
        The global SafeMode singleton

    Example:
        ```python
        sm = get_safe_mode()
        if sm.is_normal_mode():
            # System is in normal mode
            pass
        ```
    """
    global _safe_mode
    if _safe_mode is None:
        with _safe_mode_lock:
            if _safe_mode is None:
                _safe_mode = SafeMode()
    return _safe_mode


# Convenience functions
def enter_safe_mode(
    level: SafeModeLevel = SafeModeLevel.LIMITED,
    reason: str = "",
    source: str = "manual"
) -> bool:
    """
    Convenience function to enter safe mode.

    Args:
        level: Safe mode level to enter
        reason: Why entering safe mode
        source: What triggered it

    Returns:
        True if successfully entered

    Example:
        ```python
        enter_safe_mode(
            SafeModeLevel.LIMITED,
            "High resource usage"
        )
        ```
    """
    sm = get_safe_mode()
    return sm.enter_level(level, reason, source)


def exit_safe_mode(reason: str = "", source: str = "manual") -> bool:
    """
    Convenience function to exit safe mode.

    Args:
        reason: Why exiting safe mode
        source: What triggered exit

    Returns:
        True if successfully exited

    Example:
        ```python
        exit_safe_mode("Issue resolved")
        ```
    """
    sm = get_safe_mode()
    return sm.exit_level(reason, source)


# Decorator for operation checking
def require_operation(operation: str):
    """
    Decorator that checks if operation is allowed in current mode.

    Args:
        operation: Operation type to check

    Example:
        ```python
        @require_operation("write")
        def write_data():
            # This won't run if write is not allowed
            pass
        ```
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            sm = get_safe_mode()
            if not sm.is_operation_allowed(operation):
                raise RuntimeError(
                    f"Operation '{operation}' not allowed in {sm.current_level.value} mode"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
