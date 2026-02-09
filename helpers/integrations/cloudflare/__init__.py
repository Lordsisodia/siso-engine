"""
Cloudflare Integration for BlackBox5
=====================================

This module provides integration with Cloudflare services.

Features:
- DNS management (create, update, delete, list records)
- Workers deployment and management
- KV store operations
- R2 storage operations (S3-compatible)

Usage:
    >>> from integration.cloudflare import CloudflareManager
    >>> manager = CloudflareManager()
    >>> await manager.dns_create_record(...)
"""

from .manager import CloudflareManager

__all__ = ["CloudflareManager"]

__version__ = "1.0.0"
