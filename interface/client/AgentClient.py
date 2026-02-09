"""
BlackBox5 Agent Client
=======================

Adapted from Auto-Claude's client.py for BlackBox5 architecture.

This module provides a generic agent client factory with:
- Project capability detection
- Tool permission management
- Project caching with TTL
- MCP server configuration support

Source: .docs/research/agents/auto-claude/apps/backend/core/client.py
Adapted for: BlackBox5 engine architecture

Key differences from Auto-Claude:
- No Claude SDK dependencies (generic structure)
- Uses Anthropic API directly (via configuration)
- Maintains caching and capability detection logic
- Prepared for future MCP server integration
"""

import copy
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# Project Index Cache
# =============================================================================
# Caches project index and capabilities to avoid reloading on every call.
# This significantly reduces the time to create new agent sessions.

_PROJECT_INDEX_CACHE: dict[str, tuple[dict[str, Any], dict[str, bool], float]] = {}
_CACHE_TTL_SECONDS = 300  # 5 minute TTL
_CACHE_LOCK = threading.Lock()  # Protects _PROJECT_INDEX_CACHE access


def _get_cached_project_data(
    project_dir: Path,
) -> tuple[dict[str, Any], dict[str, bool]]:
    """
    Get project index and capabilities with caching.

    Args:
        project_dir: Path to the project directory

    Returns:
        Tuple of (project_index, project_capabilities)
    """
    key = str(project_dir.resolve())
    now = time.time()
    debug = os.environ.get("DEBUG", "").lower() in ("true", "1")

    # Check cache with lock
    with _CACHE_LOCK:
        if key in _PROJECT_INDEX_CACHE:
            cached_index, cached_capabilities, cached_time = _PROJECT_INDEX_CACHE[key]
            cache_age = now - cached_time
            if cache_age < _CACHE_TTL_SECONDS:
                if debug:
                    print(
                        f"[AgentClientCache] Cache HIT for project index (age: {cache_age:.1f}s / TTL: {_CACHE_TTL_SECONDS}s)"
                    )
                logger.debug(f"Using cached project index for {project_dir}")
                # Return deep copies to prevent callers from corrupting the cache
                return copy.deepcopy(cached_index), copy.deepcopy(cached_capabilities)
            elif debug:
                print(
                    f"[AgentClientCache] Cache EXPIRED for project index (age: {cache_age:.1f}s > TTL: {_CACHE_TTL_SECONDS}s)"
                )

    # Cache miss or expired - load fresh data (outside lock to avoid blocking)
    load_start = time.time()
    logger.debug(f"Loading project index for {project_dir}")
    project_index = load_project_index(project_dir)
    project_capabilities = detect_project_capabilities(project_index)

    if debug:
        load_duration = (time.time() - load_start) * 1000
        print(
            f"[AgentClientCache] Cache MISS - loaded project index in {load_duration:.1f}ms"
        )

    # Store in cache with lock - use double-checked locking pattern
    # Re-check if another thread populated the cache while we were loading
    with _CACHE_LOCK:
        if key in _PROJECT_INDEX_CACHE:
            cached_index, cached_capabilities, cached_time = _PROJECT_INDEX_CACHE[key]
            cache_age = now - cached_time
            if cache_age < _CACHE_TTL_SECONDS:
                # Another thread already cached valid data while we were loading
                if debug:
                    print(
                        "[AgentClientCache] Cache was populated by another thread, using cached data"
                    )
                # Return deep copies to prevent callers from corrupting the cache
                return copy.deepcopy(cached_index), copy.deepcopy(cached_capabilities)
        # Either no cache entry or it's expired - store our fresh data
        _PROJECT_INDEX_CACHE[key] = (project_index, project_capabilities, time.time())

    # Return the freshly loaded data (no need to copy since it's not from cache)
    return project_index, project_capabilities


def invalidate_project_cache(project_dir: Optional[Path] = None) -> None:
    """
    Invalidate the project index cache.

    Args:
        project_dir: Specific project to invalidate, or None to clear all
    """
    with _CACHE_LOCK:
        if project_dir is None:
            _PROJECT_INDEX_CACHE.clear()
            logger.debug("Cleared all project index cache entries")
        else:
            key = str(project_dir.resolve())
            if key in _PROJECT_INDEX_CACHE:
                del _PROJECT_INDEX_CACHE[key]
                logger.debug(f"Invalidated project index cache for {project_dir}")


def load_project_index(project_dir: Path) -> dict:
    """
    Load project_index.json from the project's blackbox5 directory.

    Adapted from Auto-Claude's prompts_pkg/project_context.py

    Args:
        project_dir: Root directory of the project

    Returns:
        Parsed project index dict, or empty dict if not found
    """
    index_file = project_dir / "blackbox5" / "project_index.json"
    if not index_file.exists():
        logger.debug(f"No project index found at {index_file}")
        return {}

    try:
        with open(index_file, encoding="utf-8") as f:
            index = json.load(f)
            logger.debug(f"Loaded project index from {index_file}")
            return index
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load project index from {index_file}: {e}")
        return {}


def detect_project_capabilities(project_index: dict) -> dict:
    """
    Detect what tools and capabilities are relevant for this project.

    Adapted from Auto-Claude's prompts_pkg/project_context.py

    Analyzes the project_index.json to identify:
    - Desktop app frameworks (Electron, Tauri)
    - Mobile frameworks (Expo, React Native)
    - Web frontend frameworks (React, Vue, Next.js, etc.)
    - Backend capabilities (APIs, databases)

    Args:
        project_index: Parsed project_index.json dict

    Returns:
        Dictionary of capability flags:
        - is_electron: True if project uses Electron
        - is_tauri: True if project uses Tauri
        - is_expo: True if project uses Expo
        - is_react_native: True if project uses React Native
        - is_web_frontend: True if project has web frontend (React, Vue, etc.)
        - is_nextjs: True if project uses Next.js
        - is_nuxt: True if project uses Nuxt
        - has_api: True if project has API routes
        - has_database: True if project has database connections
    """
    capabilities = {
        # Desktop app frameworks
        "is_electron": False,
        "is_tauri": False,
        # Mobile frameworks
        "is_expo": False,
        "is_react_native": False,
        # Web frontend frameworks
        "is_web_frontend": False,
        "is_nextjs": False,
        "is_nuxt": False,
        # Backend capabilities
        "has_api": False,
        "has_database": False,
    }

    services = project_index.get("services", {})

    # Handle both dict format (services by name) and list format
    if isinstance(services, dict):
        service_list = services.values()
    elif isinstance(services, list):
        service_list = services
    else:
        service_list = []

    for service in service_list:
        if not isinstance(service, dict):
            continue

        # Collect all dependencies
        deps = set()
        for dep in service.get("dependencies", []):
            if isinstance(dep, str):
                deps.add(dep.lower())
        for dep in service.get("dev_dependencies", []):
            if isinstance(dep, str):
                deps.add(dep.lower())

        # Get framework (normalize to lowercase)
        framework = str(service.get("framework", "")).lower()

        # Desktop app detection
        if "electron" in deps or any("@electron" in d for d in deps):
            capabilities["is_electron"] = True
        if "@tauri-apps/api" in deps or "tauri" in deps:
            capabilities["is_tauri"] = True

        # Mobile framework detection
        if "expo" in deps:
            capabilities["is_expo"] = True
        if "react-native" in deps:
            capabilities["is_react_native"] = True

        # Web frontend detection
        web_frameworks = ("react", "vue", "svelte", "angular", "solid")
        if framework in web_frameworks:
            capabilities["is_web_frontend"] = True

        # Meta-framework detection
        if framework in ("nextjs", "next.js", "next"):
            capabilities["is_nextjs"] = True
            capabilities["is_web_frontend"] = True
        if framework in ("nuxt", "nuxt.js"):
            capabilities["is_nuxt"] = True
            capabilities["is_web_frontend"] = True

        # Also check deps for framework indicators
        if "next" in deps:
            capabilities["is_nextjs"] = True
            capabilities["is_web_frontend"] = True
        if "nuxt" in deps:
            capabilities["is_nuxt"] = True
            capabilities["is_web_frontend"] = True
        if "vite" in deps and not capabilities["is_electron"]:
            # Vite usually indicates web frontend (unless Electron)
            capabilities["is_web_frontend"] = True

        # API detection
        api_info = service.get("api", {})
        if isinstance(api_info, dict) and api_info.get("routes"):
            capabilities["has_api"] = True

        # Database detection
        if service.get("database"):
            capabilities["has_database"] = True
        # Also check for ORM/database deps
        db_deps = {
            "prisma",
            "drizzle-orm",
            "sequelize",
            "typeorm",
            "mongoose",
            "dexie",
            "supabase",
            "postgres",
            "mysql",
            "mongodb",
            "sqlite",
        }
        if any(db_dep in deps for db_dep in db_deps):
            capabilities["has_database"] = True

    logger.debug(f"Detected project capabilities: {capabilities}")
    return capabilities


def get_tools_for_agent(
    agent_type: str,
    project_capabilities: Optional[dict] = None,
) -> list[str]:
    """
    Get the list of allowed tools for a specific agent type.

    Adapted from Auto-Claude's agents/tools_pkg/permissions.py

    This ensures each agent only sees tools relevant to their role,
    preventing context pollution and accidental misuse.

    Args:
        agent_type: Agent type identifier (e.g., 'coder', 'planner', 'qa_reviewer')
        project_capabilities: Optional dict from detect_project_capabilities()
                            containing flags like is_electron, is_web_frontend, etc.

    Returns:
        List of allowed tool names for this agent type
    """
    # Default capabilities if not provided
    if project_capabilities is None:
        project_capabilities = {}

    # Base tool sets for different agent types
    # This is a simplified version - will be expanded based on BlackBox5 needs
    agent_tool_configs = {
        "planner": {
            "base_tools": [
                "Read",
                "Write",
                "Edit",
                "Glob",
                "Grep",
                "Bash",
                "WebSearch",
                "WebFetch",
            ],
            "optional_tools": [],
        },
        "coder": {
            "base_tools": [
                "Read",
                "Write",
                "Edit",
                "Glob",
                "Grep",
                "Bash",
                "WebSearch",
                "WebFetch",
            ],
            "optional_tools": [],
        },
        "qa_reviewer": {
            "base_tools": [
                "Read",
                "Glob",
                "Grep",
                "Bash",
                "WebSearch",
                "WebFetch",
            ],
            "optional_tools": [
                # Browser tools for E2E testing
                "browser_take_screenshot",
                "browser_click",
                "browser_fill",
                "browser_navigate",
            ],
        },
        "qa_fixer": {
            "base_tools": [
                "Read",
                "Write",
                "Edit",
                "Glob",
                "Grep",
                "Bash",
                "WebSearch",
                "WebFetch",
            ],
            "optional_tools": [
                # Browser tools for E2E testing
                "browser_take_screenshot",
                "browser_click",
                "browser_fill",
                "browser_navigate",
            ],
        },
    }

    # Get config for this agent type
    config = agent_tool_configs.get(agent_type, {"base_tools": [], "optional_tools": []})

    # Start with base tools
    allowed_tools = list(config["base_tools"])

    # Add optional tools based on project capabilities
    optional_tools = config.get("optional_tools", [])

    # Browser tools for web/electron projects
    if agent_type in ("qa_reviewer", "qa_fixer"):
        if project_capabilities.get("is_electron") or project_capabilities.get(
            "is_web_frontend"
        ):
            # Filter browser tools from optional_tools
            browser_tools = [t for t in optional_tools if t.startswith("browser_")]
            allowed_tools.extend(browser_tools)

    logger.debug(f"Tools for {agent_type}: {allowed_tools}")
    return allowed_tools


def create_client(
    project_dir: Path,
    model: str = "claude-sonnet-4-5-20250929",
    agent_type: str = "coder",
    max_thinking_tokens: Optional[int] = None,
) -> dict:
    """
    Create an agent client configuration for BlackBox5.

    Adapted from Auto-Claude's create_client() function

    This is a factory function that returns a configuration dict
    that can be used with the Anthropic API or future SDK integration.

    Args:
        project_dir: Root directory for the project (working directory)
        model: Claude model to use
        agent_type: Agent type identifier (e.g., 'coder', 'planner', 'qa_reviewer')
        max_thinking_tokens: Token budget for extended thinking (None = disabled)

    Returns:
        Configuration dict with:
        - model: Model name
        - system_prompt: System prompt for the agent
        - allowed_tools: List of allowed tools
        - project_capabilities: Detected project capabilities
        - max_thinking_tokens: Extended thinking budget

    Note:
        This is a generic structure that will be extended with:
        - Anthropic API client configuration
        - MCP server integration
        - Security hooks
    """
    # Load project capabilities
    project_index, project_capabilities = _get_cached_project_data(project_dir)

    # Get allowed tools for this agent type
    allowed_tools = get_tools_for_agent(agent_type, project_capabilities)

    # Build system prompt with output format for agent-to-agent communication
    base_prompt = (
        f"You are an expert full-stack developer building production-quality software. "
        f"Your working directory is: {project_dir.resolve()}\n"
        f"Your filesystem access is RESTRICTED to this directory only. "
        f"Use relative paths (starting with ./) for all file operations. "
        f"Never use absolute paths or try to access files outside your working directory.\n\n"
        f"You follow existing code patterns, write clean maintainable code, and verify "
        f"your work through thorough testing. You communicate progress through Git commits "
        f"and build-progress.txt updates.\n\n"
        f"## CRITICAL: Output Format for Agent Communication\n\n"
        f"Every response MUST use this exact format:\n\n"
        f"```markdown\n"
        f"<output>\n"
        f"{{\n"
        f'  "status": "success|partial|failed",\n'
        f'  "summary": "One sentence describing what you did",\n'
        f'  "deliverables": ["file1.ts", "file2.ts", "artifact-name"],\n'
        f'  "next_steps": ["action1", "action2"],\n'
        f'  "metadata": {{\n'
        f'    "agent": "your-agent-name",\n'
        f'    "task_id": "from-input",\n'
        f'    "duration_seconds": 0\n'
        f'  }}\n'
        f"}}\n"
        f"---\n"
        f"[Your full explanation here - code, reasoning, details for humans]\n"
        f"</output>\n"
        f"```\n\n"
        f"The JSON block at top (inside <output> tags) is for OTHER AGENTS to parse.\n"
        f"The content after --- is for HUMANS to read.\n"
        f"Always include both parts - this enables agent coordination."
    )

    # Log configuration
    logger.info(f"Creating {agent_type} client for {project_dir}")
    logger.info(f"Model: {model}")
    logger.info(f"Max thinking tokens: {max_thinking_tokens or 'disabled'}")
    logger.info(f"Project capabilities: {project_capabilities}")
    logger.info(f"Allowed tools: {len(allowed_tools)} tools")

    # Return configuration dict
    config = {
        "model": model,
        "system_prompt": base_prompt,
        "allowed_tools": allowed_tools,
        "project_capabilities": project_capabilities,
        "max_thinking_tokens": max_thinking_tokens,
        "project_dir": str(project_dir.resolve()),
    }

    return config
