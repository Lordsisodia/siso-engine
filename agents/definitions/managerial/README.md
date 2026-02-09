# BlackBox5 Managerial Agent

A comprehensive managerial agent system for orchestrating, monitoring, and managing teams of AI agents working on the BlackBox5 codebase.

## Overview

The Managerial Agent provides:

1. **Vibe Kanban Integration** - Full control over task creation, agent spawning, and status tracking
2. **Management Memory** - Persistent tracking of all events, histories, and performance metrics
3. **Task Lifecycle Management** - Complete workflows from planning to archival
4. **Team Dashboard** - Real-time monitoring with alerts and visualization
5. **Merge Coordination** - Automated review and merge workflows

## Architecture

```
agents/managerial/
├── skills/
│   ├── vibe_kanban_manager.py    # Vibe Kanban API client
│   └── team_dashboard.py          # Monitoring dashboard
├── memory/
│   └── management_memory.py       # Persistent memory system
├── task_lifecycle.py              # Lifecycle workflows
└── README.md                      # This file
```

## Components

### 1. VibeKanbanManager (`skills/vibe_kanban_manager.py`)

Complete interface to Vibe Kanban for task and agent management.

**Key Features:**
- Create, update, delete tasks
- Spawn and monitor agents
- Track dependencies
- Get workspace changes
- Coordinate merges

**Example:**
```python
from agents.managerial.skills.vibe_kanban_manager import VibeKanbanManager

manager = VibeKanbanManager()

# Create a task
task = manager.create_task(
    title="Fix API bug",
    description="Fix the critical bug in main.py"
)

# Start an agent
agent = manager.start_agent(
    task_id=task.id,
    executor="CLAUDE_CODE"
)

# Monitor to completion
manager.monitor_task(task.id)
```

### 2. ManagementMemory (`memory/management_memory.py`)

Persistent memory system for tracking all management events.

**Key Features:**
- Event logging (task_created, agent_spawned, merge_succeeded, etc.)
- Task history tracking
- Agent performance metrics
- Dependency graph management
- Merge decision tracking
- Metrics history for trends

**Example:**
```python
from agents.managerial.memory.management_memory import get_management_memory

memory = get_management_memory()

# Record an event
memory.record_event(
    EventType.TASK_CREATED,
    task_id="abc-123",
    task_title="Fix bug"
)

# Get agent stats
stats = memory.get_agent_stats()
print(f"Success rate: {stats['successful']}/{stats['total']}")
```

### 3. TaskLifecycleManager (`task_lifecycle.py`)

Orchestrates complete task lifecycles from planning to completion.

**Stages:**
1. **Planning** - Create task plans with estimates and dependencies
2. **Creation** - Create tasks in Vibe Kanban
3. **Assignment** - Start agents on tasks
4. **Monitoring** - Track progress to completion
5. **Review** - Review completed work
6. **Merge** - Merge successful tasks
7. **Archival** - Archive completed tasks

**Example:**
```python
from agents.managerial.task_lifecycle import TaskLifecycleManager, TaskPlan, Priority

lifecycle = TaskLifecycleManager()

# Plan a task
plan = lifecycle.plan_task(
    title="Fix critical bug",
    description="Fix the bug in main.py",
    priority=Priority.CRITICAL,
    estimated_duration=120
)

# Execute from plan to completion
result = lifecycle.execute_single_task(plan)
```

**Execute a wave of parallel tasks:**
```python
plans = [
    lifecycle.plan_task("Task 1", "Description 1"),
    lifecycle.plan_task("Task 2", "Description 2"),
    lifecycle.plan_task("Task 3", "Description 3"),
]

results = lifecycle.execute_wave(plans)
```

### 4. TeamDashboard (`skills/team_dashboard.py`)

Real-time monitoring dashboard with alerts and metrics.

**Key Features:**
- Agent status monitoring
- Queue status tracking
- Resource utilization
- Performance metrics
- Alert generation
- Multiple render modes (text, JSON, HTML)

**Example:**
```python
from agents.managerial.skills.team_dashboard import get_dashboard

dashboard = get_dashboard()

# Get snapshot
snapshot = dashboard.get_snapshot()

# Render as text
print(dashboard.render_text())

# Watch continuously
dashboard.watch(interval=10)
```

**From command line:**
```bash
# Show dashboard once
python3 -m agents.managerial.skills.team_dashboard

# Watch dashboard (auto-refresh)
python3 -m agents.managerial.skills.team_dashboard watch
python3 -m agents.managerial.skills.team_dashboard watch 5  # 5-second interval
```

## Complete Workflows

### Creating and Executing a Single Task

```python
from agents.managerial.task_lifecycle import get_lifecycle_manager, TaskPlan, Priority

lifecycle = get_lifecycle_manager()

# 1. Plan the task
plan = lifecycle.plan_task(
    title="PLAN-011: Add Unit Tests",
    description="Add comprehensive unit tests for the routing module",
    priority=Priority.HIGH,
    estimated_duration=180  # 3 hours
)

# 2. Execute end-to-end
result = lifecycle.execute_single_task(
    plan=plan,
    executor="CLAUDE_CODE",
    auto_merge=True  # Automatically merge on completion
)

print(f"Success: {result.success}")
print(f"Files modified: {result.files_modified}")
```

### Executing a Wave of Parallel Tasks

```python
# 1. Plan multiple tasks
plans = [
    lifecycle.plan_task(
        title="PLAN-012: Fix bug A",
        description="Fix critical bug A",
        priority=Priority.CRITICAL
    ),
    lifecycle.plan_task(
        title="PLAN-013: Add feature B",
        description="Implement feature B",
        priority=Priority.NORMAL,
        dependencies=["<PLAN-012-task-id>"]  # Depends on PLAN-012
    ),
]

# 2. Execute wave
results = lifecycle.execute_wave(
    plans=plans,
    executor="CLAUDE_CODE",
    auto_merge=True
)

# 3. Check results
for task_id, result in results.items():
    if result.success:
        print(f"✅ {task_id} succeeded")
    else:
        print(f"❌ {task_id} failed")
```

### Monitoring Active Agents

```python
from agents.managerial.skills.team_dashboard import get_dashboard

dashboard = get_dashboard()

# Get all active agents
active_agents = dashboard.get_active_agents()
for agent in active_agents:
    print(f"{agent.task_title}: {agent.runtime:.1f}min")

# Check for stuck agents
stuck = dashboard.get_stuck_agents(timeout_minutes=60)
for agent in stuck:
    print(f"⚠️ Agent may be stuck: {agent.task_title}")

# Get alerts
alerts = dashboard.generate_alerts()
for alert in alerts:
    print(f"{alert.level.value}: {alert.message}")
```

### Reviewing and Merging Completed Tasks

```python
from agents.managerial.skills.vibe_kanban_manager import VibeKanbanManager

manager = VibeKanbanManager()

# Get tasks in review
review_tasks = manager.list_tasks(status=TaskStatus.IN_REVIEW)

for task in review_tasks:
    # Get changes
    changes = manager.get_workspace_changes(task.id)
    print(f"\n{task.title}")
    print(f"  Modified: {changes['files_modified']}")
    print(f"  Created: {changes['files_created']}")

    # Review
    review = manager.review_task(task.id)

    # If approved, merge
    if input("Approve merge? (y/n): ").lower() == 'y':
        success = manager.merge_task(task.id, merge_method="merge")
        if success:
            print(f"✅ Merged successfully")
        else:
            print(f"❌ Merge failed")
```

## Memory Storage

All management data is stored in:
```
blackbox5/5-project-memory/management/
├── events.json              # All management events
├── task_histories.json      # Complete task histories
├── agent_performance.json   # Agent performance metrics
├── dependency_graph.json    # Task dependencies
├── merge_decisions.json     # Merge history
└── metrics_history.json     # Metrics over time
```

## Dashboard Output

### Text Dashboard
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    BLACKBOX5 TEAM DASHBOARD                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Timestamp: 2026-01-19T22:04:49.554408+00:00

📊 METRICS
--------------------------------------------------------------------------------
  Tasks: 11 total | 0 in progress | 3 in review | 0 completed
  Success Rate: 0.0%

🤖 ACTIVE AGENTS (0)
--------------------------------------------------------------------------------
  No active agents

📋 QUEUE STATUS
--------------------------------------------------------------------------------
  Pending: 8 | In Progress: 0 | In Review: 3 | Blocked: 0
```

### HTML Dashboard
Auto-refreshing HTML dashboard with:
- Real-time metrics cards
- Active agent list
- Alert notifications
- 10-second auto-refresh

## Integration with BlackBox5

The Managerial Agent is designed to be used as a **skill** by other BlackBox5 agents:

```python
# In your agent code
from agents.managerial.skills.vibe_kanban_manager import create_manager

# Get manager instance
manager = create_manager()

# Use it to manage your team
tasks = manager.list_tasks()
metrics = manager.get_metrics()
```

## Configuration

Default configuration (can be overridden):

```python
VibeKanbanManager(
    base_url="http://127.0.0.1:57276",
    project_id="48ec7737-b706-4817-b86c-5786163a0139",
    repo_id="b5b86bc2-fbfb-4276-b15e-01496d647a81",
    repo_path="~/.blackbox5"
)

ManagementMemory(
    memory_path="/Users/.../blackbox5/5-project-memory/management"
)
```

## Event Types

The system tracks these events:
- `task_created` - New task created
- `task_started` - Agent started on task
- `task_completed` - Task completed successfully
- `task_failed` - Task failed
- `task_blocked` - Task blocked by dependencies
- `agent_spawned` - Agent process spawned
- `agent_completed` - Agent finished successfully
- `agent_failed` - Agent failed
- `merge_attempted` - Merge attempted
- `merge_succeeded` - Merge succeeded
- `merge_failed` - Merge failed
- `review_requested` - Review requested
- `review_completed` - Review completed
- `blocker_resolved` - Blocking task completed
- `dependency_added` - Dependency added
- `dependency_removed` - Dependency removed

## Task Status Flow

```
todo → inprogress → inreview → done
  ↓
cancelled
```

## Alerts

The dashboard generates alerts for:
- **CRITICAL**: Failed tasks, merge failures
- **WARNING**: Stuck agents (60min+ inactivity), excessive blocking
- **INFO**: Queue backup, new tasks created

## Best Practices

1. **Always plan tasks before execution** - Use `TaskPlan` for structure
2. **Set dependencies explicitly** - Prevents incorrect execution order
3. **Monitor actively** - Use dashboard to track progress
4. **Review before merging** - Check changes with `review_task()`
5. **Track metrics** - Use memory system for long-term insights
6. **Handle failures gracefully** - Check `ExecutionResult.success` before proceeding

## Troubleshooting

### Agents not starting
- Check Vibe Kanban is running: `http://127.0.0.1:57276`
- Verify project_id and repo_id are correct
- Check task dependencies are satisfied

### Merge failures
- Check for merge conflicts in workspace
- Verify branch exists
- Try `merge_method="squash"` as alternative

### Dashboard not updating
- Clear memory cache: `memory.clear()`
- Restart Vibe Kanban
- Check API connectivity

## License

Part of BlackBox5 AI Development Platform
