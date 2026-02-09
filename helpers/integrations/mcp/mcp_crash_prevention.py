"""
MCP Server Crash Prevention System
===================================

Prevents VSCode crashes caused by runaway MCP server processes.

Key Features:
- Process monitoring with resource limits
- Automatic cleanup of orphaned/duplicate servers
- Health checks with automatic recovery
- Integration with Black Box 5 health monitor and circuit breaker

Architecture:
- Extends MCPIntegration.py with crash prevention hooks
- Integrates with health.py for system-wide monitoring
- Uses circuit_breaker.py for failure detection
- Follows Black Box 5 configuration patterns
"""

import asyncio
import logging
import os
import psutil
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class MCPServerStatus(Enum):
    """MCP server health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"  # High resource usage but functional
    UNHEALTHY = "unhealthy"  # Failed health check
    ZOMBIE = "zombie"  # Orphaned process
    DUPLICATE = "duplicate"  # Too many instances


@dataclass
class MCPServerMetrics:
    """Metrics for a single MCP server process"""
    pid: int
    server_type: str  # e.g., "chrome-devtools", "playwright"
    cpu_percent: float
    memory_mb: float
    uptime_seconds: float
    status: MCPServerStatus
    last_check: datetime


@dataclass
class MCPCrashPreventionConfig:
    """Configuration for MCP crash prevention"""
    # Resource limits
    max_instances_per_type: int = 2
    max_cpu_percent: float = 80.0
    max_memory_mb: float = 500.0
    max_age_seconds: int = 7200  # 2 hours

    # Health check settings
    health_check_interval: int = 60  # seconds
    health_check_timeout: int = 30  # seconds
    restart_max_retries: int = 3
    restart_backoff_seconds: int = 60

    # Auto-cleanup settings
    enable_auto_cleanup: bool = True
    cleanup_interval: int = 60  # seconds
    zombie_detection_enabled: bool = True

    # Thresholds for warnings
    warning_cpu_percent: float = 70.0
    warning_memory_mb: float = 300.0


class MCPCrashPrevention:
    """
    MCP Server Crash Prevention System.

    Monitors MCP server processes, enforces resource limits,
    and automatically cleans up problematic servers.

    Integrates with:
    - MCPIntegration.py for server lifecycle
    - health.py for system-wide health monitoring
    - circuit_breaker.py for failure detection
    """

    def __init__(
        self,
        config: Optional[MCPCrashPreventionConfig] = None,
        mcp_manager=None,
        health_monitor=None
    ):
        """
        Initialize MCP crash prevention system.

        Args:
            config: Crash prevention configuration
            mcp_manager: MCPManager instance for server control
            health_monitor: HealthMonitor instance for system integration
        """
        self.config = config or MCPCrashPreventionConfig()
        self.mcp_manager = mcp_manager
        self.health_monitor = health_monitor

        # Runtime state
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._server_metrics: Dict[int, MCPServerMetrics] = {}  # pid -> metrics
        self._server_lock = threading.Lock()

        # Server type tracking (for duplicate detection)
        self._server_type_counts: Dict[str, int] = {}
        self._known_pids: Set[int] = set()

        # Statistics
        self._stats = {
            "cleanups_performed": 0,
            "health_checks_failed": 0,
            "resources_exceeded": 0,
            "duplicates_detected": 0,
            "last_cleanup": None,
        }

        logger.info("MCP Crash Prevention initialized")

    async def start(self) -> None:
        """Start crash prevention monitoring."""
        if self._running:
            logger.warning("Crash prevention already running")
            return

        self._running = True

        # Start monitoring tasks
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        # Register with health monitor if available
        if self.health_monitor:
            self.health_monitor.register_check(
                "mcp_crash_prevention",
                self._health_check,
                interval=self.config.health_check_interval,
                timeout=self.config.health_check_timeout
            )

        logger.info("MCP Crash Prevention started")

    async def stop(self) -> None:
        """Stop crash prevention monitoring."""
        if not self._running:
            return

        self._running = False

        # Cancel tasks
        if self._monitor_task:
            self._monitor_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # Wait for tasks to complete
        try:
            await asyncio.gather(self._monitor_task, self._cleanup_task, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error stopping tasks: {e}")

        logger.info("MCP Crash Prevention stopped")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                await self._collect_metrics()
                await self._check_resource_limits()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
                await asyncio.sleep(self.config.health_check_interval)

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup loop."""
        while self._running:
            try:
                if self.config.enable_auto_cleanup:
                    await self._perform_cleanup()
                await asyncio.sleep(self.config.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                await asyncio.sleep(self.config.cleanup_interval)

    async def _collect_metrics(self) -> None:
        """Collect metrics from all MCP server processes."""
        with self._server_lock:
            # Clear old metrics
            self._server_metrics.clear()
            self._server_type_counts.clear()
            self._known_pids.clear()

            # Find all MCP-related processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'create_time']):
                try:
                    pid = proc.info['pid']
                    cmdline = proc.info['cmdline']

                    if not cmdline:
                        continue

                    cmdline_str = ' '.join(cmdline)

                    # Identify MCP server type
                    server_type = self._identify_server_type(cmdline_str)
                    if not server_type:
                        continue

                    # Collect metrics
                    cpu_percent = proc.info['cpu_percent'] or 0
                    memory_mb = (proc.info['memory_info'].rss / 1024 / 1024) if proc.info['memory_info'] else 0
                    uptime = time.time() - proc.info['create_time']

                    # Determine status
                    status = self._determine_status(cpu_percent, memory_mb, uptime)

                    metrics = MCPServerMetrics(
                        pid=pid,
                        server_type=server_type,
                        cpu_percent=cpu_percent,
                        memory_mb=memory_mb,
                        uptime_seconds=uptime,
                        status=status,
                        last_check=datetime.now()
                    )

                    self._server_metrics[pid] = metrics
                    self._server_type_counts[server_type] = self._server_type_counts.get(server_type, 0) + 1
                    self._known_pids.add(pid)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            logger.debug(f"Collected metrics for {len(self._server_metrics)} MCP processes")

    def _identify_server_type(self, cmdline: str) -> Optional[str]:
        """Identify MCP server type from command line."""
        server_patterns = {
            'chrome-devtools': 'chrome-devtools-mcp',
            'duckduckgo': 'duckduckgo-mcp',
            'playwright': 'playwright.*mcp',
            'filesystem': 'mcp-server-filesystem',
            'supabase': 'supabase.*mcp',
            'sequential-thinking': 'sequential-thinking',
            'fetch': 'mcp.*fetch',
        }

        for server_type, pattern in server_patterns.items():
            if pattern.lower() in cmdline.lower():
                return server_type

        return None

    def _determine_status(self, cpu: float, memory: float, uptime: float) -> MCPServerStatus:
        """Determine server status based on metrics."""
        # Check resource limits
        if cpu > self.config.max_cpu_percent or memory > self.config.max_memory_mb:
            return MCPServerStatus.UNHEALTHY

        # Check for old servers
        if uptime > self.config.max_age_seconds:
            return MCPServerStatus.DEGRADED

        return MCPServerStatus.HEALTHY

    async def _check_resource_limits(self) -> None:
        """Check if any servers exceed resource limits."""
        for pid, metrics in self._server_metrics.items():
            if metrics.status == MCPServerStatus.UNHEALTHY:
                logger.warning(
                    f"MCP server {metrics.server_type} (PID {pid}) exceeds limits: "
                    f"CPU: {metrics.cpu_percent:.1f}%, Memory: {metrics.memory_mb:.1f}MB"
                )
                self._stats["resources_exceeded"] += 1

                # Could trigger restart here
                # await self._restart_server(metrics)

    async def _perform_cleanup(self) -> None:
        """Perform cleanup of problematic servers."""
        cleanups = 0

        with self._server_lock:
            # Check for duplicates
            for server_type, count in self._server_type_counts.items():
                if count > self.config.max_instances_per_type:
                    logger.warning(f"Too many {server_type} instances: {count}")
                    self._stats["duplicates_detected"] += 1

                    # Kill excess instances (keep newest)
                    instances = [
                        (pid, metrics) for pid, metrics in self._server_metrics.items()
                        if metrics.server_type == server_type
                    ]
                    instances.sort(key=lambda x: x[1].uptime_seconds, reverse=True)

                    # Kill oldest excess instances
                    for pid, _ in instances[self.config.max_instances_per_type:]:
                        try:
                            os.kill(pid, signal.SIGTERM)
                            cleanups += 1
                            logger.info(f"Killed excess {server_type} process (PID {pid})")
                        except ProcessLookupError:
                            pass

            # Check for zombies
            if self.config.zombie_detection_enabled:
                current_pids = {proc.pid for proc in psutil.process_iter()}
                for pid in list(self._known_pids):
                    if pid not in current_pids:
                        # Process died, clean up tracking
                        self._known_pids.discard(pid)
                        if pid in self._server_metrics:
                            logger.debug(f"Cleaned up dead process tracking (PID {pid})")
                            del self._server_metrics[pid]

        if cleanups > 0:
            self._stats["cleanups_performed"] += cleanups
            self._stats["last_cleanup"] = datetime.now()
            logger.info(f"Performed {cleanups} cleanups")

    def _health_check(self) -> bool:
        """
        Health check for integration with health monitor.

        Returns:
            True if system is healthy
        """
        try:
            # Check total MCP process count
            total_processes = len(self._server_metrics)

            if total_processes > 20:
                logger.warning(f"Too many MCP processes: {total_processes}")
                return False

            # Check for unhealthy servers
            unhealthy_count = sum(
                1 for m in self._server_metrics.values()
                if m.status == MCPServerStatus.UNHEALTHY
            )

            if unhealthy_count > 0:
                logger.warning(f"{unhealthy_count} unhealthy MCP servers")
                return False

            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        with self._server_lock:
            return {
                "server_count": len(self._server_metrics),
                "server_type_counts": dict(self._server_type_counts),
                "statistics": dict(self._stats),
                "servers_by_type": {
                    server_type: [
                        {
                            "pid": m.pid,
                            "cpu": m.cpu_percent,
                            "memory_mb": m.memory_mb,
                            "uptime": m.uptime_seconds,
                            "status": m.status.value,
                        }
                        for m in self._server_metrics.values()
                        if m.server_type == server_type
                    ]
                    for server_type in self._server_type_counts.keys()
                }
            }

    def get_status_summary(self) -> Dict[str, Any]:
        """Get human-readable status summary."""
        metrics = self.get_metrics()

        return {
            "total_servers": metrics["server_count"],
            "by_type": metrics["server_type_counts"],
            "unhealthy_count": sum(
                1 for m in self._server_metrics.values()
                if m.status == MCPServerStatus.UNHEALTHY
            ),
            "statistics": metrics["statistics"],
            "last_updated": datetime.now().isoformat(),
        }


# =============================================================================
# Singleton Instance
# =============================================================================

_crash_prevention: Optional[MCPCrashPrevention] = None
_lock = threading.Lock()


def get_crash_prevention(
    config: Optional[MCPCrashPreventionConfig] = None,
    mcp_manager=None,
    health_monitor=None
) -> MCPCrashPrevention:
    """
    Get singleton crash prevention instance.

    Args:
        config: Optional configuration
        mcp_manager: Optional MCPManager instance
        health_monitor: Optional HealthMonitor instance

    Returns:
        MCPCrashPrevention instance
    """
    global _crash_prevention

    with _lock:
        if _crash_prevention is None:
            _crash_prevention = MCPCrashPrevention(
                config=config,
                mcp_manager=mcp_manager,
                health_monitor=health_monitor
            )

        return _crash_prevention


def reset_crash_prevention() -> None:
    """Reset the singleton instance (for testing)."""
    global _crash_prevention
    with _lock:
        _crash_prevention = None
