"""
Automatic Skill Router for BMAD

Routes tasks to appropriate BMAD skills based on keyword matching.
Part of Agent-2.3 automatic skill routing feature.

Updated for folder-based skill structure (Anthropic Standard).
"""

import re
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
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
    PLANNING = "planning"    # Planning Agent (BMAD Framework)
    WEB_SEARCH = "web-search"  # Web Search utility
    RUN_INIT = "run-init"    # Run Initialization
    CONTINUOUS_IMPROVEMENT = "continuous-improvement"  # Continuous Improvement
    RALF_CLOUD = "ralf-cloud"  # RALF Cloud Control
    LEGACY_CLOUD = "legacy-cloud"  # Legacy Cloud Control
    GITHUB_CODESPACES = "github-codespaces"  # GitHub Codespaces Control
    TRUTH_SEEKING = "truth-seeking"  # Truth-Seeking Protocol
    GIT_COMMIT = "git-commit"  # Git Commit
    TASK_SELECTION = "task-selection"  # Task Selection
    STATE_MANAGEMENT = "state-management"  # State Management
    SUPABASE_OPERATIONS = "supabase-operations"  # Supabase Operations
    CODEBASE_NAVIGATION = "codebase-navigation"  # Codebase Navigation


@dataclass
class SkillRoute:
    """Result of skill routing."""
    role: SkillRole
    skill_name: str
    skill_path: Path
    confidence: float  # 0.0 to 1.0
    matched_keywords: List[str]
    agent_name: str
    skill_metadata: Dict[str, Any]


@dataclass
class SkillMetadata:
    """Parsed skill metadata from SKILL.md frontmatter."""
    name: str
    description: str
    category: str
    agent: Optional[str] = None
    role: Optional[str] = None
    trigger: Optional[str] = None
    keywords: List[str] = None
    commands: List[str] = None
    weight: float = 1.0

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.commands is None:
            self.commands = []


# Skill routing configuration - maps roles to skill folders
# Keywords are used for matching; skills are loaded from SKILL.md files
SKILL_MAP: Dict[SkillRole, Dict] = {
    SkillRole.PM: {
        "name": "Product Manager",
        "agent": "John",
        "folder": "bmad-pm",
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
        "folder": "bmad-architect",
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
        "folder": "bmad-analyst",
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
        "folder": "bmad-sm",
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
        "folder": "bmad-ux",
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
        "folder": "bmad-dev",
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
        "folder": "bmad-qa",
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
        "folder": "bmad-tea",
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
        "folder": "bmad-quick-flow",
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
        "folder": "superintelligence-protocol",
        "keywords": [
            "protocol", "superintelligence", "deep analysis", "architecture decision",
            "complex problem", "multi-dimensional", "system design", "redesign",
            "optimize", "uncertain", "novel", "high impact", "cross-cutting",
            "first principles", "expert analysis", "synthesize"
        ],
        "weight": 1.3  # Higher weight to catch complex tasks
    },
    SkillRole.PLANNING: {
        "name": "Planning Agent",
        "agent": "Planner",
        "folder": "bmad-planning",
        "keywords": [
            "plan", "planning", "breakdown", "epic", "task breakdown",
            "prd", "product requirements", "roadmap", "milestone",
            "bmad", "business analysis", "model design", "architecture design",
            "development plan", "project structure", "generate tasks",
            "create plan", "vibe kanban", "kanban cards", "assign tasks"
        ],
        "weight": 1.1  # Slightly higher to catch planning tasks
    },
    SkillRole.WEB_SEARCH: {
        "name": "Web Search",
        "agent": None,
        "folder": "web-search",
        "keywords": [
            "search", "web search", "google", "find online", "look up",
            "research online", "current information", "latest", "news"
        ],
        "weight": 1.0
    },
    SkillRole.RUN_INIT: {
        "name": "Run Initialization",
        "agent": None,
        "folder": "run-initialization",
        "keywords": [
            "initialize run", "start run", "new run", "create run",
            "setup run", "run folder", "init run"
        ],
        "weight": 1.0
    },
    SkillRole.CONTINUOUS_IMPROVEMENT: {
        "name": "Continuous Improvement",
        "agent": None,
        "folder": "continuous-improvement",
        "keywords": [
            "improve", "optimize", "refine", "iterate", "learn",
            "retrospective", "lessons learned", "post-mortem"
        ],
        "weight": 1.0
    },
    SkillRole.RALF_CLOUD: {
        "name": "RALF Cloud Control",
        "agent": None,
        "folder": "ralf-cloud-control",
        "keywords": [
            "ralf cloud", "kubernetes", "k8s", "cloud agent",
            "spawn ralf", "scale ralf", "ralf status"
        ],
        "weight": 1.0
    },
    SkillRole.LEGACY_CLOUD: {
        "name": "Legacy Cloud Control",
        "agent": None,
        "folder": "legacy-cloud-control",
        "keywords": [
            "legacy cloud", "legacy kubernetes", "legacy k8s",
            "spawn legacy", "scale legacy", "legacy status"
        ],
        "weight": 1.0
    },
    SkillRole.GITHUB_CODESPACES: {
        "name": "GitHub Codespaces Control",
        "agent": None,
        "folder": "github-codespaces-control",
        "keywords": [
            "codespace", "github codespace", "cloud dev environment",
            "spawn codespace", "create codespace"
        ],
        "weight": 1.0
    },
    SkillRole.TRUTH_SEEKING: {
        "name": "Truth-Seeking Protocol",
        "agent": None,
        "folder": "truth-seeking",
        "keywords": [
            "validate", "verify", "assumption", "fact check",
            "truth", "confidence", "self-correct", "validation"
        ],
        "weight": 1.1
    },
    SkillRole.GIT_COMMIT: {
        "name": "Git Commit",
        "agent": None,
        "folder": "git-commit",
        "keywords": [
            "commit", "git commit", "save work", "stage",
            "push", "branch protection", "commit message"
        ],
        "weight": 1.0
    },
    SkillRole.TASK_SELECTION: {
        "name": "Task Selection",
        "agent": None,
        "folder": "task-selection",
        "keywords": [
            "select task", "next task", "pick task", "task selection",
            "what to work on", "choose task", "dependencies"
        ],
        "weight": 1.0
    },
    SkillRole.STATE_MANAGEMENT: {
        "name": "State Management",
        "agent": None,
        "folder": "state-management",
        "keywords": [
            "update state", "mark complete", "state.yaml",
            "task status", "completed", "metrics"
        ],
        "weight": 1.0
    },
    SkillRole.SUPABASE_OPERATIONS: {
        "name": "Supabase Operations",
        "agent": None,
        "folder": "supabase-operations",
        "keywords": [
            "supabase", "database", "migration", "rls",
            "postgres", "sql", "table", "policy"
        ],
        "weight": 1.0
    },
    SkillRole.CODEBASE_NAVIGATION: {
        "name": "Codebase Navigation",
        "agent": None,
        "folder": "codebase-navigation",
        "keywords": [
            "find", "where is", "how does", "locate",
            "search codebase", "find file", "find function"
        ],
        "weight": 1.0
    }
}


class SkillRouter:
    """
    Routes tasks to appropriate BMAD skills based on content analysis.
    Loads skills from folder-based structure following Anthropic Standard.
    """

    def __init__(self, skills_path: Optional[Path] = None):
        """
        Initialize the skill router.

        Args:
            skills_path: Path to skills directory
        """
        self.skills_path = skills_path or Path(__file__).parent.parent / "skills"
        self.skill_map = SKILL_MAP
        self._skill_metadata_cache: Dict[str, SkillMetadata] = {}

    def _parse_skill_md(self, skill_folder: str) -> Optional[SkillMetadata]:
        """
        Parse SKILL.md file to extract metadata from YAML frontmatter.

        Args:
            skill_folder: Name of the skill folder

        Returns:
            SkillMetadata or None if parsing fails
        """
        if skill_folder in self._skill_metadata_cache:
            return self._skill_metadata_cache[skill_folder]

        skill_file = self.skills_path / skill_folder / "SKILL.md"
        if not skill_file.exists():
            logger.warning(f"SKILL.md not found: {skill_file}")
            return None

        try:
            content = skill_file.read_text()

            # Parse YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    metadata = SkillMetadata(
                        name=frontmatter.get('name', skill_folder),
                        description=frontmatter.get('description', ''),
                        category=frontmatter.get('category', 'unknown'),
                        agent=frontmatter.get('agent'),
                        role=frontmatter.get('role'),
                        trigger=frontmatter.get('trigger'),
                        keywords=frontmatter.get('keywords', []),
                        commands=frontmatter.get('commands', []),
                        weight=frontmatter.get('weight', 1.0)
                    )
                    self._skill_metadata_cache[skill_folder] = metadata
                    return metadata

        except Exception as e:
            logger.error(f"Failed to parse SKILL.md for {skill_folder}: {e}")

        return None

    def _get_skill_path(self, role: SkillRole) -> Optional[Path]:
        """
        Get the path to a skill's SKILL.md file.

        Args:
            role: SkillRole to look up

        Returns:
            Path to SKILL.md or None if not found
        """
        config = self.skill_map.get(role)
        if not config:
            return None

        folder = config.get("folder")
        if not folder:
            return None

        skill_path = self.skills_path / folder / "SKILL.md"
        if skill_path.exists():
            return skill_path

        return None

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

        # Get skill path
        skill_path = self._get_skill_path(best_role)
        if not skill_path:
            return None

        # Parse metadata
        metadata = self._parse_skill_md(config["folder"]) or {}

        return SkillRoute(
            role=best_role,
            skill_name=config["folder"],
            skill_path=skill_path,
            confidence=confidence,
            matched_keywords=best_matches[:5],  # Top 5 matches
            agent_name=config.get("agent", "Unknown"),
            skill_metadata=metadata.__dict__ if metadata else {}
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

                skill_path = self._get_skill_path(role)
                if skill_path:
                    metadata = self._parse_skill_md(config["folder"]) or {}

                    routes.append(SkillRoute(
                        role=role,
                        skill_name=config["folder"],
                        skill_path=skill_path,
                        confidence=confidence,
                        matched_keywords=matches[:5],
                        agent_name=config.get("agent", "Unknown"),
                        skill_metadata=metadata.__dict__ if metadata else {}
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
            return "No specific skill matched. Consider using bmad-quick-flow for simple tasks."

        config = self.skill_map[route.role]

        return f"""## Skill Recommendation

**Recommended Agent:** {config['name']} ({route.agent_name})
**Confidence:** {route.confidence:.0%}
**Skill Path:** `{route.skill_path}`

**Matched Keywords:** {', '.join(route.matched_keywords)}

**Next Steps:**
1. Load skill: `cat {route.skill_path}`
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
            if route.skill_path.exists():
                return route.skill_path.read_text()
            else:
                logger.warning(f"Skill file not found: {route.skill_path}")
                return None
        except Exception as e:
            logger.error(f"Failed to load skill content: {e}")
            return None

    def list_all_skills(self) -> List[Dict[str, Any]]:
        """
        List all available skills with their metadata.

        Returns:
            List of skill information dictionaries
        """
        skills = []
        for role, config in self.skill_map.items():
            metadata = self._parse_skill_md(config["folder"])
            skills.append({
                "role": role.value,
                "name": config["name"],
                "agent": config.get("agent"),
                "folder": config["folder"],
                "path": str(self._get_skill_path(role)) if self._get_skill_path(role) else None,
                "keywords_count": len(config["keywords"]),
                "metadata": metadata.__dict__ if metadata else None
            })
        return skills

    def discover_skills(self) -> List[str]:
        """
        Discover skills by scanning the skills directory.

        Returns:
            List of skill folder names found
        """
        discovered = []
        if not self.skills_path.exists():
            return discovered

        for item in self.skills_path.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                discovered.append(item.name)

        return discovered


def main():
    """CLI interface for skill routing."""
    import sys
    import argparse
    import json

    parser = argparse.ArgumentParser(description="BMAD Skill Router")
    parser.add_argument("task", nargs="?", help="Task description to route")
    parser.add_argument("--all", "-a", action="store_true", help="Show all matching routes")
    parser.add_argument("--file", "-f", help="Read task from file")
    parser.add_argument("--skill-path", "-p", help="Path to skills directory")
    parser.add_argument("--list", "-l", action="store_true", help="List all skills")
    parser.add_argument("--discover", "-d", action="store_true", help="Discover skills in directory")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Initialize router
    skills_path = Path(args.skill_path) if args.skill_path else None
    router = SkillRouter(skills_path)

    if args.list:
        # List all skills
        skills = router.list_all_skills()
        if args.json:
            print(json.dumps(skills, indent=2))
        else:
            print("## Available Skills\n")
            for skill in skills:
                agent_info = f" (Agent: {skill['agent']})" if skill['agent'] else ""
                print(f"- **{skill['name']}**{agent_info}")
                print(f"  Folder: {skill['folder']}")
                print(f"  Keywords: {skill['keywords_count']}")
                print()
        return

    if args.discover:
        # Discover skills in directory
        discovered = router.discover_skills()
        print("## Discovered Skills\n")
        for skill in discovered:
            print(f"- {skill}/")
        return

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

    if args.all:
        # Show all routes
        routes = router.get_all_routes(task)
        if args.json:
            output = [
                {
                    "role": r.role.value,
                    "name": router.skill_map[r.role]["name"],
                    "agent": r.agent_name,
                    "confidence": r.confidence,
                    "path": str(r.skill_path),
                    "keywords": r.matched_keywords
                }
                for r in routes
            ]
            print(json.dumps(output, indent=2))
        else:
            print(f"## All Matching Routes ({len(routes)} found)\n")
            for i, route in enumerate(routes, 1):
                config = router.skill_map[route.role]
                print(f"{i}. **{config['name']}** ({route.agent_name})")
                print(f"   Confidence: {route.confidence:.0%}")
                print(f"   Path: {route.skill_path}")
                print(f"   Keywords: {', '.join(route.matched_keywords)}")
                print()
    else:
        # Show best match
        if args.json:
            route = router.route(task)
            if route:
                output = {
                    "role": route.role.value,
                    "name": router.skill_map[route.role]["name"],
                    "agent": route.agent_name,
                    "confidence": route.confidence,
                    "path": str(route.skill_path),
                    "keywords": route.matched_keywords,
                    "metadata": route.skill_metadata
                }
                print(json.dumps(output, indent=2))
            else:
                print(json.dumps({"error": "No matching skill found"}))
        else:
            print(router.suggest_skill(task))


if __name__ == "__main__":
    main()
