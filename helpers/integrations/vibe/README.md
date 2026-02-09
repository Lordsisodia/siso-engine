# Vibe Kanban Integration for BlackBox5

This integration provides Vibe Kanban card management following CCPM's GitHub patterns.

## Features

- **Card Management**: Create, move, and update Kanban cards
- **Status Mapping**: Automatic status-to-column mapping
- **Progress Sync**: CCPM-style incremental progress synchronization
- **Local Memory**: Store card context in working memory
- **Comments**: Add progress comments to cards

## Architecture

### Components

- **`VibeKanbanManager`**: Main manager class for all operations
- **`CardData`**: Data class for card information
- **`CardSpec`**: Specification for creating new cards
- **`CardStatus`**: Enum for card statuses
- **`Column`**: Enum for Kanban columns

### Status to Column Mapping

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

## Usage

### Basic Usage

```python
import asyncio
from integration.vibe import VibeKanbanManager, Column, CardStatus

async def main():
    # Initialize manager
    manager = VibeKanbanManager(
        api_url="http://localhost:3001",
        memory_path="./memory/working"
    )

    # Create card
    card = await manager.create_card(
        title="Fix authentication bug",
        description="Users cannot login with Google OAuth",
        column=Column.DOING
    )

    # Move card
    await manager.move_card(card.id, Column.DONE)

    # Update status (preferred method)
    await manager.update_card_status(card.id, CardStatus.DONE)

    # Add comment
    await manager.add_comment(
        card.id,
        "Fixed OAuth callback URL configuration"
    )

    # Close connection
    await manager.close()

asyncio.run(main())
```

### Creating Cards from Specification

```python
from integration.vibe import VibeKanbanManager, CardSpec

manager = VibeKanbanManager()

spec = CardSpec(
    title="Add user authentication",
    description="Implement OAuth2 login with Google and GitHub",
    acceptance_criteria=[
        "User can login with Google",
        "User can login with GitHub",
        "Session persists across browser restarts",
        "Logout functionality works"
    ],
    labels=["priority:high", "type:feature"],
    epic_link="#123",
    spec_link="/docs/specs/auth.md"
)

card = await manager.create_card_from_spec(spec)
```

### Querying Cards

```python
# List all cards in progress
cards = await manager.list_cards(
    status=CardStatus.IN_PROGRESS
)

# Get specific card
card = await manager.get_card(card_id=1)

# Filter by column
cards = await manager.list_cards(column=Column.DONE)
```

### Progress Synchronization

```python
# Sync local progress to card
await manager.sync_progress(card_id=1)
```

## Setup

### Vibe Kanban Server

Start Vibe Kanban locally:

```bash
docker-compose -f docker-compose.vibe-kanban-local.yml up -d
```

The server will be available at:
- Web UI: http://localhost:3000
- API: http://localhost:3001

### Configuration

Set environment variables (optional):

```bash
export VIBE_API_URL="http://localhost:3001"
export VIBE_API_TOKEN="your-token"
export VIBE_MEMORY_PATH="./memory/working"
```

## Testing

Run the test suite:

```bash
cd .blackbox5
pytest tests/test_vibe_integration.py -v
```

Run the full workflow demonstration:

```bash
python tests/test_vibe_integration.py
```

## Patterns from CCPM

This integration follows the same patterns as GitHub's CCPM integration:

1. **Incremental Sync**: Only posts comments when there's new content
2. **Memory Integration**: Stores card context in working memory
3. **Status Mapping**: Maintains status-to-column mapping
4. **Progress Comments**: CCPM-style structured progress updates
5. **Repository Protection**: Prevents writing to template repos

## API Endpoints

The integration expects Vibe Kanban to expose the following API endpoints:

- `POST /api/cards` - Create card
- `GET /api/cards/:id` - Get card
- `GET /api/cards` - List cards (with filters)
- `PATCH /api/cards/:id` - Update card
- `POST /api/cards/:id/comments` - Add comment

## Memory Structure

Cards are stored in the working memory directory:

```
memory/working/
├── cards/
│   ├── 1/
│   │   ├── card.md          # Card context
│   │   ├── progress.md      # Progress tracking
│   │   └── .last_sync       # Sync marker
│   └── 2/
│       └── ...
```

## Error Handling

The manager raises `httpx.HTTPError` for API failures:

```python
try:
    card = await manager.create_card(...)
except httpx.HTTPError as e:
    print(f"Failed to create card: {e}")
```

## License

MIT

## Implementation Details

### Files Created

1. **`VibeKanbanManager.py`** (739 lines) - Main manager class
2. **`__init__.py`** - Package initialization and exports
3. **`demo.py`** - Interactive demonstration
4. **`tests/test_vibe_integration.py`** (475 lines) - 12 comprehensive test functions
5. **`README.md`** - Complete documentation
6. **`COMPARISON.md`** - GitHub vs Vibe Kanban pattern comparison
7. **`QUICK-REFERENCE.md`** - Quick start guide

### Key Implementation Details

1. **Status-to-Column Mapping**:
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

2. **CCPM Patterns Implemented**:
   - Incremental sync (only posts when new content)
   - Memory integration (card context in markdown files)
   - Progress comments (structured format with timestamps)
   - Specification pattern (CardSpec mirrors GitHub's TaskSpec)

3. **API Endpoints Expected**:
   - `POST /api/cards` - Create card
   - `GET /api/cards/:id` - Get card
   - `GET /api/cards` - List cards (with filters)
   - `PATCH /api/cards/:id` - Update card
   - `POST /api/cards/:id/comments` - Add comment

4. **Local Memory Structure**:
   ```
   memory/working/
   └── cards/
       └── {id}/
           ├── card.md
           ├── progress.md
           └── .last_sync
   ```

### Test Coverage

12 comprehensive test functions:
- Card creation (basic and from spec)
- Card movement between columns
- Status updates with automatic column mapping
- Query cards with filters
- Add comments
- Full workflow demonstration

### Setup

```bash
# Start Vibe Kanban
docker-compose -f docker-compose.vibe-kanban-local.yml up -d

# Run tests
pytest tests/test_vibe_integration.py -v

# Run demo
python integration/vibe/demo.py
```
