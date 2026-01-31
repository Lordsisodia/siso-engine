#!/usr/bin/env python3
"""
RALF Log Ingestor - Pattern Analysis & Feedback Pipeline
Captures RALF loop outputs, extracts failure patterns, generates insights
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class FailurePattern:
    """Extracted failure pattern from RALF logs"""
    pattern_type: str
    description: str
    frequency: int
    last_occurrence: str
    examples: List[str]
    suggested_fix: Optional[str] = None


@dataclass
class LoopAnalysis:
    """Analysis of a single RALF loop"""
    loop_id: str
    timestamp: str
    duration_seconds: Optional[int]
    status: str
    errors: List[str]
    warnings: List[str]
    decisions_made: List[str]
    task_completed: Optional[str]
    context_budget_exceeded: bool = False
    phase_gates_blocked: List[str] = None

    def __post_init__(self):
        if self.phase_gates_blocked is None:
            self.phase_gates_blocked = []


class RALFLogAnalyzer:
    """Analyzes RALF session logs for patterns"""

    # Pattern matchers for common failures

    def _get_current_branch(self) -> str:
        """Get current git branch"""
        import subprocess
        try:
            result = subprocess.run(
                ["git", "-C", str(self.blackbox5_dir), "branch", "--show-current"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def _get_commit_history(self, limit: int = 5) -> List[Dict]:
        """Get recent commit history for context"""
        import subprocess
        try:
            result = subprocess.run(
                ["git", "-C", str(self.blackbox5_dir), "log", "--oneline", f"-{limit}", "--format=%h|%s|%ci"],
                capture_output=True, text=True, check=True
            )
            commits = []
            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    hash_, subject, date = line.split("|", 2)
                    commits.append({"hash": hash_, "subject": subject, "date": date})
            return commits
        except subprocess.CalledProcessError:
            return []
    ERROR_PATTERNS = {
        'git_conflict': re.compile(r'conflict|merge.*failed|CONFLICT', re.I),
        'permission_denied': re.compile(r'permission denied|access denied|EACCES', re.I),
        'file_not_found': re.compile(r'file not found|no such file|ENOENT', re.I),
        'syntax_error': re.compile(r'syntax error|unexpected token|parse error', re.I),
        'import_error': re.compile(r'cannot import|module not found|ImportError', re.I),
        'context_exceeded': re.compile(r'context budget|token limit|exceeded', re.I),
        'phase_blocked': re.compile(r'phase.*blocked|gate.*failed', re.I),
        'tool_failure': re.compile(r'tool.*failed|execution.*error|Bash.*exit', re.I),
        'task_abandoned': re.compile(r'task.*abandoned|incomplete|partial', re.I),
    }

    def __init__(self, blackbox5_dir: Path):
        self.blackbox5_dir = Path(blackbox5_dir)
        self.logs_dir = self.blackbox5_dir / "5-project-memory/blackbox5/.autonomous/LOGS"
        self.runs_dir = self.blackbox5_dir / "5-project-memory/blackbox5/.autonomous/runs"
        self.knowledge_dir = self.blackbox5_dir / "5-project-memory/blackbox5/knowledge/ralf-patterns"
        self.insights_file = self.knowledge_dir / "auto-insights.json"

        # Ensure knowledge directory exists
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

    def parse_session_log(self, log_path: Path) -> Optional[LoopAnalysis]:
        """Parse a single RALF session log file"""
        if not log_path.exists():
            return None

        content = log_path.read_text()
        lines = content.split('\n')

        # Extract loop ID from filename
        loop_id = log_path.stem.replace('ralf-session-', '')

        # Find timestamp
        timestamp_match = re.search(r'\[(\d{2}:\d{2}:\d{2})\]', content)
        timestamp = timestamp_match.group(1) if timestamp_match else "unknown"

        # Extract errors and warnings
        errors = []
        warnings = []
        decisions = []
        phase_blocked = []

        for line in lines:
            if '[ERROR]' in line or '✗' in line:
                errors.append(line.strip())
            elif '[WARNING]' in line or '⚠' in line:
                warnings.append(line.strip())
            elif 'Decision:' in line or 'decision_registry' in line:
                decisions.append(line.strip())
            elif 'phase' in line.lower() and 'blocked' in line.lower():
                phase_blocked.append(line.strip())

        # Determine status
        status = "unknown"
        if "COMPLETE" in content:
            status = "complete"
        elif "BLOCKED" in content:
            status = "blocked"
        elif errors:
            status = "failed"
        elif warnings:
            status = "partial"

        # Check for context budget issues
        context_exceeded = bool(re.search(r'context budget.*exceeded|forcing checkpoint', content, re.I))

        # Extract task if mentioned
        task_match = re.search(r'Task:\s*(TASK-\d+)', content)
        task_completed = task_match.group(1) if task_match else None

        return LoopAnalysis(
            loop_id=loop_id,
            timestamp=timestamp,
            duration_seconds=None,  # Would need to parse from telemetry
            status=status,
            errors=errors,
            warnings=warnings,
            decisions_made=decisions,
            task_completed=task_completed,
            context_budget_exceeded=context_exceeded,
            phase_gates_blocked=phase_blocked
        )

    def identify_failure_patterns(self, analyses: List[LoopAnalysis]) -> List[FailurePattern]:
        """Identify recurring failure patterns across loops"""
        pattern_counts = defaultdict(lambda: {"count": 0, "examples": [], "last": None})

        for analysis in analyses:
            content = ' '.join(analysis.errors + analysis.warnings)

            for pattern_name, regex in self.ERROR_PATTERNS.items():
                if regex.search(content):
                    pattern_counts[pattern_name]["count"] += 1
                    if len(pattern_counts[pattern_name]["examples"]) < 3:
                        pattern_counts[pattern_name]["examples"].append(analysis.loop_id)
                    pattern_counts[pattern_name]["last"] = analysis.timestamp

        patterns = []
        for pattern_type, data in pattern_counts.items():
            if data["count"] >= 2:  # Only report recurring patterns
                patterns.append(FailurePattern(
                    pattern_type=pattern_type,
                    description=self._get_pattern_description(pattern_type),
                    frequency=data["count"],
                    last_occurrence=data["last"],
                    examples=data["examples"],
                    suggested_fix=self._get_suggested_fix(pattern_type)
                ))

        return sorted(patterns, key=lambda p: p.frequency, reverse=True)

    def _get_pattern_description(self, pattern_type: str) -> str:
        """Get human-readable description for pattern type"""
        descriptions = {
            'git_conflict': 'Git merge conflicts preventing automatic updates',
            'permission_denied': 'File system permission errors',
            'file_not_found': 'Referenced files or paths not found',
            'syntax_error': 'Code syntax errors in generated/modified files',
            'import_error': 'Python/module import failures',
            'context_exceeded': 'Context window budget exceeded',
            'phase_blocked': 'Phase gates blocking progress',
            'tool_failure': 'Tool execution failures (Bash, Read, etc.)',
            'task_abandoned': 'Tasks abandoned or partially completed',
        }
        return descriptions.get(pattern_type, f"Unknown pattern: {pattern_type}")

    def _get_suggested_fix(self, pattern_type: str) -> Optional[str]:
        """Get suggested fix for pattern type"""
        fixes = {
            'git_conflict': 'Implement automatic conflict resolution or pause for manual intervention',
            'permission_denied': 'Check file permissions before write operations; use appropriate user context',
            'file_not_found': 'Verify file existence before operations; create missing directories',
            'syntax_error': 'Add syntax validation before file writes; use AST parsing for Python',
            'import_error': 'Verify module installation; check import paths; add requirements check',
            'context_exceeded': 'Implement aggressive context compression; spawn sub-agents earlier',
            'phase_blocked': 'Review phase gate criteria; ensure prerequisites are documented',
            'tool_failure': 'Add retry logic; validate tool inputs; check prerequisites',
            'task_abandoned': 'Break tasks into smaller chunks; add verification checkpoints',
        }
        return fixes.get(pattern_type)

    def generate_insights(self, analyses: List[LoopAnalysis]) -> Dict[str, Any]:
        """Generate actionable insights from loop analyses"""
        total = len(analyses)
        if total == 0:
            return {"error": "No analyses to process"}

        status_counts = defaultdict(int)
        error_types = defaultdict(int)
        context_issues = 0

        for analysis in analyses:
            status_counts[analysis.status] += 1
            if analysis.context_budget_exceeded:
                context_issues += 1
            for error in analysis.errors:
                for pattern_name, regex in self.ERROR_PATTERNS.items():
                    if regex.search(error):
                        error_types[pattern_name] += 1

        patterns = self.identify_failure_patterns(analyses)

        return {
            "generated_at": datetime.now().isoformat(),
            "branch": self._get_current_branch(),
            "recent_commits": self._get_commit_history(5),
            "total_loops_analyzed": total,
            "status_distribution": dict(status_counts),
            "success_rate": round((status_counts.get("complete", 0) / total) * 100, 1),
            "context_budget_issues": context_issues,
            "top_failure_patterns": [asdict(p) for p in patterns[:5]],
            "recommendations": self._generate_recommendations(patterns, status_counts),
        }

    def _generate_recommendations(self, patterns: List[FailurePattern], status_counts: Dict) -> List[str]:
        """Generate recommendations based on patterns"""
        recommendations = []

        # Check success rate
        total = sum(status_counts.values())
        complete_rate = status_counts.get("complete", 0) / total if total > 0 else 0

        if complete_rate < 0.5:
            recommendations.append("CRITICAL: Success rate below 50%. Review task complexity and system prompt.")
        elif complete_rate < 0.8:
            recommendations.append("WARNING: Success rate below 80%. Consider simplifying tasks or adding checkpoints.")

        # Pattern-specific recommendations
        for pattern in patterns[:3]:
            if pattern.frequency >= 3:
                recommendations.append(f"HIGH PRIORITY: {pattern.pattern_type} occurred {pattern.frequency} times. {pattern.suggested_fix}")

        return recommendations

    def ingest_latest(self, limit: int = 10) -> Dict[str, Any]:
        """Ingest and analyze the latest N session logs"""
        if not self.logs_dir.exists():
            return {"error": f"Logs directory not found: {self.logs_dir}"}

        # Get latest log files
        log_files = sorted(self.logs_dir.glob("ralf-session-*.log"), key=lambda p: p.stat().st_mtime, reverse=True)

        analyses = []
        for log_file in log_files[:limit]:
            analysis = self.parse_session_log(log_file)
            if analysis:
                analyses.append(analysis)

        # Generate insights
        insights = self.generate_insights(analyses)

        # Save insights
        self.insights_file.write_text(json.dumps(insights, indent=2))

        return insights

    def get_prompt_enhancements(self) -> List[str]:
        """Generate prompt enhancements based on observed patterns"""
        if not self.insights_file.exists():
            return []

        insights = json.loads(self.insights_file.read_text())
        enhancements = []

        for pattern_data in insights.get("top_failure_patterns", []):
            pattern_type = pattern_data.get("pattern_type")

            if pattern_type == "context_exceeded":
                enhancements.append("- Monitor context budget actively; spawn sub-agents when approaching limits")
            elif pattern_type == "tool_failure":
                enhancements.append("- Validate tool prerequisites before execution; add retry logic for transient failures")
            elif pattern_type == "phase_blocked":
                enhancements.append("- Document phase gate criteria explicitly; verify prerequisites before claiming completion")
            elif pattern_type == "file_not_found":
                enhancements.append("- Verify file existence before read operations; create directories before writing")
            elif pattern_type == "syntax_error":
                enhancements.append("- Validate code syntax before saving; use language-specific validators")

        return enhancements


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="RALF Log Ingestor")
    parser.add_argument("--blackbox5", default="/Users/shaansisodia/.blackbox5", help="Blackbox5 directory")
    parser.add_argument("--limit", type=int, default=10, help="Number of recent logs to analyze")
    parser.add_argument("--prompt-enhancements", action="store_true", help="Output prompt enhancements")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    analyzer = RALFLogAnalyzer(Path(args.blackbox5))

    if args.prompt_enhancements:
        enhancements = analyzer.get_prompt_enhancements()
        for enhancement in enhancements:
            print(enhancement)
    else:
        insights = analyzer.ingest_latest(limit=args.limit)

        if args.json:
            print(json.dumps(insights, indent=2))
        else:
            print(f"=== RALF Analysis ({insights.get('total_loops_analyzed', 0)} loops) ===")
            print(f"Success rate: {insights.get('success_rate', 0)}%")
            print(f"Status distribution: {insights.get('status_distribution', {})}")
            print()

            if insights.get("top_failure_patterns"):
                print("Top failure patterns:")
                for pattern in insights["top_failure_patterns"][:3]:
                    print(f"  - {pattern['pattern_type']}: {pattern['frequency']} occurrences")

            if insights.get("recommendations"):
                print()
                print("Recommendations:")
                for rec in insights["recommendations"]:
                    print(f"  • {rec}")


if __name__ == "__main__":
    main()
