#!/usr/bin/env python3
"""
Improvement Scout Analysis Script

Scans BlackBox5 for improvement opportunities and generates analysis reports.

Usage:
    scout-analyze.py [--project-dir DIR] [--output FILE]

Options:
    --project-dir   Project memory directory (default: 5-project-memory/blackbox5)
    --output        Output file path (default: auto-generated)
"""

import argparse
import os
import sys
import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import Counter


@dataclass
class Opportunity:
    id: str
    category: str
    title: str
    description: str
    evidence: str
    impact_score: int
    effort_score: int
    frequency_score: int
    suggested_action: str
    files_to_check: List[str]

    @property
    def total_score(self) -> float:
        """Calculate total score using formula: (impact × 3) + (frequency × 2) - (effort × 1.5)"""
        return (self.impact_score * 3) + (self.frequency_score * 2) - (self.effort_score * 1.5)


@dataclass
class Pattern:
    name: str
    description: str
    occurrences: int
    related_opportunities: List[str]


@dataclass
class QuickWin:
    id: str
    title: str
    effort_minutes: int
    impact: str
    action: str


class ImprovementScout:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.opportunities: List[Opportunity] = []
        self.patterns: List[Pattern] = []
        self.quick_wins: List[QuickWin] = []
        self.seq_counter = 0

    def _next_id(self, prefix: str = "OPP") -> str:
        self.seq_counter += 1
        return f"{prefix}-{self.seq_counter:03d}"

    def analyze_skill_metrics(self) -> None:
        """Analyze skill effectiveness from metrics file."""
        metrics_file = self.project_dir / "operations" / "skill-metrics.yaml"

        if not metrics_file.exists():
            self.opportunities.append(Opportunity(
                id=self._next_id(),
                category="infrastructure",
                title="Skill metrics file not found",
                description="Cannot analyze skill effectiveness without metrics data",
                evidence=f"File not found: {metrics_file}",
                impact_score=3,
                effort_score=2,
                frequency_score=2,
                suggested_action="Run skill metrics collection script",
                files_to_check=["operations/skill-metrics.yaml"]
            ))
            return

        try:
            with open(metrics_file) as f:
                metrics = yaml.safe_load(f)

            if not metrics or 'skills' not in metrics:
                return

            skills = metrics['skills']
            # Handle both list and dict formats
            if isinstance(skills, list):
                skills_iter = [(s.get('name', f'skill-{i}'), s) for i, s in enumerate(skills)]
            elif isinstance(skills, dict):
                skills_iter = skills.items()
            else:
                return

            null_skills_count = 0

            for skill_name, skill_data in skills_iter:
                if not isinstance(skill_data, dict):
                    continue

                effectiveness = skill_data.get('effectiveness_score')
                success_rate = skill_data.get('success_rate')
                usage_count = skill_data.get('usage_count', 0)
                trigger_accuracy = skill_data.get('trigger_accuracy')

                # Count skills with all null metrics (need data collection)
                if effectiveness is None and success_rate is None and usage_count == 0:
                    null_skills_count += 1
                    continue

                # Check for ineffective skills
                if effectiveness is not None and effectiveness < 70:
                    self.opportunities.append(Opportunity(
                        id=self._next_id(),
                        category="skills",
                        title=f"Skill '{skill_name}' has low effectiveness ({effectiveness}%)",
                        description=f"Skill effectiveness is {effectiveness}%, below 70% threshold",
                        evidence=f"skill-metrics.yaml: effectiveness_score={effectiveness}",
                        impact_score=4 if effectiveness < 50 else 3,
                        effort_score=3,
                        frequency_score=2,
                        suggested_action=f"Review {skill_name} skill definition and triggers",
                        files_to_check=[
                            f".claude/skills/{skill_name}/SKILL.md",
                            "operations/skill-usage.yaml"
                        ]
                    ))

                # Check for unused skills
                if usage_count == 0:
                    self.opportunities.append(Opportunity(
                        id=self._next_id(),
                        category="skills",
                        title=f"Skill '{skill_name}' has never been used",
                        description="Skill has zero usage despite being defined",
                        evidence=f"skill-metrics.yaml: usage_count=0",
                        impact_score=2,
                        effort_score=2,
                        frequency_score=1,
                        suggested_action=f"Either promote {skill_name} usage or deprecate it",
                        files_to_check=[
                            f".claude/skills/{skill_name}/SKILL.md",
                            "operations/skill-selection.yaml"
                        ]
                    ))

                # Check for poor trigger accuracy
                if trigger_accuracy is not None and trigger_accuracy < 80:
                    self.opportunities.append(Opportunity(
                        id=self._next_id(),
                        category="skills",
                        title=f"Skill '{skill_name}' has poor trigger accuracy ({trigger_accuracy}%)",
                        description=f"Skill triggers incorrectly {100-trigger_accuracy}% of the time",
                        evidence=f"skill-metrics.yaml: trigger_accuracy={trigger_accuracy}",
                        impact_score=3,
                        effort_score=2,
                        frequency_score=3,
                        suggested_action=f"Refine trigger conditions for {skill_name}",
                        files_to_check=[
                            f".claude/skills/{skill_name}/SKILL.md",
                            "operations/skill-usage.yaml"
                        ]
                    ))

            # If many skills have null metrics, that's an opportunity
            if null_skills_count >= 10:
                self.opportunities.append(Opportunity(
                    id=self._next_id(),
                    category="infrastructure",
                    title=f"{null_skills_count} skills have no effectiveness data",
                    description="Skill metrics are not being populated automatically",
                    evidence=f"skill-metrics.yaml shows {null_skills_count} skills with null values",
                    impact_score=4,
                    effort_score=3,
                    frequency_score=3,
                    suggested_action="Implement automatic skill metrics collection from task outcomes",
                    files_to_check=[
                        "operations/skill-metrics.yaml",
                        "bin/collect-skill-metrics.py"
                    ]
                ))

        except Exception as e:
            self.opportunities.append(Opportunity(
                id=self._next_id(),
                category="infrastructure",
                title="Failed to parse skill metrics",
                description=f"Error reading skill metrics: {str(e)}",
                evidence=str(e),
                impact_score=2,
                effort_score=2,
                frequency_score=1,
                suggested_action="Fix skill metrics YAML format",
                files_to_check=["operations/skill-metrics.yaml"]
            ))

    def analyze_recent_learnings(self) -> None:
        """Analyze recent run learnings for patterns."""
        runs_dir = self.project_dir / ".autonomous" / "runs"

        if not runs_dir.exists():
            return

        # Get recent run folders (last 5)
        run_folders = sorted(runs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:5]

        all_learnings = []
        friction_points = []

        for run_folder in run_folders:
            if not run_folder.is_dir():
                continue

            learnings_file = run_folder / "LEARNINGS.md"
            thoughts_file = run_folder / "THOUGHTS.md"

            # Parse LEARNINGS.md
            if learnings_file.exists():
                try:
                    with open(learnings_file) as f:
                        content = f.read()
                        all_learnings.append({
                            'run': run_folder.name,
                            'content': content
                        })

                        # Look for challenges
                        if 'challenge' in content.lower() or 'harder than expected' in content.lower():
                            friction_points.append(run_folder.name)

                except Exception:
                    pass

            # Parse THOUGHTS.md for challenges
            if thoughts_file.exists():
                try:
                    with open(thoughts_file) as f:
                        content = f.read()
                        if 'challenge' in content.lower():
                            friction_points.append(run_folder.name)
                except Exception:
                    pass

        # If multiple runs mention friction, create opportunity
        if len(friction_points) >= 2:
            self.opportunities.append(Opportunity(
                id=self._next_id(),
                category="process",
                title=f"Recurring friction in {len(friction_points)} recent runs",
                description="Multiple recent runs mention challenges or difficulties",
                evidence=f"Friction found in runs: {', '.join(friction_points[:3])}",
                impact_score=4,
                effort_score=3,
                frequency_score=3,
                suggested_action="Review recent THOUGHTS.md files to identify common friction points",
                files_to_check=[f".autonomous/runs/{run}/THOUGHTS.md" for run in friction_points[:3]]
            ))

    def analyze_improvement_backlog(self) -> None:
        """Check improvement backlog for stale items."""
        backlog_file = self.project_dir / "operations" / "improvement-backlog.yaml"

        if not backlog_file.exists():
            return

        try:
            with open(backlog_file) as f:
                backlog = yaml.safe_load(f)

            if not backlog or 'backlog' not in backlog:
                return

            # Check for stale improvements (pending for too long)
            stale_count = 0
            for item in backlog['backlog'].get('medium_priority', []):
                if item.get('status') == 'pending':
                    stale_count += 1

            if stale_count > 5:
                self.opportunities.append(Opportunity(
                    id=self._next_id(),
                    category="process",
                    title=f"{stale_count} medium-priority improvements are pending",
                    description="Improvement backlog has items that haven't been addressed",
                    evidence=f"improvement-backlog.yaml shows {stale_count} pending medium-priority items",
                    impact_score=3,
                    effort_score=4,
                    frequency_score=2,
                    suggested_action="Schedule dedicated improvement sprint to clear backlog",
                    files_to_check=["operations/improvement-backlog.yaml"]
                ))

        except Exception:
            pass

    def analyze_documentation(self) -> None:
        """Check for documentation gaps."""
        docs_dir = self.project_dir / ".docs"

        # Check if .docs exists and has content
        if not docs_dir.exists():
            self.opportunities.append(Opportunity(
                id=self._next_id(),
                category="documentation",
                title="Project documentation directory missing",
                description="No .docs directory found in project",
                evidence="Directory .docs/ does not exist",
                impact_score=3,
                effort_score=2,
                frequency_score=1,
                suggested_action="Create basic project documentation structure",
                files_to_check=[".docs/README.md"]
            ))

    def identify_patterns(self) -> None:
        """Identify patterns across opportunities."""
        # Group by category
        by_category = Counter(opp.category for opp in self.opportunities)

        for category, count in by_category.items():
            if count >= 2:
                related = [opp.id for opp in self.opportunities if opp.category == category]
                self.patterns.append(Pattern(
                    name=f"Multiple {category} issues",
                    description=f"Found {count} opportunities in {category} category",
                    occurrences=count,
                    related_opportunities=related
                ))

    def identify_quick_wins(self) -> None:
        """Identify quick win opportunities (low effort, high impact)."""
        for opp in self.opportunities:
            if opp.effort_score <= 2 and opp.impact_score >= 3:
                self.quick_wins.append(QuickWin(
                    id=opp.id.replace("OPP", "QUICK"),
                    title=opp.title,
                    effort_minutes=opp.effort_score * 15,  # Rough estimate
                    impact="high" if opp.impact_score >= 4 else "medium",
                    action=opp.suggested_action
                ))

    def generate_report(self) -> Dict[str, Any]:
        """Generate the final analysis report."""
        # Sort opportunities by total score
        sorted_opportunities = sorted(
            self.opportunities,
            key=lambda x: x.total_score,
            reverse=True
        )

        return {
            "scout_report": {
                "id": f"SCOUT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "scout_version": "1.0.0",
                "summary": {
                    "total_opportunities": len(self.opportunities),
                    "high_impact": len([o for o in self.opportunities if o.impact_score >= 4]),
                    "quick_wins": len(self.quick_wins),
                    "categories": {
                        "skills": len([o for o in self.opportunities if o.category == "skills"]),
                        "process": len([o for o in self.opportunities if o.category == "process"]),
                        "documentation": len([o for o in self.opportunities if o.category == "documentation"]),
                        "infrastructure": len([o for o in self.opportunities if o.category == "infrastructure"])
                    }
                },
                "opportunities": [
                    {
                        **asdict(opp),
                        "total_score": opp.total_score
                    }
                    for opp in sorted_opportunities
                ],
                "patterns": [asdict(p) for p in self.patterns],
                "quick_wins": [asdict(q) for q in self.quick_wins],
                "recommendations": [
                    {
                        "priority": i + 1,
                        "opportunity_id": opp.id,
                        "rationale": f"High score ({opp.total_score:.1f}) in {opp.category} category"
                    }
                    for i, opp in enumerate(sorted_opportunities[:5])
                ]
            }
        }

    def run(self) -> str:
        """Run full analysis and return report path."""
        print("🔍 Improvement Scout Analysis Starting...")

        print("  📊 Analyzing skill metrics...")
        self.analyze_skill_metrics()

        print("  📚 Analyzing recent learnings...")
        self.analyze_recent_learnings()

        print("  📋 Checking improvement backlog...")
        self.analyze_improvement_backlog()

        print("  📝 Checking documentation...")
        self.analyze_documentation()

        print("  🔗 Identifying patterns...")
        self.identify_patterns()

        print("  ⚡ Identifying quick wins...")
        self.identify_quick_wins()

        # Generate report
        report = self.generate_report()

        # Ensure output directory exists
        output_dir = self.project_dir / ".autonomous" / "analysis" / "scout-reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write report
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        output_file = output_dir / f"scout-report-{timestamp}.yaml"

        with open(output_file, 'w') as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)

        print(f"\n✅ Analysis complete!")
        print(f"   Found {len(self.opportunities)} opportunities")
        print(f"   Identified {len(self.quick_wins)} quick wins")
        print(f"   Report saved to: {output_file}")

        return str(output_file)


def main():
    parser = argparse.ArgumentParser(description="Improvement Scout Analysis")
    parser.add_argument(
        "--project-dir",
        default=os.path.expanduser("~/.blackbox5/5-project-memory/blackbox5"),
        help="Project memory directory"
    )
    parser.add_argument(
        "--output",
        help="Output file path (optional)"
    )

    args = parser.parse_args()

    scout = ImprovementScout(args.project_dir)
    report_path = scout.run()

    # Also print summary to stdout
    print(f"\n📄 Report: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
