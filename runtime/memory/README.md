# AgentMemory System

A simplified persistent memory system for BlackBox5 agents, adapted from Auto-Claude's Graphiti integration.

## Overview

AgentMemory provides each agent with its own isolated memory environment using JSON-based storage. It enables agents to:

- **Track Sessions**: Record task executions and results
- **Store Insights**: Save learned patterns, gotchas, and discoveries
- **Accumulate Context**: Build knowledge across sessions
- **Search Memory**: Find relevant insights quickly
- **Report Statistics**: Track performance and learning

## Architecture

### Storage Structure

```
.blackbox5/data/memory/
├── agent-1/
│   ├── sessions.json    # Execution history
│   ├── insights.json    # Learned insights
│   └── context.json     # Accumulated knowledge
├── agent-2/
│   ├── sessions.json
│   ├── insights.json
│   └── context.json
└── ...
```

Each agent has completely isolated memory - no data sharing between agents.

### Data Models

#### MemorySession
```python
@dataclass
class MemorySession:
    session_id: str
    timestamp: str
    task: str
    result: str
    metadata: dict[str, Any]
    success: bool
    duration_seconds: Optional[float]
```

#### MemoryInsight
```python
@dataclass
class MemoryInsight:
    insight_id: str
    timestamp: str
    content: str
    category: str  # pattern, gotcha, discovery, optimization
    confidence: float  # 0.0 to 1.0
    source_session: Optional[str]
    metadata: dict[str, Any]
```

#### MemoryContext
```python
@dataclass
class MemoryContext:
    context_id: str
    agent_id: str
    created_at: str
    updated_at: str
    patterns: list[str]
    gotchas: list[str]
    discoveries: list[str]
    preferences: dict[str, Any]
    statistics: dict[str, Any]
```

## Usage

### Basic Usage

```python
from engine.memory.AgentMemory import AgentMemory

# Create memory for an agent
memory = AgentMemory(agent_id="my-agent")

# Track a session
session_id = memory.add_session(
    task="Implement feature X",
    result="Successfully completed",
    success=True,
    duration_seconds=120.5
)

# Store insights
memory.add_insight(
    content="Use TypeScript for type safety",
    category="pattern",
    confidence=0.9
)

# Retrieve context
context = memory.get_context()
print(f"Patterns: {context['patterns']}")
print(f"Gotchas: {context['gotchas']}")
```

### Session Tracking

```python
# Add a session with metadata
memory.add_session(
    task="Refactor database queries",
    result="Optimized 15 queries",
    success=True,
    duration_seconds=300,
    metadata={
        "files_modified": ["models.py", "queries.py"],
        "queries_optimized": 15,
        "performance_improvement": "50%"
    }
)

# Get recent sessions
recent = memory.get_sessions(limit=10)

# Get only successful sessions
successful = memory.get_sessions(successful_only=True)
```

### Insight Management

```python
# Add different types of insights
memory.add_insight(
    "Use React hooks for component state",
    category="pattern",
    confidence=0.95
)

memory.add_insight(
    "Always validate user input on server side",
    category="gotcha",
    confidence=1.0
)

memory.add_insight(
    "Redis caching reduces database load by 80%",
    category="discovery",
    confidence=0.8
)

# Get insights by category
patterns = memory.get_insights(category="pattern")

# Get high-confidence insights
confident = memory.get_insights(min_confidence=0.9)

# Search insights
results = memory.search_insights("React hooks")
```

### Context Updates

```python
# Update context directly
memory.update_context({
    "patterns": ["New pattern 1", "New pattern 2"],
    "gotchas": ["New gotcha"],
    "preferences": {
        "language": "python",
        "framework": "fastapi"
    }
})

# Context automatically merges
memory.update_context({
    "patterns": ["New pattern 2", "New pattern 3"]  # No duplicates
})
```

### Statistics and Reporting

```python
# Get comprehensive statistics
stats = memory.get_statistics()

print(f"Total sessions: {stats['total_sessions']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Avg duration: {stats['avg_duration_seconds']:.1f}s")
print(f"Total insights: {stats['total_insights']}")
```

### Export and Import

```python
# Export memory
data = memory.export_memory()

# Import to new agent (merge mode)
new_memory = AgentMemory(agent_id="new-agent")
new_memory.import_memory(data, merge=True)

# Import (replace mode)
new_memory.import_memory(data, merge=False)
```

## Key Features

### 1. Automatic Persistence

All operations are automatically saved to disk:

```python
memory = AgentMemory(agent_id="auto-save", auto_save=True)  # Default
memory.add_session("Task", "Result")  # Automatically saved
```

### 2. Agent Isolation

Each agent has completely separate memory:

```python
agent1 = AgentMemory(agent_id="agent-1")
agent2 = AgentMemory(agent_id="agent-2")

# agent1 and agent2 have no data sharing
```

### 3. Thread Safety

All operations are thread-safe using locks:

```python
import threading

def add_sessions():
    for i in range(100):
        memory.add_session(f"Task {i}", f"Result {i}")

threads = [threading.Thread(target=add_sessions) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

# All 1000 sessions safely stored
```

### 4. Context Accumulation

Insights automatically update context:

```python
memory.add_insight("Use async/await", "pattern")
context = memory.get_context()
assert "Use async/await" in context["patterns"]
```

## Testing

Run the test suite:

```bash
cd .blackbox5
python3 -m pytest tests/test_agent_memory.py -v
```

Run the demonstration:

```bash
python3 engine/memory/demo.py
```

## Comparison with Graphiti

| Feature | Graphiti (Auto-Claude) | AgentMemory (BlackBox5) |
|---------|----------------------|------------------------|
| Storage | LadybugDB (graph DB) | JSON files |
| Semantic Search | Embedding-based | Keyword-based |
| Complexity | High | Low |
| Dependencies | graphiti_core, ladybugdb | Standard library only |
| Setup | Docker (optional) | No setup required |
| Use Case | Complex knowledge graphs | Simple persistent memory |

## API Reference

### AgentMemory

#### Constructor

```python
AgentMemory(
    agent_id: str,
    memory_base_path: Optional[Path] = None,
    auto_save: bool = True
)
```

#### Methods

##### add_session

```python
add_session(
    task: str,
    result: str,
    success: bool = True,
    duration_seconds: Optional[float] = None,
    metadata: Optional[dict[str, Any]] = None
) -> str
```

Store an execution session.

**Returns**: session_id

##### add_insight

```python
add_insight(
    content: str,
    category: str,
    confidence: float = 1.0,
    source_session: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None
) -> str
```

Store a learned insight.

**Categories**: "pattern", "gotcha", "discovery", "optimization"

**Returns**: insight_id

##### get_context

```python
get_context() -> dict[str, Any]
```

Retrieve accumulated context.

**Returns**: Dictionary with patterns, gotchas, discoveries, preferences, statistics

##### update_context

```python
update_context(updates: dict[str, Any]) -> None
```

Update accumulated context.

##### get_sessions

```python
get_sessions(
    limit: Optional[int] = None,
    successful_only: bool = False
) -> list[dict[str, Any]]
```

Retrieve execution sessions.

##### get_insights

```python
get_insights(
    category: Optional[str] = None,
    min_confidence: float = 0.0,
    limit: Optional[int] = None
) -> list[dict[str, Any]]
```

Retrieve learned insights.

##### search_insights

```python
search_insights(query: str, limit: int = 10) -> list[dict[str, Any]]
```

Search insights by content (case-insensitive).

##### get_statistics

```python
get_statistics() -> dict[str, Any]
```

Get memory usage statistics.

##### clear_memory

```python
clear_memory(keep_context: bool = True) -> None
```

Clear all memory data.

##### export_memory

```python
export_memory() -> dict[str, Any]
```

Export all memory data as a dictionary.

##### import_memory

```python
import_memory(data: dict[str, Any], merge: bool = True) -> None
```

Import memory data from a dictionary.

## Design Decisions

### Why JSON instead of Graph DB?

1. **Simplicity**: No external dependencies or complex setup
2. **Portability**: Easy to inspect, edit, and version control
3. **Performance**: Fast for small to medium datasets (<10K entries)
4. **Sufficient**: Keyword search works well for most use cases

### Why Per-Agent Isolation?

1. **Security**: Agents can't access each other's memory
2. **Clarity**: Each agent has its own learning trajectory
3. **Flexibility**: Easy to export/import specific agent memories

### Why These Insight Categories?

- **pattern**: Reusable solutions (e.g., "Use React hooks")
- **gotcha**: Common pitfalls (e.g., "Always validate input")
- **discovery**: New findings (e.g., "Redis improves performance")
- **optimization**: Performance improvements (e.g., "Cache results")

## Future Enhancements

Possible future improvements:

1. **Semantic Search**: Add embedding-based search for better relevance
2. **Memory Compression**: Archive old sessions to reduce file size
3. **Memory Sharing**: Optional cross-agent memory sharing
4. **Time-based Decay**: Reduce confidence of old insights
5. **Graph Relations**: Store relationships between insights
6. **Memory Visualization**: UI for exploring agent memories

## License

Part of the BlackBox5 framework.
