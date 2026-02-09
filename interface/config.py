"""
Configuration Management for Spec-Driven Pipeline

This module handles loading, validating, and providing access to configuration
settings for the spec-driven development pipeline.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

import yaml

from .exceptions import SpecDrivenException


@dataclass
class GitHubConfig:
    """GitHub integration configuration."""

    token: Optional[str] = None
    default_branch: str = "main"
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None
    enable_auto_sync: bool = False  # Disabled by default for testing
    create_draft_prs: bool = True


@dataclass
class ValidationConfig:
    """Validation rules and thresholds."""

    strict_mode: bool = False
    require_estimates: bool = True
    require_acceptance_criteria: bool = True
    max_task_duration_hours: int = 40
    min_task_duration_hours: int = 1


@dataclass
class TaskConfig:
    """Configuration for task generation and management"""

    # Directory structure
    base_dir: Path = field(default_factory=lambda: Path.cwd() / "blackbox5")
    specs_dir: Path = field(default_factory=lambda: Path.cwd() / "blackbox5" / "specs")
    tasks_dir: Path = field(default_factory=lambda: Path.cwd() / "blackbox5" / "specs" / "tasks")

    # Task generation settings
    max_tasks_per_epic: int = 20
    default_task_priority: str = "medium"
    require_acceptance_criteria: bool = True
    require_estimates: bool = True

    # Complexity estimation
    complexity_weights: Dict[str, float] = field(default_factory=lambda: {
        "trivial": 0.5,
        "simple": 1.0,
        "moderate": 2.0,
        "complex": 4.0,
        "very_complex": 8.0
    })

    # Acceptance criteria
    min_criteria_per_task: int = 2
    max_criteria_per_task: int = 6
    default_verification_method: str = "automated_test"

    # Dependency analysis
    analyze_file_dependencies: bool = True
    auto_create_blocking_dependencies: bool = True

    # Output formatting
    include_estimates: bool = True
    include_technical_notes: bool = True
    include_traceability: bool = True

    # Validation
    validate_on_creation: bool = True
    fail_on_validation_error: bool = False

    def ensure_directories(self) -> None:
        """Ensure directories exist"""
        self.tasks_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class AgentConfig:
    """AI agent configuration."""

    model: str = "claude-opus-4-5-20251101"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout_seconds: int = 300


@dataclass
class PathConfig:
    """Path configuration for the pipeline."""

    blackbox_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    specs_dir: Path = field(init=False)
    prds_dir: Path = field(init=False)
    templates_dir: Path = field(init=False)
    examples_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    cache_dir: Path = field(init=False)

    def __post_init__(self):
        """Set up paths after initialization."""
        self.specs_dir = self.blackbox_root / "specs"
        self.prds_dir = self.specs_dir / "prds"
        self.templates_dir = self.blackbox_root / "templates" / "spec_driven"
        self.examples_dir = self.blackbox_root / "examples" / "specs" / "prds"
        self.output_dir = self.blackbox_root / "output"
        self.cache_dir = self.blackbox_root / "cache"


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[Path] = None
    console: bool = True


@dataclass
class Config:
    """
    Main configuration class for the spec-driven pipeline.

    This class aggregates all configuration sections and provides
    validation and default values.
    """

    github: GitHubConfig = field(default_factory=GitHubConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # PRD settings (legacy compatibility)
    prd_template_path: Path = field(init=False)
    prd_required_sections: list = field(init=False)

    # Environment-specific settings
    environment: str = "development"
    debug: bool = False

    def __post_init__(self):
        """Set up additional paths after initialization."""
        # Legacy paths
        self.prd_template_path = self.paths.templates_dir / "prd_first_principles.md"
        self.prd_required_sections = [
            "First Principles Analysis",
            "Requirements",
            "Success Metrics",
            "Acceptance Criteria",
            "User Stories"
        ]

    def validate(self) -> None:
        """
        Validate the configuration.

        Raises:
            SpecDrivenException: If configuration is invalid
        """
        errors = []

        # Validate GitHub config if auto-sync is enabled
        if self.github.enable_auto_sync:
            if not self.github.token:
                errors.append("GitHub token is required when auto_sync is enabled")
            if not self.github.repo_owner or not self.github.repo_name:
                errors.append("GitHub repo owner and name are required when auto_sync is enabled")

        # Validate paths exist or can be created
        try:
            self.paths.specs_dir.mkdir(parents=True, exist_ok=True)
            self.paths.prds_dir.mkdir(parents=True, exist_ok=True)
            self.paths.output_dir.mkdir(parents=True, exist_ok=True)
            self.paths.cache_dir.mkdir(parents=True, exist_ok=True)
            self.paths.templates_dir.mkdir(parents=True, exist_ok=True)
            self.paths.examples_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create required directories: {e}")

        # Validate logging level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level.upper() not in valid_levels:
            errors.append(f"Invalid logging level: {self.logging.level}")

        # Validate agent config
        if self.agent.temperature < 0 or self.agent.temperature > 2:
            errors.append(f"Agent temperature must be between 0 and 2, got {self.agent.temperature}")
        if self.agent.max_tokens < 1:
            errors.append(f"Agent max_tokens must be positive, got {self.agent.max_tokens}")

        if errors:
            raise SpecDrivenException(
                "Configuration validation failed",
                {"errors": errors}
            )

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.paths.specs_dir.mkdir(parents=True, exist_ok=True)
        self.paths.prds_dir.mkdir(parents=True, exist_ok=True)
        self.paths.output_dir.mkdir(parents=True, exist_ok=True)
        self.paths.cache_dir.mkdir(parents=True, exist_ok=True)
        self.paths.templates_dir.mkdir(parents=True, exist_ok=True)
        self.paths.examples_dir.mkdir(parents=True, exist_ok=True)

    def setup_logging(self) -> None:
        """
        Configure logging based on settings.

        Sets up both console and file logging if configured.
        """
        import logging

        level = getattr(logging, self.logging.level.upper())
        handlers: List[logging.Handler] = []

        # Console handler
        if self.logging.console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(logging.Formatter(self.logging.format))
            handlers.append(console_handler)

        # File handler
        if self.logging.file:
            self.logging.file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.logging.file)
            file_handler.setLevel(level)
            file_handler.setFormatter(logging.Formatter(self.logging.format))
            handlers.append(file_handler)

        # Configure root logger
        logging.basicConfig(
            level=level,
            handlers=handlers,
            force=True  # Override any existing configuration
        )


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from file and environment variables.

    Args:
        config_path: Path to config file (default: .blackbox5/config.yml)

    Returns:
        Config: Validated configuration object

    Raises:
        SpecDrivenException: If config cannot be loaded or is invalid
    """
    if config_path is None:
        # Default to .blackbox5/config.yml in project root
        project_root = Path.cwd()
        while project_root != project_root.parent:
            config_path = project_root / "blackbox5" / "config.yml"
            if config_path.exists():
                break
            project_root = project_root.parent
        else:
            # No config file found, use defaults
            config_path = Path("blackbox5/config.yml")

    # Start with default configuration
    config = Config()

    # Load from YAML file if it exists
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                yaml_config = yaml.safe_load(f) or {}
        except Exception as e:
            raise SpecDrivenException(
                f"Failed to load config file: {e}",
                {"config_path": str(config_path)}
            )

        # Update config with values from file
        config = _update_config_from_dict(config, yaml_config)

    # Override with environment variables
    config = _update_config_from_env(config)

    # Ensure directories exist
    config.ensure_directories()

    # Validate the final configuration
    config.validate()

    return config


def _update_config_from_dict(config: Config, data: Dict[str, Any]) -> Config:
    """
    Update configuration object with values from dictionary.

    Args:
        config: Existing configuration object
        data: Dictionary of configuration values

    Returns:
        Updated configuration object
    """
    # GitHub config
    if "github" in data:
        github_data = data["github"]
        if "token" in github_data:
            config.github.token = github_data["token"]
        if "default_branch" in github_data:
            config.github.default_branch = github_data["default_branch"]
        if "repo_owner" in github_data:
            config.github.repo_owner = github_data["repo_owner"]
        if "repo_name" in github_data:
            config.github.repo_name = github_data["repo_name"]
        if "enable_auto_sync" in github_data:
            config.github.enable_auto_sync = github_data["enable_auto_sync"]
        if "create_draft_prs" in github_data:
            config.github.create_draft_prs = github_data["create_draft_prs"]

    # Validation config
    if "validation" in data:
        validation_data = data["validation"]
        if "strict_mode" in validation_data:
            config.validation.strict_mode = validation_data["strict_mode"]
        if "require_estimates" in validation_data:
            config.validation.require_estimates = validation_data["require_estimates"]
        if "require_acceptance_criteria" in validation_data:
            config.validation.require_acceptance_criteria = validation_data["require_acceptance_criteria"]
        if "max_task_duration_hours" in validation_data:
            config.validation.max_task_duration_hours = validation_data["max_task_duration_hours"]
        if "min_task_duration_hours" in validation_data:
            config.validation.min_task_duration_hours = validation_data["min_task_duration_hours"]

    # Agent config
    if "agent" in data:
        agent_data = data["agent"]
        if "model" in agent_data:
            config.agent.model = agent_data["model"]
        if "temperature" in agent_data:
            config.agent.temperature = agent_data["temperature"]
        if "max_tokens" in agent_data:
            config.agent.max_tokens = agent_data["max_tokens"]
        if "timeout_seconds" in agent_data:
            config.agent.timeout_seconds = agent_data["timeout_seconds"]

    # Logging config
    if "logging" in data:
        logging_data = data["logging"]
        if "level" in logging_data:
            config.logging.level = logging_data["level"]
        if "format" in logging_data:
            config.logging.format = logging_data["format"]
        if "file" in logging_data:
            config.logging.file = Path(logging_data["file"]) if logging_data["file"] else None
        if "console" in logging_data:
            config.logging.console = logging_data["console"]

    # General settings
    if "environment" in data:
        config.environment = data["environment"]
    if "debug" in data:
        config.debug = data["debug"]

    return config


def _update_config_from_env(config: Config) -> Config:
    """
    Update configuration with values from environment variables.

    Environment variables take precedence over file-based config.

    Args:
        config: Existing configuration object

    Returns:
        Updated configuration object
    """
    # GitHub settings
    if os.getenv("GITHUB_TOKEN"):
        config.github.token = os.getenv("GITHUB_TOKEN")
    if os.getenv("GITHUB_REPO"):
        parts = os.getenv("GITHUB_REPO", "").split("/")
        if len(parts) == 2:
            config.github.repo_owner = parts[0]
            config.github.repo_name = parts[1]

    # Agent settings
    if os.getenv("CLAUDE_MODEL"):
        config.agent.model = os.getenv("CLAUDE_MODEL")
    if os.getenv("CLAUDE_TEMPERATURE"):
        config.agent.temperature = float(os.getenv("CLAUDE_TEMPERATURE", "0.7"))

    # Environment
    if os.getenv("ENVIRONMENT"):
        config.environment = os.getenv("ENVIRONMENT")
    if os.getenv("DEBUG"):
        config.debug = os.getenv("DEBUG").lower() in ("true", "1", "yes")

    return config
