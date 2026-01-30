"""
Notification Handler for Agent Output Bus

Receives agent outputs and sends notifications based on status.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable

# Import from parent directory
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from AgentOutputBus import OutputHandler, HandlerResult, OutputEvent, OutputStatus

logger = logging.getLogger(__name__)


class NotificationHandler(OutputHandler):
    """
    Handler for sending notifications based on agent outputs.

    Sends notifications for:
    - Failed tasks (alert)
    - Partial success (warning)
    - Success with next steps (info)
    """

    def __init__(
        self,
        notify_on_failure: bool = True,
        notify_on_partial: bool = True,
        notify_on_success: bool = False,
        custom_callbacks: Optional[Dict[str, Callable]] = None
    ):
        """
        Initialize notification handler.

        Args:
            notify_on_failure: Send notifications on failed status
            notify_on_partial: Send notifications on partial status
            notify_on_success: Send notifications on success status
            custom_callbacks: Dict of status -> callback functions
        """
        super().__init__("NotificationHandler")

        self.notify_on_failure = notify_on_failure
        self.notify_on_partial = notify_on_partial
        self.notify_on_success = notify_on_success
        self.custom_callbacks = custom_callbacks or {}

    def handle(self, event: OutputEvent) -> HandlerResult:
        """
        Handle agent output event by sending notifications.

        Args:
            event: Parsed agent output event

        Returns:
            HandlerResult with notification status
        """
        try:
            notifications_sent = []

            # Check if we should notify
            should_notify = (
                (event.is_failed and self.notify_on_failure) or
                (event.is_partial and self.notify_on_partial) or
                (event.is_success and self.notify_on_success)
            )

            if not should_notify:
                return HandlerResult(
                    success=True,
                    message="Notification suppressed by configuration",
                    data={"notifications_sent": []}
                )

            # Run custom callback if registered
            status_key = event.status.value
            if status_key in self.custom_callbacks:
                callback = self.custom_callbacks[status_key]
                try:
                    result = callback(event)
                    notifications_sent.append({
                        "type": "custom_callback",
                        "status": status_key,
                        "result": result
                    })
                except Exception as e:
                    logger.error(f"Custom callback failed: {e}")

            # Built-in notification methods
            if event.is_failed:
                self._notify_failure(event)
                notifications_sent.append({
                    "type": "failure_alert",
                    "message": f"Agent {event.agent_name} failed: {event.summary}"
                })

            elif event.is_partial:
                self._notify_partial(event)
                notifications_sent.append({
                    "type": "partial_warning",
                    "message": f"Agent {event.agent_name} partial: {event.summary}"
                })

            elif event.is_success and event.next_steps:
                self._notify_next_steps(event)
                notifications_sent.append({
                    "type": "next_steps_info",
                    "message": f"Agent {event.agent_name} has {len(event.next_steps)} next steps"
                })

            data = {
                "notifications_sent": notifications_sent,
                "status": event.status.value
            }

            return HandlerResult(
                success=True,
                message=f"Sent {len(notifications_sent)} notification(s)",
                data=data
            )

        except Exception as e:
            logger.error(f"NotificationHandler error: {e}")
            return HandlerResult(
                success=False,
                message=f"Failed to send notifications: {e}",
                data=None
            )

    def _notify_failure(self, event: OutputEvent) -> None:
        """Send failure notification."""
        emoji = "❌"
        logger.error(f"{emoji} Agent {event.agent_name} FAILED: {event.summary}")
        if event.metadata.get('error'):
            logger.error(f"   Error: {event.metadata['error']}")

    def _notify_partial(self, event: OutputEvent) -> None:
        """Send partial success notification."""
        emoji = "⚠️"
        logger.warning(f"{emoji} Agent {event.agent_name} PARTIAL: {event.summary}")
        if event.next_steps:
            logger.warning(f"   Next steps: {', '.join(event.next_steps[:3])}")

    def _notify_next_steps(self, event: OutputEvent) -> None:
        """Send info about next steps."""
        emoji = "→"
        logger.info(f"{emoji} Agent {event.agent_name} has {len(event.next_steps)} next steps")
        for i, step in enumerate(event.next_steps[:3], 1):
            logger.info(f"   {i}. {step}")
        if len(event.next_steps) > 3:
            logger.info(f"   ... and {len(event.next_steps) - 3} more")

    def register_callback(self, status: str, callback: Callable) -> None:
        """
        Register a custom callback for a status.

        Args:
            status: Status key (success, partial, failed)
            callback: Function that receives OutputEvent
        """
        self.custom_callbacks[status] = callback
        logger.info(f"Registered callback for status: {status}")


class SlackNotificationHandler(NotificationHandler):
    """
    Extended notification handler that sends messages to Slack.
    """

    def __init__(
        self,
        slack_webhook_url: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Slack notification handler.

        Args:
            slack_webhook_url: Slack webhook URL for sending messages
            **kwargs: Passed to parent NotificationHandler
        """
        super().__init__(**kwargs)
        self.slack_webhook_url = slack_webhook_url

    def _send_slack_message(self, text: str, color: str = "good") -> None:
        """Send message to Slack webhook."""
        if not self.slack_webhook_url:
            logger.debug("Slack webhook not configured, skipping")
            return

        try:
            import requests

            payload = {
                "attachments": [
                    {
                        "color": color,
                        "text": text
                    }
                ]
            }

            response = requests.post(self.slack_webhook_url, json=payload)
            response.raise_for_status()

            logger.info("Slack notification sent")

        except ImportError:
            logger.warning("requests not installed, cannot send Slack notifications")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    def _notify_failure(self, event: OutputEvent) -> None:
        """Send failure notification to Slack."""
        super()._notify_failure(event)
        text = f"❌ *Agent {event.agent_name} FAILED*\n> {event.summary}"
        self._send_slack_message(text, color="danger")

    def _notify_partial(self, event: OutputEvent) -> None:
        """Send partial notification to Slack."""
        super()._notify_partial(event)
        text = f"⚠️ *Agent {event.agent_name} PARTIAL*\n> {event.summary}"
        self._send_slack_message(text, color="warning")

    def _notify_next_steps(self, event: OutputEvent) -> None:
        """Send next steps notification to Slack."""
        super()._notify_next_steps(event)
        steps_text = "\n".join(f"• {step}" for step in event.next_steps[:5])
        text = f"→ *Agent {event.agent_name}* completed\n> {event.summary}\n\n{steps_text}"
        self._send_slack_message(text, color="good")


def create_notification_handler(
    slack_webhook_url: Optional[str] = None,
    **kwargs
) -> NotificationHandler:
    """
    Convenience function to create notification handler.

    Args:
        slack_webhook_url: If provided, returns SlackNotificationHandler
        **kwargs: Passed to handler constructor
    """
    if slack_webhook_url:
        return SlackNotificationHandler(
            slack_webhook_url=slack_webhook_url,
            **kwargs
    )
    return NotificationHandler(**kwargs)
