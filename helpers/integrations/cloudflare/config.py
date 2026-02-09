"""
Configuration helpers for Cloudflare integration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CloudflareConfig:
    """
    Configuration for Cloudflare integration.

    Attributes:
        token: Cloudflare API token
        account_id: Cloudflare Account ID (required for Workers, KV, R2)
        base_url: API base URL
        timeout: Request timeout in seconds
        retry_count: Number of retries for failed requests
        retry_delay: Delay between retries in seconds
    """

    token: str
    account_id: str | None = None
    base_url: str = "https://api.cloudflare.com/client/v4"
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0

    @classmethod
    def from_env(cls) -> "CloudflareConfig":
        """
        Load configuration from environment variables.

        Environment Variables:
            CLOUDFLARE_API_TOKEN: API token (required)
            CLOUDFLARE_ACCOUNT_ID: Account ID (optional but recommended)
            CLOUDFLARE_BASE_URL: API base URL (optional)
            CLOUDFLARE_TIMEOUT: Request timeout (optional)

        Returns:
            Configuration instance

        Raises:
            ValueError: If required environment variables not set
        """
        token = os.environ.get("CLOUDFLARE_API_TOKEN")
        if not token:
            raise ValueError(
                "CLOUDFLARE_API_TOKEN environment variable not set"
            )

        return cls(
            token=token,
            account_id=os.environ.get("CLOUDFLARE_ACCOUNT_ID"),
            base_url=os.environ.get(
                "CLOUDFLARE_BASE_URL",
                "https://api.cloudflare.com/client/v4"
            ),
            timeout=int(os.environ.get("CLOUDFLARE_TIMEOUT", "30")),
        )

    @classmethod
    def from_file(cls, path: Path | str) -> "CloudflareConfig":
        """
        Load configuration from file.

        Args:
            path: Path to config file (JSON or YAML)

        Returns:
            Configuration instance
        """
        import json

        path = Path(path)
        data = json.loads(path.read_text())

        return cls(
            token=data["token"],
            account_id=data.get("account_id"),
            base_url=data.get("base_url", "https://api.cloudflare.com/client/v4"),
            timeout=data.get("timeout", 30),
        )


def get_default_config() -> CloudflareConfig:
    """
    Get default configuration from environment.

    Returns:
        Configuration instance
    """
    return CloudflareConfig.from_env()
