"""
API Authentication Middleware for RALF
Provides API key-based authentication and rate limiting
Part of Feature F-012 (API Gateway & External Service Integration)

Usage:
    from api_auth import APIAuth, require_api_key, check_rate_limit

    auth = APIAuth(config_file="~/.blackbox5/api-config.yaml")

    # In Flask route
    @app.route("/api/v1/tasks")
    @require_api_key(auth)
    def get_tasks():
        return {"tasks": []}

Requirements:
    - Flask (web framework)
    - Configuration file with API keys
"""

import logging
import time
import hashlib
from typing import Optional, Dict, List, Tuple, Callable
from functools import wraps
from datetime import datetime, timedelta
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class APIAuthError(Exception):
    """Base exception for authentication errors."""
    pass


class InvalidAPIKeyError(APIAuthError):
    """Invalid API key provided."""
    pass


class RateLimitExceededError(APIAuthError):
    """Rate limit exceeded."""
    pass


class APIKey:
    """Represents an API key with metadata."""

    def __init__(self, name: str, key: str, scopes: List[str], created_at: str = None):
        self.name = name
        self.key = key
        self.scopes = scopes
        self.created_at = created_at or datetime.utcnow().isoformat()

    def has_scope(self, scope: str) -> bool:
        """Check if API key has required scope."""
        return "*" in self.scopes or scope in self.scopes

    def to_dict(self) -> dict:
        """Convert to dictionary (hiding sensitive data)."""
        return {
            "name": self.name,
            "scopes": self.scopes,
            "created_at": self.created_at
        }


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = {}

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed based on rate limit.

        Args:
            identifier: Unique identifier (API key or IP address)

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        now = time.time()
        minute_ago = now - 60

        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                timestamp for timestamp in self.requests[identifier]
                if timestamp > minute_ago
            ]
        else:
            self.requests[identifier] = []

        # Check limit
        if len(self.requests[identifier]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False

        # Record this request
        self.requests[identifier].append(now)
        return True

    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        now = time.time()
        minute_ago = now - 60

        if identifier not in self.requests:
            return self.requests_per_minute

        # Clean old requests
        self.requests[identifier] = [
            timestamp for timestamp in self.requests[identifier]
            if timestamp > minute_ago
        ]

        return max(0, self.requests_per_minute - len(self.requests[identifier]))


class APIAuth:
    """
    API Authentication Manager.

    Handles API key validation, rate limiting, and request logging.
    """

    def __init__(self, config_file: str = None):
        """
        Initialize API authentication.

        Args:
            config_file: Path to API configuration file
        """
        self.config_file = Path(config_file).expanduser() if config_file else None
        self.api_keys: Dict[str, APIKey] = {}
        self.rate_limiter: Optional[RateLimiter] = None
        self.rate_limit_enabled = False
        self.requests_per_minute = 100

        if self.config_file and self.config_file.exists():
            self._load_config()

    def _load_config(self):
        """Load API keys and rate limiting from configuration file."""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f) or {}

            # Load API keys
            auth_config = config.get('auth', {})
            keys_config = auth_config.get('api_keys', [])

            for key_config in keys_config:
                api_key = APIKey(
                    name=key_config.get('name', 'unknown'),
                    key=key_config.get('key', ''),
                    scopes=key_config.get('scopes', ['*']),
                    created_at=key_config.get('created_at')
                )
                # Store by key hash (not the key itself for security)
                key_hash = self._hash_key(api_key.key)
                self.api_keys[key_hash] = api_key

            logger.info(f"Loaded {len(self.api_keys)} API keys")

            # Load rate limiting
            rate_limit_config = auth_config.get('rate_limit', {})
            self.rate_limit_enabled = rate_limit_config.get('enabled', False)
            self.requests_per_minute = rate_limit_config.get('requests_per_minute', 100)

            if self.rate_limit_enabled:
                self.rate_limiter = RateLimiter(self.requests_per_minute)
                logger.info(f"Rate limiting enabled: {self.requests_per_minute} req/min")

        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")

    def _hash_key(self, key: str) -> str:
        """Hash API key for storage (SHA-256)."""
        return hashlib.sha256(key.encode()).hexdigest()

    def validate_key(self, api_key: str) -> Tuple[bool, Optional[APIKey]]:
        """
        Validate API key.

        Args:
            api_key: The API key to validate

        Returns:
            Tuple of (is_valid, api_key_object)
        """
        key_hash = self._hash_key(api_key)

        if key_hash in self.api_keys:
            return True, self.api_keys[key_hash]

        return False, None

    def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if request is allowed based on rate limit.

        Args:
            identifier: Unique identifier (API key hash or IP address)

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        if not self.rate_limit_enabled or not self.rate_limiter:
            return True

        return self.rate_limiter.is_allowed(identifier)

    def get_rate_limit_info(self, identifier: str) -> dict:
        """
        Get rate limit information for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Dictionary with rate limit info
        """
        if not self.rate_limit_enabled or not self.rate_limiter:
            return {
                "enabled": False,
                "limit": self.requests_per_minute,
                "remaining": self.requests_per_minute
            }

        return {
            "enabled": True,
            "limit": self.requests_per_minute,
            "remaining": self.rate_limiter.get_remaining(identifier),
            "reset": int((time.time() // 60 + 1) * 60)
        }


# Flask Decorators

def require_api_key(auth: APIAuth):
    """
    Flask decorator to require API key authentication.

    Usage:
        @app.route("/api/v1/tasks")
        @require_api_key(auth)
        def get_tasks():
            return {"tasks": []}
    """
    from flask import request, jsonify, g

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from header
            api_key = request.headers.get('X-API-Key')

            if not api_key:
                logger.warning("Request missing API key")
                return jsonify({
                    "error": "Unauthorized",
                    "message": "API key required. Use X-API-Key header."
                }), 401

            # Validate API key
            is_valid, key_obj = auth.validate_key(api_key)

            if not is_valid:
                logger.warning(f"Invalid API key from {request.remote_addr}")
                return jsonify({
                    "error": "Forbidden",
                    "message": "Invalid API key"
                }), 403

            # Check rate limit
            key_hash = auth._hash_key(api_key)
            if not auth.check_rate_limit(key_hash):
                logger.warning(f"Rate limit exceeded for key: {key_obj.name}")
                return jsonify({
                    "error": "Too Many Requests",
                    "message": "Rate limit exceeded. Please try again later.",
                    "rate_limit": auth.get_rate_limit_info(key_hash)
                }), 429

            # Store API key in Flask g object
            g.api_key = key_obj

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_scope(auth: APIAuth, scope: str):
    """
    Flask decorator to require specific API scope.

    Usage:
        @app.route("/api/v1/tasks", methods=["POST"])
        @require_api_key(auth)
        @require_scope(auth, "write:tasks")
        def create_task():
            return {"task_id": "TASK-001"}
    """
    from flask import g, jsonify

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = getattr(g, 'api_key', None)

            if not api_key:
                return jsonify({
                    "error": "Unauthorized",
                    "message": "API key not found"
                }), 401

            if not api_key.has_scope(scope):
                logger.warning(f"Scope '{scope}' required but not present in key '{api_key.name}'")
                return jsonify({
                    "error": "Forbidden",
                    "message": f"API key missing required scope: {scope}"
                }), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Security Headers

def add_security_headers(response):
    """Add security headers to Flask response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


# Logging

def log_request(auth: APIAuth):
    """
    Flask decorator to log API requests.

    Usage:
        @app.before_request
        def log_api_request():
            if request.path.startswith('/api/v1'):
                log_request(auth)
    """
    from flask import request, g

    api_key = getattr(g, 'api_key', None)
    key_name = api_key.name if api_key else 'anonymous'

    logger.info(f"{request.method} {request.path} - Key: {key_name} - IP: {request.remote_addr}")
