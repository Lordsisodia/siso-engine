"""
Developer Agent (Amelia)

Specializes in code implementation, debugging, and technical tasks.

Uses Claude Code CLI for actual AI-powered code execution.
"""

import logging
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from agents.core.base_agent import BaseAgent, AgentTask, AgentResult, AgentConfig

# Import Claude Code execution mixin
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from client.ClaudeCodeAgentMixin import ClaudeCodeAgentMixin

logger = logging.getLogger(__name__)


class DeveloperAgent(BaseAgent, ClaudeCodeAgentMixin):
    """
    Developer Agent - Amelia 💻

    Specializes in:
    - Code implementation
    - Debugging and troubleshooting
    - Code review and optimization
    - Technical documentation
    - Testing and validation

    Uses Claude Code CLI for AI-powered code execution.
    """

    # Claude Code configuration
    claude_timeout = 300  # 5 minutes
    claude_mcp_profile = None  # Auto-detect based on task

    def __init__(self, config: AgentConfig):
        """Initialize DeveloperAgent with both BaseAgent and ClaudeCodeAgentMixin."""
        BaseAgent.__init__(self, config)
        ClaudeCodeAgentMixin.__init__(self)

    @classmethod
    def get_default_config(cls) -> AgentConfig:
        """Get default configuration for the Developer agent."""
        return AgentConfig(
            name="developer",
            full_name="Amelia",
            role="Developer",
            category="specialists",
            description="Expert developer specializing in code implementation, debugging, and technical problem-solving",
            capabilities=[
                "coding",
                "implementation",
                "debugging",
                "code_review",
                "testing",
                "refactoring",
                "documentation",
            ],
            temperature=0.3,  # Lower temperature for more focused coding
            metadata={
                "icon": "💻",
                "created_at": datetime.now().isoformat(),
            }
        )

    async def execute(self, task: AgentTask) -> AgentResult:
        """
        Execute a development task using Claude Code CLI.

        Args:
            task: The task to execute

        Returns:
            AgentResult with code or technical solution from Claude Code
        """
        thinking_steps = await self.think(task)

        # Build task-specific prompt based on task type
        task_lower = task.description.lower()
        task_type = None
        context_prompt = None

        if any(word in task_lower for word in ["debug", "fix", "error", "bug"]):
            task_type = "debugging"
            context_prompt = self._build_debug_prompt(task)
        elif any(word in task_lower for word in ["review", "refactor", "optimize"]):
            task_type = "code_review"
            context_prompt = self._build_review_prompt(task)
        elif any(word in task_lower for word in ["test", "validate"]):
            task_type = "testing"
            context_prompt = self._build_test_prompt(task)
        else:
            task_type = "implementation"
            context_prompt = self._build_implementation_prompt(task)

        # Execute with Claude Code CLI
        claude_result = await self.execute_with_claude(
            task_description=context_prompt,
            mcp_profile=self._select_mcp_profile(task_type, task)
        )

        # Extract additional metadata
        languages = self._detect_languages(task)
        code_blocks = self._extract_code_blocks(claude_result.get("output", ""))

        return AgentResult(
            success=claude_result.get("success", False),
            output=claude_result.get("output", ""),
            thinking_steps=thinking_steps,
            artifacts={
                "code_blocks": code_blocks,
                "files_created": claude_result.get("artifacts", {}).get("files_created", []),
            },
            metadata={
                "agent_name": self.name,
                "task_complexity": task.complexity,
                "task_type": task_type,
                "languages_used": languages,
                "execution_engine": "claude-code-cli",
                "duration": claude_result.get("metadata", {}).get("duration", 0),
                "mcp_profile": claude_result.get("metadata", {}).get("mcp_profile", "unknown"),
            }
        )

    async def think(self, task: AgentTask) -> List[str]:
        """Generate thinking steps for development tasks."""
        return [
            f"🔍 Analyzing requirements: {task.description[:100]}...",
            "💻 Designing implementation approach",
            "🧪 Considering edge cases and testing strategy",
            "📝 Writing clean, maintainable code",
            "✅ Validating solution against requirements",
        ]

    # =========================================================================
    # TASK-SPECIFIC PROMPT BUILDERS
    # =========================================================================

    def _build_debug_prompt(self, task: AgentTask) -> str:
        """Build prompt for debugging tasks."""
        return f"""Debug and fix the following issue: {task.description}

Please:
1. Analyze the issue systematically
2. Identify the root cause
3. Propose a minimal, targeted fix
4. Explain the testing approach to verify the fix
5. Consider potential edge cases and regressions

Provide your analysis and solution with clear code examples."""

    def _build_review_prompt(self, task: AgentTask) -> str:
        """Build prompt for code review tasks."""
        return f"""Review the code related to: {task.description}

Please analyze:
1. Code quality and structure
2. Naming conventions and readability
3. Error handling and edge cases
4. Performance considerations
5. Security vulnerabilities
6. Testing coverage

Provide specific, actionable recommendations with code examples where applicable."""

    def _build_test_prompt(self, task: AgentTask) -> str:
        """Build prompt for test writing tasks."""
        return f"""Write comprehensive tests for: {task.description}

Please include:
1. Unit tests for core functionality
2. Integration tests for component interactions
3. Edge case and boundary condition tests
4. Error handling and exception tests
5. Clear test documentation

Use pytest and follow testing best practices."""

    def _build_implementation_prompt(self, task: AgentTask) -> str:
        """Build prompt for feature implementation tasks."""
        return f"""Implement the following: {task.description}

Please provide:
1. Clean, well-documented code following best practices
2. Type hints for clarity
3. Comprehensive docstrings
4. Error handling
5. Usage examples
6. Testing recommendations

Focus on maintainability, readability, and extensibility."""

    def _select_mcp_profile(self, task_type: str, task: AgentTask) -> Optional[str]:
        """Select appropriate MCP profile based on task type."""
        # For most coding tasks, minimal is fastest
        if task_type == "implementation":
            # Check if task involves files or APIs
            task_lower = task.description.lower()
            if any(kw in task_lower for kw in ["file", "read", "write", "api", "http"]):
                return "filesystem"
            return "minimal"
        elif task_type == "testing":
            return "filesystem"  # May need to read test files
        elif task_type == "code_review":
            return "filesystem"  # Needs to read code files
        elif task_type == "debugging":
            return "filesystem"  # Needs to read code files
        return None  # Auto-detect

    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract code blocks from output."""
        import re
        return re.findall(r'```(?:python|javascript|typescript)?\n(.*?)```', text, re.DOTALL)

    def _estimate_files(self, task: AgentTask) -> int:
        """Estimate number of files that would be created."""
        return 1  # Simplified

    def _detect_languages(self, task: AgentTask) -> List[str]:
        """Detect programming languages from task."""
        task_lower = task.description.lower()
        languages = []

        if "python" in task_lower or "py" in task_lower:
            languages.append("Python")
        if "javascript" in task_lower or "js" in task_lower:
            languages.append("JavaScript")
        if "typescript" in task_lower or "ts" in task_lower:
            languages.append("TypeScript")

        return languages or ["Python"]  # Default
