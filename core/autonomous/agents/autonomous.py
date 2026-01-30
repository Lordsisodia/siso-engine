"""
Autonomous Agent: Claims and executes tasks.

Autonomous agents:
- Subscribe to Redis task channels
- Claim available tasks based on capabilities
- Execute tasks independently
- Report status and results
- Handle retries and failures
"""

import asyncio
import signal
import sys
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import threading

from ..schemas.task import Task, TaskState, TaskRegistry
from ..redis.coordinator import RedisCoordinator


class AutonomousAgent:
    """
    Autonomous agent that claims and executes tasks.

    The agent runs an OODA loop:
    1. OBSERVE: Check for available tasks
    2. ORIENT: Understand task requirements
    3. DECIDE: Choose to claim task
    4. ACT: Execute the task
    5. CHECK: Report results and update state
    """

    def __init__(self,
                 agent_id: str,
                 capabilities: List[str],
                 task_registry: TaskRegistry,
                 redis_coordinator: RedisCoordinator,
                 execute_fn: Optional[Callable[[Task], Dict[str, Any]]] = None):
        """
        Initialize Autonomous Agent.

        Args:
            agent_id: Unique agent identifier
            capabilities: List of task types this agent can handle
            task_registry: Task registry for persistence
            redis_coordinator: Redis coordinator for coordination
            execute_fn: Function to execute tasks (defaults to mock)
        """
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.registry = task_registry
        self.redis = redis_coordinator
        self.execute_fn = execute_fn or self._default_execute

        self.running = False
        self.current_task: Optional[Task] = None

        # Register with Redis
        self.redis.update_agent_status(
            agent_id=self.agent_id,
            status="idle",
            capabilities=self.capabilities
        )

        # Subscribe to task channels
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        """Subscribe to Redis task channels"""
        self.redis.subscribe(
            RedisCoordinator.CHANNEL_TASK_NEW,
            callback=self._on_task_new
        )

        self.redis.subscribe(
            RedisCoordinator.CHANNEL_TASK_COMPLETE,
            callback=self._on_task_complete
        )

    def _on_task_new(self, data: Dict[str, Any]):
        """
        Handle new task notification.

        Args:
            data: Task notification data
        """
        task_id = data.get("task_id")

        # Check if we can handle this task
        task_type = data.get("type")
        if task_type in self.capabilities:
            # Try to claim it
            self._try_claim_task(task_id)

    def _on_task_complete(self, data: Dict[str, Any]):
        """
        Handle task completion notification.

        Check if any of our dependencies are now satisfied.

        Args:
            data: Task completion data
        """
        task_id = data.get("task_id")

        # Check if we have tasks waiting on this
        if self.current_task and task_id in self.current_task.depends_on:
            # Dependencies satisfied, can proceed
            pass

    def _try_claim_task(self, task_id: str) -> bool:
        """
        Attempt to claim a task.

        Args:
            task_id: Task ID to claim

        Returns:
            True if successfully claimed
        """
        # Get task from registry
        task = self.registry.get(task_id)

        if not task:
            return False

        # Check if we can handle this task type
        if task.type not in self.capabilities:
            return False

        # Check if dependencies are satisfied
        if task.depends_on:
            deps_satisfied = all(
                self.registry.get(dep_id).state == TaskState.DONE
                for dep_id in task.depends_on
                if self.registry.get(dep_id)
            )

            if not deps_satisfied:
                return False

        # Try atomic claim
        claimed = self.redis.claim_task_atomic(task_id, self.agent_id)

        if claimed:
            # Update task in registry
            task.transition_to(TaskState.ASSIGNED)
            task.assignee = self.agent_id
            task.assigned_at = datetime.now()
            self.registry.update(task)

            # Log event
            self.redis.log_event(task_id, "claimed", {
                "agent": self.agent_id,
                "timestamp": datetime.now().isoformat()
            })

            # Execute task
            self._execute_task(task)

            return True

        return False

    def _execute_task(self, task: Task):
        """
        Execute a claimed task.

        Args:
            task: Task to execute
        """
        self.current_task = task

        # Update status
        self.redis.update_agent_status(
            agent_id=self.agent_id,
            status="busy",
            current_task=task.id
        )

        # Transition to active
        task.transition_to(TaskState.ACTIVE)
        task.started_at = datetime.now()
        self.registry.update(task)

        try:
            # Execute task
            result = self.execute_fn(task)

            # Mark complete
            task.transition_to(TaskState.DONE)
            task.completed_at = datetime.now()
            task.result = result
            self.registry.update(task)

            # Publish completion
            self.redis.complete_task(task.id, result)

            # Log success
            self.redis.log_event(task.id, "completed", {
                "agent": self.agent_id,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            # Handle failure
            error_msg = str(e)

            task.transition_to(TaskState.FAILED)
            task.add_error(error_msg)
            self.registry.update(task)

            # Publish failure
            self.redis.fail_task(task.id, error_msg)

            # Log failure
            self.redis.log_event(task.id, "failed", {
                "agent": self.agent_id,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            })

        finally:
            # Reset status
            self.current_task = None
            self.redis.update_agent_status(
                agent_id=self.agent_id,
                status="idle"
            )

    def _default_execute(self, task: Task) -> Dict[str, Any]:
        """
        Default task execution (mock implementation).

        In production, this would be replaced with actual execution logic.

        Args:
            task: Task to execute

        Returns:
            Execution result
        """
        # Mock execution
        return {
            "status": "success",
            "message": f"Task {task.id} executed by {self.agent_id}",
            "artifacts": []
        }

    def start(self):
        """Start the autonomous agent loop"""
        self.running = True

        # Look for available tasks
        self._look_for_work()

    def _look_for_work(self):
        """Look for available tasks to claim"""
        if not self.running:
            return

        # Get available tasks
        available = self.registry.get_available(self.agent_id, self.capabilities)

        for task in available:
            if not self.running:
                break

            # Try to claim
            if self._try_claim_task(task.id):
                # Working on task, will look for more when done
                return

    def stop(self):
        """Stop the autonomous agent"""
        self.running = False

        # Update status
        self.redis.update_agent_status(
            agent_id=self.agent_id,
            status="offline"
        )


class AutonomousAgentPool:
    """
    Pool of autonomous agents.

    Manages multiple agents with different capabilities.
    """

    def __init__(self,
                 task_registry: TaskRegistry,
                 redis_coordinator: RedisCoordinator):
        """
        Initialize agent pool.

        Args:
            task_registry: Task registry
            redis_coordinator: Redis coordinator
        """
        self.registry = task_registry
        self.redis = redis_coordinator
        self.agents: Dict[str, AutonomousAgent] = {}

    def add_agent(self, agent_id: str, capabilities: List[str],
                  execute_fn: Callable = None):
        """
        Add an agent to the pool.

        Args:
            agent_id: Agent ID
            capabilities: Task types this agent can handle
            execute_fn: Execution function
        """
        agent = AutonomousAgent(
            agent_id=agent_id,
            capabilities=capabilities,
            task_registry=self.registry,
            redis_coordinator=self.redis,
            execute_fn=execute_fn
        )

        self.agents[agent_id] = agent

    def start_all(self):
        """Start all agents in the pool"""
        for agent in self.agents.values():
            agent.start()

    def stop_all(self):
        """Stop all agents in the pool"""
        for agent in self.agents.values():
            agent.stop()

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all agents.

        Returns:
            Dictionary of agent_id -> status
        """
        return {
            agent_id: self.redis.get_agent_status(agent_id)
            for agent_id in self.agents.keys()
        }
