"""
Interface Agent: User liaison for autonomous system.

The Interface Agent:
- Reports system status to users
- Routes user commands to appropriate agents
- Provides human-readable summaries
- Handles user interactions
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from ..schemas.task import Task, TaskRegistry
from ..redis.coordinator import RedisCoordinator


class InterfaceAgent:
    """
    Interface Agent is the user's primary contact with the autonomous system.

    Provides:
    - Status reports
    - Command routing
    - Human-readable summaries
    - Interactive controls
    """

    def __init__(self,
                 task_registry: TaskRegistry,
                 redis_coordinator: RedisCoordinator,
                 agent_id: str = "interface"):
        """
        Initialize Interface Agent.

        Args:
            task_registry: Task registry
            redis_coordinator: Redis coordinator
            agent_id: Agent identifier
        """
        self.agent_id = agent_id
        self.registry = task_registry
        self.redis = redis_coordinator

        # Register interface agent
        self.redis.update_agent_status(
            agent_id=self.agent_id,
            status="idle",
            capabilities=["reporting", "command_routing", "user_interaction"]
        )

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.

        Returns:
            System status dictionary
        """
        all_tasks = self.registry.get_all()
        all_agents = self.redis.get_all_agents()

        # Task statistics
        task_stats = {
            "total": len(all_tasks),
            "backlog": sum(1 for t in all_tasks if t.state.value == "backlog"),
            "pending": sum(1 for t in all_tasks if t.state.value == "pending"),
            "assigned": sum(1 for t in all_tasks if t.state.value == "assigned"),
            "active": sum(1 for t in all_tasks if t.state.value == "active"),
            "done": sum(1 for t in all_tasks if t.state.value == "done"),
            "failed": sum(1 for t in all_tasks if t.state.value == "failed"),
        }

        # Agent statistics
        agent_stats = {
            "total": len(all_agents),
            "idle": sum(1 for a in all_agents if a.get("status") == "idle"),
            "busy": sum(1 for a in all_agents if a.get("status") == "busy"),
            "offline": sum(1 for a in all_agents if a.get("status") == "offline"),
        }

        # Queue statistics
        queue_length = self.redis.get_task_queue_length()
        active_tasks = self.redis.get_active_tasks()

        return {
            "timestamp": datetime.now().isoformat(),
            "tasks": task_stats,
            "agents": agent_stats,
            "queue": {
                "pending": queue_length,
                "active": len(active_tasks)
            },
            "agents_detail": all_agents
        }

    def format_status_report(self, status: Dict[str, Any] = None) -> str:
        """
        Format status report for human consumption.

        Args:
            status: Status dict (uses current if None)

        Returns:
            Formatted status report
        """
        if not status:
            status = self.get_system_status()

        lines = [
            "=" * 60,
            f"Autonomous System Status Report",
            f"Generated: {status['timestamp']}",
            "=" * 60,
            "",
            "TASKS:",
            f"  Total:    {status['tasks']['total']}",
            f"  Backlog:  {status['tasks']['backlog']}",
            f"  Pending:  {status['tasks']['pending']}",
            f"  Assigned: {status['tasks']['assigned']}",
            f"  Active:   {status['tasks']['active']}",
            f"  Done:     {status['tasks']['done']}",
            f"  Failed:   {status['tasks']['failed']}",
            "",
            "AGENTS:",
            f"  Total:    {status['agents']['total']}",
            f"  Idle:     {status['agents']['idle']}",
            f"  Busy:     {status['agents']['busy']}",
            f"  Offline:  {status['agents']['offline']}",
            "",
            "QUEUE:",
            f"  Pending:  {status['queue']['pending']}",
            f"  Active:   {status['queue']['active']}",
            "",
            "ACTIVE AGENTS:",
        ]

        for agent in status.get('agents_detail', []):
            agent_id = agent.get('agent_id', 'unknown')
            agent_status = agent.get('status', 'unknown')
            current_task = agent.get('current_task', 'None')

            lines.append(f"  {agent_id}: {agent_status}")
            if current_task and current_task != 'None':
                lines.append(f"    → Working on: {current_task}")

        lines.append("=" * 60)

        return "\n".join(lines)

    def get_task_summary(self, task_id: str) -> Optional[str]:
        """
        Get human-readable summary of a task.

        Args:
            task_id: Task ID

        Returns:
            Formatted task summary
        """
        task = self.registry.get(task_id)

        if not task:
            return f"Task {task_id} not found"

        lines = [
            f"Task: {task.title}",
            f"ID: {task.id}",
            f"State: {task.state.value}",
            f"Type: {task.type}",
            f"Priority: {task.priority}",
            "",
        ]

        if task.assignee:
            lines.append(f"Assigned to: {task.assignee}")
            if task.started_at:
                lines.append(f"Started: {task.started_at.isoformat()}")

        if task.state.value == "done" and task.completed_at:
            duration = (task.completed_at - task.started_at).total_seconds() if task.started_at else 0
            lines.append(f"Completed: {task.completed_at.isoformat()}")
            lines.append(f"Duration: {duration:.1f}s")

        if task.depends_on:
            lines.append(f"Dependencies: {', '.join(task.depends_on)}")

        if task.result:
            lines.append("")
            lines.append("Result:")
            lines.append(f"  {task.result}")

        if task.error_log:
            lines.append("")
            lines.append("Errors:")
            for error in task.error_log:
                lines.append(f"  {error}")

        return "\n".join(lines)

    def list_tasks(self, state: str = None, assignee: str = None,
                   limit: int = 20) -> List[str]:
        """
        List tasks with optional filtering.

        Args:
            state: Filter by state
            assignee: Filter by assignee
            limit: Maximum number of tasks

        Returns:
            List of formatted task summaries
        """
        tasks = self.registry.get_all()

        # Apply filters
        if state:
            tasks = [t for t in tasks if t.state.value == state]

        if assignee:
            tasks = [t for t in tasks if t.assignee == assignee]

        # Sort by priority
        tasks.sort(key=lambda t: t.priority, reverse=True)

        # Limit
        tasks = tasks[:limit]

        # Format
        return [self.get_task_summary(t.id) for t in tasks]

    def get_agent_summary(self, agent_id: str) -> Optional[str]:
        """
        Get summary of an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Formatted agent summary
        """
        agent_status = self.redis.get_agent_status(agent_id)

        if not agent_status:
            return f"Agent {agent_id} not found"

        lines = [
            f"Agent: {agent_id}",
            f"Status: {agent_status.get('status', 'unknown')}",
            f"Last seen: {agent_status.get('last_seen', 'never')}",
            f"Capabilities: {', '.join(agent_status.get('capabilities', []))}",
        ]

        current_task = agent_status.get('current_task')
        if current_task:
            lines.append(f"Current task: {current_task}")

            # Get task details
            task = self.registry.get(current_task)
            if task:
                lines.append(f"  {task.title}")

        return "\n".join(lines)

    def create_task(self, title: str, description: str = "",
                   type: str = "general", priority: int = 5) -> str:
        """
        Create a new task manually.

        Args:
            title: Task title
            description: Task description
            type: Task type
            priority: Task priority (1-10)

        Returns:
            Created task ID
        """
        task = self.registry.create(
            title=title,
            description=description,
            type=type,
            priority=priority
        )

        # Publish to Redis
        self.redis.add_to_pending_queue(task.id, task.priority)
        self.redis.publish_task({
            "task_id": task.id,
            "title": task.title,
            "type": task.type,
            "priority": task.priority,
            "timestamp": datetime.now().isoformat()
        })

        return task.id

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.

        Args:
            task_id: Task ID to cancel

        Returns:
            True if cancelled
        """
        task = self.registry.get(task_id)

        if not task:
            return False

        try:
            task.transition_to(TaskState.CANCELLED)
            self.registry.update(task)

            # Publish cancellation
            self.redis.publish_task({
                "task_id": task_id,
                "status": "cancelled",
                "timestamp": datetime.now().isoformat()
            })

            return True

        except ValueError:
            return False

    def get_recent_activity(self, limit: int = 10) -> List[str]:
        """
        Get recent system activity.

        Args:
            limit: Maximum number of events

        Returns:
            List of activity descriptions
        """
        all_tasks = self.registry.get_all()

        # Get recently updated tasks
        recent = sorted(
            all_tasks,
            key=lambda t: t.created_at or datetime.now(),
            reverse=True
        )[:limit]

        activities = []

        for task in recent:
            status = task.state.value
            time = task.created_at.strftime("%H:%M:%S") if task.created_at else "??"

            if task.assignee:
                activities.append(
                    f"[{time}] {task.id}: {status} ({task.assignee})"
                )
            else:
                activities.append(
                    f"[{time}] {task.id}: {status}"
                )

        return activities
