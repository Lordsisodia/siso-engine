# Vibe Kanban vs GitHub Integration - Pattern Comparison

This document shows how the Vibe Kanban integration adapts CCPM's GitHub patterns.

## Architecture Comparison

### GitHub Integration (CCPM)

```
.github_integration.py (GitHubIssuesIntegration)
├── Provider: GitHubProvider
├── Sync: CCPMSyncManager
├── Memory: MemoryManager
└── Protocol: GitProvider
```

### Vibe Kanban Integration

```
.vibe/VibeKanbanManager.py (VibeKanbanManager)
├── HTTP Client: httpx.AsyncClient
├── Sync: Built-in (CCPM-style)
├── Memory: Built-in (working memory)
└── Protocol: Custom (Vibe API)
```

## Method Mapping

| GitHub Method | Vibe Kanban Method | Notes |
|--------------|-------------------|-------|
| `create_task(spec)` | `create_card_from_spec(spec)` | Same spec pattern |
| `sync_progress(task_id)` | `sync_progress(card_id)` | CCPM incremental sync |
| `complete_task(task_id)` | `update_card_status(card_id, DONE)` | Status-based completion |
| `get_issue(issue_number)` | `get_card(card_id)` | Fetch single item |
| `list_issues(filters)` | `list_cards(filters)` | Query with filters |
| `add_comment(task_id, comment)` | `add_comment(card_id, comment)` | Add comments |
| `close_issue(issue_id)` | `update_card_status(card_id, DONE)` | Mark as done |

## Data Class Mapping

### GitHub

```python
@dataclass
class TaskSpec:
    title: str
    description: str
    acceptance_criteria: list[str] | None = None
    epic_link: str | None = None
    spec_link: str | None = None
    related_issues: list[str] | None = None
    labels: list[str] | None = None
```

### Vibe Kanban

```python
@dataclass
class CardSpec:
    title: str
    description: str
    acceptance_criteria: list[str] | None = None
    epic_link: str | None = None
    spec_link: str | None = None
    related_cards: list[int] | None = None
    labels: list[str] | None = None
```

**Key Difference**: `related_issues` (list[str]) vs `related_cards` (list[int])

## Status Mapping

### GitHub

```python
class IssueState(Enum):
    OPEN = "open"
    CLOSED = "closed"
```

### Vibe Kanban

```python
class CardStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"
    ABORTED = "aborted"

# Status to Column mapping
STATUS_TO_COLUMN = {
    CardStatus.TODO: Column.BACKLOG,
    CardStatus.IN_PROGRESS: Column.DOING,
    CardStatus.IN_REVIEW: Column.IN_REVIEW,
    CardStatus.DONE: Column.DONE,
    CardStatus.BLOCKED: Column.BLOCKED,
    CardStatus.ABORTED: Column.BACKLOG,
}
```

**Key Difference**: Vibe has granular statuses + column mapping

## Sync Pattern Comparison

### GitHub (CCPM)

```python
async def sync_progress(self, task_id: int) -> bool:
    # Get local progress
    progress = self.sync.get_task_progress(task_id)

    # Check for new content
    if not self.sync.has_new_content(task_id, progress):
        return False

    # Format progress comment
    comment = self.sync.format_progress_comment(progress)

    # Post to GitHub
    await self.provider.add_comment(task_id, comment)

    # Update sync marker
    self.sync.update_task_progress(task_id, progress)
    return True
```

### Vibe Kanban

```python
async def sync_progress(self, card_id: int) -> bool:
    # Get local progress
    progress = self._get_card_progress(card_id)

    # Check for new content
    if not self._has_new_content(card_id, progress):
        return False

    # Format progress comment
    comment = self._format_progress_comment(progress)

    # Post to Vibe
    await self.add_comment(card_id, comment)

    # Update sync marker
    self._update_sync_marker(card_id)
    return True
```

**Pattern Match**: Identical CCPM incremental sync pattern

## Memory Structure

### GitHub

```
memory/working/
├── tasks/
│   ├── 123/
│   │   ├── task.md         # Task metadata
│   │   ├── progress.md     # Progress tracking
│   │   └── .last_sync      # Sync marker
```

### Vibe Kanban

```
memory/working/
├── cards/
│   ├── 1/
│   │   ├── card.md         # Card metadata
│   │   ├── progress.md     # Progress tracking
│   │   └── .last_sync      # Sync marker
```

**Pattern Match**: Identical memory structure

## Comment Formatting

### GitHub (CCPM)

```python
def format_progress_comment(self, progress: TaskProgress) -> str:
    sections = []
    sections.append(f"## 🔄 Progress Update - {timestamp}\n")

    if progress.completed:
        sections.append("### ✅ Completed Work")
        for item in progress.completed:
            sections.append(f"- {item}")

    if progress.in_progress:
        sections.append("### 🔄 In Progress")
        for item in progress.in_progress:
            sections.append(f"- {item}")

    return "\n".join(sections)
```

### Vibe Kanban

```python
def _format_progress_comment(self, progress: dict) -> str:
    sections = []
    sections.append(f"## 🔄 Progress Update - {timestamp}\n")

    if progress.get("completed"):
        sections.append("### ✅ Completed Work")
        for item in progress["completed"]:
            sections.append(f"- {item}")

    if progress.get("in_progress"):
        sections.append("### 🔄 In Progress")
        for item in progress["in_progress"]:
            sections.append(f"- {item}")

    return "\n".join(sections)
```

**Pattern Match**: Identical CCPM comment structure

## Key Adaptations

### 1. No Provider Protocol

GitHub uses a `GitProvider` protocol for abstraction. Vibe Kanban uses direct HTTP calls via `httpx`.

**Rationale**: Vibe Kanban has a single API (no multi-provider need)

### 2. Status + Column Duality

Vibe Kanban maintains both status and column, with automatic mapping:

```python
# Update status (preferred)
await manager.update_card_status(card_id, CardStatus.IN_PROGRESS)
# Automatically moves to Column.DOING

# Or move directly
await manager.move_card(card_id, Column.DOING)
# Sets status to CardStatus.IN_PROGRESS
```

**Rationale**: Kanban boards need column position, status is derived

### 3. Built-in Sync

GitHub has separate `CCPMSyncManager` class. Vibe Kanban has sync built-in.

**Rationale**: Simpler API, single integration

### 4. Card Numbers vs IDs

GitHub uses issue numbers (visible in URLs). Vibe Kanban uses database IDs.

**Rationale**: Different identifier schemes

## Test Comparison

### GitHub Test Pattern

```python
@pytest.mark.asyncio
async def test_create_task(github_manager):
    task = await github_manager.create_task(spec)
    assert task.number == 123
    assert task.state == IssueState.OPEN
```

### Vibe Kanban Test Pattern

```python
@pytest.mark.asyncio
async def test_create_card(vibe_manager):
    card = await vibe_manager.create_card(
        title="Test",
        description="Test",
        column=Column.BACKLOG
    )
    assert card.id == 1
    assert card.status == CardStatus.TODO
```

**Pattern Match**: Identical test structure

## Success Criteria Met

✅ **VibeKanbanManager.py created**
- Location: `.blackbox5/integration/vibe/VibeKanbanManager.py`
- 600+ lines of well-documented code

✅ **Follows same patterns as GitHubManager**
- CCPM incremental sync
- Working memory integration
- Progress comment formatting
- Task/card specification pattern

✅ **Can create cards in different columns**
- `create_card(title, description, column)` method
- Column enum: BACKLOG, TODO, DOING, IN_REVIEW, DONE, BLOCKED

✅ **Can move cards between columns**
- `move_card(card_id, column)` method
- Automatic status updates

✅ **Status-to-column mapping implemented**
- `STATUS_TO_COLUMN` dictionary
- `update_card_status(card_id, status)` with auto-mapping

✅ **Test demonstrates Vibe Kanban interaction**
- `test_vibe_integration.py` with comprehensive tests
- Full workflow demonstration
- Mock-based unit tests

## Conclusion

The Vibe Kanban integration successfully adapts CCPM's GitHub patterns while accounting for Kanban-specific requirements (columns, positions). The integration maintains the proven CCPM sync patterns while providing a clean API for card management.
