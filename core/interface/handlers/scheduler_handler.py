"""
Scheduler Handler for Agent Output Bus

Receives agent outputs and queues next_steps as autonomous tasks.
"""

import logging
import sys
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable

# Import from parent directory
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from AgentOutputBus import OutputHandler, HandlerResult, OutputEvent, OutputStatus

# Try to import scheduler
try:
    from scheduler import (
        TaskScheduler,
        AutonomousTask,
        TaskPriority,
        TaskStatus
    )
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    logging.warning("scheduler not found - SchedulerHandler will be disabled")

logger = logging.getLogger(__name__)


class SchedulerHandler(OutputHandler):
    """
    Handler for integrating agent outputs with the autonomous task scheduler.

    Queues next_steps from agent outputs as new autonomous tasks.
    """

    # Priority mapping based on agent status
    # Will be set in __init__ if scheduler is available
    PRIORITY_MAP = {}

    def __init__(
        self,
        scheduler: Optional['TaskScheduler'] = None,
        auto_queue_tasks: bool = True,
        default_priority: Optional['TaskPriority'] = None,
        depends_on_parent: bool = True
    ):
        """
        Initialize Scheduler handler.

        Args:
            scheduler: TaskScheduler instance (creates new one if None)
            auto_queue_tasks: Automatically queue next_steps as tasks
            default_priority: Default priority for queued tasks
            depends_on_parent: Make next_steps depend on parent task completion
        """
        super().__init__("SchedulerHandler")

        if not SCHEDULER_AVAILABLE:
            logger.warning("SchedulerHandler initialized but scheduler module not available")
            self.scheduler = None
            # Set defaults when scheduler not available
            SchedulerHandler.PRIORITY_MAP = {}
            self.default_priority = None
        else:
            self.scheduler = scheduler or TaskScheduler()
            # Set up priority mapping now that TaskPriority is available
            SchedulerHandler.PRIORITY_MAP = {
                OutputStatus.SUCCESS: TaskPriority.LOW,
                OutputStatus.PARTIAL: TaskPriority.MEDIUM,
                OutputStatus.FAILED: TaskPriority.HIGH,
            }
            self.default_priority = default_priority if default_priority is not None else TaskPriority.MEDIUM

        self.auto_queue_tasks = auto_queue_tasks
        self.depends_on_parent = depends_on_parent

    def handle(self, event: OutputEvent) -> HandlerResult:
        """
        Handle agent output event.

        Args:
            event: Parsed agent output event

        Returns:
            HandlerResult with success status and details
        """
        if not self.scheduler:
            return HandlerResult(
                success=False,
                message="Task scheduler not available",
                data=None
            )

        try:
            if not self.auto_queue_tasks:
                return HandlerResult(
                    success=True,
                    message="Auto-queue disabled, skipping next_steps",
                    data={"queued_count": 0}
                )

            if not event.next_steps:
                return HandlerResult(
                    success=True,
                    message="No next_steps to queue",
                    data={"queued_count": 0}
                )

            # Queue each next_step as a task
            queued_tasks = []
            parent_task_id = event.metadata.get('scheduler_task_id')

            for i, step in enumerate(event.next_steps):
                task_id = self._queue_next_step(
                    step=step,
                    event=event,
                    index=i,
                    parent_task_id=parent_task_id
                )
                if task_id:
                    queued_tasks.append(task_id)

            data = {
                "queued_count": len(queued_tasks),
                "task_ids": queued_tasks,
                "parent_task_id": parent_task_id
            }

            logger.info(f"Queued {len(queued_tasks)} tasks from agent {event.agent_name}")

            return HandlerResult(
                success=True,
                message=f"Queued {len(queued_tasks)} autonomous tasks",
                data=data
            )

        except Exception as e:
            logger.error(f"SchedulerHandler error: {e}")
            return HandlerResult(
                success=False,
                message=f"Failed to queue tasks: {e}",
                data=None
            )

    def _queue_next_step(
        self,
        step: str,
        event: OutputEvent,
        index: int,
        parent_task_id: Optional[str]
    ) -> Optional[str]:
        """Queue a single next_step as an autonomous task."""
        # Determine priority
        priority = self.PRIORITY_MAP.get(event.status, self.default_priority)

        # Build dependencies
        depends_on = [parent_task_id] if (parent_task_id and self.depends_on_parent) else []

        # Create async wrapper for the task
        async def execute_step():
            # This is a placeholder - in real usage, you'd want to
            # actually execute the step (e.g., call an agent)
            logger.info(f"Executing next step: {step}")
            return {"step": step, "completed": True}

        # Schedule the task
        task_id = self.scheduler.generate_task_id()

        task = AutonomousTask(
            id=task_id,
            name=f"Next Step {index + 1}: {step[:50]}",
            description=step,
            task_type="follow-up",
            priority=priority,
            depends_on=depends_on,
            execute_func=execute_step
        )

        # Add to queue (async, but we'll just schedule it)
        asyncio.create_task(self.scheduler.task_queue.add_task(task))

        logger.debug(f"Queued task {task_id}: {step[:50]}")

        return task_id

    async def process_queue(self):
        """Process the task queue (convenience method)."""
        if self.scheduler:
            await self.scheduler.process_queue()


def create_scheduler_handler(
    scheduler: Optional['TaskScheduler'] = None
) -> Optional[SchedulerHandler]:
    """
    Convenience function to create Scheduler handler.

    Returns None if scheduler module is not available.
    """
    if not SCHEDULER_AVAILABLE:
        logger.warning("Cannot create SchedulerHandler - scheduler module not found")
        return None

    return SchedulerHandler(scheduler=scheduler)
