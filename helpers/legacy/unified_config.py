#!/usr/bin/env python3
"""
Unified Configuration Manager
==============================

A single hierarchical configuration system that consolidates 20+ config files
into a unified hierarchy with clear precedence.

Configuration Hierarchy (Highest to Lowest Precedence):
    1. Environment Variables (deployment-specific)
    2. User Config (~/.blackbox5/config/user.yaml)
    3. Project Config (5-project-memory/[project]/.autonomous/config/project.yaml)
    4. Engine Config (2-engine/configuration/engine.yaml)
    5. Base Defaults (2-engine/configuration/base.yaml)

Author: RALF System
Version: 2.0.0
"""

import os
import re
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass, field
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigNotFoundError(Exception):
    """Raised when configuration file is not found."""
    pass


@dataclass
class ConfigPaths:
    """Configuration file paths."""
    base_defaults: str = ""
    engine_config: str = ""
    project_config: str = ""
    user_config: str = ""


class UnifiedConfig:
    """
    Unified configuration manager with hierarchical loading.

    Features:
    - Hierarchical loading with precedence
    - Environment variable substitution
    - Schema validation
    - Caching for performance
    - Backward compatibility with ConfigManager
    """

    # Environment variable pattern: ${VAR_NAME} or ${VAR_NAME:-default}
    ENV_VAR_PATTERN = re.compile(r'\$\{(\w+)(?::-([^}]*))?\}')

    # Configuration hierarchy (highest to lowest precedence)
    CONFIG_HIERARCHY = [
        'user',
        'project',
        'engine',
        'base'
    ]

    def __init__(self, project_name: Optional[str] = None, auto_load: bool = True):
        """
        Initialize unified configuration.

        Args:
            project_name: Name of the project (for project config lookup)
            auto_load: Whether to automatically load configuration on init
        """
        self.project_name = project_name or os.environ.get('BB5_PROJECT', 'blackbox5')
        self.config: Dict[str, Any] = {}
        self.paths = ConfigPaths()
        self._loaded_sources: List[str] = []
        self._cache: Dict[str, Any] = {}

        if auto_load:
            self.load()

    def _get_blackbox5_root(self) -> str:
        """Get BlackBox5 root directory."""
        # Check environment variable first
        root = os.environ.get('BLACKBOX5_HOME') or os.environ.get('BB5_HOME')
        if root:
            return os.path.expanduser(root)

        # Default to ~/.blackbox5
        return os.path.expanduser('~/.blackbox5')

    def _resolve_config_paths(self) -> ConfigPaths:
        """Resolve all configuration file paths."""
        bb5_root = self._get_blackbox5_root()

        # Determine engine root (parent of .autonomous/lib)
        engine_root = Path(__file__).parent.parent

        paths = ConfigPaths()

        # Base defaults (lowest precedence)
        paths.base_defaults = str(engine_root / 'config' / 'base.yaml')

        # Engine config
        paths.engine_config = str(engine_root / 'config' / 'engine.yaml')

        # Project config
        project_config_dir = Path(bb5_root) / '5-project-memory' / self.project_name / '.autonomous' / 'config'
        paths.project_config = str(project_config_dir / 'project.yaml')

        # User config (highest precedence file-based)
        paths.user_config = os.path.expanduser('~/.blackbox5/config/user.yaml')

        return paths

    def load(self, custom_paths: Optional[ConfigPaths] = None) -> 'UnifiedConfig':
        """
        Load configuration from all sources in hierarchy.

        Args:
            custom_paths: Optional custom paths to use instead of resolved paths

        Returns:
            Self for method chaining
        """
        if custom_paths:
            self.paths = custom_paths
        elif not self.paths.base_defaults:
            self.paths = self._resolve_config_paths()

        self.config = {}
        self._loaded_sources = []

        # Load from lowest to highest precedence
        # Each level overrides the previous

        # 1. Base defaults (lowest precedence)
        if os.path.exists(self.paths.base_defaults):
            base_config = self._load_yaml_file(self.paths.base_defaults)
            self.config = base_config
            self._loaded_sources.append(f"base:{self.paths.base_defaults}")
            logger.debug(f"Loaded base defaults from {self.paths.base_defaults}")

        # 2. Engine config
        if os.path.exists(self.paths.engine_config):
            engine_config = self._load_yaml_file(self.paths.engine_config)
            self.config = self._deep_merge(self.config, engine_config)
            self._loaded_sources.append(f"engine:{self.paths.engine_config}")
            logger.debug(f"Loaded engine config from {self.paths.engine_config}")

        # 3. Project config
        if os.path.exists(self.paths.project_config):
            project_config = self._load_yaml_file(self.paths.project_config)
            self.config = self._deep_merge(self.config, project_config)
            self._loaded_sources.append(f"project:{self.paths.project_config}")
            logger.debug(f"Loaded project config from {self.paths.project_config}")

        # 4. User config (highest file precedence)
        if os.path.exists(self.paths.user_config):
            user_config = self._load_yaml_file(self.paths.user_config)
            self.config = self._deep_merge(self.config, user_config)
            self._loaded_sources.append(f"user:{self.paths.user_config}")
            logger.debug(f"Loaded user config from {self.paths.user_config}")

        # 5. Environment variables (highest precedence)
        self._apply_environment_overrides()

        # Substitute environment variables in values
        self.config = self._substitute_env_vars(self.config)

        logger.info(f"Configuration loaded from {len(self._loaded_sources)} sources")
        return self

    def _load_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load YAML file and return as dictionary.

        Args:
            file_path: Path to YAML file

        Returns:
            Dictionary containing YAML content
        """
        try:
            with open(file_path, 'r') as f:
                content = yaml.safe_load(f)
                return content if content else {}
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML from {file_path}: {e}")
            raise ConfigValidationError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise ConfigNotFoundError(f"Cannot load config from {file_path}: {e}")

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge override into base.

        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary

        Returns:
            Merged configuration dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Override value
                result[key] = value

        return result

    def _substitute_env_vars(self, obj: Any) -> Any:
        """
        Recursively substitute environment variables in strings.

        Supports:
        - ${VAR_NAME} - Substitutes with env var or empty string
        - ${VAR_NAME:-default} - Substitutes with env var or default value

        Args:
            obj: Object to process (dict, list, or string)

        Returns:
            Object with environment variables substituted
        """
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            def replace_var(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) is not None else ''
                return os.environ.get(var_name, default_value)

            return self.ENV_VAR_PATTERN.sub(replace_var, obj)
        else:
            return obj

    def _apply_environment_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # Map of environment variables to config paths
        env_mappings = {
            'BB5_LOG_LEVEL': 'system.log_level',
            'BB5_DEBUG': 'system.debug_mode',
            'BB5_PROJECT_ROOT': 'paths.project_root',
            'BB5_ENGINE_ROOT': 'paths.engine',
            'BB5_MEMORY_PATH': 'paths.memory',
            'BB5_API_HOST': 'api.host',
            'BB5_API_PORT': 'api.port',
            'BB5_DB_HOST': 'database.host',
            'BB5_DB_PORT': 'database.port',
            'BB5_DB_NAME': 'database.name',
            'GITHUB_TOKEN': 'integrations.github.token',
            'SLACK_WEBHOOK_URL': 'integrations.slack.webhook_url',
        }

        for env_var, config_path in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert boolean strings
                if value.lower() in ('true', '1', 'yes'):
                    value = True
                elif value.lower() in ('false', '0', 'no'):
                    value = False
                # Convert numeric strings
                elif value.isdigit():
                    value = int(value)

                self.set(config_path, value)
                logger.debug(f"Applied environment override: {env_var} -> {config_path}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by key path.

        Args:
            key_path: Dot-separated key path (e.g., "paths.engine")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Examples:
            >>> config.get("paths.engine")
            "/Users/.../.blackbox5/2-engine"
            >>> config.get("system.log_level")
            "INFO"
            >>> config.get("missing.key", "default")
            "default"
        """
        # Check cache first
        cache_key = f"get:{key_path}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        # Cache result
        self._cache[cache_key] = value
        return value

    def get_path(self, key_path: str, default: str = "") -> Path:
        """
        Get configuration value as Path object.

        Args:
            key_path: Dot-separated key path
            default: Default path if key not found

        Returns:
            Path object
        """
        value = self.get(key_path, default)
        return Path(os.path.expanduser(value)) if value else Path(default)

    def get_bool(self, key_path: str, default: bool = False) -> bool:
        """
        Get configuration value as boolean.

        Args:
            key_path: Dot-separated key path
            default: Default value if key not found

        Returns:
            Boolean value
        """
        value = self.get(key_path, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)

    def get_int(self, key_path: str, default: int = 0) -> int:
        """
        Get configuration value as integer.

        Args:
            key_path: Dot-separated key path
            default: Default value if key not found

        Returns:
            Integer value
        """
        value = self.get(key_path, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def get_list(self, key_path: str, default: Optional[List] = None) -> List:
        """
        Get configuration value as list.

        Args:
            key_path: Dot-separated key path
            default: Default value if key not found

        Returns:
            List value
        """
        value = self.get(key_path, default or [])
        if isinstance(value, list):
            return value
        return [value] if value else []

    def set(self, key_path: str, value: Any) -> 'UnifiedConfig':
        """
        Set configuration value at runtime.

        Args:
            key_path: Dot-separated key path
            value: Value to set

        Returns:
            Self for method chaining
        """
        keys = key_path.split('.')
        config_ref = self.config

        # Navigate to parent dictionary
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]

        # Set value
        config_ref[keys[-1]] = value

        # Clear cache
        self._cache.clear()

        logger.debug(f"Set {key_path} = {value}")
        return self

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Complete configuration dictionary
        """
        return self.config.copy()

    def get_loaded_sources(self) -> List[str]:
        """
        Get list of loaded configuration sources.

        Returns:
            List of source identifiers
        """
        return self._loaded_sources.copy()

    def reload(self) -> 'UnifiedConfig':
        """
        Reload configuration from all sources.

        Returns:
            Self for method chaining
        """
        logger.info("Reloading configuration...")
        self._cache.clear()
        return self.load()

    def save(self, file_path: Optional[str] = None, source: str = 'user') -> 'UnifiedConfig':
        """
        Save current configuration to file.

        Args:
            file_path: Path to save configuration (defaults to user config)
            source: Which config source to save to (user, project, engine)

        Returns:
            Self for method chaining
        """
        if file_path is None:
            if source == 'user':
                file_path = self.paths.user_config
            elif source == 'project':
                file_path = self.paths.project_config
            elif source == 'engine':
                file_path = self.paths.engine_config
            else:
                raise ValueError(f"Unknown source: {source}")

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Save configuration
        with open(file_path, 'w') as f:
            yaml.safe_dump(self.config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved configuration to {file_path}")
        return self

    def validate(self) -> bool:
        """
        Validate configuration against schema.

        Returns:
            True if validation passes

        Raises:
            ConfigValidationError: If validation fails
        """
        # Load schema if available
        schema_path = Path(__file__).parent.parent / 'config' / 'schema.yaml'
        if not schema_path.exists():
            logger.warning("Schema file not found, skipping validation")
            return True

        try:
            with open(schema_path, 'r') as f:
                schema = yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load schema: {e}")
            return True

        # Validate against schema
        self._validate_against_schema(self.config, schema)

        logger.info("Configuration validation passed")
        return True

    def _validate_against_schema(self, config: Dict[str, Any], schema: Dict[str, Any], path: str = "") -> None:
        """
        Recursively validate configuration against schema.

        Args:
            config: Configuration to validate
            schema: Schema to validate against
            path: Current path for error reporting
        """
        for key, schema_def in schema.items():
            current_path = f"{path}.{key}" if path else key

            # Check required fields
            if schema_def.get('required', False) and key not in config:
                raise ConfigValidationError(f"Required field missing: {current_path}")

            if key not in config:
                continue

            value = config[key]
            expected_type = schema_def.get('type')

            # Type validation
            if expected_type == 'string' and not isinstance(value, str):
                raise ConfigValidationError(f"{current_path} must be a string")
            elif expected_type == 'int' and not isinstance(value, int):
                raise ConfigValidationError(f"{current_path} must be an integer")
            elif expected_type == 'bool' and not isinstance(value, bool):
                raise ConfigValidationError(f"{current_path} must be a boolean")
            elif expected_type == 'list' and not isinstance(value, list):
                raise ConfigValidationError(f"{current_path} must be a list")
            elif expected_type == 'dict' and not isinstance(value, dict):
                raise ConfigValidationError(f"{current_path} must be a dictionary")

            # Pattern validation
            if 'pattern' in schema_def and isinstance(value, str):
                import re
                if not re.match(schema_def['pattern'], value):
                    raise ConfigValidationError(
                        f"{current_path} does not match pattern {schema_def['pattern']}"
                    )

            # Nested validation
            if expected_type == 'dict' and 'properties' in schema_def:
                self._validate_against_schema(value, schema_def['properties'], current_path)

    def get_path_resolver(self) -> 'PathResolver':
        """
        Get path resolver for resolving system paths.

        Returns:
            PathResolver instance
        """
        return PathResolver(self)


class PathResolver:
    """
    Resolves system paths using configuration values.

    Provides a centralized way to resolve all system paths,
    eliminating hardcoded paths throughout the codebase.
    """

    def __init__(self, config: UnifiedConfig):
        """
        Initialize path resolver.

        Args:
            config: UnifiedConfig instance
        """
        self.config = config
        self._bb5_root = config._get_blackbox5_root()

    @property
    def blackbox5_root(self) -> Path:
        """Get BlackBox5 root directory."""
        return Path(self._bb5_root)

    @property
    def engine_root(self) -> Path:
        """Get engine root directory."""
        engine_path = self.config.get('paths.engine')
        if engine_path:
            return Path(os.path.expanduser(engine_path))
        return Path(__file__).parent.parent.parent

    @property
    def memory_root(self) -> Path:
        """Get project memory root directory."""
        memory_path = self.config.get('paths.memory')
        if memory_path:
            return Path(os.path.expanduser(memory_path))
        return self.blackbox5_root / '5-project-memory'

    @property
    def knowledge_root(self) -> Path:
        """Get knowledge base root directory."""
        knowledge_path = self.config.get('paths.knowledge')
        if knowledge_path:
            return Path(os.path.expanduser(knowledge_path))
        return self.blackbox5_root / '1-docs'

    @property
    def tools_root(self) -> Path:
        """Get tools root directory."""
        tools_path = self.config.get('paths.tools')
        if tools_path:
            return Path(os.path.expanduser(tools_path))
        return self.blackbox5_root / 'bin'

    @property
    def templates_root(self) -> Path:
        """Get templates root directory."""
        templates_path = self.config.get('paths.templates')
        if templates_path:
            return Path(os.path.expanduser(templates_path))
        return self.engine_root / '.autonomous' / 'templates'

    def get_project_path(self, project_name: Optional[str] = None) -> Path:
        """
        Get project directory path.

        Args:
            project_name: Project name (defaults to current project)

        Returns:
            Project directory path
        """
        name = project_name or self.config.project_name
        return self.memory_root / name

    def get_project_config_path(self, project_name: Optional[str] = None) -> Path:
        """
        Get project configuration file path.

        Args:
            project_name: Project name (defaults to current project)

        Returns:
            Project configuration file path
        """
        return self.get_project_path(project_name) / '.autonomous' / 'config' / 'project.yaml'

    def get_runs_path(self, project_name: Optional[str] = None) -> Path:
        """
        Get runs directory path for a project.

        Args:
            project_name: Project name (defaults to current project)

        Returns:
            Runs directory path
        """
        return self.get_project_path(project_name) / '.autonomous' / 'runs'

    def get_tasks_path(self, project_name: Optional[str] = None) -> Path:
        """
        Get tasks directory path for a project.

        Args:
            project_name: Project name (defaults to current project)

        Returns:
            Tasks directory path
        """
        return self.get_project_path(project_name) / '.autonomous' / 'tasks'

    def resolve(self, path_key: str, default: str = "") -> Path:
        """
        Resolve a path from configuration.

        Args:
            path_key: Configuration key for the path
            default: Default path if not found

        Returns:
            Resolved Path object
        """
        path_value = self.config.get(f'paths.{path_key}', default)
        if path_value:
            return Path(os.path.expanduser(path_value))
        return Path(default)


# Global singleton instance
_global_config: Optional[UnifiedConfig] = None


def get_config(project_name: Optional[str] = None, reload: bool = False) -> UnifiedConfig:
    """
    Get global unified configuration instance.

    Args:
        project_name: Project name (only used on first call unless reload=True)
        reload: Whether to reload configuration

    Returns:
        UnifiedConfig instance

    Examples:
        >>> config = get_config()
        >>> engine_path = config.get("paths.engine")
        >>> log_level = config.get("system.log_level")
    """
    global _global_config

    if _global_config is None or reload:
        _global_config = UnifiedConfig(project_name=project_name)

    return _global_config


def get_path_resolver(project_name: Optional[str] = None) -> PathResolver:
    """
    Get path resolver for resolving system paths.

    Args:
        project_name: Project name

    Returns:
        PathResolver instance
    """
    return get_config(project_name).get_path_resolver()


def reload_config() -> UnifiedConfig:
    """
    Reload global configuration.

    Returns:
        UnifiedConfig instance
    """
    return get_config(reload=True)


# Backward compatibility with ConfigManager
def get_legacy_config(config_path: Optional[str] = None, default_config_path: Optional[str] = None):
    """
    Get configuration with legacy ConfigManager interface.

    This function provides backward compatibility for code using the old ConfigManager.

    Args:
        config_path: Path to user configuration (ignored, for compatibility)
        default_config_path: Path to default configuration (ignored, for compatibility)

    Returns:
        UnifiedConfig instance with legacy-compatible interface
    """
    config = get_config()

    # Add legacy-compatible methods
    config.save_config = config.save
    config.reload_config = config.reload

    return config


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.DEBUG)

    # Load configuration
    config = get_config()

    print("=" * 60)
    print("Unified Configuration System")
    print("=" * 60)

    print("\nLoaded Sources:")
    for source in config.get_loaded_sources():
        print(f"  - {source}")

    print("\nConfiguration Values:")
    print(f"  Engine Path: {config.get('paths.engine', 'Not set')}")
    print(f"  Memory Path: {config.get('paths.memory', 'Not set')}")
    print(f"  Log Level: {config.get('system.log_level', 'Not set')}")

    print("\nPath Resolution:")
    resolver = config.get_path_resolver()
    print(f"  BlackBox5 Root: {resolver.blackbox5_root}")
    print(f"  Engine Root: {resolver.engine_root}")
    print(f"  Memory Root: {resolver.memory_root}")
    print(f"  Project Path: {resolver.get_project_path()}")

    print("\n" + "=" * 60)
