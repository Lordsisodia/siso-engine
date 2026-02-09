# Event Handlers

> Output handlers for the Agent Output Bus

## Overview

The `handlers/` directory contains handlers that process agent outputs from the AgentOutputBus. Each handler receives parsed `OutputEvent` objects and routes them to appropriate systems:

- **DatabaseHandler** - Persistent logging to SQLite
- **NotificationHandler** - Alerts for failures/partial successes
- **VibeKanbanHandler** - Create/update Kanban tasks
- **SchedulerHandler** - Queue next_steps as autonomous tasks

## File Structure

```
handlers/
├── __init__.py              # Package exports with availability checks
├── database_handler.py      # SQLite logging handler
├── notification_handler.py  # Notification/alert handler
├── vibe_handler.py          # Vibe Kanban integration
└── scheduler_handler.py     # Autonomous task scheduler integration
```

## Architecture

All handlers inherit from `OutputHandler` base class:

```python
from AgentOutputBus import OutputHandler, HandlerResult, OutputEvent

class MyHandler(OutputHandler):
    def handle(self, event: OutputEvent) -> HandlerResult:
        # Process event
        return HandlerResult(success=True, message="Done", data={})
```

## Handlers

### DatabaseHandler
Logs agent outputs to SQLite for analytics and persistence.

**Features:**
- Automatic table creation with indexes
- JSON serialization for complex fields
- Query interface for analytics
- Statistics aggregation

**Schema:**
- timestamp, agent_name, task_id, status
- summary, deliverables, next_steps
- metadata, human_content, raw_output

**Usage:**
```python
from handlers import DatabaseHandler

handler = DatabaseHandler(db_path="outputs.db")
bus.register_handler(handler)

# Query outputs
results = handler.query_outputs(agent_name="coder", status="success")
stats = handler.get_stats()  # success_rate, total, etc.
```

### NotificationHandler
Sends notifications based on agent output status.

**Features:**
- Configurable notification triggers
- Built-in logging notifications
- Custom callback registration
- Slack integration (SlackNotificationHandler)

**Notification Types:**
- Failure alerts (ERROR log + optional Slack)
- Partial success warnings (WARNING log)
- Next steps info (INFO log)

**Usage:**
```python
from handlers import NotificationHandler

handler = NotificationHandler(
    notify_on_failure=True,
    notify_on_partial=True,
    notify_on_success=False
)
bus.register_handler(handler)

# Custom callback
handler.register_callback("failed", my_alert_function)
```

### VibeKanbanHandler
Integrates agent outputs with Vibe Kanban board.

**Status Mapping:**
| Agent Status | Kanban Status |
|--------------|---------------|
| success | DONE |
| partial | IN_REVIEW |
| failed | TODO |

**Features:**
- Auto-create tasks from agent outputs
- Update existing tasks by task_id
- Markdown descriptions with metadata
- Deliverables and next steps tracking

**Requirements:** `vibe_kanban_integration` module (optional dependency)

**Usage:**
```python
from handlers import VibeKanbanHandler

handler = VibeKanbanHandler(
    vibe_kanban_url="http://127.0.0.1:57276",
    project_id="uuid",
    auto_create_tasks=True
)
bus.register_handler(handler)
```

### SchedulerHandler
Queues `next_steps` from agent outputs as autonomous tasks.

**Priority Mapping:**
| Agent Status | Task Priority |
|--------------|---------------|
| success | LOW |
| partial | MEDIUM |
| failed | HIGH |

**Features:**
- Auto-queue next_steps as tasks
- Parent task dependency tracking
- Async task execution wrapper
- Integration with TaskScheduler

**Requirements:** `scheduler` module (optional dependency)

**Usage:**
```python
from handlers import SchedulerHandler

handler = SchedulerHandler(
    auto_queue_tasks=True,
    depends_on_parent=True
)
bus.register_handler(handler)
```

## Handler Registration

Handlers are registered with the AgentOutputBus:

```python
from AgentOutputBus import AgentOutputBus
from handlers import DatabaseHandler, NotificationHandler

bus = AgentOutputBus()
bus.initialize()

# Register handlers
bus.register_handler(DatabaseHandler())
bus.register_handler(NotificationHandler())

# Now all agent outputs are routed to handlers
bus.receive(agent_output)
```

## Conditional Imports

Handlers with external dependencies use conditional imports:

```python
# In __init__.py
try:
    from .vibe_handler import VibeKanbanHandler
    _vibe_available = True
except ImportError:
    _vibe_available = False
    VibeKanbanHandler = None
```

This allows the package to work even if optional dependencies are missing.

## OutputEvent Structure

Handlers receive `OutputEvent` objects:

```python
@dataclass
class OutputEvent:
    agent_name: str
    task_id: str
    status: OutputStatus  # SUCCESS, PARTIAL, FAILED
    summary: str
    deliverables: List[str]
    next_steps: List[str]
    metadata: Dict[str, Any]
    human_content: str
    raw_output: str
    timestamp: datetime
```

## Related Components

- **AgentOutputBus** (`../AgentOutputBus.py`) - Central router
- **AgentOutputParser** (`../AgentOutputParser.py`) - Output parsing
- **Client Libraries** (`../client/`) - Agent execution clients
