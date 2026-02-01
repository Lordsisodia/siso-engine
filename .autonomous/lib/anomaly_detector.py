#!/usr/bin/env python3
"""
Anomaly Detector for RALF Performance Monitoring
Detects anomalies and outliers in performance metrics

Version: 1.0.0
Author: RALF System
Created: 2026-02-01
"""

import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import logging
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

PROJECT_DIR = Path("/workspaces/blackbox5/5-project-memory/blackbox5")
METRICS_FILE = PROJECT_DIR / ".autonomous" / "data" / "metrics" / "metrics.yaml"

# Anomaly detection thresholds
Z_SCORE_CRITICAL = 3.0  # 3 standard deviations
Z_SCORE_WARNING = 2.5
Z_SCORE_INFO = 2.0

DURATION_CRITICAL_MULTIPLIER = 2.0  # 2x average duration
DURATION_WARNING_MULTIPLIER = 1.5

ERROR_RATE_CRITICAL = 0.5  # 50% error rate
ERROR_RATE_WARNING = 0.2  # 20% error rate

# ============================================================================
# Data Loading Functions
# ============================================================================

def load_metrics(agent_type: str = 'executor') -> List[Dict[str, Any]]:
    """
    Load metrics from storage.

    Args:
        agent_type: Filter by agent type

    Returns:
        List of metric records
    """
    try:
        if METRICS_FILE.exists():
            with open(METRICS_FILE, 'r') as f:
                data = yaml.safe_load(f)
                all_metrics = data.get('metrics', []) if data else []

                # Filter by agent type
                if agent_type:
                    all_metrics = [m for m in all_metrics if m.get('agent_type') == agent_type]

                return all_metrics
    except Exception as e:
        logger.error(f"Error loading metrics: {e}")

    return []


# ============================================================================
# Statistical Anomaly Detection
# ============================================================================

def calculate_z_score(value: float, mean: float, std_dev: float) -> float:
    """
    Calculate z-score for a value.

    Args:
        value: Value to check
        mean: Mean of the distribution
        std_dev: Standard deviation of the distribution

    Returns:
        Z-score
    """
    if std_dev == 0:
        return 0.0
    return abs((value - mean) / std_dev)


def detect_duration_anomalies(
    metrics: List[Dict[str, Any]],
    baseline_window: int = 50
) -> List[Dict[str, Any]]:
    """
    Detect duration anomalies using z-score analysis.

    Args:
        metrics: List of metric records
        baseline_window: Number of runs to use as baseline

    Returns:
        List of detected anomalies
    """
    if len(metrics) < baseline_window + 1:
        return []  # Not enough data

    # Separate baseline and current
    baseline_metrics = metrics[baseline_window:]
    current_metrics = metrics[:baseline_window]

    # Calculate baseline statistics
    baseline_durations = [
        m.get('duration_seconds', 0)
        for m in baseline_metrics
        if m.get('duration_seconds')
    ]

    if not baseline_durations:
        return []

    mean_duration = statistics.mean(baseline_durations)
    std_duration = statistics.stdev(baseline_durations) if len(baseline_durations) > 1 else 0

    anomalies = []

    # Check current metrics for anomalies
    for metric in current_metrics:
        duration = metric.get('duration_seconds')
        if duration is None:
            continue

        z_score = calculate_z_score(duration, mean_duration, std_duration)

        if z_score >= Z_SCORE_CRITICAL:
            anomalies.append({
                'type': 'duration',
                'severity': 'critical',
                'run_number': metric.get('run_number'),
                'timestamp': metric.get('timestamp'),
                'value': duration,
                'baseline_mean': round(mean_duration, 1),
                'z_score': round(z_score, 2),
                'message': f'Duration {duration}s is {z_score:.1f}σ from baseline',
            })
        elif z_score >= Z_SCORE_WARNING:
            anomalies.append({
                'type': 'duration',
                'severity': 'warning',
                'run_number': metric.get('run_number'),
                'timestamp': metric.get('timestamp'),
                'value': duration,
                'baseline_mean': round(mean_duration, 1),
                'z_score': round(z_score, 2),
                'message': f'Duration {duration}s is {z_score:.1f}σ from baseline',
            })

    return anomalies


def detect_success_rate_anomalies(
    metrics: List[Dict[str, Any]],
    window: int = 20
) -> List[Dict[str, Any]]:
    """
    Detect success rate anomalies.

    Args:
        metrics: List of metric records
        window: Window size for success rate calculation

    Returns:
        List of detected anomalies
    """
    if len(metrics) < window * 2:
        return []

    anomalies = []

    # Calculate success rate for each window
    for i in range(0, len(metrics) - window, window):
        window_metrics = metrics[i:i + window]

        successes = len([m for m in window_metrics if m.get('result') == 'success'])
        success_rate = successes / len(window_metrics)

        if success_rate < ERROR_RATE_CRITICAL:
            anomalies.append({
                'type': 'success_rate',
                'severity': 'critical',
                'window_start': window_metrics[-1].get('timestamp'),
                'window_end': window_metrics[0].get('timestamp'),
                'value': round(success_rate * 100, 1),
                'message': f'Success rate dropped to {success_rate * 100:.1f}% (threshold: {ERROR_RATE_CRITICAL * 100}%)',
            })
        elif success_rate < ERROR_RATE_WARNING:
            anomalies.append({
                'type': 'success_rate',
                'severity': 'warning',
                'window_start': window_metrics[-1].get('timestamp'),
                'window_end': window_metrics[0].get('timestamp'),
                'value': round(success_rate * 100, 1),
                'message': f'Success rate dropped to {success_rate * 100:.1f}% (threshold: {ERROR_RATE_WARNING * 100}%)',
            })

    return anomalies


def detect_blocker_streaks(
    metrics: List[Dict[str, Any]],
    threshold: int = 3
) -> List[Dict[str, Any]]:
    """
    Detect consecutive runs with blockers.

    Args:
        metrics: List of metric records
        threshold: Minimum consecutive blocked runs to trigger alert

    Returns:
        List of detected anomalies
    """
    anomalies = []
    streak_count = 0
    streak_runs = []

    for metric in metrics:
        blockers = metric.get('blockers', 0)

        if blockers > 0:
            streak_count += 1
            streak_runs.append(metric.get('run_number'))
        else:
            if streak_count >= threshold:
                anomalies.append({
                    'type': 'blocker_streak',
                    'severity': 'warning' if streak_count < threshold * 2 else 'critical',
                    'streak_length': streak_count,
                    'runs': streak_runs,
                    'message': f'{streak_count} consecutive runs with blockers',
                })
            streak_count = 0
            streak_runs = []

    # Check if streak ends at the most recent run
    if streak_count >= threshold:
        anomalies.append({
            'type': 'blocker_streak',
            'severity': 'warning' if streak_count < threshold * 2 else 'critical',
            'streak_length': streak_count,
            'runs': streak_runs,
            'message': f'{streak_count} consecutive runs with blockers (ongoing)',
        })

    return anomalies


# ============================================================================
# Rule-Based Anomaly Detection
# ============================================================================

def detect_rule_based_anomalies(
    metrics: List[Dict[str, Any]],
    baseline_window: int = 50
) -> List[Dict[str, Any]]:
    """
    Detect anomalies using rule-based thresholds.

    Args:
        metrics: List of metric records
        baseline_window: Number of runs for baseline

    Returns:
        List of detected anomalies
    """
    if len(metrics) < baseline_window + 1:
        return []

    anomalies = []

    # Calculate baseline
    baseline_metrics = metrics[baseline_window:]
    baseline_durations = [
        m.get('duration_seconds', 0)
        for m in baseline_metrics
        if m.get('duration_seconds')
    ]

    if not baseline_durations:
        return []

    baseline_avg = statistics.mean(baseline_durations)

    # Check recent runs
    recent_metrics = metrics[:baseline_window]

    for metric in recent_metrics:
        duration = metric.get('duration_seconds')
        if duration is None:
            continue

        # Rule: Duration > 2x baseline average
        if duration > baseline_avg * DURATION_CRITICAL_MULTIPLIER:
            anomalies.append({
                'type': 'duration',
                'severity': 'critical',
                'run_number': metric.get('run_number'),
                'timestamp': metric.get('timestamp'),
                'value': duration,
                'baseline_avg': round(baseline_avg, 1),
                'multiplier': round(duration / baseline_avg, 1),
                'message': f'Duration {duration}s is {duration / baseline_avg:.1f}x baseline average',
            })
        elif duration > baseline_avg * DURATION_WARNING_MULTIPLIER:
            anomalies.append({
                'type': 'duration',
                'severity': 'warning',
                'run_number': metric.get('run_number'),
                'timestamp': metric.get('timestamp'),
                'value': duration,
                'baseline_avg': round(baseline_avg, 1),
                'multiplier': round(duration / baseline_avg, 1),
                'message': f'Duration {duration}s is {duration / baseline_avg:.1f}x baseline average',
            })

    return anomalies


# ============================================================================
# Combined Anomaly Detection
# ============================================================================

def detect_anomalies(
    agent_type: str = 'executor',
    baseline_window: int = 50,
    use_statistical: bool = True,
    use_rule_based: bool = True
) -> Dict[str, Any]:
    """
    Perform comprehensive anomaly detection.

    Args:
        agent_type: Type of agent to analyze
        baseline_window: Window size for baseline calculation
        use_statistical: Enable statistical detection
        use_rule_based: Enable rule-based detection

    Returns:
        Comprehensive anomaly detection results
    """
    metrics = load_metrics(agent_type)

    if not metrics:
        logger.warning(f"No metrics available for anomaly detection (agent_type={agent_type})")
        return {'anomalies': [], 'summary': {'total': 0, 'by_severity': {}}}

    logger.info(f"Detecting anomalies in {len(metrics)} {agent_type} runs")

    all_anomalies = []

    # Statistical detection
    if use_statistical:
        duration_anomalies = detect_duration_anomalies(metrics, baseline_window)
        all_anomalies.extend(duration_anomalies)

        success_rate_anomalies = detect_success_rate_anomalies(metrics)
        all_anomalies.extend(success_rate_anomalies)

        blocker_anomalies = detect_blocker_streaks(metrics)
        all_anomalies.extend(blocker_anomalies)

    # Rule-based detection
    if use_rule_based:
        rule_anomalies = detect_rule_based_anomalies(metrics, baseline_window)
        all_anomalies.extend(rule_anomalies)

    # Count by severity
    severity_counts = {'critical': 0, 'warning': 0, 'info': 0}
    for anomaly in all_anomalies:
        severity = anomaly.get('severity', 'info')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    return {
        'metadata': {
            'agent_type': agent_type,
            'baseline_window': baseline_window,
            'sample_size': len(metrics),
            'detected_at': datetime.now(timezone.utc).isoformat(),
        },
        'anomalies': all_anomalies,
        'summary': {
            'total': len(all_anomalies),
            'by_severity': severity_counts,
            'by_type': _count_by_type(all_anomalies),
        },
    }


def _count_by_type(anomalies: List[Dict[str, Any]]) -> Dict[str, int]:
    """Helper: Count anomalies by type."""
    type_counts = {}
    for anomaly in anomalies:
        anomaly_type = anomaly.get('type', 'unknown')
        type_counts[anomaly_type] = type_counts.get(anomaly_type, 0) + 1
    return type_counts


def check_single_run(
    run_metrics: Dict[str, Any],
    agent_type: str = 'executor'
) -> List[Dict[str, Any]]:
    """
    Check a single run for anomalies.

    Args:
        run_metrics: Metrics for a single run
        agent_type: Type of agent

    Returns:
        List of anomalies detected for this run
    """
    # Load historical data for baseline
    historical = load_metrics(agent_type)

    if not historical:
        return []

    # Extract baseline durations
    baseline_durations = [
        m.get('duration_seconds', 0)
        for m in historical
        if m.get('duration_seconds')
    ]

    if not baseline_durations:
        return []

    baseline_mean = statistics.mean(baseline_durations)
    baseline_std = statistics.stdev(baseline_durations) if len(baseline_durations) > 1 else 0

    anomalies = []

    # Check duration
    duration = run_metrics.get('duration_seconds')
    if duration:
        z_score = calculate_z_score(duration, baseline_mean, baseline_std)

        if z_score >= Z_SCORE_CRITICAL or duration > baseline_mean * DURATION_CRITICAL_MULTIPLIER:
            anomalies.append({
                'type': 'duration',
                'severity': 'critical',
                'value': duration,
                'baseline_mean': round(baseline_mean, 1),
                'z_score': round(z_score, 2),
            })
        elif z_score >= Z_SCORE_WARNING or duration > baseline_mean * DURATION_WARNING_MULTIPLIER:
            anomalies.append({
                'type': 'duration',
                'severity': 'warning',
                'value': duration,
                'baseline_mean': round(baseline_mean, 1),
                'z_score': round(z_score, 2),
            })

    # Check result
    if run_metrics.get('result') != 'success':
        anomalies.append({
            'type': 'failure',
            'severity': 'warning',
            'result': run_metrics.get('result'),
        })

    # Check blockers
    if run_metrics.get('blockers', 0) > 0:
        anomalies.append({
            'type': 'blocker',
            'severity': 'info',
            'blocker_count': run_metrics.get('blockers'),
        })

    return anomalies


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI entry point for anomaly detection."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='RALF Anomaly Detector')
    parser.add_argument('--agent', choices=['executor', 'planner'], default='executor', help='Agent type')
    parser.add_argument('--window', type=int, default=50, help='Baseline window size')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--verbose', action='store_true', help='Show detailed anomaly list')

    args = parser.parse_args()

    result = detect_anomalies(
        agent_type=args.agent,
        baseline_window=args.window,
        use_statistical=True,
        use_rule_based=True,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        summary = result['summary']
        print(f"\n=== Anomaly Detection: {args.agent.upper()} ===")
        print(f"Total Anomalies: {summary['total']}")
        print(f"  Critical: {summary['by_severity']['critical']}")
        print(f"  Warning: {summary['by_severity']['warning']}")
        print(f"  Info: {summary['by_severity']['info']}")
        print(f"\nBy Type: {summary['by_type']}")

        if args.verbose and result['anomalies']:
            print(f"\n=== Anomaly Details ===")
            for anomaly in result['anomalies'][:10]:  # Show first 10
                print(f"[{anomaly['severity'].upper()}] {anomaly.get('message', 'N/A')}")


if __name__ == '__main__':
    main()
