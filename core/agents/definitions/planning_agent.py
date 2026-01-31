"""
Planning Agent for Blackbox 5

This agent converts user requests into structured project plans including:
- Requirements analysis
- PRD (Product Requirements Document) generation
- Epic creation
- Task breakdown
- Vibe Kanban integration
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from .core.base_agent import BaseAgent, AgentConfig, AgentTask, AgentResult

logger = logging.getLogger(__name__)


class PlanningAgent(BaseAgent):
    """
    Planning Agent - Converts user requests into structured plans

    Workflow:
    1. Parse user request
    2. Analyze requirements
    3. Generate PRD (Product Requirements Document)
    4. Break into Epics
    5. Break Epics into Tasks
    6. Create Vibe Kanban cards (when configured)
    7. Assign to agents
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize the PlanningAgent.

        Args:
            config: Agent configuration
        """
        super().__init__(config)
        self.vibe_kanban = None  # VibeKanbanManager (optional)
        self._bmad_enabled = config.metadata.get("bmad_enabled", True)

    async def execute(self, task: AgentTask) -> AgentResult:
        """
        Execute a planning task.

        Args:
            task: The planning task to execute

        Returns:
            AgentResult containing the planning artifacts
        """
        thinking_steps = await self.think(task)

        request = task.description
        context = task.context or {}

        try:
            # Step 1: Analyze requirements
            requirements = await self._analyze_requirements(request, context)

            # Step 2: Generate PRD
            prd = await self._generate_prd(requirements, context)

            # Step 3: Create Epics
            epics = await self._create_epics(prd, context)

            # Step 4: Break into Tasks
            tasks = await self._breakdown_tasks(epics, context)

            # Step 5: Create Vibe Kanban cards (if configured)
            kanban_results = None
            if self.vibe_kanban and context.get("create_kanban_cards", False):
                kanban_results = await self._create_kanban_cards(tasks, context)

            # Step 6: Assign to agents
            assignments = await self._assign_agents(tasks, context)

            # Build output summary
            output = self._format_output(prd, epics, tasks, assignments)

            return AgentResult(
                success=True,
                output=output,
                artifacts={
                    "requirements": requirements,
                    "prd": prd,
                    "epics": epics,
                    "tasks": tasks,
                    "assignments": assignments,
                    "kanban_results": kanban_results,
                },
                thinking_steps=thinking_steps,
                metadata={
                    "agent_name": self.name,
                    "agent_role": self.role,
                    "task_type": task.type,
                    "epic_count": len(epics),
                    "task_count": len(tasks),
                }
            )

        except Exception as e:
            logger.error(f"PlanningAgent failed to execute task {task.id}: {e}")
            return AgentResult(
                success=False,
                output="",
                error=str(e),
                thinking_steps=thinking_steps,
            )

    async def think(self, task: AgentTask) -> List[str]:
        """
        Generate thinking steps for the planning task.

        Args:
            task: The task to think about

        Returns:
            List of thinking step descriptions
        """
        return [
            "Understanding planning requirements from user request",
            "Analyzing project scope and constraints",
            "Identifying key stakeholders and success criteria",
            "Generating structured Product Requirements Document",
            "Breaking down PRD into manageable epics",
            "Decomposing epics into actionable tasks",
            "Assigning tasks to appropriate agent specialists",
        ]

    # ========== Planning Methods ==========

    async def _analyze_requirements(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user request to extract requirements.

        Args:
            request: User's request
            context: Additional context

        Returns:
            Dictionary containing analyzed requirements
        """
        # In a full implementation, this would use an LLM
        # For now, provide structured placeholder
        return {
            "original_request": request,
            "project_type": self._infer_project_type(request),
            "complexity": self._infer_complexity(request),
            "key_features": self._extract_features(request),
            "constraints": context.get("constraints", []),
            "success_criteria": context.get("success_criteria", []),
        }

    async def _generate_prd(self, requirements: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a Product Requirements Document.

        Args:
            requirements: Analyzed requirements
            context: Additional context

        Returns:
            PRD document structure
        """
        return {
            "title": self._generate_title(requirements["original_request"]),
            "version": "1.0",
            "date": datetime.now().isoformat(),
            "overview": requirements["original_request"],
            "project_type": requirements["project_type"],
            "complexity": requirements["complexity"],
            "objectives": self._generate_objectives(requirements),
            "key_features": requirements["key_features"],
            "constraints": requirements["constraints"],
            "success_criteria": requirements["success_criteria"],
            "stakeholders": context.get("stakeholders", ["Product Team", "Development Team"]),
        }

    async def _create_epics(self, prd: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Break PRD into epics.

        Args:
            prd: Product Requirements Document
            context: Additional context

        Returns:
            List of epic definitions
        """
        # Default epic breakdown pattern
        epics = []

        # Common epic patterns
        if prd["project_type"] in ["web_application", "api"]:
            epics.extend([
                {
                    "id": "EPIC-001",
                    "title": "Foundation & Infrastructure",
                    "description": "Set up project structure, development environment, and core infrastructure",
                    "priority": "high",
                    "estimated_effort": "2-3 days",
                },
                {
                    "id": "EPIC-002",
                    "title": "Core Features Implementation",
                    "description": "Implement the primary functionality of the system",
                    "priority": "high",
                    "estimated_effort": "5-7 days",
                },
                {
                    "id": "EPIC-003",
                    "title": "Integration & Testing",
                    "description": "Integrate components and perform comprehensive testing",
                    "priority": "medium",
                    "estimated_effort": "3-4 days",
                },
            ])

        # Add custom epics from context if provided
        if context.get("custom_epics"):
            epics.extend(context["custom_epics"])

        return epics

    async def _breakdown_tasks(self, epics: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Break epics into actionable tasks.

        Args:
            epics: List of epic definitions
            context: Additional context

        Returns:
            List of task definitions
        """
        tasks = []
        task_counter = 1

        for epic in epics:
            # Generate tasks for each epic
            epic_tasks = self._generate_tasks_for_epic(epic, task_counter)
            tasks.extend(epic_tasks)
            task_counter += len(epic_tasks)

        return tasks

    async def _create_kanban_cards(self, tasks: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create Vibe Kanban cards for tasks.

        Args:
            tasks: List of task definitions
            context: Additional context

        Returns:
            Kanban creation results
        """
        if not self.vibe_kanban:
            return {"status": "skipped", "reason": "Vibe Kanban not configured"}

        # This would integrate with VibeKanbanManager
        # For now, return placeholder
        return {
            "status": "not_implemented",
            "message": "Vibe Kanban integration pending"
        }

    async def _assign_agents(self, tasks: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, str]:
        """
        Assign tasks to appropriate agents.

        Args:
            tasks: List of task definitions
            context: Additional context

        Returns:
            Dictionary mapping task IDs to agent names
        """
        assignments = {}

        for task in tasks:
            # Simple assignment logic based on task type
            task_type = task.get("type", "general").lower()

            if any(kw in task_type for kw in ["design", "architecture"]):
                assignments[task["id"]] = "architect"
            elif any(kw in task_type for kw in ["backend", "api", "server"]):
                assignments[task["id"]] = "backend-developer"
            elif any(kw in task_type for kw in ["frontend", "ui", "ux"]):
                assignments[task["id"]] = "frontend-developer"
            elif any(kw in task_type for kw in ["test", "qa"]):
                assignments[task["id"]] = "qa-engineer"
            elif any(kw in task_type for kw in ["data", "database"]):
                assignments[task["id"]] = "data-specialist"
            else:
                assignments[task["id"]] = "developer"

        return assignments

    # ========== Helper Methods ==========

    def _infer_project_type(self, request: str) -> str:
        """Infer project type from request."""
        request_lower = request.lower()

        if any(kw in request_lower for kw in ["api", "rest", "graphql", "endpoint"]):
            return "api"
        elif any(kw in request_lower for kw in ["web app", "website", "frontend", "fullstack"]):
            return "web_application"
        elif any(kw in request_lower for kw in ["cli", "command line", "script"]):
            return "cli_tool"
        elif any(kw in request_lower for kw in ["library", "package", "module"]):
            return "library"
        else:
            return "general"

    def _infer_complexity(self, request: str) -> str:
        """Infer complexity from request."""
        # Simple heuristic based on request length
        word_count = len(request.split())

        if word_count < 20:
            return "low"
        elif word_count < 50:
            return "medium"
        else:
            return "high"

    def _extract_features(self, request: str) -> List[str]:
        """Extract key features from request."""
        # In full implementation, use NLP/LLM
        # For now, return placeholder
        return ["Feature 1 (pending LLM implementation)", "Feature 2 (pending LLM implementation)"]

    def _generate_title(self, request: str) -> str:
        """Generate a project title from request."""
        # Use first 50 chars as title
        if len(request) <= 50:
            return request
        return request[:47] + "..."

    def _generate_objectives(self, requirements: Dict[str, Any]) -> List[str]:
        """Generate project objectives."""
        return [
            f"Build {requirements['project_type'].replace('_', ' ').title()}",
            "Ensure high code quality and maintainability",
            "Follow best practices and design patterns",
        ]

    def _generate_tasks_for_epic(self, epic: Dict[str, Any], start_id: int) -> List[Dict[str, Any]]:
        """Generate tasks for an epic."""
        tasks = []

        # Common task patterns based on epic title
        epic_lower = epic["title"].lower()

        if "foundation" in epic_lower or "infrastructure" in epic_lower:
            tasks.extend([
                {
                    "id": f"TASK-{start_id:03d}",
                    "title": "Set up project structure",
                    "description": "Initialize project with proper directory structure",
                    "type": "setup",
                    "priority": "high",
                    "epic_id": epic["id"],
                },
                {
                    "id": f"TASK-{start_id+1:03d}",
                    "title": "Configure development environment",
                    "description": "Set up linting, formatting, and testing frameworks",
                    "type": "setup",
                    "priority": "high",
                    "epic_id": epic["id"],
                },
            ])
        elif "core" in epic_lower or "implementation" in epic_lower:
            tasks.extend([
                {
                    "id": f"TASK-{start_id:03d}",
                    "title": "Implement core functionality",
                    "description": "Build the primary features",
                    "type": "development",
                    "priority": "high",
                    "epic_id": epic["id"],
                },
                {
                    "id": f"TASK-{start_id+1:03d}",
                    "title": "Implement data models",
                    "description": "Define and implement data structures",
                    "type": "development",
                    "priority": "high",
                    "epic_id": epic["id"],
                },
            ])
        elif "integration" in epic_lower or "testing" in epic_lower:
            tasks.extend([
                {
                    "id": f"TASK-{start_id:03d}",
                    "title": "Write integration tests",
                    "description": "Create comprehensive integration tests",
                    "type": "testing",
                    "priority": "medium",
                    "epic_id": epic["id"],
                },
                {
                    "id": f"TASK-{start_id+1:03d}",
                    "title": "Perform end-to-end testing",
                    "description": "Test complete workflows",
                    "type": "testing",
                    "priority": "medium",
                    "epic_id": epic["id"],
                },
            ])

        return tasks

    def _format_output(
        self,
        prd: Dict[str, Any],
        epics: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
        assignments: Dict[str, str]
    ) -> str:
        """Format planning output as readable text."""
        lines = [
            f"# Planning Complete: {prd['title']}",
            "",
            "## Product Requirements Document",
            f"- **Type:** {prd['project_type']}",
            f"- **Complexity:** {prd['complexity']}",
            f"- **Key Features:** {len(prd['key_features'])}",
            "",
            "## Epics",
        ]

        for epic in epics:
            lines.append(f"- {epic['id']}: {epic['title']} ({epic['priority']} priority)")

        lines.extend([
            "",
            "## Tasks",
            f"- **Total Tasks:** {len(tasks)}",
            f"- **Assigned:** {len(assignments)}",
            "",
        ])

        return "\n".join(lines)

    def set_vibe_kanban(self, vibe_kanban_manager: Any) -> None:
        """
        Set the Vibe Kanban manager for card creation.

        Args:
            vibe_kanban_manager: VibeKanbanManager instance
        """
        self.vibe_kanban = vibe_kanban_manager
        logger.info(f"Vibe Kanban manager configured for {self.name}")
