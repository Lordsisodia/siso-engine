"""
Exceptions for the Spec-Driven Development Pipeline

This module defines custom exceptions for validation and synchronization errors
that can occur during the spec-driven development workflow.
"""

from typing import Optional, Dict, Any

__all__ = [
    "SpecDrivenException",
    "PRDValidationError",
    "EpicValidationError",
    "TaskValidationError",
    "TaskCreationError",
    "GitHubSyncError",
]


class SpecDrivenException(Exception):
    """Base exception for all spec-driven pipeline errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            details: Additional error context for debugging
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return formatted error message."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class PRDValidationError(SpecDrivenException):
    """
    Exception raised when PRD validation fails.

    This can occur when:
    - Required fields are missing
    - Data types are incorrect
    - Business rules are violated
    - Structure is invalid
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize PRD validation error.

        Args:
            message: Description of validation failure
            field: Field name that failed validation
            value: The invalid value
            details: Additional context
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = str(value)
        super().__init__(message, error_details)
        self.field = field
        self.value = value


class EpicValidationError(SpecDrivenException):
    """
    Exception raised when Epic validation fails.

    This can occur when:
    - Epic doesn't align with PRD
    - Tasks are missing or incomplete
    - Acceptance criteria are unclear
    - Dependencies are invalid
    """

    def __init__(
        self,
        message: str,
        epic_id: Optional[str] = None,
        prd_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Epic validation error.

        Args:
            message: Description of validation failure
            epic_id: ID of the epic that failed
            prd_id: ID of related PRD
            details: Additional context
        """
        error_details = details or {}
        if epic_id:
            error_details["epic_id"] = epic_id
        if prd_id:
            error_details["prd_id"] = prd_id
        super().__init__(message, error_details)
        self.epic_id = epic_id
        self.prd_id = prd_id


class TaskValidationError(SpecDrivenException):
    """
    Exception raised when Task validation fails.

    This can occur when:
    - Task doesn't align with Epic
    - Definition of done is incomplete
    - Estimates are missing or unrealistic
    - Dependencies are circular
    """

    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        epic_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Task validation error.

        Args:
            message: Description of validation failure
            task_id: ID of the task that failed
            epic_id: ID of related epic
            details: Additional context
        """
        error_details = details or {}
        if task_id:
            error_details["task_id"] = task_id
        if epic_id:
            error_details["epic_id"] = epic_id
        super().__init__(message, error_details)
        self.task_id = task_id
        self.epic_id = epic_id


class TaskCreationError(SpecDrivenException):
    """
    Exception raised when Task creation fails.

    This can occur when:
    - Epic file is not found
    - Epic parsing fails
    - Task generation fails
    - File write fails
    """

    def __init__(
        self,
        message: str,
        epic_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Task creation error.

        Args:
            message: Description of creation failure
            epic_id: ID of the epic that failed
            details: Additional context
        """
        error_details = details or {}
        if epic_id:
            error_details["epic_id"] = epic_id
        super().__init__(message, error_details)
        self.epic_id = epic_id


class GitHubSyncError(SpecDrivenException):
    """
    Exception raised when GitHub synchronization fails.

    This can occur when:
    - API authentication fails
    - Repository is not accessible
    - Branch creation fails
    - PR creation fails
    - Webhook configuration fails
    """

    def __init__(
        self,
        message: str,
        repo: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize GitHub sync error.

        Args:
            message: Description of sync failure
            repo: Repository that failed
            status_code: HTTP status code if applicable
            details: Additional context
        """
        error_details = details or {}
        if repo:
            error_details["repository"] = repo
        if status_code:
            error_details["status_code"] = status_code
        super().__init__(message, error_details)
        self.repo = repo
        self.status_code = status_code
