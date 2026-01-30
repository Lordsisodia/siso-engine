# Cloudflare Integration - Quick Start

Get started with the Cloudflare integration in 5 minutes.

## 1. Get Your API Token

### API Token

1. Navigate to https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token"
3. Use the "Edit Cloudflare Workers" template or create a custom token with:
   - **Zone** → **DNS** → **Edit**
   - **Account** → **Workers Scripts** → **Edit**
   - **Account** → **Workers KV Storage** → **Edit**
   - **Account** → **Cloudflare R2** → **Edit**
4. Click "Continue to summary" and create the token
5. Copy the token

### Account ID

1. Navigate to https://dash.cloudflare.com
2. Click "Workers & Pages" in the sidebar
3. Copy your **Account ID** from the right sidebar

### Zone ID (for DNS operations)

1. Navigate to your zone dashboard
2. Copy **Zone ID** from the right sidebar

### R2 Credentials (for R2 operations)

1. Navigate to https://dash.cloudflare.com → R2
2. Click "Manage R2 API Tokens"
3. Create API token and copy **Access Key ID** and **Secret Access Key**

## 2. Configure Environment Variables

```bash
# Add to your .env or shell profile
export CLOUDFLARE_API_TOKEN="your_token_here"
export CLOUDFLARE_ACCOUNT_ID="your_account_id_here"
export CLOUDFLARE_ZONE_ID="your_zone_id_here"  # For DNS operations

# For R2 operations
export R2_ACCESS_KEY_ID="your_access_key"
export R2_SECRET_ACCESS_KEY="your_secret_key"
```

## 3. Install Dependencies

```bash
pip install httpx boto3
```

## 4. Basic Usage

### Initialize Manager

```python
from integration.cloudflare import CloudflareManager

manager = CloudflareManager()
```

### Common Operations

#### DNS Management

```python
from integration.cloudflare.types import DNSRecordSpec, DNSRecordType

# Create A record
spec = DNSRecordSpec(
    type=DNSRecordType.A,
    name="www.example.com",
    content="192.0.2.1",
    ttl=1,
    proxied=True
)
record = await manager.dns_create_record(zone_id, spec)

# List records
records = await manager.dns_list_records(zone_id)

# Delete record
await manager.dns_delete_record(zone_id, record.id)
```

#### Workers Deployment

```python
# Deploy Worker
script = '''
export default {
  async fetch(request) {
    return new Response("Hello!");
  }
}
'''
result = await manager.workers_deploy("my-worker", script)

# List Workers
workers = await manager.workers_list()
```

#### KV Store

```python
# Write to KV
await manager.kv_write(namespace_id, "key", "value")

# Read from KV
value = await manager.kv_read(namespace_id, "key")

# Delete from KV
await manager.kv_delete(namespace_id, "key")
```

#### R2 Storage

```python
# Upload
await manager.r2_upload(bucket, key, content)

# Download
content = await manager.r2_download(bucket, key)

# List objects
objects = await manager.r2_list(bucket)

# Generate presigned URL
url = await manager.r2_presigned_url(bucket, key, expiration=3600)
```

## 5. Full Example

```python
import asyncio
from integration.cloudflare import CloudflareManager
from integration.cloudflare.types import DNSRecordSpec, DNSRecordType

async def main():
    async with CloudflareManager() as manager:
        # Check connection
        if await manager.check_connection():
            print("Connected!")

        # Create DNS record
        spec = DNSRecordSpec(
            type=DNSRecordType.A,
            name="test.example.com",
            content="1.2.3.4"
        )
        record = await manager.dns_create_record(zone_id, spec)
        print(f"Created: {record.id}")

        # Deploy Worker
        await manager.workers_deploy("test-worker", "export default { fetch: () => new Response('OK') }")

        # Write to KV
        await manager.kv_write(namespace_id, "test", "value")

        # Upload to R2
        await manager.r2_upload(bucket, "test.txt", b"Hello!")

asyncio.run(main())
```

## Next Steps

- Read the [full documentation](README.md)
- Check out [examples](demo.py)
- Review the [API reference](README.md#api-reference)
- Explore [Cloudflare's API docs](https://developers.cloudflare.com/api/)
