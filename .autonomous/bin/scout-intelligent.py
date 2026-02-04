#!/usr/bin/env python3
"""
Intelligent Scout - AI-Powered Improvement Discovery

Spawns Claude Code subagents via the Task tool to intelligently analyze
BlackBox5 for improvement opportunities.

Usage:
    scout-intelligent.py [--parallel] [--output-dir DIR]

This uses the Claude Code Task primitive to spawn specialized analyzer agents.
Each agent runs independently and returns structured findings.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed


# Configuration
PROJECT_DIR = Path.home() / ".blackbox5" / "5-project-memory" / "blackbox5"
ENGINE_DIR = Path.home() / ".blackbox5" / "2-engine"
OUTPUT_DIR = PROJECT_DIR / ".autonomous" / "analysis" / "scout-reports"

# Analyzer definitions - each spawns a Claude Code instance
ANALYZERS = [
    {
        "id": "skill-analyzer",
        "name": "Skill Effectiveness Analyzer",
        "prompt": """You are a Skill Effectiveness Analyzer for BlackBox5.

MISSION: Analyze the skill system to find improvement opportunities.

FILES TO ANALYZE:
- {project_dir}/operations/skill-metrics.yaml
- {project_dir}/operations/skill-usage.yaml
- {project_dir}/operations/skill-selection.yaml

WHAT TO LOOK FOR:
1. Skills with null effectiveness scores (never measured)
2. Skills with low success rates (< 80%)
3. Skills that are never triggered (usage_count = 0)
4. Skills with poor trigger accuracy (< 80%)
5. Gaps in skill coverage (common tasks without skills)

For each issue found, provide:
- Specific skill name
- Current metric values
- Why it's a problem
- Concrete fix recommendation

OUTPUT: Return ONLY a JSON object:
{{
  "opportunities": [
    {{
      "id": "skill-001",
      "title": "Clear title",
      "description": "What the issue is",
      "category": "skills",
      "evidence": "Specific data",
      "impact_score": 1-5,
      "effort_score": 1-5,
      "frequency_score": 1-3,
      "files_to_check": ["path/to/file"],
      "suggested_action": "What to do"
    }}
  ],
  "patterns": [],
  "summary": "Brief summary"
}}"""
    },
    {
        "id": "process-analyzer",
        "name": "Process Friction Analyzer",
        "prompt": """You are a Process Friction Analyzer for BlackBox5.

MISSION: Analyze recent run history to identify friction points.

FILES TO ANALYZE:
- {project_dir}/.autonomous/runs/*/THOUGHTS.md (last 5 runs)
- {project_dir}/.autonomous/runs/*/LEARNINGS.md (last 5 runs)
- {project_dir}/.autonomous/agents/communications/events.yaml

WHAT TO LOOK FOR:
1. Tasks taking much longer than estimated
2. Recurring challenges or blockers
3. "Harder than expected" patterns
4. Duplicate work or repeated research
5. Manual steps that could be automated

For each issue found, provide:
- Specific run/task references
- What went wrong
- How often it happens
- Concrete fix recommendation

OUTPUT: Return ONLY a JSON object:
{{
  "opportunities": [
    {{
      "id": "process-001",
      "title": "Clear title",
      "description": "What the issue is",
      "category": "process",
      "evidence": "Specific runs/files",
      "impact_score": 1-5,
      "effort_score": 1-5,
      "frequency_score": 1-3,
      "files_to_check": ["path/to/file"],
      "suggested_action": "What to do"
    }}
  ],
  "patterns": [],
  "summary": "Brief summary"
}}"""
    },
    {
        "id": "documentation-analyzer",
        "name": "Documentation Drift Analyzer",
        "prompt": """You are a Documentation Drift Analyzer for BlackBox5.

MISSION: Find documentation that doesn't match reality.

FILES TO ANALYZE:
- {project_dir}/.docs/**/*.md
- {project_dir}/operations/*.yaml
- {project_dir}/README.md
- {engine_dir}/.autonomous/prompts/**/*.md

WHAT TO LOOK FOR:
1. Docs describing features that don't exist
2. Outdated architecture diagrams
3. Missing documentation for new features
4. Inconsistent naming across docs
5. README files that are stale

For each issue found, provide:
- Specific file and section
- What the doc says vs reality
- Impact on users
- Concrete fix recommendation

OUTPUT: Return ONLY a JSON object:
{{
  "opportunities": [
    {{
      "id": "docs-001",
      "title": "Clear title",
      "description": "What the issue is",
      "category": "documentation",
      "evidence": "Specific files",
      "impact_score": 1-5,
      "effort_score": 1-5,
      "frequency_score": 1-3,
      "files_to_check": ["path/to/file"],
      "suggested_action": "What to do"
    }}
  ],
  "patterns": [],
  "summary": "Brief summary"
}}"""
    },
    {
        "id": "architecture-analyzer",
        "name": "Architecture Improvement Analyzer",
        "prompt": """You are an Architecture Improvement Analyzer for BlackBox5.

MISSION: Identify architectural improvements and technical debt.

FILES TO ANALYZE:
- {project_dir}/ARCHITECTURE.md
- {project_dir}/routes.yaml
- {engine_dir}/.autonomous/**/*.md
- Key source files in bin/, lib/

WHAT TO LOOK FOR:
1. Missing abstractions or patterns
2. Tight coupling that could be loosened
3. Opportunities for automation
4. Configuration that should be code
5. Scalability bottlenecks

For each issue found, provide:
- Specific location in codebase
- Current state vs ideal state
- Why it matters
- Concrete fix recommendation

OUTPUT: Return ONLY a JSON object:
{{
  "opportunities": [
    {{
      "id": "arch-001",
      "title": "Clear title",
      "description": "What the issue is",
      "category": "architecture",
      "evidence": "Specific code/files",
      "impact_score": 1-5,
      "effort_score": 1-5,
      "frequency_score": 1-3,
      "files_to_check": ["path/to/file"],
      "suggested_action": "What to do"
    }}
  ],
  "patterns": [],
  "summary": "Brief summary"
}}"""
    },
    {
        "id": "metrics-analyzer",
        "name": "Metrics & Quality Analyzer",
        "prompt": """You are a Metrics & Quality Analyzer for BlackBox5.

MISSION: Analyze metrics to find quality and measurement gaps.

FILES TO ANALYZE:
- {project_dir}/operations/improvement-backlog.yaml
- {project_dir}/operations/improvement-metrics.yaml
- {project_dir}/operations/improvement-pipeline.yaml
- {project_dir}/STATE.yaml

WHAT TO LOOK FOR:
1. Metrics that aren't being tracked
2. Stale improvements in backlog
3. Missing validation for past improvements
4. Gaps in measurement coverage
5. Opportunities for automated metrics

For each issue found, provide:
- Specific metric or process
- Current state (missing/stale)
- Why it matters
- Concrete fix recommendation

OUTPUT: Return ONLY a JSON object:
{{
  "opportunities": [
    {{
      "id": "metrics-001",
      "title": "Clear title",
      "description": "What the issue is",
      "category": "infrastructure",
      "evidence": "Specific data",
      "impact_score": 1-5,
      "effort_score": 1-5,
      "frequency_score": 1-3,
      "files_to_check": ["path/to/file"],
      "suggested_action": "What to do"
    }}
  ],
  "patterns": [],
  "summary": "Brief summary"
}}"""
    }
]


@dataclass
class ScoutReport:
    id: str
    timestamp: str
    scout_version: str
    opportunities: List[Dict[str, Any]]
    patterns: List[Dict[str, Any]]
    summary: Dict[str, Any]


def spawn_analyzer(analyzer: Dict[str, str], project_dir: Path, engine_dir: Path) -> Dict[str, Any]:
    """Spawn a Claude Code subagent to run an analyzer."""
    analyzer_id = analyzer["id"]
    analyzer_name = analyzer["name"]

    print(f"🔍 Spawning {analyzer_name}...")

    # Format the prompt with actual paths
    prompt = analyzer["prompt"].format(
        project_dir=str(project_dir),
        engine_dir=str(engine_dir)
    )

    # Create a temporary file for the output
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_file = f.name

    try:
        # Use the Task tool pattern - spawn Claude Code as a subagent
        # This requires the Claude Code CLI to be installed and configured

        # Build the command to spawn a subagent
        # We use claude code with --headless and a structured prompt
        cmd = [
            "claude",
            "code",
            "--headless",
            "--prompt", prompt,
            "--allowed-tools", "Read,Glob,Grep,Bash",
            "--output-json"
        ]

        # Run the subagent
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per analyzer
            cwd=str(project_dir)
        )

        if result.returncode != 0:
            print(f"⚠️  {analyzer_name} returned error: {result.stderr[:200]}")
            return {
                "analyzer": analyzer_id,
                "name": analyzer_name,
                "opportunities": [],
                "patterns": [],
                "summary": f"Error: {result.stderr[:200]}",
                "error": True
            }

        # Parse the output
        try:
            output = json.loads(result.stdout)
            # The output might be wrapped in a Claude response structure
            if "content" in output:
                content = output["content"]
                if isinstance(content, str):
                    # Try to parse content as JSON
                    data = json.loads(content)
                else:
                    data = content
            else:
                data = output

            # Ensure required fields
            return {
                "analyzer": analyzer_id,
                "name": analyzer_name,
                "opportunities": data.get("opportunities", []),
                "patterns": data.get("patterns", []),
                "summary": data.get("summary", "Analysis complete"),
                "error": False
            }

        except json.JSONDecodeError as e:
            print(f"⚠️  {analyzer_name} returned invalid JSON: {e}")
            # Try to extract JSON from the output
            return {
                "analyzer": analyzer_id,
                "name": analyzer_name,
                "opportunities": [],
                "patterns": [],
                "summary": f"JSON parse error: {e}",
                "error": True,
                "raw_output": result.stdout[:500]
            }

    except subprocess.TimeoutExpired:
        print(f"⏱️  {analyzer_name} timed out after 5 minutes")
        return {
            "analyzer": analyzer_id,
            "name": analyzer_name,
            "opportunities": [],
            "patterns": [],
            "summary": "Timeout after 5 minutes",
            "error": True
        }

    except FileNotFoundError:
        print(f"❌ Claude Code CLI not found. Is it installed?")
        return {
            "analyzer": analyzer_id,
            "name": analyzer_name,
            "opportunities": [],
            "patterns": [],
            "summary": "Claude Code CLI not found",
            "error": True
        }

    except Exception as e:
        print(f"❌ {analyzer_name} failed: {e}")
        return {
            "analyzer": analyzer_id,
            "name": analyzer_name,
            "opportunities": [],
            "patterns": [],
            "summary": f"Exception: {e}",
            "error": True
        }

    finally:
        # Clean up temp file
        if os.path.exists(output_file):
            os.unlink(output_file)


def calculate_scores(opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate total scores for all opportunities."""
    for opp in opportunities:
        impact = opp.get("impact_score", 3)
        effort = opp.get("effort_score", 3)
        frequency = opp.get("frequency_score", 2)
        opp["total_score"] = (impact * 3) + (frequency * 2) - (effort * 1.5)
    return opportunities


def generate_report(results: List[Dict[str, Any]], report_id: str) -> ScoutReport:
    """Generate the final scout report from analyzer results."""

    all_opportunities = []
    all_patterns = []
    analyzer_summaries = []

    for result in results:
        analyzer_id = result["analyzer"]
        analyzer_name = result["name"]
        opportunities = result.get("opportunities", [])
        patterns = result.get("patterns", [])
        summary = result.get("summary", "")
        has_error = result.get("error", False)

        # Prefix opportunity IDs with analyzer
        for opp in opportunities:
            if "id" in opp:
                opp["id"] = f"{analyzer_id}-{opp['id']}"
            else:
                opp["id"] = f"{analyzer_id}-{len(all_opportunities)+1:03d}"

        all_opportunities.extend(opportunities)
        all_patterns.extend(patterns)
        analyzer_summaries.append({
            "id": analyzer_id,
            "name": analyzer_name,
            "opportunities_found": len(opportunities),
            "patterns_found": len(patterns),
            "summary": summary,
            "error": has_error
        })

    # Calculate scores
    all_opportunities = calculate_scores(all_opportunities)

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

    summary = {
        "total_opportunities": len(all_opportunities),
        "high_impact": len([o for o in all_opportunities if o.get("impact_score", 0) >= 4]),
        "quick_wins": len(quick_wins),
        "patterns_found": len(all_patterns),
        "categories": categories,
        "analyzers": analyzer_summaries
    }

    return ScoutReport(
        id=report_id,
        timestamp=datetime.now().isoformat(),
        scout_version="1.0.0-intelligent",
        opportunities=all_opportunities,
        patterns=all_patterns,
        summary=summary
    )


def save_report(report: ScoutReport, output_dir: Path) -> Path:
    """Save the report to JSON and YAML files."""
    import yaml

    output_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_file = output_dir / f"scout-report-intelligent-{report.id}.json"
    with open(json_file, 'w') as f:
        json.dump(asdict(report), f, indent=2)

    # Save YAML (more readable)
    yaml_file = output_dir / f"scout-report-intelligent-{report.id}.yaml"
    with open(yaml_file, 'w') as f:
        yaml.dump(asdict(report), f, default_flow_style=False, sort_keys=False)

    return json_file, yaml_file


def print_summary(report: ScoutReport, json_file: Path, yaml_file: Path):
    """Print a human-readable summary of the report."""
    print("\n" + "="*60)
    print("INTELLIGENT SCOUT ANALYSIS COMPLETE")
    print("="*60)

    print(f"\n📊 Summary:")
    print(f"   Total opportunities: {report.summary['total_opportunities']}")
    print(f"   High impact (4-5): {report.summary['high_impact']}")
    print(f"   Quick wins: {report.summary['quick_wins']}")
    print(f"   Patterns found: {report.summary['patterns_found']}")

    print(f"\n📁 Reports saved:")
    print(f"   JSON: {json_file}")
    print(f"   YAML: {yaml_file}")

    if report.opportunities:
        print(f"\n🏆 Top 5 Opportunities:")
        for i, opp in enumerate(report.opportunities[:5], 1):
            score = opp.get("total_score", 0)
            impact = opp.get("impact_score", 0)
            effort = opp.get("effort_score", 0)
            cat = opp.get("category", "unknown")
            print(f"\n   {i}. {opp['title']}")
            print(f"      Score: {score:.1f} | Impact: {impact}/5 | Effort: {effort}/5 | Category: {cat}")
            print(f"      Action: {opp.get('suggested_action', 'N/A')[:70]}...")

    if report.summary.get("quick_wins", 0) > 0:
        quick_wins = [o for o in report.opportunities if o.get("effort_score", 5) <= 2 and o.get("impact_score", 1) >= 3]
        print(f"\n⚡ Quick Wins (Low effort, High impact):")
        for i, opp in enumerate(quick_wins[:3], 1):
            print(f"   {i}. {opp['title']} (Score: {opp.get('total_score', 0):.1f})")

    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Intelligent Scout - AI-powered improvement discovery"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run analyzers in parallel"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory for reports"
    )
    parser.add_argument(
        "--analyzers",
        nargs="+",
        choices=[a["id"] for a in ANALYZERS],
        help="Specific analyzers to run (default: all)"
    )

    args = parser.parse_args()

    # Generate report ID
    report_id = datetime.now().strftime("%Y%m%d-%H%M%S")

    print(f"🔍 Intelligent Scout v1.0.0 starting...")
    print(f"   Report ID: {report_id}")
    print(f"   Project: {PROJECT_DIR}")
    print(f"   Parallel: {args.parallel}")

    # Filter analyzers if specified
    analyzers_to_run = ANALYZERS
    if args.analyzers:
        analyzers_to_run = [a for a in ANALYZERS if a["id"] in args.analyzers]

    print(f"\n📋 Running {len(analyzers_to_run)} analyzers:")
    for a in analyzers_to_run:
        print(f"   - {a['name']}")

    # Run analyzers
    results = []

    if args.parallel:
        print("\n🚀 Running analyzers in parallel...")
        with ThreadPoolExecutor(max_workers=len(analyzers_to_run)) as executor:
            futures = {
                executor.submit(spawn_analyzer, a, PROJECT_DIR, ENGINE_DIR): a
                for a in analyzers_to_run
            }

            for future in as_completed(futures):
                analyzer = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    status = "✅" if not result.get("error") else "❌"
                    print(f"   {status} {analyzer['name']} complete ({len(result.get('opportunities', []))} opportunities)")
                except Exception as e:
                    print(f"   ❌ {analyzer['name']} failed: {e}")
                    results.append({
                        "analyzer": analyzer["id"],
                        "name": analyzer["name"],
                        "opportunities": [],
                        "patterns": [],
                        "summary": f"Failed: {e}",
                        "error": True
                    })
    else:
        print("\n🚀 Running analyzers sequentially...")
        for analyzer in analyzers_to_run:
            result = spawn_analyzer(analyzer, PROJECT_DIR, ENGINE_DIR)
            results.append(result)
            status = "✅" if not result.get("error") else "❌"
            print(f"   {status} {analyzer['name']} complete ({len(result.get('opportunities', []))} opportunities)")

    # Generate report
    print("\n📊 Generating report...")
    report = generate_report(results, report_id)

    # Save report
    json_file, yaml_file = save_report(report, args.output_dir)

    # Print summary
    print_summary(report, json_file, yaml_file)

    return 0


if __name__ == "__main__":
    sys.exit(main())
