#!/usr/bin/env python3
"""
Performance Reporter for RALF Performance Monitoring
Generates daily, weekly, and custom performance reports

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
from typing import Dict, List, Any, Optional
import logging
import json

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
REPORTS_DIR = PROJECT_DIR / ".autonomous" / "data" / "reports"

# Ensure reports directory exists
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Data Loading
# ============================================================================

def load_metrics() -> List[Dict[str, Any]]:
    """Load metrics from storage."""
    try:
        if METRICS_FILE.exists():
            with open(METRICS_FILE, 'r') as f:
                data = yaml.safe_load(f)
                return data.get('metrics', []) if data else []
    except Exception as e:
        logger.error(f"Error loading metrics: {e}")

    return []


def filter_metrics_by_date_range(
    metrics: List[Dict[str, Any]],
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, Any]]:
    """
    Filter metrics by date range.

    Args:
        metrics: List of metric records
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)

    Returns:
        Filtered list of metrics
    """
    filtered = []

    for metric in metrics:
        timestamp_str = metric.get('timestamp')
        if not timestamp_str:
            continue

        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            if start_date <= timestamp <= end_date:
                filtered.append(metric)
        except Exception as e:
            logger.warning(f"Error parsing timestamp {timestamp_str}: {e}")

    return filtered


# ============================================================================
# Report Generation
# ============================================================================

def calculate_report_statistics(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics for a report.

    Args:
        metrics: List of metric records

    Returns:
        Statistics dictionary
    """
    if not metrics:
        return {
            'total_runs': 0,
            'executor_runs': 0,
            'planner_runs': 0,
        }

    executor_runs = [m for m in metrics if m.get('agent_type') == 'executor']
    planner_runs = [m for m in metrics if m.get('agent_type') == 'planner']

    # Executor statistics
    executor_stats = {}
    if executor_runs:
        durations = [m.get('duration_seconds', 0) for m in executor_runs if m.get('duration_seconds')]
        successes = len([m for m in executor_runs if m.get('result') == 'success'])

        executor_stats = {
            'total_runs': len(executor_runs),
            'successful_runs': successes,
            'success_rate': round((successes / len(executor_runs)) * 100, 1) if executor_runs else 0,
            'avg_duration': round(sum(durations) / len(durations), 1) if durations else 0,
            'min_duration': round(min(durations), 1) if durations else 0,
            'max_duration': round(max(durations), 1) if durations else 0,
            'total_files_modified': sum([m.get('files_modified', 0) for m in executor_runs]),
        }

    # Planner statistics
    planner_stats = {}
    if planner_runs:
        planner_durations = [m.get('duration_seconds', 0) for m in planner_runs if m.get('duration_seconds')]
        planner_successes = len([m for m in planner_runs if m.get('result') == 'success'])

        planner_stats = {
            'total_runs': len(planner_runs),
            'successful_runs': planner_successes,
            'success_rate': round((planner_successes / len(planner_runs)) * 100, 1) if planner_runs else 0,
            'avg_duration': round(sum(planner_durations) / len(planner_durations), 1) if planner_durations else 0,
        }

    return {
        'total_runs': len(metrics),
        'executor': executor_stats,
        'planner': planner_stats,
    }


def generate_markdown_report(
    report_type: str,
    start_date: datetime,
    end_date: datetime,
    stats: Dict[str, Any],
    metrics: List[Dict[str, Any]]
) -> str:
    """
    Generate a Markdown report.

    Args:
        report_type: Type of report (daily, weekly, custom)
        start_date: Report start date
        end_date: Report end date
        stats: Statistics dictionary
        metrics: List of metric records

    Returns:
        Markdown report content
    """
    lines = []

    # Header
    title = f"RALF Performance Report - {report_type.capitalize()}"
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Period:** {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total Runs:** {stats['total_runs']}")
    if stats.get('executor'):
        lines.append(f"- **Executor Runs:** {stats['executor']['total_runs']}")
        lines.append(f"  - Success Rate: {stats['executor']['success_rate']}%")
        lines.append(f"  - Avg Duration: {stats['executor']['avg_duration']}s")
        lines.append(f"  - Files Modified: {stats['executor']['total_files_modified']}")
    if stats.get('planner'):
        lines.append(f"- **Planner Runs:** {stats['planner']['total_runs']}")
        lines.append(f"  - Success Rate: {stats['planner']['success_rate']}%")
        lines.append(f"  - Avg Duration: {stats['planner']['avg_duration']}s")
    lines.append("")

    # Top Performers (fastest executor runs)
    executor_runs = [m for m in metrics if m.get('agent_type') == 'executor']
    if executor_runs:
        lines.append("## Top Performers (Fastest Executor Runs)")
        lines.append("")
        fastest = sorted(executor_runs, key=lambda x: x.get('duration_seconds', 999999))[:5]
        for i, run in enumerate(fastest, 1):
            lines.append(f"{i}. Run {run.get('run_number')}: {run.get('duration_seconds')}s - {run.get('task_id', 'N/A')}")
        lines.append("")

    # Issues (failed runs)
    failed_runs = [m for m in metrics if m.get('result') != 'success']
    if failed_runs:
        lines.append("## Issues (Failed/Blocked Runs)")
        lines.append("")
        for run in failed_runs[:10]:
            lines.append(f"- **Run {run.get('run_number')}**: {run.get('result')} - {run.get('task_id', 'N/A')}")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("*Generated by RALF Performance Monitoring System*")

    return "\n".join(lines)


def generate_json_report(
    report_type: str,
    start_date: datetime,
    end_date: datetime,
    stats: Dict[str, Any],
    metrics: List[Dict[str, Any]]
) -> str:
    """
    Generate a JSON report.

    Args:
        report_type: Type of report
        start_date: Report start date
        end_date: Report end date
        stats: Statistics dictionary
        metrics: List of metric records

    Returns:
        JSON report string
    """
    report = {
        'report_type': report_type,
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
        },
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'statistics': stats,
        'metrics_sample': metrics[:20],  # First 20 as sample
    }

    return json.dumps(report, indent=2)


def generate_csv_report(metrics: List[Dict[str, Any]]) -> str:
    """
    Generate a CSV report of metrics.

    Args:
        metrics: List of metric records

    Returns:
        CSV report string
    """
    if not metrics:
        return "timestamp,run_number,agent_type,duration,task_id,result\n"

    lines = []
    lines.append("timestamp,run_number,agent_type,duration_seconds,task_id,result,files_modified,blockers")

    for m in metrics:
        lines.append(
            f"{m.get('timestamp', '')},"
            f"{m.get('run_number', '')},"
            f"{m.get('agent_type', '')},"
            f"{m.get('duration_seconds', '')},"
            f"{m.get('task_id', '')},"
            f"{m.get('result', '')},"
            f"{m.get('files_modified', '')},"
            f"{m.get('blockers', '')}"
        )

    return "\n".join(lines)


# ============================================================================
# Report Functions
# ============================================================================

def generate_daily_report() -> Dict[str, str]:
    """
    Generate daily performance report (last 24 hours).

    Returns:
        Dictionary with report file paths
    """
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(hours=24)

    metrics = load_metrics()
    filtered = filter_metrics_by_date_range(metrics, start_date, now)
    stats = calculate_report_statistics(filtered)

    # Generate reports
    report_date = now.strftime('%Y-%m-%d')
    base_filename = f"daily_{report_date}"

    # Markdown
    md_content = generate_markdown_report('daily', start_date, now, stats, filtered)
    md_file = REPORTS_DIR / f"{base_filename}.md"
    with open(md_file, 'w') as f:
        f.write(md_content)

    # JSON
    json_content = generate_json_report('daily', start_date, now, stats, filtered)
    json_file = REPORTS_DIR / f"{base_filename}.json"
    with open(json_file, 'w') as f:
        f.write(json_content)

    logger.info(f"Daily report generated: {md_file}")

    return {
        'markdown': str(md_file),
        'json': str(json_file),
        'period': f"{start_date.isoformat()} to {now.isoformat()}",
        'total_runs': stats['total_runs'],
    }


def generate_weekly_report() -> Dict[str, str]:
    """
    Generate weekly performance report (last 7 days).

    Returns:
        Dictionary with report file paths
    """
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=7)

    metrics = load_metrics()
    filtered = filter_metrics_by_date_range(metrics, start_date, now)
    stats = calculate_report_statistics(filtered)

    # Generate reports
    report_week = now.strftime('%Y-W%U')
    base_filename = f"weekly_{report_week}"

    # Markdown
    md_content = generate_markdown_report('weekly', start_date, now, stats, filtered)
    md_file = REPORTS_DIR / f"{base_filename}.md"
    with open(md_file, 'w') as f:
        f.write(md_content)

    # JSON
    json_content = generate_json_report('weekly', start_date, now, stats, filtered)
    json_file = REPORTS_DIR / f"{base_filename}.json"
    with open(json_file, 'w') as f:
        f.write(json_content)

    logger.info(f"Weekly report generated: {md_file}")

    return {
        'markdown': str(md_file),
        'json': str(json_file),
        'period': f"{start_date.isoformat()} to {now.isoformat()}",
        'total_runs': stats['total_runs'],
    }


def generate_custom_report(
    hours_back: int,
    output_format: str = 'markdown'
) -> Dict[str, str]:
    """
    Generate custom performance report.

    Args:
        hours_back: Number of hours to look back
        output_format: Output format (markdown, json, csv)

    Returns:
        Dictionary with report file path
    """
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(hours=hours_back)

    metrics = load_metrics()
    filtered = filter_metrics_by_date_range(metrics, start_date, now)
    stats = calculate_report_statistics(filtered)

    # Generate report
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    base_filename = f"custom_{timestamp}"

    if output_format == 'markdown':
        content = generate_markdown_report(f'custom_{hours_back}h', start_date, now, stats, filtered)
        ext = 'md'
    elif output_format == 'json':
        content = generate_json_report(f'custom_{hours_back}h', start_date, now, stats, filtered)
        ext = 'json'
    elif output_format == 'csv':
        content = generate_csv_report(filtered)
        ext = 'csv'
    else:
        raise ValueError(f"Unknown output format: {output_format}")

    report_file = REPORTS_DIR / f"{base_filename}.{ext}"
    with open(report_file, 'w') as f:
        f.write(content)

    logger.info(f"Custom report generated: {report_file}")

    return {
        'file': str(report_file),
        'format': output_format,
        'period': f"{start_date.isoformat()} to {now.isoformat()}",
        'total_runs': stats['total_runs'],
    }


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI entry point for performance reporter."""
    import argparse

    parser = argparse.ArgumentParser(description='RALF Performance Reporter')
    parser.add_argument('--daily', action='store_true', help='Generate daily report')
    parser.add_argument('--weekly', action='store_true', help='Generate weekly report')
    parser.add_argument('--custom', type=int, metavar='HOURS', help='Generate custom report (hours back)')
    parser.add_argument('--format', choices=['markdown', 'json', 'csv'], default='markdown', help='Output format')

    args = parser.parse_args()

    if args.daily:
        result = generate_daily_report()
        print(f"Daily report: {result['markdown']}")
    elif args.weekly:
        result = generate_weekly_report()
        print(f"Weekly report: {result['markdown']}")
    elif args.custom:
        result = generate_custom_report(args.custom, args.format)
        print(f"Custom report: {result['file']}")
    else:
        # Default: daily report
        result = generate_daily_report()
        print(f"Daily report: {result['markdown']}")


if __name__ == '__main__':
    main()
