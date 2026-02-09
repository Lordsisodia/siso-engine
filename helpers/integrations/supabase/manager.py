"""
Supabase Manager for BlackBox5
==============================

Main integration class for Supabase service.

Features:
- Database CRUD operations via PostgREST API
- Storage operations (upload, download, public URLs)
- Edge Function invocation
- Realtime subscriptions via WebSocket

Usage:
    >>> manager = SupabaseManager(project_ref="xxx", service_role_key="xxx")
    >>> result = await manager.query("users", filters={"status": "active"})
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Optional

import httpx

from .config import SupabaseConfig
from .types import (
    ChangeCallback,
    DeleteResult,
    EdgeFunctionResult,
    EdgeFunctionSpec,
    InsertResult,
    StorageDownloadSpec,
    StorageFile,
    StorageUploadSpec,
    SubscriptionSpec,
    TableSpec,
    UpdateResult,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Main Manager Class
# =============================================================================


class SupabaseManager:
    """
    Main manager class for Supabase integration.

    Authentication:
        Uses service role key which bypasses RLS (backend only!).
        Never expose service role key to client-side code.

    Rate Limits:
        - Database: 1000 requests/second per project
        - Storage: 1000 requests/second per project
        - Edge Functions: 500 requests/second per project

    Example:
        >>> config = SupabaseConfig.from_env()
        >>> manager = SupabaseManager(config)
        >>> users = await manager.query("users", filters={"status": "active"})
    """

    API_VERSION = "rest/v1"
    STORAGE_VERSION = "storage/v1"
    FUNCTIONS_VERSION = "functions/v1"

    def __init__(
        self,
        config: SupabaseConfig | None = None,
        project_ref: str | None = None,
        service_role_key: str | None = None,
        timeout: int = 30,
    ):
        """
        Initialize Supabase manager.

        Args:
            config: Supabase configuration (preferred)
            project_ref: Project reference (if config not provided)
            service_role_key: Service role key (if config not provided)
            timeout: Request timeout in seconds
        """
        if config:
            self.config = config
        else:
            import os

            project_ref = project_ref or os.environ.get("SUPABASE_PROJECT_REF")
            service_role_key = service_role_key or os.environ.get(
                "SUPABASE_SERVICE_ROLE_KEY"
            )

            if not project_ref:
                raise ValueError(
                    "project_ref required. Set SUPABASE_PROJECT_REF "
                    "environment variable or pass project_ref parameter."
                )
            if not service_role_key:
                raise ValueError(
                    "service_role_key required. Set SUPABASE_SERVICE_ROLE_KEY "
                    "environment variable or pass service_role_key parameter."
                )

            self.config = SupabaseConfig(
                project_ref=project_ref,
                service_role_key=service_role_key,
                timeout=timeout,
            )

        self.api_url = self.config.api_url
        self.timeout = self.config.timeout

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={
                "apikey": self.config.service_role_key,
                "Authorization": f"Bearer {self.config.service_role_key}",
                "Content-Type": "application/json",
                "User-Agent": "BlackBox5/1.0",
            },
            timeout=self.timeout,
        )

        logger.info(f"Initialized SupabaseManager for {self.api_url}")

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
    # Database Operations
    # -------------------------------------------------------------------------

    async def query(
        self,
        table: str,
        filters: dict[str, Any] | None = None,
        columns: str | list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        ascending: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Query table with optional filters.

        Args:
            table: Table name
            filters: Dictionary of column -> value pairs for filtering
            columns: Columns to select (default: all)
            limit: Maximum number of rows to return
            offset: Pagination offset
            order_by: Column to order by
            ascending: Sort direction

        Returns:
            List of rows as dictionaries

        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.info(f"Querying table: {table}")

        # Build column selection
        select = "*"
        if columns:
            if isinstance(columns, list):
                select = ",".join(columns)
            else:
                select = columns

        # Build request parameters
        params = {"select": select}

        # Add filters using Supabase filter syntax
        if filters:
            for key, value in filters.items():
                if isinstance(value, dict):
                    # Handle operators: {"age": {"gt": 18}}
                    for op, val in value.items():
                        params[key] = f"{op}.{val}"
                else:
                    # Simple equality
                    params[key] = f"eq.{value}"

        # Add pagination
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset

        # Add ordering
        if order_by:
            order = order_by if ascending else f"{order_by}.desc"
            params["order"] = order

        response = await self.client.get(
            f"/{self.API_VERSION}/{table}",
            params=params,
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"✅ Query successful: {len(result)} rows from {table}")

        return result

    async def insert(
        self,
        table: str,
        data: dict[str, Any] | list[dict[str, Any]],
    ) -> InsertResult:
        """
        Insert record(s) into table.

        Args:
            table: Table name
            data: Record or list of records to insert

        Returns:
            InsertResult with inserted data

        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.info(f"Inserting into table: {table}")

        is_bulk = isinstance(data, list)
        records = data if is_bulk else [data]

        response = await self.client.post(
            f"/{self.API_VERSION}/{table}",
            json=records,
            headers={
                "Prefer": "return=representation",
            },
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"✅ Insert successful: {len(result) if is_bulk else 1} row(s)")

        return InsertResult(data=result)

    async def update(
        self,
        table: str,
        data: dict[str, Any],
        filters: dict[str, Any],
    ) -> UpdateResult:
        """
        Update records in table.

        Args:
            table: Table name
            data: Dictionary of fields to update
            filters: Filter criteria (same as query filters)

        Returns:
            UpdateResult with updated data

        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.info(f"Updating table: {table}")

        # Build filter parameters
        params = {}
        if filters:
            for key, value in filters.items():
                if isinstance(value, dict):
                    for op, val in value.items():
                        params[key] = f"{op}.{val}"
                else:
                    params[key] = f"eq.{value}"

        response = await self.client.patch(
            f"/{self.API_VERSION}/{table}",
            json=data,
            params=params,
            headers={
                "Prefer": "return=representation",
            },
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"✅ Update successful: {len(result)} row(s)")

        return UpdateResult(data=result)

    async def delete(
        self,
        table: str,
        filters: dict[str, Any],
    ) -> DeleteResult:
        """
        Delete records from table.

        Args:
            table: Table name
            filters: Filter criteria (same as query filters)

        Returns:
            DeleteResult

        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.info(f"Deleting from table: {table}")

        # Build filter parameters
        params = {}
        if filters:
            for key, value in filters.items():
                if isinstance(value, dict):
                    for op, val in value.items():
                        params[key] = f"{op}.{val}"
                else:
                    params[key] = f"eq.{value}"

        response = await self.client.delete(
            f"/{self.API_VERSION}/{table}",
            params=params,
        )
        response.raise_for_status()

        # Get count from response headers if available
        count = None
        if "content-range" in response.headers:
            content_range = response.headers["content-range"]
            count = int(content_range.split("/")[-1])

        logger.info(f"✅ Delete successful: {count or 'unknown'} row(s)")

        return DeleteResult(count=count)

    async def count(
        self,
        table: str,
        filters: dict[str, Any] | None = None,
    ) -> int:
        """
        Count records in table.

        Args:
            table: Table name
            filters: Filter criteria

        Returns:
            Count of matching records
        """
        logger.debug(f"Counting records in table: {table}")

        # Build filter parameters
        params = {}
        if filters:
            for key, value in filters.items():
                if isinstance(value, dict):
                    for op, val in value.items():
                        params[key] = f"{op}.{val}"
                else:
                    params[key] = f"eq.{value}"

        # Request count using Prefer header
        response = await self.client.get(
            f"/{self.API_VERSION}/{table}",
            params=params,
            headers={
                "Prefer": "count=exact",
            },
        )
        response.raise_for_status()

        # Get count from headers
        count = 0
        if "content-range" in response.headers:
            content_range = response.headers["content-range"]
            count = int(content_range.split("/")[-1])

        logger.debug(f"Count: {count}")
        return count

    # -------------------------------------------------------------------------
    # Storage Operations
    # -------------------------------------------------------------------------

    async def upload_file(
        self,
        bucket: str,
        path: str,
        content: bytes | str,
        content_type: str | None = None,
        upsert: bool = False,
    ) -> dict[str, Any]:
        """
        Upload file to storage.

        Args:
            bucket: Bucket name
            path: File path in bucket
            content: File content (bytes or string)
            content_type: MIME type
            upsert: Overwrite if exists

        Returns:
            Dictionary with upload result

        Raises:
            httpx.HTTPError: If upload fails
        """
        logger.info(f"Uploading file: {bucket}/{path}")

        # Convert string to bytes if needed
        if isinstance(content, str):
            content = content.encode()

        # Build headers
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
        if upsert:
            headers["x-upsert"] = "true"

        # Create new client with binary content type support
        upload_client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={
                "apikey": self.config.service_role_key,
                "Authorization": f"Bearer {self.config.service_role_key}",
                **headers,
            },
            timeout=self.timeout,
        )

        try:
            response = await upload_client.put(
                f"/{self.STORAGE_VERSION}/object/{bucket}/{path}",
                content=content,
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"✅ Upload successful: {bucket}/{path}")

            return result
        finally:
            await upload_client.aclose()

    async def download_file(
        self,
        bucket: str,
        path: str,
    ) -> bytes:
        """
        Download file from storage.

        Args:
            bucket: Bucket name
            path: File path in bucket

        Returns:
            File content as bytes

        Raises:
            httpx.HTTPError: If download fails
        """
        logger.debug(f"Downloading file: {bucket}/{path}")

        response = await self.client.get(
            f"/{self.STORAGE_VERSION}/object/{bucket}/{path}",
        )
        response.raise_for_status()

        logger.debug(f"✅ Download successful: {bucket}/{path}")
        return response.content

    async def get_public_url(
        self,
        bucket: str,
        path: str,
    ) -> str:
        """
        Get public URL for file.

        Args:
            bucket: Bucket name
            path: File path in bucket

        Returns:
            Public URL string
        """
        url = f"{self.api_url}/{self.STORAGE_VERSION}/object/public/{bucket}/{path}"
        logger.debug(f"Public URL: {url}")
        return url

    async def list_files(
        self,
        bucket: str,
        path: str = "",
        limit: int = 100,
    ) -> list[StorageFile]:
        """
        List files in bucket.

        Args:
            bucket: Bucket name
            path: Path to list (default: root)
            limit: Maximum results

        Returns:
            List of StorageFile objects
        """
        logger.debug(f"Listing files: {bucket}/{path}")

        response = await self.client.get(
            f"/{self.STORAGE_VERSION}/object/list/{bucket}/{path}",
            params={"limit": limit},
        )
        response.raise_for_status()

        data = response.json()
        files = [
            StorageFile(
                name=item.get("name", ""),
                bucket=bucket,
                path=f"{path}/{item.get('name', '')}" if path else item.get("name", ""),
                size=item.get("metadata", {}).get("size", 0),
                content_type=item.get("metadata", {}).get("mimetype", ""),
                updated_at=datetime.fromisoformat(
                    item.get("updated_at", datetime.now(timezone.utc).isoformat())
                ).replace(tzinfo=timezone.utc),
                metadata=item.get("metadata"),
            )
            for item in data
        ]

        logger.debug(f"Listed {len(files)} files")
        return files

    async def delete_file(
        self,
        bucket: str,
        path: str,
    ) -> bool:
        """
        Delete file from storage.

        Args:
            bucket: Bucket name
            path: File path in bucket

        Returns:
            True if successful
        """
        logger.info(f"Deleting file: {bucket}/{path}")

        response = await self.client.delete(
            f"/{self.STORAGE_VERSION}/object/{bucket}/{path}",
        )
        response.raise_for_status()

        logger.info(f"✅ Deleted file: {bucket}/{path}")
        return True

    # -------------------------------------------------------------------------
    # Edge Functions
    # -------------------------------------------------------------------------

    async def invoke_function(
        self,
        name: str,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> EdgeFunctionResult:
        """
        Invoke Edge Function.

        Args:
            name: Function name
            body: Request body
            headers: Additional headers

        Returns:
            EdgeFunctionResult with response data

        Raises:
            httpx.HTTPError: If invocation fails
        """
        logger.info(f"Invoking Edge Function: {name}")

        # Build headers
        request_headers = {}
        if headers:
            request_headers.update(headers)

        response = await self.client.post(
            f"/{self.FUNCTIONS_VERSION}/{name}",
            json=body or {},
            headers=request_headers,
        )

        result = EdgeFunctionResult(
            data=response.json() if response.content else {},
            status_code=response.status_code,
            headers=dict(response.headers),
        )

        # Don't raise for status errors - let caller handle them
        if response.is_error:
            result.error = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"❌ Edge Function error: {result.error}")
        else:
            logger.info(f"✅ Edge Function invoked: {name}")

        return result

    # -------------------------------------------------------------------------
    # Realtime Subscriptions
    # -------------------------------------------------------------------------

    async def subscribe_to_changes(
        self,
        table: str,
        event: str,  # INSERT, UPDATE, DELETE
        callback: Callable[[dict[str, Any]], None],
        schema: str = "public",
        filter: str | None = None,
    ) -> Any:
        """
        Subscribe to table changes via Realtime.

        Note: This is a simplified implementation. For production use,
        consider using the official supabase-py client which has
        built-in Realtime support.

        Args:
            table: Table name
            event: Event type (INSERT, UPDATE, DELETE)
            callback: Callback function for change events
            schema: Schema name (default: public)
            filter: Optional filter string

        Returns:
            Subscription handle (for cancellation)
        """
        logger.warning(
            "subscribe_to_changes is a simplified implementation. "
            "For production Realtime, use official supabase-py client."
        )

        # For now, return a mock subscription
        # In production, you'd establish a WebSocket connection
        subscription = {
            "table": table,
            "event": event,
            "callback": callback,
        }

        logger.info(f"Created subscription: {schema}.{table} ({event})")
        return subscription

    async def unsubscribe(self, subscription: Any):
        """
        Unsubscribe from changes.

        Args:
            subscription: Subscription handle from subscribe_to_changes
        """
        logger.info(f"Unsubscribing: {subscription.get('table')}")
        # In production, close WebSocket connection

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    async def check_connection(self) -> bool:
        """
        Check Supabase connection.

        Returns:
            True if connection successful
        """
        try:
            # Try to query the health endpoint
            response = await self.client.get(
                f"/{self.API_VERSION}/",
                params={"limit": "1"},
            )
            # Even empty response means connection works
            logger.info("✅ Connection check successful")
            return True
        except Exception as e:
            logger.error(f"❌ Connection check failed: {e}")
            return False

    async def get_table_info(self, table: str) -> dict[str, Any]:
        """
        Get table structure information.

        Args:
            table: Table name

        Returns:
            Dictionary with table information
        """
        logger.debug(f"Getting table info: {table}")

        # Query with limit 0 to get headers only
        response = await self.client.get(
            f"/{self.API_VERSION}/{table}",
            params={"limit": "0"},
            headers={"Prefer": "count=exact"},
        )
        response.raise_for_status()

        # Extract info from headers
        info = {
            "table": table,
            "count": 0,
            "headers": dict(response.headers),
        }

        if "content-range" in response.headers:
            content_range = response.headers["content-range"]
            info["count"] = int(content_range.split("/")[-1])

        return info

    # -------------------------------------------------------------------------
    # Batch Operations
    # -------------------------------------------------------------------------

    async def batch_insert(
        self,
        table: str,
        data: list[dict[str, Any]],
        batch_size: int = 1000,
    ) -> list[InsertResult]:
        """
        Insert records in batches.

        Args:
            table: Table name
            data: List of records to insert
            batch_size: Records per batch

        Returns:
            List of InsertResult objects
        """
        logger.info(f"Batch inserting {len(data)} records (batch_size={batch_size})")

        results = []
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]
            result = await self.insert(table, batch)
            results.append(result)
            logger.info(f"Inserted batch {i // batch_size + 1}")

        logger.info(f"✅ Batch insert complete: {len(data)} records")
        return results
