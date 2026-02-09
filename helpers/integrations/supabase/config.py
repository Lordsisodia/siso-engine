"""
Configuration helpers for Supabase integration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SupabaseConfig:
    """
    Configuration for Supabase integration.

    Attributes:
        project_ref: Project reference (subdomain of supabase.co)
        service_role_key: Service role key (bypasses RLS, backend only!)
        base_url: API base URL
        timeout: Request timeout in seconds
        retry_count: Number of retries for failed requests
        retry_delay: Delay between retries in seconds
    """

    project_ref: str
    service_role_key: str
    base_url: str | None = None
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0

    @property
    def api_url(self) -> str:
        """Get the API base URL."""
        if self.base_url:
            return self.base_url
        return f"https://{self.project_ref}.supabase.co"

    @classmethod
    def from_env(cls) -> "SupabaseConfig":
        """
        Load configuration from environment variables.

        Environment Variables:
            SUPABASE_PROJECT_REF: Project reference (required)
            SUPABASE_SERVICE_ROLE_KEY: Service role key (required)
            SUPABASE_BASE_URL: API base URL (optional)
            SUPABASE_TIMEOUT: Request timeout (optional)

        Returns:
            Configuration instance

        Raises:
            ValueError: If required environment variables not set
        """
        project_ref = os.environ.get("SUPABASE_PROJECT_REF")
        if not project_ref:
            raise ValueError(
                "SUPABASE_PROJECT_REF environment variable not set. "
                "Get your project ref from your Supabase project settings."
            )

        service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not service_role_key:
            raise ValueError(
                "SUPABASE_SERVICE_ROLE_KEY environment variable not set. "
                "Get your service role key from your Supabase project settings."
            )

        return cls(
            project_ref=project_ref,
            service_role_key=service_role_key,
            base_url=os.environ.get("SUPABASE_BASE_URL"),
            timeout=int(os.environ.get("SUPABASE_TIMEOUT", "30")),
        )

    @classmethod
    def from_file(cls, path: Path | str) -> "SupabaseConfig":
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
            project_ref=data["project_ref"],
            service_role_key=data["service_role_key"],
            base_url=data.get("base_url"),
            timeout=data.get("timeout", 30),
        )


def get_default_config() -> SupabaseConfig:
    """
    Get default configuration from environment.

    Returns:
        Configuration instance
    """
    return SupabaseConfig.from_env()
