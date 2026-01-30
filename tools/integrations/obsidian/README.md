# Obsidian Integration for BlackBox5

Export BlackBox5 agent sessions, insights, context, and plans to Obsidian as Markdown notes with YAML frontmatter.

## Features

- **Direct File System Writes**: No API required - writes directly to your Obsidian vault
- **YAML Frontmatter**: Rich metadata for each note using standard Obsidian frontmatter
- **Wikilinks Support**: Automatic linking between related notes using `[[Note Title]]` syntax
- **Organized Structure**: Separate folders for sessions, insights, context, and plans
- **Index Generation**: Auto-generated index of all exported notes
- **Date-based Filenames**: ISO 8601 dates for consistent sorting (`session-2025-01-19-topic.md`)

## Architecture

### Components

- **`ObsidianExporter`**: Main exporter class for all operations
- **`SessionData`**: Data class for agent session notes
- **`InsightData`**: Data class for insight/knowledge notes
- **`ContextData`**: Data class for agent context notes
- **`PlanData`**: Data class for plan/task notes
- **`Wikilink`**: Helper class for generating Obsidian wikilinks

### Folder Structure

Notes are organized in your Obsidian vault as:

```
your-vault/
└── blackbox5/
    ├── sessions/        # Agent session notes
    ├── insights/        # Knowledge and insights
    ├── context/         # Agent context snapshots
    ├── plans/           # Plans and task lists
    └── _index.md        # Generated index of all notes
```

## Requirements

### Python Dependencies

```bash
pip install python-frontmatter
```

Add to `.blackbox5/engine/requirements.txt`:

```txt
python-frontmatter>=1.4.0
```

### Obsidian Setup

1. **Install Obsidian**: Download from [obsidian.md](https://obsidian.md)
2. **Create a Vault**: Set up your notes vault
3. **Configure Vault Path**: Set the path when initializing the exporter

No plugins required - uses standard Markdown + YAML frontmatter!

## Usage

### Basic Usage

```python
from integration.obsidian import ObsidianExporter
from integration.obsidian.types import SessionData
from datetime import datetime

# Initialize exporter
exporter = ObsidianExporter(
    vault_path="~/Documents/MyObsidianVault",
    create_folders=True,
)

# Export a session
session_data = SessionData(
    agent_id="agent_001",
    agent_name="ResearchAgent",
    session_id="sess_20250119",
    start_time=datetime.now(),
    goal="Research Python best practices",
    outcome="Created comprehensive documentation",
    tags=["research", "python"],
)

result = exporter.export_session(session_data)
print(f"Exported: {result.file_path}")

# Generate index of all notes
exporter.generate_index()
```

### Exporting Sessions

```python
session = SessionData(
    agent_id="agent_001",
    agent_name="ResearchAgent",
    session_id="sess_20250119_research",
    start_time=datetime.now(),
    end_time=datetime.now() + timedelta(hours=2),
    goal="Research async patterns in Python",
    outcome="Documented 8 key patterns with examples",
    steps=[
        {"title": "Literature Review", "status": "complete"},
        {"title": "Code Analysis", "status": "complete"},
        {"title": "Documentation", "status": "complete"},
    ],
    tags=["research", "python", "async"],
    related_notes=["Async Patterns", "Python Best Practices"],
)

result = exporter.export_session(session)
```

### Exporting Insights

```python
insight = InsightData(
    title="Context Managers for Resource Management",
    content="""
Context managers ensure proper resource cleanup.

## Benefits
- Automatic cleanup
- Exception safety
- Cleaner code
    """,
    category="Best Practice",
    source_session="sess_20250119_research",
    tags=["python", "pattern"],
    related_notes=["Python Best Practices"],
)

result = exporter.export_insight(insight)
```

### Exporting Context

```python
context = ContextData(
    agent_id="agent_001",
    agent_name="ResearchAgent",
    context_type="working",
    content="""
## Current Focus
Python async patterns research

## Active Projects
1. FastAPI implementation patterns
2. Pydantic validation strategies
    """,
    tags=["agent", "research"],
)

result = exporter.export_context(context)
```

### Exporting Plans

```python
plan = PlanData(
    title="Async Patterns Research",
    description="Comprehensive research into async/await patterns",
    status="planning",
    steps=[
        {"title": "Literature Review", "description": "Review docs", "status": "pending"},
        {"title": "Code Analysis", "description": "Analyze implementations", "status": "pending"},
    ],
    tags=["research", "python", "async"],
)

result = exporter.export_plan(plan)
```

### Generating Index

```python
# Create/update index of all exported notes
result = exporter.generate_index()
print(f"Index: {result.file_path}")
```

## API Reference

### Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `export_session()` | Export agent session note | `session_data: SessionData` | `ExportResult` |
| `export_insight()` | Export insight note | `insight_data: InsightData` | `ExportResult` |
| `export_context()` | Export context note | `context_data: ContextData` | `ExportResult` |
| `export_plan()` | Export plan note | `plan_data: PlanData` | `ExportResult` |
| `generate_index()` | Create index of all notes | None | `ExportResult` |

### Data Classes

#### `SessionData`

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | `str` | Unique agent identifier |
| `agent_name` | `str` | Human-readable agent name |
| `session_id` | `str` | Unique session identifier |
| `start_time` | `datetime` | Session start time |
| `end_time` | `datetime \| None` | Session end time |
| `goal` | `str \| None` | Session goal/objective |
| `outcome` | `str \| None` | Session outcome/result |
| `steps` | `list[dict]` | List of steps taken |
| `metadata` | `dict` | Additional metadata |
| `tags` | `list[str]` | Obsidian tags |
| `related_notes` | `list[str]` | Related note titles for wikilinks |

#### `InsightData`

| Field | Type | Description |
|-------|------|-------------|
| `title` | `str` | Insight title |
| `content` | `str` | Insight content (Markdown) |
| `category` | `str \| None` | Category/subject |
| `source_session` | `str \| None` | Source session ID |
| `created_at` | `datetime` | Creation timestamp |
| `tags` | `list[str]` | Obsidian tags |
| `related_notes` | `list[str]` | Related note titles |
| `metadata` | `dict` | Additional metadata |

#### `ContextData`

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | `str` | Unique agent identifier |
| `agent_name` | `str` | Human-readable agent name |
| `context_type` | `str` | Type (working, extended, archival) |
| `content` | `str` | Context content (Markdown) |
| `created_at` | `datetime` | Creation timestamp |
| `tags` | `list[str]` | Obsidian tags |
| `related_notes` | `list[str]` | Related note titles |
| `metadata` | `dict` | Additional metadata |

#### `PlanData`

| Field | Type | Description |
|-------|------|-------------|
| `title` | `str` | Plan title |
| `description` | `str \| None` | Plan description |
| `steps` | `list[dict]` | Plan steps/tasks |
| `status` | `str` | Plan status (planning, active, complete) |
| `created_at` | `datetime` | Creation timestamp |
| `updated_at` | `datetime \| None` | Last update timestamp |
| `tags` | `list[str]` | Obsidian tags |
| `related_notes` | `list[str]` | Related note titles |
| `metadata` | `dict` | Additional metadata |

#### `ExportResult`

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Whether export succeeded |
| `file_path` | `str \| None` | Path to created file |
| `note_type` | `NoteType \| None` | Type of note exported |
| `message` | `str \| None` | Success message |
| `error` | `str \| None` | Error message if failed |

### Helper Classes

#### `Wikilink`

Create wikilinks with optional aliases and section references:

```python
from integration.obsidian.types import Wikilink

# Simple link
link1 = Wikilink(title="My Note")
print(link1.to_markdown())  # [[My Note]]

# With alias
link2 = Wikilink(title="Long Note Title", alias="Short")
print(link2.to_markdown())  # [[Long Note Title|Short]]

# With section reference
link3 = Wikilink(title="My Note", section="Summary")
print(link3.to_markdown())  # [[My Note#Summary]]
```

## Note Format

### YAML Frontmatter

Each note includes rich metadata in YAML frontmatter:

```yaml
---
type: session
agent_id: agent_001
agent_name: ResearchAgent
session_id: sess_20250119
start_time: 2025-01-19T10:00:00
end_time: 2025-01-19T12:00:00
created: 2025-01-19T12:00:00
tags:
  - session
  - agent
  - research
status: completed
---
```

### Wikilinks

Notes automatically include related note sections:

```markdown
## Related Notes

- [[Async Patterns]]
- [[Python Best Practices|Best Practices]]
- [[Research Notes#Summary]]
```

## Error Handling

```python
result = exporter.export_session(session_data)

if result.success:
    print(f"Exported to: {result.file_path}")
else:
    print(f"Export failed: {result.error}")
```

## Testing

Run the demo script:

```bash
python .blackbox5/integration/obsidian/demo.py
```

Run unit tests:

```bash
python .blackbox5/integration/obsidian/tests/test_obsidian.py
```

## Troubleshooting

### Common Issues

**Issue**: "Vault directory doesn't exist"
- **Solution**: Set `create_folders=True` when initializing the exporter, or create the vault manually first

**Issue**: "Permission denied when writing files"
- **Solution**: Check that your user has write permissions for the Obsidian vault directory

**Issue**: "Notes not appearing in Obsidian"
- **Solution**: Try the Obsidian command "Reload app without saving" or restart Obsidian to refresh the file index

**Issue**: "Wikilinks not resolving"
- **Solution**: Make sure the linked note titles exactly match the actual note titles (case-sensitive)

## Best Practices

1. **Consistent Naming**: Use consistent titles for notes to make wikilinking easier
2. **Tag Strategy**: Establish a consistent tagging convention (e.g., `#agent/active`, `#insight/python`)
3. **Regular Index Updates**: Call `generate_index()` after exporting multiple notes
4. **Date Ranges**: Always include both start and end times for completed sessions
5. **Related Notes**: Use wikilinks to create a knowledge graph of related information

## Integration with Agent Workflows

```python
# In an agent workflow
from integration.obsidian import ObsidianExporter

exporter = ObsidianExporter(vault_path="~/Documents/ObsidianVault")

# At the start of a session
session = SessionData(
    agent_id=agent.id,
    agent_name=agent.name,
    session_id=session.id,
    start_time=datetime.now(),
    goal=agent.current_goal,
)

# At the end of a session
session.end_time = datetime.now()
session.outcome = agent.result
exporter.export_session(session)

# When discovering insights
insight = InsightData(
    title=f"Insight: {topic}",
    content=insight_text,
    source_session=session.id,
)
exporter.export_insight(insight)

# Update index
exporter.generate_index()
```

## See Also

- [Obsidian Documentation](https://help.obsidian.md/)
- [YAML Frontmatter in Obsidian](https://help.obsidian.md/Advanced+topics/YAML+front+matter)
- [Wikilinks in Obsidian](https://help.obsidian.md/How+to/Internal+links)
