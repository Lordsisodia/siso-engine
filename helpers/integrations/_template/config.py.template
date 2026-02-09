"""
Configuration helpers for {SERVICE_NAME} integration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class {ServiceName}Config:
    """
    Configuration for {SERVICE_NAME} integration.

    Attributes:
        token: API token
        base_url: API base URL
        timeout: Request timeout in seconds
        retry_count: Number of retries for failed requests
        retry_delay: Delay between retries in seconds
    """

    token: str
    base_url: str = "https://api.{SERVICE_LOWER}.com"
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0

    @classmethod
    def from_env(cls) -> "{ServiceName}Config":
        """
        Load configuration from environment variables.

        Environment Variables:
            {SERVICE_UPPER}_TOKEN: API token (required)
            {SERVICE_UPPER}_BASE_URL: API base URL (optional)
            {SERVICE_UPPER}_TIMEOUT: Request timeout (optional)

        Returns:
            Configuration instance

        Raises:
            ValueError: If required environment variables not set
        """
        token = os.environ.get("{SERVICE_UPPER}_TOKEN")
        if not token:
            raise ValueError(
                "{SERVICE_UPPER}_TOKEN environment variable not set"
            )

        return cls(
            token=token,
            base_url=os.environ.get(
                "{SERVICE_UPPER}_BASE_URL",
                "https://api.{SERVICE_LOWER}.com"
            ),
            timeout=int(os.environ.get("{SERVICE_UPPER}_TIMEOUT", "30")),
        )

    @classmethod
    def from_file(cls, path: Path | str) -> "{ServiceName}Config":
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
            base_url=data.get("base_url", "https://api.{SERVICE_LOWER}.com"),
            timeout=data.get("timeout", 30),
        )


def get_default_config() -> {ServiceName}Config:
    """
    Get default configuration from environment.

    Returns:
        Configuration instance
    """
    return {ServiceName}Config.from_env()
