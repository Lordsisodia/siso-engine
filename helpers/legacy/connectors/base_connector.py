"""
Base Connector Class for RALF
Abstract base class for all service connectors (Slack, Jira, Trello, etc.)
Part of Feature F-012 (API Gateway & External Service Integration)

Usage:
    from connectors.base_connector import BaseConnector

    class MyConnector(BaseConnector):
        def send_notification(self, message, **kwargs):
            # Implement notification logic
            pass

Requirements:
    - requests library for HTTP calls
    - Configuration file with connector credentials
"""

import logging
import time
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import requests


logger = logging.getLogger(__name__)


class ConnectorStatus(Enum):
    """Connector status enumeration."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class ConnectorResult:
    """Result of a connector operation."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error
        }


class ConnectorError(Exception):
    """Base exception for connector errors."""
    pass


class ConnectorConfigError(ConnectorError):
    """Connector configuration error."""
    pass


class ConnectorAuthError(ConnectorError):
    """Connector authentication error."""
    pass


class ConnectorAPIError(ConnectorError):
    """Connector API error."""
    pass


class BaseConnector(ABC):
    """
    Abstract base class for service connectors.

    Provides common functionality:
    - Configuration management
    - Authentication
    - Error handling
    - Retry logic
    - Logging
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize connector.

        Args:
            name: Connector name (e.g., 'slack', 'jira', 'trello')
            config: Connector configuration dictionary
        """
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', False)
        self.status = ConnectorStatus.ENABLED if self.enabled else ConnectorStatus.DISABLED

        # Retry settings
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1.0)
        self.timeout = config.get('timeout', 30)

        # Session for HTTP requests
        self.session = requests.Session()
        self._setup_session()

        if self.enabled:
            self._validate_config()
            logger.info(f"{self.name} connector initialized")
        else:
            logger.info(f"{self.name} connector disabled")

    def _setup_session(self):
        """Setup HTTP session with common settings."""
        self.session.headers.update({
            'User-Agent': f'RALF-Connector/{self.name}/1.0'
        })

    @abstractmethod
    def _validate_config(self):
        """
        Validate connector configuration.

        Raises:
            ConnectorConfigError: If configuration is invalid
        """
        pass

    @abstractmethod
    def send_notification(self, message: str, **kwargs) -> ConnectorResult:
        """
        Send notification to the service.

        Args:
            message: Message to send
            **kwargs: Additional parameters (channel, user, etc.)

        Returns:
            ConnectorResult with operation status
        """
        pass

    def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry: bool = True
    ) -> requests.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Request URL
            headers: Request headers
            params: Query parameters
            data: Form data
            json_data: JSON data
            retry: Whether to retry on failure

        Returns:
            Response object

        Raises:
            ConnectorAuthError: Authentication failed
            ConnectorAPIError: API request failed
        """
        last_error = None

        for attempt in range(self.max_retries if retry else 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json_data,
                    timeout=self.timeout
                )

                # Check for authentication errors
                if response.status_code == 401:
                    raise ConnectorAuthError(f"Authentication failed: {response.text}")

                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                    logger.warning(f"Rate limited, retrying after {retry_after}s")
                    time.sleep(retry_after)
                    continue

                # Check for server errors
                if response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue

                # Raise for other errors
                response.raise_for_status()

                return response

            except requests.exceptions.Timeout:
                last_error = f"Request timeout after {self.timeout}s"
                logger.error(f"{self.name}: {last_error}")

            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {e}"
                logger.error(f"{self.name}: {last_error}")

            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP error: {e}"
                logger.error(f"{self.name}: {last_error}")

            except ConnectorAuthError:
                raise

            except Exception as e:
                last_error = f"Unexpected error: {e}"
                logger.error(f"{self.name}: {last_error}")

            # Retry delay
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))

        # All retries failed
        raise ConnectorAPIError(last_error or "Request failed after all retries")

    def _log_operation(self, operation: str, result: ConnectorResult):
        """
        Log connector operation.

        Args:
            operation: Operation description
            result: Operation result
        """
        if result.success:
            logger.info(f"{self.name}: {operation} - SUCCESS: {result.message}")
        else:
            logger.error(f"{self.name}: {operation} - FAILED: {result.error}")

    def test_connection(self) -> ConnectorResult:
        """
        Test connector connection.

        Returns:
            ConnectorResult with test status
        """
        if not self.enabled:
            return ConnectorResult(
                success=False,
                message=f"{self.name} connector is disabled",
                error="Connector disabled"
            )

        try:
            # Subclasses should implement specific test
            return ConnectorResult(
                success=True,
                message=f"{self.name} connection successful"
            )

        except Exception as e:
            return ConnectorResult(
                success=False,
                message=f"{self.name} connection failed",
                error=str(e)
            )

    def get_status(self) -> Dict[str, Any]:
        """
        Get connector status.

        Returns:
            Dictionary with connector status
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "status": self.status.value,
            "max_retries": self.max_retries,
            "timeout": self.timeout
        }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()


class NotificationMixin:
    """
    Mixin for connectors that support notifications.

    Provides common notification formatting and utility methods.
    """

    @staticmethod
    def format_message(
        title: str,
        message: str,
        level: str = "info",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format notification message.

        Args:
            title: Message title
            message: Message content
            level: Message level (info, warning, error, success)
            metadata: Additional metadata

        Returns:
            Formatted message string
        """
        emoji_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅'
        }

        emoji = emoji_map.get(level, '')

        formatted = f"{emoji} *{title}*\n\n{message}"

        if metadata:
            formatted += "\n\n"
            for key, value in metadata.items():
                formatted += f"• {key}: {value}\n"

        return formatted

    @staticmethod
    def truncate_message(message: str, max_length: int = 4000) -> str:
        """
        Truncate message to maximum length.

        Args:
            message: Message to truncate
            max_length: Maximum length

        Returns:
            Truncated message with ellipsis
        """
        if len(message) <= max_length:
            return message

        return message[:max_length - 3] + "..."


class WebhookMixin:
    """
    Mixin for connectors that support webhooks.

    Provides webhook registration and management utilities.
    """

    def register_webhook(self, webhook_url: str, events: List[str]) -> ConnectorResult:
        """
        Register webhook for connector.

        Args:
            webhook_url: Webhook URL
            events: List of events to subscribe to

        Returns:
            ConnectorResult with registration status
        """
        raise NotImplementedError("Subclasses must implement register_webhook")

    def unregister_webhook(self, webhook_url: str) -> ConnectorResult:
        """
        Unregister webhook for connector.

        Args:
            webhook_url: Webhook URL

        Returns:
            ConnectorResult with unregistration status
        """
        raise NotImplementedError("Subclasses must implement unregister_webhook")
