#!/usr/bin/env python3
"""
UI Cycle Status Tracker

Monitors UI Adaptive Development Cycle runs:
- Phase completion status
- Artifact presence and completeness
- Quality gate results
- Time tracking per phase
- Overall cycle health

No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class PhaseStatus:
    """Status of a single phase."""
    name: str
    number: int
    planned_minutes: int
    artifacts: list[str]
    completed: bool = False
    artifacts_present: list[str] = field(default_factory=list)
    artifacts_missing: list[str] = field(default_factory=list)
    duration_minutes: int | None = None
    issues: list[str] = field(default_factory=list)


@dataclass
class CycleStatus:
    """Overall status of a UI cycle."""
    cycle_id: str
    run_dir: Path
    started_at: str
    task: str
    url: str
    component: str
    phases: dict[str, PhaseStatus] = field(default_factory=dict)
    total_artifacts_present: int = 0
    total_artifacts_missing: int = 0
    overall_status: str = "unknown"


# Phase definitions with required artifacts
PHASE_DEFINITIONS = {
    "0": {
        "name": "Pre-Flight",
        "planned_minutes": 2,
        "artifacts": [],  # No specific artifacts, just validation
    },
    "1": {
        "name": "Observe",
        "planned_minutes": 5,
        "artifacts": [
            "screenshots/before/mobile.png",
            "screenshots/before/tablet.png",
            "screenshots/before/desktop.png",
            "logs/before-console.json",
            "logs/before-performance.json",
        ],
    },
    "2": {
        "name": "Define",
        "planned_minutes": 10,
        "artifacts": [
            "artifacts/success-criteria.md",
            "artifacts/acceptance.test.ts",
        ],
    },
    "3": {
        "name": "Build",
        "planned_minutes": 30,
        "artifacts": [
            "logs/typecheck.log",
            "logs/lint.log",
            "logs/build.log",
        ],
    },
    "4": {
        "name": "Verify",
        "planned_minutes": 15,
        "artifacts": [
            "screenshots/after/mobile.png",
            "screenshots/after/tablet.png",
            "screenshots/after/desktop.png",
            "logs/test-results.json",
            "logs/after-console.json",
            "logs/accessibility.json",
            "logs/after-performance.json",
            "artifacts/verification-report.md",
        ],
    },
    "5": {
        "name": "Deploy",
        "planned_minutes": 5,
        "artifacts": [
            "git-commit-sha.txt",
            "deployment-url.txt",
            "screenshots/production.png",
        ],
    },
    "6": {
        "name": "Close",
        "planned_minutes": 3,
        "artifacts": [],  # Artifacts are archived elsewhere
    },
}


def read_file(path: Path) -> str | None:
    """Read file content, return None if missing."""
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, IOError):
        return None


def parse_cycle_json(run_dir: Path) -> dict | None:
    """Parse cycle.json metadata."""
    cycle_json = run_dir / "cycle.json"
    content = read_file(cycle_json)
    if not content:
        return None

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


def parse_cycle_md(run_dir: Path) -> dict:
    """Parse cycle.md for phase completion status."""
    cycle_md = run_dir / "cycle.md"
    content = read_file(cycle_md) or ""

    phases_completed = {}

    # Look for phase completion markers (e.g., "✅" or "[x]")
    for phase_num, phase_def in PHASE_DEFINITIONS.items():
        phase_name = phase_def["name"]

        # Check if phase section exists
        phase_marker = f"### Phase {phase_num} ({phase_name})"
        if phase_marker in content:
            # Look for completion indicators in the phase section
            phase_section = content.split(phase_marker)[-1]
            if len(content.split(phase_marker)) > 1:
                phase_section = content.split(phase_marker)[1].split("### Phase")[0]

            # Check for completion markers
            if "✅" in phase_section or "[x]" in phase_section:
                phases_completed[phase_num] = True
            else:
                phases_completed[phase_num] = False
        else:
            phases_completed[phase_num] = False

    return phases_completed


def check_artifacts(run_dir: Path, phase_num: str) -> tuple[list[str], list[str]]:
    """Check which artifacts are present for a phase."""
    phase_def = PHASE_DEFINITIONS[phase_num]
    required = phase_def["artifacts"]

    present = []
    missing = []

    for artifact in required:
        artifact_path = run_dir / artifact
        if artifact_path.exists():
            # Check if file has content
            if artifact_path.stat().st_size > 0:
                present.append(artifact)
            else:
                missing.append(f"{artifact} (empty)")
        else:
            missing.append(artifact)

    return present, missing


def calculate_phase_duration(run_dir: Path, phase_num: str) -> int | None:
    """Calculate phase duration from file timestamps."""
    # This is a simplified version - in reality you'd track start/end times
    # For now, we'll check if artifacts exist and estimate based on file mtimes

    phase_def = PHASE_DEFINITIONS[phase_num]
    artifacts = phase_def["artifacts"]

    if not artifacts:
        return None

    mtimes = []
    for artifact in artifacts:
        artifact_path = run_dir / artifact
        if artifact_path.exists():
            mtimes.append(artifact_path.stat().st_mtime)

    if len(mtimes) >= 2:
        # Rough estimate: time between first and last artifact
        return int(max(mtimes) - min(mtimes))
    elif mtimes:
        return phase_def["planned_minutes"]  # Assume planned time

    return None


def detect_issues(run_dir: Path, phase: PhaseStatus) -> list[str]:
    """Detect issues in a phase."""
    issues = []

    # Check for missing critical artifacts
    critical_artifacts = {
        "3": ["logs/typecheck.log", "logs/lint.log", "logs/build.log"],
        "4": ["logs/test-results.json", "logs/after-console.json"],
    }

    if phase.number in critical_artifacts:
        for artifact in critical_artifacts[phase.number]:
            if artifact not in phase.artifacts_present:
                issues.append(f"Missing critical artifact: {artifact}")

    # Check for build failures
    if phase.number == "3":
        typecheck_log = run_dir / "logs/typecheck.log"
        if typecheck_log.exists():
            content = read_file(typecheck_log) or ""
            if "error" in content.lower() or "failed" in content.lower():
                issues.append("Type check log contains errors")

    # Check for test failures
    if phase.number == "4":
        test_results = run_dir / "logs/test-results.json"
        if test_results.exists():
            try:
                data = json.loads(read_file(test_results) or "{}")
                if isinstance(data, dict):
                    if data.get("status") == "failed":
                        issues.append("Tests failed")
                    if data.get("stats", {}).get("failed", 0) > 0:
                        issues.append(f"Tests failed: {data['stats']['failed']} failed")
            except (json.JSONDecodeError, KeyError):
                pass

    return issues


def analyze_cycle(run_dir: Path) -> CycleStatus:
    """Analyze a UI cycle run and return its status."""
    # Parse metadata
    metadata = parse_cycle_json(run_dir)
    if not metadata:
        print(f"ERROR: Could not parse cycle.json in {run_dir}", file=sys.stderr)
        sys.exit(1)

    # Parse cycle.md for completion status
    phases_completed = parse_cycle_md(run_dir)

    # Create cycle status
    cycle = CycleStatus(
        cycle_id=metadata.get("cycle_id", run_dir.name),
        run_dir=run_dir,
        started_at=metadata.get("started_at", ""),
        task=metadata.get("task", ""),
        url=metadata.get("url", ""),
        component=metadata.get("component", ""),
    )

    # Analyze each phase
    for phase_num, phase_def in PHASE_DEFINITIONS.items():
        artifacts_present, artifacts_missing = check_artifacts(run_dir, phase_num)
        duration = calculate_phase_duration(run_dir, phase_num)

        phase = PhaseStatus(
            name=phase_def["name"],
            number=int(phase_num),
            planned_minutes=phase_def["planned_minutes"],
            artifacts=phase_def["artifacts"],
            completed=phases_completed.get(phase_num, False),
            artifacts_present=artifacts_present,
            artifacts_missing=artifacts_missing,
            duration_minutes=duration,
        )

        # Detect issues
        phase.issues = detect_issues(run_dir, phase)

        cycle.phases[phase_num] = phase
        cycle.total_artifacts_present += len(artifacts_present)
        cycle.total_artifacts_missing += len(artifacts_missing)

    # Determine overall status
    if all(p.completed for p in cycle.phases.values()):
        cycle.overall_status = "completed"
    elif any(p.completed for p in cycle.phases.values()):
        cycle.overall_status = "in_progress"
    else:
        cycle.overall_status = "not_started"

    # Check for issues
    if any(p.issues for p in cycle.phases.values()):
        if cycle.overall_status == "completed":
            cycle.overall_status = "completed_with_issues"

    return cycle


def print_status(cycle: CycleStatus, verbose: bool = False):
    """Print cycle status to stdout."""
    print(f"UI Cycle Status: {cycle.cycle_id}")
    print("=" * 60)
    print(f"Task: {cycle.task}")
    print(f"Component: {cycle.component}")
    print(f"URL: {cycle.url}")
    print(f"Started: {cycle.started_at}")
    print(f"Status: {cycle.overall_status}")
    print()

    # Phase summary
    print("Phases:")
    for phase_num in sorted(cycle.phases.keys()):
        phase = cycle.phases[phase_num]
        status_icon = "✅" if phase.completed else "⏳" if phase.artifacts_present else "❌"

        print(f"  Phase {phase_num} ({phase.name}): {status_icon}")

        if verbose:
            if phase.artifacts_present:
                print(f"    Artifacts present: {len(phase.artifacts_present)}/{len(phase.artifacts)}")
            if phase.artifacts_missing:
                print(f"    Missing: {len(phase.artifacts_missing)} artifacts")
            if phase.duration_minutes:
                print(f"    Duration: {phase.duration_minutes} min (planned: {phase.planned_minutes} min)")
            if phase.issues:
                print(f"    Issues: {len(phase.issues)}")
                for issue in phase.issues:
                    print(f"      - {issue}")

    print()
    print(f"Artifacts: {cycle.total_artifacts_present} present, {cycle.total_artifacts_missing} missing")

    # Overall assessment
    print()
    if cycle.overall_status == "completed":
        print("✅ Cycle completed successfully")
    elif cycle.overall_status == "completed_with_issues":
        print("⚠️  Cycle completed with issues")
    elif cycle.overall_status == "in_progress":
        print("🔄 Cycle in progress")
    else:
        print("❌ Cycle not started")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor UI Adaptive Development Cycle runs"
    )
    parser.add_argument(
        "--run",
        required=True,
        help="Path to UI cycle run directory"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed phase information"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output status as JSON"
    )

    args = parser.parse_args()

    # Resolve run path
    run_path = Path(args.run)
    if not run_path.is_absolute():
        run_path = Path.cwd() / run_path

    if not run_path.exists():
        print(f"ERROR: Run directory not found: {run_path}", file=sys.stderr)
        sys.exit(1)

    # Analyze cycle
    cycle = analyze_cycle(run_path)

    # Output
    if args.json:
        output = {
            "cycle_id": cycle.cycle_id,
            "task": cycle.task,
            "component": cycle.component,
            "url": cycle.url,
            "started_at": cycle.started_at,
            "overall_status": cycle.overall_status,
            "total_artifacts_present": cycle.total_artifacts_present,
            "total_artifacts_missing": cycle.total_artifacts_missing,
            "phases": {
                phase_num: {
                    "name": phase.name,
                    "completed": phase.completed,
                    "artifacts_present": len(phase.artifacts_present),
                    "artifacts_missing": len(phase.artifacts_missing),
                    "issues": phase.issues,
                }
                for phase_num, phase in cycle.phases.items()
            }
        }
        print(json.dumps(output, indent=2))
    else:
        print_status(cycle, verbose=args.verbose)

    # Exit code based on status
    if cycle.overall_status in ["completed_with_issues"]:
        sys.exit(1)
    elif cycle.overall_status == "not_started":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
