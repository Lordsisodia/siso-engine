"""
Cloudflare Manager for BlackBox5
=================================

Main integration class for Cloudflare services.

Features:
- DNS Management: Create, update, delete, and list DNS records
- Workers: Deploy and manage Cloudflare Workers scripts
- KV Store: Read, write, and delete key-value pairs
- R2 Storage: Upload, download, delete, and list objects

Usage:
    >>> manager = CloudflareManager(token="your_token", account_id="your_account_id")
    >>> result = await manager.dns_create_record(zone_id="...", spec=DNSRecordSpec(...))
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx

from .types import (
    DNSRecord,
    DNSRecordSpec,
    DNSRecordType,
    KVEntry,
    KVOperation,
    R2Object,
    R2PresignedURL,
    R2UploadSpec,
    WorkerDeploymentResult,
    WorkerScript,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Main Manager Class
# =============================================================================


class CloudflareManager:
    """
    Main manager class for Cloudflare integration.

    Authentication:
        Uses API token from environment variable or parameter.

    Rate Limits:
        - 1,200 requests per 5 minutes
        - Best practice: Implement exponential backoff for retries

    Example:
        >>> manager = CloudflareManager(token="your_token", account_id="your_account_id")
        >>> result = await manager.dns_create_record(zone_id="...", spec=...)
        >>> print(result)
    """

    API_BASE = "https://api.cloudflare.com/client/v4"

    def __init__(
        self,
        token: Optional[str] = None,
        account_id: Optional[str] = None,
        base_url: str = "https://api.cloudflare.com/client/v4",
        timeout: int = 30,
    ):
        """
        Initialize Cloudflare manager.

        Args:
            token: Cloudflare API token (default: from CLOUDFLARE_API_TOKEN env var)
            account_id: Cloudflare Account ID (default: from CLOUDFLARE_ACCOUNT_ID env var)
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        import os

        self.token = token or os.environ.get("CLOUDFLARE_API_TOKEN")
        if not self.token:
            raise ValueError(
                "API token required. Set CLOUDFLARE_API_TOKEN "
                "environment variable or pass token parameter."
            )

        self.account_id = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        if not self.account_id:
            logger.warning(
                "Account ID not set. Some operations (Workers, KV, R2) require it. "
                "Set CLOUDFLARE_ACCOUNT_ID environment variable or pass account_id parameter."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "BlackBox5/1.0",
            },
            timeout=timeout,
        )

        logger.info(f"Initialized CloudflareManager for account {self.account_id}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
        logger.debug("Closed HTTP client")

    # -------------------------------------------------------------------------
    # DNS Operations
    # -------------------------------------------------------------------------

    async def dns_create_record(
        self,
        zone_id: str,
        spec: DNSRecordSpec,
    ) -> Optional[DNSRecord]:
        """
        Create a DNS record.

        Args:
            zone_id: Zone ID
            spec: DNS record specification

        Returns:
            Created DNS record or None if failed

        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.info(f"Creating DNS record: {spec.name} ({spec.type})")

        payload = {
            "type": spec.type.value,
            "name": spec.name,
            "content": spec.content,
            "ttl": spec.ttl,
            "proxied": spec.proxied,
        }

        if spec.priority is not None:
            payload["priority"] = spec.priority

        response = await self.client.post(
            f"/zones/{zone_id}/dns_records",
            json=payload,
        )
        response.raise_for_status()

        data = response.json()["result"]
        record = DNSRecord(
            id=data["id"],
            type=DNSRecordType(data["type"]),
            name=data["name"],
            content=data["content"],
            ttl=data["ttl"],
            proxied=data["proxied"],
            zone_id=zone_id,
            zone_name=data["zone_name"],
            created_on=datetime.fromisoformat(data["created_on"].replace("Z", "+00:00")),
            modified_on=datetime.fromisoformat(data["modified_on"].replace("Z", "+00:00")),
        )

        logger.info(f"✅ Created DNS record: {record.id}")
        return record

    async def dns_update_record(
        self,
        zone_id: str,
        record_id: str,
        spec: DNSRecordSpec,
    ) -> Optional[DNSRecord]:
        """
        Update a DNS record.

        Args:
            zone_id: Zone ID
            record_id: Record ID
            spec: DNS record specification

        Returns:
            Updated DNS record or None if not found

        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.info(f"Updating DNS record: {record_id}")

        payload = {
            "type": spec.type.value,
            "name": spec.name,
            "content": spec.content,
            "ttl": spec.ttl,
            "proxied": spec.proxied,
        }

        if spec.priority is not None:
            payload["priority"] = spec.priority

        response = await self.client.patch(
            f"/zones/{zone_id}/dns_records/{record_id}",
            json=payload,
        )
        response.raise_for_status()

        data = response.json()["result"]
        record = DNSRecord(
            id=data["id"],
            type=DNSRecordType(data["type"]),
            name=data["name"],
            content=data["content"],
            ttl=data["ttl"],
            proxied=data["proxied"],
            zone_id=zone_id,
            zone_name=data["zone_name"],
            created_on=datetime.fromisoformat(data["created_on"].replace("Z", "+00:00")),
            modified_on=datetime.fromisoformat(data["modified_on"].replace("Z", "+00:00")),
        )

        logger.info(f"✅ Updated DNS record: {record_id}")
        return record

    async def dns_delete_record(
        self,
        zone_id: str,
        record_id: str,
    ) -> bool:
        """
        Delete a DNS record.

        Args:
            zone_id: Zone ID
            record_id: Record ID

        Returns:
            True if successful, False if not found

        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.info(f"Deleting DNS record: {record_id}")

        try:
            response = await self.client.delete(
                f"/zones/{zone_id}/dns_records/{record_id}"
            )
            response.raise_for_status()

            logger.info(f"✅ Deleted DNS record: {record_id}")
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"DNS record not found: {record_id}")
                return False
            raise

    async def dns_list_records(
        self,
        zone_id: str,
        record_type: Optional[DNSRecordType] = None,
        name: Optional[str] = None,
        limit: int = 100,
    ) -> list[DNSRecord]:
        """
        List DNS records for a zone.

        Args:
            zone_id: Zone ID
            record_type: Filter by record type (optional)
            name: Filter by name (optional)
            limit: Max results to return

        Returns:
            List of DNS records

        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.debug(f"Listing DNS records for zone: {zone_id}")

        params = {"per_page": limit}
        if record_type:
            params["type"] = record_type.value
        if name:
            params["name"] = name

        response = await self.client.get(
            f"/zones/{zone_id}/dns_records",
            params=params,
        )
        response.raise_for_status()

        data = response.json()["result"]
        records = [
            DNSRecord(
                id=item["id"],
                type=DNSRecordType(item["type"]),
                name=item["name"],
                content=item["content"],
                ttl=item["ttl"],
                proxied=item["proxied"],
                zone_id=zone_id,
                zone_name=item["zone_name"],
                created_on=datetime.fromisoformat(item["created_on"].replace("Z", "+00:00")),
                modified_on=datetime.fromisoformat(item["modified_on"].replace("Z", "+00:00")),
            )
            for item in data
        ]

        logger.debug(f"Listed {len(records)} DNS records")
        return records

    # -------------------------------------------------------------------------
    # Workers Operations
    # -------------------------------------------------------------------------

    async def workers_deploy(
        self,
        script_name: str,
        content: str,
    ) -> WorkerDeploymentResult:
        """
        Deploy a Worker script.

        Args:
            script_name: Script name
            content: Script content

        Returns:
            Deployment result

        Raises:
            ValueError: If account_id not set
            httpx.HTTPError: If API request fails
        """
        if not self.account_id:
            raise ValueError("account_id required for Workers operations")

        logger.info(f"Deploying Worker script: {script_name}")

        try:
            response = await self.client.put(
                f"/accounts/{self.account_id}/workers/scripts/{script_name}",
                content=content,
                headers={
                    "Content-Type": "application/javascript",
                },
            )
            response.raise_for_status()

            logger.info(f"✅ Deployed Worker script: {script_name}")
            return WorkerDeploymentResult(
                success=True,
                script_id=script_name,
                script_name=script_name,
                message="Worker deployed successfully",
                timestamp=datetime.now(timezone.utc),
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Worker deployment failed: {e}")
            return WorkerDeploymentResult(
                success=False,
                script_name=script_name,
                errors=[str(e)],
                message="Worker deployment failed",
                timestamp=datetime.now(timezone.utc),
            )

    async def workers_list(self) -> list[WorkerScript]:
        """
        List Worker scripts.

        Returns:
            List of Worker scripts

        Raises:
            ValueError: If account_id not set
            httpx.HTTPError: If API request fails
        """
        if not self.account_id:
            raise ValueError("account_id required for Workers operations")

        logger.debug("Listing Worker scripts")

        response = await self.client.get(
            f"/accounts/{self.account_id}/workers/scripts"
        )
        response.raise_for_status()

        data = response.json()["result"]
        scripts = [
            WorkerScript(
                id=item["id"],
                name=item["id"],
                modified_on=datetime.fromisoformat(item["modified_on"].replace("Z", "+00:00"))
                if "modified_on" in item
                else None,
                created_on=datetime.fromisoformat(item["created_on"].replace("Z", "+00:00"))
                if "created_on" in item
                else None,
            )
            for item in data
        ]

        logger.debug(f"Listed {len(scripts)} Worker scripts")
        return scripts

    async def workers_delete(self, script_name: str) -> bool:
        """
        Delete a Worker script.

        Args:
            script_name: Script name

        Returns:
            True if successful

        Raises:
            ValueError: If account_id not set
            httpx.HTTPError: If API request fails
        """
        if not self.account_id:
            raise ValueError("account_id required for Workers operations")

        logger.info(f"Deleting Worker script: {script_name}")

        response = await self.client.delete(
            f"/accounts/{self.account_id}/workers/scripts/{script_name}"
        )
        response.raise_for_status()

        logger.info(f"✅ Deleted Worker script: {script_name}")
        return True

    # -------------------------------------------------------------------------
    # KV Operations
    # -------------------------------------------------------------------------

    async def kv_write(
        self,
        namespace_id: str,
        key: str,
        value: str,
        expiration: Optional[int] = None,
    ) -> bool:
        """
        Write a value to KV store.

        Args:
            namespace_id: KV namespace ID
            key: Key name
            value: Value to write
            expiration: Expiration time in seconds (optional)

        Returns:
            True if successful

        Raises:
            ValueError: If account_id not set
            httpx.HTTPError: If API request fails
        """
        if not self.account_id:
            raise ValueError("account_id required for KV operations")

        logger.info(f"Writing to KV: {key}")

        url = f"/accounts/{self.account_id}/storage/kv/namespaces/{namespace_id}/values/{key}"

        params = {}
        if expiration:
            params["expiration_ttl"] = expiration

        response = await self.client.put(
            url,
            content=value,
            params=params,
            headers={"Content-Type": "text/plain"},
        )
        response.raise_for_status()

        logger.info(f"✅ Wrote to KV: {key}")
        return True

    async def kv_read(
        self,
        namespace_id: str,
        key: str,
    ) -> Optional[str]:
        """
        Read a value from KV store.

        Args:
            namespace_id: KV namespace ID
            key: Key name

        Returns:
            Value or None if not found

        Raises:
            ValueError: If account_id not set
            httpx.HTTPError: If API request fails
        """
        if not self.account_id:
            raise ValueError("account_id required for KV operations")

        logger.debug(f"Reading from KV: {key}")

        try:
            response = await self.client.get(
                f"/accounts/{self.account_id}/storage/kv/namespaces/{namespace_id}/values/{key}"
            )
            response.raise_for_status()

            value = response.text
            logger.debug(f"✅ Read from KV: {key}")
            return value

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"KV key not found: {key}")
                return None
            raise

    async def kv_delete(
        self,
        namespace_id: str,
        key: str,
    ) -> bool:
        """
        Delete a value from KV store.

        Args:
            namespace_id: KV namespace ID
            key: Key name

        Returns:
            True if successful

        Raises:
            ValueError: If account_id not set
            httpx.HTTPError: If API request fails
        """
        if not self.account_id:
            raise ValueError("account_id required for KV operations")

        logger.info(f"Deleting from KV: {key}")

        response = await self.client.delete(
            f"/accounts/{self.account_id}/storage/kv/namespaces/{namespace_id}/values/{key}"
        )
        response.raise_for_status()

        logger.info(f"✅ Deleted from KV: {key}")
        return True

    # -------------------------------------------------------------------------
    # R2 Operations (using boto3 for S3-compatible API)
    # -------------------------------------------------------------------------

    async def r2_upload(
        self,
        bucket_name: str,
        key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> R2Object:
        """
        Upload an object to R2.

        Args:
            bucket_name: Bucket name
            key: Object key
            content: Content to upload
            content_type: Content type
            metadata: Object metadata (optional)

        Returns:
            Uploaded R2 object

        Raises:
            ValueError: If account_id not set
            ImportError: If boto3 not installed
            Exception: If upload fails
        """
        if not self.account_id:
            raise ValueError("account_id required for R2 operations")

        logger.info(f"Uploading to R2: {bucket_name}/{key}")

        try:
            import boto3
            from botocore.client import Config
        except ImportError:
            raise ImportError(
                "boto3 required for R2 operations. "
                "Install with: pip install boto3"
            )

        # Create S3 client configured for R2
        s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
            aws_access_key_id="",  # Not used for R2 with token auth
            aws_secret_access_key="",  # Not used for R2 with token auth
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )

        # Upload using the token
        from urllib.parse import urlencode

        # For R2 with API token, we need to use different auth
        # This is a simplified implementation - production should use proper auth
        import os

        # Check if R2 credentials are available
        r2_access_key = os.environ.get("R2_ACCESS_KEY_ID")
        r2_secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")

        if r2_access_key and r2_secret_key:
            s3 = boto3.client(
                "s3",
                endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=r2_access_key,
                aws_secret_access_key=r2_secret_key,
                config=Config(signature_version="s3v4"),
                region_name="auto",
            )

        s3.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=content,
            ContentType=content_type,
            Metadata=metadata or {},
        )

        obj = R2Object(
            key=key,
            size=len(content),
            etag="",  # Would get from response
            last_modified=datetime.now(timezone.utc),
            content_type=content_type,
            bucket_name=bucket_name,
            metadata=metadata,
        )

        logger.info(f"✅ Uploaded to R2: {bucket_name}/{key}")
        return obj

    async def r2_download(
        self,
        bucket_name: str,
        key: str,
    ) -> Optional[bytes]:
        """
        Download an object from R2.

        Args:
            bucket_name: Bucket name
            key: Object key

        Returns:
            Object content or None if not found

        Raises:
            ValueError: If account_id not set
            ImportError: If boto3 not installed
            Exception: If download fails
        """
        if not self.account_id:
            raise ValueError("account_id required for R2 operations")

        logger.debug(f"Downloading from R2: {bucket_name}/{key}")

        try:
            import boto3
            from botocore.client import Config
        except ImportError:
            raise ImportError(
                "boto3 required for R2 operations. "
                "Install with: pip install boto3"
            )

        import os

        r2_access_key = os.environ.get("R2_ACCESS_KEY_ID")
        r2_secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")

        s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=r2_access_key or "",
            aws_secret_access_key=r2_secret_key or "",
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )

        try:
            response = s3.get_object(Bucket=bucket_name, Key=key)
            content = response["Body"].read()
            logger.debug(f"✅ Downloaded from R2: {bucket_name}/{key}")
            return content
        except s3.exceptions.NoSuchKey:
            logger.warning(f"R2 object not found: {bucket_name}/{key}")
            return None

    async def r2_delete(
        self,
        bucket_name: str,
        key: str,
    ) -> bool:
        """
        Delete an object from R2.

        Args:
            bucket_name: Bucket name
            key: Object key

        Returns:
            True if successful

        Raises:
            ValueError: If account_id not set
            ImportError: If boto3 not installed
            Exception: If delete fails
        """
        if not self.account_id:
            raise ValueError("account_id required for R2 operations")

        logger.info(f"Deleting from R2: {bucket_name}/{key}")

        try:
            import boto3
            from botocore.client import Config
        except ImportError:
            raise ImportError(
                "boto3 required for R2 operations. "
                "Install with: pip install boto3"
            )

        import os

        r2_access_key = os.environ.get("R2_ACCESS_KEY_ID")
        r2_secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")

        s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=r2_access_key or "",
            aws_secret_access_key=r2_secret_key or "",
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )

        s3.delete_object(Bucket=bucket_name, Key=key)

        logger.info(f"✅ Deleted from R2: {bucket_name}/{key}")
        return True

    async def r2_list(
        self,
        bucket_name: str,
        prefix: str = "",
        limit: int = 1000,
    ) -> list[R2Object]:
        """
        List objects in R2 bucket.

        Args:
            bucket_name: Bucket name
            prefix: Key prefix to filter
            limit: Max results

        Returns:
            List of R2 objects

        Raises:
            ValueError: If account_id not set
            ImportError: If boto3 not installed
            Exception: If list fails
        """
        if not self.account_id:
            raise ValueError("account_id required for R2 operations")

        logger.debug(f"Listing R2 objects: {bucket_name}/{prefix}")

        try:
            import boto3
            from botocore.client import Config
        except ImportError:
            raise ImportError(
                "boto3 required for R2 operations. "
                "Install with: pip install boto3"
            )

        import os

        r2_access_key = os.environ.get("R2_ACCESS_KEY_ID")
        r2_secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")

        s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=r2_access_key or "",
            aws_secret_access_key=r2_secret_key or "",
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )

        response = s3.list_objects_v2(
            Bucket=bucket_name, Prefix=prefix, MaxKeys=limit
        )

        objects = []
        if "Contents" in response:
            for item in response["Contents"]:
                objects.append(
                    R2Object(
                        key=item["Key"],
                        size=item["Size"],
                        etag=item["ETag"].strip('"'),
                        last_modified=item["LastModified"],
                        content_type="",
                        bucket_name=bucket_name,
                    )
                )

        logger.debug(f"Listed {len(objects)} R2 objects")
        return objects

    async def r2_presigned_url(
        self,
        bucket_name: str,
        key: str,
        expiration: int = 3600,
        method: str = "GET",
    ) -> R2PresignedURL:
        """
        Generate a presigned URL for R2 object.

        Args:
            bucket_name: Bucket name
            key: Object key
            expiration: URL expiration time in seconds (default: 1 hour)
            method: HTTP method (GET, PUT, DELETE)

        Returns:
            Presigned URL

        Raises:
            ValueError: If account_id not set
            ImportError: If boto3 not installed
            Exception: If URL generation fails
        """
        if not self.account_id:
            raise ValueError("account_id required for R2 operations")

        logger.debug(f"Generating presigned URL for R2: {bucket_name}/{key}")

        try:
            import boto3
            from botocore.client import Config
        except ImportError:
            raise ImportError(
                "boto3 required for R2 operations. "
                "Install with: pip install boto3"
            )

        import os

        r2_access_key = os.environ.get("R2_ACCESS_KEY_ID")
        r2_secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")

        s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=r2_access_key or "",
            aws_secret_access_key=r2_secret_key or "",
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )

        from botocore.exceptions import ClientError

        try:
            url = s3.generate_presigned_url(
                "get_object" if method == "GET" else "put_object",
                Params={"Bucket": bucket_name, "Key": key},
                ExpiresIn=expiration,
            )

            expires_at = datetime.now(timezone.utc).replace(
                second=0, microsecond=0
            ) + __import__("datetime").timedelta(seconds=expiration)

            result = R2PresignedURL(
                url=url,
                expires_at=expires_at,
                method=method,
            )

            logger.debug(f"✅ Generated presigned URL for R2: {bucket_name}/{key}")
            return result

        except ClientError as e:
            logger.error(f"❌ Failed to generate presigned URL: {e}")
            raise

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    async def check_connection(self) -> bool:
        """
        Check API connection.

        Returns:
            True if connection successful
        """
        try:
            response = await self.client.get("/user/tokens/verify")
            response.raise_for_status()
            logger.info("✅ Connection check successful")
            return True
        except Exception as e:
            logger.error(f"❌ Connection check failed: {e}")
            return False

    async def list_zones(self) -> list[dict[str, Any]]:
        """
        List all zones.

        Returns:
            List of zones

        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.debug("Listing zones")

        response = await self.client.get("/zones")
        response.raise_for_status()

        data = response.json()["result"]
        logger.debug(f"Listed {len(data)} zones")
        return data
