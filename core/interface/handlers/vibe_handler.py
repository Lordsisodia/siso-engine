"""
Vibe Kanban Handler for Agent Output Bus

Receives agent outputs and creates/updates tasks in Vibe Kanban.
Maps agent output status to Kanban task status.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import from parent directory
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from AgentOutputBus import OutputHandler, HandlerResult, OutputEvent, OutputStatus

# Try to import Vibe Kanban client
try:
    from vibe_kanban_integration import (
        VibeKanbanClient,
        TaskStatus,
        Repository
    )
    VIBE_KANBAN_AVAILABLE = True
except ImportError:
    VIBE_KANBAN_AVAILABLE = False
    logging.warning("vibe_kanban_integration not found - VibeKanbanHandler will be disabled")

logger = logging.getLogger(__name__)


class VibeKanbanHandler(OutputHandler):
    """
    Handler for integrating agent outputs with Vibe Kanban.

    Creates/updates Kanban tasks based on agent output:
    - success → Mark task as done/in-review
    - partial → Mark task as in-review with notes
    - failed → Mark task as todo with error details
    """

    # Status mapping: agent status → Kanban status
    # Will be set in __init__ if Vibe Kanban is available
    STATUS_MAP = {}

    def __init__(
        self,
        vibe_kanban_url: str = "http://127.0.0.1:57276",
        project_id: str = "48ec7737-b706-4817-b86c-5786163a0139",
        auto_create_tasks: bool = True,
        update_existing: bool = True
    ):
        """
        Initialize Vibe Kanban handler.

        Args:
            vibe_kanban_url: Vibe Kanban API URL
            project_id: Default project UUID for creating tasks
            auto_create_tasks: Create new tasks for outputs without task_id
            update_existing: Update existing tasks if task_id found in metadata
        """
        super().__init__("VibeKanbanHandler")

        if not VIBE_KANBAN_AVAILABLE:
            logger.warning("VibeKanbanHandler initialized but Vibe Kanban client not available")
            self.client = None
        else:
            self.client = VibeKanbanClient(vibe_kanban_url)
            # Set up status mapping now that TaskStatus is available
            VibeKanbanHandler.STATUS_MAP = {
                OutputStatus.SUCCESS: TaskStatus.DONE,
                OutputStatus.PARTIAL: TaskStatus.IN_REVIEW,
                OutputStatus.FAILED: TaskStatus.TODO,
            }

        self.project_id = project_id
        self.auto_create_tasks = auto_create_tasks
        self.update_existing = update_existing

    def handle(self, event: OutputEvent) -> HandlerResult:
        """
        Handle agent output event.

        Args:
            event: Parsed agent output event

        Returns:
            HandlerResult with success status and details
        """
        if not self.client:
            return HandlerResult(
                success=False,
                message="Vibe Kanban client not available",
                data=None
            )

        try:
            # Check if event references an existing task
            task_id = event.metadata.get('vibe_kanban_task_id')

            if task_id and self.update_existing:
                return self._update_existing_task(task_id, event)
            elif self.auto_create_tasks:
                return self._create_new_task(event)
            else:
                return HandlerResult(
                    success=False,
                    message="No task_id in metadata and auto_create_tasks is disabled",
                    data=None
                )

        except Exception as e:
            logger.error(f"VibeKanbanHandler error: {e}")
            return HandlerResult(
                success=False,
                message=f"Failed to handle event: {e}",
                data=None
            )

    def _update_existing_task(self, task_id: str, event: OutputEvent) -> HandlerResult:
        """Update an existing Vibe Kanban task based on agent output."""
        # Map agent status to Kanban status
        kanban_status = self.STATUS_MAP.get(event.status, TaskStatus.IN_REVIEW)

        # Update task status
        updated_task = self.client.update_task_status(task_id, kanban_status)

        # Build description with deliverables and next steps
        description = self._build_task_description(event)

        data = {
            "task_id": task_id,
            "kanban_status": kanban_status.value,
            "agent_status": event.status.value,
            "deliverables_count": len(event.deliverables),
            "next_steps_count": len(event.next_steps)
        }

        logger.info(f"Updated Vibe Kanban task {task_id} to status {kanban_status.value}")

        return HandlerResult(
            success=True,
            message=f"Updated task {task_id} to {kanban_status.value}",
            data=data
        )

    def _create_new_task(self, event: OutputEvent) -> HandlerResult:
        """Create a new Vibe Kanban task from agent output."""
        # Generate task title from summary
        title = self._generate_task_title(event)

        # Build description
        description = self._build_task_description(event)

        # Create task
        task = self.client.create_task(
            project_id=self.project_id,
            title=title,
            description=description
        )

        task_id = task["id"]

        # Set initial status
        kanban_status = self.STATUS_MAP.get(event.status, TaskStatus.TODO)
        self.client.update_task_status(task_id, kanban_status)

        data = {
            "task_id": task_id,
            "kanban_status": kanban_status.value,
            "agent_status": event.status.value,
            "title": title
        }

        logger.info(f"Created Vibe Kanban task {task_id}: {title}")

        return HandlerResult(
            success=True,
            message=f"Created task {task_id}: {title}",
            data=data
        )

    def _generate_task_title(self, event: OutputEvent) -> str:
        """Generate a task title from agent output event."""
        # Start with agent name and summary
        title = f"[{event.agent_name}] {event.summary}"

        # Truncate if too long (Vibe Kanban may have limits)
        max_length = 100
        if len(title) > max_length:
            title = title[:max_length - 3] + "..."

        return title

    def _build_task_description(self, event: OutputEvent) -> str:
        """Build a markdown description for the Kanban task."""
        lines = [
            f"## {event.summary}",
            "",
            f"**Agent:** {event.agent_name}",
            f"**Task ID:** {event.task_id}",
            f"**Status:** {event.status.value}",
            f"**Timestamp:** {event.timestamp.isoformat()}",
            "",
        ]

        # Add deliverables section
        if event.deliverables:
            lines.extend([
                "### Deliverables",
                ""
            ])
            for deliverable in event.deliverables:
                lines.append(f"- {deliverable}")
            lines.append("")

        # Add next steps section
        if event.next_steps:
            lines.extend([
                "### Next Steps",
                ""
            ])
            for i, step in enumerate(event.next_steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        # Add metadata section
        if event.metadata:
            lines.extend([
                "### Metadata",
                ""
            ])
            for key, value in event.metadata.items():
                if key not in ['agent', 'task_id']:
                    lines.append(f"- **{key}:** {value}")
            lines.append("")

        # Add human content
        if event.human_content:
            lines.extend([
                "---",
                "",
                "### Details",
                "",
                event.human_content
            ])

        return "\n".join(lines)


def create_vibe_handler(
    vibe_kanban_url: str = "http://127.0.0.1:57276",
    project_id: str = "48ec7737-b706-4817-b86c-5786163a0139"
) -> Optional[VibeKanbanHandler]:
    """
    Convenience function to create Vibe Kanban handler.

    Returns None if Vibe Kanban client is not available.
    """
    if not VIBE_KANBAN_AVAILABLE:
        logger.warning("Cannot create VibeKanbanHandler - vibe_kanban_integration not found")
        return None

    return VibeKanbanHandler(
        vibe_kanban_url=vibe_kanban_url,
        project_id=project_id
    )
