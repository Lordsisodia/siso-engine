"""
Agent Loader for Blackbox 5

This module provides dynamic agent loading and registration functionality.
Discovers agents from configured paths and manages the agent registry.
"""

import asyncio
import importlib
import importlib.util
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base_agent import BaseAgent, AgentConfig, AgentTask, AgentResult

# Import Claude Code execution mixin for YAML agents
import sys
# Path is: 2-engine/core/agents/definitions/core/agent_loader.py
# We need to reach: 2-engine/ to import from core/interface/client/
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from core.interface.client.ClaudeCodeAgentMixin import ClaudeCodeAgentMixin

logger = logging.getLogger(__name__)


class AgentLoader:
    """
    Dynamic agent loading and registration system.

    Discovers, loads, and manages agent classes from configured directories.
    Supports both Python modules and YAML-based agent definitions.
    """

    def __init__(self, agents_path: Optional[Path] = None):
        """
        Initialize the agent loader.

        Args:
            agents_path: Path to directory containing agent definitions
        """
        # Default to the agents directory (parent of this core module)
        if agents_path is None:
            # Path is: 2-engine/01-core/agents/core/agent_loader.py
            # We want: 2-engine/01-core/agents/
            agents_path = Path(__file__).parent.parent
        self.agents_path = agents_path
        self._loaded_agents: Dict[str, Type[BaseAgent]] = {}
        self._agent_instances: Dict[str, BaseAgent] = {}

        logger.info(f"AgentLoader initialized with path: {self.agents_path}")

    async def load_all(self) -> Dict[str, BaseAgent]:
        """
        Load all available agents from the configured path.

        Searches for agent definitions in:
        1. Python modules with BaseAgent subclasses
        2. YAML agent definition files

        Returns:
            Dictionary mapping agent names to agent instances
        """
        logger.info("Loading all agents...")

        # Load Python agents
        await self._load_python_agents()

        # Load YAML agents
        await self._load_yaml_agents()

        # Instantiate all loaded agent classes
        for name, agent_class in self._loaded_agents.items():
            if name not in self._agent_instances:
                try:
                    # Get config from agent class
                    if hasattr(agent_class, 'get_default_config'):
                        config = agent_class.get_default_config()
                    else:
                        # Create default config
                        config = AgentConfig(
                            name=name,
                            full_name=agent_class.__name__,
                            role=agent_class.__name__.replace('Agent', ''),
                            category='general',
                            description=f"Auto-generated config for {agent_class.__name__}"
                        )

                    instance = agent_class(config)
                    self._agent_instances[name] = instance
                    logger.info(f"Instantiated agent: {name}")

                except Exception as e:
                    logger.error(f"Failed to instantiate agent {name}: {e}")

        logger.info(f"Loaded {len(self._agent_instances)} agents")

        return self._agent_instances

    async def _load_python_agents(self) -> None:
        """Load agents from Python modules."""
        if not self.agents_path.exists():
            logger.warning(f"Agents path does not exist: {self.agents_path}")
            return

        # Find all Python files
        python_files = list(self.agents_path.rglob("*.py"))

        for py_file in python_files:
            # Skip __init__ and test files
            if py_file.name.startswith("__") or "test" in py_file.name.lower():
                continue

            try:
                await self._load_agent_from_file(py_file)
            except Exception as e:
                logger.debug(f"Failed to load agents from {py_file}: {e}")

    async def _load_agent_from_file(self, file_path: Path) -> None:
        """
        Load agent classes from a Python file.

        Args:
            file_path: Path to Python file
        """
        # Create module spec
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)

        if spec is None or spec.loader is None:
            logger.debug(f"Could not create spec for {file_path}")
            return

        # Load module
        module = importlib.util.module_from_spec(spec)
        sys_modules = sys.modules  # type: ignore
        sys_modules[module_name] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            logger.debug(f"Failed to load module {module_name}: {e}")
            return

        # Find BaseAgent subclasses
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and
                issubclass(obj, BaseAgent) and
                obj is not BaseAgent and
                not obj.__name__.startswith('_')):

                logger.info(f"Found agent class: {name} in {file_path}")
                self._loaded_agents[name] = obj

    async def _load_yaml_agents(self) -> None:
        """
        Load agents from YAML definition files.

        YAML agents are converted to Python classes dynamically.
        """
        yaml_files = list(self.agents_path.rglob("*.yaml")) + list(self.agents_path.rglob("*.yml"))

        for yaml_file in yaml_files:
            # Skip non-agent YAML files (look for agent or specialist in filename)
            if "agent" not in yaml_file.name.lower() and "specialist" not in yaml_file.name.lower():
                continue

            try:
                await self._load_agent_from_yaml(yaml_file)
            except Exception as e:
                logger.debug(f"Failed to load agent from {yaml_file}: {e}")

    async def _load_agent_from_yaml(self, yaml_file: Path) -> None:
        """
        Load an agent from a YAML definition file.

        Args:
            yaml_file: Path to YAML file
        """
        try:
            import yaml
        except ImportError:
            logger.warning("PyYAML not installed, skipping YAML agents")
            return

        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)

        if not data or 'agent' not in data:
            return

        agent_data = data['agent']
        metadata = agent_data.get('metadata', {})
        persona = agent_data.get('persona', {})

        # Create agent name from metadata
        agent_id = metadata.get('id', '').replace('/', '_').replace('.md', '')
        if not agent_id:
            agent_id = yaml_file.stem

        # Extract capabilities from YAML (can be list of strings or list of dicts with 'name')
        raw_caps = agent_data.get('capabilities', [])
        capabilities = []
        for cap in raw_caps:
            if isinstance(cap, str):
                capabilities.append(cap)
            elif isinstance(cap, dict) and 'name' in cap:
                capabilities.append(cap['name'])
            else:
                logger.debug(f"Unexpected capability format: {cap}")

        # Also extract tags as capabilities for routing
        tags = metadata.get('tags', [])
        capabilities.extend(tags)

        # Create config
        config = AgentConfig(
            name=metadata.get('name', agent_id),
            full_name=metadata.get('title', agent_id.replace('_', ' ').title()),
            role=persona.get('role', 'Agent'),
            category='specialists',
            description=persona.get('identity', ''),
            capabilities=capabilities,
        )

        # Create dynamic agent class
        class YamlAgent(BaseAgent, ClaudeCodeAgentMixin):
            # Store config as class attribute for get_default_config
            _yaml_config = config
            # Claude Code configuration
            claude_timeout = 300  # 5 minutes
            claude_mcp_profile = "standard"  # Default profile for specialists

            @classmethod
            def get_default_config(cls) -> AgentConfig:
                """Return the config loaded from YAML."""
                return cls._yaml_config

            def __init__(self, cfg: AgentConfig):
                """Initialize YamlAgent with both BaseAgent and ClaudeCodeAgentMixin."""
                BaseAgent.__init__(self, cfg)
                ClaudeCodeAgentMixin.__init__(self)
                self.yaml_data = data

            async def execute(self, task: AgentTask) -> AgentResult:
                """
                Execute a task using Claude Code CLI with the YAML agent's persona.

                Args:
                    task: The task to execute

                Returns:
                    AgentResult with Claude's response
                """
                thinking_steps = await self.think(task)

                # Build persona-based prompt from YAML configuration
                prompt = self._build_persona_prompt(task)

                # Execute with Claude Code CLI
                claude_result = await self.execute_with_claude(
                    task_description=prompt,
                    mcp_profile=self._select_mcp_profile(task)
                )

                return AgentResult(
                    success=claude_result.get("success", False),
                    output=claude_result.get("output", ""),
                    thinking_steps=thinking_steps,
                    metadata={
                        "agent_name": self.name,
                        "agent_role": self.config.role,
                        "yaml_source": str(yaml_file),
                        "execution_engine": "claude-code-cli",
                        "duration": claude_result.get("metadata", {}).get("duration", 0),
                        "mcp_profile": claude_result.get("metadata", {}).get("mcp_profile", "standard"),
                    }
                )

            def _build_persona_prompt(self, task: AgentTask) -> str:
                """Build a prompt based on the YAML agent's persona and configuration."""
                persona = self.yaml_data.get('agent', {}).get('persona', {})
                metadata = self.yaml_data.get('agent', {}).get('metadata', {})

                # Extract persona details
                role = persona.get('role', 'Specialist')
                identity = persona.get('identity', f"You are a {role} specialist.")
                tone_guidance = persona.get('tone', 'professional')
                domain_expertise = persona.get('domain_expertise', [])

                # Build the prompt
                prompt_parts = [
                    f"# Role: {self.config.full_name}",
                    f"",
                    f"## Identity",
                    f"{identity}",
                    f"",
                    f"## Role",
                    f"You are a **{role}** with specialized expertise.",
                    f"",
                ]

                # Add domain expertise if available
                if domain_expertise:
                    prompt_parts.extend([
                        f"## Domain Expertise",
                        f"You have deep knowledge in:",
                    ])
                    for domain in domain_expertise[:5]:  # Limit to top 5
                        prompt_parts.append(f"- {domain}")
                    prompt_parts.append("")

                # Add tone/style guidance
                prompt_parts.extend([
                    f"## Communication Style",
                    f"- Tone: {tone_guidance}",
                    f"- Be direct, actionable, and thorough",
                    f"- Provide specific examples and code when relevant",
                    f"",
                ])

                # Add capabilities context
                if self.config.capabilities:
                    prompt_parts.extend([
                        f"## Your Capabilities",
                        f"You specialize in: {', '.join(self.config.capabilities[:8])}",
                        f"",
                    ])

                # Add the task
                prompt_parts.extend([
                    f"## Task",
                    f"{task.description}",
                    f"",
                    f"Please complete this task according to your specialist expertise.",
                    f"Use markdown formatting with clear headings and structured content.",
                ])

                return "\n".join(prompt_parts)

            def _select_mcp_profile(self, task: AgentTask) -> str:
                """Select appropriate MCP profile based on task keywords."""
                task_lower = task.description.lower()

                # Check for browser automation needs
                browser_keywords = ["browser", "scrape", "screenshot", "web page", "ui test", "visual"]
                if any(kw in task_lower for kw in browser_keywords):
                    return "automation"

                # Check for research/documentation needs
                research_keywords = ["research", "documentation", "lookup", "find", "investigate"]
                if any(kw in task_lower for kw in research_keywords):
                    return "data"

                # Check for web/API needs
                web_keywords = ["api", "http", "web", "fetch", "url", "endpoint"]
                if any(kw in task_lower for kw in web_keywords):
                    return "standard"

                # Check for file operations
                file_keywords = ["read file", "write file", "create file", "analyze code", "review code"]
                if any(kw in task_lower for kw in file_keywords):
                    return "filesystem"

                # Default to standard for most specialist tasks
                return "standard"

            async def think(self, task: AgentTask) -> List[str]:
                """Generate thinking steps for YAML agent tasks."""
                persona = self.yaml_data.get('agent', {}).get('persona', {})
                role = persona.get('role', 'Specialist')
                return [
                    f"👤 {role} {self.name} analyzing task",
                    f"📋 Understanding requirements: {task.description[:80]}...",
                    f"🎯 Applying specialist expertise",
                    f"💡 Developing domain-specific solution",
                    f"✅ Formulating actionable recommendations",
                ]

        # Set class name
        YamlAgent.__name__ = metadata.get('title', agent_id).replace(' ', '')

        self._loaded_agents[agent_id] = YamlAgent
        logger.info(f"Loaded YAML agent: {agent_id}")

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Get an agent instance by name.

        Args:
            name: Agent name

        Returns:
            Agent instance or None if not found
        """
        return self._agent_instances.get(name)

    def list_agents(self) -> List[str]:
        """
        List all loaded agent names.

        Returns:
            List of agent names
        """
        return list(self._agent_instances.keys())

    def get_agent_info(self, name: str) -> Optional[Dict[str, any]]:
        """
        Get information about an agent.

        Args:
            name: Agent name

        Returns:
            Agent info dictionary or None if not found
        """
        agent = self.get_agent(name)
        if agent:
            return agent.get_capabilities()
        return None

    async def reload_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Reload a specific agent.

        Args:
            name: Agent name to reload

        Returns:
            Reloaded agent instance or None if not found
        """
        # Remove old instance
        if name in self._agent_instances:
            del self._agent_instances[name]

        # Reload all agents
        await self.load_all()

        return self.get_agent(name)


# Import sys for module loading
import sys
