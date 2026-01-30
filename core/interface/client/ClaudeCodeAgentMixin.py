"""
Claude Code Agent Mixin - Provides Claude Code CLI execution to agents

This mixin can be added to any BaseAgent to enable Claude Code CLI execution
instead of returning hardcoded template responses.

Usage:
    from agents.core.base_agent import BaseAgent, AgentTask, AgentResult
    from client.ClaudeCodeAgentMixin import ClaudeCodeAgentMixin

    class MyAgent(BaseAgent, ClaudeCodeAgentMixin):
        async def execute(self, task: AgentTask) -> AgentResult:
            return await self.execute_with_claude(task)
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from client.ClaudeCodeClient import ClaudeCodeClient, ClaudeCodeResult

logger = logging.getLogger(__name__)


class ClaudeCodeAgentMixin:
    """
    Mixin that provides Claude Code CLI execution capability to agents.

    This mixin adds the `execute_with_claude` method which uses the Claude Code CLI
    to execute tasks with real AI instead of returning hardcoded templates.

    Agents that inherit from this mixin can call `self.execute_with_claude(task)`
    in their `execute()` method.
    """

    # Default configuration for Claude Code execution
    claude_timeout: int = 300  # 5 minutes
    claude_mcp_profile: Optional[str] = None  # Auto-detect if None

    def __init__(self, *args, **kwargs):
        """Initialize the mixin (called via super().__init__ in agent)."""
        super().__init__(*args, **kwargs)
        self._claude_client: Optional[ClaudeCodeClient] = None

    @property
    def claude_client(self) -> ClaudeCodeClient:
        """Get or create the Claude Code client (lazy initialization)."""
        if self._claude_client is None:
            self._claude_client = ClaudeCodeClient()
        return self._claude_client

    def build_claude_prompt(
        self,
        task_description: str,
        context: Optional[str] = None
    ) -> str:
        """
        Build a prompt for Claude Code based on agent role and task.

        Args:
            task_description: The task description
            context: Optional context information (PRD, spec, etc.)

        Returns:
            Formatted prompt for Claude Code
        """
        # Get agent information from the BaseAgent instance
        role = getattr(self, 'role', 'AI Assistant')
        name = getattr(self, 'full_name', getattr(self, 'name', 'Agent'))
        capabilities = getattr(self, 'config', None)
        cap_list = capabilities.capabilities if capabilities else []

        prompt = f"""You are {name}, a {role}.

Your capabilities include: {', '.join(cap_list[:5])}

Task: {task_description}
"""

        if context:
            prompt += f"\nContext:\n{context}\n"

        # Add structured output format requirement
        prompt += """

## CRITICAL: Output Format

You MUST respond in this exact format:

<output>
{
  "status": "success|partial|failed",
  "summary": "One sentence describing what you did",
  "deliverables": ["list of files created or modified"],
  "next_steps": ["recommended next actions"],
  "metadata": {
    "agent": "%s",
    "task_id": "from-input",
    "duration_seconds": 0
  }
}
---
[Your detailed explanation, code, and reasoning for humans]
</output>

The JSON block at top (inside <output> tags) is for OTHER AGENTS to parse.
The content after --- is for HUMANS to read.
Always include both parts - this enables agent coordination.
""" % name

        return prompt

    async def execute_with_claude(
        self,
        task_description: str,
        context: Optional[str] = None,
        mcp_profile: Optional[str] = None,
        timeout: Optional[int] = None,
        cwd: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Execute a task using Claude Code CLI.

        Args:
            task_description: The task to execute
            context: Optional context (PRD file, spec, etc.)
            mcp_profile: MCP profile to use (default: auto-detect or use class default)
            timeout: Execution timeout (default: use class default)
            cwd: Working directory (default: current directory)

        Returns:
            Dictionary with execution result compatible with AgentResult
        """
        timeout = timeout or self.claude_timeout
        mcp_profile = mcp_profile or self.claude_mcp_profile

        # Build prompt
        prompt = self.build_claude_prompt(task_description, context)

        logger.info(f"Executing task with Claude Code: {task_description[:100]}...")

        # Execute via Claude Code
        result: ClaudeCodeResult = await self.claude_client.execute_async(
            prompt=prompt,
            mcp_profile=mcp_profile,
            context=context,
            timeout=timeout,
            cwd=cwd
        )

        # Convert ClaudeCodeResult to AgentResult-compatible format
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "artifacts": {
                "files_created": result.files_created
            },
            "metadata": {
                "duration": result.duration_seconds,
                "mcp_profile": result.metadata.get("mcp_profile"),
                "agent_name": getattr(self, 'name', 'unknown'),
                "execution_engine": "claude-code-cli"
            }
        }

    async def execute_with_claude_simple(
        self,
        task_description: str
    ) -> Dict[str, Any]:
        """
        Simple execution with Claude Code using defaults.

        Args:
            task_description: The task to execute

        Returns:
            Dictionary with execution result
        """
        return await self.execute_with_claude(task_description)


class ClaudeCodeAgentTemplate(ClaudeCodeAgentMixin):
    """
    Template agent that uses Claude Code CLI for execution.

    This is a complete example of how to create an agent that uses Claude Code CLI
    instead of hardcoded template responses.

    Subclass this and override get_default_config() to create specialized agents.
    """

    async def execute(self, task) -> Dict[str, Any]:
        """
        Execute task using Claude Code CLI.

        This method should be overridden in subclasses to add task-specific
        routing logic before calling Claude Code.
        """
        # For simple cases, just pass the task directly to Claude Code
        return await self.execute_with_claude_simple(task.description)

    async def think(self, task) -> list:
        """Generate thinking steps (returns placeholder steps)."""
        return [
            f"🔍 Analyzing: {task.description[:100]}...",
            "💡 Planning approach with Claude Code",
            "⚙️ Executing with Claude Code CLI",
            "✅ Reviewing results",
        ]


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

"""
Example: Creating a specialized agent with Claude Code execution

from agents.core.base_agent import BaseAgent, AgentTask, AgentResult, AgentConfig
from client.ClaudeCodeAgentMixin import ClaudeCodeAgentMixin

class CodeReviewerAgent(BaseAgent, ClaudeCodeAgentMixin):
    \"\"\"Agent that reviews code using Claude Code CLI.\"\"\"

    @classmethod
    def get_default_config(cls) -> AgentConfig:
        return AgentConfig(
            name="code_reviewer",
            full_name="Code Reviewer",
            role="Code Review Specialist",
            category="specialists",
            description="Expert code reviewer using Claude Code for analysis",
            capabilities=["code_review", "quality_analysis", "security_audit"],
            temperature=0.3
        )

    async def execute(self, task: AgentTask) -> AgentResult:
        \"\"\"Execute code review task using Claude Code.\"\"\"

        # Build code review prompt
        review_prompt = f\"\"\"
Please review the code related to: {task.description}

Focus on:
1. Code quality and readability
2. Potential bugs or edge cases
3. Performance considerations
4. Security issues
5. Best practices adherence

Provide specific, actionable feedback.
\"\"\"

        # Execute with Claude Code
        result = await self.execute_with_claude(review_prompt)

        return AgentResult(
            success=result["success"],
            output=result["output"],
            thinking_steps=await self.think(task),
            artifacts=result.get("artifacts", {}),
            metadata=result.get("metadata", {})
        )
"""
