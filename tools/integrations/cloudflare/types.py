"""
Data types and enums for Cloudflare integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# =============================================================================
# Enums
# =============================================================================


class DNSRecordType(str, Enum):
    """DNS record types supported by Cloudflare."""

    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    TXT = "TXT"
    MX = "MX"
    NS = "NS"
    SRV = "SRV"
    CAA = "CAA"


class DNSRecordProxied(str, Enum):
    """DNS proxied status."""

    ENABLED = "true"
    DISABLED = "false"


class WorkerStatus(str, Enum):
    """Worker deployment statuses."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    FAILED = "failed"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class DNSRecord:
    """
    DNS record data class.

    Attributes:
        id: Record ID
        type: Record type (A, AAAA, CNAME, etc.)
        name: Record name
        content: Record content (IP address, domain, etc.)
        ttl: Time to live in seconds
        proxied: Whether Cloudflare proxy is enabled
        zone_id: Zone ID
        zone_name: Zone name
        created_on: Creation timestamp
        modified_on: Last modified timestamp
        metadata: Additional metadata
    """

    id: str
    type: DNSRecordType
    name: str
    content: str
    ttl: int
    proxied: bool
    zone_id: str
    zone_name: str
    created_on: datetime
    modified_on: datetime
    metadata: Optional[dict[str, Any]] = None


@dataclass
class DNSRecordSpec:
    """
    Specification for creating/updating DNS records.

    Attributes:
        type: Record type
        name: Record name (e.g., "subdomain.example.com")
        content: Record content (IP address, domain, etc.)
        ttl: Time to live in seconds (default: 1 = auto)
        proxied: Enable Cloudflare proxy (default: True)
        priority: Priority for MX/SRV records (optional)
    """

    type: DNSRecordType
    name: str
    content: str
    ttl: int = 1
    proxied: bool = True
    priority: Optional[int] = None


@dataclass
class WorkerScript:
    """
    Worker script data class.

    Attributes:
        id: Script ID
        name: Script name
        content: Script content
        size: Script size in bytes
        modified_on: Last modified timestamp
        created_on: Creation timestamp
        status: Deployment status
        metadata: Additional metadata
    """

    id: str
    name: str
    content: Optional[str] = None
    size: Optional[int] = None
    modified_on: Optional[datetime] = None
    created_on: Optional[datetime] = None
    status: Optional[WorkerStatus] = None
    metadata: Optional[dict[str, Any]] = None


@dataclass
class WorkerDeploymentResult:
    """
    Result of worker deployment.

    Attributes:
        success: Whether deployment succeeded
        script_id: Script ID
        script_name: Script name
        errors: List of errors (if any)
        message: Deployment message
        timestamp: Deployment timestamp
    """

    success: bool
    script_id: Optional[str] = None
    script_name: Optional[str] = None
    errors: Optional[list[str]] = None
    message: Optional[str] = None
    timestamp: Optional[datetime] = None


@dataclass
class KVOperation:
    """
    KV operation specification.

    Attributes:
        namespace_id: KV namespace ID
        key: Key name
        value: Value to write
        expiration: Expiration time in seconds (optional)
        metadata: Additional metadata (optional)
    """

    namespace_id: str
    key: str
    value: str
    expiration: Optional[int] = None
    metadata: Optional[dict[str, Any]] = None


@dataclass
class KVEntry:
    """
    KV entry data class.

    Attributes:
        key: Key name
        value: Value content
        metadata: Entry metadata
        expiration: Expiration timestamp (optional)
    """

    key: str
    value: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    expiration: Optional[datetime] = None


@dataclass
class R2Object:
    """
    R2 object data class.

    Attributes:
        key: Object key
        size: Object size in bytes
        etag: Object ETag
        last_modified: Last modified timestamp
        content_type: Content type
        metadata: Object metadata
        bucket_name: Bucket name
    """

    key: str
    size: int
    etag: str
    last_modified: datetime
    content_type: str
    bucket_name: str
    metadata: Optional[dict[str, Any]] = None


@dataclass
class R2UploadSpec:
    """
    Specification for uploading to R2.

    Attributes:
        bucket_name: Bucket name
        key: Object key
        content: Content to upload
        content_type: Content type
        metadata: Object metadata (optional)
    """

    bucket_name: str
    key: str
    content: bytes
    content_type: str = "application/octet-stream"
    metadata: Optional[dict[str, Any]] = None


@dataclass
class R2PresignedURL:
    """
    Presigned URL data class.

    Attributes:
        url: Presigned URL
        expires_at: Expiration timestamp
        method: HTTP method
        metadata: Additional metadata
    """

    url: str
    expires_at: datetime
    method: str = "GET"
    metadata: Optional[dict[str, Any]] = None
