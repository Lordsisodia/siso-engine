# Obsidian Integration - Quick Start

Get started with the Obsidian integration in 5 minutes.

## 1. Install Dependencies

```bash
pip install python-frontmatter
```

## 2. Set Up Obsidian Vault

1. Download and install [Obsidian](https://obsidian.md)
2. Create a new vault or use an existing one
3. Note the vault path (e.g., `~/Documents/MyVault`)

## 3. Basic Usage

### Initialize the Exporter

```python
from integration.obsidian import ObsidianExporter

exporter = ObsidianExporter(
    vault_path="~/Documents/MyVault",
    create_folders=True,  # Auto-create folder structure
)
```

### Export a Session

```python
from integration.obsidian.types import SessionData
from datetime import datetime

session = SessionData(
    agent_id="agent_001",
    agent_name="MyAgent",
    session_id="sess_001",
    start_time=datetime.now(),
    goal="Complete a task",
    outcome="Task completed successfully",
    tags=["session", "agent"],
)

result = exporter.export_session(session)
print(f"Exported: {result.file_path}")
```

### Export an Insight

```python
from integration.obsidian.types import InsightData

insight = InsightData(
    title="Key Discovery",
    content="Important insight about the problem domain",
    category="discovery",
    tags=["insight", "knowledge"],
)

result = exporter.export_insight(insight)
```

### Generate Index

```python
# Create index of all notes
exporter.generate_index()
```

## 4. Full Example

```python
from integration.obsidian import ObsidianExporter
from integration.obsidian.types import SessionData, InsightData
from datetime import datetime

# Initialize
exporter = ObsidianExporter(
    vault_path="~/Documents/MyVault",
    create_folders=True,
)

# Export session
session = SessionData(
    agent_id="research_agent",
    agent_name="ResearchAgent",
    session_id="research_001",
    start_time=datetime.now(),
    goal="Research Python async patterns",
    outcome="Found 8 key patterns",
    tags=["research", "python"],
    related_notes=["Async Patterns"],
)
exporter.export_session(session)

# Export insight
insight = InsightData(
    title="Async Context Managers",
    content="Use async context managers for resource management",
    category="Best Practice",
    tags=["python", "async"],
)
exporter.export_insight(insight)

# Generate index
exporter.generate_index()

print("Export complete! Check your Obsidian vault.")
```

## 5. Folder Structure

Notes are organized as:

```
your-vault/
└── blackbox5/
    ├── sessions/       # Session notes
    ├── insights/       # Knowledge and insights
    ├── context/        # Agent context
    ├── plans/          # Plans and tasks
    └── _index.md       # Index of all notes
```

## Next Steps

- Read the [full documentation](README.md)
- Check out the [demo script](demo.py)
- Review the [API reference](README.md#api-reference)
- Explore [Obsidian features](https://help.obsidian.md/)
