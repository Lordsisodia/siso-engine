"""
Spec-Driven Development Pipeline

This module provides the core infrastructure for spec-driven development,
integrating PRD, Epic, and Task generation with GitHub integration.
"""

from .config import Config, load_config
from .prd_agent import PRDAgent, PRDParser, PRDValidator, PRDData
from .epic_agent import (
    EpicAgent,
    EpicParser,
    EpicValidator,
    EpicData,
    TechnicalDecisionMaker,
    ArchitectureGenerator,
    ComponentBreakdown,
    EpicStatus,
    TechnicalDecision,
    Component,
    ImplementationPhase,
)
from .exceptions import (
    SpecDrivenException,
    PRDValidationError,
    EpicValidationError,
    TaskValidationError,
    GitHubSyncError,
)

__all__ = [
    # Config
    "Config",
    "load_config",

    # PRD Agent
    "PRDAgent",
    "PRDParser",
    "PRDValidator",
    "PRDData",

    # Epic Agent
    "EpicAgent",
    "EpicParser",
    "EpicValidator",
    "EpicData",
    "TechnicalDecisionMaker",
    "ArchitectureGenerator",
    "ComponentBreakdown",
    "EpicStatus",
    "TechnicalDecision",
    "Component",
    "ImplementationPhase",

    # Exceptions
    "SpecDrivenException",
    "PRDValidationError",
    "EpicValidationError",
    "TaskValidationError",
    "GitHubSyncError",
]
