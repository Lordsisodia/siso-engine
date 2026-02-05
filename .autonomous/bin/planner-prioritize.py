#!/usr/bin/env python3
"""
Planner Agent - Prioritize Improvement Opportunities

Reads scout reports and creates prioritized improvement tasks.
Part of the Agent Improvement Loop: Scout → Planner → Executor → Verifier

Usage:
    planner-prioritize.py --scout-report FILE [--output-dir DIR]
"""

import argparse
import json
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field

# Configuration
PROJECT_DIR = Path.home() / ".blackbox5" / "5-project-memory" / "blackbox5"
ENGINE_DIR = Path.home() / ".blackbox5" / "2-engine"
DEFAULT_SCOUT_REPORT = PROJECT_DIR / ".autonomous" / "analysis" / "scout-reports" / "scout-report-intelligent-20260205-aggregated.yaml"
OUTPUT_DIR = PROJECT_DIR / "tasks" / "active"


@dataclass
class ImprovementTask:
    """Represents a prioritized improvement task."""
    id: str
    title: str
    description: str
    category: str
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    effort_minutes: int
    source_opportunity_id: str
    scout_score: float
    action: str
    files_to_modify: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class PlannerAgent:
    """
    Planner Agent that prioritizes improvement opportunities
    and creates actionable tasks.
    """

    # Priority thresholds based on total score
    PRIORITY_THRESHOLDS = {
        "CRITICAL": 15.0,  # Score >= 15
        "HIGH": 12.0,      # Score >= 12
        "MEDIUM": 8.0,     # Score >= 8
        "LOW": 0.0         # Score < 8
    }

    # Effort mapping (minutes)
    EFFORT_MAPPING = {
        1: 15,   # 15 minutes
        2: 30,   # 30 minutes
        3: 60,   # 1 hour
        4: 120,  # 2 hours
        5: 240   # 4+ hours
    }

    def __init__(self, scout_report_path: Path, output_dir: Path):
        self.scout_report_path = scout_report_path
        self.output_dir = output_dir
        self.opportunities: List[Dict[str, Any]] = []
        self.patterns: List[Dict[str, Any]] = []
        self.tasks: List[ImprovementTask] = []

    def load_scout_report(self) -> bool:
        """Load and parse the scout report."""
        if not self.scout_report_path.exists():
            print(f"❌ Scout report not found: {self.scout_report_path}")
            return False

        try:
            with open(self.scout_report_path, 'r') as f:
                if self.scout_report_path.suffix == '.json':
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)

            # Handle different report formats
            if 'scout_report' in data:
                report = data['scout_report']
            elif 'summary' in data:
                report = data
            else:
                print("❌ Unknown report format")
                return False

            self.opportunities = report.get('opportunities', report.get('all_opportunities', []))
            self.patterns = report.get('patterns', [])

            print(f"✅ Loaded {len(self.opportunities)} opportunities from scout report")
            print(f"✅ Loaded {len(self.patterns)} patterns from scout report")
            return True

        except Exception as e:
            print(f"❌ Error loading scout report: {e}")
            return False

    def calculate_priority(self, score: float) -> str:
        """Calculate priority based on score."""
        for priority, threshold in sorted(self.PRIORITY_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if score >= threshold:
                return priority
        return "LOW"

    def identify_dependencies(self, opportunity: Dict[str, Any]) -> List[str]:
        """Identify task dependencies based on category and description."""
        deps = []
        category = opportunity.get('category', '')
        title = opportunity.get('title', '')
        description = opportunity.get('description', '')

        # Critical skill system issues must be fixed first
        if 'skill' in category.lower() and 'invocation' in title.lower():
            deps.append("TASK-SKILL-001")  # Fix skill invocation

        # Infrastructure before process
        if category == 'process' and 'metric' in description.lower():
            deps.append("TASK-INFRA-001")  # Fix metrics first

        # Architecture before documentation
        if category == 'documentation' and 'architecture' in description.lower():
            deps.append("TASK-ARCH-001")  # Fix architecture first

        return deps

    def create_task(self, opportunity: Dict[str, Any], rank: int) -> ImprovementTask:
        """Create an improvement task from an opportunity."""
        opp_id = opportunity.get('id', f"opp-{rank:03d}")
        score = opportunity.get('total_score', 0)
        impact = opportunity.get('impact_score', 3)
        effort = opportunity.get('effort_score', 3)
        category = opportunity.get('category', 'general')

        # Generate task ID
        category_prefix = category[:4].upper()
        task_id = f"TASK-{category_prefix}-{rank:03d}"

        # Calculate priority and effort
        priority = self.calculate_priority(score)
        effort_minutes = self.EFFORT_MAPPING.get(effort, 60)

        # Identify dependencies
        dependencies = self.identify_dependencies(opportunity)

        return ImprovementTask(
            id=task_id,
            title=opportunity.get('title', 'Untitled Opportunity'),
            description=opportunity.get('description', ''),
            category=category,
            priority=priority,
            effort_minutes=effort_minutes,
            source_opportunity_id=opp_id,
            scout_score=score,
            action=opportunity.get('suggested_action', ''),
            files_to_modify=opportunity.get('files_to_check', []),
            dependencies=dependencies
        )

    def prioritize_opportunities(self) -> List[ImprovementTask]:
        """Prioritize all opportunities and create tasks."""
        print("\n📊 Prioritizing opportunities...")

        # Sort by score (highest first)
        sorted_opps = sorted(
            self.opportunities,
            key=lambda x: x.get('total_score', 0),
            reverse=True
        )

        tasks = []
        for rank, opp in enumerate(sorted_opps, 1):
            task = self.create_task(opp, rank)
            tasks.append(task)

        self.tasks = tasks
        return tasks

    def generate_task_markdown(self, task: ImprovementTask) -> str:
        """Generate markdown content for a task file."""
        lines = [
            f"# {task.id}: {task.title}",
            "",
            f"**Status:** {task.status}",
            f"**Priority:** {task.priority}",
            f"**Category:** {task.category}",
            f"**Estimated Effort:** {task.effort_minutes} minutes",
            f"**Created:** {task.created_at}",
            f"**Source:** Scout opportunity {task.source_opportunity_id} (Score: {task.scout_score:.1f})",
            "",
            "---",
            "",
            "## Objective",
            "",
            task.description,
            "",
            "---",
            "",
            "## Success Criteria",
            "",
            "- [ ] Understand the issue completely",
            "- [ ] Implement the suggested action",
            "- [ ] Validate the fix works",
            "- [ ] Document changes in LEARNINGS.md",
            "",
            "---",
            "",
            "## Context",
            "",
            f"**Suggested Action:** {task.action}",
            "",
            "**Files to Check/Modify:**",
        ]

        for file_path in task.files_to_modify:
            lines.append(f"- `{file_path}`")

        if task.dependencies:
            lines.extend([
                "",
                "**Dependencies:**",
            ])
            for dep in task.dependencies:
                lines.append(f"- {dep}")

        lines.extend([
            "",
            "---",
            "",
            "## Rollback Strategy",
            "",
            "If changes cause issues:",
            "1. Revert to previous state using git",
            "2. Document what went wrong",
            "3. Update this task with learnings",
            "",
            "---",
            "",
            "## Notes",
            "",
            "_Add notes as you work on this task_",
            "",
        ])

        return "\n".join(lines)

    def save_tasks(self) -> List[Path]:
        """Save all tasks to individual files."""
        saved_files = []

        # Create output directory if needed
        self.output_dir.mkdir(parents=True, exist_ok=True)

        for task in self.tasks:
            # Create task directory
            task_dir = self.output_dir / task.id
            task_dir.mkdir(exist_ok=True)

            # Save task file
            task_file = task_dir / "task.md"
            content = self.generate_task_markdown(task)

            with open(task_file, 'w') as f:
                f.write(content)

            saved_files.append(task_file)

        print(f"\n✅ Saved {len(saved_files)} tasks to {self.output_dir}")
        return saved_files

    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate a summary report of prioritized tasks."""
        # Count by priority
        by_priority = {}
        by_category = {}
        total_effort = 0

        for task in self.tasks:
            by_priority[task.priority] = by_priority.get(task.priority, 0) + 1
            by_category[task.category] = by_category.get(task.category, 0) + 1
            total_effort += task.effort_minutes

        # Get top 10 critical/high priority tasks
        top_tasks = [
            {
                "id": t.id,
                "title": t.title,
                "priority": t.priority,
                "score": t.scout_score,
                "effort_minutes": t.effort_minutes
            }
            for t in self.tasks[:10]
        ]

        report = {
            "planner_report": {
                "id": f"PLAN-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "source_scout_report": str(self.scout_report_path),
                "summary": {
                    "total_tasks_created": len(self.tasks),
                    "by_priority": by_priority,
                    "by_category": by_category,
                    "total_estimated_effort_minutes": total_effort,
                    "total_estimated_effort_hours": round(total_effort / 60, 1)
                },
                "top_10_tasks": top_tasks,
                "quick_wins": [
                    {"id": t.id, "title": t.title, "effort": t.effort_minutes}
                    for t in self.tasks
                    if t.effort_minutes <= 30 and t.priority in ["CRITICAL", "HIGH"]
                ][:5]
            }
        }

        return report

    def save_summary_report(self, report: Dict[str, Any]) -> Path:
        """Save the summary report."""
        report_dir = PROJECT_DIR / ".autonomous" / "analysis" / "planner-reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        report_id = report["planner_report"]["id"]

        # Save YAML
        yaml_file = report_dir / f"{report_id}.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)

        # Save JSON
        json_file = report_dir / f"{report_id}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"✅ Summary report saved:")
        print(f"   YAML: {yaml_file}")
        print(f"   JSON: {json_file}")

        return yaml_file

    def print_summary(self):
        """Print a human-readable summary."""
        print("\n" + "="*60)
        print("PLANNER AGENT - TASK PRIORITIZATION COMPLETE")
        print("="*60)

        # Count by priority
        critical = len([t for t in self.tasks if t.priority == "CRITICAL"])
        high = len([t for t in self.tasks if t.priority == "HIGH"])
        medium = len([t for t in self.tasks if t.priority == "MEDIUM"])
        low = len([t for t in self.tasks if t.priority == "LOW"])

        print(f"\n📊 Task Summary:")
        print(f"   Total tasks created: {len(self.tasks)}")
        print(f"   CRITICAL: {critical}")
        print(f"   HIGH: {high}")
        print(f"   MEDIUM: {medium}")
        print(f"   LOW: {low}")

        print(f"\n🏆 Top 5 Priority Tasks:")
        for i, task in enumerate(self.tasks[:5], 1):
            print(f"\n   {i}. {task.id}: {task.title}")
            print(f"      Priority: {task.priority} | Score: {task.scout_score:.1f} | Effort: {task.effort_minutes}min")
            print(f"      Action: {task.action[:60]}...")

        quick_wins = [t for t in self.tasks if t.effort_minutes <= 30 and t.priority in ["CRITICAL", "HIGH"]]
        if quick_wins:
            print(f"\n⚡ Quick Wins (<=30 min, HIGH/CRITICAL):")
            for i, task in enumerate(quick_wins[:5], 1):
                print(f"   {i}. {task.id}: {task.title} ({task.effort_minutes} min)")

        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Planner Agent - Prioritize improvement opportunities"
    )
    parser.add_argument(
        "--scout-report",
        type=Path,
        default=DEFAULT_SCOUT_REPORT,
        help="Path to scout report file"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory for task files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print summary without creating files"
    )

    args = parser.parse_args()

    # Initialize planner
    planner = PlannerAgent(args.scout_report, args.output_dir)

    # Load scout report
    if not planner.load_scout_report():
        return 1

    # Prioritize opportunities
    planner.prioritize_opportunities()

    # Generate summary report
    report = planner.generate_summary_report()

    if args.dry_run:
        print("\n🔍 DRY RUN - No files created")
        planner.print_summary()
    else:
        # Save tasks
        planner.save_tasks()

        # Save summary report
        planner.save_summary_report(report)

        # Print summary
        planner.print_summary()

    return 0


if __name__ == "__main__":
    sys.exit(main())
