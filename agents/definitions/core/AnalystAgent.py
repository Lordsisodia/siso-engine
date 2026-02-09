"""
Analyst Agent (Mary)

Specializes in research, analysis, and data-driven insights.

Uses Claude Code CLI for AI-powered research and analysis.
"""

import logging
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from agents.framework.base_agent import BaseAgent, AgentTask, AgentResult, AgentConfig

# Import Claude Code execution mixin
import sys
# Path is: 2-engine/agents/definitions/core/AnalystAgent.py
# We need to reach: 2-engine/ to import from interface/client/
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from interface.client.ClaudeCodeAgentMixin import ClaudeCodeAgentMixin

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent, ClaudeCodeAgentMixin):
    """
    Analyst Agent - Mary 📊

    Specializes in:
    - Research and investigation
    - Data analysis
    - Competitive analysis
    - Market research
    - Requirements analysis
    - User research

    Uses Claude Code CLI for AI-powered research and analysis.
    """

    # Claude Code configuration
    claude_timeout = 300  # 5 minutes
    claude_mcp_profile = None  # Auto-detect based on task

    def __init__(self, config: AgentConfig):
        """Initialize AnalystAgent with both BaseAgent and ClaudeCodeAgentMixin."""
        BaseAgent.__init__(self, config)
        ClaudeCodeAgentMixin.__init__(self)

    @classmethod
    def get_default_config(cls) -> AgentConfig:
        """Get default configuration for the Analyst agent."""
        return AgentConfig(
            name="analyst",
            full_name="Mary",
            role="Analyst",
            category="specialists",
            description="Expert analyst specializing in research, data analysis, and generating actionable insights",
            capabilities=[
                "research",
                "data_analysis",
                "competitive_analysis",
                "market_research",
                "requirements_analysis",
                "user_research",
                "analysis",
            ],
            temperature=0.5,  # Balanced for creative and analytical thinking
            metadata={
                "icon": "📊",
                "created_at": datetime.now().isoformat(),
            }
        )

    async def execute(self, task: AgentTask) -> AgentResult:
        """
        Execute an analysis task using Claude Code CLI.

        Args:
            task: The task to execute

        Returns:
            AgentResult with analysis and insights
        """
        thinking_steps = await self.think(task)

        # Build task-specific prompt based on task type
        task_lower = task.description.lower()
        task_type = None
        context_prompt = None

        if any(word in task_lower for word in ["data", "metrics", "analytics"]):
            task_type = "data_analysis"
            context_prompt = self._build_data_analysis_prompt(task)
        elif any(word in task_lower for word in ["competitor", "competitive"]):
            task_type = "competitive"
            context_prompt = self._build_competitive_analysis_prompt(task)
        elif any(word in task_lower for word in ["requirement", "spec"]):
            task_type = "requirements"
            context_prompt = self._build_requirements_analysis_prompt(task)
        else:
            task_type = "research"
            context_prompt = self._build_research_prompt(task)

        # Execute with Claude Code CLI
        claude_result = await self.execute_with_claude(
            task_description=context_prompt,
            mcp_profile=self._select_mcp_profile(task_type, task)
        )

        # Extract additional metadata
        insights = self._extract_insights(claude_result.get("output", ""))
        recommendations = self._extract_recommendations(claude_result.get("output", ""))

        return AgentResult(
            success=claude_result.get("success", False),
            output=claude_result.get("output", ""),
            thinking_steps=thinking_steps,
            artifacts={
                "insights": insights,
                "recommendations": recommendations,
            },
            metadata={
                "agent_name": self.name,
                "task_complexity": task.complexity,
                "task_type": task_type,
                "analysis_type": task_type,
                "execution_engine": "claude-code-cli",
                "duration": claude_result.get("metadata", {}).get("duration", 0),
                "mcp_profile": claude_result.get("metadata", {}).get("mcp_profile", "unknown"),
            }
        )

    async def think(self, task: AgentTask) -> List[str]:
        """Generate thinking steps for analysis tasks."""
        return [
            f"📚 Gathering information on: {task.description[:100]}...",
            "🔍 Analyzing patterns and trends",
            "📈 Processing data and identifying insights",
            "🎯 Formulating data-driven conclusions",
            "💡 Developing actionable recommendations",
        ]

    # =========================================================================
    # TASK-SPECIFIC PROMPT BUILDERS
    # =========================================================================

    def _build_research_prompt(self, task: AgentTask) -> str:
        """Build prompt for research tasks."""
        return f"""Conduct comprehensive research on: {task.description}

Please provide:

1. **Executive Summary**
   - Key findings in 2-3 sentences
   - Main conclusion

2. **Key Findings**
   - Primary insights
   - Secondary observations
   - Supporting data points

3. **Detailed Analysis**
   - Topic overview and scope
   - Methodology approach
   - Comprehensive findings
   - Identified patterns and trends

4. **Recommendations**
   - Immediate actions (now)
   - Short-term strategy (1-3 months)
   - Long-term planning (6-12 months)

5. **Sources and Validation**
   - Multi-source verification
   - Cross-reference validation
   - Confidence level in findings

Use markdown formatting with clear headings and structured content."""

    def _build_data_analysis_prompt(self, task: AgentTask) -> str:
        """Build prompt for data analysis tasks."""
        return f"""Perform comprehensive data analysis for: {task.description}

Please provide:

1. **Data Summary**
   - Key metrics in table format
   - Trend indicators (📈 increasing, 📉 decreasing, ➡️ stable)
   - Statistical overview

2. **Key Insights**
   - Trend analysis with patterns
   - Notable anomalies or outliers
   - Correlations between metrics
   - Identified opportunities

3. **Visual Analysis**
   - Describe what visualizations would be helpful
   - ASCII charts where appropriate
   - Graph interpretations

4. **Recommendations**
   - Optimization opportunities
   - Growth potential areas
   - Risk mitigation strategies

5. **Next Steps**
   - Metrics to monitor
   - Areas for deeper analysis
   - Implementation recommendations

Include tables and structured data presentation."""

    def _build_competitive_analysis_prompt(self, task: AgentTask) -> str:
        """Build prompt for competitive analysis tasks."""
        return f"""Conduct competitive analysis for: {task.description}

Please provide:

1. **Market Landscape**
   - Market overview and dynamics
   - Key players and positioning

2. **Competitor Overview**
   - Create a comparison table with:
     * Competitor names
     * Key strengths
     * Notable weaknesses
     * Market position

3. **Competitive Analysis**
   - Our competitive advantages
   - Market gaps and opportunities
   - Threat assessment

4. **Strategic Recommendations**
   - How to leverage our strengths
   - Areas to address/gaps to close
   - Differentiation strategies
   - Monitoring approach

5. **Action Plan**
   - Short-term immediate actions
   - Medium-term strategic initiatives
   - Long-term vision

Use tables for clear comparison and structured recommendations."""

    def _build_requirements_analysis_prompt(self, task: AgentTask) -> str:
        """Build prompt for requirements analysis tasks."""
        return f"""Perform detailed requirements analysis for: {task.description}

Please provide:

1. **Requirements Breakdown**
   - Functional requirements table with:
     * Requirement ID
     * Description
     * Priority (Critical/High/Medium/Low)
     * Complexity
     * Status

   - Non-functional requirements table with:
     * Category
     * Requirement
     * Success metric
     * Priority

2. **Analysis**
   - **Completeness**: What's covered vs missing
   - **Consistency**: Any conflicts or dependencies
   - **Feasibility**: Technical and resource assessment
   - **Clarity**: Items needing clarification

3. **Recommendations**
   - Items to clarify with stakeholders
   - Prioritization approach
   - Dependency management
   - Validation strategy

4. **Updated Requirements**
   - Refined requirements list
   - Acceptance criteria
   - Assumptions documented

Use tables for clear requirement presentation."""

    def _select_mcp_profile(self, task_type: str, task: AgentTask) -> Optional[str]:
        """Select appropriate MCP profile based on task type."""
        # Analyst tasks often need research/data capabilities
        task_lower = task.description.lower()

        if any(kw in task_lower for kw in ["web research", "lookup", "documentation"]):
            return "data"  # May need documentation/web access
        elif any(kw in task_lower for kw in ["analyze code", "review code"]):
            return "filesystem"  # Need to read code files
        return "standard"  # Default to standard for research

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _extract_insights(self, text: str) -> List[str]:
        """Extract key insights from output."""
        import re
        insights = re.findall(r'[•-]\s+\*\*(.+?)\*\*:\s*(.+)', text)
        return [f"{title}: {content}" for title, content in insights]

    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from output."""
        import re
        return re.findall(r'^\d+\.\s+\*\*(.+?)\*\*:\s*(.+)', text, re.MULTILINE)
