#!/usr/bin/env python3
"""
RALF Configuration Manager
============================

Provides configuration management for RALF system components.
Supports loading, validating, and accessing configuration values
with fallback to defaults.

Author: RALF System
Version: 1.0.0
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigManager:
    """
    Configuration manager for RALF system.

    Provides:
    - Load YAML configuration files
    - Validate configuration values
    - Access nested configuration values
    - Fallback to defaults when config missing/invalid
    - Runtime configuration updates
    """

    def __init__(self, config_path: Optional[str] = None, default_config_path: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to user configuration file (optional)
            default_config_path: Path to default configuration file (optional)
        """
        self.config_path = config_path
        self.default_config_path = default_config_path
        self.config: Dict[str, Any] = {}
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load configuration from file(s) with fallback to defaults."""
        # Load default configuration first
        default_config = self._load_default_config()

        # Load user configuration if provided
        user_config = {}
        if self.config_path and os.path.exists(self.config_path):
            try:
                user_config = self._load_yaml_file(self.config_path)
                logger.info(f"Loaded user configuration from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load user configuration: {e}. Using defaults.")
                user_config = {}
        else:
            logger.info(f"User configuration not found at {self.config_path}. Using defaults.")

        # Merge configurations (user config overrides defaults)
        self.config = self._merge_configs(default_config, user_config)

        # Validate merged configuration
        try:
            self.validate_config(self.config)
        except ConfigValidationError as e:
            logger.error(f"Configuration validation failed: {e}. Using defaults.")
            self.config = default_config

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration from default config file."""
        if self.default_config_path and os.path.exists(self.default_config_path):
            return self._load_yaml_file(self.default_config_path)
        else:
            logger.warning(f"Default configuration not found at {self.default_config_path}. Using built-in defaults.")
            return self._get_builtin_defaults()

    def _load_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load YAML file and return as dictionary.

        Args:
            file_path: Path to YAML file

        Returns:
            Dictionary containing YAML content

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}

    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge user configuration with default configuration.

        Args:
            default: Default configuration dictionary
            user: User configuration dictionary

        Returns:
            Merged configuration dictionary
        """
        result = default.copy()

        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._merge_configs(result[key], value)
            else:
                # User value overrides default
                result[key] = value

        return result

    def _get_builtin_defaults(self) -> Dict[str, Any]:
        """
        Get built-in default configuration.

        Returns:
            Default configuration dictionary
        """
        return {
            'version': '1.0',
            'thresholds': {
                'skill_invocation_confidence': 70,
                'queue_depth_min': 3,
                'queue_depth_max': 5,
                'loop_timeout_seconds': 120,
            },
            'routing': {
                'default_agent': 'executor',
                'task_type_routing': {
                    'feature': 'executor',
                    'fix': 'executor',
                    'research': 'executor',
                    'refactor': 'executor',
                    'analyze': 'executor',
                }
            },
            'notifications': {
                'enabled': False,
                'on_task_completion': False,
                'on_error': True,
                'on_milestone': False,
            }
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration values.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if validation passes

        Raises:
            ConfigValidationError: If validation fails
        """
        # Validate thresholds
        if 'thresholds' in config:
            thresholds = config['thresholds']

            # Validate skill_invocation_confidence (0-100)
            if 'skill_invocation_confidence' in thresholds:
                confidence = thresholds['skill_invocation_confidence']
                if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 100):
                    raise ConfigValidationError(
                        f"skill_invocation_confidence must be between 0 and 100, got {confidence}"
                    )

            # Validate queue_depth_min (positive integer)
            if 'queue_depth_min' in thresholds:
                min_depth = thresholds['queue_depth_min']
                if not isinstance(min_depth, int) or min_depth < 0:
                    raise ConfigValidationError(
                        f"queue_depth_min must be a non-negative integer, got {min_depth}"
                    )

            # Validate queue_depth_max (positive integer, >= min)
            if 'queue_depth_max' in thresholds:
                max_depth = thresholds['queue_depth_max']
                if not isinstance(max_depth, int) or max_depth < 0:
                    raise ConfigValidationError(
                        f"queue_depth_max must be a non-negative integer, got {max_depth}"
                    )

                # Check that max >= min
                if 'queue_depth_min' in thresholds and max_depth < thresholds['queue_depth_min']:
                    raise ConfigValidationError(
                        f"queue_depth_max ({max_depth}) must be >= queue_depth_min ({thresholds['queue_depth_min']})"
                    )

            # Validate loop_timeout_seconds (positive integer)
            if 'loop_timeout_seconds' in thresholds:
                timeout = thresholds['loop_timeout_seconds']
                if not isinstance(timeout, int) or timeout < 0:
                    raise ConfigValidationError(
                        f"loop_timeout_seconds must be a non-negative integer, got {timeout}"
                    )

        # Validate routing
        if 'routing' in config:
            routing = config['routing']

            if 'default_agent' in routing:
                default_agent = routing['default_agent']
                valid_agents = ['executor', 'planner', 'analyst']
                if default_agent not in valid_agents:
                    raise ConfigValidationError(
                        f"default_agent must be one of {valid_agents}, got {default_agent}"
                    )

        return True

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by key path (supports nested keys).

        Args:
            key_path: Dot-separated key path (e.g., "thresholds.skill_invocation_confidence")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Examples:
            >>> config.get("thresholds.skill_invocation_confidence")
            70
            >>> config.get("routing.default_agent")
            "executor"
            >>> config.get("missing.key", "default_value")
            "default_value"
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value at runtime (not persisted to file).

        Args:
            key_path: Dot-separated key path (e.g., "thresholds.skill_invocation_confidence")
            value: Value to set

        Examples:
            >>> config.set("thresholds.skill_invocation_confidence", 80)
            >>> config.set("routing.default_agent", "planner")
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

        logger.info(f"Set {key_path} = {value} (runtime only, not persisted)")

    def save_config(self, file_path: Optional[str] = None) -> None:
        """
        Save current configuration to file.

        Args:
            file_path: Path to save configuration (defaults to self.config_path)

        Raises:
            ValueError: If no file path specified and config_path is None
        """
        save_path = file_path or self.config_path

        if not save_path:
            raise ValueError("No file path specified for saving configuration")

        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Save configuration
        with open(save_path, 'w') as f:
            yaml.safe_dump(self.config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved configuration to {save_path}")

    def reload_config(self) -> None:
        """Reload configuration from file(s)."""
        logger.info("Reloading configuration...")
        self._load_configuration()
        logger.info("Configuration reloaded successfully")

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Complete configuration dictionary
        """
        return self.config.copy()


# Global configuration instance (singleton pattern)
_global_config: Optional[ConfigManager] = None


def get_config(config_path: Optional[str] = None, default_config_path: Optional[str] = None) -> ConfigManager:
    """
    Get global configuration instance (singleton pattern).

    Args:
        config_path: Path to user configuration file (only used on first call)
        default_config_path: Path to default configuration file (only used on first call)

    Returns:
        ConfigManager instance

    Examples:
        >>> config = get_config()
        >>> threshold = config.get("thresholds.skill_invocation_confidence")
    """
    global _global_config

    if _global_config is None:
        # Determine default paths
        if config_path is None:
            config_path = os.path.expanduser("~/.blackbox5/config.yaml")
        if default_config_path is None:
            default_config_path = os.path.join(
                os.path.dirname(__file__),
                "../config/default.yaml"
            )

        _global_config = ConfigManager(config_path, default_config_path)

    return _global_config


def reload_global_config() -> None:
    """Reload global configuration instance."""
    global _global_config

    if _global_config is not None:
        _global_config.reload_config()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Get configuration
    config = get_config()

    # Access configuration values
    print(f"Skill invocation threshold: {config.get('thresholds.skill_invocation_confidence')}")
    print(f"Queue depth target: {config.get('thresholds.queue_depth_min')}-{config.get('thresholds.queue_depth_max')}")
    print(f"Default agent: {config.get('routing.default_agent')}")

    # Set value at runtime
    config.set("thresholds.skill_invocation_confidence", 80)
    print(f"Updated threshold: {config.get('thresholds.skill_invocation_confidence')}")
