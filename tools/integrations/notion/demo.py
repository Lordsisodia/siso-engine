#!/usr/bin/env python3
"""
Notion Integration Demo
=======================

Demonstrates basic usage of the Notion integration.

Usage:
    python demo.py
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from integration.notion import NotionManager


async def main():
    """Run demo."""

    # Check for token
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        print("❌ Error: NOTION_TOKEN environment variable not set")
        print("   Get your token at: https://www.notion.so/my-integrations")
        print("   Create an integration and copy the 'Internal Integration Token'")
        return

    print("🚀 Notion Integration Demo")
    print("=" * 50)

    # Initialize manager
    async with NotionManager() as manager:
        # Check connection
        print("\n1. Checking connection...")
        if await manager.check_connection():
            print("   ✅ Connected successfully")
        else:
            print("   ❌ Connection failed")
            return

        # Get user info
        print("\n2. Getting user info...")
        user_info = await manager.get_user_info()
        user_name = user_info.get("name", "Unknown")
        user_id = user_info.get("id", "Unknown")
        print(f"   User: {user_name}")
        print(f"   ID: {user_id}")

        # Search workspace
        print("\n3. Searching workspace...")
        results = await manager.search(query="test", page_size=5)
        print(f"   Found {len(results.get('results', []))} results")

        # Create a page
        print("\n4. Creating a test page...")
        print("   Note: You need a valid parent page ID to create a page")
        print("   Skipping page creation (set PARENT_ID env var to test)")

        parent_id = os.environ.get("NOTION_PARENT_ID")
        if parent_id:
            try:
                # Create markdown content
                markdown_content = """# Test Page

This is a test page created by the Notion integration.

## Features

- Create pages with blocks
- Query databases
- Search workspace

### Code Example

```python
async with NotionManager() as manager:
    page = await manager.create_page(parent_id, properties, children)
```

### Todo List

- [x] Create integration
- [ ] Test all features
- [ ] Write documentation

> This is a quote block

---

---

"""

                # Convert markdown to blocks
                blocks = manager.markdown_to_blocks(markdown_content)
                print(f"   Converted markdown to {len(blocks)} blocks")

                # Create page
                properties = {
                    "title": {
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": "BlackBox5 Test Page"},
                            }
                        ]
                    }
                }

                page = await manager.create_page(
                    parent_id=parent_id,
                    properties=properties,
                    children=blocks,
                    icon="🚀",
                )

                print(f"   ✅ Created page: {page.title}")
                print(f"   URL: {page.url}")

                # Query a database
                print("\n5. Querying databases...")
                db_results = await manager.search_databases(query="", page_size=5)
                print(f"   Found {len(db_results)} databases")

                if db_results:
                    db = db_results[0]
                    print(f"   First database: {db.title} ({db.id})")

                    # Query the database
                    try:
                        query_results = await manager.query_database(db.id, page_size=5)
                        print(f"   Query returned {len(query_results.get('results', []))} results")
                    except Exception as e:
                        print(f"   Note: Could not query database (may need permissions)")

            except Exception as e:
                print(f"   ❌ Error: {e}")
        else:
            print("   To test page creation, set NOTION_PARENT_ID env var")
            print("   Example: export NOTION_PARENT_ID='page_1234567890'")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
