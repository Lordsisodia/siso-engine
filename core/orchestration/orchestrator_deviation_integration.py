"""
Orchestrator Integration with Deviation Handler

This module provides integration code to add 4-Rule Deviation Handling
to the existing AgentOrchestrator.

Copy the relevant sections into Orchestrator.py to enable autonomous
error recovery.
"""

# =============================================================================
# ADD TO IMPORTS SECTION (around line 60)
# =============================================================================

from .deviation_handler import DeviationHandler, DeviationType


# =============================================================================
# ADD TO AgentOrchestrator.__init__() METHOD (around line 280)
# =============================================================================

def __init__(
    self,
    event_bus: Optional[RedisEventBus] = None,
    task_router: Optional[TaskRouter] = None,
    memory_base_path: Optional[Path] = None,
    max_concurrent_agents: int = 5,
    enable_checkpoints: bool = True,
    checkpoint_frequency: int = 1,
    checkpoint_retention: int = 5,
    enable_atomic_commits: bool = True,
    max_recovery_attempts: int = 3,  # NEW: Deviation recovery config
    enable_deviation_handling: bool = True,  # NEW: Enable/disable deviation handling
):
    """
    Initialize the agent orchestrator.

    Args:
        event_bus: Event bus for emitting orchestration events
        task_router: Task router for complexity-based routing
        memory_base_path: Base path for storing agent memory
        max_concurrent_agents: Maximum number of concurrent agents
        enable_checkpoints: Enable checkpoint saving
        checkpoint_frequency: Save checkpoint after N waves (1 = every wave)
        checkpoint_retention: Keep N most recent checkpoints
        enable_atomic_commits: Enable automatic commits after task completion
        max_recovery_attempts: Maximum autonomous recovery attempts per task (NEW)
        enable_deviation_handling: Enable autonomous error recovery (NEW)
    """
    # ... existing initialization code ...

    self.enable_atomic_commits = enable_atomic_commits

    # NEW: Initialize deviation handler
    self.enable_deviation_handling = enable_deviation_handling
    self.max_recovery_attempts = max_recovery_attempts
    self.deviation_handler: Optional[DeviationHandler] = None

    if self.enable_deviation_handling:
        try:
            self.deviation_handler = DeviationHandler(
                max_recovery_attempts=max_recovery_attempts
            )
            logger.info(f"Deviation handling enabled (max_attempts={max_recovery_attempts})")
        except Exception as e:
            logger.warning(f"Failed to initialize deviation handler: {e}")
            self.deviation_handler = None
            self.enable_deviation_handling = False

    # ... rest of initialization code ...


# =============================================================================
# NEW METHOD: Execute task with deviation detection and recovery
# =============================================================================

async def _execute_with_recovery(
    self,
    task: WorkflowStep,
    wave_id: Optional[int] = None
) -> ParallelTaskResult:
    """
    Execute task with deviation detection and autonomous recovery.

    This method wraps task execution with the 4-Rule Deviation Handling system:
    1. Attempts to execute the task
    2. If error occurs, detects deviation type
    3. Applies autonomous recovery strategy based on deviation type
    4. Retries task if recovery successful
    5. Returns error if recovery fails or deviation is unrecoverable

    Args:
        task: Workflow step to execute
        wave_id: Optional wave ID for tracking

    Returns:
        ParallelTaskResult with execution outcome
    """
    max_retries = 3  # Total attempts including initial try

    for attempt in range(max_retries):
        start_time = datetime.now()

        try:
            # Try to execute task
            logger.debug(f"Task {task.agent_id or 'unknown'} attempt {attempt + 1}/{max_retries}")

            # Use existing task execution logic
            result = await self._execute_task_with_commit(task, wave_id)

            # If successful, return result
            if result.success:
                logger.info(f"Task {task.agent_id or 'unknown'} completed successfully")
                return result
            else:
                # Task failed but not due to exception
                logger.warning(f"Task {task.agent_id or 'unknown'} failed: {result.error}")
                return result

        except Exception as e:
            logger.warning(f"Task {task.agent_id or 'unknown'} raised exception: {type(e).__name__}")

            # Check if deviation handling is enabled
            if not self.enable_deviation_handling or not self.deviation_handler:
                # No deviation handling, return error immediately
                duration = (datetime.now() - start_time).total_seconds()
                return ParallelTaskResult(
                    task_id=task.agent_id or "unknown",
                    agent_id=task.agent_id or "unknown",
                    agent_type=task.agent_type,
                    success=False,
                    error=str(e),
                    duration=duration
                )

            # Detect deviation type
            task_context = {
                'task_id': task.agent_id or 'unknown',
                'description': task.task,
                'agent_type': task.agent_type,
                'metadata': task.metadata,
                'wave_id': wave_id,
                'attempt': attempt + 1,
            }

            deviation = self.deviation_handler.detect_deviation(e, task_context)

            if deviation:
                logger.warning(
                    f"Deviation detected for task {task.agent_id or 'unknown'}: "
                    f"{deviation.deviation_type.value} ({deviation.error_type})"
                )

                # Log suggested fixes
                if deviation.suggested_fixes:
                    logger.info(f"Suggested fixes: {', '.join(deviation.suggested_fixes[:3])}")

                # Attempt autonomous recovery
                recovered = await self.deviation_handler.recover_from_deviation(
                    deviation,
                    task,
                    self  # Pass orchestrator as tool system
                )

                if recovered:
                    logger.info(
                        f"Autonomous recovery successful for {deviation.deviation_type.value}, "
                        f"retrying task {task.agent_id or 'unknown'}..."
                    )
                    # Continue to next attempt (retry the task)
                    continue
                else:
                    logger.error(
                        f"Autonomous recovery failed for {deviation.deviation_type.value} "
                        f"on task {task.agent_id or 'unknown'}"
                    )
                    # Fall through to return error

            else:
                # No recovery strategy for this error type
                logger.info(
                    f"No autonomous recovery available for {type(e).__name__}, "
                    f"returning error to caller"
                )

            # If we get here, recovery failed or was not possible
            duration = (datetime.now() - start_time).total_seconds()

            return ParallelTaskResult(
                task_id=task.agent_id or "unknown",
                agent_id=task.agent_id or "unknown",
                agent_type=task.agent_type,
                success=False,
                error=str(e),
                duration=duration
            )

    # Should not reach here, but just in case
    duration = (datetime.now() - start_time).total_seconds()
    return ParallelTaskResult(
        task_id=task.agent_id or "unknown",
        agent_id=task.agent_id or "unknown",
        agent_type=task.agent_type,
        success=False,
        error="Max retry attempts exceeded",
        duration=duration
    )


# =============================================================================
# MODIFIED METHOD: Update parallel_execute to use deviation handling
# =============================================================================

async def parallel_execute(
    self,
    tasks: List[Union[Dict[str, Any], WorkflowStep]]
) -> List[ParallelTaskResult]:
    """
    Execute multiple agent tasks in parallel with deviation handling.

    Args:
        tasks: List of tasks to execute in parallel

    Returns:
        List of ParallelTaskResult with execution results
    """
    if len(tasks) > self.max_concurrent_agents:
        logger.warning(
            f"Requested {len(tasks)} parallel tasks but max_concurrent is "
            f"{self.max_concurrent_agents}. Some tasks will queue."
        )

    results = []
    semaphore = asyncio.Semaphore(self.max_concurrent_agents)

    async def execute_single(task_def, task_id: str) -> ParallelTaskResult:
        """Execute a single task within semaphore limit with deviation handling."""
        async with semaphore:
            # Parse task
            if isinstance(task_def, dict):
                step = WorkflowStep(**task_def)
            else:
                step = task_def

            # Use deviation-aware execution
            return await self._execute_with_recovery(step)

    # Create coroutines for all tasks
    coroutines = [
        execute_single(task, f"task_{i}")
        for i, task in enumerate(tasks)
    ]

    # Execute in parallel
    results = await asyncio.gather(*coroutines, return_exceptions=True)

    # Handle exceptions
    formatted_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            formatted_results.append(
                ParallelTaskResult(
                    task_id=f"task_{i}",
                    agent_id="unknown",
                    agent_type="unknown",
                    success=False,
                    error=str(result)
                )
            )
        else:
            formatted_results.append(result)

    logger.info(
        f"Parallel execution completed: "
        f"{sum(1 for r in formatted_results if r.success)}/{len(tasks)} succeeded"
    )

    return formatted_results


# =============================================================================
# NEW METHOD: Get deviation recovery statistics
# =============================================================================

def get_deviation_statistics(self) -> Dict[str, Any]:
    """
    Get statistics about deviation detection and recovery.

    Returns:
        Dictionary with deviation statistics
    """
    if not self.enable_deviation_handling or not self.deviation_handler:
        return {
            "enabled": False,
            "message": "Deviation handling is not enabled"
        }

    stats = self.deviation_handler.get_recovery_statistics()
    stats["enabled"] = True
    return stats


# =============================================================================
# NEW METHOD: Get recent recovery attempts
# =============================================================================

def get_recent_recoveries(self, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent autonomous recovery attempts.

    Args:
        limit: Maximum number of recent recoveries to return

    Returns:
        List of recent recovery attempts
    """
    if not self.enable_deviation_handling or not self.deviation_handler:
        return []

    return self.deviation_handler.get_recent_recoveries(limit)


# =============================================================================
# MODIFIED METHOD: Update get_statistics to include deviation stats
# =============================================================================

def get_statistics(self) -> Dict[str, Any]:
    """
    Get orchestrator statistics including deviation handling.

    Returns:
        Dictionary with statistics
    """
    # Count agents by state
    agents_by_state = {}
    for state in AgentState:
        agents_by_state[state.value] = sum(
            1 for agent in self._agents.values()
            if agent.state == state
        )

    # Count agents by type
    agents_by_type = {}
    for agent in self._agents.values():
        agent_type = agent.config.agent_type
        agents_by_type[agent_type] = agents_by_type.get(agent_type, 0) + 1

    # Workflow statistics
    completed_workflows = sum(
        1 for w in self._workflows.values()
        if w.state == WorkflowState.COMPLETED
    )
    failed_workflows = sum(
        1 for w in self._workflows.values()
        if w.state == WorkflowState.FAILED
    )

    # Build stats dictionary
    stats = {
        "total_agents": len(self._agents),
        "agents_by_state": agents_by_state,
        "agents_by_type": agents_by_type,
        "total_workflows": len(self._workflows),
        "completed_workflows": completed_workflows,
        "failed_workflows": failed_workflows,
        "max_concurrent_agents": self.max_concurrent_agents,
        "memory_base_path": str(self.memory_base_path),
    }

    # Add deviation statistics if enabled
    if self.enable_deviation_handling:
        stats["deviation_handling"] = self.get_deviation_statistics()
    else:
        stats["deviation_handling"] = {"enabled": False}

    # Add atomic commit statistics if enabled
    if self.atomic_commits:
        stats["atomic_commits"] = self.get_commit_statistics()
    else:
        stats["atomic_commits"] = {"enabled": False}

    return stats


# =============================================================================
# MODIFIED: Update create_orchestrator convenience function
# =============================================================================

def create_orchestrator(
    event_bus: Optional[RedisEventBus] = None,
    task_router: Optional[TaskRouter] = None,
    memory_base_path: Optional[Path] = None,
    max_concurrent_agents: int = 5,
    enable_checkpoints: bool = True,
    checkpoint_frequency: int = 1,
    checkpoint_retention: int = 5,
    max_recovery_attempts: int = 3,  # NEW
    enable_deviation_handling: bool = True,  # NEW
) -> AgentOrchestrator:
    """
    Create an AgentOrchestrator with sensible defaults.

    Args:
        event_bus: Optional event bus
        task_router: Optional task router
        memory_base_path: Optional memory base path
        max_concurrent_agents: Maximum concurrent agents
        enable_checkpoints: Enable checkpoint saving
        checkpoint_frequency: Save checkpoint after N waves
        checkpoint_retention: Keep N most recent checkpoints
        max_recovery_attempts: Maximum autonomous recovery attempts (NEW)
        enable_deviation_handling: Enable autonomous error recovery (NEW)

    Returns:
        Configured AgentOrchestrator instance
    """
    return AgentOrchestrator(
        event_bus=event_bus,
        task_router=task_router,
        memory_base_path=memory_base_path,
        max_concurrent_agents=max_concurrent_agents,
        enable_checkpoints=enable_checkpoints,
        checkpoint_frequency=checkpoint_frequency,
        checkpoint_retention=checkpoint_retention,
        max_recovery_attempts=max_recovery_attempts,
        enable_deviation_handling=enable_deviation_handling,
    )


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
Example 1: Basic usage with deviation handling

    orchestrator = create_orchestrator(
        max_recovery_attempts=3,
        enable_deviation_handling=True
    )

    # Execute workflow with automatic error recovery
    workflow = [
        {"agent_type": "developer", "task": "Implement feature"},
        {"agent_type": "tester", "task": "Run tests"},
    ]
    result = await orchestrator.execute_wave_based(workflow)

    # Check recovery statistics
    stats = orchestrator.get_deviation_statistics()
    print(f"Recovery attempts: {stats['total_attempts']}")


Example 2: Disable deviation handling for specific workflows

    orchestrator = create_orchestrator(
        enable_deviation_handling=False  # Disable globally
    )


Example 3: View recent recovery attempts

    recent = orchestrator.get_recent_recoveries(limit=5)
    for recovery in recent:
        print(f"{recovery['timestamp']}: {recovery['deviation_type']}")


Example 4: Full statistics including deviation handling

    stats = orchestrator.get_statistics()
    print(f"Deviation handling: {stats['deviation_handling']}")
    print(f"Atomic commits: {stats['atomic_commits']}")
"""
