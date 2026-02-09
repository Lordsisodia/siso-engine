"""
BMAD Architecture Design Module

Analyzes the system architecture:
- Components and their responsibilities
- Interfaces between components
- Data storage requirements
- Integration points
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ArchitectureDesign:
    """
    Architecture Design - How will it work?

    This module defines the system architecture:
    - What components are needed?
    - How do they communicate?
    - Where is data stored?
    - What external integrations are needed?
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize architecture designer with optional configuration."""
        self.config = config or {}

    async def analyze(
        self,
        request: str,
        context: Dict[str, Any],
        model_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze the system architecture from project request.

        Args:
            request: The user's project description
            context: Additional context
            model_result: Results from model design

        Returns:
            Dictionary with architecture design results
        """
        logger.info("Running Architecture Design")

        return {
            "components": self._identify_components(request, context),
            "interfaces": self._define_interfaces(request, context),
            "data_stores": self._select_stores(request, context),
            "integration_points": self._find_integrations(request, context),
            "tech_stack": self._infer_tech_stack(request, context),
        }

    def _identify_components(self, request: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify system components."""
        components = []
        request_lower = request.lower()

        # API components
        if "api" in request_lower or "rest" in request_lower:
            components.extend([
                {
                    "name": "API Gateway",
                    "responsibility": "Request routing, authentication, rate limiting",
                    "type": "infrastructure"
                },
                {
                    "name": "Service Layer",
                    "responsibility": "Business logic, request validation",
                    "type": "service"
                },
                {
                    "name": "Data Access Layer",
                    "responsibility": "Database operations, data transformation",
                    "type": "data"
                }
            ])

        # Auth components
        if "authentication" in request_lower or "auth" in request_lower:
            components.append({
                "name": "Auth Service",
                "responsibility": "User authentication, token management",
                "type": "service"
            })

        # Real-time components
        if "real-time" in request_lower or "websocket" in request_lower:
            components.append({
                "name": "Event Broker",
                "responsibility": "Message routing, event streaming",
                "type": "infrastructure"
            })

        # Web UI components
        if "web" in request_lower or "frontend" in request_lower:
            components.append({
                "name": "Web Client",
                "responsibility": "User interface, client-side logic",
                "type": "client"
            })

        # Default components if nothing specific
        if not components:
            components = [
                {
                    "name": "Application Core",
                    "responsibility": "Main application logic",
                    "type": "service"
                },
                {
                    "name": "Data Layer",
                    "responsibility": "Data persistence and retrieval",
                    "type": "data"
                }
            ]

        # Add context components if provided
        if "components" in context:
            components.extend(context["components"])

        return components

    def _define_interfaces(self, request: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Define interfaces between components."""
        interfaces = []
        request_lower = request.lower()

        if "api" in request_lower:
            interfaces.extend([
                {
                    "name": "REST API",
                    "type": "HTTP/REST",
                    "description": "JSON over HTTP",
                    "protocols": ["HTTP/1.1", "HTTP/2"]
                },
                {
                    "name": "Service Interface",
                    "type": "Internal",
                    "description": "Inter-service communication",
                    "protocols": ["Function call", "Async messaging"]
                }
            ])

        if "authentication" in request_lower:
            interfaces.append({
                "name": "Auth Interface",
                "type": "Security",
                "description": "Token-based authentication",
                "protocols": ["JWT", "OAuth2"]
            })

        # Add context interfaces if provided
        if "interfaces" in context:
            interfaces.extend(context["interfaces"])

        return interfaces

    def _select_stores(self, request: str, context: Dict[str, Any]) -> List[str]:
        """Select data storage solutions."""
        stores = []
        request_lower = request.lower()

        # Standard stores
        if "user" in request_lower or "data" in request_lower:
            stores.append("PostgreSQL (relational data)")

        if "cache" in request_lower or "session" in request_lower:
            stores.append("Redis (caching, sessions)")

        if "document" in request_lower or "file" in request_lower:
            stores.append("S3-compatible storage (documents, files)")

        if "search" in request_lower or "query" in request_lower:
            stores.append("Elasticsearch (full-text search)")

        # Default if nothing specific
        if not stores:
            stores = ["PostgreSQL (primary data store)", "File system (static assets)"]

        # Add context stores if provided
        if "data_stores" in context:
            stores.extend(context["data_stores"])

        return list(set(stores))

    def _find_integrations(self, request: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find integration points with external systems."""
        integrations = []
        request_lower = request.lower()

        # Common integrations
        if "email" in request_lower or "notification" in request_lower:
            integrations.append({
                "system": "Email Service",
                "purpose": "Sending notifications",
                "type": "outbound"
            })

        if "payment" in request_lower or "billing" in request_lower:
            integrations.append({
                "system": "Payment Gateway",
                "purpose": "Processing payments",
                "type": "external"
            })

        if "log" in request_lower or "monitoring" in request_lower:
            integrations.append({
                "system": "Logging/Monitoring",
                "purpose": "Observability",
                "type": "infrastructure"
            })

        # Add context integrations if provided
        if "integrations" in context:
            integrations.extend(context["integrations"])

        return integrations

    def _infer_tech_stack(self, request: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Infer appropriate technology stack."""
        stack = {}

        request_lower = request.lower()

        # Language inference
        if any(lang in request_lower for lang in ["python", "fastapi", "django"]):
            stack["language"] = "Python"
        elif any(lang in request_lower for lang in ["node", "javascript", "typescript"]):
            stack["language"] = "TypeScript/Node.js"
        elif "java" in request_lower:
            stack["language"] = "Java"
        elif "go" in request_lower or "golang" in request_lower:
            stack["language"] = "Go"
        else:
            stack["language"] = "Python (default)"

        # Framework inference
        if "fastapi" in request_lower:
            stack["framework"] = "FastAPI"
        elif "django" in request_lower:
            stack["framework"] = "Django"
        elif "flask" in request_lower:
            stack["framework"] = "Flask"
        elif "express" in request_lower:
            stack["framework"] = "Express.js"
        else:
            stack["framework"] = "Based on language"

        # API protocol
        if "api" in request_lower:
            stack["api_protocol"] = "REST (JSON)"

        # Override with context if provided
        if "tech_stack" in context:
            tech_context = context["tech_stack"]
            if isinstance(tech_context, dict):
                stack.update(tech_context)
            elif isinstance(tech_context, list):
                # List of technologies - add as "specified" key
                stack["specified"] = ", ".join(tech_context)

        return stack
