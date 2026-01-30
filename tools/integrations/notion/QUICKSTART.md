# Notion Integration - Quick Start

Get started with the Notion integration in 5 minutes.

## 1. Create Your Integration

1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Fill in the details:
   - **Name**: BlackBox5 (or your preferred name)
   - **Associated workspace**: Select your workspace
   - **Type**: Internal
   - **Capabilities**: Check Read/Update user information and content
4. Click "Submit"
5. Copy the **Internal Integration Token** (starts with `secret_`)

## 2. Configure Environment Variables

```bash
# Add to your .env or shell profile
export NOTION_TOKEN="secret_your_token_here"

# Optional: Set a default parent page ID for testing
export NOTION_PARENT_ID="page_your_parent_page_id"
```

## 3. Share Pages with Integration

Before the integration can access pages, you must share them:

1. Open the page or database you want to access
2. Click the **...** (more) menu in the top right
3. Scroll down and click **Add connections**
4. Select your integration (e.g., "BlackBox5")

## 4. Install Dependencies

```bash
pip install httpx
```

## 5. Basic Usage

### Initialize Manager

```python
from integration.notion import NotionManager

# With environment variable
manager = NotionManager()

# Or pass token directly
manager = NotionManager(token="your_token")

# Use as context manager (recommended)
async with NotionManager() as manager:
    # Your code here
    pass
```

### Common Operations

#### Check Connection

```python
async with NotionManager() as manager:
    if await manager.check_connection():
        print("Connected!")
```

#### Get User Info

```python
async with NotionManager() as manager:
    user = await manager.get_user_info()
    print(f"User: {user['name']}")
```

#### Search Workspace

```python
async with NotionManager() as manager:
    # Search all content
    results = await manager.search(query="project")

    # Search only pages
    pages = await manager.search_pages(query="tasks")

    # Search only databases
    databases = await manager.search_databases(query="database")
```

#### Create a Page

```python
async with NotionManager() as manager:
    # Simple page
    properties = {
        "title": {
            "title": [
                {"type": "text", "text": {"content": "My New Page"}}
            ]
        }
    }

    page = await manager.create_page(
        parent_id="parent_page_or_database_id",
        properties=properties
    )

    print(f"Created: {page.url}")
```

#### Create Page with Blocks

```python
async with NotionManager() as manager:
    properties = {
        "title": {
            "title": [
                {"type": "text", "text": {"content": "Page with Content"}}
            ]
        }
    }

    children = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "Hello, Notion!"}}
                ]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {"type": "text", "text": {"content": "Section Header"}}
                ]
            }
        }
    ]

    page = await manager.create_page(
        parent_id="parent_id",
        properties=properties,
        children=children
    )
```

#### Use Markdown to Create Content

```python
async with NotionManager() as manager:
    markdown = """
# Project Plan

## Tasks

- [x] Setup project
- [ ] Implement features
- [ ] Write tests

## Code

```python
def hello():
    print("Hello!")
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

#### Get a Page

```python
async with NotionManager() as manager:
    page = await manager.get_page("page_id")
    print(f"Title: {page.title}")
    print(f"URL: {page.url}")
    print(f"Created: {page.created_at}")
```

#### Query a Database

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
        }
    )

    for item in results.get("results", []):
        print(item["properties"])
```

#### Append Blocks to Page

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
        }
    ]

    await manager.append_blocks(
        block_id="page_id",
        blocks=blocks
    )
```

#### Create a Database

```python
async with NotionManager() as manager:
    properties = {
        "Name": {"title": {}},
        "Status": {
            "select": {
                "options": [
                    {"name": "Todo", "color": "gray"},
                    {"name": "In Progress", "color": "blue"},
                    {"name": "Done", "color": "green"}
                ]
            }
        },
        "Priority": {
            "number": {"format": "number"}
        }
    }

    database = await manager.create_database(
        parent_id="parent_page_id",
        title="Tasks",
        properties=properties,
        icon="📋"
    )

    print(f"Created: {database.url}")
```

## 6. Full Example

```python
import asyncio
from integration.notion import NotionManager

async def main():
    async with NotionManager() as manager:
        # Check connection
        if not await manager.check_connection():
            print("Connection failed!")
            return

        # Get user info
        user = await manager.get_user_info()
        print(f"Connected as: {user['name']}")

        # Create a page with markdown content
        markdown = """
# Welcome to BlackBox5

This page was created automatically.

## Features

- 📝 Create pages programmatically
- 🗃️ Query databases
- 🔍 Search workspace
- 📄 Markdown support

Try it out!
"""

        blocks = manager.markdown_to_blocks(markdown)

        properties = {
            "title": {
                "title": [
                    {"type": "text", "text": {"content": "BlackBox5 Demo"}}
                ]
            }
        }

        page = await manager.create_page(
            parent_id="your_parent_page_id",
            properties=properties,
            children=blocks,
            icon="🚀"
        )

        print(f"✅ Created page: {page.url}")

asyncio.run(main())
```

## 7. Test the Demo

Run the included demo to verify your setup:

```bash
cd .blackbox5/integration/notion
python demo.py
```

The demo will:
1. Check your connection
2. Get your user info
3. Search your workspace
4. Create a test page (if NOTION_PARENT_ID is set)

## Next Steps

- Read the [full documentation](README.md)
- Check out [API reference](README.md#api-reference)
- Learn about [block types](README.md#block-types)
- Understand [property types](README.md#property-types)
- Review [rate limits](README.md#rate-limits)

## Tips

1. **Page IDs vs Database IDs**: Use `page_` prefix for page parents and database IDs directly

2. **Finding IDs**: Copy from URL:
   - Page: `https://notion.so/page-PAGE_ID` → use `PAGE_ID`
   - Database: Same format

3. **Sharing**: Always share pages/databases with your integration before accessing

4. **Rate Limiting**: Keep requests under 3/sec for reliability

5. **Debugging**: Use `check_connection()` to verify setup before operations
