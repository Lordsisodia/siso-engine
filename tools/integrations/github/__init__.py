"""
GitHub Integration for BlackBox5
=================================

Provides GitHub Issues and PR management with memory integration.
Combines Auto-Claude's provider pattern with CCPM's bidirectional sync.
"""

# Try to import from the advanced integration first
try:
    from .github_integration import (
        DEFAULT_LABELS,
        GitHubIssuesIntegration,
        TaskOutcome,
        TaskSpec,
    )
    from .providers.github_provider import GitHubProvider
    from .providers.protocol import (
        IssueData,
        IssueFilters,
        IssueState,
        LabelData,
        PRData,
        PRFilters,
        PRState,
        ProviderType,
        ReviewData,
        ReviewEvent,
    )
    from .sync.ccpm_sync import CCPMSyncManager, TaskProgress

    __all__ = [
        # Main integration
        "GitHubIssuesIntegration",
        "TaskSpec",
        "TaskOutcome",
        "DEFAULT_LABELS",
        # Provider
        "GitHubProvider",
        # Protocol
        "IssueData",
        "IssueFilters",
        "IssueState",
        "LabelData",
        "PRData",
        "PRFilters",
        "PRState",
        "ProviderType",
        "ReviewData",
        "ReviewEvent",
        # Sync
        "CCPMSyncManager",
        "TaskProgress",
    ]
except ImportError:
    # Fall back to basic manager if advanced features not available
    try:
        from .manager import GitHubManager
        from .types import (
            GitHubIssue,
            GitHubPR,
            GitHubComment,
            GitHubRepository,
            GitHubLabel,
            GitHubUser,
        )

        __all__ = [
            "GitHubManager",
            "GitHubIssue",
            "GitHubPR",
            "GitHubComment",
            "GitHubRepository",
            "GitHubLabel",
            "GitHubUser",
        ]
    except ImportError:
        pass
