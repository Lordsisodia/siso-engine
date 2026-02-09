"""
Skill Manager for Blackbox 5

This module provides skill discovery, loading, and management functionality.
Skills are reusable capabilities that can be attached to agents.

Extended with Tier 2 Agent Skills Standard support:
- Tier 1: Python-based engine skills (existing)
- Tier 2: Agent Skills Standard (SKILL.md with YAML frontmatter)
"""

import asyncio
import importlib
import importlib.util
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Union
from enum import Enum

logger = logging.getLogger(__name__)


class SkillType(Enum):
    """Types of skills."""
    OPERATION = "operation"      # Executable operations
    WORKFLOW = "workflow"        # Multi-step workflows
    KNOWLEDGE = "knowledge"      # Knowledge retrieval
    INTEGRATION = "integration"  # External system integrations
    TOOL = "tool"               # Utility tools


@dataclass
class Skill:
    """Represents a Tier 1 skill that can be used by agents (Python-based)."""
    name: str
    description: str
    category: str
    skill_type: SkillType = SkillType.OPERATION
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert skill to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "type": self.skill_type.value,
            "capabilities": self.capabilities,
            "metadata": self.metadata,
            "enabled": self.enabled,
            "tier": 1,
        }


@dataclass
class AgentSkill:
    """
    Represents a Tier 2 Agent Skill (Agent Skills Standard).

    Format: SKILL.md with YAML frontmatter + Markdown content.
    Compatible with Claude Code, OpenCode, and other agent platforms.
    """
    name: str
    description: str
    tags: List[str]
    content: str
    author: Optional[str] = None
    version: Optional[str] = None
    category: str = "general"
    enabled: bool = True
    file_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert skill to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "content": self.content,
            "author": self.author,
            "version": self.version,
            "category": self.category,
            "enabled": self.enabled,
            "tier": 2,
            "file_path": str(self.file_path) if self.file_path else None,
        }

    @classmethod
    def from_markdown(cls, path: Path) -> 'AgentSkill':
        """
        Parse SKILL.md file with YAML frontmatter.

        Args:
            path: Path to SKILL.md file

        Returns:
            AgentSkill instance

        Raises:
            ValueError: If file format is invalid
            FileNotFoundError: If file doesn't exist
        """
        if not path.exists():
            raise FileNotFoundError(f"Skill file not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse YAML frontmatter
        if not content.startswith('---'):
            raise ValueError(f"Invalid SKILL.md format (missing frontmatter): {path}")

        # Split on ---
        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid SKILL.md format (incomplete frontmatter): {path}")

        frontmatter_str = parts[1].strip()
        markdown_content = parts[2].strip()

        # Parse YAML frontmatter
        try:
            import yaml
            frontmatter = yaml.safe_load(frontmatter_str)
        except ImportError:
            # Fallback: simple key-value parsing
            frontmatter = {}
            for line in frontmatter_str.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip().strip('"').strip("'")

        # Extract required fields
        name = frontmatter.get('name', path.parent.name)
        description = frontmatter.get('description', '')
        tags = frontmatter.get('tags', [])

        # Normalize tags to list (handle various YAML formats)
        if isinstance(tags, str):
            # Handle string representation like "[tag1, tag2]" or "tag1, tag2"
            tags = tags.strip('[]').split(',')
            tags = [t.strip().strip('"').strip("'") for t in tags if t.strip()]
        elif not isinstance(tags, list):
            tags = list(tags) if tags else []

        # Validate required fields
        if not name:
            raise ValueError(f"Skill missing 'name' in frontmatter: {path}")
        if not description:
            raise ValueError(f"Skill missing 'description' in frontmatter: {path}")

        return cls(
            name=name,
            description=description,
            tags=tags,
            content=markdown_content,
            author=frontmatter.get('author'),
            version=frontmatter.get('version'),
            category=frontmatter.get('category', 'general'),
            enabled=frontmatter.get('enabled', True),
            file_path=path,
        )

    def get_summary(self) -> str:
        """
        Get a summary of the skill (for progressive disclosure).

        Returns:
            Summary string with key info only
        """
        return f"""# {self.name}

**Description**: {self.description}
**Tags**: {', '.join(self.tags)}
**Author**: {self.author or 'Unknown'}
**Version**: {self.version or 'N/A'}

Use `load_skill_full` for complete content."""


class SkillManager:
    """
    Skill discovery and management system with two-tier support.

    Tier 1: Python-based engine skills (existing)
    - JSON definitions
    - Python modules
    - Engine-internal operations

    Tier 2: Agent Skills Standard (NEW)
    - SKILL.md files with YAML frontmatter
    - Located in ~/.claude/skills/
    - Cross-platform compatible
    - Token-efficient on-demand loading
    """

    def __init__(self, skills_path: Optional[Path] = None):
        """
        Initialize the skill manager.

        Args:
            skills_path: Path to directory containing Tier 1 skill definitions
        """
        self.skills_path = skills_path or Path.cwd() / ".skills"

        # Tier 1: Python-based skills (existing)
        self._skills: Dict[str, Skill] = {}
        self._skills_by_category: Dict[str, List[str]] = {}
        self._agent_skill_map: Dict[str, List[str]] = {}  # agent_name -> [skill_names]

        # Tier 2: Agent Skills Standard (NEW)
        self._tier2_skills_path = Path.home() / ".claude" / "skills"
        self._tier2_skills: Dict[str, AgentSkill] = {}
        self._tier2_tags_index: Dict[str, List[str]] = {}  # tag -> [skill_names]

        # Advanced caching with ContextManager (NEW)
        self._cache_manager: Optional['ContextManager'] = None
        self._cache_enabled = True

        logger.info(f"SkillManager initialized with Tier 1 path: {self.skills_path}")
        logger.info(f"SkillManager initialized with Tier 2 path: {self._tier2_skills_path}")

    def set_tier2_path(self, path: Path) -> None:
        """
        Set a custom Tier 2 skills path (for testing).

        Args:
            path: Path to Tier 2 skills directory
        """
        self._tier2_skills_path = path
        logger.debug(f"Tier 2 skills path set to: {path}")

    async def load_all(self) -> List[Union[Skill, AgentSkill]]:
        """
        Load all available skills from both Tier 1 and Tier 2 sources.

        Returns:
            List of all loaded skills (Tier 1 and Tier 2)
        """
        logger.info("Loading all skills (Tier 1 + Tier 2)...")

        # Load Tier 1 skills (existing)
        if self.skills_path.exists():
            await self._load_json_skills()
            await self._load_python_skills()
            self._organize_skills()
        else:
            logger.warning(f"Tier 1 skills path does not exist: {self.skills_path}")

        # Load Tier 2 skills (NEW - Agent Skills Standard)
        await self._load_tier2_skills()

        tier1_count = len(self._skills)
        tier2_count = len(self._tier2_skills)
        logger.info(f"Loaded {tier1_count} Tier 1 skills and {tier2_count} Tier 2 skills")

        return list(self._skills.values()) + list(self._tier2_skills.values())

    async def _load_json_skills(self) -> None:
        """Load skills from JSON definition files."""
        json_files = list(self.skills_path.rglob("*.json"))

        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)

                if 'name' not in data or 'description' not in data:
                    logger.debug(f"Skipping invalid skill file: {json_file}")
                    continue

                # Create skill
                skill_type = SkillType(data.get('type', 'operation'))
                skill = Skill(
                    name=data['name'],
                    description=data['description'],
                    category=data.get('category', 'general'),
                    skill_type=skill_type,
                    capabilities=data.get('capabilities', []),
                    metadata=data.get('metadata', {}),
                    enabled=data.get('enabled', True)
                )

                self._skills[skill.name] = skill
                logger.debug(f"Loaded JSON skill: {skill.name}")

            except Exception as e:
                logger.debug(f"Failed to load skill from {json_file}: {e}")

    async def _load_python_skills(self) -> None:
        """Load skills from Python modules."""
        python_files = list(self.skills_path.rglob("*.py"))

        for py_file in python_files:
            # Skip __init__ and test files
            if py_file.name.startswith("__") or "test" in py_file.name.lower():
                continue

            try:
                await self._load_skill_from_file(py_file)
            except Exception as e:
                logger.debug(f"Failed to load skills from {py_file}: {e}")

    async def _load_skill_from_file(self, file_path: Path) -> None:
        """
        Load skills from a Python file.

        Args:
            file_path: Path to Python file
        """
        # Create module spec
        module_name = f"skill_{file_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)

        if spec is None or spec.loader is None:
            return

        # Load module
        module = importlib.util.module_from_spec(spec)

        import sys
        sys_modules = sys.modules
        sys_modules[module_name] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            logger.debug(f"Failed to load skill module {module_name}: {e}")
            return

        # Find skill definitions
        for name, obj in vars(module).items():
            if name.startswith('_') or not inspect.isclass(obj):
                continue

            # Check if it's a skill class
            if hasattr(obj, '__skill_name__') or name.endswith('Skill'):
                try:
                    skill_info = getattr(obj, '__skill_info__', {})
                    skill = Skill(
                        name=getattr(obj, '__skill_name__', name),
                        description=skill_info.get('description', obj.__doc__ or ''),
                        category=skill_info.get('category', 'general'),
                        skill_type=SkillType(skill_info.get('type', 'operation')),
                        capabilities=skill_info.get('capabilities', []),
                        metadata=skill_info,
                    )
                    self._skills[skill.name] = skill
                    logger.debug(f"Loaded Python skill: {skill.name}")
                except Exception as e:
                    logger.debug(f"Failed to create skill from {name}: {e}")

    async def _load_tier2_skills(self) -> None:
        """
        Load Tier 2 skills from Agent Skills Standard directory.

        Scans ~/.claude/skills/ for SKILL.md files with YAML frontmatter.
        """
        if not self._tier2_skills_path.exists():
            logger.info(f"Tier 2 skills path does not exist yet: {self._tier2_skills_path}")
            logger.info("Create it with: mkdir -p ~/.claude/skills")
            return

        logger.info(f"Loading Tier 2 skills from: {self._tier2_skills_path}")

        # Find all SKILL.md files
        skill_files = list(self._tier2_skills_path.rglob("SKILL.md"))

        for skill_file in skill_files:
            try:
                skill = AgentSkill.from_markdown(skill_file)

                # Check if skill is enabled
                if not skill.enabled:
                    logger.debug(f"Skipping disabled skill: {skill.name}")
                    continue

                self._tier2_skills[skill.name] = skill

                # Index by tags
                for tag in skill.tags:
                    if tag not in self._tier2_tags_index:
                        self._tier2_tags_index[tag] = []
                    if skill.name not in self._tier2_tags_index[tag]:
                        self._tier2_tags_index[tag].append(skill.name)

                logger.debug(f"Loaded Tier 2 skill: {skill.name} from {skill_file}")

            except Exception as e:
                logger.warning(f"Failed to load Tier 2 skill from {skill_file}: {e}")

        logger.info(f"Loaded {len(self._tier2_skills)} Tier 2 skills")

    def _organize_skills(self) -> None:
        """Organize skills by category."""
        self._skills_by_category.clear()

        for skill_name, skill in self._skills.items():
            if skill.category not in self._skills_by_category:
                self._skills_by_category[skill.category] = []
            self._skills_by_category[skill.category].append(skill_name)

    def get_skill(self, name: str) -> Optional[Union[Skill, AgentSkill]]:
        """
        Get a skill by name (checks Tier 2 first for token efficiency).

        Args:
            name: Skill name

        Returns:
            Skill (Tier 1 or Tier 2) or None if not found
        """
        # Check Tier 2 first (more token efficient)
        if name in self._tier2_skills:
            return self._tier2_skills[name]

        # Fall back to Tier 1
        return self._skills.get(name)

    def get_skill_content(
        self,
        name: str,
        use_progressive: bool = True
    ) -> Optional[str]:
        """
        Get skill content with optional progressive disclosure.

        Args:
            name: Skill name
            use_progressive: If True, return summary for Tier 2 skills (token efficient)

        Returns:
            Skill content or summary, or None if not found
        """
        skill = self.get_skill(name)

        if skill is None:
            return None

        if isinstance(skill, AgentSkill):
            # Tier 2 skill
            if use_progressive:
                # Return summary first (progressive disclosure)
                return skill.get_summary()
            else:
                # Return full content
                return skill.content
        else:
            # Tier 1 skill
            return skill.description

    def search_skills_by_tag(self, tag: str) -> List[AgentSkill]:
        """
        Search Tier 2 skills by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of skills with this tag
        """
        skill_names = self._tier2_tags_index.get(tag, [])
        return [self._tier2_skills[name] for name in skill_names if name in self._tier2_skills]

    def list_tier2_skills(self) -> List[str]:
        """
        List all Tier 2 skill names.

        Returns:
            List of Tier 2 skill names
        """
        return list(self._tier2_skills.keys())

    def list_tier1_skills(self) -> List[str]:
        """
        List all Tier 1 skill names.

        Returns:
            List of Tier 1 skill names
        """
        return list(self._skills.keys())

    def list_all_skills(self) -> Dict[str, List[str]]:
        """
        List all skills by tier.

        Returns:
            Dict with 'tier1' and 'tier2' keys containing skill name lists
        """
        return {
            "tier1": self.list_tier1_skills(),
            "tier2": self.list_tier2_skills(),
        }

    def get_skills_by_category(self, category: str) -> List[Skill]:
        """
        Get all skills in a category.

        Args:
            category: Category name

        Returns:
            List of skills in the category
        """
        skill_names = self._skills_by_category.get(category, [])
        return [self._skills[name] for name in skill_names if name in self._skills]

    def list_categories(self) -> List[str]:
        """
        List all skill categories.

        Returns:
            List of category names
        """
        return sorted(self._skills_by_category.keys())

    def get_skills_for_agent(self, agent_name: str) -> List[Union[Skill, AgentSkill]]:
        """
        Get skills that are available for a specific agent (both tiers).

        Args:
            agent_name: Name of the agent

        Returns:
            List of skills (Tier 1 and Tier 2) available to the agent
        """
        # Check if agent has specific skills mapped
        if agent_name in self._agent_skill_map:
            skill_names = self._agent_skill_map[agent_name]
            skills = []
            for name in skill_names:
                # Check Tier 2 first
                if name in self._tier2_skills:
                    skills.append(self._tier2_skills[name])
                # Fall back to Tier 1
                elif name in self._skills:
                    skills.append(self._skills[name])
            return skills

        # Return all enabled skills from both tiers by default
        tier1_skills = [s for s in self._skills.values() if s.enabled]
        tier2_skills = [s for s in self._tier2_skills.values() if s.enabled]
        return tier1_skills + tier2_skills

    def map_skill_to_agent(self, skill_name: str, agent_name: str) -> bool:
        """
        Map a skill to an agent.

        Args:
            skill_name: Name of the skill
            agent_name: Name of the agent

        Returns:
            True if mapped successfully, False otherwise
        """
        if skill_name not in self._skills:
            logger.warning(f"Skill not found: {skill_name}")
            return False

        if agent_name not in self._agent_skill_map:
            self._agent_skill_map[agent_name] = []

        if skill_name not in self._agent_skill_map[agent_name]:
            self._agent_skill_map[agent_name].append(skill_name)
            logger.info(f"Mapped skill '{skill_name}' to agent '{agent_name}'")

        return True

    def register_skill(self, skill: Skill) -> None:
        """
        Register a new skill.

        Args:
            skill: Skill to register
        """
        self._skills[skill.name] = skill

        if skill.category not in self._skills_by_category:
            self._skills_by_category[skill.category] = []

        if skill.name not in self._skills_by_category[skill.category]:
            self._skills_by_category[skill.category].append(skill.name)

        logger.info(f"Registered skill: {skill.name}")

    def unregister_skill(self, name: str) -> bool:
        """
        Unregister a skill.

        Args:
            name: Name of skill to unregister

        Returns:
            True if unregistered, False if not found
        """
        if name in self._skills:
            skill = self._skills[name]
            category = skill.category

            del self._skills[name]

            if category in self._skills_by_category:
                self._skills_by_category[category].remove(name)

            # Remove from agent mappings
            for agent_name in self._agent_skill_map:
                if name in self._agent_skill_map[agent_name]:
                    self._agent_skill_map[agent_name].remove(name)

            logger.info(f"Unregistered skill: {name}")
            return True

        return False

    # ========== Advanced Caching with ContextManager (NEW) ==========

    def _get_cache_manager(self) -> Optional['ContextManager']:
        """
        Get or create the ContextManager for skill caching.

        Returns:
            ContextManager instance or None if not available
        """
        if self._cache_manager is None:
            try:
                # Try to import ContextManager from runtime
                from runtime.context.manager import ContextManager

                cache_root = Path.home() / ".claude" / "skills" / ".cache"
                cache_root.mkdir(parents=True, exist_ok=True)

                self._cache_manager = ContextManager(
                    context_root=cache_root,
                    max_size_mb=50.0,  # 50MB skill cache
                    enable_compression=True,
                    enable_semantic_index=False
                )
                logger.info(f"ContextManager initialized for skill caching at {cache_root}")
            except ImportError:
                # ContextManager not available, disable caching
                logger.debug("ContextManager not available, caching disabled")
                self._cache_enabled = False

        return self._cache_manager

    async def cache_skill_content(
        self,
        skill_name: str,
        content: str,
        tags: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Cache skill content using ContextManager.

        Args:
            skill_name: Name of the skill
            content: Skill content to cache
            tags: Tags for the skill (for searchability)
            metadata: Optional metadata

        Returns:
            True if cached successfully, False otherwise
        """
        if not self._cache_enabled:
            return False

        cache_mgr = self._get_cache_manager()
        if cache_mgr is None:
            return False

        try:
            await cache_mgr.add_context(
                key=f"skill:{skill_name}",
                value=content,
                metadata={
                    "type": "skill",
                    "skill_name": skill_name,
                    "cached_at": datetime.utcnow().isoformat(),
                    **(metadata or {})
                },
                tags=tags + ["skill", "cached"]  # Add standard tags
            )
            logger.debug(f"Cached skill content: {skill_name}")
            return True
        except Exception as e:
            logger.warning(f"Failed to cache skill {skill_name}: {e}")
            return False

    async def get_cached_skill_content(self, skill_name: str) -> Optional[str]:
        """
        Get skill content from cache.

        Args:
            skill_name: Name of the skill

        Returns:
            Cached content or None if not in cache
        """
        if not self._cache_enabled:
            return None

        cache_mgr = self._get_cache_manager()
        if cache_mgr is None:
            return None

        content = await cache_mgr.get_context(f"skill:{skill_name}")
        return content

    async def search_cached_skills_by_tag(self, tag: str) -> List[str]:
        """
        Search cached skills by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of skill names with this tag
        """
        if not self._cache_enabled:
            return []

        cache_mgr = self._get_cache_manager()
        if cache_mgr is None:
            return []

        skill_keys = await cache_mgr.search_by_tag(tag)
        # Remove "skill:" prefix
        return [k.replace("skill:", "") for k in skill_keys if k.startswith("skill:")]

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self._cache_enabled:
            return {"enabled": False}

        cache_mgr = self._get_cache_manager()
        if cache_mgr is None:
            return {"enabled": False}

        summary = cache_mgr.get_context_summary()
        return {
            "enabled": True,
            "total_cached_items": summary.get("total_items", 0),
            "total_size_bytes": summary.get("total_size_bytes", 0),
            "total_size_mb": summary.get("total_size_mb", 0.0),
            "utilization_percent": summary.get("utilization_percent", 0.0),
        }

    def clear_skill_cache(self) -> bool:
        """
        Clear all cached skill content.

        Returns:
            True if cleared successfully, False otherwise
        """
        if not self._cache_enabled:
            return False

        cache_mgr = self._get_cache_manager()
        if cache_mgr is None:
            return False

        cache_mgr.clear_context(confirm=True)
        logger.info("Cleared all skill cache")
        return True


# Import inspect for Python skill loading
import inspect
