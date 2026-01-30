"""
Supervisor Agent: Creates tasks and manages dependencies.

The Supervisor Agent is responsible for:
- Breaking down goals into concrete tasks
- Managing task dependencies
- Publishing tasks to Redis for agents to claim
- Never executes tasks itself (separation of concerns)
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..schemas.task import Task, TaskState, TaskRegistry
from ..redis.coordinator import RedisCoordinator


@dataclass
class TaskBreakdown:
    """Result of task breakdown"""
    tasks: List[Task]
    dependencies: Dict[str, List[str]]  # task_id -> [dep_ids]
    estimated_duration: Optional[int] = None  # minutes


class SupervisorAgent:
    """
    Supervisor Agent manages task creation and coordination.

    The Supervisor:
    1. Receives high-level goals
    2. Breaks down goals into concrete tasks
    3. Manages dependencies between tasks
    4. Publishes tasks to Redis for autonomous agents
    5. Tracks progress and resolves blockers
    """

    def __init__(self, task_registry: TaskRegistry,
                 redis_coordinator: RedisCoordinator,
                 agent_id: str = "supervisor"):
        """
        Initialize Supervisor Agent.

        Args:
            task_registry: Task registry for persistence
            redis_coordinator: Redis coordinator for pub/sub
            agent_id: Agent identifier
        """
        self.agent_id = agent_id
        self.registry = task_registry
        self.redis = redis_coordinator

        # Register supervisor
        self.redis.update_agent_status(
            agent_id=self.agent_id,
            status="idle",
            capabilities=["task_creation", "dependency_management", "coordination"]
        )

    def plan_goal(self, goal: str, context: Dict[str, Any] = None) -> TaskBreakdown:
        """
        Break down high-level goal into concrete tasks.

        Args:
            goal: High-level goal description
            context: Additional context for planning

        Returns:
            TaskBreakdown with tasks and dependencies
        """
        # This is where LLM integration would happen
        # For now, return a simple breakdown structure

        tasks = self._create_task_plan(goal, context)
        dependencies = self._resolve_dependencies(tasks)

        return TaskBreakdown(
            tasks=tasks,
            dependencies=dependencies
        )

    def _create_task_plan(self, goal: str,
                         context: Dict[str, Any]) -> List[Task]:
        """
        Create task plan from goal.

        In production, this would use an LLM to break down the goal.
        For now, return placeholder structure.
        """
        # Placeholder: Create a simple task
        task = Task(
            title=goal,
            description=f"Implement: {goal}",
            type="development",
            priority=5,
            state=TaskState.BACKLOG
        )

        return [task]

    def _resolve_dependencies(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """
        Resolve dependencies between tasks.

        Args:
            tasks: List of tasks

        Returns:
            Dictionary mapping task_id to list of dependency IDs
        """
        dependencies = {}

        for task in tasks:
            dependencies[task.id] = task.depends_on

        return dependencies

    def publish_tasks(self, tasks: List[Task]):
        """
        Publish tasks to Redis for agents to claim.

        Args:
            tasks: List of tasks to publish
        """
        for task in tasks:
            # Save to registry
            self.registry.create(
                title=task.title,
                description=task.description,
                type=task.type,
                priority=task.priority,
                depends_on=task.depends_on
            )

            # Move to pending state
            task.transition_to(TaskState.PENDING)

            # Add to Redis queue
            self.redis.add_to_pending_queue(task.id, task.priority)

            # Publish to channel
            self.redis.publish_task({
                "task_id": task.id,
                "title": task.title,
                "type": task.type,
                "priority": task.priority,
                "timestamp": datetime.now().isoformat()
            })

    def execute_goal(self, goal: str, context: Dict[str, Any] = None):
        """
        Execute a goal by breaking it down and publishing tasks.

        Args:
            goal: High-level goal to execute
            context: Additional context
        """
        # Update status
        self.redis.update_agent_status(
            agent_id=self.agent_id,
            status="busy",
            current_task=goal
        )

        try:
            # Break down goal
            breakdown = self.plan_goal(goal, context)

            # Publish tasks
            self.publish_tasks(breakdown.tasks)

            print(f"[{self.agent_id}] Published {len(breakdown.tasks)} tasks for goal: {goal}")

        finally:
            # Reset status
            self.redis.update_agent_status(
                agent_id=self.agent_id,
                status="idle"
            )

    def monitor_progress(self) -> Dict[str, Any]:
        """
        Monitor progress of all tasks.

        Returns:
            Progress statistics
        """
        all_tasks = self.registry.get_all()

        stats = {
            "total": len(all_tasks),
            "pending": 0,
            "assigned": 0,
            "active": 0,
            "done": 0,
            "failed": 0,
            "blocked": 0
        }

        blocked_tasks = []

        for task in all_tasks:
            state = task.state.value
            stats[state] = stats.get(state, 0) + 1

            # Check if blocked
            if task.depends_on:
                deps_satisfied = all(
                    self.registry.get(dep_id).state == TaskState.DONE
                    for dep_id in task.depends_on
                    if self.registry.get(dep_id)
                )

                if not deps_satisfied:
                    stats["blocked"] += 1
                    blocked_tasks.append(task.id)

        return stats

    def resolve_blockers(self):
        """
        Check for blocked tasks and publish when dependencies are satisfied.
        """
        all_tasks = self.registry.get_all()

        for task in all_tasks:
            if task.state == TaskState.BACKLOG:
                # Check if dependencies are satisfied
                deps_satisfied = all(
                    self.registry.get(dep_id).state == TaskState.DONE
                    for dep_id in task.depends_on
                    if self.registry.get(dep_id)
                )

                if deps_satisfied and not task.depends_on:
                    # Move to pending
                    task.transition_to(TaskState.PENDING)
                    self.registry.update(task)

                    # Publish to Redis
                    self.redis.add_to_pending_queue(task.id, task.priority)
                    self.redis.publish_task({
                        "task_id": task.id,
                        "title": task.title,
                        "type": task.type,
                        "priority": task.priority,
                        "timestamp": datetime.now().isoformat()
                    })

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed status of a task.

        Args:
            task_id: Task ID

        Returns:
            Task status dict or None
        """
        task = self.registry.get(task_id)

        if not task:
            return None

        return {
            "id": task.id,
            "title": task.title,
            "state": task.state.value,
            "assignee": task.assignee,
            "priority": task.priority,
            "depends_on": task.depends_on,
            "blocks": task.blocks,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    def shutdown(self):
        """Shutdown supervisor agent"""
        self.redis.update_agent_status(
            agent_id=self.agent_id,
            status="offline"
        )
