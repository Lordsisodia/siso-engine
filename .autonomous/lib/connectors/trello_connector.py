"""
Trello Connector for RALF
Creates and manages Trello cards from RALF tasks
Part of Feature F-012 (API Gateway & External Service Integration)

Usage:
    from connectors.trello_connector import TrelloConnector

    connector = TrelloConnector(config={
        'enabled': True,
        'api_key': 'your-api-key',
        'api_secret': 'your-api-secret',
        'token': 'your-token',
        'default_board': 'My Board',
        'default_list': 'To Do'
    })
    result = connector.create_card('TASK-001', 'Implement feature', 'Description...')

Requirements:
    - requests library
    - Trello API key and token (https://trello.com/app-key)
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import requests

from .base_connector import (
    BaseConnector,
    ConnectorResult,
    ConnectorConfigError,
    NotificationMixin
)


logger = logging.getLogger(__name__)


class TrelloConnector(BaseConnector, NotificationMixin):
    """
    Trello integration connector.

    Supports:
    - Creating cards from RALF tasks
    - Updating card status
    - Adding comments to cards
    - Moving cards between lists
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Trello connector.

        Args:
            config: Configuration dictionary
                - enabled: Whether connector is enabled
                - api_key: Trello API key
                - api_secret: Trello API secret
                - token: Trello OAuth token
                - default_board: Default board name
                - default_list: Default list name
        """
        self.api_key = config.get('api_key', '')
        self.api_secret = config.get('api_secret', '')
        self.token = config.get('token', '')
        self.default_board = config.get('default_board', 'RALF Tasks')
        self.default_list = config.get('default_list', 'To Do')

        # Trello API endpoints
        self.api_base = 'https://api.trello.com/1'

        # Cache for board and list IDs
        self._board_id: Optional[str] = None
        self._list_ids: Dict[str, str] = {}

        super().__init__('trello', config)

    def _validate_config(self):
        """Validate Trello configuration."""
        if not self.api_key:
            raise ConnectorConfigError("Trello connector requires api_key")

        if not self.token:
            raise ConnectorConfigError("Trello connector requires token")

        # Add API key and token to all requests
        self.session.params.update({
            'key': self.api_key,
            'token': self.token
        })

        logger.info("Trello configuration validated")

    def send_notification(self, message: str, **kwargs) -> ConnectorResult:
        """
        Send notification (not applicable for Trello).

        Trello doesn't support direct notifications. Use create_card instead.

        Args:
            message: Message content
            **kwargs: Additional parameters

        Returns:
            ConnectorResult indicating not supported
        """
        return ConnectorResult(
            success=False,
            message="Trello connector doesn't support direct notifications",
            error="Use create_card() instead"
        )

    def _get_board_id(self, board_name: Optional[str] = None) -> Optional[str]:
        """
        Get board ID by name.

        Args:
            board_name: Board name (default: default_board)

        Returns:
            Board ID or None if not found
        """
        board_name = board_name or self.default_board

        try:
            response = self._make_request(
                method='GET',
                url=f'{self.api_base}/members/me/boards',
                params={'filter': 'open'}
            )

            boards = response.json()

            for board in boards:
                if board.get('name') == board_name:
                    board_id = board.get('id')
                    logger.debug(f"Found board '{board_name}': {board_id}")
                    return board_id

            logger.warning(f"Board not found: {board_name}")
            return None

        except Exception as e:
            logger.error(f"Error getting board ID: {e}")
            return None

    def _get_list_id(self, list_name: Optional[str] = None, board_id: Optional[str] = None) -> Optional[str]:
        """
        Get list ID by name.

        Args:
            list_name: List name (default: default_list)
            board_id: Board ID (default: cached board ID)

        Returns:
            List ID or None if not found
        """
        list_name = list_name or self.default_list
        board_id = board_id or self._board_id

        if not board_id:
            board_id = self._get_board_id()
            if board_id:
                self._board_id = board_id
            else:
                return None

        # Check cache
        cache_key = f"{board_id}:{list_name}"
        if cache_key in self._list_ids:
            return self._list_ids[cache_key]

        try:
            response = self._make_request(
                method='GET',
                url=f'{self.api_base}/boards/{board_id}/lists',
                params={'filter': 'open'}
            )

            lists = response.json()

            for trello_list in lists:
                if trello_list.get('name') == list_name:
                    list_id = trello_list.get('id')
                    self._list_ids[cache_key] = list_id
                    logger.debug(f"Found list '{list_name}': {list_id}")
                    return list_id

            logger.warning(f"List not found: {list_name}")
            return None

        except Exception as e:
            logger.error(f"Error getting list ID: {e}")
            return None

    def create_card(
        self,
        task_id: str,
        name: str,
        description: str = "",
        list_name: Optional[str] = None,
        board_name: Optional[str] = None,
        labels: Optional[List[str]] = None,
        due_date: Optional[str] = None
    ) -> ConnectorResult:
        """
        Create Trello card from RALF task.

        Args:
            task_id: RALF task ID (e.g., TASK-001)
            name: Card name
            description: Card description
            list_name: List name (default: default_list)
            board_name: Board name (default: default_board)
            labels: Card labels
            due_date: Due date (ISO 8601 format)

        Returns:
            ConnectorResult with card details
        """
        if not self.enabled:
            return ConnectorResult(
                success=False,
                message="Trello connector is disabled",
                error="Connector disabled"
            )

        try:
            # Get list ID
            list_id = self._get_list_id(list_name, self._get_board_id(board_name))

            if not list_id:
                return ConnectorResult(
                    success=False,
                    message=f"List not found: {list_name or self.default_list}",
                    error="List not found"
                )

            # Build card payload
            payload = {
                'name': f"[{task_id}] {name}",
                'desc': description,
                'idList': list_id
            }

            if due_date:
                payload['due'] = due_date

            # Create card
            response = self._make_request(
                method='POST',
                url=f'{self.api_base}/cards',
                params=payload
            )

            data = response.json()

            # Add labels if provided
            if labels:
                self._add_labels_to_card(data.get('id'), labels)

            result = ConnectorResult(
                success=True,
                message=f"Card created: {data.get('name')}",
                data={
                    'card_id': data.get('id'),
                    'card_name': data.get('name'),
                    'task_id': task_id,
                    'url': data.get('url'),
                    'list_id': list_id
                }
            )

            self._log_operation("create_card", result)
            return result

        except Exception as e:
            result = ConnectorResult(
                success=False,
                message=f"Failed to create card for {task_id}",
                error=str(e)
            )
            self._log_operation("create_card", result)
            return result

    def update_card_status(
        self,
        card_id: str,
        list_name: str,
        board_name: Optional[str] = None
    ) -> ConnectorResult:
        """
        Move card to different list.

        Args:
            card_id: Trello card ID
            list_name: Target list name
            board_name: Board name (default: default_board)

        Returns:
            ConnectorResult
        """
        if not self.enabled:
            return ConnectorResult(
                success=False,
                message="Trello connector is disabled",
                error="Connector disabled"
            )

        try:
            # Get target list ID
            list_id = self._get_list_id(list_name, self._get_board_id(board_name))

            if not list_id:
                return ConnectorResult(
                    success=False,
                    message=f"List not found: {list_name}",
                    error="List not found"
                )

            # Move card
            self._make_request(
                method='PUT',
                url=f'{self.api_base}/cards/{card_id}',
                params={'idList': list_id}
            )

            result = ConnectorResult(
                success=True,
                message=f"Card {card_id} moved to {list_name}",
                data={
                    'card_id': card_id,
                    'list_name': list_name,
                    'list_id': list_id
                }
            )

            self._log_operation("update_card_status", result)
            return result

        except Exception as e:
            result = ConnectorResult(
                success=False,
                message=f"Failed to move card {card_id}",
                error=str(e)
            )
            self._log_operation("update_card_status", result)
            return result

    def add_comment(
        self,
        card_id: str,
        comment: str
    ) -> ConnectorResult:
        """
        Add comment to card.

        Args:
            card_id: Trello card ID
            comment: Comment text

        Returns:
            ConnectorResult
        """
        if not self.enabled:
            return ConnectorResult(
                success=False,
                message="Trello connector is disabled",
                error="Connector disabled"
            )

        try:
            payload = {
                'text': comment
            }

            response = self._make_request(
                method='POST',
                url=f'{self.api_base}/cards/{card_id}/actions/comments',
                params=payload
            )

            data = response.json()

            result = ConnectorResult(
                success=True,
                message=f"Comment added to card {card_id}",
                data={
                    'card_id': card_id,
                    'comment_id': data.get('id')
                }
            )

            self._log_operation("add_comment", result)
            return result

        except Exception as e:
            result = ConnectorResult(
                success=False,
                message=f"Failed to add comment to card {card_id}",
                error=str(e)
            )
            self._log_operation("add_comment", result)
            return result

    def _add_labels_to_card(self, card_id: str, labels: List[str]) -> bool:
        """
        Add labels to card.

        Args:
            card_id: Trello card ID
            labels: List of label names

        Returns:
            True if successful
        """
        try:
            for label_name in labels:
                # Try to find existing label or create new one
                # Note: Trello API requires label color, we'll use 'blue' as default
                payload = {
                    'name': label_name,
                    'color': 'blue'
                }

                self._make_request(
                    method='POST',
                    url=f'{self.api_base}/cards/{card_id}/labels',
                    params=payload
                )

            return True

        except Exception as e:
            logger.error(f"Error adding labels: {e}")
            return False

    def get_card(self, card_id: str) -> ConnectorResult:
        """
        Get card details.

        Args:
            card_id: Trello card ID

        Returns:
            ConnectorResult with card details
        """
        if not self.enabled:
            return ConnectorResult(
                success=False,
                message="Trello connector is disabled",
                error="Connector disabled"
            )

        try:
            response = self._make_request(
                method='GET',
                url=f'{self.api_base}/cards/{card_id}',
                params={'fields': 'all,list'}
            )

            data = response.json()

            result = ConnectorResult(
                success=True,
                message=f"Card retrieved: {data.get('name')}",
                data={
                    'id': data.get('id'),
                    'name': data.get('name'),
                    'desc': data.get('desc'),
                    'closed': data.get('closed'),
                    'due': data.get('due'),
                    'list_id': data.get('idList'),
                    'url': data.get('url')
                }
            )

            return result

        except Exception as e:
            return ConnectorResult(
                success=False,
                message=f"Failed to get card {card_id}",
                error=str(e)
            )

    def test_connection(self) -> ConnectorResult:
        """Test Trello connection."""
        if not self.enabled:
            return ConnectorResult(
                success=False,
                message="Trello connector is disabled",
                error="Connector disabled"
            )

        try:
            # Try to get boards
            response = self._make_request(
                method='GET',
                url=f'{self.api_base}/members/me/boards',
                params={'filter': 'open', 'fields': 'name'}
            )

            boards = response.json()

            result = ConnectorResult(
                success=True,
                message=f"Trello connection successful ({len(boards)} boards found)",
                data={
                    'board_count': len(boards),
                    'boards': [b.get('name') for b in boards[:5]]
                }
            )

            return result

        except Exception as e:
            return ConnectorResult(
                success=False,
                message="Trello connection test failed",
                error=str(e)
            )
