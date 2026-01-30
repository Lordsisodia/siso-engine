"""
Configuration helpers for Notion integration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class NotionConfig:
    """
    Configuration for Notion integration.

    Attributes:
        token: API token (integration token)
        base_url: API base URL
        timeout: Request timeout in seconds
        retry_count: Number of retries for failed requests
        retry_delay: Delay between retries in seconds
        rate_limit_calls: Rate limit calls per period
        rate_limit_period: Rate limit period in seconds
    """

    token: str
    base_url: str = "https://api.notion.com"
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    rate_limit_calls: int = 3
    rate_limit_period: float = 1.0

    @classmethod
    def from_env(cls) -> "NotionConfig":
        """
        Load configuration from environment variables.

        Environment Variables:
            NOTION_TOKEN: API token (required)
            NOTION_BASE_URL: API base URL (optional)
            NOTION_TIMEOUT: Request timeout (optional)
            NOTION_RETRY_COUNT: Number of retries (optional)
            NOTION_RETRY_DELAY: Delay between retries (optional)

        Returns:
            Configuration instance

        Raises:
            ValueError: If required environment variables not set
        """
        token = os.environ.get("NOTION_TOKEN")
        if not token:
            raise ValueError("NOTION_TOKEN environment variable not set")

        return cls(
            token=token,
            base_url=os.environ.get("NOTION_BASE_URL", "https://api.notion.com"),
            timeout=int(os.environ.get("NOTION_TIMEOUT", "30")),
            retry_count=int(os.environ.get("NOTION_RETRY_COUNT", "3")),
            retry_delay=float(os.environ.get("NOTION_RETRY_DELAY", "1.0")),
        )

    @classmethod
    def from_file(cls, path: Path | str) -> "NotionConfig":
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
            base_url=data.get("base_url", "https://api.notion.com"),
            timeout=data.get("timeout", 30),
            retry_count=data.get("retry_count", 3),
            retry_delay=data.get("retry_delay", 1.0),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "token": self.token,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "rate_limit_calls": self.rate_limit_calls,
            "rate_limit_period": self.rate_limit_period,
        }


def get_default_config() -> NotionConfig:
    """
    Get default configuration from environment.

    Returns:
        Configuration instance
    """
    return NotionConfig.from_env()


def validate_config(config: NotionConfig) -> list[str]:
    """
    Validate configuration and return list of errors.

    Args:
        config: Configuration to validate

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    if not config.token:
        errors.append("API token is required")

    if config.timeout < 1:
        errors.append("Timeout must be at least 1 second")

    if config.retry_count < 0:
        errors.append("Retry count cannot be negative")

    if config.retry_delay < 0:
        errors.append("Retry delay cannot be negative")

    if config.rate_limit_calls < 1:
        errors.append("Rate limit calls must be at least 1")

    if config.rate_limit_period < 0.1:
        errors.append("Rate limit period must be at least 0.1 seconds")

    return errors
