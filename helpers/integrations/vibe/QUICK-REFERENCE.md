# Vibe Kanban Integration - Quick Reference

## Import

```python
from integration.vibe import (
    VibeKanbanManager,
    CardSpec,
    CardData,
    CardStatus,
    Column,
    STATUS_TO_COLUMN,
)
```

## Initialize

```python
manager = VibeKanbanManager(
    api_url="http://localhost:3001",  # Vibe Kanban API
    memory_path="./memory/working",   # Local memory
    repo="owner/repo",                # Optional repo
)
```

## Create Cards

### Basic Card

```python
card = await manager.create_card(
    title="Fix bug",
    description="Critical issue",
    column=Column.BACKLOG
)
```

### From Spec (CCPM-style)

```python
spec = CardSpec(
    title="Add feature",
    description="Implementation",
    acceptance_criteria=["Criteria 1", "Criteria 2"],
    labels=["priority:high", "type:feature"]
)

card = await manager.create_card_from_spec(spec)
```

## Move Cards

```python
# Move to different column
card = await manager.move_card(card_id, Column.DOING)

# Available columns:
# - Column.BACKLOG
# - Column.TODO
# - Column.DOING
# - Column.IN_REVIEW
# - Column.DONE
# - Column.BLOCKED
```

## Update Status

```python
# Update status (preferred - auto-maps to column)
card = await manager.update_card_status(
    card_id,
    CardStatus.IN_PROGRESS  # → Moves to Column.DOING
)

# Available statuses:
# - CardStatus.TODO → Column.BACKLOG
# - CardStatus.IN_PROGRESS → Column.DOING
# - CardStatus.IN_REVIEW → Column.IN_REVIEW
# - CardStatus.DONE → Column.DONE
# - CardStatus.BLOCKED → Column.BLOCKED
# - CardStatus.ABORTED → Column.BACKLOG
```

## Query Cards

```python
# Get single card
card = await manager.get_card(card_id=1)

# List all cards
cards = await manager.list_cards()

# Filter by status
cards = await manager.list_cards(status=CardStatus.IN_PROGRESS)

# Filter by column
cards = await manager.list_cards(column=Column.DONE)

# Filter by project/repo
cards = await manager.list_cards(
    project_id=1,
    repo_id=2
)
```

## Add Comments

```python
await manager.add_comment(
    card_id,
    "Progress: Implemented core logic"
)
```

## Sync Progress

```python
# Sync local progress to card (CCPM incremental sync)
await manager.sync_progress(card_id)
```

## Close Connection

```python
await manager.close()
```

## Complete Workflow

```python
async def workflow():
    manager = VibeKanbanManager()

    # 1. Create in backlog
    card = await manager.create_card(
        title="Feature X",
        description="Add feature X",
        column=Column.BACKLOG
    )

    # 2. Start work
    card = await manager.update_card_status(
        card.id,
        CardStatus.IN_PROGRESS
    )

    # 3. Add progress
    await manager.add_comment(
        card.id,
        "Implementation complete, testing"
    )

    # 4. Request review
    card = await manager.update_card_status(
        card.id,
        CardStatus.IN_REVIEW
    )

    # 5. Complete
    card = await manager.update_card_status(
        card.id,
        CardStatus.DONE
    )

    await manager.close()
```

## Status to Column Mapping

```python
STATUS_TO_COLUMN = {
    CardStatus.TODO: Column.BACKLOG,
    CardStatus.IN_PROGRESS: Column.DOING,
    CardStatus.IN_REVIEW: Column.IN_REVIEW,
    CardStatus.DONE: Column.DONE,
    CardStatus.BLOCKED: Column.BLOCKED,
    CardStatus.ABORTED: Column.BACKLOG,
}
```

## Memory Structure

```
memory/working/
└── cards/
    └── {id}/
        ├── card.md       # Card metadata
        ├── progress.md   # Progress tracking
        └── .last_sync    # Sync marker
```

## Error Handling

```python
import httpx

try:
    card = await manager.create_card(...)
except httpx.HTTPError as e:
    print(f"API error: {e}")
```

## Testing

```bash
# Run tests
cd .blackbox5
pytest tests/test_vibe_integration.py -v

# Run demo
python3 integration/vibe/demo.py
```

## Files

- `VibeKanbanManager.py` - Main implementation (739 lines)
- `test_vibe_integration.py` - Test suite (475 lines, 12 tests)
- `README.md` - Full documentation
- `COMPARISON.md` - GitHub vs Vibe Kanban patterns
- `IMPLEMENTATION-SUMMARY.md` - Implementation details
- `demo.py` - Interactive demonstration
