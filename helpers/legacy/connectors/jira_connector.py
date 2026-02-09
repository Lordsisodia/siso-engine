"""
Jira Connector for RALF
Creates and manages Jira issues from RALF tasks
Part of Feature F-012 (API Gateway & External Service Integration)

Usage:
    from connectors.jira_connector import JiraConnector

    connector = JiraConnector(config={
        'enabled': True,
        'base_url': 'https://your-domain.atlassian.net',
        'email': 'your-email@example.com',
        'api_token': 'your-api-token',
        'project_key': 'RALF'
    })
    result = connector.create_issue('TASK-001', 'Implement feature', 'Description...')

Requirements:
    - requests library
    - Jira API token (https://id.atlassian.com/manage-profile/security/api-tokens)
"""

import logging
import base64
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
from datetime import datetime

import requests

from .base_connector import (
    BaseConnector,
    ConnectorResult,
    ConnectorConfigError,
    ConnectorAuthError
)


logger = logging.getLogger(__name__)


class JiraConnector(BaseConnector):
    """
    Jira integration connector.

    Supports:
    - Creating issues from RALF tasks
    - Updating issue status
    - Adding comments to issues
    - Syncing task progress
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Jira connector.

        Args:
            config: Configuration dictionary
                - enabled: Whether connector is enabled
                - base_url: Jira instance URL (e.g., https://your-domain.atlassian.net)
                - email: User email for authentication
                - api_token: Jira API token
                - project_key: Project key (e.g., RALF)
                - default_issue_type: Default issue type (Task, Bug, Story)
        """
        self.base_url = config.get('base_url', '').rstrip('/')
        self.email = config.get('email', '')
        self.api_token = config.get('api_token', '')
        self.project_key = config.get('project_key', 'RALF')
        self.default_issue_type = config.get('default_issue_type', 'Task')

        # Jira API endpoints
        self.api_base = f'{self.base_url}/rest/api/3'

        super().__init__('jira', config)

    def _validate_config(self):
        """Validate Jira configuration."""
        if not self.base_url:
            raise ConnectorConfigError("Jira connector requires base_url")

        if not self.email:
            raise ConnectorConfigError("Jira connector requires email")

        if not self.api_token:
            raise ConnectorConfigError("Jira connector requires api_token")

        if not self.project_key:
            raise ConnectorConfigError("Jira connector requires project_key")

        # Setup basic authentication
        auth_string = f"{self.email}:{self.api_token}"
        b64_auth = base64.b64encode(auth_string.encode()).decode()
        self.session.headers.update({
            'Authorization': f'Basic {b64_auth}',
            'Content-Type': 'application/json'
        })

        logger.info("Jira configuration validated")

    def send_notification(self, message: str, **kwargs) -> ConnectorResult:
        """
        Send notification (not applicable for Jira).

        Jira doesn't support direct notifications. Use create_issue instead.

        Args:
            message: Message content
            **kwargs: Additional parameters

        Returns:
            ConnectorResult indicating not supported
        """
        return ConnectorResult(
            success=False,
            message="Jira connector doesn't support direct notifications",
            error="Use create_issue() instead"
        )

    def create_issue(
        self,
        task_id: str,
        summary: str,
        description: str = "",
        issue_type: Optional[str] = None,
        priority: str = "Medium",
        labels: Optional[List[str]] = None,
        assignee: Optional[str] = None
    ) -> ConnectorResult:
        """
        Create Jira issue from RALF task.

        Args:
            task_id: RALF task ID (e.g., TASK-001)
            summary: Issue summary/title
            description: Issue description
            issue_type: Issue type (Task, Bug, Story, etc.)
            priority: Issue priority
            labels: Issue labels
            assignee: Assignee account ID

        Returns:
            ConnectorResult with issue details
        """
        if not self.enabled:
            return ConnectorResult(
                success=False,
                message="Jira connector is disabled",
                error="Connector disabled"
            )

        try:
            # Build issue payload
            payload = {
                'fields': {
                    'project': {'key': self.project_key},
                    'summary': f"[{task_id}] {summary}",
                    'description': {
                        'type': 'doc',
                        'version': 1,
                        'content': [
                            {
                                'type': 'paragraph',
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': description
                                    }
                                ]
                            }
                        ]
                    },
                    'issuetype': {'name': issue_type or self.default_issue_type},
                    'priority': {'name': priority}
                }
            }

            # Add labels if provided
            if labels:
                payload['fields']['labels'] = labels + [task_id]

            # Add assignee if provided
            if assignee:
                payload['fields']['assignee'] = {'accountId': assignee}

            # Create issue
            response = self._make_request(
                method='POST',
                url=f'{self.api_base}/issue',
                json_data=payload
            )

            data = response.json()

            result = ConnectorResult(
                success=True,
                message=f"Issue created: {data.get('key')}",
                data={
                    'issue_key': data.get('key'),
                    'issue_id': data.get('id'),
                    'task_id': task_id,
                    'url': f'{self.base_url}/browse/{data.get("key")}'
                }
            )

            self._log_operation("create_issue", result)
            return result

        except Exception as e:
            result = ConnectorResult(
                success=False,
                message=f"Failed to create issue for {task_id}",
                error=str(e)
            )
            self._log_operation("create_issue", result)
            return result

    def update_issue_status(
        self,
        issue_key: str,
        status: str,
        transition_name: Optional[str] = None
    ) -> ConnectorResult:
        """
        Update issue status.

        Args:
            issue_key: Jira issue key (e.g., RALF-123)
            status: New status (To Do, In Progress, Done, etc.)
            transition_name: Transition name (if different from status)

        Returns:
            ConnectorResult
        """
        if not self.enabled:
            return ConnectorResult(
                success=False,
                message="Jira connector is disabled",
                error="Connector disabled"
            )

        try:
            # Get available transitions
            response = self._make_request(
                method='GET',
                url=f'{self.api_base}/issue/{issue_key}/transitions'
            )

            data = response.json()
            transitions = data.get('transitions', [])

            # Find matching transition
            transition_id = None
            target_name = transition_name or status

            for transition in transitions:
                if transition.get('to', {}).get('name') == target_name:
                    transition_id = transition.get('id')
                    break

            if not transition_id:
                return ConnectorResult(
                    success=False,
                    message=f"Transition not found: {target_name}",
                    error=f"Available transitions: {[t['name'] for t in transitions]}"
                )

            # Execute transition
            payload = {
                'transition': {'id': transition_id}
            }

            self._make_request(
                method='POST',
                url=f'{self.api_base}/issue/{issue_key}/transitions',
                json_data=payload
            )

            result = ConnectorResult(
                success=True,
                message=f"Issue {issue_key} status updated to {status}",
                data={
                    'issue_key': issue_key,
                    'status': status
                }
            )

            self._log_operation("update_issue_status", result)
            return result

        except Exception as e:
            result = ConnectorResult(
                success=False,
                message=f"Failed to update issue {issue_key}",
                error=str(e)
            )
            self._log_operation("update_issue_status", result)
            return result

    def add_comment(
        self,
        issue_key: str,
        comment: str,
        public: bool = True
    ) -> ConnectorResult:
        """
        Add comment to issue.

        Args:
            issue_key: Jira issue key
            comment: Comment text
            public: Whether comment is public (internal=false) or private (internal=true)

        Returns:
            ConnectorResult
        """
        if not self.enabled:
            return ConnectorResult(
                success=False,
                message="Jira connector is disabled",
                error="Connector disabled"
            )

        try:
            payload = {
                'body': {
                    'type': 'doc',
                    'version': 1,
                    'content': [
                        {
                            'type': 'paragraph',
                            'content': [
                                {
                                    'type': 'text',
                                    'text': comment
                                }
                            ]
                        }
                    ]
                },
                'properties': [
                    {
                        'key': 'sd.public.comment',
                        'value': {'internal': not public}
                    }
                ]
            }

            response = self._make_request(
                method='POST',
                url=f'{self.api_base}/issue/{issue_key}/comment',
                json_data=payload
            )

            data = response.json()

            result = ConnectorResult(
                success=True,
                message=f"Comment added to {issue_key}",
                data={
                    'issue_key': issue_key,
                    'comment_id': data.get('id'),
                    'public': public
                }
            )

            self._log_operation("add_comment", result)
            return result

        except Exception as e:
            result = ConnectorResult(
                success=False,
                message=f"Failed to add comment to {issue_key}",
                error=str(e)
            )
            self._log_operation("add_comment", result)
            return result

    def get_issue(self, issue_key: str) -> ConnectorResult:
        """
        Get issue details.

        Args:
            issue_key: Jira issue key

        Returns:
            ConnectorResult with issue details
        """
        if not self.enabled:
            return ConnectorResult(
                success=False,
                message="Jira connector is disabled",
                error="Connector disabled"
            )

        try:
            response = self._make_request(
                method='GET',
                url=f'{self.api_base}/issue/{issue_key}'
            )

            data = response.json()

            # Extract relevant fields
            fields = data.get('fields', {})

            result = ConnectorResult(
                success=True,
                message=f"Issue retrieved: {issue_key}",
                data={
                    'key': data.get('key'),
                    'id': data.get('id'),
                    'summary': fields.get('summary'),
                    'status': fields.get('status', {}).get('name'),
                    'priority': fields.get('priority', {}).get('name'),
                    'issue_type': fields.get('issuetype', {}).get('name'),
                    'assignee': fields.get('assignee', {}).get('displayName'),
                    'created': fields.get('created'),
                    'updated': fields.get('updated')
                }
            )

            return result

        except Exception as e:
            return ConnectorResult(
                success=False,
                message=f"Failed to get issue {issue_key}",
                error=str(e)
            )

    def search_issues(self, jql: str, max_results: int = 50) -> ConnectorResult:
        """
        Search issues using JQL.

        Args:
            jql: JQL query string
            max_results: Maximum results to return

        Returns:
            ConnectorResult with issue list
        """
        if not self.enabled:
            return ConnectorResult(
                success=False,
                message="Jira connector is disabled",
                error="Connector disabled"
            )

        try:
            payload = {
                'jql': jql,
                'maxResults': max_results,
                'fields': ['key', 'summary', 'status', 'priority', 'issuetype', 'assignee', 'created', 'updated']
            }

            response = self._make_request(
                method='POST',
                url=f'{self.api_base}/search',
                json_data=payload
            )

            data = response.json()

            issues = [
                {
                    'key': issue.get('key'),
                    'summary': issue.get('fields', {}).get('summary'),
                    'status': issue.get('fields', {}).get('status', {}).get('name'),
                    'priority': issue.get('fields', {}).get('priority', {}).get('name')
                }
                for issue in data.get('issues', [])
            ]

            result = ConnectorResult(
                success=True,
                message=f"Found {len(issues)} issues",
                data={
                    'issues': issues,
                    'total': data.get('total'),
                    'jql': jql
                }
            )

            return result

        except Exception as e:
            return ConnectorResult(
                success=False,
                message=f"Failed to search issues",
                error=str(e)
            )

    def test_connection(self) -> ConnectorResult:
        """Test Jira connection."""
        if not self.enabled:
            return ConnectorResult(
                success=False,
                message="Jira connector is disabled",
                error="Connector disabled"
            )

        try:
            # Try to get current user
            response = self._make_request(
                method='GET',
                url=f'{self.api_base}/myself'
            )

            data = response.json()

            result = ConnectorResult(
                success=True,
                message=f"Jira connection successful (user: {data.get('displayName')})",
                data={
                    'email': data.get('emailAddress'),
                    'display_name': data.get('displayName')
                }
            )

            return result

        except Exception as e:
            return ConnectorResult(
                success=False,
                message="Jira connection test failed",
                error=str(e)
            )
