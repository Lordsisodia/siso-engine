"""
Architect Agent (Alex)

Specializes in system architecture, design patterns, and technical planning.

Uses Claude Code CLI for AI-powered architectural analysis.
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


class ArchitectAgent(BaseAgent, ClaudeCodeAgentMixin):
    """
    Architect Agent - Alex 🏗️

    Specializes in:
    - System architecture
    - Design patterns
    - Technical planning
    - Infrastructure design
    - Scalability planning
    - Security architecture

    Uses Claude Code CLI for AI-powered architectural analysis.
    """

    # Claude Code configuration
    claude_timeout = 300  # 5 minutes
    claude_mcp_profile = None  # Auto-detect based on task

    def __init__(self, config: AgentConfig):
        """Initialize ArchitectAgent with both BaseAgent and ClaudeCodeAgentMixin."""
        BaseAgent.__init__(self, config)
        ClaudeCodeAgentMixin.__init__(self)

    @classmethod
    def get_default_config(cls) -> AgentConfig:
        """Get default configuration for the Architect agent."""
        return AgentConfig(
            name="architect",
            full_name="Alex",
            role="Architect",
            category="specialists",
            description="Expert architect specializing in system design, patterns, and scalable architecture",
            capabilities=[
                "architecture",
                "design_patterns",
                "system_design",
                "scalability",
                "security_design",
                "infrastructure",
                "technical_planning",
            ],
            temperature=0.4,  # Balanced for creative and structured thinking
            metadata={
                "icon": "🏗️",
                "created_at": datetime.now().isoformat(),
            }
        )

    async def execute(self, task: AgentTask) -> AgentResult:
        """
        Execute an architecture task using Claude Code CLI.

        Args:
            task: The task to execute

        Returns:
            AgentResult with architectural design and recommendations
        """
        thinking_steps = await self.think(task)

        # Build task-specific prompt based on task type
        task_lower = task.description.lower()
        task_type = None
        context_prompt = None

        if any(word in task_lower for word in ["pattern", "anti-pattern"]):
            task_type = "patterns"
            context_prompt = self._build_patterns_prompt(task)
        elif any(word in task_lower for word in ["scal", "scale", "performance"]):
            task_type = "scalability"
            context_prompt = self._build_scalability_prompt(task)
        elif any(word in task_lower for word in ["security", "secure"]):
            task_type = "security"
            context_prompt = self._build_security_prompt(task)
        else:
            task_type = "architecture"
            context_prompt = self._build_architecture_prompt(task)

        # Execute with Claude Code CLI
        claude_result = await self.execute_with_claude(
            task_description=context_prompt,
            mcp_profile=self._select_mcp_profile(task_type, task)
        )

        # Extract additional metadata
        diagrams = self._extract_diagram_refs(claude_result.get("output", ""))
        components = self._extract_components(claude_result.get("output", ""))
        decisions = self._extract_decisions(claude_result.get("output", ""))

        return AgentResult(
            success=claude_result.get("success", False),
            output=claude_result.get("output", ""),
            thinking_steps=thinking_steps,
            artifacts={
                "diagrams": diagrams,
                "components": components,
                "decisions": decisions,
            },
            metadata={
                "agent_name": self.name,
                "task_complexity": task.complexity,
                "task_type": task_type,
                "architecture_type": task_type,
                "execution_engine": "claude-code-cli",
                "duration": claude_result.get("metadata", {}).get("duration", 0),
                "mcp_profile": claude_result.get("metadata", {}).get("mcp_profile", "unknown"),
            }
        )

    async def think(self, task: AgentTask) -> List[str]:
        """Generate thinking steps for architecture tasks."""
        return [
            f"🏗️ Analyzing requirements for: {task.description[:100]}...",
            "📐 Designing system structure and components",
            "🔄 Considering scalability and performance",
            "🔒 Planning security and reliability",
            "📋 Documenting architecture decisions",
        ]

    # =========================================================================
    # TASK-SPECIFIC PROMPT BUILDERS
    # =========================================================================

    def _build_architecture_prompt(self, task: AgentTask) -> str:
        """Build prompt for architecture design tasks."""
        return f"""Design a comprehensive system architecture for: {task.description}

Please provide:

1. **Architecture Overview**
   - High-level system design
   - Component decomposition
   - Technology stack recommendations

2. **Architecture Diagram**
   - ASCII or text-based diagram showing layers and interactions
   - Clear component boundaries

3. **Component Details**
   - Purpose of each major component
   - Communication patterns between components
   - Data flow diagrams

4. **Quality Attributes**
   - Scalability approach
   - Reliability measures
   - Security considerations
   - Performance characteristics

5. **Technology Recommendations**
   - Programming languages
   - Frameworks and libraries
   - Database choices
   - Infrastructure tools

6. **Trade-offs and Decisions**
   - Key architectural decisions
   - Rationale for each choice
   - Alternative approaches considered

Use markdown formatting with clear headings and code blocks where appropriate."""

    def _build_patterns_prompt(self, task: AgentTask) -> str:
        """Build prompt for design pattern tasks."""
        return f"""Analyze and recommend design patterns for: {task.description}

Please provide:

1. **Pattern Recommendations**
   - Creational patterns (Factory, Builder, etc.)
   - Structural patterns (Adapter, Composite, etc.)
   - Behavioral patterns (Strategy, Observer, etc.)

2. **Pattern Examples**
   - Code examples in Python or TypeScript
   - When to use each pattern
   - Benefits and trade-offs

3. **Anti-Patterns to Avoid**
   - Common mistakes
   - Code smells
   - Refactoring recommendations

4. **Best Practices**
   - SOLID principles application
   - Composition over inheritance
   - Interface segregation

Provide concrete, actionable examples with code."""

    def _build_scalability_prompt(self, task: AgentTask) -> str:
        """Build prompt for scalability planning tasks."""
        return f"""Design a comprehensive scalability strategy for: {task.description}

Please provide:

1. **Current Assessment**
   - Assumed current capacity baseline
   - Expected growth trajectory
   - Identified bottlenecks

2. **Scaling Strategies**
   - Horizontal scaling approach
   - Vertical scaling approach
   - Caching strategy (multi-level)
   - Database scaling (read replicas, partitioning)

3. **Performance Optimization**
   - Query optimization
   - API optimization
   - CDN and content delivery
   - Load balancing

4. **Implementation Roadmap**
   - Phased rollout plan
   - Expected improvements per phase
   - Cost considerations

5. **Monitoring and Alerting**
   - Key metrics to track
   - Alert thresholds
   - Capacity planning approach

Include specific configurations and code examples where applicable."""

    def _build_security_prompt(self, task: AgentTask) -> str:
        """Build prompt for security architecture tasks."""
        return f"""Design a comprehensive security architecture for: {task.description}

Please provide:

1. **Security Principles**
   - Defense in depth approach
   - Least privilege implementation
   - Zero trust architecture

2. **Authentication & Authorization**
   - Authentication flow design
   - JWT/token-based approach
   - RBAC model
   - Code examples

3. **Data Security**
   - Encryption at rest (AES-256)
   - Encryption in transit (TLS 1.3)
   - Key management strategy
   - PII protection approach

4. **API Security**
   - Rate limiting
   - Input validation
   - CORS configuration
   - DDoS protection

5. **Security Monitoring**
   - Logging strategy
   - Alerting on anomalies
   - Audit trail design

6. **Compliance**
   - GDPR considerations
   - SOC 2 requirements
   - Industry-specific compliance

Include security checklist and implementation examples."""

    def _select_mcp_profile(self, task_type: str, task: AgentTask) -> Optional[str]:
        """Select appropriate MCP profile based on task type."""
        # For architecture tasks, we typically don't need filesystem access
        # unless the task involves reading existing code
        task_lower = task.description.lower()

        if any(kw in task_lower for kw in ["read", "analyze code", "review"]):
            return "filesystem"  # Need to read code files
        elif any(kw in task_lower for kw in ["research", "best practices"]):
            return "data"  # May need documentation lookup
        return "minimal"  # Architecture design is mostly text output

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _extract_diagram_refs(self, text: str) -> List[str]:
        """Extract diagram references."""
        import re
        return re.findall(r'```\n(.+?)```', text, re.DOTALL)

    def _extract_components(self, text: str) -> List[str]:
        """Extract component names."""
        import re
        return re.findall(r'^\*\*(.+?)\*\*\*:', text, re.MULTILINE)

    def _extract_decisions(self, text: str) -> List[str]:
        """Extract architectural decisions."""
        import re
        return re.findall(r'^\d+\.\s+\*\*(.+?)\*\*:', text, re.MULTILINE)
