"""
Webhook Receiver for RALF
Handles incoming webhooks from external services (Slack, Jira, Trello, etc.)
Part of Feature F-012 (API Gateway & External Service Integration)

Usage:
    from webhook_receiver import WebhookReceiver, WebhookValidator

    receiver = WebhookReceiver(config_file="~/.blackbox5/api-config.yaml")
    signature = request.headers.get('X-Webhook-Signature')
    payload = request.get_json()
    is_valid = receiver.validate_webhook('slack', payload, signature)

Requirements:
    - HMAC signature verification
    - Configuration file with webhook secret
"""

import logging
import hmac
import hashlib
import json
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timezone
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class WebhookError(Exception):
    """Base exception for webhook errors."""
    pass


class InvalidSignatureError(WebhookError):
    """Webhook signature verification failed."""
    pass


class ExpiredWebhookError(WebhookError):
    """Webhook payload too old."""
    pass


class WebhookValidator:
    """Validates webhook signatures and timestamps."""

    def __init__(self, secret: str, algorithm: str = 'sha256'):
        """
        Initialize webhook validator.

        Args:
            secret: Webhook secret for signature verification
            algorithm: Hash algorithm (default: sha256)
        """
        self.secret = secret
        self.algorithm = algorithm

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Raw payload bytes
            signature: Signature from request header (format: sha256=...)

        Returns:
            True if signature is valid

        Raises:
            InvalidSignatureError: If signature is invalid
        """
        # Parse signature (format: sha256=hex_digest)
        if not signature.startswith(f'{self.algorithm}='):
            raise InvalidSignatureError(f"Invalid signature format. Expected: {algorithm}=...")

        expected_signature = signature.split('=')[1]

        # Calculate expected signature
        mac = hmac.new(
            self.secret.encode(),
            payload,
            getattr(hashlib, self.algorithm)
        )
        calculated_signature = mac.hexdigest()

        # Compare signatures
        if not hmac.compare_digest(calculated_signature, expected_signature):
            raise InvalidSignatureError("Signature verification failed")

        return True

    def verify_timestamp(self, payload: Dict[str, Any], max_age_seconds: int = 300) -> bool:
        """
        Verify webhook timestamp is not too old.

        Args:
            payload: Parsed webhook payload
            max_age_seconds: Maximum age in seconds (default: 5 minutes)

        Returns:
            True if timestamp is valid

        Raises:
            ExpiredWebhookError: If timestamp is too old or missing
        """
        # Check for timestamp in payload
        timestamp = payload.get('timestamp') or payload.get('ts') or payload.get('event_time')

        if not timestamp:
            # Some services don't include timestamps
            logger.warning("No timestamp in webhook payload, skipping timestamp validation")
            return True

        try:
            # Parse timestamp (ISO 8601 or Unix timestamp)
            if isinstance(timestamp, (int, float)):
                webhook_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            else:
                webhook_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

            # Calculate age
            now = datetime.now(timezone.utc)
            age = (now - webhook_time).total_seconds()

            if age > max_age_seconds:
                raise ExpiredWebhookError(f"Webhook too old: {age} seconds")

            if age < -60:  # Allow 1 minute clock skew
                raise ExpiredWebhookError(f"Webhook timestamp in the future: {-age} seconds")

            return True

        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing webhook timestamp: {e}")
            raise ExpiredWebhookError(f"Invalid timestamp format: {timestamp}")


class WebhookReceiver:
    """
    Webhook Receiver Manager.

    Handles incoming webhooks from external services, validates signatures,
    and triggers RALF workflows.
    """

    def __init__(self, config_file: str = None):
        """
        Initialize webhook receiver.

        Args:
            config_file: Path to API configuration file
        """
        self.config_file = Path(config_file).expanduser() if config_file else None
        self.secret: Optional[str] = None
        self.algorithm = 'sha256'
        self.enabled_services: Dict[str, bool] = {}
        self.handlers: Dict[str, List[Callable]] = {}

        if self.config_file and self.config_file.exists():
            self._load_config()

    def _load_config(self):
        """Load webhook configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f) or {}

            # Load webhook config
            webhook_config = config.get('webhooks', {})
            self.secret = webhook_config.get('secret', '')
            self.algorithm = webhook_config.get('signature_algorithm', 'sha256')

            # Load enabled services
            services_config = webhook_config.get('services', {})
            for service_name, service_config in services_config.items():
                self.enabled_services[service_name] = service_config.get('enabled', False)

            logger.info(f"Loaded webhook config for {len(self.enabled_services)} services")

        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading webhook config: {e}")

    def validate_webhook(self, service: str, payload: bytes, signature: str) -> bool:
        """
        Validate incoming webhook.

        Args:
            service: Service name (slack, jira, trello, etc.)
            payload: Raw payload bytes
            signature: Signature from request header

        Returns:
            True if webhook is valid

        Raises:
            InvalidSignatureError: If signature is invalid
            ExpiredWebhookError: If timestamp is too old
        """
        if not self.secret:
            logger.warning("Webhook secret not configured")
            return False

        # Check if service is enabled
        if service not in self.enabled_services or not self.enabled_services[service]:
            logger.warning(f"Webhook service not enabled: {service}")
            return False

        # Create validator
        validator = WebhookValidator(self.secret, self.algorithm)

        # Verify signature
        validator.verify_signature(payload, signature)

        # Verify timestamp (if present)
        try:
            payload_dict = json.loads(payload.decode())
            validator.verify_timestamp(payload_dict)
        except json.JSONDecodeError:
            # Payload not JSON, skip timestamp validation
            pass

        return True

    def register_handler(self, service: str, event_type: str, handler: Callable):
        """
        Register webhook event handler.

        Args:
            service: Service name (slack, jira, trello, etc.)
            event_type: Event type (task.created, issue.updated, etc.)
            handler: Callback function(handler, payload) -> None
        """
        key = f"{service}.{event_type}"

        if key not in self.handlers:
            self.handlers[key] = []

        self.handlers[key].append(handler)
        logger.info(f"Registered handler for {key}")

    def handle_webhook(self, service: str, payload: Dict[str, Any]) -> List[Any]:
        """
        Handle incoming webhook by calling registered handlers.

        Args:
            service: Service name
            payload: Parsed webhook payload

        Returns:
            List of handler results
        """
        results = []

        # Get event type from payload
        event_type = payload.get('event') or payload.get('type') or payload.get('action', 'unknown')

        # Find handlers
        key = f"{service}.{event_type}"
        handlers = self.handlers.get(key, [])

        if not handlers:
            logger.warning(f"No handlers registered for {key}")
            return results

        # Call handlers
        for handler in handlers:
            try:
                result = handler(service, event_type, payload)
                results.append(result)
            except Exception as e:
                logger.error(f"Handler error for {key}: {e}")

        return results

    def parse_slack_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Slack webhook payload.

        Args:
            payload: Raw webhook payload

        Returns:
            Parsed Slack event
        """
        # Slack webhooks have different formats
        if 'challenge' in payload:
            # URL verification request
            return {
                'type': 'url_verification',
                'challenge': payload['challenge']
            }

        if 'event' in payload:
            # Event API
            event = payload['event']
            return {
                'type': 'event',
                'event_type': event.get('type'),
                'user': event.get('user'),
                'channel': event.get('channel'),
                'text': event.get('text'),
                'timestamp': event.get('ts'),
                'raw': payload
            }

        if 'command' in payload:
            # Slash command
            return {
                'type': 'command',
                'command': payload['command'],
                'user_name': payload.get('user_name'),
                'channel_id': payload.get('channel_id'),
                'text': payload.get('text'),
                'response_url': payload.get('response_url'),
                'raw': payload
            }

        return {'raw': payload}

    def parse_jira_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Jira webhook payload.

        Args:
            payload: Raw webhook payload

        Returns:
            Parsed Jira event
        """
        return {
            'type': 'webhook',
            'event_type': payload.get('webhookEvent'),
            'issue_key': payload.get('issue', {}).get('key'),
            'issue_id': payload.get('issue', {}).get('id'),
            'user': payload.get('user', {}).get('displayName'),
            'timestamp': payload.get('timestamp'),
            'raw': payload
        }

    def parse_trello_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Trello webhook payload.

        Args:
            payload: Raw webhook payload

        Returns:
            Parsed Trello event
        """
        return {
            'type': 'webhook',
            'action_type': payload.get('action', {}).get('type'),
            'model_type': payload.get('model', {}).get('type'),
            'card_id': payload.get('action', {}).get('data', {}).get('card', {}).get('id'),
            'board_id': payload.get('action', {}).get('data', {}).get('board', {}).get('id'),
            'timestamp': payload.get('action', {}).get('date'),
            'raw': payload
        }


# Flask Integration

def create_webhook_endpoint(receiver: WebhookReceiver):
    """
    Create Flask webhook endpoint.

    Usage:
        from flask import Flask, request

        app = Flask(__name__)
        receiver = WebhookReceiver(config_file="~/.blackbox5/api-config.yaml")

        @app.route('/api/v1/webhooks/<service>', methods=['POST'])
        def handle_webhook(service):
            return create_webhook_endpoint(receiver)(service)
    """
    from flask import request, jsonify

    def handler(service):
        try:
            # Get signature from header
            signature = request.headers.get('X-Webhook-Signature') or \
                        request.headers.get('X-Hub-Signature-256') or \
                        request.headers.get('X-Trello-Webhook')

            # Get raw payload
            payload_bytes = request.get_data()

            # Validate webhook
            if receiver.secret:
                if not signature:
                    logger.warning("Webhook received without signature")
                    return jsonify({
                        "error": "Unauthorized",
                        "message": "Missing signature"
                    }), 401

                receiver.validate_webhook(service, payload_bytes, signature)

            # Parse payload
            try:
                payload = request.get_json()
            except Exception:
                payload = {'raw': payload_bytes.decode()}

            # Handle webhook
            results = receiver.handle_webhook(service, payload)

            # Log webhook
            logger.info(f"Received webhook from {service}: {payload.get('event', 'unknown')}")

            # Return success
            return jsonify({
                "status": "success",
                "service": service,
                "handlers_called": len(results)
            }), 200

        except InvalidSignatureError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return jsonify({
                "error": "Unauthorized",
                "message": str(e)
            }), 401

        except ExpiredWebhookError as e:
            logger.error(f"Expired webhook: {e}")
            return jsonify({
                "error": "Forbidden",
                "message": str(e)
            }), 403

        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e)
            }), 500

    return handler
