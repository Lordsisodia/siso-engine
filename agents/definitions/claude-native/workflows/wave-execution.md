# Wave-Based Execution in BlackBox5

## Overview

Wave-based execution is a task scheduling and orchestration pattern that groups tasks into sequential "waves" based on their dependencies. Tasks within the same wave have no inter-dependencies and can execute in parallel, while waves themselves execute sequentially.

### Why Wave-Based Execution Matters

1. **Maximize Parallelism**: Execute independent tasks simultaneously to reduce total execution time
2. **Respect Dependencies**: Ensure tasks only run after their dependencies complete successfully
3. **Optimize Resource Usage**: Balance parallel execution against resource constraints
4. **Clear Progress Tracking**: Waves provide natural checkpoints for monitoring progress
5. **Failure Isolation**: Failures in one wave prevent dependent waves from starting

### Key Benefits

| Aspect | Sequential | Wave-Based | Improvement |
|--------|-----------|------------|-------------|
| Diamond Pattern (A→[B,C]→D) | 4 steps | 3 waves | 25% faster |
| Complex DAG (7 tasks) | 7 steps | 3-4 waves | ~50% faster |
| Resource Utilization | Low | High | Better CPU/GPU usage |
| Visibility | Poor | Excellent | Clear progress per wave |

---

## Dependency Graph

### Parsing `depends_on` from Task Frontmatter

Tasks in BlackBox5 specify dependencies in their frontmatter:

```yaml
---
id: task-003
name: Build API
depends_on:
  - task-001  # Setup Database
  - task-002  # Configure Auth
---
```

### Building the Dependency Graph

The dependency graph is a directed acyclic graph (DAG) where:
- **Nodes** represent tasks
- **Edges** represent dependencies (A → B means B depends on A)

```python
from dataclasses import dataclass
from typing import List, Dict, Set
from collections import defaultdict

@dataclass
class Task:
    id: str
    name: str
    depends_on: List[str]

def build_dependency_graph(tasks: List[Task]) -> Dict[str, Set[str]]:
    """
    Build adjacency list representation of dependency graph.

    Returns:
        Dict mapping task_id -> set of task_ids it depends on
    """
    graph = defaultdict(set)

    for task in tasks:
        graph[task.id] = set(task.depends_on)

    return dict(graph)

def build_reverse_graph(graph: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """
    Build reverse graph for finding dependents.

    Returns:
        Dict mapping task_id -> set of task_ids that depend on it
    """
    reverse = defaultdict(set)

    for task_id, deps in graph.items():
        for dep in deps:
            reverse[dep].add(task_id)

    return dict(reverse)
```

### Visual Representation

```
Linear Chain:
  task-001 → task-002 → task-003

Diamond Pattern:
           ┌→ task-002 ─┐
  task-001 ─┤            ├→ task-004
           └→ task-003 ─┘

Complex DAG:
  task-001 ─┐
            ├→ task-003 ─┐
  task-002 ─┘            ├→ task-005
            ┌→ task-004 ─┘
  task-006 ─┘
```

---

## Wave Calculation Algorithm

### Algorithm Overview

The wave calculation algorithm assigns each task to a wave based on its dependencies:

1. **Wave 0**: Tasks with no dependencies (roots)
2. **Wave N**: Tasks whose dependencies are all in waves < N

### Python Implementation

```python
def calculate_waves(tasks: List[Task]) -> Dict[str, int]:
    """
    Calculate wave assignments for all tasks.

    Args:
        tasks: List of tasks with dependencies

    Returns:
        Dict mapping task_id -> wave_number

    Raises:
        ValueError: If circular dependency detected
    """
    graph = build_dependency_graph(tasks)
    task_map = {t.id: t for t in tasks}

    # Track wave assignments
    waves = {}

    # Track which tasks have been assigned
    assigned = set()

    # Track tasks we've visited (for cycle detection)
    visiting = set()
    visited = set()

    def get_wave(task_id: str) -> int:
        """Recursively calculate wave for a task."""
        if task_id in waves:
            return waves[task_id]

        if task_id in visiting:
            # Circular dependency detected
            raise ValueError(f"Circular dependency detected involving task: {task_id}")

        if task_id in visited:
            # Already processed
            return waves.get(task_id, 0)

        visiting.add(task_id)

        deps = graph.get(task_id, set())

        if not deps:
            # Root task - wave 0
            waves[task_id] = 0
        else:
            # Wave = max(wave of dependencies) + 1
            max_dep_wave = max(get_wave(dep) for dep in deps)
            waves[task_id] = max_dep_wave + 1

        visiting.remove(task_id)
        visited.add(task_id)
        assigned.add(task_id)

        return waves[task_id]

    # Calculate waves for all tasks
    for task in tasks:
        get_wave(task.id)

    return waves

def group_by_wave(tasks: List[Task], waves: Dict[str, int]) -> Dict[int, List[Task]]:
    """
    Group tasks by their wave assignments.

    Returns:
        Dict mapping wave_number -> list of tasks
    """
    wave_groups = defaultdict(list)

    for task in tasks:
        wave_num = waves[task.id]
        wave_groups[wave_num].append(task)

    # Sort by wave number
    return dict(sorted(wave_groups.items()))
```

### Example Calculation

Given tasks:
```yaml
task-001: depends_on: []
task-002: depends_on: [task-001]
task-003: depends_on: [task-001]
task-004: depends_on: [task-002, task-003]
```

Wave assignments:
```
Wave 0: task-001 (no dependencies)
Wave 1: task-002, task-003 (depend on wave 0)
Wave 2: task-004 (depends on wave 1)
```

### Text Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    WAVE CALCULATION                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input Tasks:                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ task-001 │  │ task-002 │  │ task-003 │  │ task-004 │   │
│  │ deps: [] │  │deps:[001]│  │deps:[001]│  │deps:[002,│   │
│  │          │  │          │  │          │  │    003]  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │             │             │          │
│       └─────────────┴─────────────┘             │          │
│                     │                           │          │
│                     └───────────────────────────┘          │
│                                                             │
│  Wave Calculation:                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Wave 0: task-001 (root)                             │   │
│  │ Wave 1: task-002, task-003 (deps satisfied)         │   │
│  │ Wave 2: task-004 (all deps in wave 1)               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Execution Order:                                           │
│  [Wave 0] ──→ [Wave 1] ──→ [Wave 2]                        │
│  [task-001]   [task-002]    [task-004]                      │
│               [task-003]                                    │
│               (parallel)                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Parallel Execution

### Spawning Tasks Within a Wave

Tasks in the same wave have no inter-dependencies and can execute in parallel:

```python
import asyncio
from typing import List, Callable, Awaitable, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class WaveResult:
    wave_number: int
    task_results: Dict[str, Any]
    started_at: datetime
    completed_at: datetime
    success_count: int
    failure_count: int

class WaveExecutor:
    """Executes tasks within a wave in parallel."""

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_wave(
        self,
        wave_number: int,
        tasks: List[Task],
        executor_func: Callable[[Task], Awaitable[Any]]
    ) -> WaveResult:
        """
        Execute all tasks in a wave concurrently.

        Args:
            wave_number: Current wave number
            tasks: Tasks in this wave
            executor_func: Async function to execute a task

        Returns:
            WaveResult with all task outcomes
        """
        started_at = datetime.now()
        task_results = {}
        success_count = 0
        failure_count = 0

        async def execute_with_limit(task: Task) -> tuple:
            """Execute task with concurrency limit."""
            async with self.semaphore:
                try:
                    result = await executor_func(task)
                    return (task.id, result, True)
                except Exception as e:
                    return (task.id, e, False)

        # Execute all tasks concurrently
        results = await asyncio.gather(
            *[execute_with_limit(task) for task in tasks],
            return_exceptions=True
        )

        # Process results
        for task_id, result, success in results:
            task_results[task_id] = result
            if success:
                success_count += 1
            else:
                failure_count += 1

        return WaveResult(
            wave_number=wave_number,
            task_results=task_results,
            started_at=started_at,
            completed_at=datetime.now(),
            success_count=success_count,
            failure_count=failure_count
        )
```

### Concurrency Control

Limit parallel execution to prevent resource exhaustion:

```python
async def execute_with_semaphore(
    task: Task,
    semaphore: asyncio.Semaphore,
    executor: Callable
) -> Any:
    """Execute task with concurrency control."""
    async with semaphore:
        return await executor(task)

# Usage
semaphore = asyncio.Semaphore(5)  # Max 5 concurrent tasks
results = await asyncio.gather(*[
    execute_with_semaphore(task, semaphore, execute_task)
    for task in wave_tasks
])
```

### Progress Tracking

```python
from typing import Optional

class WaveProgressTracker:
    """Track progress of wave execution."""

    def __init__(self, total_waves: int):
        self.total_waves = total_waves
        self.current_wave = 0
        self.completed_tasks = 0
        self.total_tasks = 0
        self.wave_start_times = {}

    def start_wave(self, wave_number: int, task_count: int):
        """Mark wave as started."""
        self.current_wave = wave_number
        self.total_tasks = task_count
        self.completed_tasks = 0
        self.wave_start_times[wave_number] = datetime.now()

        print(f"🌊 Starting Wave {wave_number}/{self.total_waves} "
              f"({task_count} tasks)")

    def task_completed(self, task_id: str, success: bool):
        """Mark task as completed."""
        self.completed_tasks += 1
        status = "✓" if success else "✗"
        print(f"  {status} Task {task_id} "
              f"({self.completed_tasks}/{self.total_tasks})")

    def end_wave(self, wave_number: int):
        """Mark wave as completed."""
        duration = (datetime.now() -
                   self.wave_start_times[wave_number]).total_seconds()
        print(f"🌊 Wave {wave_number} completed in {duration:.2f}s")
```

---

## Sequential Waves

### Wave Dependencies

Each wave depends on the successful completion of all previous waves:

```python
async def execute_waves_sequentially(
    wave_groups: Dict[int, List[Task]],
    executor: WaveExecutor,
    executor_func: Callable[[Task], Awaitable[Any]],
    continue_on_failure: bool = False
) -> List[WaveResult]:
    """
    Execute waves in sequence, respecting dependencies.

    Args:
        wave_groups: Tasks grouped by wave number
        executor: Wave executor instance
        executor_func: Function to execute individual tasks
        continue_on_failure: Whether to continue after wave failure

    Returns:
        List of WaveResult for each executed wave
    """
    results = []
    failed = False

    for wave_number in sorted(wave_groups.keys()):
        if failed and not continue_on_failure:
            print(f"⏹️  Skipping Wave {wave_number} due to previous failure")
            continue

        tasks = wave_groups[wave_number]
        print(f"\n🌊 Executing Wave {wave_number} ({len(tasks)} tasks)")

        # Execute wave
        wave_result = await executor.execute_wave(
            wave_number, tasks, executor_func
        )
        results.append(wave_result)

        # Check for failures
        if wave_result.failure_count > 0:
            print(f"⚠️  Wave {wave_number} had {wave_result.failure_count} failures")
            failed = True

            if not continue_on_failure:
                print("🛑 Stopping execution due to wave failure")
                break

    return results
```

### Wave Completion Criteria

A wave is considered complete when:
1. All tasks in the wave have finished execution
2. Success criteria met (or failure handling applied)

```python
def is_wave_complete(wave_result: WaveResult, require_all_success: bool = True) -> bool:
    """
    Check if wave completed successfully.

    Args:
        wave_result: Result from wave execution
        require_all_success: If True, all tasks must succeed

    Returns:
        True if wave completed successfully
    """
    total = wave_result.success_count + wave_result.failure_count

    if wave_result.success_count + wave_result.failure_count == 0:
        return False  # No tasks executed

    if require_all_success:
        return wave_result.failure_count == 0
    else:
        # Allow partial success
        return wave_result.success_count > 0
```

---

## Implementation Example

### Complete Wave-Based Orchestrator

```python
import asyncio
from typing import List, Dict, Callable, Awaitable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ExecutionState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    name: str
    depends_on: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Wave:
    number: int
    tasks: List[Task]

@dataclass
class ExecutionResult:
    state: ExecutionState
    waves_completed: int
    steps_completed: int
    steps_total: int
    wave_details: List[Dict[str, Any]]
    errors: Dict[str, str]
    started_at: datetime
    completed_at: Optional[datetime]

class WaveOrchestrator:
    """
    Wave-based task orchestrator for BlackBox5.

    Features:
    - Automatic wave calculation from dependencies
    - Parallel execution within waves
    - Sequential wave progression
    - Configurable concurrency limits
    - Progress tracking and reporting
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        continue_on_failure: bool = False,
        require_all_success: bool = True
    ):
        self.max_concurrent = max_concurrent
        self.continue_on_failure = continue_on_failure
        self.require_all_success = require_all_success
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute(
        self,
        tasks: List[Task],
        executor_func: Callable[[Task], Awaitable[Any]],
        workflow_id: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute tasks using wave-based scheduling.

        Args:
            tasks: List of tasks to execute
            executor_func: Async function to execute a task
            workflow_id: Optional workflow identifier

        Returns:
            ExecutionResult with complete execution details
        """
        started_at = datetime.now()
        workflow_id = workflow_id or f"workflow-{started_at.timestamp()}"

        logger.info(f"Starting workflow {workflow_id} with {len(tasks)} tasks")

        try:
            # Step 1: Calculate waves
            waves = self._calculate_waves(tasks)
            wave_groups = self._group_by_wave(tasks, waves)

            logger.info(f"Calculated {len(wave_groups)} waves")
            for wave_num, wave_tasks in wave_groups.items():
                logger.info(f"  Wave {wave_num}: {len(wave_tasks)} tasks")

            # Step 2: Execute waves sequentially
            wave_results = []
            errors = {}

            for wave_num in sorted(wave_groups.keys()):
                wave_tasks = wave_groups[wave_num]

                logger.info(f"Executing Wave {wave_num} ({len(wave_tasks)} tasks)")

                wave_result = await self._execute_wave(
                    wave_num, wave_tasks, executor_func
                )
                wave_results.append(wave_result)

                # Collect errors
                for task_id, result in wave_result.task_results.items():
                    if isinstance(result, Exception):
                        errors[task_id] = str(result)

                # Check if we should continue
                if wave_result.failure_count > 0 and not self.continue_on_failure:
                    logger.error(f"Wave {wave_num} failed, stopping execution")
                    break

            # Step 3: Determine final state
            total_failures = sum(wr.failure_count for wr in wave_results)
            state = ExecutionState.COMPLETED if total_failures == 0 else ExecutionState.FAILED

            return ExecutionResult(
                state=state,
                waves_completed=len(wave_results),
                steps_completed=sum(wr.success_count for wr in wave_results),
                steps_total=len(tasks),
                wave_details=[self._wave_to_dict(wr) for wr in wave_results],
                errors=errors,
                started_at=started_at,
                completed_at=datetime.now()
            )

        except Exception as e:
            logger.exception("Workflow execution failed")
            return ExecutionResult(
                state=ExecutionState.FAILED,
                waves_completed=0,
                steps_completed=0,
                steps_total=len(tasks),
                wave_details=[],
                errors={"workflow": str(e)},
                started_at=started_at,
                completed_at=datetime.now()
            )

    def _calculate_waves(self, tasks: List[Task]) -> Dict[str, int]:
        """Calculate wave assignments for all tasks."""
        task_map = {t.id: t for t in tasks}
        waves = {}
        visiting = set()

        def get_wave(task_id: str) -> int:
            if task_id in waves:
                return waves[task_id]

            if task_id in visiting:
                raise ValueError(f"Circular dependency detected: {task_id}")

            visiting.add(task_id)
            task = task_map.get(task_id)

            if not task or not task.depends_on:
                waves[task_id] = 0
            else:
                max_dep_wave = max(get_wave(dep) for dep in task.depends_on)
                waves[task_id] = max_dep_wave + 1

            visiting.remove(task_id)
            return waves[task_id]

        for task in tasks:
            get_wave(task.id)

        return waves

    def _group_by_wave(
        self,
        tasks: List[Task],
        waves: Dict[str, int]
    ) -> Dict[int, List[Task]]:
        """Group tasks by wave number."""
        groups = {}
        for task in tasks:
            wave_num = waves[task.id]
            if wave_num not in groups:
                groups[wave_num] = []
            groups[wave_num].append(task)
        return dict(sorted(groups.items()))

    async def _execute_wave(
        self,
        wave_num: int,
        tasks: List[Task],
        executor_func: Callable[[Task], Awaitable[Any]]
    ) -> 'WaveResult':
        """Execute all tasks in a wave."""
        from dataclasses import dataclass

        @dataclass
        class WaveResult:
            wave_number: int
            task_results: Dict[str, Any]
            success_count: int
            failure_count: int

        task_results = {}
        success_count = 0
        failure_count = 0

        async def execute_single(task: Task) -> tuple:
            async with self.semaphore:
                try:
                    result = await executor_func(task)
                    return (task.id, result, True)
                except Exception as e:
                    logger.error(f"Task {task.id} failed: {e}")
                    return (task.id, e, False)

        results = await asyncio.gather(*[
            execute_single(task) for task in tasks
        ])

        for task_id, result, success in results:
            task_results[task_id] = result
            if success:
                success_count += 1
            else:
                failure_count += 1

        return WaveResult(
            wave_number=wave_num,
            task_results=task_results,
            success_count=success_count,
            failure_count=failure_count
        )

    def _wave_to_dict(self, wave_result: Any) -> Dict[str, Any]:
        """Convert wave result to dictionary."""
        return {
            "wave_number": wave_result.wave_number,
            "success_count": wave_result.success_count,
            "failure_count": wave_result.failure_count,
            "total_tasks": wave_result.success_count + wave_result.failure_count
        }


# ============ USAGE EXAMPLE ============

async def example_usage():
    """Demonstrate wave-based execution."""

    # Define tasks with dependencies
    tasks = [
        Task(id="setup-db", name="Setup Database", depends_on=[]),
        Task(id="setup-cache", name="Setup Cache", depends_on=[]),
        Task(id="user-service", name="Build User Service", depends_on=["setup-db"]),
        Task(id="auth-service", name="Build Auth Service", depends_on=["setup-db", "setup-cache"]),
        Task(id="api-gateway", name="Build API Gateway", depends_on=["user-service", "auth-service"]),
        Task(id="integration-tests", name="Run Integration Tests", depends_on=["api-gateway"]),
    ]

    # Define task executor
    async def execute_task(task: Task) -> str:
        """Simulate task execution."""
        await asyncio.sleep(0.1)  # Simulate work
        return f"Completed: {task.name}"

    # Create orchestrator and execute
    orchestrator = WaveOrchestrator(max_concurrent=3)
    result = await orchestrator.execute(tasks, execute_task, workflow_id="demo")

    # Print results
    print(f"\nWorkflow State: {result.state.value}")
    print(f"Waves Completed: {result.waves_completed}")
    print(f"Tasks: {result.steps_completed}/{result.steps_total}")

    for wave_detail in result.wave_details:
        print(f"  Wave {wave_detail['wave_number']}: "
              f"{wave_detail['success_count']}/{wave_detail['total_tasks']} succeeded")


if __name__ == "__main__":
    asyncio.run(example_usage())
```

---

## Error Handling

### Failure Modes

When a task in a wave fails, several strategies are available:

```python
from enum import Enum

class FailureStrategy(Enum):
    STOP_ALL = "stop_all"           # Stop entire workflow
    STOP_WAVE = "stop_wave"         # Stop current wave, skip dependent waves
    CONTINUE = "continue"           # Continue with remaining tasks
    RETRY = "retry"                 # Retry failed tasks

class WaveErrorHandler:
    """Handle failures in wave execution."""

    def __init__(self, strategy: FailureStrategy = FailureStrategy.STOP_ALL):
        self.strategy = strategy
        self.failed_tasks = set()
        self.retry_counts = {}
        self.max_retries = 3

    async def handle_failure(
        self,
        task: Task,
        error: Exception,
        wave_result: 'WaveResult'
    ) -> bool:
        """
        Handle a task failure.

        Returns:
            True if execution should continue, False to stop
        """
        self.failed_tasks.add(task.id)

        if self.strategy == FailureStrategy.STOP_ALL:
            logger.error(f"Task {task.id} failed, stopping workflow: {error}")
            return False

        elif self.strategy == FailureStrategy.STOP_WAVE:
            logger.error(f"Task {task.id} failed, stopping wave: {error}")
            wave_result.failure_count += 1
            return True  # Continue to record other failures

        elif self.strategy == FailureStrategy.CONTINUE:
            logger.warning(f"Task {task.id} failed, continuing: {error}")
            wave_result.failure_count += 1
            return True

        elif self.strategy == FailureStrategy.RETRY:
            return await self._retry_task(task, error, wave_result)

        return False

    async def _retry_task(
        self,
        task: Task,
        error: Exception,
        wave_result: 'WaveResult'
    ) -> bool:
        """Attempt to retry a failed task."""
        current_retries = self.retry_counts.get(task.id, 0)

        if current_retries >= self.max_retries:
            logger.error(f"Task {task.id} exceeded max retries")
            wave_result.failure_count += 1
            return True

        self.retry_counts[task.id] = current_retries + 1
        logger.info(f"Retrying task {task.id} (attempt {current_retries + 1})")

        # Retry logic would be implemented here
        # For now, mark as needing retry
        return True
```

### Error Propagation

```python
def get_affected_waves(
    failed_task_id: str,
    wave_groups: Dict[int, List[Task]],
    task_map: Dict[str, Task]
) -> Set[int]:
    """
    Determine which waves are affected by a task failure.

    Returns:
        Set of wave numbers that cannot proceed
    """
    affected_waves = set()

    # Find all tasks that depend on the failed task
    def find_dependents(task_id: str, visited: Set[str] = None):
        if visited is None:
            visited = set()

        if task_id in visited:
            return
        visited.add(task_id)

        for task in task_map.values():
            if task_id in task.depends_on:
                # Find which wave this task is in
                for wave_num, wave_tasks in wave_groups.items():
                    if any(t.id == task.id for t in wave_tasks):
                        affected_waves.add(wave_num)

                # Recursively find dependents
                find_dependents(task.id, visited)

    find_dependents(failed_task_id)
    return affected_waves
```

### Retry with Exponential Backoff

```python
import random

async def execute_with_retry(
    task: Task,
    executor: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> Any:
    """
    Execute task with exponential backoff retry.

    Args:
        task: Task to execute
        executor: Execution function
        max_retries: Maximum retry attempts
        base_delay: Base delay in seconds

    Returns:
        Task result

    Raises:
        Exception: If all retries fail
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return await executor(task)
        except Exception as e:
            last_error = e

            if attempt < max_retries:
                # Exponential backoff with jitter
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(
                    f"Task {task.id} failed (attempt {attempt + 1}), "
                    f"retrying in {delay:.2f}s: {e}"
                )
                await asyncio.sleep(delay)

    raise last_error
```

---

## Integration with BB5

### Using with task-execution.yaml

The wave-based execution integrates with BB5's existing task execution workflow:

```yaml
# task-execution.yaml with wave support
name: task-execution
version: "2.1.0"

phases:
  - id: research
    name: Pre-Execution Research
    required: true
    # ... research steps

  - id: execution
    name: Task Execution
    required: true
    depends_on: research

    # Wave-based execution configuration
    execution_strategy: wave_based

    wave_config:
      max_concurrent: 5
      continue_on_failure: false
      require_all_success: true
      failure_strategy: stop_all

    steps:
      - id: calculate_waves
        name: Calculate Execution Waves
        action: calculate_waves
        inputs:
          tasks: "{{ tasks }}"
        outputs:
          wave_groups: dict

      - id: execute_waves
        name: Execute Tasks in Waves
        action: execute_wave_based
        inputs:
          wave_groups: "{{ steps.calculate_waves.outputs.wave_groups }}"
          max_concurrent: "{{ phase.wave_config.max_concurrent }}"
        outputs:
          results: list
          failed_tasks: list

  - id: completion
    name: Documentation and Completion
    required: true
    depends_on: execution
    # ... completion steps
```

### Integration with Orchestrator.py

The existing `AgentOrchestrator` can be extended with wave-based execution:

```python
# Extension to /Users/shaansisodia/.blackbox5/2-engine/workflows/engine/Orchestrator.py

class AgentOrchestrator:
    # ... existing code ...

    async def execute_wave_based(
        self,
        workflow: Workflow,
        max_concurrent: int = 5
    ) -> Workflow:
        """
        Execute workflow using wave-based scheduling.

        This method groups steps into waves based on dependencies
        and executes each wave in parallel.

        Args:
            workflow: Workflow to execute
            max_concurrent: Maximum concurrent steps per wave

        Returns:
            Completed workflow
        """
        # Build task list from workflow steps
        tasks = [
            Task(
                id=step.id,
                name=step.name,
                depends_on=step.depends_on
            )
            for step in workflow.steps
        ]

        # Create wave orchestrator
        wave_orchestrator = WaveOrchestrator(
            max_concurrent=max_concurrent,
            continue_on_failure=False
        )

        # Map tasks back to workflow steps
        step_map = {step.id: step for step in workflow.steps}

        async def execute_step_task(task: Task) -> AgentResult:
            """Execute workflow step."""
            step = step_map[task.id]
            return await self._execute_step(step)

        # Execute using wave-based scheduling
        result = await wave_orchestrator.execute(
            tasks=tasks,
            executor_func=execute_step_task,
            workflow_id=workflow.id
        )

        # Update workflow status based on result
        if result.state == ExecutionState.COMPLETED:
            workflow.status = WorkflowStatus.COMPLETED
        else:
            workflow.status = WorkflowStatus.FAILED

        workflow.completed_at = datetime.now().isoformat()
        return workflow
```

### Task File Format with Dependencies

BB5 task files can specify dependencies in frontmatter:

```markdown
---
id: TASK-1769913005
title: Implement User Authentication
depends_on:
  - TASK-1769913003  # Database Schema
  - TASK-1769913004  # User Model
priority: HIGH
status: pending
---

# TASK-1769913005: Implement User Authentication

## Objective
Implement JWT-based user authentication system.

## Success Criteria
- [ ] User login endpoint
- [ ] Token generation
- [ ] Token validation middleware

## Context
Depends on database schema and user model being complete.

## Rollback Strategy
Remove auth middleware if issues occur.
```

### Reading Task Dependencies

```python
import re
import yaml
from pathlib import Path
from typing import List, Optional

def parse_task_file(task_path: Path) -> Optional[Task]:
    """
    Parse task file and extract dependencies.

    Args:
        task_path: Path to task markdown file

    Returns:
        Task object or None if parsing fails
    """
    content = task_path.read_text()

    # Extract frontmatter
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not frontmatter_match:
        return None

    try:
        frontmatter = yaml.safe_load(frontmatter_match.group(1))
    except yaml.YAMLError:
        return None

    return Task(
        id=frontmatter.get('id', task_path.stem),
        name=frontmatter.get('title', 'Untitled'),
        depends_on=frontmatter.get('depends_on', []),
        metadata={
            'priority': frontmatter.get('priority'),
            'status': frontmatter.get('status'),
            'file_path': str(task_path)
        }
    )

def load_tasks_from_directory(tasks_dir: Path) -> List[Task]:
    """Load all tasks from a directory."""
    tasks = []

    for task_file in tasks_dir.glob('TASK-*.md'):
        task = parse_task_file(task_file)
        if task:
            tasks.append(task)

    return tasks
```

---

## Wave Flow Diagrams

### Simple Diamond Pattern

```
┌──────────────────────────────────────────────────────────────┐
│                    DIAMOND PATTERN                           │
│                    (A → [B,C] → D)                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Wave 0: Setup                                               │
│  ┌─────────────────┐                                         │
│  │   Setup Infra   │                                         │
│  │    (task-001)   │                                         │
│  │   No deps       │                                         │
│  └────────┬────────┘                                         │
│           │                                                  │
│           ▼                                                  │
│  Wave 1: Parallel Build                                      │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │  Build Frontend │    │  Build Backend  │                 │
│  │   (task-002)    │    │   (task-003)    │                 │
│  │  deps: [001]    │    │  deps: [001]    │                 │
│  │                 │    │                 │                 │
│  │  ╔═══════════╗  │    │  ╔═══════════╗  │                 │
│  │  ║ PARALLEL  ║  │    │  ║ PARALLEL  ║  │                 │
│  │  ╚═══════════╝  │    │  ╚═══════════╝  │                 │
│  └────────┬────────┘    └────────┬────────┘                 │
│           │                      │                           │
│           └──────────┬───────────┘                           │
│                      │                                       │
│                      ▼                                       │
│  Wave 2: Integration                                         │
│  ┌─────────────────┐                                         │
│  │  Integration    │                                         │
│  │    Tests        │                                         │
│  │   (task-004)    │                                         │
│  │ deps: [002,003] │                                         │
│  └─────────────────┘                                         │
│                                                              │
│  Timeline:                                                   │
│  ─────────────────────────────────────────►                  │
│  │ Wave 0 │  Wave 1  │ Wave 2 │                              │
│  │  1s    │   3s     │   2s   │  = 6s total                  │
│  │        │ [parallel]│       │                              │
│  │        │ 2s each  │       │                              │
│                                                              │
│  Sequential would be: 1+3+3+2 = 9s                           │
│  Wave-based: 33% faster!                                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Complex Multi-Level DAG

```
┌──────────────────────────────────────────────────────────────┐
│                  COMPLEX DAG EXECUTION                       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Wave 0: Foundation                                          │
│  ┌──────────┐  ┌──────────┐                                 │
│  │ Setup DB │  │Setup Cache│                                │
│  │  [001]   │  │   [002]  │                                 │
│  └────┬─────┘  └────┬─────┘                                 │
│       │             │                                        │
│       ▼             ▼                                        │
│  Wave 1: Services                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  User    │  │  Auth    │  │  Config  │                  │
│  │ Service  │  │ Service  │  │ Service  │                  │
│  │  [003]   │  │  [004]   │  │  [005]   │                  │
│  │deps:[001]│  │deps:[001,│  │deps:[002]│                  │
│  │          │  │   002]   │  │          │                  │
│  │ ╔══════╗ │  │ ╔══════╗ │  │ ╔══════╗ │                  │
│  │ ║PARAL-║ │  │ ║PARAL-║ │  │ ║PARAL-║ │                  │
│  │ ║LEL   ║ │  │ ║LEL   ║ │  │ ║LEL   ║ │                  │
│  │ ╚══════╝ │  │ ╚══════╝ │  │ ╚══════╝ │                  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
│       │             │             │                          │
│       └─────────────┼─────────────┘                          │
│                     │                                        │
│                     ▼                                        │
│  Wave 2: API Layer                                           │
│  ┌──────────────────────────────────┐                       │
│  │         API Gateway              │                       │
│  │            [006]                 │                       │
│  │    deps: [003, 004, 005]         │                       │
│  └────────────────┬─────────────────┘                       │
│                   │                                          │
│                   ▼                                          │
│  Wave 3: Testing                                             │
│  ┌──────────────────────────────────┐                       │
│  │      Integration Tests           │                       │
│  │            [007]                 │                       │
│  │       deps: [006]                │                       │
│  └──────────────────────────────────┘                       │
│                                                              │
│  Summary:                                                    │
│  ─────────────────────────────────────────►                  │
│  │ W0 │  W1  │  W2  │  W3 │                                   │
│  │ 2s │  4s  │  3s  │  5s │  = 14s total                     │
│  │    │[para]│      │     │                                   │
│  │    │ 4s→2s│      │     │                                   │
│                                                              │
│  Sequential: 2+4+4+4+3+3+5 = 25s                             │
│  Wave-based: 14s (44% faster!)                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Error Handling Flow

```
┌──────────────────────────────────────────────────────────────┐
│                  ERROR HANDLING FLOW                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Normal Execution:                                           │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│  │ Wave 0  │───→│ Wave 1  │───→│ Wave 2  │                 │
│  │ ✓✓✓     │    │ ✓✓✓     │    │ ✓✓✓     │                 │
│  └─────────┘    └─────────┘    └─────────┘                 │
│                                                              │
│  With Failure (STOP_ALL):                                    │
│  ┌─────────┐    ┌─────────┐    ╔═════════╗                 │
│  │ Wave 0  │───→│ Wave 1  │───→║ Wave 2  ║                 │
│  │ ✓✓✓     │    │ ✓✗✓     │    ║ SKIPPED ║                 │
│  └─────────┘    └────┬────┘    ╚═════════╝                 │
│                      │                                       │
│                      ▼                                       │
│                 ┌─────────┐                                  │
│                 │  FAIL   │                                  │
│                 └─────────┘                                  │
│                                                              │
│  With Failure (CONTINUE):                                    │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│  │ Wave 0  │───→│ Wave 1  │───→│ Wave 2  │                 │
│  │ ✓✓✓     │    │ ✓✗✓     │    │ ✓✓✓     │                 │
│  └─────────┘    └─────────┘    └─────────┘                 │
│                   (1 fail)       (deps met)                  │
│                                                              │
│  With Retry:                                                 │
│  ┌─────────┐    ┌─────────────────────┐    ┌─────────┐     │
│  │ Wave 0  │───→│       Wave 1        │───→│ Wave 2  │     │
│  │ ✓✓✓     │    │ ✓⟳✓ (retry task)  │    │ ✓✓✓     │     │
│  └─────────┘    │ 2nd attempt succeeds│    └─────────┘     │
│                 └─────────────────────┘                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Best Practices

### 1. Keep Dependencies Minimal

```python
# Good: Clear, minimal dependencies
task_c.depends_on = ["task_a", "task_b"]

# Bad: Unnecessary transitive dependencies
task_c.depends_on = ["task_a", "task_b", "task_a_dep"]
# task_a_dep is already implied by task_a
```

### 2. Balance Wave Sizes

```python
def analyze_wave_balance(wave_groups: Dict[int, List[Task]]) -> Dict[str, Any]:
    """Analyze wave size distribution."""
    sizes = [len(tasks) for tasks in wave_groups.values()]

    return {
        "total_waves": len(wave_groups),
        "largest_wave": max(sizes),
        "smallest_wave": min(sizes),
        "average_size": sum(sizes) / len(sizes),
        "imbalance_ratio": max(sizes) / min(sizes) if min(sizes) > 0 else 0,
        "recommendation": "Consider breaking large waves" if max(sizes) > 10 else "Good balance"
    }
```

### 3. Set Appropriate Concurrency Limits

```python
# CPU-bound tasks: Lower concurrency
cpu_orchestrator = WaveOrchestrator(max_concurrent=4)

# IO-bound tasks: Higher concurrency
io_orchestrator = WaveOrchestrator(max_concurrent=20)

# Mixed workload: Medium with adaptive scaling
mixed_orchestrator = WaveOrchestrator(max_concurrent=8)
```

### 4. Monitor and Log

```python
import json

def log_wave_metrics(result: ExecutionResult, workflow_id: str):
    """Log wave execution metrics."""
    metrics = {
        "workflow_id": workflow_id,
        "state": result.state.value,
        "waves_completed": result.waves_completed,
        "parallelism_efficiency": result.steps_completed / result.waves_completed,
        "total_duration": (
            (result.completed_at - result.started_at).total_seconds()
            if result.completed_at else None
        ),
        "wave_breakdown": result.wave_details
    }

    logger.info(f"Wave metrics: {json.dumps(metrics, indent=2)}")
```

### 5. Handle Circular Dependencies

```python
def validate_no_cycles(tasks: List[Task]) -> Optional[List[str]]:
    """
    Validate that tasks have no circular dependencies.

    Returns:
        List of task IDs forming a cycle, or None if no cycles
    """
    graph = build_dependency_graph(tasks)

    # DFS-based cycle detection
    visited = set()
    rec_stack = set()

    def dfs(node: str, path: List[str]) -> Optional[List[str]]:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                cycle = dfs(neighbor, path)
                if cycle:
                    return cycle
            elif neighbor in rec_stack:
                # Found cycle
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]

        rec_stack.remove(node)
        path.pop()
        return None

    for node in graph:
        if node not in visited:
            cycle = dfs(node, [])
            if cycle:
                return cycle

    return None
```

---

## References

### Related Files

- `/Users/shaansisodia/.blackbox5/2-engine/workflows/engine/Orchestrator.py` - Core orchestration logic
- `/Users/shaansisodia/.blackbox5/2-engine/instructions/workflows/task-execution.yaml` - Task execution workflow
- `/Users/shaansisodia/.blackbox5/2-engine/agents/framework/task_schema.py` - Task data structures
- `/Users/shaansisodia/.blackbox5/1-docs/05-examples/code/wave_execution_example.py` - Usage examples

### External References

- [Apache Airflow DAGs](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html) - DAG execution patterns
- [Temporal Workflows](https://docs.temporal.io/workflows) - Workflow orchestration
- [Prefect Task Dependencies](https://docs.prefect.io/latest/concepts/tasks/) - Task dependency management
- [Luigi Task Pipeline](https://luigi.readthedocs.io/en/stable/) - Pipeline execution patterns

---

## Summary

Wave-based execution in BlackBox5 provides:

1. **Automatic Parallelism**: Tasks without dependencies run simultaneously
2. **Dependency Safety**: Tasks only execute after dependencies complete
3. **Progress Visibility**: Clear wave-by-wave progress tracking
4. **Failure Isolation**: Contain failures to specific waves
5. **Resource Control**: Configurable concurrency limits

The key insight is that most workflows have inherent parallelism that sequential execution wastes. By calculating waves from the dependency graph, we can execute independent work in parallel while respecting all dependencies.

**Remember**: The goal is not maximum parallelism, but optimal parallelism - balancing speed against resource constraints and dependency requirements.
