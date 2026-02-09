#!/usr/bin/env python3
"""
Executor Agent - Implement Quick Wins

Automatically implements low-effort, high-impact improvements.
Part of the Agent Improvement Loop: Scout → Planner → Executor → Verifier

Usage:
    executor-implement.py --task-id ID [--dry-run]
    executor-implement.py --quick-wins [--limit N]
"""

import argparse
import json
import os
import re
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# Import path resolution library
import sys
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir.parent / "lib"))
from paths import PathResolver, get_path_resolver

# Configuration
resolver = get_path_resolver()
PROJECT_DIR = resolver.get_project_path()
ENGINE_DIR = resolver.engine_path
PLANNER_REPORT_DIR = resolver.get_analysis_path() / "planner-reports"
TASKS_DIR = resolver.get_project_path() / "tasks" / "active"
RESULTS_DIR = resolver.get_runs_path()

# Load agent configuration from YAML
CONFIG_PATH = Path(__file__).parent.parent / "config" / "agent-config.yaml"

def load_agent_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    return {}

AGENT_CONFIG = load_agent_config()


@dataclass
class ExecutionResult:
    """Result of executing an improvement."""
    task_id: str
    success: bool
    action_taken: str
    files_modified: List[str]
    error_message: Optional[str] = None
    before_state: Optional[str] = None
    after_state: Optional[str] = None
    execution_time_ms: int = 0


class ExecutorAgent:
    """
    Executor Agent that implements quick wins automatically.
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.results: List[ExecutionResult] = []

    def log(self, message: str):
        """Print execution log."""
        prefix = "[DRY-RUN] " if self.dry_run else ""
        print(f"{prefix}{message}")

    def load_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load a task file."""
        task_file = TASKS_DIR / task_id / "task.md"
        if not task_file.exists():
            self.log(f"❌ Task file not found: {task_file}")
            return None

        try:
            with open(task_file, 'r') as f:
                content = f.read()

            # Parse basic info from markdown
            task = {
                "id": task_id,
                "content": content,
                "file_path": str(task_file)
            }

            # Extract fields from markdown
            lines = content.split('\n')
            for line in lines:
                if line.startswith('**Priority:**'):
                    task["priority"] = line.split('**Priority:**')[1].strip()
                elif line.startswith('**Category:**'):
                    task["category"] = line.split('**Category:**')[1].strip()
                elif line.startswith('**Suggested Action:**'):
                    task["action"] = line.split('**Suggested Action:**')[1].strip()

            return task

        except Exception as e:
            self.log(f"❌ Error loading task: {e}")
            return None

    def execute_threshold_fix(self, task: Dict[str, Any]) -> ExecutionResult:
        """
        Execute: Lower confidence threshold from 70% to 60%.
        Uses config path for skill-selection.yaml.
        """
        task_id = task["id"]
        # Use config path if available, fall back to default
        paths_config = AGENT_CONFIG.get("paths", {})
        ops_dir = paths_config.get("operations", "operations")
        file_path = PROJECT_DIR / ops_dir / "skill-registry.yaml"

        start_time = datetime.now()

        try:
            with open(file_path, 'r') as f:
                content = f.read()
                before_state = content

            # Check if already fixed
            if 'threshold: 60' in content:
                return ExecutionResult(
                    task_id=task_id,
                    success=True,
                    action_taken="Threshold already at 60%, no change needed",
                    files_modified=[str(file_path)],
                    before_state=before_state,
                    after_state=before_state
                )

            # Replace threshold
            new_content = re.sub(
                r'threshold: 70',
                'threshold: 60',
                content
            )

            # Also update the note
            new_content = re.sub(
                r'Only invoke skill if confidence >= 70%',
                'Only invoke skill if confidence >= 60%',
                new_content
            )

            if not self.dry_run:
                with open(file_path, 'w') as f:
                    f.write(new_content)

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return ExecutionResult(
                task_id=task_id,
                success=True,
                action_taken="Lowered skill confidence threshold from 70% to 60%",
                files_modified=[str(file_path)],
                before_state=before_state,
                after_state=new_content,
                execution_time_ms=execution_time
            )

        except Exception as e:
            return ExecutionResult(
                task_id=task_id,
                success=False,
                action_taken="Failed to update threshold",
                files_modified=[],
                error_message=str(e)
            )

    def execute_fix_engine_path(self, task: Dict[str, Any]) -> ExecutionResult:
        """
        Execute: Fix blackbox.py engine path (01-core -> core).
        Uses config for project paths.
        """
        task_id = task["id"]
        # Use standard project paths
        file_path = PROJECT_DIR / "bin" / "blackbox.py"

        start_time = datetime.now()

        try:
            with open(file_path, 'r') as f:
                content = f.read()
                before_state = content

            # Replace path
            new_content = re.sub(
                r'01-core',
                'core',
                content
            )

            if not self.dry_run:
                with open(file_path, 'w') as f:
                    f.write(new_content)

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return ExecutionResult(
                task_id=task_id,
                success=True,
                action_taken="Fixed engine path from '01-core' to 'core'",
                files_modified=[str(file_path)],
                before_state=before_state,
                after_state=new_content,
                execution_time_ms=execution_time
            )

        except Exception as e:
            return ExecutionResult(
                task_id=task_id,
                success=False,
                action_taken="Failed to fix engine path",
                files_modified=[],
                error_message=str(e)
            )

    def execute_standardize_thresholds(self, task: Dict[str, Any]) -> ExecutionResult:
        """
        Execute: Standardize all confidence thresholds to 70%.
        Uses config path for operations directory.
        """
        task_id = task["id"]
        # Use config path if available
        paths_config = AGENT_CONFIG.get("paths", {})
        ops_dir = paths_config.get("operations", "operations")
        files_to_check = [
            PROJECT_DIR / ops_dir / "skill-selection.yaml",
        ]

        start_time = datetime.now()
        modified_files = []

        for file_path in files_to_check:
            if not file_path.exists():
                continue

            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Standardize all thresholds to 70%
                new_content = re.sub(
                    r'confidence_threshold:\s*\d+',
                    'confidence_threshold: 70',
                    content
                )

                if content != new_content and not self.dry_run:
                    with open(file_path, 'w') as f:
                        f.write(new_content)
                    modified_files.append(str(file_path))

            except Exception as e:
                self.log(f"⚠️  Error processing {file_path}: {e}")

        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return ExecutionResult(
            task_id=task_id,
            success=len(modified_files) > 0,
            action_taken=f"Standardized thresholds in {len(modified_files)} files",
            files_modified=modified_files,
            execution_time_ms=execution_time
        )

    def execute_sync_completion_counts(self, task: Dict[str, Any]) -> ExecutionResult:
        """
        Execute: Sync completion counts across metrics files.
        Uses config paths for task directories.
        """
        task_id = task["id"]

        start_time = datetime.now()

        # This is a data consistency fix - would need to analyze actual files
        # For now, mark as requiring manual review

        return ExecutionResult(
            task_id=task_id,
            success=False,
            action_taken="Requires manual review - data consistency check needed",
            files_modified=[],
            error_message="Manual review required for data synchronization"
        )

    def get_handler_for_task(self, task_id: str, task_action: str = "") -> str:
        """
        Get the handler method name for a given task ID.
        First checks agent-config.yaml mappings, then falls back to action string matching.
        """
        # Check config mappings first
        task_handlers = AGENT_CONFIG.get("task_handlers", {})
        if task_id in task_handlers:
            return task_handlers[task_id].get("handler", "")

        # Fall back to action string matching
        action_lower = task_action.lower()
        if "threshold" in action_lower and "standardize" not in action_lower:
            return "threshold_fix"
        elif "engine path" in action_lower:
            return "engine_path_fix"
        elif "standardize" in action_lower:
            return "standardize_thresholds"
        elif "sync completion" in action_lower:
            return "sync_completion"

        return ""

    def execute_task(self, task_id: str) -> ExecutionResult:
        """Execute a specific task using config-driven routing."""
        self.log(f"\n🔧 Executing task: {task_id}")

        task = self.load_task(task_id)
        if not task:
            return ExecutionResult(
                task_id=task_id,
                success=False,
                action_taken="Failed to load task",
                files_modified=[],
                error_message="Task file not found or unreadable"
            )

        # Get handler from config or fallback matching
        handler_name = self.get_handler_for_task(task_id, task.get("action", ""))

        # Route to appropriate executor
        handler_map = {
            "threshold_fix": self.execute_threshold_fix,
            "engine_path_fix": self.execute_fix_engine_path,
            "standardize_thresholds": self.execute_standardize_thresholds,
            "sync_completion": self.execute_sync_completion_counts,
        }

        if handler_name and handler_name in handler_map:
            return handler_map[handler_name](task)
        else:
            return ExecutionResult(
                task_id=task_id,
                success=False,
                action_taken="No automated executor available for this task",
                files_modified=[],
                error_message="Manual execution required"
            )

    def execute_quick_wins(self, limit: int = 5) -> List[ExecutionResult]:
        """Execute all quick win tasks."""
        self.log(f"\n🚀 Executing up to {limit} quick wins...")

        # Load planner report to find quick wins
        planner_reports = sorted(PLANNER_REPORT_DIR.glob("PLAN-*.yaml"), reverse=True)
        if not planner_reports:
            self.log("❌ No planner reports found")
            return []

        with open(planner_reports[0], 'r') as f:
            report = yaml.safe_load(f)

        quick_wins = report.get("planner_report", {}).get("quick_wins", [])

        results = []
        for win in quick_wins[:limit]:
            task_id = win.get("id")
            if task_id:
                result = self.execute_task(task_id)
                results.append(result)

        return results

    def save_execution_report(self, results: List[ExecutionResult]) -> Path:
        """Save execution results to a report."""
        report_dir = PROJECT_DIR / ".autonomous" / "analysis" / "executor-reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        report_id = f"EXEC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        report = {
            "executor_report": {
                "id": report_id,
                "timestamp": datetime.now().isoformat(),
                "dry_run": self.dry_run,
                "summary": {
                    "total_tasks": len(results),
                    "successful": len([r for r in results if r.success]),
                    "failed": len([r for r in results if not r.success]),
                    "total_execution_time_ms": sum(r.execution_time_ms for r in results)
                },
                "results": [asdict(r) for r in results]
            }
        }

        # Save YAML
        yaml_file = report_dir / f"{report_id}.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)

        # Save JSON
        json_file = report_dir / f"{report_id}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)

        self.log(f"\n✅ Execution report saved:")
        self.log(f"   YAML: {yaml_file}")
        self.log(f"   JSON: {json_file}")

        return yaml_file

    def print_summary(self, results: List[ExecutionResult]):
        """Print execution summary."""
        print("\n" + "="*60)
        print("EXECUTOR AGENT - IMPLEMENTATION SUMMARY")
        print("="*60)

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        print(f"\n📊 Execution Summary:")
        print(f"   Total tasks: {len(results)}")
        print(f"   ✅ Successful: {len(successful)}")
        print(f"   ❌ Failed: {len(failed)}")

        if successful:
            print(f"\n✅ Successful Implementations:")
            for r in successful:
                print(f"   • {r.task_id}: {r.action_taken}")
                if r.files_modified:
                    print(f"     Files: {', '.join(r.files_modified)}")

        if failed:
            print(f"\n❌ Failed Implementations:")
            for r in failed:
                print(f"   • {r.task_id}: {r.error_message or r.action_taken}")

        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Executor Agent - Implement quick wins"
    )
    parser.add_argument(
        "--task-id",
        type=str,
        help="Specific task ID to execute"
    )
    parser.add_argument(
        "--quick-wins",
        action="store_true",
        help="Execute all quick win tasks"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Limit number of quick wins to execute"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )

    args = parser.parse_args()

    # Initialize executor
    executor = ExecutorAgent(dry_run=args.dry_run)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")

    results = []

    if args.task_id:
        # Execute specific task
        result = executor.execute_task(args.task_id)
        results.append(result)
    elif args.quick_wins:
        # Execute all quick wins
        results = executor.execute_quick_wins(limit=args.limit)
    else:
        print("❌ Please specify --task-id or --quick-wins")
        return 1

    # Save execution report
    if results:
        executor.save_execution_report(results)
        executor.print_summary(results)

    return 0 if all(r.success for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
