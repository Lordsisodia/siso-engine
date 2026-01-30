#!/usr/bin/env python3
"""
Testing Pipeline System for BlackBox5

Automates the testing process with an auto-fix loop:
1. Run tests
2. Analyze failures
3. Fix failures (using AI)
4. Re-test
5. Loop until all tests pass

Integrates with pytest and provides comprehensive test reporting.
"""

import asyncio
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml

from .context_extractor import ContextExtractor


class TestStatus(str, Enum):
    """Status of a test run"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class FixStrategy(str, Enum):
    """Strategy for fixing test failures"""
    AUTO_FIX = "auto_fix"  # AI generates fixes
    MANUAL = "manual"  # Human intervention needed
    SKIP = "skip"  # Skip this test
    RETRY = "retry"  # Just retry without changes


@dataclass
class TestFailure:
    """
    Represents a test failure.

    Attributes:
        test_file: Path to test file
        test_name: Name of the failing test
        error_type: Type of error (AssertionError, ImportError, etc.)
        error_message: Error message
        traceback: Full traceback
        context: Relevant code context
        fix_strategy: Suggested fix strategy
        fix_attempts: Number of fix attempts made
        resolved: Whether the failure has been resolved
    """
    test_file: str
    test_name: str
    error_type: str
    error_message: str
    traceback: str
    context: Dict[str, Any] = field(default_factory=dict)
    fix_strategy: FixStrategy = FixStrategy.AUTO_FIX
    fix_attempts: int = 0
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'test_file': self.test_file,
            'test_name': self.test_name,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'traceback': self.traceback,
            'context': self.context,
            'fix_strategy': self.fix_strategy.value,
            'fix_attempts': self.fix_attempts,
            'resolved': self.resolved
        }


@dataclass
class TestResult:
    """
    Results from a test run.

    Attributes:
        run_id: Unique identifier for this run
        timestamp: When the test run started
        test_files: List of test files executed
        total_tests: Total number of tests
        passed: Number of passed tests
        failed: Number of failed tests
        skipped: Number of skipped tests
        errors: Number of errors
        duration: Test run duration in seconds
        failures: List of TestFailure objects
        status: Overall test status
    """
    run_id: str
    timestamp: datetime
    test_files: List[str]
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    failures: List[TestFailure] = field(default_factory=list)
    status: TestStatus = TestStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'run_id': self.run_id,
            'timestamp': self.timestamp.isoformat(),
            'test_files': self.test_files,
            'total_tests': self.total_tests,
            'passed': self.passed,
            'failed': self.failed,
            'skipped': self.skipped,
            'errors': self.errors,
            'duration': self.duration,
            'failures': [f.to_dict() for f in self.failures],
            'status': self.status.value if isinstance(self.status, TestStatus) else self.status
        }


class TestRunner:
    """
    Runs tests using pytest and parses results.
    """

    def __init__(self, blackbox_root: Path):
        self.blackbox_root = Path(blackbox_root)
        self.tests_dir = self.blackbox_root / "tests"
        self.engine_tests_dir = self.blackbox_root / "engine" / "development" / "tests"

    async def run_tests(
        self,
        test_pattern: str = "test_*.py",
        verbose: bool = False
    ) -> TestResult:
        """
        Run tests using pytest.

        Args:
            test_pattern: Pattern for test files
            verbose: Whether to run in verbose mode

        Returns:
            TestResult with test outcomes
        """
        import uuid

        run_id = str(uuid.uuid4())[:8]
        start_time = datetime.utcnow()

        # Build pytest command
        pytest_args = [
            sys.executable, "-m", "pytest",
            "-v" if verbose else "",
            "--tb=short",
            "--json-report",  # Requires pytest-json-report plugin
            "--json-report-file=/tmp/pytest_report.json",
            str(self.tests_dir),
            str(self.engine_tests_dir),
            "-k", test_pattern
        ]

        # Filter out empty strings
        pytest_args = [arg for arg in pytest_args if arg]

        print(f"\n🧪 Running tests: {' '.join(pytest_args)}\n")

        # Run pytest
        try:
            result = subprocess.run(
                pytest_args,
                cwd=self.blackbox_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                run_id=run_id,
                timestamp=start_time,
                test_files=[],
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                duration=300.0,
                status=TestStatus.ERROR
            )

        duration = (datetime.utcnow() - start_time).total_seconds()

        # Parse output
        return self._parse_test_output(
            run_id=run_id,
            timestamp=start_time,
            output=result.stdout,
            error=result.stderr,
            duration=duration
        )

    def _parse_test_output(
        self,
        run_id: str,
        timestamp: datetime,
        output: str,
        error: str,
        duration: float
    ) -> TestResult:
        """Parse pytest output to extract test results"""

        # Try to load JSON report if available
        json_report_path = Path("/tmp/pytest_report.json")
        if json_report_path.exists():
            try:
                with open(json_report_path) as f:
                    report = json.load(f)
                return self._parse_json_report(run_id, timestamp, report, duration)
            except Exception:
                pass

        # Fall back to parsing stdout
        return self._parse_stdout(run_id, timestamp, output, error, duration)

    def _parse_json_report(
        self,
        run_id: str,
        timestamp: datetime,
        report: Dict[str, Any],
        duration: float
    ) -> TestResult:
        """Parse pytest JSON report"""

        summary = report.get('summary', {})
        total_tests = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)
        errors = summary.get('error', 0)

        # Extract failures
        failures = []
        for test in report.get('tests', []):
            if test.get('outcome') in ['failed', 'error']:
                failure = TestFailure(
                    test_file=test.get('nodeid', '').split('::')[0],
                    test_name=test.get('nodeid', ''),
                    error_type=test.get('call', {}).get('longrepr', '').split('\n')[0] if test.get('call') else 'Unknown',
                    error_message=test.get('call', {}).get('longrepr', ''),
                    traceback=test.get('call', {}).get('longrepr', '')
                )
                failures.append(failure)

        status = TestStatus.PASSED if (failed == 0 and errors == 0) else TestStatus.FAILED

        return TestResult(
            run_id=run_id,
            timestamp=timestamp,
            test_files=[],
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=duration,
            failures=failures,
            status=status
        )

    def _parse_stdout(
        self,
        run_id: str,
        timestamp: datetime,
        output: str,
        error: str,
        duration: float
    ) -> TestResult:
        """Parse pytest stdout to extract results"""

        # Parse summary line (e.g., "5 passed, 2 failed in 3.45s")
        lines = output.split('\n')

        total_tests = 0
        passed = 0
        failed = 0
        skipped = 0
        errors = 0

        for line in lines:
            if ' passed' in line or ' failed' in line:
                # Extract numbers
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'passed' in part:
                        passed = int(parts[i-1]) if i > 0 else 0
                    elif 'failed' in part:
                        failed = int(parts[i-1]) if i > 0 else 0
                    elif 'skipped' in part:
                        skipped = int(parts[i-1]) if i > 0 else 0
                    elif 'error' in part:
                        errors = int(parts[i-1]) if i > 0 else 0

        total_tests = passed + failed + skipped + errors

        status = TestStatus.PASSED if (failed == 0 and errors == 0) else TestStatus.FAILED

        return TestResult(
            run_id=run_id,
            timestamp=timestamp,
            test_files=[],
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=duration,
            status=status
        )


class FailureAnalyzer:
    """
    Analyzes test failures to determine:
    1. Root cause
    2. Fix strategy
    3. Required context for fixing
    """

    def __init__(self, context_extractor: ContextExtractor):
        self.context_extractor = context_extractor

    async def analyze_failure(self, failure: TestFailure) -> Dict[str, Any]:
        """
        Analyze a test failure.

        Returns:
            Dictionary with:
            - root_cause: str
            - fix_strategy: FixStrategy
            - suggested_fix: str
            - context_files: List[str]
        """
        # Extract keywords from error
        keywords = self._extract_keywords(failure)

        # Get relevant context
        context = await self.context_extractor.extract_context(
            task_id=f"fix_{failure.test_name}",
            task_description=f"Fix failing test: {failure.test_name}"
        )

        # Determine fix strategy
        fix_strategy = self._determine_fix_strategy(failure, context)

        # Generate suggested fix
        suggested_fix = self._generate_fix_suggestion(failure, context)

        return {
            'root_cause': self._identify_root_cause(failure),
            'fix_strategy': fix_strategy,
            'suggested_fix': suggested_fix,
            'context_files': [f.file_path for f in context.relevant_files]
        }

    def _extract_keywords(self, failure: TestFailure) -> List[str]:
        """Extract keywords from failure for context search"""
        keywords = []

        # From test name
        test_name_parts = failure.test_name.split('_')
        keywords.extend(test_name_parts)

        # From error type
        if failure.error_type:
            keywords.append(failure.error_type.lower())

        # From error message
        if failure.error_message:
            words = failure.error_message.split()[:5]
            keywords.extend(words)

        return keywords

    def _determine_fix_strategy(self, failure: TestFailure, context: Any) -> FixStrategy:
        """Determine the best strategy for fixing this failure"""

        # Import errors - need to add imports
        if 'ImportError' in failure.error_type or 'ModuleNotFoundError' in failure.error_type:
            return FixStrategy.AUTO_FIX

        # Assertion errors - usually logic issues
        if 'AssertionError' in failure.error_type:
            return FixStrategy.AUTO_FIX

        # Type errors - usually type mismatches
        if 'TypeError' in failure.error_type:
            return FixStrategy.AUTO_FIX

        # Attribute errors - missing attributes
        if 'AttributeError' in failure.error_type:
            return FixStrategy.AUTO_FIX

        # Unknown errors - manual review
        return FixStrategy.MANUAL

    def _identify_root_cause(self, failure: TestFailure) -> str:
        """Identify the root cause of the failure"""

        if 'ImportError' in failure.error_type:
            return "Missing import or module"
        elif 'AssertionError' in failure.error_type:
            return "Test assertion failed - logic error"
        elif 'TypeError' in failure.error_type:
            return "Type mismatch"
        elif 'AttributeError' in failure.error_type:
            return "Missing attribute or method"
        else:
            return "Unknown error"

    def _generate_fix_suggestion(self, failure: TestFailure, context: Any) -> str:
        """Generate a suggested fix for the failure"""

        if 'ImportError' in failure.error_type:
            module = failure.error_message.split("'")[1] if "'" in failure.error_message else "module"
            return f"Add import: from {module} import ..."

        elif 'AssertionError' in failure.error_type:
            return "Review the assertion logic and fix the implementation"

        elif 'AttributeError' in failure.error_type:
            attr = failure.error_message.split("'")[1] if "'" in failure.error_message else "attribute"
            return f"Add missing attribute: {attr}"

        else:
            return "Review the error and fix the implementation"


class AutoFixAgent:
    """
    AI-powered agent that automatically fixes test failures.

    Uses context extraction and code analysis to generate fixes.
    """

    def __init__(self, context_extractor: ContextExtractor):
        self.context_extractor = context_extractor

    async def fix_failure(self, failure: TestFailure, analysis: Dict[str, Any]) -> bool:
        """
        Attempt to fix a test failure.

        Args:
            failure: The test failure to fix
            analysis: Analysis from FailureAnalyzer

        Returns:
            True if fix was applied successfully
        """
        # For now, this is a placeholder
        # In a real implementation, this would:
        # 1. Generate code fixes
        # 2. Apply fixes to files
        # 3. Re-run tests

        print(f"🔧 Attempting to fix: {failure.test_name}")
        print(f"   Strategy: {analysis['fix_strategy']}")
        print(f"   Suggestion: {analysis['suggested_fix']}")

        # Simulate fix application
        failure.fix_attempts += 1

        # Return False to indicate manual intervention needed
        # (In real implementation, this would return True if fix applied)
        return False


class TestingPipeline:
    """
    Main testing pipeline orchestrator.

    Runs tests, analyzes failures, and fixes them in an automated loop.
    """

    def __init__(self, blackbox_root: Path):
        self.blackbox_root = Path(blackbox_root)
        self.pipeline_dir = self.blackbox_root / "blackbox5" / "pipeline"
        self.test_results_file = self.pipeline_dir / "test_results.yaml"

        # Ensure directories exist
        self.pipeline_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.context_extractor = ContextExtractor(
            codebase_path=self.blackbox_root,
            max_context_tokens=8000
        )
        self.test_runner = TestRunner(blackbox_root)
        self.failure_analyzer = FailureAnalyzer(self.context_extractor)
        self.auto_fix_agent = AutoFixAgent(self.context_extractor)

        # Load history
        self.test_history: List[TestResult] = self._load_history()

    def _load_history(self) -> List[TestResult]:
        """Load test history from disk"""
        if not self.test_results_file.exists():
            return []

        with open(self.test_results_file, 'r') as f:
            data = yaml.safe_load(f)

        history = []
        for item in data.get('runs', []):
            # Reconstruct failures
            failures = [
                TestFailure(**f) for f in item.get('failures', [])
            ]
            item['failures'] = failures
            item['timestamp'] = datetime.fromisoformat(item['timestamp'])
            history.append(TestResult(**item))

        return history

    def _save_history(self):
        """Save test history to disk"""
        data = {
            'updated_at': datetime.utcnow().isoformat(),
            'total_runs': len(self.test_history),
            'runs': [r.to_dict() for r in self.test_history]
        }

        with open(self.test_results_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    async def run_test_suite(
        self,
        test_pattern: str = "test_*.py",
        max_iterations: int = 3
    ) -> TestResult:
        """
        Run the test suite with auto-fix loop.

        Args:
            test_pattern: Pattern for test files
            max_iterations: Maximum fix iterations

        Returns:
            Final test result
        """
        print(f"\n{'='*80}")
        print(f"🧪 TESTING PIPELINE")
        print(f"{'='*80}\n")

        iteration = 0
        current_result: Optional[TestResult] = None

        while iteration < max_iterations:
            iteration += 1
            print(f"\n📋 Iteration {iteration}/{max_iterations}")
            print("-" * 40)

            # Run tests
            current_result = await self.test_runner.run_tests(test_pattern)

            print(f"\n📊 Test Results:")
            print(f"   Total: {current_result.total_tests}")
            print(f"   Passed: {current_result.passed} ✅")
            print(f"   Failed: {current_result.failed} ❌")
            print(f"   Skipped: {current_result.skipped} ⏭️")
            print(f"   Duration: {current_result.duration:.2f}s")

            # Save result
            self.test_history.append(current_result)
            self._save_history()

            # Check if all tests passed
            if current_result.status == TestStatus.PASSED:
                print(f"\n✅ All tests passed!")
                break

            # If there are failures, try to fix them
            if current_result.failures:
                print(f"\n🔧 Analyzing {len(current_result.failures)} failures...")

                for failure in current_result.failures:
                    # Analyze failure
                    analysis = await self.failure_analyzer.analyze_failure(failure)

                    # Try to fix
                    fixed = await self.auto_fix_agent.fix_failure(failure, analysis)

                    if not fixed:
                        print(f"⚠️  Could not auto-fix: {failure.test_name}")
                        print(f"   Manual intervention may be needed")

                # If we made fixes, continue to next iteration
                if iteration < max_iterations:
                    print(f"\n🔄 Re-running tests...")
                    continue

        print(f"\n{'='*80}")
        print(f"{'✅ TESTING COMPLETE' if current_result.status == TestStatus.PASSED else '⚠️ TESTING FINISHED WITH FAILURES'}")
        print(f"{'='*80}\n")

        return current_result

    def get_test_history(self, limit: int = 10) -> List[TestResult]:
        """Get recent test history"""
        return self.test_history[-limit:]

    def get_failure_summary(self) -> Dict[str, Any]:
        """Get summary of recent failures"""
        recent_failures = []

        for result in self.test_history[-10:]:
            for failure in result.failures:
                recent_failures.append({
                    'test': failure.test_name,
                    'error': failure.error_type,
                    'timestamp': result.timestamp.isoformat(),
                    'resolved': failure.resolved
                })

        return {
            'total_failures': len(recent_failures),
            'unresolved': len([f for f in recent_failures if not f['resolved']]),
            'failures': recent_failures
        }


# CLI interface
def main():
    """CLI entry point for testing pipeline"""
    import argparse

    parser = argparse.ArgumentParser(
        description="BlackBox5 Testing Pipeline"
    )
    parser.add_argument(
        "command",
        choices=["run", "history", "summary"],
        help="Command to execute"
    )
    parser.add_argument("--pattern", type=str, default="test_*.py", help="Test pattern")
    parser.add_argument("--iterations", type=int, default=3, help="Max fix iterations")
    parser.add_argument("--blackbox", type=Path, default=Path.cwd(), help="BlackBox5 root")

    args = parser.parse_args()

    async def run_command():
        pipeline = TestingPipeline(args.blackbox)

        if args.command == "run":
            result = await pipeline.run_test_suite(
                test_pattern=args.pattern,
                max_iterations=args.iterations
            )

            # Exit with error code if tests failed
            if result.status != TestStatus.PASSED:
                sys.exit(1)

        elif args.command == "history":
            history = pipeline.get_test_history()
            print(f"\n📜 Recent Test Runs ({len(history)}\n")

            for result in history:
                status_emoji = "✅" if result.status == TestStatus.PASSED else "❌"
                print(f"   {status_emoji} {result.timestamp.strftime('%Y-%m-%d %H:%M')}")
                print(f"      {result.passed}/{result.total_tests} passed in {result.duration:.2f}s")

        elif args.command == "summary":
            summary = pipeline.get_failure_summary()
            print(f"\n📊 Failure Summary\n")
            print(f"   Total: {summary['total_failures']}")
            print(f"   Unresolved: {summary['unresolved']}")

            for failure in summary['failures']:
                status_emoji = "✅" if failure['resolved'] else "❌"
                print(f"   {status_emoji} {failure['test']}")

    asyncio.run(run_command())


if __name__ == "__main__":
    main()
