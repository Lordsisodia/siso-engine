# Agent Output Bus - Architecture Design

## Purpose

Single entry point for all agent outputs. Routes structured outputs to:
- Vibe Kanban (task cards)
- Scheduler (next steps queue)
- Database (logging/analytics)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Execution                           │
│  (Claude Code CLI, GLM, or any agent)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              AgentOutputBus.receive(output)                 │
│                                                               │
│  1. Parse structured output                                  │
│  2. Validate format                                          │
│  3. Extract metadata                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌─────────────────────────────────────┐
              │  Router (based on status/summary)  │
              └─────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┬───────────────┐
         │               │               │               │
         ▼               ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │Vibe    │    │Scheduler│    │Database│    │Notifier│
    │Kanban  │    │         │    │         │    │         │
    │Integration│    │Queue   │    │Log      │    │Slack/   │
    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

## Components

### 1. AgentOutputBus (Main Class)
- `receive(output)` - Main entry point
- `register_handler(callback)` - Add custom handlers
- `process(output)` - Parse and route

### 2. Handlers
- `VibeKanbanHandler` - Create/update Kanban cards
- `SchedulerHandler` - Queue next steps
- `DatabaseHandler` - Log to SQLite
- `NotificationHandler` - Send alerts

### 3. Integration Points
- Connect to `vibe_kanban_integration.py`
- Connect to `runtime/scheduler.py`
- Use `03-knowledge/storage` for database

## Data Flow

1. Agent completes task → produces structured output
2. AgentOutputBus receives output
3. Parse → extract status, deliverables, next_steps
4. Route to handlers:
   - Vibe Kanban: Create/update task card with status
   - Scheduler: Queue next_steps as AutonomousTask
   - Database: Log for analytics
   - Notifications: Alert on failures

## Files

- `AgentOutputBus.py` - Main bus implementation
- `handlers/vibe_handler.py` - Vibe Kanban integration
- `handlers/scheduler_handler.py` - Scheduler integration
- `handlers/database_handler.py` - Database logging
- `tests/test_agent_output_bus.py` - Integration tests

## Dependencies

- Existing: `vibe_kanban_integration.py`, `scheduler.py`
- New: `AgentOutputParser.py` (already exists)
- Storage: `03-knowledge/storage` (already exists)
