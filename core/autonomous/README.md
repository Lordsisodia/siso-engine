# Autonomous Agent System

Complete implementation of the autonomous multi-agent system with Redis coordination.

## Quick Start

### Prerequisites

1. **Install Redis**
   ```bash
   # macOS
   brew install redis
   brew services start redis

   # Ubuntu/Debian
   sudo apt-get install redis-server
   sudo systemctl start redis
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Test Redis connectivity**
   ```bash
   python ../../../examples/autonomous/redis_latency_test.py
   ```

### Run the Demo

```bash
python ../../../examples/autonomous/basic_demo.py
```

This will demonstrate:
- Creating tasks from a goal
- Autonomous agents claiming and executing tasks
- Real-time status reporting
- Event-driven coordination

## Project Structure

```
core/autonomous/
├── schemas/
│   └── task.py              # Task dataclass and registry
├── stores/
│   ├── json_store.py        # JSON file-based storage
│   └── sqlite_store.py      # SQLite storage (production)
├── redis/
│   └── coordinator.py       # Redis coordination layer
├── agents/
│   ├── supervisor.py        # Creates and manages tasks
│   ├── autonomous.py        # Claims and executes tasks
│   └── interface.py         # User liaison and reporting
├── requirements.txt
└── README.md

examples/autonomous/
├── basic_demo.py            # Basic system demonstration
└── redis_latency_test.py    # Redis performance test
```

## Component Overview

### Task System

**schemas/task.py**
- `Task`: Production-ready task dataclass
- `TaskState`: Task lifecycle states (BACKLOG → PENDING → ASSIGNED → ACTIVE → DONE)
- `TaskRegistry`: Central task management with multiple backends
- `TaskMetrics`: Execution time, resource usage, quality metrics

### Storage Backends

**stores/json_store.py**
- Simple file-based storage
- Git-tracked for easy version control
- Ideal for development and testing

**stores/sqlite_store.py**
- ACID-compliant storage
- Built-in indexing for performance
- Event logging for audit trail
- Production-ready

### Redis Coordination

**redis/coordinator.py**
- `RedisCoordinator`: Main coordination class
- Pub/sub for instant notifications (1ms latency)
- Sorted sets for priority task queues
- Atomic operations for conflict prevention
- Event streams for replay and debugging

Key channels:
- `tasks:new`: New task notifications
- `tasks:claimed`: Task claim notifications
- `tasks:updated`: Task status updates
- `tasks:complete`: Task completion notifications
- `tasks:failed`: Task failure notifications

### Agents

**agents/supervisor.py**
- Creates tasks from high-level goals
- Manages dependencies between tasks
- Publishes tasks to Redis
- Monitors progress and resolves blockers
- Never executes tasks (separation of concerns)

**agents/autonomous.py**
- Subscribes to Redis task channels
- Claims available tasks based on capabilities
- Executes tasks independently
- Handles retries and failures
- Reports status and results

**agents/interface.py**
- Reports system status to users
- Routes user commands
- Provides human-readable summaries
- Creates manual tasks
- Cancels tasks

## Usage Examples

### Basic Setup

```python
from schemas.task import TaskRegistry
from stores.sqlite_store import SQLiteTaskStore
from redis.coordinator import RedisCoordinator, RedisConfig
from agents import SupervisorAgent, AutonomousAgent, InterfaceAgent

# Initialize components
registry = TaskRegistry(backend="sqlite")
redis = RedisCoordinator(RedisConfig(host="localhost", port=6379))

# Create agents
supervisor = SupervisorAgent(registry, redis)
interface = InterfaceAgent(registry, redis)

# Create autonomous agents
dev_agent = AutonomousAgent(
    agent_id="dev-1",
    capabilities=["development", "frontend"],
    task_registry=registry,
    redis_coordinator=redis
)
dev_agent.start()
```

### Submit a Goal

```python
# Supervisor breaks down goal into tasks
supervisor.execute_goal("Build user authentication system")

# Tasks are automatically published to Redis
# Autonomous agents claim and execute them
```

### Check Status

```python
# Get system status
status = interface.get_system_status()
print(interface.format_status_report(status))

# Get task details
summary = interface.get_task_summary("task-123")
print(summary)
```

### Create Manual Task

```python
# Create a task manually
task_id = interface.create_task(
    title="Write documentation",
    description="Document the authentication system",
    type="development",
    priority=7
)
```

## Architecture Patterns

### OODA Loop for Autonomy

Each autonomous agent runs an OODA loop:

1. **Observe**: Check Redis for available tasks
2. **Orient**: Understand task requirements
3. **Decide**: Choose whether to claim task
4. **Act**: Execute the task
5. **Check**: Report results and update state

### Event-Driven Coordination

```
Supervisor creates task
         ↓
Publishes to Redis (1ms)
         ↓
Autonomous agents receive instantly
         ↓
First agent claims (atomic operation)
         ↓
Executes task
         ↓
Publishes completion
         ↓
Other agents see completion
         ↓
Dependent tasks become available
```

### Atomic Task Claiming

Uses Redis sorted sets and locks:

```python
# Remove from pending queue (atomic)
claimed = redis.zrem("tasks:pending", task_id)

if claimed:
    # Only one agent gets it
    # Set assignee
    # Publish claim event
```

## Performance Characteristics

### Latency

- Redis pub/sub: ~1ms
- Task claiming: ~1ms
- Status updates: ~1ms

### Scalability

- Unlimited autonomous agents (limited by Redis)
- Sub-millisecond coordination overhead
- Linear scaling with agent count

### Throughput

- Thousands of tasks per second
- Limited by task execution, not coordination
- Parallel execution via multiple agents

## Production Checklist

- [ ] Redis configured with persistence (RDB/AOF)
- [ ] Task registry backed by PostgreSQL (not SQLite)
- [ ] Agent restart handling
- [ ] Dead letter queue for failed tasks
- [ ] Circuit breakers for cascading failures
- [ ] Metrics collection and monitoring
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Git worktree isolation for each agent
- [ ] Automatic cleanup of completed worktrees

## Troubleshooting

### Redis Connection Failed

```
Error: Cannot connect to Redis at localhost:6379
```

**Solution**: Start Redis server
```bash
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

### Tasks Not Being Claimed

**Check**:
1. Are autonomous agents running?
2. Do agent capabilities match task types?
3. Are dependencies satisfied?

```python
# Check agent status
agents = redis.get_all_agents()

# Check pending tasks
pending = redis.get_pending_tasks()
```

### High Memory Usage

**Solution**: Redis can be configured with maxmemory

```bash
redis-cli CONFIG SET maxmemory 1gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## Next Steps

1. Run the basic demo to understand the system
2. Modify the demo to test your use case
3. Integrate with your existing Claude Code workflow
4. Add custom task types and execution logic
5. Deploy Redis for production use

## Documentation

- [Redis Pub/Sub](https://redis.io/docs/manual/pubsub/)
- [Redis Sorted Sets](https://redis.io/data-types/sorted-sets/)
- Task Tracking Guide: `1-docs/guides/autonomous/task-tracking.md`
- Redis Coordination Guide: `1-docs/guides/autonomous/redis-guide.md`
- Plandex Research: `1-docs/research/autonomous-system/plandex-research.md`
- Auto-Claude Research: `1-docs/research/autonomous-system/auto-claude-research.md`
- System Overview: `1-docs/guides/autonomous/autonomous-system-overview.md`
