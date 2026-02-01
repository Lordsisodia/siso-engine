#!/usr/bin/env python3
"""
Metrics Collector for RALF Performance Monitoring
Collects and stores performance metrics from planner/executor runs

Version: 1.0.0
Author: RALF System
Created: 2026-02-01
"""

import yaml
import json
from pathlib import Path
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

# Project paths
PROJECT_DIR = Path("/workspaces/blackbox5/5-project-memory/blackbox5")
METRICS_DIR = PROJECT_DIR / ".autonomous" / "data" / "metrics"
PLANNER_RUNS_DIR = PROJECT_DIR / "runs" / "planner"
EXECUTOR_RUNS_DIR = PROJECT_DIR / "runs" / "executor"

# Storage settings
METRICS_FILE = METRICS_DIR / "metrics.yaml"
MAX_RUNS_TO_STORE = 1000

# Ensure metrics directory exists
METRICS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Metrics Collection Functions
# ============================================================================

def extract_metrics_from_run(run_dir: Path, agent_type: str) -> Optional[Dict[str, Any]]:
    """
    Extract metrics from a single run directory.

    Args:
        run_dir: Path to the run directory (e.g., runs/executor/run-0058)
        agent_type: Type of agent ('planner' or 'executor')

    Returns:
        Dictionary of metrics or None if extraction fails
    """
    try:
        metadata_file = run_dir / "metadata.yaml"

        if not metadata_file.exists():
            logger.warning(f"No metadata.yaml found in {run_dir}")
            return None

        with open(metadata_file, 'r') as f:
            metadata = yaml.safe_load(f)

        if not metadata:
            logger.warning(f"Empty metadata in {run_dir}")
            return None

        # Extract key metrics
        loop_data = metadata.get('loop', {})
        state_data = metadata.get('state', {})

        # Calculate duration if end timestamp exists
        duration_seconds = None
        if 'timestamp_end' in loop_data:
            start_time = loop_data.get('timestamp_start', loop_data.get('timestamp'))
            end_time = loop_data['timestamp_end']

            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration_seconds = int((end_dt - start_dt).total_seconds())
            except Exception as e:
                logger.warning(f"Could not calculate duration for {run_dir}: {e}")

        # Extract outcome
        task_status = state_data.get('task_status', 'unknown')
        result = 'success' if task_status == 'completed' else task_status

        # Build metrics record
        metrics = {
            'timestamp': loop_data.get('timestamp_start', datetime.now(timezone.utc).isoformat()),
            'run_number': loop_data.get('number', int(run_dir.name.split('-')[-1])),
            'run_directory': str(run_dir),
            'agent_type': agent_type,
            'agent': loop_data.get('agent', agent_type),
            'duration_seconds': duration_seconds,
            'task_id': state_data.get('task_claimed'),
            'task_status': task_status,
            'result': result,
            'files_modified': len(state_data.get('files_modified', [])),
            'commit_hash': state_data.get('commit_hash'),
            'actions_taken': len(loop_data.get('actions_taken', [])),
            'blockers': len(loop_data.get('blockers', [])),
            'discoveries': len(loop_data.get('discoveries', [])),
            'questions_asked': len(loop_data.get('questions_asked', [])),
        }

        return metrics

    except Exception as e:
        logger.error(f"Error extracting metrics from {run_dir}: {e}")
        return None


def collect_all_metrics() -> List[Dict[str, Any]]:
    """
    Collect metrics from all planner and executor runs.

    Returns:
        List of metric records, sorted by timestamp (newest first)
    """
    all_metrics = []

    # Collect from executor runs
    if EXECUTOR_RUNS_DIR.exists():
        for run_dir in sorted(EXECUTOR_RUNS_DIR.iterdir()):
            if run_dir.is_dir() and run_dir.name.startswith('run-'):
                metrics = extract_metrics_from_run(run_dir, 'executor')
                if metrics:
                    all_metrics.append(metrics)

    # Collect from planner runs
    if PLANNER_RUNS_DIR.exists():
        for run_dir in sorted(PLANNER_RUNS_DIR.iterdir()):
            if run_dir.is_dir() and run_dir.name.startswith('run-'):
                metrics = extract_metrics_from_run(run_dir, 'planner')
                if metrics:
                    all_metrics.append(metrics)

    # Sort by timestamp (newest first)
    all_metrics.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    logger.info(f"Collected {len(all_metrics)} metrics from runs")
    return all_metrics


def load_existing_metrics() -> List[Dict[str, Any]]:
    """
    Load existing metrics from storage.

    Returns:
        List of existing metric records
    """
    try:
        if METRICS_FILE.exists():
            with open(METRICS_FILE, 'r') as f:
                data = yaml.safe_load(f)
                return data.get('metrics', []) if data else []
    except Exception as e:
        logger.error(f"Error loading existing metrics: {e}")

    return []


def save_metrics(metrics: List[Dict[str, Any]]) -> bool:
    """
    Save metrics to storage, respecting retention policy.

    Args:
        metrics: List of metric records to save

    Returns:
        True if save successful, False otherwise
    """
    try:
        # Apply retention policy
        if len(metrics) > MAX_RUNS_TO_STORE:
            metrics = metrics[:MAX_RUNS_TO_STORE]
            logger.info(f"Applied retention policy: keeping {MAX_RUNS_TO_STORE} most recent runs")

        # Create data structure
        data = {
            'metadata': {
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'total_runs': len(metrics),
                'retention_policy': MAX_RUNS_TO_STORE,
            },
            'metrics': metrics
        }

        # Write to file
        with open(METRICS_FILE, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved {len(metrics)} metrics to {METRICS_FILE}")
        return True

    except Exception as e:
        logger.error(f"Error saving metrics: {e}")
        return False


def collect_and_store_metrics() -> Dict[str, Any]:
    """
    Main function: collect all metrics and store them.

    Returns:
        Summary of collection results
    """
    logger.info("Starting metrics collection...")

    # Load existing metrics
    existing_metrics = load_existing_metrics()
    logger.info(f"Loaded {len(existing_metrics)} existing metrics")

    # Collect new metrics from runs
    new_metrics = collect_all_metrics()
    logger.info(f"Collected {len(new_metrics)} metrics from runs")

    # Merge: use new_metrics (fresh collection from all runs)
    # In the future, we could do incremental updates, but for now re-collecting is safer
    merged_metrics = new_metrics

    # Save to storage
    success = save_metrics(merged_metrics)

    # Build summary
    summary = {
        'success': success,
        'total_metrics': len(merged_metrics),
        'executor_runs': len([m for m in merged_metrics if m.get('agent_type') == 'executor']),
        'planner_runs': len([m for m in merged_metrics if m.get('agent_type') == 'planner']),
        'last_updated': datetime.now(timezone.utc).isoformat(),
    }

    logger.info(f"Metrics collection complete: {summary}")
    return summary


def get_metrics_summary() -> Dict[str, Any]:
    """
    Get a summary of stored metrics.

    Returns:
        Summary statistics
    """
    metrics = load_existing_metrics()

    if not metrics:
        return {
            'total_runs': 0,
            'executor_runs': 0,
            'planner_runs': 0,
            'date_range': None,
        }

    executor_runs = [m for m in metrics if m.get('agent_type') == 'executor']
    planner_runs = [m for m in metrics if m.get('agent_type') == 'planner']

    # Calculate date range
    timestamps = [m.get('timestamp') for m in metrics if m.get('timestamp')]
    date_range = {
        'earliest': min(timestamps) if timestamps else None,
        'latest': max(timestamps) if timestamps else None,
    }

    return {
        'total_runs': len(metrics),
        'executor_runs': len(executor_runs),
        'planner_runs': len(planner_runs),
        'date_range': date_range,
    }


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI entry point for metrics collection."""
    import argparse

    parser = argparse.ArgumentParser(description='RALF Metrics Collector')
    parser.add_argument('--summary', action='store_true', help='Show metrics summary')
    parser.add_argument('--collect', action='store_true', help='Collect and store metrics')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.summary:
        summary = get_metrics_summary()
        print(json.dumps(summary, indent=2))
    elif args.collect:
        result = collect_and_store_metrics()
        print(json.dumps(result, indent=2))
    else:
        # Default: collect and store
        result = collect_and_store_metrics()
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
