#!/usr/bin/env python3
"""
Guide Middleware

Integrates the Guide System into agent execution flows.
Implements "inverted intelligence" - system is smart, agent can be dumb.

The middleware intercepts agent actions and offers proactive guidance
at key points in the workflow, making Blackbox 5 easier to use for
any agent regardless of its capabilities.

Events handled:
- agent_execute: Before agent executes an action
- agent_complete: After agent completes an action
- file_written: When files are written to disk
- git_stage: When files are staged for commit

Confidence thresholds:
- before_agent_action: 0.7 (only high-confidence suggestions)
- after_agent_action: 0.5 (medium confidence for follow-ups)
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

# Import Guide system
try:
    from guides import Guide
except ImportError:
    # Fallback for relative imports
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from guides import Guide


logger = logging.getLogger(__name__)


class GuideMiddleware:
    """
    Middleware that integrates Guide System into agent execution flows.

    This implements the "inverted intelligence" pattern where the system
    is smart and proactive, while the agent can remain simple and reactive.

    The middleware monitors agent actions and offers relevant guidance
    at appropriate moments, reducing the cognitive burden on agents.
    """

    # Confidence thresholds
    BEFORE_THRESHOLD = 0.7  # High confidence for proactive suggestions
    AFTER_THRESHOLD = 0.5   # Medium confidence for follow-up suggestions

    # Events to monitor
    MONITORED_EVENTS = [
        "agent_execute",
        "agent_complete",
        "file_written",
        "git_stage",
        "command_execute",
        "test_run",
        "deployment_start"
    ]

    def __init__(self, project_path: str = "."):
        """
        Initialize the Guide Middleware.

        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path).resolve()
        self.guide = Guide(str(self.project_path))
        self._enabled = True
        self._stats = {
            "suggestions_offered": 0,
            "suggestions_accepted": 0,
            "guides_executed": 0,
            "errors": 0
        }

        logger.info(f"GuideMiddleware initialized for {self.project_path}")

    # ========== Middleware API ==========

    async def before_agent_action(self, event: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check for guide suggestions BEFORE agent action.

        This is called right before an agent is about to perform an action.
        Only high-confidence suggestions (>= 0.7) are returned to avoid
        interrupting the agent with low-relevance guidance.

        Args:
            event: The event type (e.g., "agent_execute", "file_written")
            context: Contextual information about the action

        Returns:
            Dictionary with suggestion if confidence >= 0.7, None otherwise
        """
        if not self._enabled:
            return None

        if event not in self.MONITORED_EVENTS:
            return None

        try:
            # Get top suggestion from guide system
            suggestion = self.guide.get_top_suggestion(event, context)

            if suggestion and suggestion.get('confidence', 0) >= self.BEFORE_THRESHOLD:
                self._stats["suggestions_offered"] += 1

                return {
                    "action": "offer_guide",
                    "guide": suggestion['guide'],
                    "suggestion": suggestion['suggestion'],
                    "description": suggestion['description'],
                    "confidence": suggestion['confidence'],
                    "estimated_time": suggestion.get('estimated_time', 'unknown'),
                    "difficulty": suggestion.get('difficulty', 'medium'),
                    "trigger_event": event,
                    "timing": "before"
                }

        except Exception as e:
            logger.error(f"Error in before_agent_action: {e}")
            self._stats["errors"] += 1

        return None

    async def after_agent_action(self, event: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check for relevant guides AFTER agent action.

        This is called after an agent has completed an action.
        Returns multiple suggestions with confidence >= 0.5 for follow-up actions.

        Args:
            event: The event type (e.g., "agent_complete", "file_written")
            context: Contextual information about the action

        Returns:
            List of suggestion dictionaries with confidence >= 0.5
        """
        if not self._enabled:
            return []

        if event not in self.MONITORED_EVENTS:
            return []

        try:
            # Get all matching guides
            matches = self.guide.check_context(event, context)

            # Filter by threshold and format results
            suggestions = []
            for match in matches:
                if match.get('confidence', 0) >= self.AFTER_THRESHOLD:
                    suggestions.append({
                        "action": "offer_guide",
                        "guide": match['guide'],
                        "suggestion": match['suggestion'],
                        "description": match['description'],
                        "confidence": match['confidence'],
                        "estimated_time": match.get('estimated_time', 'unknown'),
                        "difficulty": match.get('difficulty', 'medium'),
                        "trigger_event": event,
                        "timing": "after"
                    })

            if suggestions:
                self._stats["suggestions_offered"] += len(suggestions)

            return suggestions

        except Exception as e:
            logger.error(f"Error in after_agent_action: {e}")
            self._stats["errors"] += 1
            return []

    async def execute_guide_if_accepted(self, guide_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a guide automatically when agent accepts suggestion.

        This method runs the full recipe for a guide without requiring
        further agent intervention. The system handles all steps automatically.

        Args:
            guide_name: Name of the guide/operation to execute
            context: Contextual information for the guide

        Returns:
            Dictionary with execution results
        """
        if not self._enabled:
            return {
                "error": "Guide middleware is disabled"
            }

        try:
            self._stats["suggestions_accepted"] += 1

            # Start the operation
            result = self.guide.start_operation(guide_name, context)

            if "error" in result:
                logger.error(f"Error starting operation '{guide_name}': {result['error']}")
                self._stats["errors"] += 1
                return result

            # Execute all steps automatically
            execution_result = self.guide.execute_full_recipe(guide_name, context)

            if execution_result.get("status") == "success":
                self._stats["guides_executed"] += 1
                logger.info(f"Successfully executed guide: {guide_name}")
            else:
                logger.error(f"Guide execution failed: {guide_name}")
                self._stats["errors"] += 1

            return execution_result

        except Exception as e:
            logger.error(f"Error executing guide '{guide_name}': {e}")
            self._stats["errors"] += 1
            return {
                "error": str(e),
                "guide": guide_name
            }

    # ========== Control Methods ==========

    def enable(self) -> None:
        """Enable the guide middleware."""
        self._enabled = True
        logger.info("Guide middleware enabled")

    def disable(self) -> None:
        """Disable the guide middleware."""
        self._enabled = False
        logger.info("Guide middleware disabled")

    def is_enabled(self) -> bool:
        """Check if the guide middleware is enabled."""
        return self._enabled

    # ========== Statistics & Monitoring ==========

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get middleware usage statistics.

        Returns:
            Dictionary with usage metrics
        """
        return {
            "enabled": self._enabled,
            "suggestions_offered": self._stats["suggestions_offered"],
            "suggestions_accepted": self._stats["suggestions_accepted"],
            "guides_executed": self._stats["guides_executed"],
            "errors": self._stats["errors"],
            "acceptance_rate": (
                self._stats["suggestions_accepted"] / self._stats["suggestions_offered"]
                if self._stats["suggestions_offered"] > 0 else 0.0
            )
        }

    def reset_statistics(self) -> None:
        """Reset usage statistics."""
        self._stats = {
            "suggestions_offered": 0,
            "suggestions_accepted": 0,
            "guides_executed": 0,
            "errors": 0
        }
        logger.info("Guide middleware statistics reset")

    # ========== Discovery & Search ==========

    def list_available_guides(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available guides.

        Args:
            category: Optional category filter

        Returns:
            List of guide information dictionaries
        """
        return self.guide.list_operations(category)

    def search_guides(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for guides by keyword.

        Args:
            query: Search query

        Returns:
            List of matching guides
        """
        return self.guide.search_guides(query)

    def list_categories(self) -> List[str]:
        """
        List all available guide categories.

        Returns:
            List of category names
        """
        return self.guide.list_categories()

    # ========== Active Recipe Management ==========

    def get_active_recipes(self) -> List[Dict[str, Any]]:
        """
        Get all currently active recipes.

        Returns:
            List of active recipe summaries
        """
        return self.guide.list_active_recipes()

    def get_recipe_status(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific recipe.

        Args:
            recipe_id: Recipe identifier

        Returns:
            Recipe status dictionary or None if not found
        """
        return self.guide.get_recipe_status(recipe_id)


# ========== Singleton Pattern ==========

_guide_middleware: Optional[GuideMiddleware] = None


def get_guide_middleware(project_path: str = ".") -> GuideMiddleware:
    """
    Get or create the Guide Middleware singleton.

    This ensures that only one instance of the middleware exists
    per process, maintaining consistent state across the application.

    Args:
        project_path: Path to the project directory (only used on first call)

    Returns:
        The singleton GuideMiddleware instance

    Example:
        >>> middleware = get_guide_middleware("/path/to/project")
        >>> suggestion = await middleware.before_agent_action("file_written", {"file_path": "test.py"})
    """
    global _guide_middleware

    if _guide_middleware is None:
        _guide_middleware = GuideMiddleware(project_path)
        logger.info(f"Created GuideMiddleware singleton for {project_path}")

    return _guide_middleware


def reset_guide_middleware() -> None:
    """
    Reset the Guide Middleware singleton.

    This creates a new instance on the next call to get_guide_middleware().
    Useful for testing or when switching projects.
    """
    global _guide_middleware
    _guide_middleware = None
    logger.info("GuideMiddleware singleton reset")


# ========== Convenience Functions ==========

async def offer_guidance_before(event: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convenience function to offer guidance before an action.

    Args:
        event: Event type
        context: Event context

    Returns:
        Suggestion dictionary or None
    """
    middleware = get_guide_middleware()
    return await middleware.before_agent_action(event, context)


async def offer_guidance_after(event: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convenience function to offer guidance after an action.

    Args:
        event: Event type
        context: Event context

    Returns:
        List of suggestion dictionaries
    """
    middleware = get_guide_middleware()
    return await middleware.after_agent_action(event, context)


async def execute_guide(guide_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to execute a guide.

    Args:
        guide_name: Name of the guide
        context: Execution context

    Returns:
        Execution result dictionary
    """
    middleware = get_guide_middleware()
    return await middleware.execute_guide_if_accepted(guide_name, context)
