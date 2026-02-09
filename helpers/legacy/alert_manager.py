#!/usr/bin/env python3
"""
Alert Manager for RALF Performance Monitoring
Manages alert configuration, triggering, and delivery

Version: 1.0.0
Author: RALF System
Created: 2026-02-01
"""

import sys
from pathlib import Path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
from paths import PathResolver, get_path_resolver

resolver = get_path_resolver()
PROJECT_DIR = resolver.get_project_path()

import yaml
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================
ALERT_LOG_FILE = PROJECT_DIR / ".autonomous" / "data" / "alerts" / "alert_history.yaml"
ALERT_CONFIG_FILE = PROJECT_DIR / "2-engine" / ".autonomous" / "config" / "alert-config.yaml"

# Ensure alert directory exists
ALERT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Default alert thresholds (can be overridden by config)
DEFAULT_THRESHOLDS = {
    'duration': {
        'critical_seconds': 600,  # 10 minutes
        'warning_seconds': 300,   # 5 minutes
    },
    'success_rate': {
        'critical_percent': 50,   # 50% success rate
        'warning_percent': 80,    # 80% success rate
    },
    'queue_depth': {
        'critical': 0,            # Empty queue
        'warning': 2,             # Low queue
    },
    'agent_timeout': {
        'seconds': 120,           # 2 minutes without heartbeat
    },
}

# Alert channels
CHANNELS = {
    'log': True,      # Write to log file
    'dashboard': True, # Send to dashboard (F-008)
    'webhook': False,  # Optional webhook (future)
}

# ============================================================================
# Alert History Management
# ============================================================================

def load_alert_history() -> List[Dict[str, Any]]:
    """Load alert history from storage."""
    try:
        if ALERT_LOG_FILE.exists():
            with open(ALERT_LOG_FILE, 'r') as f:
                data = yaml.safe_load(f)
                return data.get('alerts', []) if data else []
    except Exception as e:
        logger.error(f"Error loading alert history: {e}")

    return []


def save_alert_to_history(alert: Dict[str, Any]) -> bool:
    """
    Save alert to history log.

    Args:
        alert: Alert record

    Returns:
        True if save successful
    """
    try:
        history = load_alert_history()

        # Add timestamp if not present
        if 'timestamp' not in alert:
            alert['timestamp'] = datetime.now(timezone.utc).isoformat()

        # Prepend to history (newest first)
        history.insert(0, alert)

        # Keep last 1000 alerts
        history = history[:1000]

        # Save
        data = {
            'metadata': {
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'total_alerts': len(history),
            },
            'alerts': history,
        }

        with open(ALERT_LOG_FILE, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

        return True

    except Exception as e:
        logger.error(f"Error saving alert to history: {e}")
        return False


# ============================================================================
# Alert Configuration
# ============================================================================

def load_alert_config() -> Dict[str, Any]:
    """Load alert configuration from file."""
    try:
        if ALERT_CONFIG_FILE.exists():
            with open(ALERT_CONFIG_FILE, 'r') as f:
                return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Error loading alert config: {e}, using defaults")

    return {'thresholds': DEFAULT_THRESHOLDS, 'channels': CHANNELS}


def get_thresholds() -> Dict[str, Any]:
    """Get alert thresholds from config."""
    config = load_alert_config()
    return config.get('thresholds', DEFAULT_THRESHOLDS)


# ============================================================================
# Alert Creation
# ============================================================================

def create_alert(
    alert_type: str,
    severity: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create an alert record.

    Args:
        alert_type: Type of alert (duration, success_rate, queue, etc.)
        severity: Severity level (critical, warning, info)
        message: Alert message
        metadata: Additional metadata

    Returns:
        Alert record
    """
    alert = {
        'id': f"{alert_type}_{int(datetime.now(timezone.utc).timestamp())}",
        'type': alert_type,
        'severity': severity,
        'message': message,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'metadata': metadata or {},
    }

    return alert


# ============================================================================
# Alert Delivery
# ============================================================================

def send_to_log(alert: Dict[str, Any]) -> bool:
    """
    Send alert to log file.

    Args:
        alert: Alert record

    Returns:
        True if successful
    """
    try:
        log_message = f"[ALERT:{alert['severity'].upper()}] {alert['message']}"

        if alert['severity'] == 'critical':
            logger.error(log_message)
        elif alert['severity'] == 'warning':
            logger.warning(log_message)
        else:
            logger.info(log_message)

        return True

    except Exception as e:
        logger.error(f"Error sending alert to log: {e}")
        return False


def send_to_dashboard(alert: Dict[str, Any]) -> bool:
    """
    Send alert to dashboard (F-008 integration).
    For now, this writes to the events.yaml file which the dashboard reads.

    Args:
        alert: Alert record

    Returns:
        True if successful
    """
    try:
        events_file = PROJECT_DIR / ".autonomous" / "communications" / "events.yaml"

        # Create event entry
        event = {
            'timestamp': alert['timestamp'],
            'type': 'alert',
            'severity': alert['severity'],
            'alert_type': alert['type'],
            'message': alert['message'],
            'metadata': alert.get('metadata', {}),
        }

        # Load existing events
        events = []
        if events_file.exists():
            with open(events_file, 'r') as f:
                data = yaml.safe_load(f)
                events = data if isinstance(data, list) else []

        # Prepend new event
        events.insert(0, event)

        # Save
        with open(events_file, 'w') as f:
            yaml.safe_dump(events, f, default_flow_style=False)

        logger.info(f"Alert sent to dashboard: {alert['id']}")
        return True

    except Exception as e:
        logger.error(f"Error sending alert to dashboard: {e}")
        return False


def trigger_alert(
    alert_type: str,
    severity: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Trigger an alert across all configured channels.

    Args:
        alert_type: Type of alert
        severity: Severity level
        message: Alert message
        metadata: Additional metadata

    Returns:
        Alert record with delivery status
    """
    # Create alert
    alert = create_alert(alert_type, severity, message, metadata)

    # Load configuration
    config = load_alert_config()
    channels = config.get('channels', CHANNELS)

    # Send to channels
    delivery_status = {}

    if channels.get('log', True):
        delivery_status['log'] = send_to_log(alert)

    if channels.get('dashboard', True):
        delivery_status['dashboard'] = send_to_dashboard(alert)

    if channels.get('webhook', False):
        # Future: webhook support
        delivery_status['webhook'] = False

    # Save to history
    save_alert_to_history(alert)

    # Add delivery status to alert
    alert['delivery_status'] = delivery_status

    logger.info(f"Alert triggered: {alert['id']} ({severity})")
    return alert


# ============================================================================
# Alert Evaluation Functions
# ============================================================================

def evaluate_duration_anomaly(
    current_duration: float,
    baseline_duration: float,
    run_number: int
) -> Optional[Dict[str, Any]]:
    """
    Evaluate duration anomaly and trigger alert if needed.

    Args:
        current_duration: Current run duration
        baseline_duration: Baseline average duration
        run_number: Run number

    Returns:
        Alert if triggered, None otherwise
    """
    thresholds = get_thresholds()
    duration_thresholds = thresholds.get('duration', {})

    critical_threshold = duration_thresholds.get('critical_seconds', 600)
    warning_threshold = duration_thresholds.get('warning_seconds', 300)

    # Check absolute thresholds
    if current_duration > critical_threshold:
        return trigger_alert(
            'duration',
            'critical',
            f'Duration {current_duration}s exceeds critical threshold ({critical_threshold}s)',
            {'run_number': run_number, 'value': current_duration, 'threshold': critical_threshold}
        )
    elif current_duration > warning_threshold:
        return trigger_alert(
            'duration',
            'warning',
            f'Duration {current_duration}s exceeds warning threshold ({warning_threshold}s)',
            {'run_number': run_number, 'value': current_duration, 'threshold': warning_threshold}
        )

    # Check relative to baseline
    if baseline_duration > 0:
        ratio = current_duration / baseline_duration

        if ratio >= 2.0:
            return trigger_alert(
                'duration',
                'critical',
                f'Duration {current_duration}s is {ratio:.1f}x baseline average ({baseline_duration:.1f}s)',
                {'run_number': run_number, 'value': current_duration, 'baseline': baseline_duration}
            )
        elif ratio >= 1.5:
            return trigger_alert(
                'duration',
                'warning',
                f'Duration {current_duration}s is {ratio:.1f}x baseline average ({baseline_duration:.1f}s)',
                {'run_number': run_number, 'value': current_duration, 'baseline': baseline_duration}
            )

    return None


def evaluate_success_rate(
    success_rate: float,
    window: int
) -> Optional[Dict[str, Any]]:
    """
    Evaluate success rate and trigger alert if needed.

    Args:
        success_rate: Success rate (0-100)
        window: Window size used for calculation

    Returns:
        Alert if triggered, None otherwise
    """
    thresholds = get_thresholds()
    sr_thresholds = thresholds.get('success_rate', {})

    critical_threshold = sr_thresholds.get('critical_percent', 50)
    warning_threshold = sr_thresholds.get('warning_percent', 80)

    if success_rate < critical_threshold:
        return trigger_alert(
            'success_rate',
            'critical',
            f'Success rate {success_rate:.1f}% below critical threshold ({critical_threshold}%)',
            {'value': success_rate, 'threshold': critical_threshold, 'window': window}
        )
    elif success_rate < warning_threshold:
        return trigger_alert(
            'success_rate',
            'warning',
            f'Success rate {success_rate:.1f}% below warning threshold ({warning_threshold}%)',
            {'value': success_rate, 'threshold': warning_threshold, 'window': window}
        )

    return None


def evaluate_queue_depth(queue_depth: int) -> Optional[Dict[str, Any]]:
    """
    Evaluate queue depth and trigger alert if needed.

    Args:
        queue_depth: Current queue depth

    Returns:
        Alert if triggered, None otherwise
    """
    thresholds = get_thresholds()
    queue_thresholds = thresholds.get('queue_depth', {})

    critical_threshold = queue_thresholds.get('critical', 0)
    warning_threshold = queue_thresholds.get('warning', 2)

    if queue_depth <= critical_threshold:
        return trigger_alert(
            'queue_depth',
            'critical',
            f'Queue depth {queue_depth} at or below critical threshold ({critical_threshold})',
            {'value': queue_depth, 'threshold': critical_threshold}
        )
    elif queue_depth <= warning_threshold:
        return trigger_alert(
            'queue_depth',
            'warning',
            f'Queue depth {queue_depth} at or below warning threshold ({warning_threshold})',
            {'value': queue_depth, 'threshold': warning_threshold}
        )

    return None


def evaluate_agent_timeout(
    agent_type: str,
    last_seen: str
) -> Optional[Dict[str, Any]]:
    """
    Evaluate agent heartbeat timeout and trigger alert if needed.

    Args:
        agent_type: Type of agent (planner, executor)
        last_seen: Last seen timestamp

    Returns:
        Alert if triggered, None otherwise
    """
    thresholds = get_thresholds()
    timeout_threshold = thresholds.get('agent_timeout', {}).get('seconds', 120)

    try:
        last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        elapsed_seconds = (now - last_seen_dt).total_seconds()

        if elapsed_seconds > timeout_threshold:
            return trigger_alert(
                'agent_timeout',
                'critical',
                f'{agent_type} timeout: No heartbeat for {elapsed_seconds:.0f}s (threshold: {timeout_threshold}s)',
                {'agent_type': agent_type, 'last_seen': last_seen, 'elapsed_seconds': elapsed_seconds}
            )

    except Exception as e:
        logger.error(f"Error evaluating agent timeout: {e}")

    return None


# ============================================================================
# Alert Summary
# ============================================================================

def get_alert_summary(hours: int = 24) -> Dict[str, Any]:
    """
    Get summary of recent alerts.

    Args:
        hours: Number of hours to look back

    Returns:
        Alert summary
    """
    history = load_alert_history()

    # Filter by time window
    cutoff_time = datetime.now(timezone.utc).timestamp() - (hours * 3600)
    recent_alerts = [
        alert for alert in history
        if datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00')).timestamp() > cutoff_time
    ]

    # Count by severity
    severity_counts = {'critical': 0, 'warning': 0, 'info': 0}
    for alert in recent_alerts:
        severity = alert.get('severity', 'info')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    # Count by type
    type_counts = {}
    for alert in recent_alerts:
        alert_type = alert.get('type', 'unknown')
        type_counts[alert_type] = type_counts.get(alert_type, 0) + 1

    return {
        'time_window_hours': hours,
        'total_alerts': len(recent_alerts),
        'by_severity': severity_counts,
        'by_type': type_counts,
        'recent_alerts': recent_alerts[:10],  # Last 10
    }


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI entry point for alert manager."""
    import argparse

    parser = argparse.ArgumentParser(description='RALF Alert Manager')
    parser.add_argument('--test', action='store_true', help='Trigger test alert')
    parser.add_argument('--summary', type=int, default=24, help='Show alert summary (hours)')
    parser.add_argument('--history', action='store_true', help='Show alert history')

    args = parser.parse_args()

    if args.test:
        # Trigger test alert
        alert = trigger_alert(
            'test',
            'info',
            'Test alert - Alert manager is functioning',
            {'test': True}
        )
        print(f"Test alert triggered: {alert['id']}")

    elif args.history:
        # Show alert history
        history = load_alert_history()
        print(f"\n=== Alert History ({len(history)} alerts) ===")
        for alert in history[:20]:
            print(f"[{alert['timestamp']}] [{alert['severity'].upper()}] {alert['message']}")

    else:
        # Show summary
        summary = get_alert_summary(hours=args.summary)
        print(f"\n=== Alert Summary (Last {args.summary} hours) ===")
        print(f"Total Alerts: {summary['total_alerts']}")
        print(f"By Severity: {summary['by_severity']}")
        print(f"By Type: {summary['by_type']}")


if __name__ == '__main__':
    main()
