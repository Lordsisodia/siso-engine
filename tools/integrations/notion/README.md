# Notion Integration for BlackBox5

Complete integration with Notion API for managing pages, databases, and blocks programmatically.

## Features

- **Page Management**: Create, update, retrieve, and archive pages
- **Block Operations**: Append blocks, convert markdown to Notion blocks
- **Database Operations**: Create databases, query with filters, update schemas
- **Search**: Full-text search across pages and databases
- **Markdown Support**: Convert markdown to Notion block structure
- **Type Safety**: Full type hints with dataclasses for all entities
- **Rate Limiting**: Built-in rate limiter (3 req/sec recommended)

## Architecture

### Components

- **`NotionManager`**: Main manager class for all operations
- **`Page`**: Data class for page entities
- **`Database`**: Data class for database entities
- **`Block`**: Data class for block content
- **`BlockType`**: Enum for block types (paragraph, heading, code, etc.)
- **`PropertyType`**: Enum for property types (title, rich_text, select, etc.)

## Requirements

### Authentication

1. **Create Integration**:
   - Navigate to https://www.notion.so/my-integrations
   - Click "New integration"
   - Give it a name (e.g., "BlackBox5")
   - Select your workspace
   - Copy the "Internal Integration Token"

2. **Share Pages/Databases**:
   - Go to the page or database you want to access
   - Click "..." → "Add connections"
   - Select your integration

3. **Set Environment Variable**:
   ```bash
   export NOTION_TOKEN="your_integration_token_here"
   ```

### Python Dependencies

```bash
pip install httpx
```

Add to `.blackbox5/engine/requirements.txt`:
```txt
httpx>=0.27.0
```

## Usage

### Basic Usage

```python
import asyncio
from integration.notion import NotionManager

async def main():
    # Initialize manager
    manager = NotionManager(token="your_token")

    # Create a page
    properties = {
        "title": {
            "title": [
                {"type": "text", "text": {"content": "My Page"}}
            ]
        }
    }
    blocks = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "Hello, Notion!"}}
                ]
            }
        }
    ]

    page = await manager.create_page(
        parent_id="parent_page_id",
        properties=properties,
        children=blocks
    )

    print(f"Created page: {page.url}")

    # Close connection
    await manager.close()

asyncio.run(main())
```

### Using Context Manager

```python
async with NotionManager() as manager:
    page = await manager.get_page("page_id")
    print(page.title)
```

### Creating Pages with Markdown

```python
async with NotionManager() as manager:
    markdown = """
# Project Plan

## Tasks

- [x] Setup project
- [ ] Implement features
- [ ] Write tests

## Code Example

```python
def hello():
    print("Hello, Notion!")
```
"""

    blocks = manager.markdown_to_blocks(markdown)
    properties = {
        "title": {
            "title": [
                {"type": "text", "text": {"content": "Project Plan"}}
            ]
        }
    }

    page = await manager.create_page(
        parent_id="parent_id",
        properties=properties,
        children=blocks
    )
```

### Querying Databases

```python
async with NotionManager() as manager:
    # Simple query
    results = await manager.query_database(
        database_id="database_id",
        page_size=10
    )

    # Query with filter
    results = await manager.query_database(
        database_id="database_id",
        filter={
            "property": "Status",
            "select": {
                "equals": "In Progress"
            }
        },
        sorts=[
            {
                "property": "Priority",
                "direction": "descending"
            }
        ]
    )

    for result in results.get("results", []):
        print(result["properties"])
```

### Creating Databases

```python
async with NotionManager() as manager:
    properties = {
        "Name": {"title": {}},
        "Status": {
            "select": {
                "options": [
                    {"name": "Not Started", "color": "gray"},
                    {"name": "In Progress", "color": "blue"},
                    {"name": "Done", "color": "green"}
                ]
            }
        },
        "Priority": {
            "number": {
                "format": "number"
            }
        },
        "Due Date": {
            "date": {}
        }
    }

    database = await manager.create_database(
        parent_id="page_id",
        title="Tasks",
        properties=properties,
        description="Task tracking database",
        icon="📋"
    )

    print(f"Created database: {database.url}")
```

### Searching

```python
async with NotionManager() as manager:
    # Search all content
    results = await manager.search(
        query="project plan",
        page_size=10
    )

    # Search only pages
    pages = await manager.search_pages(
        query="project plan",
        page_size=10
    )

    # Search only databases
    databases = await manager.search_databases(
        query="tasks",
        page_size=10
    )

    for page in pages:
        print(f"{page.title} - {page.url}")
```

### Appending Blocks

```python
async with NotionManager() as manager:
    blocks = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "New content"}}
                ]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {"type": "text", "text": {"content": "Section"}}
                ]
            }
        }
    ]

    await manager.append_blocks(
        block_id="page_id",
        blocks=blocks
    )
```

## API Reference

### Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `create_page()` | Create a new page | `parent_id`, `properties`, `children`, `icon`, `cover` | `Page` |
| `get_page()` | Get page by ID | `page_id` | `Page \| None` |
| `update_page()` | Update page properties | `page_id`, `properties`, `archived` | `Page \| None` |
| `delete_page()` | Archive a page | `page_id` | `bool` |
| `append_blocks()` | Add blocks to page | `block_id`, `blocks` | `list[dict]` |
| `get_block_children()` | Get block children | `block_id`, `page_size`, `start_cursor` | `dict` |
| `create_database()` | Create a database | `parent_id`, `title`, `properties`, `description`, `icon` | `Database` |
| `get_database()` | Get database by ID | `database_id` | `Database \| None` |
| `query_database()` | Query a database | `database_id`, `filter`, `sorts`, `start_cursor`, `page_size` | `dict` |
| `update_database()` | Update database | `database_id`, `title`, `properties`, `archived` | `Database \| None` |
| `search()` | Search workspace | `query`, `filter`, `sort`, `start_cursor`, `page_size` | `dict` |
| `search_pages()` | Search pages only | `query`, `page_size` | `list[SearchResult]` |
| `search_databases()` | Search databases only | `query`, `page_size` | `list[SearchResult]` |
| `markdown_to_blocks()` | Convert markdown to blocks | `markdown_text` | `list[dict]` |
| `check_connection()` | Verify API connection | None | `bool` |
| `get_user_info()` | Get user information | None | `dict` |
| `close()` | Close HTTP client | None | `None` |

### Data Classes

#### `Page`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Page ID |
| `title` | `str` | Page title |
| `url` | `str` | Page URL |
| `icon` | `str \| None` | Page icon (emoji or URL) |
| `cover` | `str \| None` | Cover image URL |
| `parent_id` | `str \| None` | Parent page/database ID |
| `parent_type` | `ParentType \| None` | Parent type |
| `created_at` | `datetime \| None` | Creation time |
| `last_edited` | `datetime \| None` | Last edit time |
| `archived` | `bool` | Whether archived |
| `properties` | `dict \| None` | All properties |

#### `Database`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Database ID |
| `title` | `str` | Database title |
| `url` | `str` | Database URL |
| `description` | `str \| None` | Database description |
| `icon` | `str \| None` | Database icon |
| `parent_id` | `str \| None` | Parent page ID |
| `created_at` | `datetime \| None` | Creation time |
| `last_edited` | `datetime \| None` | Last edit time |
| `properties` | `dict \| None` | Property schema |

#### `Block`

| Field | Type | Description |
|-------|------|-------------|
| `type` | `BlockType` | Block type enum |
| `content` | `str \| list \| dict` | Block content |
| `children` | `list[Block] \| None` | Child blocks |
| `checked` | `bool \| None` | Checkbox state (for to_do) |
| `color` | `Color` | Text/background color |
| `language` | `str \| None` | Code language |

## Block Types

Supported block types in `BlockType` enum:

- `PARAGRAPH` - Plain text paragraph
- `HEADING_1`, `HEADING_2`, `HEADING_3` - Headings
- `BULLETED_LIST` - Bullet list item
- `NUMBERED_LIST` - Numbered list item
- `TO_DO` - Checkbox item
- `TOGGLE` - Collapsible toggle
- `QUOTE` - Quote block
- `DIVIDER` - Horizontal line
- `CALLOUT` - Callout box
- `CODE` - Code block with syntax highlighting
- `TABLE` - Table
- `IMAGE` - Embedded image
- `VIDEO` - Embedded video
- `FILE` - File attachment
- `PDF` - PDF embed
- `BOOKMARK` - Bookmark
- `EQUATION` - Math equation

## Property Types

Supported property types in `PropertyType` enum:

- `TITLE` - Page title
- `RICH_TEXT` - Formatted text
- `NUMBER` - Numeric value
- `SELECT` - Single choice dropdown
- `MULTI_SELECT` - Multiple choice tags
- `DATE` - Date/time value
- `PEOPLE` - User references
- `FILES` - File attachments
- `CHECKBOX` - Boolean checkbox
- `URL` - Link URL
- `EMAIL` - Email address
- `PHONE` - Phone number
- `FORMULA` - Computed value
- `RELATION` - Related pages
- `ROLLUP` - Aggregated value
- `CREATED_TIME` - Creation timestamp
- `CREATED_BY` - Creator user
- `LAST_EDITED_TIME` - Last edit timestamp
- `LAST_EDITED_BY` - Last editor user

## Error Handling

```python
import httpx

async with NotionManager() as manager:
    try:
        page = await manager.get_page("invalid_id")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print("Page not found")
        elif e.response.status_code == 401:
            print("Unauthorized - check your token")
        else:
            print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

## Rate Limits

- **Recommended**: 3 requests per second
- **Hard Limit**: 2,700 requests per 15 minutes
- **Best Practices**:
  - Use rate limiter for bulk operations
  - Implement exponential backoff for retries
  - Cache frequently accessed data
  - Use pagination for large datasets

### Using Rate Limiter

```python
from integration.notion.manager import RateLimiter

limiter = RateLimiter(calls=3, period=1.0)

async with NotionManager() as manager:
    await limiter.acquire()
    page1 = await manager.get_page("page1_id")

    await limiter.acquire()
    page2 = await manager.get_page("page2_id")
```

## Testing

```bash
# Run demo
python .blackbox5/integration/notion/demo.py

# Run tests (when implemented)
python .blackbox5/integration/notion/tests/test_integration.py
```

## Troubleshooting

### Common Issues

**Issue**: "Unauthorized" error
- **Solution**: Verify NOTION_TOKEN is correct and integration has access to the page

**Issue**: "Object not found" error
- **Solution**: Ensure the integration is shared with the page/database via "Add connections"

**Issue**: Rate limit errors
- **Solution**: Implement rate limiting with 1 second delay between requests

**Issue**: Block creation fails
- **Solution**: Ensure block structure matches Notion API format exactly

**Issue**: Database query returns empty
- **Solution**: Check filter syntax and ensure property names match exactly

## Notion API Version

This integration uses Notion API version `2025-09-03`. The integration will continue to work with future API versions until Notion deprecates version `2022-06-28` (set via `Notion-Version` header).

## See Also

- Notion API Documentation: https://developers.notion.com/reference
- Notion Integration Guide: https://developers.notion.com/docs/create-a-notion-integration
- Block Types: https://developers.notion.com/reference/block-type
- Property Types: https://developers.notion.com/reference/property-object

## Implementation Details

### Files Created

1. **`manager.py`** (~500 lines) - Main `NotionManager` class
2. **`types.py`** (~400 lines) - Data classes and enums for Page, Database, Block, etc.
3. **`config.py`** - Configuration helpers with `RateLimiter` class
4. **`demo.py`** - Usage demonstrations
5. **`README.md`** - Full documentation
6. **`QUICKSTART.md`** - Quick start guide
7. **`tests/test_integration.py`** - Comprehensive tests

### Key Implementation Details

1. **API Configuration**:
   - API Base URL: `https://api.notion.com`
   - API Version: `2025-09-03`
   - Notion-Version Header: `2022-06-28`
   - Authentication: Bearer token from `NOTION_TOKEN` env var

2. **Block Structure**: Hierarchical block system mirroring Notion's content model
3. **Markdown Conversion**: Comprehensive markdown-to-blocks converter
4. **Type Safety**: Dataclasses for all Notion entities with proper type hints
5. **Rate Limiting**: `RateLimiter` helper for 3 req/sec recommended limit
6. **Error Handling**: Graceful 404 handling (returns None) with proper logging

### Notion API Quirks

1. No partial property updates - must provide full property object
2. Title property is required (exactly one per page)
3. Integration must be shared via "Add connections" before API access
4. Rich text arrays required for all text content
5. Database schema updates require full schema

### Rate Limits

- Recommended: 3 requests per second
- Hard Limit: 2,700 requests per 15 minutes
