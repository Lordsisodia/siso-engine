#!/usr/bin/env python3
"""
Historical Analyzer for RALF Performance Monitoring
Analyzes trends and patterns in historical performance data

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
from datetime import datetime, timezone, timedelta
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
METRICS_FILE = PROJECT_DIR / ".autonomous" / "data" / "metrics" / "metrics.yaml"

# ============================================================================
# Data Loading Functions
# ============================================================================

def load_metrics() -> List[Dict[str, Any]]:
    """
    Load metrics from storage.

    Returns:
        List of metric records
    """
    try:
        if METRICS_FILE.exists():
            with open(METRICS_FILE, 'r') as f:
                data = yaml.safe_load(f)
                return data.get('metrics', []) if data else []
    except Exception as e:
        logger.error(f"Error loading metrics: {e}")

    return []


def filter_metrics_by_window(
    metrics: List[Dict[str, Any]],
    window: int = 100,
    agent_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter metrics by time window and agent type.

    Args:
        metrics: List of metric records
        window: Number of most recent runs to include
        agent_type: Filter by agent type ('planner', 'executor', or None for both)

    Returns:
        Filtered list of metrics
    """
    filtered = metrics

    # Filter by agent type if specified
    if agent_type:
        filtered = [m for m in filtered if m.get('agent_type') == agent_type]

    # Take N most recent runs
    filtered = filtered[:window]

    return filtered


# ============================================================================
# Trend Analysis Functions
# ============================================================================

def calculate_velocity_trend(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate velocity trend (runs per hour).

    Args:
        metrics: List of metric records (should be executor runs)

    Returns:
        Velocity trend statistics
    """
    if len(metrics) < 2:
        return {'average': 0, 'trend': 'unknown', 'recent': 0, 'baseline': 0}

    # Calculate durations
    durations = [m.get('duration_seconds') for m in metrics if m.get('duration_seconds')]

    if not durations:
        return {'average': 0, 'trend': 'unknown', 'recent': 0, 'baseline': 0}

    # Calculate average duration (in minutes)
    avg_duration_seconds = statistics.mean(durations)
    avg_duration_minutes = avg_duration_seconds / 60

    # Velocity = runs per hour = 60 / avg_duration_minutes
    if avg_duration_minutes > 0:
        velocity = 60 / avg_duration_minutes
    else:
        velocity = 0

    # Calculate recent vs baseline
    recent_count = len(metrics) // 3  # Most recent 1/3
    recent_metrics = metrics[:recent_count] if recent_count > 0 else metrics
    baseline_metrics = metrics[recent_count:] if recent_count > 0 else []

    recent_durations = [m.get('duration_seconds', 0) for m in recent_metrics if m.get('duration_seconds')]
    baseline_durations = [m.get('duration_seconds', 0) for m in baseline_metrics if m.get('duration_seconds')]

    recent_velocity = 0
    baseline_velocity = 0

    if recent_durations:
        recent_avg_min = statistics.mean(recent_durations) / 60
        recent_velocity = 60 / recent_avg_min if recent_avg_min > 0 else 0

    if baseline_durations:
        baseline_avg_min = statistics.mean(baseline_durations) / 60
        baseline_velocity = 60 / baseline_avg_min if baseline_avg_min > 0 else 0

    # Determine trend
    if recent_velocity > baseline_velocity * 1.1:
        trend = 'improving'  # Getting faster
    elif recent_velocity < baseline_velocity * 0.9:
        trend = 'degrading'  # Getting slower
    else:
        trend = 'stable'

    return {
        'average': round(velocity, 2),
        'recent': round(recent_velocity, 2),
        'baseline': round(baseline_velocity, 2),
        'trend': trend,
        'sample_size': len(durations),
    }


def calculate_success_rate(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate success rate trend.

    Args:
        metrics: List of metric records

    Returns:
        Success rate statistics
    """
    if not metrics:
        return {'average': 0, 'trend': 'unknown', 'recent': 0, 'baseline': 0}

    # Count successes
    total = len(metrics)
    successes = len([m for m in metrics if m.get('result') == 'success'])

    if total == 0:
        return {'average': 0, 'trend': 'unknown', 'recent': 0, 'baseline': 0}

    success_rate = (successes / total) * 100

    # Calculate recent vs baseline
    recent_count = total // 3
    recent_metrics = metrics[:recent_count] if recent_count > 0 else metrics
    baseline_metrics = metrics[recent_count:] if recent_count > 0 else []

    recent_total = len(recent_metrics)
    recent_successes = len([m for m in recent_metrics if m.get('result') == 'success'])
    recent_rate = (recent_successes / recent_total * 100) if recent_total > 0 else 0

    baseline_total = len(baseline_metrics)
    baseline_successes = len([m for m in baseline_metrics if m.get('result') == 'success'])
    baseline_rate = (baseline_successes / baseline_total * 100) if baseline_total > 0 else 0

    # Determine trend
    if recent_rate > baseline_rate + 5:
        trend = 'improving'
    elif recent_rate < baseline_rate - 5:
        trend = 'degrading'
    else:
        trend = 'stable'

    return {
        'average': round(success_rate, 1),
        'recent': round(recent_rate, 1),
        'baseline': round(baseline_rate, 1),
        'trend': trend,
        'total_runs': total,
        'successful_runs': successes,
    }


def calculate_duration_trend(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate duration trend (average run time).

    Args:
        metrics: List of metric records

    Returns:
        Duration trend statistics
    """
    durations = [m.get('duration_seconds') for m in metrics if m.get('duration_seconds')]

    if not durations:
        return {'average': 0, 'trend': 'unknown', 'recent': 0, 'baseline': 0}

    avg_duration = statistics.mean(durations)

    # Calculate recent vs baseline
    recent_count = len(metrics) // 3
    recent_metrics = metrics[:recent_count] if recent_count > 0 else metrics
    baseline_metrics = metrics[recent_count:] if recent_count > 0 else []

    recent_durations = [m.get('duration_seconds', 0) for m in recent_metrics if m.get('duration_seconds')]
    baseline_durations = [m.get('duration_seconds', 0) for m in baseline_metrics if m.get('duration_seconds')]

    recent_avg = statistics.mean(recent_durations) if recent_durations else 0
    baseline_avg = statistics.mean(baseline_durations) if baseline_durations else 0

    # Determine trend
    if recent_avg < baseline_avg * 0.9:
        trend = 'improving'  # Getting faster
    elif recent_avg > baseline_avg * 1.1:
        trend = 'degrading'  # Getting slower
    else:
        trend = 'stable'

    return {
        'average': round(avg_duration, 1),
        'recent': round(recent_avg, 1),
        'baseline': round(baseline_avg, 1),
        'trend': trend,
        'min': round(min(durations), 1),
        'max': round(max(durations), 1),
        'median': round(statistics.median(durations), 1),
        'sample_size': len(durations),
    }


def calculate_throughput(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate throughput (files modified per run, lines delivered).

    Args:
        metrics: List of metric records

    Returns:
        Throughput statistics
    """
    if not metrics:
        return {'avg_files_per_run': 0, 'total_files': 0}

    files_counts = [m.get('files_modified', 0) for m in metrics]
    total_files = sum(files_counts)
    avg_files = statistics.mean(files_counts) if files_counts else 0

    return {
        'avg_files_per_run': round(avg_files, 1),
        'total_files': total_files,
        'max_files': max(files_counts) if files_counts else 0,
        'min_files': min(files_counts) if files_counts else 0,
    }


def analyze_trends(window: int = 100, agent_type: str = 'executor') -> Dict[str, Any]:
    """
    Perform comprehensive trend analysis.

    Args:
        window: Number of recent runs to analyze
        agent_type: Type of agent to analyze ('executor' or 'planner')

    Returns:
        Comprehensive trend analysis
    """
    metrics = load_metrics()

    if not metrics:
        logger.warning("No metrics available for analysis")
        return {}

    filtered = filter_metrics_by_window(metrics, window, agent_type)

    if not filtered:
        logger.warning(f"No metrics found for agent_type={agent_type} in window={window}")
        return {}

    logger.info(f"Analyzing {len(filtered)} {agent_type} runs")

    analysis = {
        'metadata': {
            'window': window,
            'agent_type': agent_type,
            'sample_size': len(filtered),
            'analyzed_at': datetime.now(timezone.utc).isoformat(),
        },
        'velocity': calculate_velocity_trend(filtered),
        'success_rate': calculate_success_rate(filtered),
        'duration': calculate_duration_trend(filtered),
        'throughput': calculate_throughput(filtered),
    }

    return analysis


def compare_vs_baseline(
    current_metrics: Dict[str, Any],
    baseline_window: int = 100
) -> Dict[str, Any]:
    """
    Compare current metrics against historical baseline.

    Args:
        current_metrics: Current run metrics
        baseline_window: Window size for baseline calculation

    Returns:
        Comparison results
    """
    metrics = load_metrics()
    baseline = filter_metrics_by_window(metrics, baseline_window, 'executor')

    if not baseline:
        return {'status': 'no_baseline'}

    # Extract comparable metrics
    baseline_duration = calculate_duration_trend(baseline)
    baseline_success = calculate_success_rate(baseline)

    current_duration = current_metrics.get('duration_seconds', 0)
    current_success = 1 if current_metrics.get('result') == 'success' else 0

    # Compare
    comparisons = []

    # Duration comparison
    if current_duration > 0:
        baseline_avg = baseline_duration.get('average', 0)
        if baseline_avg > 0:
            ratio = current_duration / baseline_avg
            if ratio > 2:
                comparisons.append({
                    'metric': 'duration',
                    'status': 'critical',
                    'message': f'Duration {ratio:.1f}x baseline average',
                    'current': current_duration,
                    'baseline': baseline_avg,
                })
            elif ratio > 1.5:
                comparisons.append({
                    'metric': 'duration',
                    'status': 'warning',
                    'message': f'Duration {ratio:.1f}x baseline average',
                    'current': current_duration,
                    'baseline': baseline_avg,
                })

    return {
        'baseline_window': baseline_window,
        'baseline_sample_size': len(baseline),
        'comparisons': comparisons,
    }


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI entry point for historical analysis."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='RALF Historical Analyzer')
    parser.add_argument('--window', type=int, default=100, help='Analysis window (default: 100)')
    parser.add_argument('--agent', choices=['executor', 'planner'], default='executor', help='Agent type')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    analysis = analyze_trends(window=args.window, agent_type=args.agent)

    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print(f"\n=== Historical Analysis: {args.agent.upper()} ===")
        print(f"Sample Size: {analysis['metadata']['sample_size']} runs")
        print(f"\nVelocity: {analysis['velocity']['average']} runs/hour ({analysis['velocity']['trend']})")
        print(f"Success Rate: {analysis['success_rate']['average']}% ({analysis['success_rate']['trend']})")
        print(f"Duration: {analysis['duration']['average']}s avg ({analysis['duration']['trend']})")
        print(f"Throughput: {analysis['throughput']['avg_files_per_run']} files/run")


if __name__ == '__main__':
    main()
