"""
RALF Service Connectors
External service integration connectors (Slack, Jira, Trello, etc.)
Part of Feature F-012 (API Gateway & External Service Integration)
"""

from .base_connector import (
    BaseConnector,
    ConnectorResult,
    ConnectorError,
    ConnectorConfigError,
    ConnectorAuthError,
    ConnectorAPIError,
    NotificationMixin,
    WebhookMixin
)

from .slack_connector import SlackConnector
from .jira_connector import JiraConnector
from .trello_connector import TrelloConnector

__all__ = [
    # Base classes
    'BaseConnector',
    'ConnectorResult',
    'ConnectorError',
    'ConnectorConfigError',
    'ConnectorAuthError',
    'ConnectorAPIError',
    'NotificationMixin',
    'WebhookMixin',

    # Connectors
    'SlackConnector',
    'JiraConnector',
    'TrelloConnector'
]
