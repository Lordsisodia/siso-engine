"""
BMAD Model Design Module

Analyzes the conceptual model of a project:
- Entities and their properties
- Relationships between entities
- Data flow patterns
- State model
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ModelDesign:
    """
    Model Design - What's the conceptual model?

    This module defines the conceptual model of the system:
    - What entities exist?
    - How do they relate?
    - How does data flow?
    - What are the key states?
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize model designer with optional configuration."""
        self.config = config or {}

    async def analyze(
        self,
        request: str,
        context: Dict[str, Any],
        business_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze the conceptual model from project request.

        Args:
            request: The user's project description
            context: Additional context
            business_result: Results from business analysis

        Returns:
            Dictionary with model design results
        """
        logger.info("Running Model Design")

        return {
            "entities": self._extract_entities(request, context),
            "relationships": self._extract_relationships(request, context),
            "data_flow": self._model_data_flow(request, context),
            "state_model": self._define_states(request, context),
        }

    def _extract_entities(self, request: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract key entities from the request."""
        entities = []
        request_lower = request.lower()

        # Common entity patterns
        if "user" in request_lower:
            entities.append({
                "name": "User",
                "properties": ["id", "username", "email", "created_at"],
                "description": "System user account"
            })

        if "api" in request_lower and "user" in request_lower:
            entities.append({
                "name": "APIKey",
                "properties": ["id", "user_id", "key_hash", "created_at"],
                "description": "API authentication key"
            })

        if "task" in request_lower or "project" in request_lower:
            entities.append({
                "name": "Task",
                "properties": ["id", "title", "description", "status", "created_at"],
                "description": "Work item to be completed"
            })

        # Standard system entities
        if "session" not in [e["name"].lower() for e in entities]:
            entities.append({
                "name": "Session",
                "properties": ["id", "user_id", "token", "expires_at"],
                "description": "User authentication session"
            })

        # Add context entities if provided
        if "entities" in context:
            entities.extend(context["entities"])

        # Default if nothing found
        if not entities:
            entities = [
                {
                    "name": "Resource",
                    "properties": ["id", "name", "created_at"],
                    "description": "Generic resource entity"
                }
            ]

        return entities

    def _extract_relationships(self, request: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relationships between entities."""
        relationships = []
        request_lower = request.lower()

        # User-based relationships
        if "user" in request_lower:
            relationships.extend([
                {
                    "from": "User",
                    "to": "APIKey",
                    "type": "one-to-many",
                    "description": "User has multiple API keys"
                },
                {
                    "from": "User",
                    "to": "Session",
                    "type": "one-to-many",
                    "description": "User has multiple sessions"
                }
            ])

        # Task relationships
        if "task" in request_lower:
            relationships.append({
                "from": "User",
                "to": "Task",
                "type": "one-to-many",
                "description": "User creates/owns tasks"
            })

        # Add context relationships if provided
        if "relationships" in context:
            relationships.extend(context["relationships"])

        return relationships

    def _model_data_flow(self, request: str, context: Dict[str, Any]) -> List[str]:
        """Model the data flow patterns."""
        flows = []

        request_lower = request.lower()

        if "api" in request_lower:
            flows.extend([
                "Client → API Gateway → Service Layer → Data Layer",
                "Request → Validation → Business Logic → Persistence",
                "Data → Transformation → Response"
            ])

        if "authentication" in request_lower or "auth" in request_lower:
            flows.extend([
                "Credentials → Auth Service → Token",
                "Token → Validation → User Context"
            ])

        if "real-time" in request_lower:
            flows.append("Event → Stream → Processor → Subscriber")

        # Default flow
        if not flows:
            flows = [
                "Request → Handler → Processor → Response",
                "Input → Validation → Storage → Retrieval"
            ]

        return flows

    def _define_states(self, request: str, context: Dict[str, Any]) -> Dict[str, List[str]]:
        """Define key states for entities."""
        states = {}

        request_lower = request.lower()

        # Common state models
        if "task" in request_lower:
            states["Task"] = ["pending", "in_progress", "completed", "cancelled"]

        if "user" in request_lower:
            states["User"] = ["inactive", "active", "suspended"]

        if "api" in request_lower and "key" in request_lower:
            states["APIKey"] = ["active", "revoked", "expired"]

        # Generic states if nothing specific
        if not states:
            states["Resource"] = ["draft", "active", "archived"]

        # Add context states if provided
        if "states" in context:
            states.update(context["states"])

        return states
