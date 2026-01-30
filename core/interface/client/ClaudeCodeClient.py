"""
Claude Code Client - Execute tasks via Claude Code CLI

This client provides a Python interface to execute tasks through the Claude Code CLI
instead of using API calls. This is the primary execution method for Blackbox5 agents.

Usage:
    from client.ClaudeCodeClient import ClaudeCodeClient

    client = ClaudeCodeClient()
    result = client.execute("Write a hello world function in Python")
"""

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import os
import tempfile

logger = logging.getLogger(__name__)


@dataclass
class ClaudeCodeRequest:
    """Request configuration for Claude Code execution."""
    prompt: str
    mcp_profile: str = "minimal"  # minimal, filesystem, standard, data, automation, full
    context: Optional[str] = None  # Additional context file (PRD, spec, etc.)
    timeout: int = 300  # 5 minutes default
    cwd: Optional[Path] = None
    env: Dict[str, str] = field(default_factory=dict)


@dataclass
class ClaudeCodeResult:
    """Result from Claude Code execution."""
    success: bool
    output: str
    error: Optional[str] = None
    duration_seconds: float = 0.0
    files_created: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ClaudeCodeClient:
    """
    Client for executing tasks via Claude Code CLI.

    This client uses subprocess to call the Claude Code CLI with appropriate
    MCP profiles based on task requirements.
    """

    # Available MCP profiles (from ralphy-mcp-profiles.sh)
    MCP_PROFILES = {
        "minimal": {
            "description": "No MCP servers (fastest, ~1s startup)",
            "mcp_servers": [],
            "best_for": "Pure coding tasks"
        },
        "filesystem": {
            "description": "Filesystem access only (~2s startup)",
            "mcp_servers": ["filesystem"],
            "best_for": "File operations"
        },
        "standard": {
            "description": "Common MCPs (~5s startup)",
            "mcp_servers": ["filesystem", "fetch", "search"],
            "best_for": "APIs + web requests"
        },
        "data": {
            "description": "Data & docs MCPs (~10s startup)",
            "mcp_servers": ["filesystem", "fetch", "context7", "wikipedia"],
            "best_for": "Research + docs"
        },
        "automation": {
            "description": "Browser automation (~15s startup)",
            "mcp_servers": ["filesystem", "playwright", "chrome-devtools"],
            "best_for": "Browser automation"
        },
        "full": {
            "description": "All MCPs (~30s+ startup)",
            "mcp_servers": "all",
            "best_for": "Everything (slowest)"
        }
    }

    def __init__(
        self,
        claude_path: Optional[str] = None,
        profiles_dir: Optional[Path] = None
    ):
        """
        Initialize Claude Code client.

        Args:
            claude_path: Path to Claude Code CLI binary (default: auto-detect)
            profiles_dir: Directory containing MCP profiles (default: ~/.claude-profiles/)
        """
        self.claude_path = claude_path or self._find_claude_cli()
        self.profiles_dir = Path(profiles_dir or Path.home() / ".claude-profiles")

        logger.debug(f"ClaudeCodeClient initialized: claude={self.claude_path}, profiles={self.profiles_dir}")

    def _find_claude_cli(self) -> str:
        """Find Claude Code CLI binary."""
        # Check common locations
        candidates = [
            "claude",  # In PATH
            "/usr/local/bin/claude",
            Path.home() / ".local" / "bin" / "claude",
        ]

        for candidate in candidates:
            try:
                result = subprocess.run(
                    [str(candidate), "--version"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.debug(f"Found Claude CLI at: {candidate}")
                    return str(candidate)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        logger.warning("Claude CLI not found in PATH, using 'claude' as fallback")
        return "claude"

    def detect_mcp_profile(self, task: str) -> str:
        """
        Auto-detect appropriate MCP profile based on task description.

        Args:
            task: Task description

        Returns:
            Recommended MCP profile name
        """
        task_lower = task.lower()

        # Check for browser automation keywords
        browser_keywords = ["browser", "scrape", "screenshot", "web", "chrome", "playwright", "headless", "automate"]
        if any(kw in task_lower for kw in browser_keywords):
            return "automation"

        # Check for research/documentation keywords
        research_keywords = ["search", "documentation", "docs", "wikipedia", "research", "context", "reference"]
        if any(kw in task_lower for kw in research_keywords):
            return "data"

        # Check for web/API keywords
        web_keywords = ["fetch", "http", "api", "url", "download"]
        if any(kw in task_lower for kw in web_keywords):
            return "standard"

        # Default to minimal for pure coding
        return "minimal"

    def _get_profile_config_dir(self, profile: str) -> Path:
        """Get config directory for a specific MCP profile."""
        return self.profiles_dir / profile

    def _build_claude_command(
        self,
        request: ClaudeCodeRequest
    ) -> List[str]:
        """
        Build Claude CLI command with appropriate environment.

        Args:
            request: ClaudeCodeRequest

        Returns:
            Command list for subprocess
        """
        # Use profile-specific config directory
        profile_dir = self._get_profile_config_dir(request.mcp_profile)

        # Build environment
        env = os.environ.copy()
        env["CLAUDE_CONFIG_DIR"] = str(profile_dir)

        # Add custom environment variables
        env.update(request.env)

        return env

    def execute(
        self,
        prompt: str,
        mcp_profile: Optional[str] = None,
        context: Optional[str] = None,
        timeout: int = 300,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None
    ) -> ClaudeCodeResult:
        """
        Execute a task via Claude Code CLI (synchronous).

        Args:
            prompt: Task description/prompt
            mcp_profile: MCP profile to use (default: auto-detect)
            context: Optional context file path (PRD, spec, etc.)
            timeout: Execution timeout in seconds
            cwd: Working directory (default: current directory)
            env: Additional environment variables

        Returns:
            ClaudeCodeResult with execution output
        """
        # Auto-detect profile if not specified
        if mcp_profile is None:
            mcp_profile = self.detect_mcp_profile(prompt)

        start_time = datetime.now()

        try:
            # Build request
            request = ClaudeCodeRequest(
                prompt=prompt,
                mcp_profile=mcp_profile,
                context=context,
                timeout=timeout,
                cwd=cwd or Path.cwd(),
                env=env or {}
            )

            logger.info(f"Executing task with profile '{mcp_profile}': {prompt[:100]}...")

            # Build environment
            cli_env = self._build_claude_command(request)

            # Prepare command
            cmd = [self.claude_path]

            # Add context file if provided
            if request.context:
                cmd.extend(["--context", request.context])

            # For now, we'll use stdin to pass the prompt
            # In production, you might want to use a file or different approach

            # Execute
            result = subprocess.run(
                cmd,
                input=request.prompt,
                capture_output=True,
                text=True,
                cwd=request.cwd,
                env=cli_env,
                timeout=request.timeout
            )

            duration = (datetime.now() - start_time).total_seconds()

            # Check result
            if result.returncode == 0:
                output = result.stdout

                # Extract files created (parse from output if available)
                files_created = self._extract_files_created(output, request.cwd)

                logger.info(f"Task completed successfully in {duration:.2f}s")

                return ClaudeCodeResult(
                    success=True,
                    output=output,
                    duration_seconds=duration,
                    files_created=files_created,
                    metadata={
                        "mcp_profile": mcp_profile,
                        "returncode": result.returncode,
                        "cwd": str(request.cwd)
                    }
                )
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"Task failed: {error_msg}")

                return ClaudeCodeResult(
                    success=False,
                    output="",
                    error=error_msg,
                    duration_seconds=duration,
                    metadata={
                        "mcp_profile": mcp_profile,
                        "returncode": result.returncode
                    }
                )

        except subprocess.TimeoutExpired as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Task timed out after {duration:.2f}s")

            return ClaudeCodeResult(
                success=False,
                output="",
                error=f"Task timed out after {timeout} seconds",
                duration_seconds=duration,
                metadata={"mcp_profile": mcp_profile}
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Task execution failed: {e}")

            return ClaudeCodeResult(
                success=False,
                output="",
                error=str(e),
                duration_seconds=duration,
                metadata={"mcp_profile": mcp_profile}
            )

    async def execute_async(
        self,
        prompt: str,
        mcp_profile: Optional[str] = None,
        context: Optional[str] = None,
        timeout: int = 300,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None
    ) -> ClaudeCodeResult:
        """
        Execute a task via Claude Code CLI (asynchronous).

        Args:
            prompt: Task description/prompt
            mcp_profile: MCP profile to use (default: auto-detect)
            context: Optional context file path (PRD, spec, etc.)
            timeout: Execution timeout in seconds
            cwd: Working directory (default: current directory)
            env: Additional environment variables

        Returns:
            ClaudeCodeResult with execution output
        """
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.execute(prompt, mcp_profile, context, timeout, cwd, env)
        )

    def _extract_files_created(self, output: str, cwd: Path) -> List[str]:
        """
        Extract list of created files from Claude output.

        This parses the output to find file operations. In production, you might
        want to use a more sophisticated approach like parsing Claude's structured output.

        Args:
            output: Claude's output text
            cwd: Working directory

        Returns:
            List of created file paths
        """
        files = []

        # Look for common file creation patterns
        # This is a simple heuristic - you might want to improve this
        lines = output.split("\n")
        for line in lines:
            line = line.strip()
            # Look for "Created file:" or similar patterns
            if "created" in line.lower() and "/" in line:
                # Try to extract file path
                parts = line.split()
                for part in parts:
                    if "/" in part or part.endswith(".py") or part.endswith(".md"):
                        files.append(part)

        return files

    def list_profiles(self) -> Dict[str, Any]:
        """Get information about available MCP profiles."""
        return self.MCP_PROFILES

    def get_profile_info(self, profile: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific MCP profile."""
        return self.MCP_PROFILES.get(profile)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_default_client: Optional[ClaudeCodeClient] = None


def get_client(claude_path: Optional[str] = None) -> ClaudeCodeClient:
    """Get or create the default Claude Code client."""
    global _default_client
    if _default_client is None:
        _default_client = ClaudeCodeClient(claude_path=claude_path)
    return _default_client


def execute(
    prompt: str,
    mcp_profile: Optional[str] = None,
    context: Optional[str] = None,
    timeout: int = 300,
    cwd: Optional[Path] = None
) -> ClaudeCodeResult:
    """
    Convenience function to execute a task via Claude Code CLI.

    Args:
        prompt: Task description
        mcp_profile: MCP profile (default: auto-detect)
        context: Optional context file
        timeout: Execution timeout
        cwd: Working directory

    Returns:
        ClaudeCodeResult
    """
    client = get_client()
    return client.execute(prompt, mcp_profile, context, timeout, cwd)


async def execute_async(
    prompt: str,
    mcp_profile: Optional[str] = None,
    context: Optional[str] = None,
    timeout: int = 300,
    cwd: Optional[Path] = None
) -> ClaudeCodeResult:
    """Async convenience function to execute a task via Claude Code CLI."""
    client = get_client()
    return await client.execute_async(prompt, mcp_profile, context, timeout, cwd)
