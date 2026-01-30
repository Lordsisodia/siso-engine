# Cloudflare Integration for BlackBox5

Comprehensive integration with Cloudflare services including DNS management, Workers deployment, KV storage, and R2 object storage.

## Features

- **DNS Management**: Create, update, delete, and list DNS records
- **Workers**: Deploy and manage Cloudflare Workers scripts
- **KV Store**: Read, write, and delete key-value pairs in Workers KV
- **R2 Storage**: Upload, download, delete, list objects, and generate presigned URLs

## Architecture

### Components

- **`CloudflareManager`**: Main manager class for all Cloudflare operations
- **`DNSRecord`**: Data class for DNS record entities
- **`WorkerScript`**: Data class for Worker script entities
- **`KVEntry`**: Data class for KV store entries
- **`R2Object`**: Data class for R2 storage objects
- **`DNSRecordSpec`, `WorkerDeploymentResult`, `KVOperation`, `R2UploadSpec`, `R2PresignedURL`**: Specification/result types

## Requirements

### Authentication

1. **Get API Token**:
   - Navigate to https://dash.cloudflare.com/profile/api-tokens
   - Create a custom token with permissions:
     - **Zone - DNS - Edit**
     - **Account - Workers Scripts - Edit**
     - **Account - Workers KV Storage - Edit**
     - **Account - Cloudflare R2 - Edit**
   - Copy token and set as environment variable:
     ```bash
     export CLOUDFLARE_API_TOKEN="your_token_here"
     ```

2. **Get Account ID** (required for Workers, KV, R2):
   - Navigate to https://dash.cloudflare.com → Workers & Pages
   - Copy Account ID from the right sidebar
   - Set as environment variable:
     ```bash
     export CLOUDFLARE_ACCOUNT_ID="your_account_id_here"
     ```

3. **Get Zone ID** (required for DNS operations):
   - Navigate to your zone dashboard
   - Copy Zone ID from the right sidebar
   - Set as environment variable:
     ```bash
     export CLOUDFLARE_ZONE_ID="your_zone_id_here"
     ```

4. **R2 Credentials** (required for R2 operations):
   - Create R2 API token at https://dash.cloudflare.com → R2 → Manage R2 API Tokens
   - Set as environment variables:
     ```bash
     export R2_ACCESS_KEY_ID="your_access_key"
     export R2_SECRET_ACCESS_KEY="your_secret_key"
     ```

### Python Dependencies

```bash
pip install httpx boto3
```

Add to `.blackbox5/engine/requirements.txt`:
```txt
httpx>=0.27.0
boto3>=1.34.0
```

## Usage

### Basic Usage

```python
import asyncio
from integration.cloudflare import CloudflareManager
from integration.cloudflare.types import DNSRecordSpec, DNSRecordType

async def main():
    # Initialize manager
    manager = CloudflareManager(
        token="your_api_token",
        account_id="your_account_id"
    )

    # Create DNS record
    spec = DNSRecordSpec(
        type=DNSRecordType.A,
        name="www.example.com",
        content="1.2.3.4",
        ttl=1,
        proxied=True
    )
    record = await manager.dns_create_record(zone_id="...", spec=spec)
    print(f"Created record: {record.id}")

    # Close connection
    await manager.close()

asyncio.run(main())
```

### Advanced Usage

#### DNS Management

```python
# Create A record
spec = DNSRecordSpec(
    type=DNSRecordType.A,
    name="subdomain.example.com",
    content="192.0.2.1",
    ttl=1,
    proxied=True
)
record = await manager.dns_create_record(zone_id, spec)

# Update record
spec.content = "192.0.2.2"
updated = await manager.dns_update_record(zone_id, record.id, spec)

# List records
records = await manager.dns_list_records(zone_id, record_type=DNSRecordType.A)

# Delete record
await manager.dns_delete_record(zone_id, record.id)
```

#### Workers Deployment

```python
# Deploy Worker
script_content = '''
export default {
  async fetch(request) {
    return new Response("Hello from BlackBox5!");
  }
}
'''
result = await manager.workers_deploy("my-worker", script_content)

# List Workers
workers = await manager.workers_list()

# Delete Worker
await manager.workers_delete("my-worker")
```

#### KV Store Operations

```python
# Write to KV
await manager.kv_write(
    namespace_id="...",
    key="user:123",
    value='{"name": "John", "age": 30}'
)

# Read from KV
value = await manager.kv_read(namespace_id, "user:123")

# Delete from KV
await manager.kv_delete(namespace_id, "user:123")
```

#### R2 Storage Operations

```python
# Upload to R2
content = b"Hello, R2!"
obj = await manager.r2_upload(
    bucket_name="my-bucket",
    key="files/example.txt",
    content=content,
    content_type="text/plain"
)

# Download from R2
content = await manager.r2_download("my-bucket", "files/example.txt")

# List objects
objects = await manager.r2_list("my-bucket", prefix="files/")

# Generate presigned URL
url = await manager.r2_presigned_url("my-bucket", "files/example.txt", expiration=3600)
print(f"Presigned URL: {url.url}")

# Delete object
await manager.r2_delete("my-bucket", "files/example.txt")
```

## API Reference

### Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `dns_create_record` | Create DNS record | `zone_id`, `spec` | `DNSRecord` |
| `dns_update_record` | Update DNS record | `zone_id`, `record_id`, `spec` | `DNSRecord` |
| `dns_delete_record` | Delete DNS record | `zone_id`, `record_id` | `bool` |
| `dns_list_records` | List DNS records | `zone_id`, `record_type`, `name`, `limit` | `list[DNSRecord]` |
| `workers_deploy` | Deploy Worker script | `script_name`, `content` | `WorkerDeploymentResult` |
| `workers_list` | List Worker scripts | - | `list[WorkerScript]` |
| `workers_delete` | Delete Worker script | `script_name` | `bool` |
| `kv_write` | Write to KV store | `namespace_id`, `key`, `value`, `expiration` | `bool` |
| `kv_read` | Read from KV store | `namespace_id`, `key` | `str` |
| `kv_delete` | Delete from KV store | `namespace_id`, `key` | `bool` |
| `r2_upload` | Upload to R2 | `bucket_name`, `key`, `content`, `content_type`, `metadata` | `R2Object` |
| `r2_download` | Download from R2 | `bucket_name`, `key` | `bytes` |
| `r2_delete` | Delete from R2 | `bucket_name`, `key` | `bool` |
| `r2_list` | List R2 objects | `bucket_name`, `prefix`, `limit` | `list[R2Object]` |
| `r2_presigned_url` | Generate presigned URL | `bucket_name`, `key`, `expiration`, `method` | `R2PresignedURL` |
| `check_connection` | Verify API connection | - | `bool` |
| `list_zones` | List all zones | - | `list[dict]` |

### Data Classes

#### `DNSRecord`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Record ID |
| `type` | `DNSRecordType` | Record type (A, AAAA, CNAME, etc.) |
| `name` | `str` | Record name |
| `content` | `str` | Record content (IP, domain, etc.) |
| `ttl` | `int` | Time to live in seconds |
| `proxied` | `bool` | Cloudflare proxy enabled |
| `zone_id` | `str` | Zone ID |
| `zone_name` | `str` | Zone name |
| `created_on` | `datetime` | Creation timestamp |
| `modified_on` | `datetime` | Last modified timestamp |

#### `DNSRecordSpec`

| Field | Type | Description |
|-------|------|-------------|
| `type` | `DNSRecordType` | Record type |
| `name` | `str` | Record name |
| `content` | `str` | Record content |
| `ttl` | `int` | Time to live (default: 1 = auto) |
| `proxied` | `bool` | Enable proxy (default: True) |
| `priority` | `int` | Priority for MX/SRV (optional) |

#### `WorkerDeploymentResult`

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Deployment succeeded |
| `script_id` | `str` | Script ID |
| `script_name` | `str` | Script name |
| `errors` | `list[str]` | Errors (if any) |
| `message` | `str` | Deployment message |
| `timestamp` | `datetime` | Deployment timestamp |

#### `R2Object`

| Field | Type | Description |
|-------|------|-------------|
| `key` | `str` | Object key |
| `size` | `int` | Size in bytes |
| `etag` | `str` | ETag |
| `last_modified` | `datetime` | Last modified |
| `content_type` | `str` | Content type |
| `bucket_name` | `str` | Bucket name |

#### `R2PresignedURL`

| Field | Type | Description |
|-------|------|-------------|
| `url` | `str` | Presigned URL |
| `expires_at` | `datetime` | Expiration timestamp |
| `method` | `str` | HTTP method |

## Error Handling

```python
import httpx

try:
    record = await manager.dns_create_record(zone_id, spec)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        print("Zone not found")
    elif e.response.status_code == 400:
        print("Invalid request")
    else:
        print(f"HTTP error: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
```

## Rate Limits

- **Rate Limit**: 1,200 requests per 5 minutes per API token
- **Best Practices**:
  - Implement exponential backoff for retries
  - Cache DNS records and Worker scripts when possible
  - Use bulk operations where available
  - Monitor rate limit headers in responses

## Testing

```bash
# Run demo
python .blackbox5/integration/cloudflare/demo.py

# Run tests
python .blackbox5/integration/cloudflare/tests/test_integration.py
```

## Troubleshooting

### Common Issues

**Issue**: "API token required" error
- **Solution**: Set `CLOUDFLARE_API_TOKEN` environment variable or pass `token` parameter

**Issue**: "account_id required for Workers operations"
- **Solution**: Set `CLOUDFLARE_ACCOUNT_ID` environment variable or pass `account_id` parameter

**Issue**: R2 operations fail with auth error
- **Solution**: Create R2 API token and set `R2_ACCESS_KEY_ID` and `R2_SECRET_ACCESS_KEY` environment variables

**Issue**: DNS record creation fails with "validations failed"
- **Solution**: Ensure record name includes the full domain (e.g., `www.example.com`)

**Issue**: Rate limit errors (429 status)
- **Solution**: Implement backoff and retry logic, reduce request frequency

## See Also

- Cloudflare Documentation: https://developers.cloudflare.com/
- Cloudflare API Reference: https://developers.cloudflare.com/api/
- Cloudflare Python SDK: https://github.com/cloudflare/cloudflare-python
- R2 Documentation: https://developers.cloudflare.com/r2/

## Implementation Details

### Files Created

1. **`__init__.py`** - Package initialization, exports `CloudflareManager`
2. **`manager.py`** (28,675 bytes) - Main `CloudflareManager` class with async context manager support
3. **`types.py`** (5,568 bytes) - Data classes: `DNSRecord`, `WorkerScript`, `KVEntry`, `R2Object`, etc.
4. **`config.py`** (2,654 bytes) - `CloudflareConfig` with `from_env()` and `from_file()` methods
5. **`demo.py`** (5,512 bytes) - Demonstration script
6. **`README.md`** - Full documentation
7. **`QUICKSTART.md`** (4,030 bytes) - Quick start guide
8. **`tests/test_integration.py`** (5,454 bytes) - Integration tests

### Key Implementation Details

1. **SDK Usage**: `httpx` for Cloudflare API, `boto3` for S3-compatible R2 operations
2. **Authentication**: API token from `CLOUDFLARE_API_TOKEN`, Account ID from `CLOUDFLARE_ACCOUNT_ID`
3. **Rate Limits**: 1,200 requests per 5 minutes per API token
4. **R2 Endpoint**: `https://{ACCOUNT_ID}.r2.cloudflarestorage.com`
5. **Async Design**: All methods are async with context manager support
6. **Error Handling**: Proper exception propagation and graceful 404 handling

### Dependencies

- `httpx>=0.27.0` - HTTP client
- `boto3>=1.34.0` - R2 storage operations

### Environment Variables

Required:
- `CLOUDFLARE_API_TOKEN` - API token

Optional:
- `CLOUDFLARE_ACCOUNT_ID` - Account ID for Workers, KV, R2
- `CLOUDFLARE_ZONE_ID` - Zone ID for DNS operations
- `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` - R2 credentials
