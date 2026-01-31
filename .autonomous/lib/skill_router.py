"""
Automatic Skill Router for BMAD

Routes tasks to appropriate BMAD skills based on keyword matching.
Part of Agent-2.3 automatic skill routing feature.
"""

import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SkillRole(Enum):
    """BMAD skill roles."""
    PM = "pm"           # Product Manager (John)
    ARCHITECT = "architect"  # Architect (Winston)
    ANALYST = "analyst"      # Analyst (Mary)
    SCRUM_MASTER = "sm"      # Scrum Master (Bob)
    UX = "ux"                # UX Designer (Sally)
    DEV = "dev"              # Developer (Amelia)
    QA = "qa"                # QA Engineer (Quinn)
    TEA = "tea"              # Test Architect (TEA)
    QUICK_FLOW = "quick"     # Quick Flow (Barry)
    SUPERINTELLIGENCE = "superintelligence"  # Superintelligence Protocol


@dataclass
class SkillRoute:
    """Result of skill routing."""
    role: SkillRole
    skill_file: str
    confidence: float  # 0.0 to 1.0
    matched_keywords: List[str]
    agent_name: str


# Skill routing configuration
SKILL_MAP: Dict[SkillRole, Dict] = {
    SkillRole.PM: {
        "name": "Product Manager",
        "agent": "John",
        "file": "bmad-pm.md",
        "keywords": [
            "prd", "requirements", "product", "feature", "user story", "stakeholder",
            "roadmap", "milestone", "release", "mvp", "epic", "backlog",
            "discovery", "interview", "market research", "competitive analysis",
            "value proposition", "business case", "prioritization", "scope"
        ],
        "weight": 1.0
    },
    SkillRole.ARCHITECT: {
        "name": "Architect",
        "agent": "Winston",
        "file": "bmad-architect.md",
        "keywords": [
            "architecture", "design", "system", "pattern", "component",
            "scalability", "performance", "reliability", "integration",
            "api design", "data model", "infrastructure", "cloud",
            "microservices", "database", "security", "compliance",
            "technical decision", "trade-off", "constraint"
        ],
        "weight": 1.0
    },
    SkillRole.ANALYST: {
        "name": "Analyst",
        "agent": "Mary",
        "file": "bmad-analyst.md",
        "keywords": [
            "research", "analyze", "investigate", "study", "survey",
            "data", "metrics", "kpi", "measurement", "benchmark",
            "root cause", "problem analysis", "impact assessment",
            "feasibility", "risk analysis", "cost benefit", "report"
        ],
        "weight": 1.0
    },
    SkillRole.SCRUM_MASTER: {
        "name": "Scrum Master",
        "agent": "Bob",
        "file": "bmad-sm.md",
        "keywords": [
            "sprint", "story", "planning", "estimation", "velocity",
            "retrospective", "standup", "ceremony", "process",
            "blocker", "impediment", "team coordination", "daily sync",
            "iteration", "burn down", "capacity", "assignment"
        ],
        "weight": 1.0
    },
    SkillRole.UX: {
        "name": "UX Designer",
        "agent": "Sally",
        "file": "bmad-ux.md",
        "keywords": [
            "ux", "ui", "design", "user", "interface", "experience",
            "wireframe", "prototype", "mockup", "figma", "usability",
            "accessibility", "user flow", "journey map", "persona",
            "visual design", "interaction", "responsive", "mobile"
        ],
        "weight": 1.0
    },
    SkillRole.DEV: {
        "name": "Developer",
        "agent": "Amelia",
        "file": "bmad-dev.md",
        "keywords": [
            "implement", "code", "develop", "fix", "bug", "feature",
            "refactor", "optimize", "debug", "test", "deploy",
            "integration", "api", "endpoint", "function", "class",
            "module", "library", "framework", "database query"
        ],
        "weight": 1.0
    },
    SkillRole.QA: {
        "name": "QA Engineer",
        "agent": "Quinn",
        "file": "bmad-qa.md",
        "keywords": [
            "test", "qa", "quality", "verify", "validate", "check",
            "automation", "regression", "unit test", "integration test",
            "e2e", "acceptance", "coverage", "defect", "bug report",
            "test case", "test plan", "ci/cd", "pipeline"
        ],
        "weight": 1.0
    },
    SkillRole.TEA: {
        "name": "Test Architect",
        "agent": "TEA",
        "file": "bmad-tea.md",
        "keywords": [
            "test architecture", "test plan", "test strategy",
            "testing framework", "test infrastructure", "performance test",
            "load test", "security test", "test coverage strategy",
            "quality gate", "test automation strategy", "test data"
        ],
        "weight": 0.9  # Slightly lower to avoid conflict with QA
    },
    SkillRole.QUICK_FLOW: {
        "name": "Quick Flow",
        "agent": "Barry",
        "file": "bmad-quick-flow.md",
        "keywords": [
            "small", "quick", "clear", "simple", "minor", "trivial",
            "hotfix", "patch", "one-liner", "typo", "documentation fix",
            "config change", "update readme", "comment", "formatting"
        ],
        "weight": 1.2  # Higher weight to catch simple tasks
    },
    SkillRole.SUPERINTELLIGENCE: {
        "name": "Superintelligence Protocol",
        "agent": "Protocol",
        "file": "superintelligence-protocol.md",
        "keywords": [
            "protocol", "superintelligence", "deep analysis", "architecture decision",
            "complex problem", "multi-dimensional", "system design", "redesign",
            "optimize", "uncertain", "novel", "high impact", "cross-cutting",
            "first principles", "expert analysis", "synthesize"
        ],
        "weight": 1.3  # Higher weight to catch complex tasks
    }
}


class SkillRouter:
    """
    Routes tasks to appropriate BMAD skills based on content analysis.
    """

    def __init__(self, skills_path: Optional[Path] = None):
        """
        Initialize the skill router.

        Args:
            skills_path: Path to BMAD skills directory
        """
        self.skills_path = skills_path or Path(__file__).parent.parent / "skills"
        self.skill_map = SKILL_MAP

    def route(self, task_description: str) -> Optional[SkillRoute]:
        """
        Route a task to the most appropriate skill.

        Args:
            task_description: Description of the task

        Returns:
            SkillRoute with the best matching skill, or None if no match
        """
        if not task_description:
            return None

        task_lower = task_description.lower()
        scores: Dict[SkillRole, Tuple[float, List[str]]] = {}

        # Calculate scores for each skill
        for role, config in self.skill_map.items():
            score, matches = self._calculate_score(task_lower, config)
            if score > 0:
                scores[role] = (score, matches)

        if not scores:
            return None

        # Find best match
        best_role = max(scores.keys(), key=lambda r: scores[r][0])
        best_score, best_matches = scores[best_role]
        config = self.skill_map[best_role]

        # Calculate confidence (normalize by max possible score)
        max_possible = len(config["keywords"]) * config["weight"]
        confidence = min(best_score / max_possible * 2, 1.0)  # Scale for reasonable confidence

        return SkillRoute(
            role=best_role,
            skill_file=str(self.skills_path / config["file"]),
            confidence=confidence,
            matched_keywords=best_matches[:5],  # Top 5 matches
            agent_name=config["agent"]
        )

    def _calculate_score(self, task_lower: str, config: Dict) -> Tuple[float, List[str]]:
        """
        Calculate match score for a skill configuration.

        Args:
            task_lower: Lowercase task description
            config: Skill configuration

        Returns:
            Tuple of (score, matched_keywords)
        """
        score = 0.0
        matches = []
        weight = config.get("weight", 1.0)

        for keyword in config["keywords"]:
            # Check for whole word match (more weight) or substring match
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, task_lower):
                score += 2.0 * weight  # Whole word match
                matches.append(keyword)
            elif keyword.lower() in task_lower:
                score += 1.0 * weight  # Substring match
                matches.append(keyword)

        return score, matches

    def get_all_routes(self, task_description: str) -> List[SkillRoute]:
        """
        Get all matching routes sorted by confidence.

        Args:
            task_description: Description of the task

        Returns:
            List of SkillRoute objects sorted by confidence (highest first)
        """
        if not task_description:
            return []

        task_lower = task_description.lower()
        routes = []

        for role, config in self.skill_map.items():
            score, matches = self._calculate_score(task_lower, config)
            if score > 0:
                max_possible = len(config["keywords"]) * config.get("weight", 1.0)
                confidence = min(score / max_possible * 2, 1.0)

                routes.append(SkillRoute(
                    role=role,
                    skill_file=str(self.skills_path / config["file"]),
                    confidence=confidence,
                    matched_keywords=matches[:5],
                    agent_name=config["agent"]
                ))

        # Sort by confidence (highest first)
        routes.sort(key=lambda r: r.confidence, reverse=True)
        return routes

    def suggest_skill(self, task_description: str) -> str:
        """
        Get a human-readable skill suggestion.

        Args:
            task_description: Description of the task

        Returns:
            Formatted suggestion string
        """
        route = self.route(task_description)

        if not route:
            return "No specific skill matched. Consider using bmad-quick-flow.md for simple tasks."

        config = self.skill_map[route.role]

        return f"""## Skill Recommendation

**Recommended Agent:** {config['name']} ({route.agent_name})
**Confidence:** {route.confidence:.0%}
**Skill File:** `{route.skill_file}`

**Matched Keywords:** {', '.join(route.matched_keywords)}

**Next Steps:**
1. Load skill: `cat {route.skill_file}`
2. Follow the BMAD workflow for {route.agent_name}
3. Execute with appropriate commands

**Alternative Skills:**
{self._get_alternatives(task_description, route.role)}
"""

    def _get_alternatives(self, task_description: str, exclude_role: SkillRole) -> str:
        """Get alternative skill suggestions."""
        routes = self.get_all_routes(task_description)
        alternatives = [r for r in routes if r.role != exclude_role and r.confidence > 0.3][:2]

        if not alternatives:
            return "None with significant match."

        lines = []
        for alt in alternatives:
            config = self.skill_map[alt.role]
            lines.append(f"- {config['name']} ({alt.agent_name}) - {alt.confidence:.0%} match")

        return '\n'.join(lines)

    def load_skill_content(self, route: SkillRoute) -> Optional[str]:
        """
        Load the skill file content.

        Args:
            route: SkillRoute with skill file path

        Returns:
            Skill file content or None if not found
        """
        try:
            path = Path(route.skill_file)
            if path.exists():
                return path.read_text()
            else:
                logger.warning(f"Skill file not found: {path}")
                return None
        except Exception as e:
            logger.error(f"Failed to load skill content: {e}")
            return None


def main():
    """CLI interface for skill routing."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="BMAD Skill Router")
    parser.add_argument("task", nargs="?", help="Task description to route")
    parser.add_argument("--all", "-a", action="store_true", help="Show all matching routes")
    parser.add_argument("--file", "-f", help="Read task from file")
    parser.add_argument("--skill-path", "-p", help="Path to skills directory")

    args = parser.parse_args()

    # Get task description
    if args.file:
        task = Path(args.file).read_text()
    elif args.task:
        task = args.task
    else:
        # Read from stdin
        task = sys.stdin.read()

    if not task.strip():
        print("Error: No task description provided", file=sys.stderr)
        sys.exit(1)

    # Initialize router
    skills_path = Path(args.skill_path) if args.skill_path else None
    router = SkillRouter(skills_path)

    if args.all:
        # Show all routes
        routes = router.get_all_routes(task)
        print(f"## All Matching Routes ({len(routes)} found)\n")
        for i, route in enumerate(routes, 1):
            config = router.skill_map[route.role]
            print(f"{i}. **{config['name']}** ({route.agent_name})")
            print(f"   Confidence: {route.confidence:.0%}")
            print(f"   File: {route.skill_file}")
            print(f"   Keywords: {', '.join(route.matched_keywords)}")
            print()
    else:
        # Show best match
        print(router.suggest_skill(task))


if __name__ == "__main__":
    main()
