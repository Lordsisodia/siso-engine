"""
BMAD Framework - Business, Model, Architecture, Development

A structured methodology for analyzing and planning software projects.
This framework provides a systematic approach to understanding requirements
from multiple perspectives.
"""

import logging
from typing import Any, Dict, List, Optional
from .business import BusinessAnalysis
from .model import ModelDesign
from .architecture import ArchitectureDesign
from .development import DevelopmentPlan

logger = logging.getLogger(__name__)


class BMADFramework:
    """
    Business, Model, Architecture, Development Framework

    A comprehensive analysis framework that breaks down project requirements
    into four key dimensions:

    - **Business**: What are we building and why?
    - **Model**: What's the conceptual model?
    - **Architecture**: How will it work?
    - **Development**: How do we build it?

    Example:
        ```python
        bmad = BMADFramework()
        analysis = await bmad.analyze("Build a REST API for user management")

        # Access results
        business_goals = analysis["business"]["goals"]
        entities = analysis["model"]["entities"]
        components = analysis["architecture"]["components"]
        phases = analysis["development"]["phases"]
        ```
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the BMAD Framework.

        Args:
            config: Optional configuration for customizing analysis behavior
        """
        self.config = config or {}

        # Initialize analyzers
        self.business = BusinessAnalysis(self.config.get("business", {}))
        self.model = ModelDesign(self.config.get("model", {}))
        self.architecture = ArchitectureDesign(self.config.get("architecture", {}))
        self.development = DevelopmentPlan(self.config.get("development", {}))

    async def analyze(self, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Apply BMAD analysis to a user request.

        This is the main entry point for the framework. It runs all four
        analysis dimensions and returns a consolidated result.

        Args:
            request: The user's project request
            context: Additional context (constraints, preferences, etc.)

        Returns:
            Dictionary with four top-level keys:
            - "business": Business analysis results
            - "model": Conceptual model design
            - "architecture": System architecture
            - "development": Development plan

        Example:
            ```python
            result = await bmad.analyze(
                "Build a task management API",
                context={"tech_stack": ["Python", "FastAPI"]}
            )
            ```
        """
        context = context or {}

        logger.info(f"Starting BMAD analysis for: {request[:50]}...")

        # Run all four analyses
        business_result = await self.business.analyze(request, context)
        model_result = await self.model.analyze(request, context, business_result)
        architecture_result = await self.architecture.analyze(request, context, model_result)
        development_result = await self.development.analyze(request, context, architecture_result)

        result = {
            "business": business_result,
            "model": model_result,
            "architecture": architecture_result,
            "development": development_result,
            "metadata": {
                "request": request,
                "framework_version": "1.0",
                "analysis_timestamp": self._get_timestamp(),
            }
        }

        logger.info("BMAD analysis complete")
        return result

    async def analyze_business_only(self, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run only business analysis."""
        return await self.business.analyze(request, context or {})

    async def analyze_model_only(self, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run only model design."""
        business = await self.business.analyze(request, context or {})
        return await self.model.analyze(request, context or {}, business)

    async def analyze_architecture_only(self, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run only architecture design."""
        business = await self.business.analyze(request, context or {})
        model = await self.model.analyze(request, context or {}, business)
        return await self.architecture.analyze(request, context or {}, model)

    async def analyze_development_only(self, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run only development planning."""
        business = await self.business.analyze(request, context or {})
        model = await self.model.analyze(request, context or {}, business)
        architecture = await self.architecture.analyze(request, context or {}, model)
        return await self.development.analyze(request, context or {}, architecture)

    def get_summary(self, analysis: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the BMAD analysis.

        Args:
            analysis: The full analysis result from analyze()

        Returns:
            Formatted markdown summary
        """
        lines = [
            "# BMAD Analysis Summary",
            "",
            f"**Request:** {analysis['metadata']['request']}",
            f"**Analyzed:** {analysis['metadata']['analysis_timestamp']}",
            "",
            "## Business Analysis",
            f"- **Goals:** {len(analysis['business'].get('goals', []))} identified",
            f"- **Users:** {', '.join(analysis['business'].get('users', []))}",
            f"- **Value:** {analysis['business'].get('value_proposition', 'N/A')[:80]}...",
            "",
            "## Model Design",
            f"- **Entities:** {len(analysis['model'].get('entities', []))} identified",
            f"- **Relationships:** {len(analysis['model'].get('relationships', []))} defined",
            "",
            "## Architecture",
            f"- **Components:** {len(analysis['architecture'].get('components', []))} identified",
            f"- **Data Stores:** {', '.join(analysis['architecture'].get('data_stores', []))}",
            "",
            "## Development Plan",
            f"- **Phases:** {len(analysis['development'].get('phases', []))} planned",
            f"- **Total Tasks:** {analysis['development'].get('total_tasks', 'N/A')}",
            f"- **Estimated Effort:** {analysis['development'].get('estimated_effort', 'N/A')}",
            "",
        ]

        return "\n".join(lines)

    @staticmethod
    def _get_timestamp() -> str:
        """Get current ISO timestamp."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
