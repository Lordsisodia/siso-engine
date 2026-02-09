#!/usr/bin/env python3
"""
Vibe Kanban Management Skill

This skill enables a managerial agent to:
1. Create and manage Vibe Kanban tasks
2. Monitor agent progress across all workspaces
3. Coordinate merges and reviews
4. Track task dependencies and execution status
5. Provide real-time team oversight
"""

import requests
import json
import socket
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import subprocess
import os
from pathlib import Path


class TaskStatus(Enum):
    """Vibe Kanban task statuses"""
    TODO = "todo"
    IN_PROGRESS = "inprogress"
    IN_REVIEW = "inreview"
    DONE = "done"
    CANCELLED = "cancelled"


class Priority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class Repository:
    """Repository configuration"""
    repo_id: str
    base_branch: str = "main"
    path: Optional[str] = None


@dataclass
class TaskInfo:
    """Comprehensive task information"""
    id: str
    title: str
    status: TaskStatus
    created_at: str
    updated_at: str
    description: Optional[str] = None
    has_in_progress_attempt: bool = False
    last_attempt_failed: bool = False
    workspace_id: Optional[str] = None
    branch: Optional[str] = None
    executor: Optional[str] = None

    # Tracking fields
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    completion_estimate: Optional[str] = None

    # Review fields
    needs_review: bool = False
    review_notes: Optional[str] = None
    approved_for_merge: bool = False


@dataclass
class AgentState:
    """State of a running agent"""
    task_id: str
    task_title: str
    workspace_path: Optional[str] = None
    branch: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    started_at: Optional[str] = None
    last_activity: Optional[str] = None
    files_modified: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    completion_percentage: int = 0


@dataclass
class ManagementMetrics:
    """Team management metrics"""
    total_tasks: int = 0
    in_progress: int = 0
    in_review: int = 0
    completed: int = 0
    failed: int = 0
    blocked: int = 0

    # Time tracking
    avg_completion_time: Optional[float] = None
    estimated_time_remaining: Optional[float] = None

    # Quality metrics
    merge_success_rate: Optional[float] = None
    agent_success_rate: Optional[float] = None


class VibeKanbanManager:
    """
    Complete Vibe Kanban management interface for agents.

    This class provides all the tools a managerial agent needs to:
    - Create and organize tasks
    - Spawn and monitor agents
    - Track progress and status
    - Coordinate merges and reviews
    - Manage dependencies

    The manager automatically detects the Vibe Kanban server port if not specified.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        project_id: str = "48ec7737-b706-4817-b86c-5786163a0139",
        repo_id: str = "b5b86bc2-fbfb-4276-b15e-01496d647a81",
        repo_path: str = "/Users/shaansisodia/.blackbox5"
    ):
        """
        Initialize Vibe Kanban Manager

        Args:
            base_url: Vibe Kanban API URL (auto-detected if None)
            project_id: Project UUID
            repo_id: Default repository UUID
            repo_path: Local path to repository
        """
        if base_url is None:
            base_url = self._detect_vibe_kanban_url()

        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
        self.project_id = project_id
        self.repo_id = repo_id
        self.repo_path = Path(repo_path)

        # Tracking
        self._task_cache: Dict[str, TaskInfo] = {}
        self._agent_states: Dict[str, AgentState] = {}

    # =========================================================================
    # TASK MANAGEMENT
    # =========================================================================

    def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: Priority = Priority.NORMAL,
        dependencies: Optional[List[str]] = None
    ) -> TaskInfo:
        """
        Create a new task

        Args:
            title: Task title
            description: Task description (markdown)
            priority: Task priority
            dependencies: List of task IDs this depends on

        Returns:
            TaskInfo object
        """
        payload = {
            "project_id": self.project_id,
            "title": title
        }
        if description:
            payload["description"] = description

        result = self._api_call("POST", "/tasks", json=payload)
        task = TaskInfo(
            id=result["id"],
            title=title,
            status=TaskStatus(result["status"]),
            created_at=result.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=result.get("updated_at", datetime.now(timezone.utc).isoformat()),
            description=description,
            dependencies=dependencies or []
        )

        self._task_cache[task.id] = task
        return task

    def get_task(self, task_id: str) -> TaskInfo:
        """Get task details"""
        if task_id in self._task_cache:
            return self._task_cache[task_id]

        result = self._api_call("GET", f"/tasks/{task_id}")
        return self._parse_task(result)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[TaskInfo]:
        """List tasks in project"""
        params = {"project_id": self.project_id, "limit": limit}
        if status:
            params["status"] = status.value

        result = self._api_call("GET", "/tasks", params=params)
        tasks = [self._parse_task(t) for t in result]

        # Update cache
        for task in tasks:
            self._task_cache[task.id] = task

        return tasks

    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[TaskStatus] = None
    ) -> TaskInfo:
        """Update task"""
        payload = {}
        if title:
            payload["title"] = title
        if description:
            payload["description"] = description
        if status:
            payload["status"] = status.value

        result = self._api_call("PUT", f"/tasks/{task_id}", json=payload)
        return self._parse_task(result)

    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        try:
            self._api_call("DELETE", f"/tasks/{task_id}")
            if task_id in self._task_cache:
                del self._task_cache[task_id]
            return True
        except Exception as e:
            print(f"Failed to delete task {task_id}: {e}")
            return False

    # =========================================================================
    # AGENT EXECUTION
    # =========================================================================

    def start_agent(
        self,
        task_id: str,
        executor: str = "CLAUDE_CODE",
        repos: Optional[List[Repository]] = None,
        branch: Optional[str] = None
    ) -> AgentState:
        """
        Start an agent working on a task

        Args:
            task_id: Task UUID
            executor: Executor type (CLAUDE_CODE, AMP, etc.)
            repos: List of repositories to work with
            branch: Branch name (auto-generated if None)

        Returns:
            AgentState object
        """
        task = self.get_task(task_id)

        if not repos:
            branch = branch or self._generate_branch_name(task.title)
            repos = [Repository(repo_id=self.repo_id, base_branch=branch)]

        payload = {
            "task_id": task_id,
            "executor_profile_id": {
                "executor": executor,
                "variant": None
            },
            "repos": [
                {
                    "repo_id": repo.repo_id,
                    "target_branch": repo.base_branch
                }
                for repo in repos
            ]
        }

        result = self._api_call("POST", "/task-attempts", json=payload)

        agent_state = AgentState(
            task_id=task_id,
            task_title=task.title,
            workspace_path=result.get("workspace_path"),
            branch=branch,
            status=TaskStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc).isoformat(),
            last_activity=datetime.now(timezone.utc).isoformat()
        )

        self._agent_states[task_id] = agent_state
        return agent_state

    def spawn_parallel_agents(
        self,
        tasks: List[Tuple[str, str]],  # List of (task_id, executor) tuples
        wait_between: float = 1.0
    ) -> List[AgentState]:
        """
        Spawn multiple agents in parallel

        Args:
            tasks: List of (task_id, executor) tuples
            wait_between: Seconds to wait between spawns

        Returns:
            List of AgentState objects
        """
        agents = []
        for task_id, executor in tasks:
            agent = self.start_agent(task_id, executor)
            agents.append(agent)
            import time
            time.sleep(wait_between)

        return agents

    # =========================================================================
    # MONITORING & STATUS
    # =========================================================================

    def get_task_status(self, task_id: str) -> TaskStatus:
        """Get current task status"""
        task = self.get_task(task_id)
        return task.status

    def monitor_task(
        self,
        task_id: str,
        poll_interval: int = 5,
        timeout: int = 7200,
        callback: Optional[callable] = None
    ) -> TaskInfo:
        """
        Monitor a task until completion

        Args:
            task_id: Task UUID
            poll_interval: Seconds between checks
            timeout: Maximum seconds to wait
            callback: Optional callback(status, task)

        Returns:
            Final TaskInfo
        """
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            task = self.get_task(task_id)

            if callback:
                callback(task.status, task)

            # Check completion
            if task.status in [TaskStatus.IN_REVIEW, TaskStatus.DONE]:
                return task
            elif task.last_attempt_failed:
                raise RuntimeError(f"Task {task_id} failed")

            time.sleep(poll_interval)

        raise TimeoutError(f"Task {task_id} did not complete in {timeout}s")

    def get_all_agent_states(self) -> Dict[str, AgentState]:
        """Get states of all tracked agents"""
        # Refresh from current tasks
        tasks = self.list_tasks()
        for task in tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                if task.id not in self._agent_states:
                    self._agent_states[task.id] = AgentState(
                        task_id=task.id,
                        task_title=task.title,
                        status=task.status
                    )
                self._agent_states[task.id].status = task.status
                self._agent_states[task.id].last_activity = task.updated_at

        return self._agent_states

    # =========================================================================
    # MERGE & REVIEW COORDINATION
    # =========================================================================

    def get_workspace_changes(self, task_id: str) -> Dict[str, Any]:
        """
        Get changes made in a task's workspace

        Returns dict with:
        - branch: branch name
        - files_modified: list of modified files
        - files_created: list of new files
        - diff: git diff output
        - commit_info: commit information
        """
        task = self.get_task(task_id)
        agent_state = self._agent_states.get(task_id)

        if not agent_state or not agent_state.branch:
            raise ValueError(f"No branch found for task {task_id}")

        # Find workspace
        workspace_path = self._find_workspace(agent_state.branch)
        if not workspace_path:
            raise ValueError(f"Workspace not found for branch {agent_state.branch}")

        os.chdir(workspace_path)

        # Get changes
        result = {
            "branch": agent_state.branch,
            "workspace_path": workspace_path,
            "files_modified": [],
            "files_created": [],
            "diff": "",
            "commits": []
        }

        # Get modified files
        try:
            status_output = subprocess.check_output(
                ["git", "status", "--porcelain"],
                text=True
            )
            for line in status_output.strip().split('\n'):
                if line:
                    status, filepath = line[:3], line[3:]
                    if 'M' in status:
                        result["files_modified"].append(filepath)
                    if '??' in status:
                        result["files_created"].append(filepath)
        except Exception as e:
            result["errors"] = [f"git status failed: {e}"]

        # Get diff
        try:
            result["diff"] = subprocess.check_output(
                ["git", "diff", "main"],
                text=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Get commits
        try:
            commit_output = subprocess.check_output(
                ["git", "log", "--oneline", "main..HEAD"],
                text=True
            )
            result["commits"] = commit_output.strip().split('\n')
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return result

    def review_task(self, task_id: str) -> Dict[str, Any]:
        """
        Review a completed task

        Returns:
            Dict with review findings
        """
        changes = self.get_workspace_changes(task_id)
        task = self.get_task(task_id)

        return {
            "task_id": task_id,
            "task_title": task.title,
            "approved": False,
            "notes": "",
            "changes": changes,
            "recommendations": []
        }

    def merge_task(
        self,
        task_id: str,
        merge_method: str = "merge"
    ) -> bool:
        """
        Merge a completed task

        Args:
            task_id: Task UUID
            merge_method: "merge", "squash", or "rebase"

        Returns:
            True if successful
        """
        agent_state = self._agent_states.get(task_id)
        if not agent_state or not agent_state.branch:
            raise ValueError(f"No branch found for task {task_id}")

        workspace_path = self._find_workspace(agent_state.branch)
        if not workspace_path:
            raise ValueError(f"Workspace not found for branch {agent_state.branch}")

        os.chdir(workspace_path)

        try:
            # Commit any uncommitted changes
            subprocess.run(["git", "add", "-A"], check=True)
            subprocess.run(
                ["git", "commit", "-m", f"Complete {agent_state.task_title}"],
                check=True
            )

            # Switch to main
            os.chdir(self.repo_path)
            subprocess.run(["git", "checkout", "main"], check=True)

            # Merge
            if merge_method == "merge":
                subprocess.run(
                    ["git", "merge", agent_state.branch, "--no-ff"],
                    check=True
                )
            elif merge_method == "squash":
                subprocess.run(
                    ["git", "merge", "--squash", agent_state.branch],
                    check=True
                )
                subprocess.run(
                    ["git", "commit", "-m", f"Squash merge {agent_state.task_title}"],
                    check=True
                )

            return True
        except subprocess.CalledProcessError as e:
            print(f"Merge failed: {e}")
            return False

    # =========================================================================
    # DEPENDENCY MANAGEMENT
    # =========================================================================

    def set_dependencies(self, task_id: str, depends_on: List[str]) -> bool:
        """Set task dependencies"""
        task = self.get_task(task_id)
        task.dependencies = depends_on
        return True

    def get_blockers(self, task_id: str) -> List[str]:
        """Get tasks blocking this task"""
        task = self.get_task(task_id)
        blockers = []

        for dep_id in task.dependencies:
            dep_task = self.get_task(dep_id)
            if dep_task.status not in [TaskStatus.DONE, TaskStatus.CANCELLED]:
                blockers.append(dep_id)

        return blockers

    def get_dependents(self, task_id: str) -> List[str]:
        """Get tasks that depend on this task"""
        dependents = []
        for t in self.list_tasks():
            if task_id in t.dependencies:
                dependents.append(t.id)
        return dependents

    def can_start(self, task_id: str) -> bool:
        """Check if task can start (no uncompleted dependencies)"""
        return len(self.get_blockers(task_id)) == 0

    # =========================================================================
    # METRICS & REPORTING
    # =========================================================================

    def get_metrics(self) -> ManagementMetrics:
        """Get team management metrics"""
        tasks = self.list_tasks()

        metrics = ManagementMetrics(
            total_tasks=len(tasks)
        )

        for task in tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                metrics.in_progress += 1
            elif task.status == TaskStatus.IN_REVIEW:
                metrics.in_review += 1
            elif task.status == TaskStatus.DONE:
                metrics.completed += 1
            elif task.last_attempt_failed:
                metrics.failed += 1

            if self.get_blockers(task.id):
                metrics.blocked += 1

        return metrics

    def generate_report(self) -> str:
        """Generate management report"""
        metrics = self.get_metrics()
        agents = self.get_all_agent_states()

        report = [
            "# BlackBox5 Team Management Report",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "## Metrics",
            f"- Total Tasks: {metrics.total_tasks}",
            f"- In Progress: {metrics.in_progress}",
            f"- In Review: {metrics.in_review}",
            f"- Completed: {metrics.completed}",
            f"- Failed: {metrics.failed}",
            f"- Blocked: {metrics.blocked}",
            "",
            "## Active Agents",
        ]

        for task_id, agent in agents.items():
            report.append(f"- {agent.task_title} ({agent.status.value})")

        report.append("")
        report.append("## Tasks Awaiting Review")

        for task in self.list_tasks(status=TaskStatus.IN_REVIEW):
            report.append(f"- {task.title}")

        report.append("")
        report.append("## Blocked Tasks")

        for task in self.list_tasks():
            blockers = self.get_blockers(task.id)
            if blockers:
                blocker_names = [self.get_task(b).title for b in blockers]
                report.append(f"- {task.title} (blocked by: {', '.join(blocker_names)})")

        return "\n".join(report)

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    @staticmethod
    def _detect_vibe_kanban_url() -> str:
        """
        Auto-detect Vibe Kanban server URL by finding the listening port.

        Vibe Kanban uses a random port on each start. This method finds the
        process and determines its listening port.

        Returns:
            URL like "http://127.0.0.1:58842"

        Raises:
            RuntimeError: If Vibe Kanban server is not running
        """
        # Method 1: Use lsof to find vibe-kanban listening port
        try:
            result = subprocess.run(
                ['lsof', '-nP', '-iTCP', '-sTCP:LISTEN'],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.splitlines():
                if 'vibe-kanb' in line.lower():
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'TCP' in part:
                            # Format: 127.0.0.1:58842 (LISTEN)
                            port = parts[i+1].split(':')[-1].split(' ')[0]
                            return f"http://127.0.0.1:{port}"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Method 2: Check common port range for Vibe Kanban
        for port in range(3000, 3010):
            try:
                test_url = f"http://127.0.0.1:{port}/api/projects"
                r = requests.get(test_url, timeout=1)
                if r.status_code == 200:
                    return f"http://127.0.0.1:{port}"
            except requests.RequestException:
                continue

        # Method 3: Check wider port range (Vibe Kanban sometimes uses higher ports)
        for port in range(58000, 59000):
            try:
                test_url = f"http://127.0.0.1:{port}/api/projects"
                r = requests.get(test_url, timeout=0.2)
                if r.status_code == 200:
                    return f"http://127.0.0.1:{port}"
            except requests.RequestException:
                continue

        raise RuntimeError(
            "Vibe Kanban server not found. Please start it with: vibe-kanban start"
        )

    def _api_call(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API call"""
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json().get("data", response.json())

    def _parse_task(self, data: Dict[str, Any]) -> TaskInfo:
        """Parse task data from API"""
        return TaskInfo(
            id=data["id"],
            title=data["title"],
            status=TaskStatus(data["status"]),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            description=data.get("description"),
            has_in_progress_attempt=data.get("has_in_progress_attempt", False),
            last_attempt_failed=data.get("last_attempt_failed", False)
        )

    def _generate_branch_name(self, title: str) -> str:
        """Generate branch name from task title"""
        # Extract identifier (e.g., "PLAN-008" from "PLAN-008: Fix API")
        parts = title.split(":")
        identifier = parts[0].strip().lower().replace(" ", "-").replace("_", "-")
        return f"bb5/{identifier}"

    def _find_workspace(self, branch: str) -> Optional[str]:
        """Find workspace path for branch"""
        # Check common workspace locations
        locations = [
            f"/tmp/bb5-wave0/{branch.replace('bb5/', '')}",
            f"/var/folders/_g/n9v_ywr5173f74ywkzf843vr0000gn/T/vibe-kanban/worktrees/*-{branch[:20]}"
        ]

        for loc in locations:
            if os.path.exists(loc):
                return loc

        return None


# =============================================================================
# CONVENIENCE FUNCTIONS FOR AGENTS
# =============================================================================

def create_manager(
    project_id: str = "48ec7737-b706-4817-b86c-5786163a0139",
    repo_id: str = "b5b86bc2-fbfb-4276-b15e-01496d647a81"
) -> VibeKanbanManager:
    """Create a Vibe Kanban manager instance"""
    return VibeKanbanManager(project_id=project_id, repo_id=repo_id)


def quick_status() -> str:
    """Get quick status of all tasks"""
    manager = create_manager()
    return manager.generate_report()


if __name__ == "__main__":
    # Example: Generate management report
    print(quick_status())
