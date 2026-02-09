"""
Task Router for Blackbox5

Intelligently routes tasks to appropriate agents based on
capabilities, complexity, and workload.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from agents.framework.base_agent import BaseAgent, AgentTask
from routing.complexity import TaskComplexityAnalyzer, ComplexityLevel

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Agent type categories."""
    SPECIALIST = "specialist"
    GENERALIST = "generalist"
    ORCHESTRATOR = "orchestrator"
    ANY = "any"


@dataclass
class AgentCapabilities:
    """
    Describes an agent's capabilities.

    Attributes:
        name: Agent name
        agent_type: Type of agent
        capabilities: List of capability strings
        current_tasks: Number of tasks currently being handled
        max_tasks: Maximum concurrent tasks
        avg_task_time: Average time to complete a task
        success_rate: Task success rate (0-1)
    """

    name: str
    agent_type: AgentType
    capabilities: List[str]
    current_tasks: int = 0
    max_tasks: int = 5
    avg_task_time: float = 1.0
    success_rate: float = 1.0

    @property
    def available(self) -> bool:
        """Check if agent is available for new tasks."""
        return self.current_tasks < self.max_tasks

    @property
    def utilization(self) -> float:
        """Get agent utilization (0-1)."""
        return self.current_tasks / self.max_tasks

    def can_handle(self, required_capabilities: Set[str]) -> bool:
        """
        Check if agent has required capabilities.

        Args:
            required_capabilities: Set of required capability strings

        Returns:
            True if agent has all required capabilities
        """
        if not required_capabilities:
            return True

        agent_caps = set(cap.lower() for cap in self.capabilities)
        required = set(req.lower() for req in required_capabilities)

        return required.issubset(agent_caps)


@dataclass
class Task:
    """
    Represents a task to be routed.

    Attributes:
        id: Unique task identifier
        description: Task description
        type: Task type (e.g., "implementation", "research")
        priority: Task priority (1-10, higher is more important)
        required_capabilities: Set of required capabilities
        complexity: Task complexity level (optional)
        estimated_duration: Estimated time in minutes
        metadata: Additional task metadata
    """

    id: str
    description: str
    type: str = "general"
    priority: int = 5
    required_capabilities: Set[str] = field(default_factory=set)
    complexity: Optional[ComplexityLevel] = None
    estimated_duration: float = 10.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    """
    Represents a routing decision.

    Attributes:
        agent_name: Name of selected agent
        confidence: Confidence in this decision (0-1)
        reasoning: Human-readable explanation
        alternative_agents: List of alternative agents
    """

    agent_name: str
    confidence: float
    reasoning: str
    alternative_agents: List[str] = field(default_factory=list)


class TaskRouter:
    """
    Routes tasks to appropriate agents.

    Uses multiple strategies:
    1. Capability matching
    2. Workload balancing
    3. Performance-based routing
    4. Complexity-based routing
    """

    def __init__(
        self,
        complexity_analyzer: Optional[TaskComplexityAnalyzer] = None,
        event_bus: Optional[Any] = None
    ):
        """
        Initialize the task router.

        Args:
            complexity_analyzer: Optional complexity analyzer
            event_bus: Optional event bus for emitting events
        """
        self.complexity_analyzer = complexity_analyzer or TaskComplexityAnalyzer()
        self._event_bus = event_bus
        self._agents: Dict[str, AgentCapabilities] = {}
        self._task_history: List[Tuple[str, str, bool]] = []
        self._lock = asyncio.Lock()

    async def register_agent(
        self,
        agent: BaseAgent,
        agent_type: AgentType = AgentType.SPECIALIST
    ) -> None:
        """
        Register an agent with the router.

        Args:
            agent: Agent instance
            agent_type: Type of agent
        """
        caps = AgentCapabilities(
            name=agent.name,
            agent_type=agent_type,
            capabilities=agent.config.capabilities,
            max_tasks=5,
        )

        async with self._lock:
            self._agents[agent.name] = caps

        logger.info(
            f"Registered agent: {agent.name} "
            f"({len(caps.capabilities)} capabilities)"
        )

    async def unregister_agent(self, agent_name: str) -> None:
        """
        Unregister an agent.

        Args:
            agent_name: Name of agent to unregister
        """
        async with self._lock:
            if agent_name in self._agents:
                del self._agents[agent_name]

        logger.info(f"Unregistered agent: {agent_name}")

    async def route(self, task: Task) -> RoutingDecision:
        """
        Route a task to the best available agent.

        Args:
            task: Task to route

        Returns:
            RoutingDecision with selected agent

        Raises:
            ValueError: No suitable agent available
        """
        if task.complexity is None:
            complexity_score = self.complexity_analyzer.analyze(task.description)
            task.complexity = complexity_score.level

        candidates = await self._get_candidates(task)

        if not candidates:
            raise ValueError(
                f"No available agents for task with requirements: "
                f"{task.required_capabilities}"
            )

        scored_candidates = await self._score_candidates(task, candidates)
        best_agent, score = scored_candidates[0]

        confidence = min(1.0, score / 100.0)
        alternatives = [agent for agent, _ in scored_candidates[1:4]]

        reasoning = self._build_reasoning(task, best_agent, score)

        return RoutingDecision(
            agent_name=best_agent,
            confidence=confidence,
            reasoning=reasoning,
            alternative_agents=alternatives,
        )

    async def _get_candidates(self, task: Task) -> List[str]:
        """Get list of candidate agents for a task."""
        async with self._lock:
            candidates = []
            for name, caps in self._agents.items():
                if not caps.available:
                    continue

                # If no capabilities required, all available agents are candidates
                if not task.required_capabilities:
                    candidates.append(name)
                    continue

                # Check if agent has ANY matching capability (partial match)
                agent_caps = set(cap.lower() for cap in caps.capabilities)
                required = set(req.lower() for req in task.required_capabilities)
                intersection = agent_caps & required

                # Include agents that have at least one matching capability
                # or use can_handle for exact match (all required capabilities)
                if intersection or required.issubset(agent_caps):
                    candidates.append(name)

        return candidates

    async def _score_candidates(
        self,
        task: Task,
        candidates: List[str]
    ) -> List[Tuple[str, float]]:
        """Score candidates for a task."""
        async with self._lock:
            agent_caps = {name: self._agents[name] for name in candidates}

        scores = []
        for name, caps in agent_caps.items():
            score = await self._calculate_score(task, caps)
            scores.append((name, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    async def _calculate_score(
        self,
        task: Task,
        caps: AgentCapabilities
    ) -> float:
        """Calculate routing score for an agent."""
        score = 0.0

        if task.required_capabilities:
            matched = len(task.required_capabilities & set(caps.capabilities))
            total = len(task.required_capabilities)
            score += (matched / total) * 40
        else:
            score += 20

        if caps.available:
            availability_score = (1 - caps.utilization) * 30
            score += availability_score

        score += caps.success_rate * 20
        score += (1 - caps.utilization) * 10

        return score

    def _build_reasoning(
        self,
        task: Task,
        agent_name: str,
        score: float
    ) -> str:
        """Build human-readable reasoning for routing decision."""
        parts = [
            f"Selected {agent_name} (score: {score:.1f}/100)",
        ]

        if task.required_capabilities:
            parts.append(f"Required capabilities: {', '.join(task.required_capabilities)}")

        if task.complexity:
            parts.append(f"Complexity: {task.complexity.value}")

        parts.append(f"Priority: {task.priority}/10")

        return ". ".join(parts) + "."

    async def update_agent_status(
        self,
        agent_name: str,
        task_change: int,
        success: Optional[bool] = None
    ) -> None:
        """Update agent status after task assignment/completion."""
        async with self._lock:
            if agent_name not in self._agents:
                return

            caps = self._agents[agent_name]
            caps.current_tasks += task_change

            if success is not None:
                alpha = 0.2
                caps.success_rate = (
                    alpha * (1.0 if success else 0.0) +
                    (1 - alpha) * caps.success_rate
                )

    async def record_task_completion(
        self,
        agent_name: str,
        task_id: str,
        success: bool
    ) -> None:
        """
        Record task completion for statistics tracking.

        Args:
            agent_name: Name of agent that processed the task
            task_id: ID of the completed task
            success: Whether the task completed successfully
        """
        async with self._lock:
            # Add to task history
            self._task_history.append((agent_name, task_id, success))

            # Update agent state - decrement current tasks
            if agent_name in self._agents:
                caps = self._agents[agent_name]
                caps.current_tasks = max(0, caps.current_tasks - 1)

                # Update success rate with exponential moving average
                alpha = 0.2
                caps.success_rate = (
                    alpha * (1.0 if success else 0.0) +
                    (1 - alpha) * caps.success_rate
                )

            # Keep task history manageable (last 1000 tasks)
            if len(self._task_history) > 1000:
                self._task_history = self._task_history[-1000:]

    async def get_statistics(self) -> Dict[str, Any]:
        """Get router statistics."""
        async with self._lock:
            return {
                "total_agents": len(self._agents),
                "available_agents": sum(
                    1 for caps in self._agents.values() if caps.available
                ),
                "total_tasks_processed": len(self._task_history),
                "agent_status": {
                    name: {
                        "available": caps.available,
                        "utilization": caps.utilization,
                        "current_tasks": caps.current_tasks,
                        "success_rate": caps.success_rate,
                    }
                    for name, caps in self._agents.items()
                },
            }
