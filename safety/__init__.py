"""
BlackBox 5 Safety System

Provides critical safety features for multi-agent operations:
- Kill Switch: Emergency shutdown capability
- Safe Mode: Degraded operation mode
- Constitutional Classifiers: Input/output content filtering
"""

from .kill_switch import KillSwitch, get_kill_switch, activate_emergency_shutdown
from .safe_mode import SafeMode, SafeModeLevel, get_safe_mode
from .constitutional_classifier import ConstitutionalClassifier, get_classifier

__all__ = [
    'KillSwitch',
    'get_kill_switch',
    'activate_emergency_shutdown',
    'SafeMode',
    'SafeModeLevel',
    'get_safe_mode',
    'ConstitutionalClassifier',
    'get_classifier',
]
