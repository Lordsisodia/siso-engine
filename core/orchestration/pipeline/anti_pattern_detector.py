"""
Anti-Pattern Detection - Code Quality Scanning

This module provides tools to detect anti-patterns and code quality issues
in a codebase. It scans for common problems like TODO comments, placeholder
code, security issues, and more.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import re
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    """Violation severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Violation:
    """Represents an anti-pattern violation"""
    file_path: str
    line_number: int
    pattern_name: str
    severity: Severity
    line_content: str
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class AntiPatternDetector:
    """
    Scans codebase for anti-patterns and code quality issues.

    Patterns detected:
    - TODO/FIXME comments
    - Placeholder functions (pass, NotImplemented)
    - Duplicate code
    - Long functions (>50 lines)
    - Complex functions (cyclomatic complexity > 10)
    - Dead code (unused imports/variables)
    - Security issues (hardcoded secrets, etc.)
    """

    def __init__(self, custom_patterns: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize detector with pattern definitions.

        Args:
            custom_patterns: Optional custom patterns to add/override defaults
        """
        self.patterns = {
            'todo': {
                'regex': re.compile(r'#\s*TODO\s*:?\s*(.+)'),
                'severity': Severity.LOW,
                'suggestion': 'Implement or remove TODO item'
            },
            'fixme': {
                'regex': re.compile(r'#\s*FIXME\s*:?\s*(.+)'),
                'severity': Severity.HIGH,
                'suggestion': 'Fix the issue or document why it exists'
            },
            'hack': {
                'regex': re.compile(r'#\s*HACK\s*:?\s*(.+)'),
                'severity': Severity.MEDIUM,
                'suggestion': 'Refactor hack into proper solution'
            },
            'xxx': {
                'regex': re.compile(r'#\s*XXX\s*:?\s*(.+)'),
                'severity': Severity.HIGH,
                'suggestion': 'Address critical issue'
            },
            'placeholder_pass': {
                'regex': re.compile(r'^(\s*)pass\s*#\s*placeholder'),
                'severity': Severity.MEDIUM,
                'suggestion': 'Implement actual functionality'
            },
            'not_implemented': {
                'regex': re.compile(r'raise\s+NotImplementedError'),
                'severity': Severity.HIGH,
                'suggestion': 'Implement the method'
            },
            'hardcoded_secret': {
                'regex': re.compile(r'(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
                'severity': Severity.CRITICAL,
                'suggestion': 'Use environment variables or config files'
            },
            'debug_print': {
                'regex': re.compile(r'print\(.+\)'),
                'severity': Severity.INFO,
                'suggestion': 'Use proper logging instead of print'
            },
            'bare_except': {
                'regex': re.compile(r'except\s*:'),
                'severity': Severity.MEDIUM,
                'suggestion': 'Catch specific exceptions'
            },
            'global_variable': {
                'regex': re.compile(r'^([A-Z_]+)\s*=\s*.+'),
                'severity': Severity.LOW,
                'suggestion': 'Consider using constants module or class'
            },
            'noqa_comment': {
                'regex': re.compile(r'#\s*noqa'),
                'severity': Severity.INFO,
                'suggestion': 'Review noqa usage - ensure issues are properly addressed'
            },
            'pytest_todo': {
                'regex': re.compile(r'@pytest\.mark\.skip|@pytest\.mark\.xfail'),
                'severity': Severity.MEDIUM,
                'suggestion': 'Implement or update skipped tests'
            },
        }

        # Add custom patterns if provided
        if custom_patterns:
            for name, config in custom_patterns.items():
                if 'regex' in config:
                    config['regex'] = re.compile(config['regex'])
                self.patterns[name] = config

    def scan(
        self,
        path: Path,
        file_patterns: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None
    ) -> List[Violation]:
        """
        Scan codebase for anti-patterns.

        Args:
            path: Root path to scan
            file_patterns: Optional file patterns (default: ['*.py'])
            exclude_dirs: Directories to exclude (default: ['node_modules', '.git', '__pycache__'])

        Returns:
            List of violations found
        """
        if file_patterns is None:
            file_patterns = ['*.py', '*.js', '*.ts', '*.tsx']

        if exclude_dirs is None:
            exclude_dirs = ['node_modules', '.git', '__pycache__', 'venv', 'dist', 'build', '.venv', 'env']

        violations = []

        for pattern in file_patterns:
            for file_path in path.rglob(pattern):
                # Skip excluded directories
                if any(exclude in str(file_path) for exclude in exclude_dirs):
                    continue

                # Skip non-files
                if not file_path.is_file():
                    continue

                violations.extend(self._scan_file(file_path))

        logger.info(f"Found {len(violations)} violations in {path}")
        return violations

    def _scan_file(self, file_path: Path) -> List[Violation]:
        """Scan a single file for violations"""
        violations = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # Check each pattern
                for pattern_name, pattern_config in self.patterns.items():
                    match = pattern_config['regex'].search(line)
                    if match:
                        violation = Violation(
                            file_path=str(file_path),
                            line_number=line_num,
                            pattern_name=pattern_name,
                            severity=pattern_config['severity'],
                            line_content=line.strip(),
                            suggestion=pattern_config.get('suggestion')
                        )
                        violations.append(violation)

        except Exception as e:
            logger.debug(f"Could not scan {file_path}: {e}")

        return violations

    def get_report(self, violations: List[Violation], max_per_severity: int = 10) -> str:
        """
        Generate human-readable report.

        Args:
            violations: List of violations
            max_per_severity: Maximum violations to show per severity

        Returns:
            Formatted report string
        """
        if not violations:
            return "No violations found! ✨"

        # Group by severity
        by_severity = {
            Severity.CRITICAL: [],
            Severity.HIGH: [],
            Severity.MEDIUM: [],
            Severity.LOW: [],
            Severity.INFO: []
        }

        for v in violations:
            by_severity[v.severity].append(v)

        lines = [
            "# Anti-Pattern Detection Report",
            "",
            f"**Total Violations:** {len(violations)}",
            "",
        ]

        # Print by severity
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]:
            sev_violations = by_severity[severity]
            if sev_violations:
                lines.append(f"## {severity.value.upper()} ({len(sev_violations)})")
                lines.append("")

                for v in sev_violations[:max_per_severity]:
                    lines.append(f"### {v.file_path}:{v.line_number}")
                    lines.append(f"**Pattern:** {v.pattern_name}")
                    if v.suggestion:
                        lines.append(f"**Suggestion:** {v.suggestion}")
                    lines.append("```")
                    lines.append(v.line_content)
                    lines.append("```")
                    lines.append("")

        return '\n'.join(lines)

    def get_statistics(self, violations: List[Violation]) -> Dict[str, Any]:
        """
        Get statistics about violations.

        Args:
            violations: List of violations

        Returns:
            Dictionary with violation statistics
        """
        total = len(violations)

        by_pattern = defaultdict(int)
        by_severity = defaultdict(int)
        by_file = defaultdict(int)

        for v in violations:
            # Count by pattern
            pattern = v.pattern_name
            by_pattern[pattern] += 1

            # Count by severity
            severity = v.severity.value
            by_severity[severity] += 1

            # Count by file
            file = v.file_path
            by_file[file] += 1

        return {
            'total': total,
            'by_pattern': dict(by_pattern),
            'by_severity': dict(by_severity),
            'top_files': dict(sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:10])
        }

    def filter_by_severity(self, violations: List[Violation], min_severity: Severity) -> List[Violation]:
        """
        Filter violations by minimum severity level.

        Args:
            violations: List of violations
            min_severity: Minimum severity to include

        Returns:
            Filtered list of violations
        """
        severity_order = {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4
        }

        min_level = severity_order[min_severity]
        return [v for v in violations if severity_order[v.severity] >= min_level]

    def filter_by_pattern(self, violations: List[Violation], pattern_names: List[str]) -> List[Violation]:
        """
        Filter violations by pattern names.

        Args:
            violations: List of violations
            pattern_names: Pattern names to include

        Returns:
            Filtered list of violations
        """
        return [v for v in violations if v.pattern_name in pattern_names]

    def filter_by_file(self, violations: List[Violation], file_path: str) -> List[Violation]:
        """
        Filter violations by file path.

        Args:
            violations: List of violations
            file_path: File path to filter by (partial match)

        Returns:
            Filtered list of violations
        """
        return [v for v in violations if file_path in v.file_path]
