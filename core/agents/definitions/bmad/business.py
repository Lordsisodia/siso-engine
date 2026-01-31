"""
BMAD Business Analysis Module

Analyzes the business dimension of a project:
- Goals and objectives
- Users and stakeholders
- Value proposition
- Success metrics
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class BusinessAnalysis:
    """
    Business Analysis - What are we building and why?

    This module extracts business-focused insights from project requirements:
    - What problems are being solved?
    - Who are the users?
    - What value does this deliver?
    - How do we measure success?
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize business analyzer with optional configuration."""
        self.config = config or {}

    async def analyze(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the business aspects of a project request.

        Args:
            request: The user's project description
            context: Additional context (existing users, constraints, etc.)

        Returns:
            Dictionary with business analysis results
        """
        logger.info("Running Business Analysis")

        return {
            "goals": self._extract_goals(request, context),
            "users": self._identify_users(request, context),
            "value_proposition": self._extract_value(request, context),
            "success_metrics": self._define_metrics(request, context),
            "constraints": self._identify_constraints(request, context),
            "stakeholders": self._identify_stakeholders(request, context),
        }

    def _extract_goals(self, request: str, context: Dict[str, Any]) -> List[str]:
        """Extract project goals from the request."""
        # In a full implementation, this would use LLM analysis
        # For now, provide heuristic-based extraction

        goals = []

        # Look for goal indicators
        request_lower = request.lower()

        # Common goal patterns
        if "api" in request_lower or "endpoint" in request_lower:
            goals.append("Build a scalable API for data access")

        if "user" in request_lower and "management" in request_lower:
            goals.append("Provide comprehensive user management capabilities")

        if "authentication" in request_lower or "auth" in request_lower:
            goals.append("Secure access with authentication and authorization")

        if "data" in request_lower:
            goals.append("Enable efficient data storage and retrieval")

        # Default goal if nothing specific found
        if not goals:
            goals.append("Deliver a functional solution that meets user needs")

        # Add context goals if provided
        if "goals" in context:
            goals.extend(context["goals"])

        return goals

    def _identify_users(self, request: str, context: Dict[str, Any]) -> List[str]:
        """Identify user types/stakeholders."""
        users = []

        request_lower = request.lower()

        # Common user types
        if "admin" in request_lower or "management" in request_lower:
            users.append("Administrators")

        if "api" in request_lower:
            users.append("API Developers/Integrators")

        if "user" in request_lower:
            users.append("End Users")

        # Always include developers
        if "dev" not in request_lower:
            users.append("Developers")

        # Add context users if provided
        if "users" in context:
            users.extend(context["users"])

        # Default if empty
        if not users:
            users = ["End Users", "Administrators"]

        return list(set(users))  # Deduplicate

    def _extract_value(self, request: str, context: Dict[str, Any]) -> str:
        """Extract value proposition."""
        request_lower = request.lower()

        # Heuristics for value
        if "api" in request_lower:
            return "Provides programmatic access to core functionality, enabling integration with other systems"

        if "management" in request_lower:
            return "Streamlines operations and improves efficiency through centralized management"

        if "security" in request_lower or "authentication" in request_lower:
            return "Protects data and resources through secure access controls"

        if "real-time" in request_lower:
            return "Delivers immediate insights and responses for time-sensitive operations"

        # Default
        return "Solves identified user problems with an efficient, maintainable solution"

    def _define_metrics(self, request: str, context: Dict[str, Any]) -> List[str]:
        """Define success metrics."""
        metrics = []

        # Standard technical metrics
        metrics.append("API response time < 200ms (p95)")
        metrics.append("System availability > 99.5%")
        metrics.append("Zero critical bugs in production")

        # Context-specific metrics
        request_lower = request.lower()

        if "user" in request_lower:
            metrics.append("User onboarding time < 5 minutes")

        if "api" in request_lower:
            metrics.append("API error rate < 0.1%")

        if "scale" in request_lower or "performance" in request_lower:
            metrics.append("Handle 1000+ concurrent requests")

        # Add context metrics if provided
        if "success_metrics" in context:
            metrics.extend(context["success_metrics"])

        return metrics

    def _identify_constraints(self, request: str, context: Dict[str, Any]) -> List[str]:
        """Identify business constraints."""
        constraints = []

        # Check context for explicit constraints
        if "constraints" in context:
            constraints.extend(context["constraints"])

        # Infer from request
        request_lower = request.lower()

        if "budget" in request_lower:
            constraints.append("Budget limitations")

        if "deadline" in request_lower or "timeline" in request_lower:
            constraints.append("Time constraints")

        if "legacy" in request_lower:
            constraints.append("Integration with legacy systems")

        # Default constraints
        if not constraints:
            constraints = ["Development resources", "Time to market"]

        return constraints

    def _identify_stakeholders(self, request: str, context: Dict[str, Any]) -> List[str]:
        """Identify stakeholders."""
        stakeholders = ["Product Team", "Development Team"]

        # Add context stakeholders
        if "stakeholders" in context:
            stakeholders.extend(context["stakeholders"])

        return list(set(stakeholders))


# Type hint for optional import
Optional = Dict[str, Any] if 'Optional' not in dir() else None
