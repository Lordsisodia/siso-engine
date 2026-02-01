"""
Slack Connector for RALF
Sends notifications to Slack channels and handles Slack webhooks
Part of Feature F-012 (API Gateway & External Service Integration)

Usage:
    from connectors.slack_connector import SlackConnector

    connector = SlackConnector(config={
        'enabled': True,
        'webhook_url': 'https://hooks.slack.com/services/...',
        'bot_token': 'xoxb-...'
    })
    result = connector.send_notification('Hello from RALF!', channel='#general')

Requirements:
    - requests library
    - Slack Webhook URL or Bot Token
"""

import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

import requests

from .base_connector import (
    BaseConnector,
    ConnectorResult,
    ConnectorConfigError,
    ConnectorAuthError,
    NotificationMixin
)


logger = logging.getLogger(__name__)


class SlackConnector(BaseConnector, NotificationMixin):
    """
    Slack notification connector.

    Supports:
    - Incoming Webhooks (simple notifications)
    - Bot API (rich messages, attachments, blocks)
    - File uploads
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Slack connector.

        Args:
            config: Configuration dictionary
                - enabled: Whether connector is enabled
                - webhook_url: Incoming webhook URL
                - bot_token: Bot user OAuth token (optional)
                - default_channel: Default channel for messages
        """
        self.webhook_url = config.get('webhook_url', '')
        self.bot_token = config.get('bot_token', '')
        self.default_channel = config.get('default_channel', '#ralf-notifications')

        # Bot API endpoint
        self.api_base = 'https://slack.com/api'

        super().__init__('slack', config)

    def _validate_config(self):
        """Validate Slack configuration."""
        if not self.webhook_url and not self.bot_token:
            raise ConnectorConfigError(
                "Slack connector requires either webhook_url or bot_token"
            )

        if self.webhook_url:
            # Validate webhook URL format
            parsed = urlparse(self.webhook_url)
            if not parsed.scheme or not parsed.netloc or 'hooks.slack.com' not in parsed.netloc:
                raise ConnectorConfigError(f"Invalid Slack webhook URL: {self.webhook_url}")

        if self.bot_token:
            # Validate bot token format
            if not self.bot_token.startswith('xoxb-'):
                raise ConnectorConfigError(f"Invalid Slack bot token: {self.bot_token}")

            # Setup bot token authentication
            self.session.headers.update({
                'Authorization': f'Bearer {self.bot_token}'
            })

        logger.info("Slack configuration validated")

    def _setup_session(self):
        """Setup HTTP session."""
        super()._setup_session()
        # Slack requires Content-Type for bot API
        if self.bot_token:
            self.session.headers.update({
                'Content-Type': 'application/json;charset=utf-8'
            })

    def send_notification(
        self,
        message: str,
        channel: Optional[str] = None,
        username: str = "RALF",
        icon_emoji: str = ":robot_face:",
        blocks: Optional[List[Dict[str, Any]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ConnectorResult:
        """
        Send notification to Slack.

        Args:
            message: Message text
            channel: Channel name (default: default_channel)
            username: Bot username
            icon_emoji: Bot icon emoji
            blocks: Structured message blocks (Slack Block Kit)
            attachments: Message attachments
            **kwargs: Additional parameters

        Returns:
            ConnectorResult with operation status
        """
        if not self.enabled:
            return ConnectorResult(
                success=False,
                message="Slack connector is disabled",
                error="Connector disabled"
            )

        try:
            # Use webhook if available (simpler)
            if self.webhook_url:
                return self._send_webhook(
                    message=message,
                    channel=channel or self.default_channel,
                    username=username,
                    icon_emoji=icon_emoji,
                    blocks=blocks,
                    attachments=attachments
                )

            # Fallback to bot API
            return self._send_bot_api(
                message=message,
                channel=channel or self.default_channel,
                blocks=blocks,
                attachments=attachments
            )

        except Exception as e:
            result = ConnectorResult(
                success=False,
                message="Failed to send Slack notification",
                error=str(e)
            )
            self._log_operation("send_notification", result)
            return result

    def _send_webhook(
        self,
        message: str,
        channel: str,
        username: str,
        icon_emoji: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> ConnectorResult:
        """
        Send notification via incoming webhook.

        Args:
            message: Message text
            channel: Channel name
            username: Bot username
            icon_emoji: Bot icon
            blocks: Message blocks
            attachments: Message attachments

        Returns:
            ConnectorResult
        """
        payload = {
            'text': message,
            'username': username,
            'icon_emoji': icon_emoji,
            'channel': channel
        }

        if blocks:
            payload['blocks'] = blocks

        if attachments:
            payload['attachments'] = attachments

        response = self._make_request(
            method='POST',
            url=self.webhook_url,
            json_data=payload,
            retry=False  # Webhooks don't support retry (idempotent)
        )

        if response.status_code == 200:
            result = ConnectorResult(
                success=True,
                message=f"Message sent to {channel}",
                data={'channel': channel}
            )
        else:
            result = ConnectorResult(
                success=False,
                message=f"Failed to send message to {channel}",
                error=response.text
            )

        self._log_operation("send_webhook", result)
        return result

    def _send_bot_api(
        self,
        message: str,
        channel: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> ConnectorResult:
        """
        Send notification via bot API.

        Args:
            message: Message text
            channel: Channel name
            blocks: Message blocks
            attachments: Message attachments

        Returns:
            ConnectorResult
        """
        payload = {
            'channel': channel,
            'text': message
        }

        if blocks:
            payload['blocks'] = blocks

        if attachments:
            payload['attachments'] = attachments

        response = self._make_request(
            method='POST',
            url=f'{self.api_base}/chat.postMessage',
            json_data=payload
        )

        data = response.json()

        if data.get('ok'):
            result = ConnectorResult(
                success=True,
                message=f"Message sent to {channel}",
                data={
                    'channel': channel,
                    'timestamp': data.get('ts'),
                    'message_id': data.get('ts')
                }
            )
        else:
            result = ConnectorResult(
                success=False,
                message=f"Failed to send message to {channel}",
                error=data.get('error', 'Unknown error')
            )

        self._log_operation("send_bot_api", result)
        return result

    def send_formatted_message(
        self,
        title: str,
        message: str,
        level: str = "info",
        channel: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConnectorResult:
        """
        Send formatted notification message.

        Args:
            title: Message title
            message: Message content
            level: Message level (info, warning, error, success)
            channel: Channel name
            metadata: Additional metadata

        Returns:
            ConnectorResult
        """
        formatted = self.format_message(title, message, level, metadata)
        return self.send_notification(formatted, channel=channel)

    def send_rich_message(
        self,
        title: str,
        fields: List[Dict[str, str]],
        color: str = "good",
        channel: Optional[str] = None
    ) -> ConnectorResult:
        """
        Send rich message with fields.

        Args:
            title: Attachment title
            fields: List of field dicts {'title': ..., 'value': ...}
            color: Attachment color (good, warning, danger, or hex code)
            channel: Channel name

        Returns:
            ConnectorResult
        """
        attachment = {
            'color': color,
            'title': title,
            'fields': fields,
            'footer': 'RALF Automation',
            'ts': int(time.time())
        }

        return self.send_notification(
            message=title,
            channel=channel,
            attachments=[attachment]
        )

    def upload_file(
        self,
        file_content: str,
        filename: str,
        title: Optional[str] = None,
        channels: Optional[List[str]] = None
    ) -> ConnectorResult:
        """
        Upload file to Slack.

        Args:
            file_content: File content
            filename: File name
            title: File title
            channels: List of channel IDs

        Returns:
            ConnectorResult
        """
        if not self.bot_token:
            return ConnectorResult(
                success=False,
                message="File upload requires bot token",
                error="Missing bot_token in configuration"
            )

        try:
            files = {
                'file': file_content
            }

            data = {
                'filename': filename,
                'channels': ','.join(channels or [self.default_channel])
            }

            if title:
                data['title'] = title

            response = self._make_request(
                method='POST',
                url=f'{self.api_base}/files.upload',
                files=files,
                data=data
            )

            result_data = response.json()

            if result_data.get('ok'):
                result = ConnectorResult(
                    success=True,
                    message=f"File uploaded: {filename}",
                    data={
                        'filename': filename,
                        'file_id': result_data.get('file', {}).get('id')
                    }
                )
            else:
                result = ConnectorResult(
                    success=False,
                    message=f"Failed to upload file: {filename}",
                    error=result_data.get('error', 'Unknown error')
                )

            self._log_operation("upload_file", result)
            return result

        except Exception as e:
            return ConnectorResult(
                success=False,
                message="Failed to upload file",
                error=str(e)
            )

    def test_connection(self) -> ConnectorResult:
        """Test Slack connection."""
        if not self.enabled:
            return ConnectorResult(
                success=False,
                message="Slack connector is disabled",
                error="Connector disabled"
            )

        try:
            # Send test message
            result = self.send_notification(
                message="RALF Slack connector test - Connection successful! :white_check_mark:",
                channel=self.default_channel
            )

            if result.success:
                result.message = "Slack connection test successful"

            return result

        except Exception as e:
            return ConnectorResult(
                success=False,
                message="Slack connection test failed",
                error=str(e)
            )
