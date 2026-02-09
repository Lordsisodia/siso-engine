"""
BMAD Development Planning Module

Creates the development plan:
- Development phases
- Task breakdown
- Dependencies
- Effort estimates
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DevelopmentPlan:
    """
    Development Plan - How do we build it?

    This module creates the development roadmap:
    - What are the development phases?
    - What tasks are in each phase?
    - What are the dependencies?
    - How long will it take?
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize development planner with optional configuration."""
        self.config = config or {}

    async def analyze(
        self,
        request: str,
        context: Dict[str, Any],
        architecture_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create the development plan from project request.

        Args:
            request: The user's project description
            context: Additional context
            architecture_result: Results from architecture design

        Returns:
            Dictionary with development plan results
        """
        logger.info("Running Development Planning")

        phases = self._break_into_phases(request, context, architecture_result)

        return {
            "phases": phases,
            "tasks": self._define_tasks(request, context, phases),
            "dependencies": self._find_dependencies(request, context, phases),
            "effort_estimates": self._estimate_effort(request, context, phases),
            "total_phases": len(phases),
            "total_tasks": sum(len(p.get("tasks", [])) for p in phases),
            "estimated_effort": self._calculate_total_effort(phases),
        }

    def _break_into_phases(
        self,
        request: str,
        context: Dict[str, Any],
        arch_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Break development into phases."""
        phases = []

        # Standard phases for any project
        phases.append({
            "id": "PHASE-1",
            "name": "Foundation",
            "description": "Set up project infrastructure and base components",
            "priority": "critical",
            "tasks": [
                "Initialize project structure",
                "Set up development environment",
                "Configure linting, formatting, testing",
                "Set up CI/CD pipeline"
            ]
        })

        phases.append({
            "id": "PHASE-2",
            "name": "Core Features",
            "description": "Implement primary functionality",
            "priority": "high",
            "tasks": [
                "Implement data models",
                "Build core business logic",
                "Create primary API endpoints",
                "Implement authentication (if needed)"
            ]
        })

        phases.append({
            "id": "PHASE-3",
            "name": "Integration",
            "description": "Integrate components and external services",
            "priority": "medium",
            "tasks": [
                "Integrate data layer",
                "Connect external services",
                "Implement error handling"
            ]
        })

        phases.append({
            "id": "PHASE-4",
            "name": "Testing & Quality",
            "description": "Comprehensive testing and quality assurance",
            "priority": "high",
            "tasks": [
                "Write unit tests",
                "Write integration tests",
                "Performance testing",
                "Security review"
            ]
        })

        phases.append({
            "id": "PHASE-5",
            "name": "Deployment",
            "description": "Deploy to production",
            "priority": "high",
            "tasks": [
                "Prepare deployment configuration",
                "Set up monitoring",
                "Deploy to staging",
                "Deploy to production"
            ]
        })

        # Add context phases if provided
        if "phases" in context:
            phases.extend(context["phases"])

        return phases

    def _define_tasks(
        self,
        request: str,
        context: Dict[str, Any],
        phases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Define detailed tasks from phases."""
        tasks = []
        task_id = 1

        for phase in phases:
            for task_name in phase.get("tasks", []):
                tasks.append({
                    "id": f"TASK-{task_id:03d}",
                    "title": task_name,
                    "phase": phase["id"],
                    "priority": phase["priority"],
                    "status": "pending"
                })
                task_id += 1

        return tasks

    def _find_dependencies(
        self,
        request: str,
        context: Dict[str, Any],
        phases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find dependencies between tasks and phases."""
        dependencies = []

        # Phase dependencies (each phase depends on previous)
        for i in range(1, len(phases)):
            dependencies.append({
                "from": phases[i]["id"],
                "to": phases[i-1]["id"],
                "type": "phase",
                "description": f"{phases[i]['name']} depends on {phases[i-1]['name']}"
            })

        # Add context dependencies if provided
        if "dependencies" in context:
            dependencies.extend(context["dependencies"])

        return dependencies

    def _estimate_effort(
        self,
        request: str,
        context: Dict[str, Any],
        phases: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Estimate effort for each phase."""
        estimates = {}

        # Base estimates in days
        phase_days = {
            "PHASE-1": "2-3 days",
            "PHASE-2": "5-7 days",
            "PHASE-3": "3-4 days",
            "PHASE-4": "2-3 days",
            "PHASE-5": "1-2 days"
        }

        for phase in phases:
            phase_id = phase["id"]
            if phase_id in phase_days:
                estimates[phase_id] = phase_days[phase_id]
            else:
                estimates[phase_id] = "2-3 days"  # Default

        # Adjust based on complexity
        request_lower = request.lower()
        if any(kw in request_lower for kw in ["complex", "enterprise", "scale"]):
            for key in estimates:
                # Increase estimate by 50%
                estimates[key] = estimates[key].replace("days", "days (est.)")

        return estimates

    def _calculate_total_effort(self, phases: List[Dict[str, Any]]) -> str:
        """Calculate total estimated effort."""
        # Rough estimate: 2 weeks minimum + 1 week per phase beyond 5
        base_weeks = 2
        additional_weeks = max(0, len(phases) - 5)

        total_weeks = base_weeks + additional_weeks

        if total_weeks <= 2:
            return "2-3 weeks"
        elif total_weeks <= 4:
            return "1 month"
        elif total_weeks <= 8:
            return "1-2 months"
        else:
            return f"{total_weeks // 4}+ months"
