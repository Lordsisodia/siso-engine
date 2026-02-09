#!/usr/bin/env python3
"""
Path Resolution Library
=======================

Unified path resolution for BlackBox5 components.
Eliminates hardcoded paths throughout the codebase.

Usage:
    from paths import PathResolver, get_path_resolver

    # Get resolver instance
    resolver = get_path_resolver()

    # Access common paths
    engine_path = resolver.engine_path
    project_path = resolver.get_project_path("blackbox5")
    runs_path = resolver.get_runs_path("blackbox5")

    # Build custom paths
    custom = resolver.get_path("custom", "subdir")
"""

import os
from pathlib import Path
from typing import Optional, Union


class PathResolver:
    """
    Resolves all BlackBox5 system paths.

    Eliminates hardcoded paths by providing a centralized
    configuration-based path resolution system.

    Path Hierarchy (highest to lowest precedence):
        1. Environment variables (BLACKBOX5_HOME, BB5_*)
        2. User config (~/.blackbox5/config/user.yaml)
        3. Project config (project/.autonomous/config/project.yaml)
        4. Engine config (2-engine/configuration/engine.yaml)
        5. Base defaults
    """

    def __init__(self, project_name: Optional[str] = None):
        """
        Initialize path resolver.

        Args:
            project_name: Default project name for project-relative paths
        """
        self.project_name = project_name or os.environ.get('BB5_PROJECT', 'blackbox5')
        self._bb5_root: Optional[Path] = None
        self._engine_root: Optional[Path] = None
        self._memory_root: Optional[Path] = None

    @property
    def blackbox5_root(self) -> Path:
        """Get BlackBox5 root directory (~/.blackbox5)."""
        if self._bb5_root is None:
            root = os.environ.get('BLACKBOX5_HOME') or os.environ.get('BB5_HOME')
            if root:
                self._bb5_root = Path(os.path.expanduser(root))
            else:
                self._bb5_root = Path.home() / '.blackbox5'
        return self._bb5_root

    @property
    def engine_path(self) -> Path:
        """Get engine root directory (2-engine)."""
        if self._engine_root is None:
            engine = os.environ.get('BB5_ENGINE_ROOT')
            if engine:
                self._engine_root = Path(os.path.expanduser(engine))
            else:
                # Default: parent of this file's parent (.autonomous)
                self._engine_root = Path(__file__).parent.parent
        return self._engine_root

    @property
    def lib_path(self) -> Path:
        """Get library directory path."""
        return self.engine_path / '.autonomous' / 'lib'

    @property
    def config_path(self) -> Path:
        """Get engine config directory path."""
        return self.engine_path / '.autonomous' / 'config'

    @property
    def prompts_path(self) -> Path:
        """Get prompts directory path."""
        return self.engine_path / '.autonomous' / 'prompts'

    @property
    def hooks_path(self) -> Path:
        """Get hooks directory path."""
        return self.engine_path / '.autonomous' / 'hooks'

    @property
    def bin_path(self) -> Path:
        """Get bin directory path."""
        return self.engine_path / '.autonomous' / 'bin'

    @property
    def templates_path(self) -> Path:
        """Get templates directory path."""
        return self.engine_path / '.autonomous' / 'templates'

    @property
    def memory_root(self) -> Path:
        """Get project memory root directory (5-project-memory)."""
        if self._memory_root is None:
            memory = os.environ.get('BB5_MEMORY_PATH')
            if memory:
                self._memory_root = Path(os.path.expanduser(memory))
            else:
                self._memory_root = self.blackbox5_root / '5-project-memory'
        return self._memory_root

    @property
    def docs_root(self) -> Path:
        """Get documentation root directory (1-docs)."""
        return self.blackbox5_root / '1-docs'

    @property
    def bin_root(self) -> Path:
        """Get tools/bin root directory (bin)."""
        return self.blackbox5_root / 'bin'

    @property
    def roadmap_root(self) -> Path:
        """Get roadmap directory (6-roadmap)."""
        return self.blackbox5_root / '6-roadmap'

    def get_project_path(self, project_name: Optional[str] = None) -> Path:
        """
        Get project directory path.

        Args:
            project_name: Project name (defaults to initialized project)

        Returns:
            Path to project directory
        """
        name = project_name or self.project_name
        return self.memory_root / name

    def get_project_config_path(self, project_name: Optional[str] = None) -> Path:
        """
        Get project configuration file path.

        Args:
            project_name: Project name (defaults to initialized project)

        Returns:
            Path to project.yaml config file
        """
        return self.get_project_path(project_name) / '.autonomous' / 'config' / 'project.yaml'

    def get_runs_path(self, project_name: Optional[str] = None) -> Path:
        """
        Get runs directory path for a project.

        Args:
            project_name: Project name (defaults to initialized project)

        Returns:
            Path to runs directory
        """
        return self.get_project_path(project_name) / '.autonomous' / 'runs'

    def get_tasks_path(self, project_name: Optional[str] = None, status: str = 'active') -> Path:
        """
        Get tasks directory path for a project.

        Args:
            project_name: Project name (defaults to initialized project)
            status: Task status - 'active', 'completed', 'archived'

        Returns:
            Path to tasks directory
        """
        return self.get_project_path(project_name) / '.autonomous' / 'tasks' / status

    def get_memory_path(self, project_name: Optional[str] = None) -> Path:
        """
        Get memory directory path for a project.

        Args:
            project_name: Project name (defaults to initialized project)

        Returns:
            Path to memory directory
        """
        return self.get_project_path(project_name) / '.autonomous' / 'memory'

    def get_analysis_path(self, project_name: Optional[str] = None) -> Path:
        """
        Get analysis directory path for a project.

        Args:
            project_name: Project name (defaults to initialized project)

        Returns:
            Path to analysis directory
        """
        return self.get_project_path(project_name) / '.autonomous' / 'analysis'

    def get_timeline_path(self, project_name: Optional[str] = None) -> Path:
        """
        Get timeline directory path for a project.

        Args:
            project_name: Project name (defaults to initialized project)

        Returns:
            Path to timeline directory
        """
        return self.get_project_path(project_name) / '.autonomous' / 'timeline'

    def get_routes_path(self) -> Path:
        """
        Get routes.yaml file path.

        Returns:
            Path to routes.yaml
        """
        return self.engine_path / '.autonomous' / 'config' / 'routes.yaml'

    def get_run_path(self, run_id: str, project_name: Optional[str] = None) -> Path:
        """
        Get specific run directory path.

        Args:
            run_id: Run identifier (e.g., 'run-001')
            project_name: Project name (defaults to initialized project)

        Returns:
            Path to run directory
        """
        return self.get_runs_path(project_name) / run_id

    def get_task_path(self, task_id: str, project_name: Optional[str] = None) -> Path:
        """
        Get specific task directory path.

        Args:
            task_id: Task identifier (e.g., 'TASK-001')
            project_name: Project name (defaults to initialized project)

        Returns:
            Path to task directory
        """
        # Try active first, then completed
        active_path = self.get_tasks_path(project_name, 'active') / task_id
        if active_path.exists():
            return active_path
        return self.get_tasks_path(project_name, 'completed') / task_id

    def get_path(self, *parts: Union[str, Path]) -> Path:
        """
        Build a path relative to BlackBox5 root.

        Args:
            *parts: Path components

        Returns:
            Combined path
        """
        return self.blackbox5_root.joinpath(*parts)

    def get_engine_path(self, *parts: Union[str, Path]) -> Path:
        """
        Build a path relative to engine root.

        Args:
            *parts: Path components

        Returns:
            Combined path
        """
        return self.engine_path.joinpath(*parts)

    def get_project_subpath(self, *parts: Union[str, Path], project_name: Optional[str] = None) -> Path:
        """
        Build a path relative to project root.

        Args:
            *parts: Path components
            project_name: Project name (defaults to initialized project)

        Returns:
            Combined path
        """
        return self.get_project_path(project_name).joinpath(*parts)

    def ensure_dir(self, path: Union[str, Path]) -> Path:
        """
        Ensure directory exists, creating if necessary.

        Args:
            path: Directory path

        Returns:
            Path object (directory is created)
        """
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj

    def exists(self, path: Union[str, Path]) -> bool:
        """
        Check if path exists.

        Args:
            path: Path to check

        Returns:
            True if exists
        """
        return Path(path).exists()


# Global instance cache
_resolver_instance: Optional[PathResolver] = None


def get_path_resolver(project_name: Optional[str] = None) -> PathResolver:
    """
    Get global PathResolver instance.

    Args:
        project_name: Optional project name override

    Returns:
        PathResolver instance (cached)
    """
    global _resolver_instance
    if _resolver_instance is None or (project_name and _resolver_instance.project_name != project_name):
        _resolver_instance = PathResolver(project_name=project_name)
    return _resolver_instance


def reset_path_resolver() -> None:
    """Reset global resolver instance (useful for testing)."""
    global _resolver_instance
    _resolver_instance = None


# Convenience functions for common paths
def get_blackbox5_root() -> Path:
    """Get BlackBox5 root directory."""
    return get_path_resolver().blackbox5_root


def get_engine_path() -> Path:
    """Get engine root directory."""
    return get_path_resolver().engine_path


def get_memory_root() -> Path:
    """Get project memory root directory."""
    return get_path_resolver().memory_root


def get_routes_path() -> Path:
    """Get routes.yaml file path."""
    return get_path_resolver().get_routes_path()


# RALF-specific path functions with environment variable support
# These provide the interface expected by RALF agent scripts

def get_ralf_project_dir() -> Path:
    """
    Get RALF project directory from environment or default.

    Environment Variable:
        RALF_PROJECT_DIR: Override project directory path
        Falls back to BB5_PROJECT_ROOT, then default path

    Returns:
        Path to project directory
    """
    env_path = os.environ.get('RALF_PROJECT_DIR')
    if env_path:
        return Path(os.path.expanduser(env_path))

    # Try BB5_PROJECT_ROOT
    bb5_root = os.environ.get('BB5_PROJECT_ROOT')
    if bb5_root:
        return Path(os.path.expanduser(bb5_root))

    # Default via resolver
    return get_path_resolver().get_project_path()


def get_ralf_engine_dir() -> Path:
    """
    Get RALF engine directory from environment or default.

    Environment Variable:
        RALF_ENGINE_DIR: Override engine directory path
        Falls back to BB5_ENGINE_ROOT, then default path

    Returns:
        Path to engine directory
    """
    env_path = os.environ.get('RALF_ENGINE_DIR')
    if env_path:
        return Path(os.path.expanduser(env_path))

    # Try BB5_ENGINE_ROOT
    bb5_engine = os.environ.get('BB5_ENGINE_ROOT')
    if bb5_engine:
        return Path(os.path.expanduser(bb5_engine))

    # Default: ~/.blackbox5/2-engine
    return get_blackbox5_root() / '2-engine'


def validate_ralf_paths() -> tuple[Path, Path]:
    """
    Validate and return RALF project and engine paths.

    Returns:
        Tuple of (project_dir, engine_dir)

    Raises:
        FileNotFoundError: If project or engine directory doesn't exist
    """
    project_dir = get_ralf_project_dir()
    engine_dir = get_ralf_engine_dir()

    errors = []

    if not project_dir.exists():
        errors.append(
            f"RALF_PROJECT_DIR does not exist: {project_dir}\n"
            f"Set RALF_PROJECT_DIR environment variable or create directory"
        )

    if not engine_dir.exists():
        errors.append(
            f"RALF_ENGINE_DIR does not exist: {engine_dir}\n"
            f"Set RALF_ENGINE_DIR environment variable or create directory"
        )

    if errors:
        raise FileNotFoundError("\n\n".join(errors))

    return project_dir, engine_dir


def setup_ralf_lib_path() -> None:
    """
    Add engine lib to sys.path for RALF scripts.

    This should be called at the top of project-based RALF scripts
    that need to import from the engine lib.
    """
    import sys
    engine_lib = get_ralf_engine_dir() / '.autonomous' / 'lib'
    if engine_lib.exists():
        engine_lib_str = str(engine_lib)
        if engine_lib_str not in sys.path:
            sys.path.insert(0, engine_lib_str)


if __name__ == "__main__":
    # Demo usage
    resolver = get_path_resolver()

    print("BlackBox5 Path Resolution")
    print("=" * 50)
    print(f"BlackBox5 Root: {resolver.blackbox5_root}")
    print(f"Engine Path: {resolver.engine_path}")
    print(f"Lib Path: {resolver.lib_path}")
    print(f"Config Path: {resolver.config_path}")
    print(f"Memory Root: {resolver.memory_root}")
    print(f"Docs Root: {resolver.docs_root}")
    print(f"Bin Root: {resolver.bin_root}")
    print()
    print(f"Project Path: {resolver.get_project_path()}")
    print(f"Runs Path: {resolver.get_runs_path()}")
    print(f"Tasks Path: {resolver.get_tasks_path()}")
    print(f"Memory Path: {resolver.get_memory_path()}")
    print(f"Analysis Path: {resolver.get_analysis_path()}")
    print(f"Routes Path: {resolver.get_routes_path()}")
    print()
    print("RALF Path Resolution")
    print("=" * 50)
    print(f"RALF Project Dir: {get_ralf_project_dir()}")
    print(f"RALF Engine Dir:  {get_ralf_engine_dir()}")
    print(f"Environment:")
    print(f"  RALF_PROJECT_DIR: {os.environ.get('RALF_PROJECT_DIR', '(not set)')}")
    print(f"  RALF_ENGINE_DIR:  {os.environ.get('RALF_ENGINE_DIR', '(not set)')}")
