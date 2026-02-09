# Supabase Integration - Quick Start

Get started with the Supabase integration in 5 minutes.

## 1. Get Your Supabase Credentials

1. Go to https://supabase.com/dashboard
2. Create a new project or select existing one
3. Navigate to Settings → API
4. Copy the following:
   - **Project Reference**: Found in your project URL (e.g., `xxx.supabase.co`)
   - **Service Role Key**: Found in "Project API keys" section (starts with `eyJ...`)

## 2. Configure Environment Variables

```bash
# Add to your .env file
SUPABASE_PROJECT_REF=your_project_ref_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

Or export in your shell:
```bash
export SUPABASE_PROJECT_REF="your_project_ref_here"
export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key_here"
```

## 3. Install Dependencies

```bash
pip install httpx
```

## 4. Basic Usage

### Initialize Manager

```python
from integration.supabase import SupabaseManager
from integration.supabase.config import SupabaseConfig

# Load from environment
config = SupabaseConfig.from_env()
manager = SupabaseManager(config)
```

### Common Operations

#### Query Records

```python
# Get all users (limit 10)
users = await manager.query("users", limit=10)

# Filter records
active_users = await manager.query(
    "users",
    filters={"status": "active"}
)

# Select specific columns
results = await manager.query(
    "users",
    columns=["id", "email", "name"],
    limit=5
)
```

#### Insert Data

```python
# Insert single record
result = await manager.insert(
    "users",
    {
        "email": "john@example.com",
        "name": "John Doe",
        "status": "active"
    }
)
print(f"Created: {result.data[0]['id']}")
```

#### Upload File

```python
# Upload to storage
await manager.upload_file(
    bucket="my-bucket",
    path="files/document.txt",
    content="Hello, World!",
    content_type="text/plain"
)

# Get public URL
url = await manager.get_public_url("my-bucket", "files/document.txt")
```

#### Invoke Edge Function

```python
result = await manager.invoke_function(
    name="my-function",
    body={"param": "value"}
)
print(result.data)
```

## 5. Full Example

```python
import asyncio
from integration.supabase import SupabaseManager
from integration.supabase.config import SupabaseConfig

async def main():
    # Load config from environment
    config = SupabaseConfig.from_env()

    # Use async context manager
    async with SupabaseManager(config) as manager:
        # Check connection
        if await manager.check_connection():
            print("✅ Connected!")

        # Query data
        users = await manager.query("users", limit=5)
        print(f"Found {len(users)} users")

        # Insert data
        result = await manager.insert(
            "my_table",
            {"name": "Test", "value": 123}
        )
        print(f"Inserted: {result.data[0]['id']}")

asyncio.run(main())
```

## Next Steps

- Read the [full documentation](README.md)
- Check out [demo examples](demo.py)
- Review the [API reference](README.md#api-reference)
- Explore [filter operators](README.md#filter-operators)
