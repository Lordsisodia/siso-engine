#!/usr/bin/env python3
"""
RALF API Gateway Server
REST API for RALF system with authentication, rate limiting, and service connectors
Part of Feature F-012 (API Gateway & External Service Integration)

Usage:
    from api_server import create_app

    app = create_app(config_file="~/.blackbox5/api-config.yaml")
    app.run(host="0.0.0.0", port=5000)

    Or run directly:
    python -m 2_engine.autonomous.lib.api_server

Requirements:
    - Flask (web framework)
    - Configuration file with API keys and connector settings
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from flask import Flask, jsonify, request, g
from flask_cors import CORS

# Add engine lib to path
engine_lib = Path(__file__).parent.parent
if str(engine_lib) not in sys.path:
    sys.path.insert(0, str(engine_lib))

from api_auth import APIAuth, require_api_key, require_scope, add_security_headers
from webhook_receiver import WebhookReceiver, create_webhook_endpoint
from connectors import SlackConnector, JiraConnector, TrelloConnector


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
API_VERSION = "1.0.0"


class RalfAPIGateway:
    """
    RALF API Gateway Server.

    Provides REST API for RALF system with:
    - Authentication (API keys)
    - Rate limiting
    - Task management endpoints
    - Queue status endpoints
    - Metrics endpoints
    - Webhook receiver
    - Service connectors
    """

    def __init__(self, config_file: str = None):
        """
        Initialize API Gateway.

        Args:
            config_file: Path to API configuration file
        """
        self.config_file = Path(config_file).expanduser() if config_file else None

        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['JSON_SORT_KEYS'] = False

        # Load configuration
        self.config = self._load_config()

        # Setup CORS
        self._setup_cors()

        # Initialize authentication
        self.auth = APIAuth(str(self.config_file) if self.config_file else None)

        # Initialize webhook receiver
        self.webhook_receiver = WebhookReceiver(str(self.config_file) if self.config_file else None)

        # Initialize service connectors
        self.connectors: Dict[str, Any] = {}
        self._init_connectors()

        # Register routes
        self._register_routes()

        # Register error handlers
        self._register_error_handlers()

        # Register middleware
        self._register_middleware()

        logger.info("RALF API Gateway initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        import yaml

        if not self.config_file or not self.config_file.exists():
            logger.warning(f"Config file not found: {self.config_file}")
            return {}

        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def _setup_cors(self):
        """Setup CORS based on configuration."""
        server_config = self.config.get('server', {})
        cors_enabled = server_config.get('cors_enabled', True)

        if cors_enabled:
            cors_origins = server_config.get('cors_origins', ['*'])
            CORS(self.app, origins=cors_origins)
            logger.info(f"CORS enabled for origins: {cors_origins}")

    def _init_connectors(self):
        """Initialize service connectors."""
        connectors_config = self.config.get('connectors', {})

        # Slack connector
        slack_config = connectors_config.get('slack', {})
        if slack_config.get('enabled', False):
            try:
                self.connectors['slack'] = SlackConnector(slack_config)
                logger.info("Slack connector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Slack connector: {e}")

        # Jira connector
        jira_config = connectors_config.get('jira', {})
        if jira_config.get('enabled', False):
            try:
                self.connectors['jira'] = JiraConnector(jira_config)
                logger.info("Jira connector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Jira connector: {e}")

        # Trello connector
        trello_config = connectors_config.get('trello', {})
        if trello_config.get('enabled', False):
            try:
                self.connectors['trello'] = TrelloConnector(trello_config)
                logger.info("Trello connector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Trello connector: {e}")

        logger.info(f"Initialized {len(self.connectors)} service connectors")

    def _register_middleware(self):
        """Register request middleware."""

        @self.app.before_request
        def log_request():
            """Log API requests."""
            if not request.path.startswith('/health'):
                api_key = getattr(g, 'api_key', None)
                key_name = api_key.name if api_key else 'anonymous'
                logger.info(f"{request.method} {request.path} - Key: {key_name} - IP: {request.remote_addr}")

        @self.app.after_request
        def add_headers(response):
            """Add security headers."""
            return add_security_headers(response)

    def _register_error_handlers(self):
        """Register error handlers."""

        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                "error": "Not Found",
                "message": f"Endpoint not found: {request.path}",
                "path": request.path
            }), 404

        @self.app.errorhandler(405)
        def method_not_allowed(error):
            return jsonify({
                "error": "Method Not Allowed",
                "message": f"Method {request.method} not allowed for {request.path}",
                "path": request.path,
                "method": request.method
            }), 405

        @self.app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Internal server error: {error}")
            return jsonify({
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }), 500

    def _register_routes(self):
        """Register API routes."""

        # ========================================================================
        # Health Check
        # ========================================================================

        @self.app.route('/health')
        def health_check():
            """Health check endpoint (no auth required)."""
            return jsonify({
                "status": "healthy",
                "version": API_VERSION,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "connectors": {
                    name: conn.get_status()
                    for name, conn in self.connectors.items()
                }
            }), 200

        # ========================================================================
        # Task Endpoints
        # ========================================================================

        @self.app.route('/api/v1/tasks', methods=['GET'])
        @require_api_key(self.auth)
        def get_tasks():
            """Get all tasks."""
            # This is a placeholder - in real implementation, would read from task files
            return jsonify({
                "tasks": [],
                "total": 0,
                "message": "Task management not fully implemented"
            }), 200

        @self.app.route('/api/v1/tasks/<task_id>', methods=['GET'])
        @require_api_key(self.auth)
        def get_task(task_id):
            """Get task by ID."""
            # Placeholder implementation
            return jsonify({
                "error": "Not Implemented",
                "message": f"Task details for {task_id} not implemented"
            }), 501

        @self.app.route('/api/v1/tasks', methods=['POST'])
        @require_api_key(self.auth)
        @require_scope(self.auth, "write:tasks")
        def create_task():
            """Create new task."""
            # Placeholder implementation
            return jsonify({
                "error": "Not Implemented",
                "message": "Task creation not implemented"
            }), 501

        @self.app.route('/api/v1/tasks/<task_id>', methods=['PUT'])
        @require_api_key(self.auth)
        @require_scope(self.auth, "write:tasks")
        def update_task(task_id):
            """Update task."""
            # Placeholder implementation
            return jsonify({
                "error": "Not Implemented",
                "message": f"Task update for {task_id} not implemented"
            }), 501

        # ========================================================================
        # Queue Endpoints
        # ========================================================================

        @self.app.route('/api/v1/queue', methods=['GET'])
        @require_api_key(self.auth)
        def get_queue():
            """Get queue status."""
            # Placeholder - would read from queue.yaml
            return jsonify({
                "depth": 0,
                "tasks": [],
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "message": "Queue management not fully implemented"
            }), 200

        # ========================================================================
        # Metrics Endpoints
        # ========================================================================

        @self.app.route('/api/v1/metrics', methods=['GET'])
        @require_api_key(self.auth)
        def get_metrics():
            """Get system metrics."""
            # Placeholder implementation
            return jsonify({
                "tasks_completed": 0,
                "success_rate": 0.0,
                "average_duration": 0,
                "uptime": "unknown",
                "message": "Metrics not fully implemented"
            }), 200

        # ========================================================================
        # Connector Endpoints
        # ========================================================================

        @self.app.route('/api/v1/connectors', methods=['GET'])
        @require_api_key(self.auth)
        def list_connectors():
            """List all service connectors."""
            connectors = {
                name: conn.get_status()
                for name, conn in self.connectors.items()
            }

            return jsonify({
                "connectors": connectors,
                "total": len(self.connectors)
            }), 200

        @self.app.route('/api/v1/connectors/<connector_name>/test', methods=['POST'])
        @require_api_key(self.auth)
        def test_connector(connector_name):
            """Test connector connection."""
            if connector_name not in self.connectors:
                return jsonify({
                    "error": "Not Found",
                    "message": f"Connector not found: {connector_name}"
                }), 404

            connector = self.connectors[connector_name]
            result = connector.test_connection()

            return jsonify(result.to_dict()), 200 if result.success else 500

        @self.app.route('/api/v1/connectors/<connector_name>/notify', methods=['POST'])
        @require_api_key(self.auth)
        def send_notification(connector_name):
            """Send notification via connector."""
            if connector_name not in self.connectors:
                return jsonify({
                    "error": "Not Found",
                    "message": f"Connector not found: {connector_name}"
                }), 404

            data = request.get_json()
            message = data.get('message', '')

            if not message:
                return jsonify({
                    "error": "Bad Request",
                    "message": "Message required"
                }), 400

            connector = self.connectors[connector_name]
            result = connector.send_notification(message, **data.get('params', {}))

            return jsonify(result.to_dict()), 200 if result.success else 500

        # ========================================================================
        # Webhook Endpoints
        # ========================================================================

        @self.app.route('/api/v1/webhooks/<service>', methods=['POST'])
        def handle_webhook(service):
            """Handle incoming webhooks."""
            return create_webhook_endpoint(self.webhook_receiver)(service)

    def run(self, host: str = None, port: int = None, debug: bool = None):
        """
        Run the API server.

        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        server_config = self.config.get('server', {})

        host = host or server_config.get('host', 'localhost')
        port = port or server_config.get('port', 5000)
        debug = debug if debug is not None else server_config.get('debug', False)

        logger.info(f"Starting RALF API Gateway on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def create_app(config_file: str = None) -> Flask:
    """
    Create Flask app for RALF API Gateway.

    Args:
        config_file: Path to API configuration file

    Returns:
        Flask application
    """
    # Default config location
    if not config_file:
        config_file = os.path.expanduser("~/.blackbox5/api-config.yaml")

    gateway = RalfAPIGateway(config_file=config_file)
    return gateway.app


def main():
    """Main entry point for running the server."""
    import argparse

    parser = argparse.ArgumentParser(description='RALF API Gateway Server')
    parser.add_argument(
        '--config',
        default='~/.blackbox5/api-config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument('--host', default=None, help='Host to bind to')
    parser.add_argument('--port', type=int, default=None, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    # Create gateway
    gateway = RalfAPIGateway(config_file=args.config)

    # Run server
    gateway.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


if __name__ == '__main__':
    main()
