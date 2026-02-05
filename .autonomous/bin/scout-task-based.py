#!/usr/bin/env python3
"""
Task-Based Intelligent Scout

Uses Claude Code's Task tool to spawn subagents for analysis.
This is the proper way to spawn Claude instances within Claude Code.

Usage:
    scout-task-based.py [--output-dir DIR]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

# Configuration
PROJECT_DIR = Path.home() / ".blackbox5" / "5-project-memory" / "blackbox5"
ENGINE_DIR = Path.home() / ".blackbox5" / "2-engine"
OUTPUT_DIR = PROJECT_DIR / ".autonomous" / "analysis" / "scout-reports"


def create_task_prompt(analyzer_type: str) -> str:
    """Create the prompt for a specific analyzer type."""

    prompts = {
        "skill": f"""You are a Skill Effectiveness Analyzer.

Analyze the skill system in {PROJECT_DIR} to find improvement opportunities.

READ THESE FILES:
1. operations/skill-metrics.yaml - Check for null values, low scores
2. operations/skill-usage.yaml - Check trigger patterns
3. operations/skill-selection.yaml - Check selection logic

FIND:
- Skills with no metrics (all null values)
- Skills never triggered (usage_count = 0)
- Skills with low effectiveness (< 70%)
- Poor trigger accuracy (< 80%)
- Gaps in skill coverage

For each issue, provide:
- Title: Clear, actionable title
- Description: What the issue is and why it matters
- Evidence: Specific data from files
- Impact: 1-5 (5 = affects all tasks)
- Effort: 1-5 (5 = >2 hours)
- Frequency: 1-3 (3 = daily occurrence)
- Action: Concrete next step
- Files: List of relevant files

OUTPUT FORMAT - Return valid JSON:
{{
  "opportunities": [
    {{
      "id": "skill-001",
      "title": "...",
      "description": "...",
      "category": "skills",
      "evidence": "...",
      "impact_score": 4,
      "effort_score": 3,
      "frequency_score": 3,
      "files_to_check": ["operations/skill-metrics.yaml"],
      "suggested_action": "..."
    }}
  ],
  "patterns": [],
  "summary": "Found X issues..."
}}""",

        "process": f"""You are a Process Friction Analyzer.

Analyze recent runs in {PROJECT_DIR} to identify friction points.

READ THESE FILES:
1. .autonomous/runs/*/THOUGHTS.md (last 5 runs)
2. .autonomous/runs/*/LEARNINGS.md (last 5 runs)
3. .autonomous/agents/communications/events.yaml

FIND:
- Tasks taking >2x estimated time
- Recurring challenges or blockers
- "Harder than expected" patterns
- Duplicate work
- Manual steps that could be automated

For each issue, provide:
- Title: Clear, actionable title
- Description: What the issue is
- Evidence: Specific run IDs, quotes
- Impact: 1-5
- Effort: 1-5
- Frequency: 1-3
- Action: Concrete fix
- Files: Relevant files

OUTPUT FORMAT - Return valid JSON:
{{
  "opportunities": [...],
  "patterns": [...],
  "summary": "..."
}}""",

        "documentation": f"""You are a Documentation Drift Analyzer.

Analyze documentation in {PROJECT_DIR} for drift and gaps.

READ THESE FILES:
1. .docs/**/*.md
2. README.md
3. ARCHITECTURE.md
4. operations/*.yaml

FIND:
- Docs describing non-existent features
- Outdated architecture info
- Missing documentation
- Inconsistent naming
- Stale README

For each issue, provide:
- Title: Clear, actionable title
- Description: What the issue is
- Evidence: Specific files, sections
- Impact: 1-5
- Effort: 1-5
- Frequency: 1-3
- Action: Concrete fix
- Files: Relevant files

OUTPUT FORMAT - Return valid JSON:
{{
  "opportunities": [...],
  "patterns": [...],
  "summary": "..."
}}""",

        "architecture": f"""You are an Architecture Improvement Analyzer.

Analyze the codebase in {PROJECT_DIR} and {ENGINE_DIR} for architectural improvements.

READ THESE FILES:
1. routes.yaml
2. ARCHITECTURE.md
3. 2-engine/.autonomous/**/*.md
4. Key scripts in bin/

FIND:
- Missing abstractions
- Tight coupling
- Automation opportunities
- Config that should be code
- Scalability issues

For each issue, provide:
- Title: Clear, actionable title
- Description: What the issue is
- Evidence: Specific code locations
- Impact: 1-5
- Effort: 1-5
- Frequency: 1-3
- Action: Concrete fix
- Files: Relevant files

OUTPUT FORMAT - Return valid JSON:
{{
  "opportunities": [...],
  "patterns": [...],
  "summary": "..."
}}""",

        "metrics": f"""You are a Metrics & Quality Analyzer.

Analyze metrics tracking in {PROJECT_DIR} for gaps.

READ THESE FILES:
1. operations/improvement-backlog.yaml
2. operations/improvement-metrics.yaml
3. operations/improvement-pipeline.yaml
4. STATE.yaml

FIND:
- Untracked metrics
- Stale improvements
- Missing validation
- Measurement gaps
- Automation opportunities

For each issue, provide:
- Title: Clear, actionable title
- Description: What the issue is
- Evidence: Specific data
- Impact: 1-5
- Effort: 1-5
- Frequency: 1-3
- Action: Concrete fix
- Files: Relevant files

OUTPUT FORMAT - Return valid JSON:
{{
  "opportunities": [...],
  "patterns": [...],
  "summary": "..."
}}"""
    }

    return prompts.get(analyzer_type, prompts["skill"])


def run_analyzer_with_task_tool(analyzer_type: str) -> Dict[str, Any]:
    """
    Run an analyzer using the Task tool.

    This function prints the Task tool call that should be made.
    The actual execution happens through Claude Code's Task tool.
    """
    prompt = create_task_prompt(analyzer_type)

    analyzer_names = {
        "skill": "Skill Effectiveness Analyzer",
        "process": "Process Friction Analyzer",
        "documentation": "Documentation Drift Analyzer",
        "architecture": "Architecture Improvement Analyzer",
        "metrics": "Metrics & Quality Analyzer"
    }

    print(f"\n{'='*60}")
    print(f"TASK TOOL CALL FOR: {analyzer_names[analyzer_type]}")
    print(f"{'='*60}")
    print(f"""
Use the Task tool with these parameters:

subagent_type: "general-purpose"
model: "sonnet"
prompt: """{prompt}"""
run_in_background: true
""")

    # Since we can't actually call the Task tool from within a script,
    # we return a placeholder that indicates this needs to be run manually
    return {
        "analyzer": analyzer_type,
        "name": analyzer_names[analyzer_type],
        "status": "PENDING_TASK_EXECUTION",
        "prompt": prompt,
        "opportunities": [],
        "patterns": [],
        "summary": "Waiting for Task tool execution"
    }


def run_all_analyzers() -> List[Dict[str, Any]]:
    """Run all 5 analyzers and collect results."""
    analyzer_types = ["skill", "process", "documentation", "architecture", "metrics"]

    print("\n" + "="*60)
    print("INTELLIGENT SCOUT - TASK-BASED MODE")
    print("="*60)
    print("\nThis scout requires manual execution of Task tool calls.")
    print("Copy each Task tool call below and execute it in Claude Code.")
    print("Then collect the results and run the aggregation.\n")

    results = []
    for analyzer_type in analyzer_types:
        result = run_analyzer_with_task_tool(analyzer_type)
        results.append(result)

    return results


def aggregate_results(results: List[Dict[str, Any]], report_id: str) -> Dict[str, Any]:
    """Aggregate results from all analyzers into a final report."""

    all_opportunities = []
    all_patterns = []
    analyzer_summaries = []

    for result in results:
        analyzer_id = result["analyzer"]
        analyzer_name = result["name"]
        opportunities = result.get("opportunities", [])
        patterns = result.get("patterns", [])
        summary = result.get("summary", "")

        # Calculate scores
        for opp in opportunities:
            impact = opp.get("impact_score", 3)
            effort = opp.get("effort_score", 3)
            frequency = opp.get("frequency_score", 2)
            opp["total_score"] = (impact * 3) + (frequency * 2) - (effort * 1.5)

        all_opportunities.extend(opportunities)
        all_patterns.extend(patterns)
        analyzer_summaries.append({
            "id": analyzer_id,
            "name": analyzer_name,
            "opportunities_found": len(opportunities),
            "patterns_found": len(patterns),
            "summary": summary
        })

    # Sort by total score
    all_opportunities.sort(key=lambda x: x.get("total_score", 0), reverse=True)

    # Identify quick wins
    quick_wins = [
        opp for opp in all_opportunities
        if opp.get("effort_score", 5) <= 2 and opp.get("impact_score", 1) >= 3
    ]

    # Count by category
    categories = {}
    for opp in all_opportunities:
        cat = opp.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "scout_report": {
            "id": report_id,
            "timestamp": datetime.now().isoformat(),
            "scout_version": "1.0.0-task-based",
            "summary": {
                "total_opportunities": len(all_opportunities),
                "high_impact": len([o for o in all_opportunities if o.get("impact_score", 0) >= 4]),
                "quick_wins": len(quick_wins),
                "patterns_found": len(all_patterns),
                "categories": categories,
                "analyzers": analyzer_summaries
            },
            "opportunities": all_opportunities,
            "patterns": all_patterns,
            "quick_wins": quick_wins[:5],
            "recommendations": [
                {
                    "priority": i + 1,
                    "opportunity_id": opp["id"],
                    "title": opp["title"],
                    "total_score": opp["total_score"],
                    "rationale": f"Score: {opp['total_score']:.1f} | Impact: {opp['impact_score']}/5 | Effort: {opp['effort_score']}/5"
                }
                for i, opp in enumerate(all_opportunities[:10])
            ]
        }
    }


def save_report(report: Dict[str, Any], output_dir: Path):
    """Save the report to JSON and YAML files."""
    import yaml

    output_dir.mkdir(parents=True, exist_ok=True)
    report_id = report["scout_report"]["id"]

    # Save JSON
    json_file = output_dir / f"scout-report-task-{report_id}.json"
    with open(json_file, 'w') as f:
        json.dump(report, f, indent=2)

    # Save YAML
    yaml_file = output_dir / f"scout-report-task-{report_id}.yaml"
    with open(yaml_file, 'w') as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False)

    return json_file, yaml_file


def main():
    parser = argparse.ArgumentParser(
        description="Task-Based Intelligent Scout"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory for reports"
    )
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Skip task generation, only aggregate existing results"
    )

    args = parser.parse_args()

    report_id = datetime.now().strftime("%Y%m%d-%H%M%S")

    if not args.aggregate_only:
        # Phase 1: Generate Task tool calls
        results = run_all_analyzers()

        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print("""
1. Copy each Task tool call from above
2. Execute them in Claude Code (they'll run in parallel)
3. Collect the JSON outputs from each Task
4. Save them to: {output_dir}/raw-results/
5. Run: scout-task-based.py --aggregate-only

Or manually aggregate the results and create the report.
""")

        # Save the task definitions for reference
        tasks_file = args.output_dir / f"scout-tasks-{report_id}.json"
        args.output_dir.mkdir(parents=True, exist_ok=True)
        with open(tasks_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Task definitions saved to: {tasks_file}")

    else:
        # Phase 2: Aggregate existing results
        print("Aggregating results from raw-results/...")
        # This would read files from raw-results/ directory
        # For now, just create an empty report template
        report = aggregate_results([], report_id)
        json_file, yaml_file = save_report(report, args.output_dir)
        print(f"Report saved to: {json_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
