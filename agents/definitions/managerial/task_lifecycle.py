#!/usr/bin/env python3
"""
Task Lifecycle Management for BlackBox5 Managerial Agent

This module provides complete workflows for managing tasks through their
entire lifecycle:
1. Planning and task creation
2. Agent assignment and execution
3. Monitoring and checkpointing
4. Review and quality assurance
5. Merge and integration
6. Cleanup and archival
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time

from .skills.vibe_kanban_manager import (
    VibeKanbanManager,
    TaskInfo,
    TaskStatus,
    Priority,
    AgentState
)
from .memory.management_memory import (
    ManagementMemory,
    EventType,
    get_management_memory
)


class LifecycleStage(Enum):
    """Task lifecycle stages"""
    PLANNING = "planning"
    CREATED = "created"
    ASSIGNED = "assigned"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    MERGED = "merged"
    ARCHIVED = "archived"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskPlan:
    """A plan for a task"""
    title: str
    description: str
    priority: Priority
    estimated_duration: Optional[int] = None  # minutes
    dependencies: Optional[List[str]] = None
    executor: str = "CLAUDE_CODE"
    branch: Optional[str] = None
    requires_review: bool = True
    merge_method: str = "merge"


@dataclass
class ExecutionResult:
    """Result of task execution"""
    task_id: str
    success: bool
    duration: float
    files_modified: int
    files_created: int
    errors: List[str]
    workspace_path: Optional[str] = None
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    quality_score: Optional[float] = None


class TaskLifecycleManager:
    """
    Complete task lifecycle management.

    This class orchestrates the entire life of a task from creation
    to archival, with full tracking and memory persistence.
    """

    def __init__(
        self,
        vkb_manager: Optional[VibeKanbanManager] = None,
        memory: Optional[ManagementMemory] = None
    ):
        """
        Initialize lifecycle manager

        Args:
            vkb_manager: Vibe Kanban manager instance
            memory: Management memory instance
        """
        self.vkb = vkb_manager or VibeKanbanManager()
        self.memory = memory or get_management_memory()

    # =========================================================================
    # PLANNING STAGE
    # =========================================================================

    def plan_task(
        self,
        title: str,
        description: str,
        priority: Priority = Priority.NORMAL,
        dependencies: Optional[List[str]] = None,
        estimated_duration: Optional[int] = None
    ) -> TaskPlan:
        """
        Create a plan for a task

        Args:
            title: Task title
            description: Task description
            priority: Task priority
            dependencies: List of task IDs this depends on
            estimated_duration: Estimated duration in minutes

        Returns:
            TaskPlan object
        """
        plan = TaskPlan(
            title=title,
            description=description,
            priority=priority,
            dependencies=dependencies,
            estimated_duration=estimated_duration
        )

        # Record planning event
        self.memory.record_event(
            EventType.TASK_CREATED,
            task_title=title,
            priority=priority.value,
            dependencies=dependencies or [],
            estimated_duration=estimated_duration
        )

        return plan

    def plan_wave(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[TaskPlan]:
        """
        Plan a wave of parallel tasks

        Args:
            tasks: List of task dicts with keys:
                - title, description, priority, dependencies

        Returns:
            List of TaskPlan objects
        """
        plans = []
        for task_dict in tasks:
            plan = self.plan_task(
                title=task_dict["title"],
                description=task_dict["description"],
                priority=task_dict.get("priority", Priority.NORMAL),
                dependencies=task_dict.get("dependencies"),
                estimated_duration=task_dict.get("estimated_duration")
            )
            plans.append(plan)

        return plans

    # =========================================================================
    # CREATION STAGE
    # =========================================================================

    def create_task(self, plan: TaskPlan) -> TaskInfo:
        """
        Create a task from plan

        Args:
            plan: TaskPlan object

        Returns:
            TaskInfo object
        """
        task = self.vkb.create_task(
            title=plan.title,
            description=plan.description,
            priority=plan.priority
        )

        # Set dependencies
        if plan.dependencies:
            for dep_id in plan.dependencies:
                self.memory.add_dependency(task.id, dep_id)

        # Create task history
        self.memory.create_task_history(
            task_id=task.id,
            title=task.title
        )

        # Record event
        self.memory.record_event(
            EventType.TASK_CREATED,
            task_id=task.id,
            task_title=task.title
        )

        return task

    def create_wave(self, plans: List[TaskPlan]) -> List[TaskInfo]:
        """
        Create multiple tasks from plans

        Args:
            plans: List of TaskPlan objects

        Returns:
            List of TaskInfo objects
        """
        tasks = []
        for plan in plans:
            # Check if dependencies are satisfied
            if plan.dependencies:
                can_create = all(
                    self.vkb.get_task(dep_id).status == TaskStatus.DONE
                    for dep_id in plan.dependencies
                )
                if not can_create:
                    print(f"Skipping {plan.title} - dependencies not met")
                    continue

            task = self.create_task(plan)
            tasks.append(task)

        return tasks

    # =========================================================================
    # ASSIGNMENT & EXECUTION STAGE
    # =========================================================================

    def assign_and_start(
        self,
        task: TaskInfo,
        executor: str = "CLAUDE_CODE"
    ) -> AgentState:
        """
        Assign task to agent and start execution

        Args:
            task: TaskInfo object
            executor: Executor type

        Returns:
            AgentState object
        """
        # Check blockers
        blockers = self.memory.get_blockers(task.id)
        if blockers:
            raise RuntimeError(
                f"Task {task.id} is blocked by: {blockers}"
            )

        # Start agent
        agent = self.vkb.start_agent(
            task_id=task.id,
            executor=executor,
            branch=self.vkb._generate_branch_name(task.title)
        )

        # Track agent performance
        self.memory.track_agent_start(task.id, executor)

        # Record event
        self.memory.record_event(
            EventType.AGENT_SPAWNED,
            task_id=task.id,
            task_title=task.title,
            executor=executor,
            workspace_path=agent.workspace_path
        )

        return agent

    def start_wave(
        self,
        tasks: List[TaskInfo],
        executor: str = "CLAUDE_CODE",
        wait_between: float = 1.0
    ) -> List[AgentState]:
        """
        Start multiple agents in parallel

        Args:
            tasks: List of TaskInfo objects
            executor: Executor type
            wait_between: Seconds between spawns

        Returns:
            List of AgentState objects
        """
        agents = []

        # Filter tasks that can start
        ready_tasks = [
            task for task in tasks
            if self.vkb.can_start(task.id)
        ]

        print(f"Starting {len(ready_tasks)} agents (out of {len(tasks)} tasks)")

        for task in ready_tasks:
            try:
                agent = self.assign_and_start(task, executor)
                agents.append(agent)
                time.sleep(wait_between)
            except Exception as e:
                print(f"Failed to start agent for {task.title}: {e}")
                self.memory.record_event(
                    EventType.AGENT_FAILED,
                    task_id=task.id,
                    task_title=task.title,
                    error=str(e)
                )

        return agents

    # =========================================================================
    # MONITORING STAGE
    # =========================================================================

    def monitor_task(
        self,
        task_id: str,
        poll_interval: int = 10,
        timeout: int = 7200,
        on_progress: Optional[callable] = None
    ) -> ExecutionResult:
        """
        Monitor task execution to completion

        Args:
            task_id: Task UUID
            poll_interval: Seconds between checks
            timeout: Maximum seconds to wait
            on_progress: Callback(status, task_info)

        Returns:
            ExecutionResult object
        """
        start_time = time.time()
        task = self.vkb.get_task(task_id)

        while time.time() - start_time < timeout:
            task = self.vkb.get_task(task_id)

            # Call progress callback
            if on_progress:
                on_progress(task.status, task)

            # Check completion
            if task.status == TaskStatus.IN_REVIEW:
                # Agent finished successfully
                return self._complete_execution(task_id, success=True)
            elif task.status == TaskStatus.DONE:
                # Task marked as done
                return self._complete_execution(task_id, success=True)
            elif task.last_attempt_failed:
                # Agent failed
                return self._complete_execution(task_id, success=False)

            time.sleep(poll_interval)

        # Timeout
        return self._complete_execution(task_id, success=False)

    def monitor_wave(
        self,
        task_ids: List[str],
        poll_interval: int = 10,
        timeout: int = 7200
    ) -> Dict[str, ExecutionResult]:
        """
        Monitor multiple tasks in parallel

        Args:
            task_ids: List of task UUIDs
            poll_interval: Seconds between checks
            timeout: Maximum seconds to wait

        Returns:
            Dict mapping task_id to ExecutionResult
        """
        results = {}
        pending = set(task_ids)

        start_time = time.time()

        while pending and time.time() - start_time < timeout:
            for task_id in list(pending):
                task = self.vkb.get_task(task_id)

                if task.status in [TaskStatus.IN_REVIEW, TaskStatus.DONE]:
                    results[task_id] = self._complete_execution(task_id, success=True)
                    pending.remove(task_id)
                elif task.last_attempt_failed:
                    results[task_id] = self._complete_execution(task_id, success=False)
                    pending.remove(task_id)

            # Print status
            print(f"Progress: {len(results)}/{len(task_ids)} completed, {len(pending)} pending")

            if pending:
                time.sleep(poll_interval)

        return results

    def _complete_execution(self, task_id: str, success: bool) -> ExecutionResult:
        """Complete task execution and gather results"""
        task = self.vkb.get_task(task_id)

        # Get workspace changes
        try:
            changes = self.vkb.get_workspace_changes(task_id)
            files_modified = len(changes.get("files_modified", []))
            files_created = len(changes.get("files_created", []))
        except (KeyError, OSError, ValueError):
            files_modified = 0
            files_created = 0

        # Record completion
        self.memory.track_agent_completion(
            task_id=task_id,
            success=success,
            files_modified=files_modified,
            files_created=files_created
        )

        # Record event
        event_type = EventType.AGENT_COMPLETED if success else EventType.AGENT_FAILED
        self.memory.record_event(
            event_type,
            task_id=task_id,
            task_title=task.title,
            files_modified=files_modified,
            files_created=files_created
        )

        return ExecutionResult(
            task_id=task_id,
            success=success,
            duration=0.0,  # Would be calculated from timestamps
            files_modified=files_modified,
            files_created=files_created,
            errors=[]
        )

    # =========================================================================
    # REVIEW STAGE
    # =========================================================================

    def request_review(self, task_id: str) -> Dict[str, Any]:
        """
        Request review of completed task

        Args:
            task_id: Task UUID

        Returns:
            Review data dict
        """
        review = self.vkb.review_task(task_id)

        self.memory.record_event(
            EventType.REVIEW_REQUESTED,
            task_id=task_id,
            task_title=review.get("task_title")
        )

        return review

    def approve_task(
        self,
        task_id: str,
        review_notes: Optional[str] = None
    ):
        """Approve task for merge"""
        task = self.vkb.get_task(task_id)

        self.memory.record_event(
            EventType.REVIEW_COMPLETED,
            task_id=task_id,
            task_title=task.title,
            approved=True,
            notes=review_notes
        )

    def reject_task(
        self,
        task_id: str,
        reason: str
    ):
        """Reject task, requiring rework"""
        task = self.vkb.get_task(task_id)

        self.memory.record_event(
            EventType.REVIEW_COMPLETED,
            task_id=task_id,
            task_title=task.title,
            approved=False,
            reason=reason
        )

    # =========================================================================
    # MERGE STAGE
    # =========================================================================

    def merge_task(
        self,
        task_id: str,
        merge_method: str = "merge"
    ) -> bool:
        """
        Merge completed task

        Args:
            task_id: Task UUID
            merge_method: "merge", "squash", or "rebase"

        Returns:
            True if successful
        """
        task = self.vkb.get_task(task_id)
        agent_state = self.vkb._agent_states.get(task_id)

        if not agent_state or not agent_state.branch:
            print(f"No branch found for task {task_id}")
            return False

        # Record attempt
        self.memory.record_merge_attempt(
            task_id,
            agent_state.branch,
            merge_method
        )

        # Attempt merge
        try:
            success = self.vkb.merge_task(task_id, merge_method)

            if success:
                # Get commit hash
                import subprocess
                import os
                os.chdir(self.vkb.repo_path)
                commit_hash = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    text=True
                ).strip()

                self.memory.record_merge_success(task_id, commit_hash)

                # Mark task as done
                self.vkb.update_task(task_id, status=TaskStatus.DONE)

                # Complete task in memory
                self.memory.complete_task(task_id, "merged")

                return True
            else:
                self.memory.record_merge_failure(
                    task_id,
                    "Merge command failed"
                )
                return False

        except Exception as e:
            self.memory.record_merge_failure(task_id, str(e))
            return False

    def merge_wave(
        self,
        task_ids: List[str],
        merge_method: str = "merge"
    ) -> Dict[str, bool]:
        """
        Merge multiple completed tasks

        Args:
            task_ids: List of task UUIDs
            merge_method: Merge method

        Returns:
            Dict mapping task_id to success status
        """
        results = {}

        for task_id in task_ids:
            task = self.vkb.get_task(task_id)

            # Only merge if in review
            if task.status == TaskStatus.IN_REVIEW:
                success = self.merge_task(task_id, merge_method)
                results[task_id] = success
            else:
                print(f"Skipping {task.title} - not ready for merge")
                results[task_id] = False

        return results

    # =========================================================================
    # CLEANUP STAGE
    # =========================================================================

    def archive_task(self, task_id: str):
        """Archive completed task"""
        # Mark as archived in memory
        task_history = self.memory.get_task_history(task_id)
        if task_history:
            # Could move to archival storage
            pass

        self.memory.record_event(
            EventType.TASK_COMPLETED,
            task_id=task_id,
            archived=True
        )

    # =========================================================================
    # COMPLETE WORKFLOWS
    # =========================================================================

    def execute_single_task(
        self,
        plan: TaskPlan,
        executor: str = "CLAUDE_CODE",
        auto_merge: bool = True
    ) -> ExecutionResult:
        """
        Execute a single task from plan to completion

        Args:
            plan: TaskPlan
            executor: Executor type
            auto_merge: Whether to auto-merge on completion

        Returns:
            ExecutionResult
        """
        # Create
        task = self.create_task(plan)
        print(f"Created task: {task.title}")

        # Start
        agent = self.assign_and_start(task, executor)
        print(f"Started agent on branch: {agent.branch}")

        # Monitor
        print("Monitoring execution...")
        result = self.monitor_task(task.id)

        if result.success:
            print(f"✅ Task completed successfully")

            # Review
            review = self.request_review(task.id)
            print(f"Files modified: {result.files_modified}")
            print(f"Files created: {result.files_created}")

            # Merge
            if auto_merge:
                print("Attempting merge...")
                if self.merge_task(task.id):
                    print(f"✅ Merged successfully")
                else:
                    print(f"❌ Merge failed")
        else:
            print(f"❌ Task failed")

        return result

    def execute_wave(
        self,
        plans: List[TaskPlan],
        executor: str = "CLAUDE_CODE",
        auto_merge: bool = True
    ) -> Dict[str, ExecutionResult]:
        """
        Execute a wave of parallel tasks

        Args:
            plans: List of TaskPlan objects
            executor: Executor type
            auto_merge: Whether to auto-merge on completion

        Returns:
            Dict mapping task_id to ExecutionResult
        """
        # Create all tasks
        print("Creating tasks...")
        tasks = self.create_wave(plans)
        print(f"Created {len(tasks)} tasks")

        # Start all agents
        print("Starting agents...")
        agents = self.start_wave(tasks, executor)
        print(f"Started {len(agents)} agents")

        # Monitor all
        print("Monitoring execution...")
        task_ids = [t.id for t in tasks]
        results = self.monitor_wave(task_ids)

        # Report results
        successful = sum(1 for r in results.values() if r.success)
        print(f"\n🎉 Wave complete: {successful}/{len(results)} successful")

        # Merge successful tasks
        if auto_merge:
            successful_ids = [
                tid for tid, result in results.items()
                if result.success
            ]
            print(f"\nMerging {len(successful_ids)} tasks...")
            merge_results = self.merge_wave(successful_ids)

            merged = sum(1 for success in merge_results.values() if success)
            print(f"✅ Merged {merged}/{len(successful_ids)} tasks")

        return results


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_lifecycle_manager() -> TaskLifecycleManager:
    """Get the lifecycle manager singleton"""
    return TaskLifecycleManager()


if __name__ == "__main__":
    # Example: Execute a single task
    manager = get_lifecycle_manager()

    plan = manager.plan_task(
        title="PLAN-008: Fix Critical API Mismatches",
        description="Fix API parameter mismatches in main.py",
        priority=Priority.CRITICAL,
        estimated_duration=120
    )

    result = manager.execute_single_task(plan)
    print(f"Result: {result}")
