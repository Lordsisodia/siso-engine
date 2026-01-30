# Supabase Integration for BlackBox5

Comprehensive integration with Supabase for database operations, storage management, and Edge Function invocation.

## Features

- **Database Operations**: Full CRUD operations with filtering, pagination, and ordering
- **Storage Management**: Upload, download, and manage files in Supabase Storage
- **Edge Functions**: Invoke Supabase Edge Functions with custom payloads
- **Realtime Subscriptions**: Subscribe to database changes (basic implementation)
- **Batch Operations**: Efficient bulk inserts with automatic batching
- **Type Safety**: Data classes and type hints throughout

## Architecture

### Components

- **`SupabaseManager`**: Main manager class for all Supabase operations
- **`SupabaseConfig`**: Configuration class with environment variable support
- **Data Classes**: `TableSpec`, `InsertResult`, `UpdateResult`, `DeleteResult`, `StorageFile`, `EdgeFunctionResult`

## Requirements

### Authentication

1. **Get Project Credentials**:
   - Navigate to https://supabase.com/dashboard
   - Select your project (or create a new one)
   - Go to Settings → API
   - Copy:
     - **Project Reference**: The subdomain of your Supabase URL
     - **Service Role Key**: Found in "Project API keys" section

2. **Set Environment Variables**:
   ```bash
   export SUPABASE_PROJECT_REF="your_project_ref"
   export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"
   ```

   Add to your `.env` file:
   ```bash
   SUPABASE_PROJECT_REF=your_project_ref
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
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
from integration.supabase import SupabaseManager
from integration.supabase.config import SupabaseConfig

async def main():
    # Load config from environment
    config = SupabaseConfig.from_env()

    # Initialize manager
    async with SupabaseManager(config) as manager:
        # Query table
        users = await manager.query("users", limit=10)
        print(users)

asyncio.run(main())
```

### Database Operations

#### Query with Filters

```python
# Simple filter
active_users = await manager.query(
    "users",
    filters={"status": "active"}
)

# Complex filters
results = await manager.query(
    "users",
    filters={
        "status": "active",
        "age": {"gte": 18},
        "created_at": {"gte": "2024-01-01"}
    },
    columns=["id", "email", "created_at"],
    limit=100,
    offset=0,
    order_by="created_at",
    ascending=False
)
```

#### Insert Records

```python
# Single record
result = await manager.insert(
    "users",
    {
        "email": "user@example.com",
        "name": "John Doe",
        "status": "active"
    }
)

# Bulk insert
result = await manager.insert(
    "users",
    [
        {"email": "user1@example.com", "name": "User 1"},
        {"email": "user2@example.com", "name": "User 2"},
    ]
)
```

#### Update Records

```python
result = await manager.update(
    "users",
    data={"status": "inactive"},
    filters={"id": "123"}
)

# Update with complex filter
result = await manager.update(
    "users",
    data={"last_login": "2024-01-19"},
    filters={"created_at": {"lt": "2024-01-01"}}
)
```

#### Delete Records

```python
result = await manager.delete(
    "users",
    filters={"id": "123"}
)

# Delete with complex filter
result = await manager.delete(
    "users",
    filters={"status": "deleted", "created_at": {"lt": "2023-01-01"}}
)
```

#### Count Records

```python
count = await manager.count("users")
count = await manager.count(
    "users",
    filters={"status": "active"}
)
```

### Storage Operations

#### Upload File

```python
# Upload text
await manager.upload_file(
    bucket="documents",
    path="reports/report.txt",
    content="Hello, World!",
    content_type="text/plain"
)

# Upload binary
with open("image.png", "rb") as f:
    await manager.upload_file(
        bucket="images",
        path="logos/logo.png",
        content=f.read(),
        content_type="image/png"
    )
```

#### Download File

```python
content = await manager.download_file(
    bucket="documents",
    path="reports/report.txt"
)
```

#### Get Public URL

```python
url = await manager.get_public_url(
    bucket="documents",
    path="reports/report.txt"
)
# https://xxx.supabase.co/storage/v1/object/public/documents/reports/report.txt
```

#### List Files

```python
files = await manager.list_files(
    bucket="documents",
    path="reports",
    limit=100
)

for file in files:
    print(f"{file.name} - {file.size} bytes")
```

#### Delete File

```python
await manager.delete_file(
    bucket="documents",
    path="reports/old-report.txt"
)
```

### Edge Functions

#### Invoke Function

```python
result = await manager.invoke_function(
    name="process-payment",
    body={
        "amount": 100,
        "currency": "USD",
        "customer_id": "123"
    },
    headers={"X-Custom-Header": "value"}
)

if result.error:
    print(f"Error: {result.error}")
else:
    print(f"Result: {result.data}")
```

### Batch Operations

#### Bulk Insert

```python
# Insert 5000 records in batches of 1000
data = [{"name": f"User {i}"} for i in range(5000)]

results = await manager.batch_insert(
    "users",
    data,
    batch_size=1000
)
```

## API Reference

### Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `query` | Query table with filters | `table`, `filters`, `columns`, `limit`, `offset`, `order_by`, `ascending` | `list[dict]` |
| `insert` | Insert record(s) | `table`, `data` | `InsertResult` |
| `update` | Update records | `table`, `data`, `filters` | `UpdateResult` |
| `delete` | Delete records | `table`, `filters` | `DeleteResult` |
| `count` | Count records | `table`, `filters` | `int` |
| `upload_file` | Upload to storage | `bucket`, `path`, `content`, `content_type`, `upsert` | `dict` |
| `download_file` | Download from storage | `bucket`, `path` | `bytes` |
| `get_public_url` | Get public URL | `bucket`, `path` | `str` |
| `list_files` | List files in bucket | `bucket`, `path`, `limit` | `list[StorageFile]` |
| `delete_file` | Delete file | `bucket`, `path` | `bool` |
| `invoke_function` | Invoke Edge Function | `name`, `body`, `headers` | `EdgeFunctionResult` |
| `batch_insert` | Batch insert records | `table`, `data`, `batch_size` | `list[InsertResult]` |
| `check_connection` | Check API connection | None | `bool` |
| `get_table_info` | Get table information | `table` | `dict` |

### Data Classes

#### `InsertResult`

| Field | Type | Description |
|-------|------|-------------|
| `data` | `list[dict]` | Inserted records |
| `count` | `int | None` | Number of records |
| `error` | `str | None` | Error message if failed |

#### `UpdateResult`

| Field | Type | Description |
|-------|------|-------------|
| `data` | `list[dict]` | Updated records |
| `count` | `int | None` | Number of records |
| `error` | `str | None` | Error message if failed |

#### `StorageFile`

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | File name |
| `bucket` | `str` | Bucket name |
| `path` | `str` | Full path |
| `size` | `int` | File size in bytes |
| `content_type` | `str` | MIME type |
| `updated_at` | `datetime` | Last update time |
| `metadata` | `dict | None` | Additional metadata |

## Filter Operators

When querying with filters, you can use the following operators:

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equal | `{"status": "active"}` |
| `gt` | Greater than | `{"age": {"gt": 18}}` |
| `gte` | Greater than or equal | `{"age": {"gte": 18}}` |
| `lt` | Less than | `{"age": {"lt": 65}}` |
| `lte` | Less than or equal | `{"age": {"lte": 65}}` |
| `neq` | Not equal | `{"status": {"neq": "deleted"}}` |
| `like` | Pattern match (case-sensitive) | `{"name": {"like": "%John%"}}` |
| `ilike` | Pattern match (case-insensitive) | `{"name": {"ilike": "%john%"}}` |
| `in` | In array | `{"id": {"in": [1, 2, 3]}}` |
| `is` | IS NULL/NOT NULL | `{"deleted_at": {"is": None}}` |

## Error Handling

```python
import httpx

try:
    result = await manager.query("users")
except httpx.HTTPStatusError as e:
    print(f"HTTP Error: {e.response.status_code}")
    print(f"Response: {e.response.text}")
except httpx.RequestError as e:
    print(f"Request Error: {e}")
```

## Rate Limits

- **Database**: 1000 requests/second per project
- **Storage**: 1000 requests/second per project
- **Edge Functions**: 500 requests/second per project

## Security Notes

- **Service Role Key**: The integration uses the service role key which bypasses Row Level Security (RLS)
- **Backend Only**: Never expose the service role key in client-side code
- **Environment Variables**: Always store credentials in environment variables
- **Permissions**: Ensure your service role key has only necessary permissions

## Testing

```bash
# Run the demo
python .blackbox5/integration/supabase/demo.py
```

## Troubleshooting

### Common Issues

**Issue**: Authentication failed
- **Solution**: Verify SUPABASE_PROJECT_REF and SUPABASE_SERVICE_ROLE_KEY are correct

**Issue**: Table not found
- **Solution**: Ensure table exists in your Supabase project

**Issue**: Permission denied
- **Solution**: Check RLS policies and ensure service role key has access

**Issue**: Bucket not found
- **Solution**: Create storage bucket in Supabase dashboard first

**Issue**: Rate limit exceeded
- **Solution**: Implement retry logic or reduce request frequency

## See Also

- Supabase Documentation: https://supabase.com/docs
- API Reference: https://supabase.com/docs/reference/javascript
- Python Client: https://github.com/supabase/supabase-py

## Implementation Details

### Files Created

1. **`manager.py`** (777 lines) - Main `SupabaseManager` class
2. **`types.py`** (159 lines) - Data classes: `TableSpec`, `InsertResult`, `StorageFile`, etc.
3. **`config.py`** (110 lines) - `SupabaseConfig` with environment variable loading
4. **`demo.py`** (140 lines) - Demonstrates all major features
5. **`tests/test_integration.py`** (288 lines) - Comprehensive unit tests
6. **`README.md`** - Comprehensive documentation
7. **`QUICKSTART.md`** - 5-minute quick start guide

### Key Implementation Details

1. **API Endpoints**:
   - Database: `https://<PROJECT_REF>.supabase.co/rest/v1/`
   - Storage: `https://<PROJECT_REF>.supabase.co/storage/v1/`
   - Functions: `https://<PROJECT_REF>.supabase.co/functions/v1/`

2. **Authentication**: Service role key for backend operations (bypasses RLS)
3. **Filter Operators**: eq, gt, lt, gte, lte, neq, like, ilike, in, is
4. **Async Design**: All methods are async with context manager support
5. **Batch Operations**: Automatic batching for bulk inserts

### Security Notes

- Never expose service role key to client-side code
- Store credentials in environment variables only
- Use only in trusted backend environments

### Environment Variables

```bash
SUPABASE_PROJECT_REF=your_project_ref
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Dependencies

- `httpx>=0.27.0` - Async HTTP client
