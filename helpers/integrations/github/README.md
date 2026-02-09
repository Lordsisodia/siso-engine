# GitHub Integration for BlackBox5

A simplified GitHub integration system adapted from CCPM's GitHub sync patterns, using Python's `requests` library for direct GitHub API calls.

## Overview

This integration provides a simple, HTTP-based interface to GitHub's API for:
- Creating and managing issues
- Creating pull requests
- Adding comments to issues
- Updating issue status
- Repository safety checks

## Features

### Core Capabilities

- **Issue Management**: Create, read, update, and close issues
- **Pull Request Management**: Create and list PRs
- **Comments**: Add comments to issues and PRs
- **Labels**: Apply labels to issues and PRs
- **Repository Safety**: Prevents modifications to template repositories
- **Auto-detection**: Automatically detects repository from git config

### CCPM Patterns

Adapted from CCPM's GitHub integration:
- Epic-style issues with task breakdowns
- Progress update comments with structured format
- Label-based organization (epic, task, feature, bug)
- Incremental sync markers to prevent duplicates

## Installation

### Requirements

```bash
pip install requests
```

### GitHub Token

Create a Personal Access Token (PAT) at https://github.com/settings/tokens

Required scopes:
- `repo` - Full repository access
- `issues` - Issue management
- `pull_requests` - PR management

## Quick Start

### Basic Usage

```python
from blackbox5.integration.github import GitHubManager

# Initialize with token and repository
manager = GitHubManager(
    token="ghp_xxxxxxxxxxxx",
    repo="owner/repo"
)

# Create an issue
issue = manager.create_issue(
    title="Fix authentication bug",
    body="Users cannot login with SAML SSO",
    labels=["bug", "critical", "authentication"]
)

print(f"Created issue #{issue.number}: {issue.html_url}")

# Add a progress update comment
manager.add_comment(issue.number, """
## 🔄 Progress Update

### ✅ Completed Work
- Identified root cause in SAML handler

### 🔄 In Progress
- Implementing fix
- Adding regression tests
""")

# Update status
manager.update_status(issue.number, "closed")
```

### Using Environment Variables

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_REPO="owner/repo"
```

```python
from blackbox5.integration.github import create_manager_from_env

manager = create_manager_from_env()
```

### Creating Pull Requests

```python
# Create a PR from a feature branch
pr = manager.create_pr(
    branch="feature/add-auth",
    title="Add user authentication",
    body="Implements OAuth2 login flow with SAML support",
    base="main",
    labels=["feature", "authentication"],
    draft=False  # Set True for draft PR
)

print(f"Created PR #{pr.number}: {pr.html_url}")

# Add comment to PR
manager.add_pr_comment(pr.number, "Ready for review")
```

## CCPM-Style Patterns

### Epic Creation

```python
# Create epic issue (CCPM pattern)
epic_body = """# Epic: User Authentication

## Overview
Implement OAuth2 authentication with SAML SSO support.

## Key Decisions
- Use Auth0 for OAuth2 provider
- Support SAML 2.0 for enterprise SSO
- Store tokens securely with encryption

## Stats
Total tasks: 5
Parallel tasks: 3 (can be worked on simultaneously)
Sequential tasks: 2 (have dependencies)
Estimated total effort: 16 hours
"""

epic = manager.create_issue(
    title="Epic: User Authentication",
    body=epic_body,
    labels=["epic", "epic:user-auth", "feature"]
)

# Create sub-tasks
task1 = manager.create_issue(
    title="Implement OAuth2 login endpoint",
    body="# Task: OAuth2 Login\n\n## Acceptance Criteria\n- [ ] Endpoint accepts code\n- [ ] Returns JWT token",
    labels=["task", "epic:user-auth"]
)
```

### Progress Updates

```python
# Add structured progress comment (CCPM pattern)
manager.add_comment(issue.number, f"""## 🔄 Progress Update - {datetime.now().isoformat()}

### ✅ Completed Work
- Created OAuth2 login endpoint
- Implemented JWT token generation
- Added token validation

### 🔄 In Progress
- Adding SAML SSO support
- Implementing token refresh

### 📝 Technical Notes
- Using PyJWT for JWT handling
- Token expiry: 1 hour
- Refresh token expiry: 30 days

### 📊 Acceptance Criteria Status
- ✅ Login endpoint accepts OAuth2 code
- ✅ Returns JWT on successful auth
- ✅ Validates tokens properly
- 🔄 SAML SSO implementation
- □ Token refresh flow

### 🚀 Next Steps
- Complete SAML implementation
- Add comprehensive tests
- Update API documentation

### 💻 Recent Commits
- Issue #123: Create OAuth2 endpoint
- Issue #123: Implement JWT handling

---
*Progress: 75% | Synced from local updates at {datetime.now().isoformat()}*
""")
```

### Completion Comments

```python
# Mark task as complete
manager.add_comment(issue.number, """## ✅ Task Completed - 2024-01-15T15:00:00Z

### 🎯 All Acceptance Criteria Met
- ✅ Login endpoint accepts OAuth2 code
- ✅ Returns JWT on successful authentication
- ✅ Validates tokens against database
- ✅ Returns appropriate error for invalid tokens
- ✅ Rate limiting implemented

### 📦 Deliverables
- src/api/auth/login.py (OAuth2 endpoint)
- src/lib/jwt.py (JWT utilities)
- tests/auth/login_test.py (Unit tests)
- docs/api/authentication.md (API docs)

### 🧪 Testing
- Unit tests: ✅ Passing (15/15)
- Integration tests: ✅ Passing (5/5)
- Manual testing: ✅ Complete

### 📚 Documentation
- API documentation: ✅ Updated
- Code comments: ✅ Complete
- README: ✅ Updated with auth setup

This task is ready for review and can be closed.

---
*Task completed: 100% | Synced at 2024-01-15T15:00:00Z*
""")

# Close the issue
manager.update_status(issue.number, "closed")
```

## API Reference

### GitHubManager

Main class for GitHub API interactions.

#### Constructor

```python
GitHubManager(
    token: Optional[str] = None,
    repo: Optional[str] = None,
    base_url: str = "https://api.github.com"
)
```

**Parameters:**
- `token`: GitHub Personal Access Token (or use `GITHUB_TOKEN` env var)
- `repo`: Repository in "owner/repo" format (auto-detected if None)
- `base_url`: API base URL (for GitHub Enterprise)

**Raises:**
- `ValueError`: If token not provided
- `RuntimeError`: If repo cannot be determined

#### Methods

##### create_issue

```python
create_issue(
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None
) -> GitHubIssue
```

Create a new GitHub issue.

**Returns:** `GitHubIssue` object

##### get_issue

```python
get_issue(issue_number: int) -> GitHubIssue
```

Retrieve issue details.

##### update_issue

```python
update_issue(
    issue_number: int,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: Optional[str] = None,
    labels: Optional[List[str]] = None
) -> GitHubIssue
```

Update existing issue.

##### update_status

```python
update_status(issue_number: int, status: str) -> GitHubIssue
```

Set issue state to "open" or "closed".

##### add_comment

```python
add_comment(issue_number: int, comment: str) -> Dict[str, Any]
```

Add comment to issue.

##### list_comments

```python
list_comments(issue_number: int) -> List[Dict[str, Any]]
```

List all comments on issue.

##### create_pr

```python
create_pr(
    branch: str,
    title: str,
    body: str,
    base: Optional[str] = None,
    draft: bool = False,
    labels: Optional[List[str]] = None
) -> GitHubPR
```

Create a pull request.

##### get_pr

```python
get_pr(pr_number: int) -> GitHubPR
```

Retrieve PR details.

##### list_prs

```python
list_prs(
    state: str = "open",
    head: Optional[str] = None,
    base: Optional[str] = None
) -> List[GitHubPR]
```

List pull requests with filters.

##### check_repository_safe

```python
check_repository_safe() -> bool
```

Check if repository is safe for modifications.

### Data Classes

#### GitHubIssue

```python
@dataclass
class GitHubIssue:
    number: int
    title: str
    body: str
    state: str
    html_url: str
    labels: List[str]
    created_at: str
    updated_at: str
```

#### GitHubPR

```python
@dataclass
class GitHubPR:
    number: int
    title: str
    body: str
    state: str
    html_url: str
    head_ref: str
    base_ref: str
    created_at: str
    updated_at: str
```

## Testing

### Run Unit Tests

```bash
pytest .blackbox5/tests/test_github_integration.py -v
```

### Run Integration Tests

Integration tests require a GitHub token and test repository:

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_REPO="owner/test-repo"

pytest .blackbox5/tests/test_github_integration.py -v -m integration
```

### Run with Coverage

```bash
pytest .blackbox5/tests/test_github_integration.py \
    --cov=.blackbox5/integration/github \
    --cov-report=html
```

## Examples

### Example 1: Bug Tracking

```python
# Create bug report
bug = manager.create_issue(
    title="Bug: Application crashes on startup",
    body="""## Bug Description
Application crashes immediately after launch.

## Steps to Reproduce
1. Open application
2. Click "Login" button
3. Application crashes

## Expected Behavior
Should show login form

## Actual Behavior
Application crashes with error code 500

## Environment
- Version: 2.1.0
- OS: macOS 14.2
- Browser: Chrome 120
""",
    labels=["bug", "critical", "crash"]
)

# Add triage comment
manager.add_comment(bug.number, "Triaging: Assigned to team member")
```

### Example 2: Feature Development

```python
# Create epic for feature
epic = manager.create_issue(
    title="Epic: Dark Mode Support",
    body="Add dark mode theme across entire application",
    labels=["epic", "feature", "enhancement"]
)

# Break down into tasks
tasks = [
    ("Create color palette", "Design dark mode colors"),
    ("Update components", "Modify all UI components"),
    ("Add theme switcher", "Implement toggle button"),
    ("Update documentation", "Document dark mode usage")
]

for task_title, task_desc in tasks:
    task = manager.create_issue(
        title=f"Task: {task_title}",
        body=f"# {task_title}\n\n{task_desc}",
        labels=["task", "epic:dark-mode"]
    )
    manager.add_comment(
        epic.number,
        f"Created sub-task: #{task.number}"
    )
```

### Example 3: PR Workflow

```python
# Create feature branch PR
pr = manager.create_pr(
    branch="feature/user-profiles",
    title="Add user profile pages",
    body="""## Summary
Implements user profile pages with avatar, bio, and activity feed.

## Changes
- Added UserProfile component
- Created profile API endpoints
- Updated routing
- Added unit tests

## Testing
- Manual testing completed
- Unit tests: 100% passing
- Integration tests: 100% passing

## Checklist
- [x] Tests pass
- [x] Documentation updated
- [x] No breaking changes
""",
    base="main",
    labels=["feature", "ready-for-review"]
)

# Add reviewers comment
manager.add_pr_comment(
    pr.number,
    "@reviewer1 @reviewer2 Please review when you have time"
)
```

## Error Handling

```python
try:
    issue = manager.create_issue("Title", "Body")
except requests.HTTPError as e:
    if e.response.status_code == 401:
        print("Authentication failed. Check your token.")
    elif e.response.status_code == 403:
        print("Permission denied. Check repo access.")
    elif e.response.status_code == 404:
        print("Repository not found.")
    else:
        print(f"GitHub API error: {e}")
```

## Best Practices

### 1. Use Structured Issue Bodies

```python
# Good: Structured markdown
body = """## Problem
Clear description of the problem.

## Solution
Proposed solution approach.

## Alternatives
Alternative approaches considered.

## Impact
Breaking changes and migration guide.
"""

# Bad: Unstructured text
body = "Fix the thing that's broken with the auth system"
```

### 2. Apply Consistent Labels

```python
# Use standardized label categories
labels = [
    # Priority
    "priority:critical", "priority:high", "priority:medium", "priority:low",

    # Type
    "type:feature", "type:bug", "type:refactor", "type:docs",

    # Status
    "status:backlog", "status:in-progress", "status:review", "status:done",

    # CCPM patterns
    "epic", "task", "epic:name"
]
```

### 3. Incremental Progress Updates

```python
# Add sync markers to prevent duplicate comments
comment_body = """## Progress Update

<!-- SYNCED: 2024-01-15T10:30:00Z -->

New updates here...
"""
```

### 4. Repository Safety

```python
# Always check repository safety before bulk operations
if not manager.check_repository_safe():
    print("⚠️ Repository not safe for modifications")
    return

# Proceed with operations
manager.create_issue("Title", "Body")
```

## Comparison with CCPM

### Similarities

- GitHub Issues as source of truth
- Structured progress comments
- Epic/task breakdown patterns
- Label-based organization
- Repository protection checks

### Differences

| Feature | CCPM | BlackBox5 GitHubManager |
|---------|------|------------------------|
| Implementation | GitHub CLI (`gh`) | Python `requests` |
| Async | No | Yes (async methods planned) |
| Memory Integration | Yes | Planned |
| Sub-issues | Via extension | Manual implementation |
| Auto-detection | git remote | git remote |

## Future Enhancements

- [ ] Async/await support for better performance
- [ ] Sub-issue support (parent-child relationships)
- [ ] Webhook handling
- [ ] Memory integration (working memory + brain)
- [ ] Rate limiting and retry logic
- [ ] GitHub Enterprise support
- [ ] Asset upload (images, files)
- [ ] Reaction emoji support
- [ ] Project board integration
- [ ] Milestone management

## Contributing

When contributing to the GitHub integration:

1. Follow CCPM patterns for consistency
2. Add tests for new features
3. Update documentation
4. Use structured commit messages
5. Test with real GitHub API

## License

Part of BlackBox5. See main project LICENSE.

## References

- [CCPM GitHub Integration Explained](../../.docs/research/development-tools/ccpm/GITHUB-INTEGRATION-EXPLAINED.md)
- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [CCPM Epic Sync](../../.docs/research/development-tools/ccpm/ccpm/commands/pm/epic-sync.md)
- [Python Requests Library](https://requests.readthedocs.io/)

## Implementation Details

### Files Created

1. **`GitHubManager.py`** (450 lines) - Main manager class with GitHub API integration
2. **`tests/test_github_integration.py`** (650 lines) - Comprehensive test suite
3. **`demo.py`** (300 lines) - Interactive demonstration script
4. **`README.md`** - Complete API reference and usage examples

### Key Implementation Details

1. **Library**: Python `requests` for HTTP calls to GitHub REST API v3
2. **Authentication**: GitHub Personal Access Token (PAT) via `GITHUB_TOKEN` env var
3. **Auto-detection**: Repository auto-detected from git config
4. **Safety Checks**: Prevents modifications to template repositories
5. **CCPM Patterns**: Epic/task organization, structured progress comments, label-based organization

### API Methods

**Issue Operations:**
- `create_issue(title, body, labels)` - Create issue
- `get_issue(number)` - Get issue details
- `update_issue(number, ...)` - Update issue
- `update_status(number, status)` - Set open/closed
- `add_comment(number, comment)` - Add comment

**Pull Request Operations:**
- `create_pr(branch, title, body, base)` - Create PR
- `get_pr(number)` - Get PR details
- `list_prs(state, head, base)` - List PRs

**Repository Operations:**
- `check_repository_safe()` - Safety check

### Testing

```bash
# Unit tests
pytest tests/test_github_integration.py -v -m "not integration"

# Integration tests
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_REPO="owner/test-repo"
pytest tests/test_github_integration.py -v -m integration
```
