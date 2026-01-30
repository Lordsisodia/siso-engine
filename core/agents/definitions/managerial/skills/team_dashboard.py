#!/usr/bin/env python3
"""
Team Monitoring Dashboard Skill

This skill provides real-time monitoring and visualization of:
- Active agents and their progress
- Task queues and bottlenecks
- Resource utilization
- Team performance metrics
- Alerts and notifications
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
import json

from ..skills.vibe_kanban_manager import (
    VibeKanbanManager,
    TaskStatus,
    AgentState
)
from ..memory.management_memory import ManagementMemory, get_management_memory


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """A dashboard alert"""
    level: AlertLevel
    message: str
    task_id: Optional[str] = None
    timestamp: str = None
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.details is None:
            self.details = {}


@dataclass
class AgentStatus:
    """Real-time agent status"""
    task_id: str
    task_title: str
    status: TaskStatus
    runtime: Optional[float] = None  # minutes
    completion_pct: int = 0
    files_modified: int = 0
    files_created: int = 0
    errors: List[str] = None
    last_activity: Optional[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class QueueStatus:
    """Task queue status"""
    pending: int = 0
    in_progress: int = 0
    in_review: int = 0
    blocked: int = 0
    estimated_wait_time: Optional[float] = None  # minutes


@dataclass
class ResourceMetrics:
    """Resource utilization metrics"""
    active_agents: int = 0
    total_workspaces: int = 0
    memory_usage_mb: Optional[float] = None
    disk_usage_gb: Optional[float] = None


class TeamDashboard:
    """
    Real-time team monitoring dashboard.

    Provides comprehensive visibility into all aspects of
    agent team operations.
    """

    def __init__(
        self,
        vkb_manager: Optional[VibeKanbanManager] = None,
        memory: Optional[ManagementMemory] = None
    ):
        """
        Initialize dashboard

        Args:
            vkb_manager: Vibe Kanban manager
            memory: Management memory
        """
        self.vkb = vkb_manager or VibeKanbanManager()
        self.memory = memory or get_management_memory()
        self._alerts: List[Alert] = []

    # =========================================================================
    # DASHBOARD SNAPSHOT
    # =========================================================================

    def get_snapshot(self) -> Dict[str, Any]:
        """
        Get a complete dashboard snapshot

        Returns:
            Dict with all dashboard data
        """
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents": self.get_agent_statuses(),
            "queues": self.get_queue_status(),
            "resources": self.get_resource_metrics(),
            "alerts": self.get_active_alerts(),
            "metrics": self.get_performance_metrics()
        }

    # =========================================================================
    # AGENT MONITORING
    # =========================================================================

    def get_agent_statuses(self) -> List[AgentStatus]:
        """Get status of all agents"""
        agents = []
        agent_states = self.vkb.get_all_agent_states()

        for task_id, agent_state in agent_states.items():
            task = self.vkb.get_task(task_id)

            # Calculate runtime
            runtime = None
            if agent_state.started_at:
                started = datetime.fromisoformat(agent_state.started_at.replace('Z', '+00:00'))
                runtime = (datetime.now(timezone.utc) - started).total_seconds() / 60

            # Get performance data
            perf = self.memory.get_agent_performance(task_id)

            status = AgentStatus(
                task_id=task_id,
                task_title=agent_state.task_title,
                status=agent_state.status,
                runtime=runtime,
                completion_pct=agent_state.completion_percentage,
                files_modified=perf.files_modified if perf else 0,
                files_created=perf.files_created if perf else 0,
                errors=perf.errors if perf else [],
                last_activity=agent_state.last_activity
            )

            agents.append(status)

        return agents

    def get_active_agents(self) -> List[AgentStatus]:
        """Get only active (in-progress) agents"""
        return [
            agent for agent in self.get_agent_statuses()
            if agent.status == TaskStatus.IN_PROGRESS
        ]

    def get_stuck_agents(self, timeout_minutes: int = 60) -> List[AgentStatus]:
        """
        Get agents that appear stuck

        Args:
            timeout_minutes: Minutes of inactivity to consider stuck

        Returns:
            List of stuck agents
        """
        stuck = []
        threshold = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)

        for agent in self.get_active_agents():
            if agent.last_activity:
                last_active = datetime.fromisoformat(agent.last_activity.replace('Z', '+00:00'))
                if last_active < threshold:
                    stuck.append(agent)

        return stuck

    # =========================================================================
    # QUEUE MONITORING
    # =========================================================================

    def get_queue_status(self) -> QueueStatus:
        """Get task queue status"""
        tasks = self.vkb.list_tasks()

        queue = QueueStatus()

        for task in tasks:
            if task.status == TaskStatus.TODO:
                # Check if blocked
                if self.vkb.get_blockers(task.id):
                    queue.blocked += 1
                else:
                    queue.pending += 1
            elif task.status == TaskStatus.IN_PROGRESS:
                queue.in_progress += 1
            elif task.status == TaskStatus.IN_REVIEW:
                queue.in_review += 1

        return queue

    def get_blocked_tasks(self) -> List[Dict[str, Any]]:
        """Get all blocked tasks with their blockers"""
        blocked = []
        tasks = self.vkb.list_tasks(status=TaskStatus.TODO)

        for task in tasks:
            blockers = self.vkb.get_blockers(task.id)
            if blockers:
                blocked.append({
                    "task_id": task.id,
                    "title": task.title,
                    "blockers": [
                        {
                            "task_id": b,
                            "title": self.vkb.get_task(b).title,
                            "status": self.vkb.get_task(b).status.value
                        }
                        for b in blockers
                    ]
                })

        return blocked

    def get_ready_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks ready to start (not blocked)"""
        ready = []
        tasks = self.vkb.list_tasks(status=TaskStatus.TODO)

        for task in tasks:
            if not self.vkb.get_blockers(task.id):
                ready.append({
                    "task_id": task.id,
                    "title": task.title,
                    "priority": "normal"  # Could be extended
                })

        return ready

    # =========================================================================
    # RESOURCE MONITORING
    # =========================================================================

    def get_resource_metrics(self) -> ResourceMetrics:
        """Get resource utilization metrics"""
        metrics = ResourceMetrics()

        # Count active agents
        metrics.active_agents = len(self.get_active_agents())

        # Count total workspaces (approximate)
        try:
            import subprocess
            result = subprocess.check_output(
                ["git", "worktree", "list"],
                text=True,
                cwd=self.vkb.repo_path
            )
            # Subtract 1 for main
            metrics.total_workspaces = max(0, len(result.strip().split('\n')) - 1)
        except:
            pass

        return metrics

    # =========================================================================
    # PERFORMANCE METRICS
    # =========================================================================

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get team performance metrics"""
        vkb_metrics = self.vkb.get_metrics()
        agent_stats = self.memory.get_agent_stats()

        return {
            "tasks": {
                "total": vkb_metrics.total_tasks,
                "in_progress": vkb_metrics.in_progress,
                "in_review": vkb_metrics.in_review,
                "completed": vkb_metrics.completed,
                "failed": vkb_metrics.failed,
                "blocked": vkb_metrics.blocked
            },
            "agents": agent_stats,
            "success_rate": (
                vkb_metrics.completed / vkb_metrics.total_tasks * 100
                if vkb_metrics.total_tasks > 0 else 0
            )
        }

    def get_metrics_trend(
        self,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get metrics trend over time

        Args:
            hours: Number of hours to look back

        Returns:
            List of metric snapshots
        """
        history = self.memory.get_metrics_history(limit=1000)

        # Filter by time
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        filtered = [
            m for m in history
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]

        return filtered

    # =========================================================================
    # ALERTS
    # =========================================================================

    def generate_alerts(self) -> List[Alert]:
        """Generate alerts based on current state"""
        alerts = []

        # Check for stuck agents
        stuck = self.get_stuck_agents()
        for agent in stuck:
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                message=f"Agent may be stuck: {agent.task_title}",
                task_id=agent.task_id,
                details={
                    "runtime_minutes": agent.runtime,
                    "last_activity": agent.last_activity
                }
            ))

        # Check for excessive blocking
        blocked = self.get_blocked_tasks()
        if len(blocked) > 5:
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                message=f"High number of blocked tasks: {len(blocked)}",
                details={"blocked_tasks": len(blocked)}
            ))

        # Check for queue backup
        queue = self.get_queue_status()
        if queue.pending > 10:
            alerts.append(Alert(
                level=AlertLevel.INFO,
                message=f"Task queue backup: {queue.pending} pending",
                details={"pending": queue.pending}
            ))

        # Check for failed tasks
        metrics = self.vkb.get_metrics()
        if metrics.failed > 0:
            alerts.append(Alert(
                level=AlertLevel.CRITICAL,
                message=f"Failed tasks detected: {metrics.failed}",
                details={"failed_count": metrics.failed}
            ))

        return alerts

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        # Generate fresh alerts
        self._alerts = self.generate_alerts()
        return self._alerts

    def clear_alerts(self):
        """Clear all alerts"""
        self._alerts = []

    # =========================================================================
    # DASHBOARD RENDERING
    # =========================================================================

    def render_text(self) -> str:
        """
        Render dashboard as text

        Returns:
            Formatted text dashboard
        """
        snapshot = self.get_snapshot()

        lines = [
            "╔" + "═" * 78 + "╗",
            "║" + " " * 20 + "BLACKBOX5 TEAM DASHBOARD" + " " * 39 + "║",
            "╚" + "═" * 78 + "╝",
            "",
            f"Timestamp: {snapshot['timestamp']}",
            ""
        ]

        # Metrics
        metrics = snapshot["metrics"]
        lines.append("📊 METRICS")
        lines.append("-" * 80)
        lines.append(f"  Tasks: {metrics['tasks']['total']} total | "
                    f"{metrics['tasks']['in_progress']} in progress | "
                    f"{metrics['tasks']['in_review']} in review | "
                    f"{metrics['tasks']['completed']} completed")
        lines.append(f"  Success Rate: {metrics['success_rate']:.1f}%")
        lines.append("")

        # Active Agents
        agents = snapshot["agents"]
        active = [a for a in agents if a.status == TaskStatus.IN_PROGRESS]
        lines.append(f"🤖 ACTIVE AGENTS ({len(active)})")
        lines.append("-" * 80)

        if active:
            for agent in active:
                lines.append(f"  • {agent.task_title}")
                lines.append(f"    Runtime: {agent.runtime:.1f}min | "
                            f"Files: {agent.files_modified} mod, {agent.files_created} new")
                if agent.errors:
                    lines.append(f"    ⚠️  Errors: {len(agent.errors)}")
        else:
            lines.append("  No active agents")
        lines.append("")

        # Queue Status
        queue = snapshot["queues"]
        lines.append("📋 QUEUE STATUS")
        lines.append("-" * 80)
        lines.append(f"  Pending: {queue.pending} | "
                    f"In Progress: {queue.in_progress} | "
                    f"In Review: {queue.in_review} | "
                    f"Blocked: {queue.blocked}")
        lines.append("")

        # Alerts
        alerts = snapshot["alerts"]
        if alerts:
            lines.append("⚠️  ALERTS")
            lines.append("-" * 80)
            for alert in alerts:
                icon = "🔴" if alert.level == AlertLevel.CRITICAL else \
                      "🟡" if alert.level == AlertLevel.WARNING else "🔵"
                lines.append(f"  {icon} {alert.message}")
            lines.append("")

        lines.append("╔" + "═" * 78 + "╗")
        lines.append("║" + " " * 78 + "║")
        lines.append("╚" + "═" * 78 + "╝")

        return "\n".join(lines)

    def render_json(self) -> str:
        """
        Render dashboard as JSON

        Returns:
            JSON string
        """
        snapshot = self.get_snapshot()

        # Convert dataclasses to dicts
        def convert_to_dict(obj):
            if hasattr(obj, '__dict__'):
                return {
                    k: convert_to_dict(v)
                    for k, v in obj.__dict__.items()
                    if not k.startswith('_')
                }
            elif isinstance(obj, list):
                return [convert_to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_to_dict(v) for k, v in obj.items()}
            elif hasattr(obj, 'value'):  # Enum
                return obj.value
            else:
                return obj

        return json.dumps(convert_to_dict(snapshot), indent=2)

    def render_html(self) -> str:
        """
        Render dashboard as HTML

        Returns:
            HTML string
        """
        snapshot = self.get_snapshot()
        metrics = snapshot["metrics"]
        agents = snapshot["agents"]
        alerts = snapshot["alerts"]

        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "  <title>BlackBox5 Team Dashboard</title>",
            "  <style>",
            "    body { font-family: monospace; padding: 20px; background: #1e1e1e; color: #d4d4d4; }",
            "    h1 { color: #4ec9b0; }",
            "    h2 { color: #569cd6; border-bottom: 1px solid #444; padding-bottom: 5px; }",
            "    .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }",
            "    .metric-card { background: #252526; padding: 15px; border-radius: 5px; }",
            "    .metric-value { font-size: 32px; font-weight: bold; color: #4ec9b0; }",
            "    .metric-label { font-size: 14px; color: #888; }",
            "    .agent { background: #252526; padding: 10px; margin: 5px 0; border-radius: 3px; }",
            "    .alert { padding: 10px; margin: 5px 0; border-radius: 3px; }",
            "    .alert.critical { background: #5a1d1d; border-left: 4px solid #f44336; }",
            "    .alert.warning { background: #5a4a1d; border-left: 4px solid #ff9800; }",
            "    .alert.info { background: #1d3a5a; border-left: 4px solid #2196f3; }",
            "  </style>",
            "  <script>",
            "    setTimeout(() => location.reload(), 10000);",  # Auto-reload every 10s
            "  </script>",
            "</head>",
            "<body>",
            "  <h1>🤖 BlackBox5 Team Dashboard</h1>",
            f"  <p>Updated: {snapshot['timestamp']}</p>",
            "",
            "  <h2>📊 Metrics</h2>",
            "  <div class='metrics'>",
            f"    <div class='metric-card'><div class='metric-value'>{metrics['tasks']['total']}</div><div class='metric-label'>Total Tasks</div></div>",
            f"    <div class='metric-card'><div class='metric-value'>{metrics['tasks']['in_progress']}</div><div class='metric-label'>In Progress</div></div>",
            f"    <div class='metric-card'><div class='metric-value'>{metrics['tasks']['completed']}</div><div class='metric-label'>Completed</div></div>",
            f"    <div class='metric-card'><div class='metric-value'>{metrics['success_rate']:.1f}%</div><div class='metric-label'>Success Rate</div></div>",
            "  </div>",
            "",
            "  <h2>🤖 Active Agents</h2>"
        ]

        active = [a for a in agents if a.status == TaskStatus.IN_PROGRESS]
        if active:
            for agent in active:
                html.append(f"  <div class='agent'>")
                html.append(f"    <strong>{agent.task_title}</strong><br/>")
                html.append(f"    Runtime: {agent.runtime:.1f}min | Files: {agent.files_modified} mod, {agent.files_created} new")
                if agent.errors:
                    html.append(f"    <br/><span style='color: #f44336;'>⚠️ {len(agent.errors)} errors</span>")
                html.append(f"  </div>")
        else:
            html.append("  <p>No active agents</p>")

        # Alerts
        if alerts:
            html.append("")
            html.append("  <h2>⚠️ Alerts</h2>")
            for alert in alerts:
                level_class = alert.level.value
                html.append(f"  <div class='alert {level_class}'>{alert.message}</div>")

        html.extend([
            "",
            "</body>",
            "</html>"
        ])

        return "\n".join(html)

    # =========================================================================
    # WATCH MODE
    # =========================================================================

    def watch(
        self,
        interval: int = 10,
        render_format: str = "text"
    ):
        """
        Continuously monitor dashboard

        Args:
            interval: Seconds between updates
            render_format: "text", "json", or "html"
        """
        import time

        try:
            while True:
                # Clear screen
                import os
                os.system('clear' if os.name == 'posix' else 'cls')

                # Render
                if render_format == "text":
                    print(self.render_text())
                elif render_format == "json":
                    print(self.render_json())
                elif render_format == "html":
                    # For HTML, write to file and open in browser
                    html = self.render_html()
                    with open("/tmp/bb5-dashboard.html", "w") as f:
                        f.write(html)
                    print(f"Dashboard written to /tmp/bb5-dashboard.html")
                    print(f"Open in browser: file:///tmp/bb5-dashboard.html")

                print(f"\nRefreshing every {interval}s... (Ctrl+C to exit)")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\nDashboard monitoring stopped")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_dashboard() -> TeamDashboard:
    """Get the team dashboard instance"""
    return TeamDashboard()


def show_dashboard():
    """Show dashboard (one-time)"""
    dashboard = get_dashboard()
    print(dashboard.render_text())


def watch_dashboard(interval: int = 10):
    """Watch dashboard continuously"""
    dashboard = get_dashboard()
    dashboard.watch(interval=interval)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        watch_dashboard(interval)
    else:
        show_dashboard()
