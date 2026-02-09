# GitHub Integration - Quick Start

Get started with BlackBox5's GitHub integration in 5 minutes.

## 1. Install Dependencies

```bash
pip install requests
```

## 2. Get GitHub Token

Create a Personal Access Token at https://github.com/settings/tokens

Required scopes:
- ✅ `repo` - Full repository access

## 3. Set Environment Variables

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_REPO="owner/repo"
```

## 4. Basic Usage

### Create an Issue

```python
from blackbox5.integration.github import create_manager_from_env

manager = create_manager_from_env()

issue = manager.create_issue(
    title="Fix authentication bug",
    body="Users cannot login with SAML",
    labels=["bug", "critical"]
)

print(f"Created: {issue.html_url}")
```

### Add Progress Comment

```python
manager.add_comment(issue.number, """## 🔄 Progress Update

### ✅ Completed Work
- Fixed SAML authentication
- Added error handling

### 📊 Status
- Progress: 80%
- Tests: Passing

---
*Synced at 2024-01-15T10:00:00Z*
""")
```

### Close Issue

```python
manager.update_status(issue.number, "closed")
```

### Create Pull Request

```python
pr = manager.create_pr(
    branch="feature/new-auth",
    title="Add SAML authentication",
    body="Implements enterprise SSO",
    base="main"
)

print(f"Created PR: {pr.html_url}")
```

## 5. Run Demo

```bash
python .blackbox5/integration/github/demo.py
```

## 6. Run Tests

```bash
# Set test credentials
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_REPO="owner/test-repo"

# Run tests
pytest .blackbox5/tests/test_github_integration.py -v
```

## Common Patterns

### Epic/Task Pattern (CCPM)

```python
# Create epic
epic = manager.create_issue(
    title="Epic: User Authentication",
    body="# Epic\n## Overview\nImplement OAuth2 login",
    labels=["epic", "epic:user-auth", "feature"]
)

# Create sub-tasks
task1 = manager.create_issue(
    title="Task: Implement login endpoint",
    body="# Task\n## Acceptance Criteria\n- [ ] POST /login",
    labels=["task", "epic:user-auth"]
)

task2 = manager.create_issue(
    title="Task: Add tests",
    body="# Task\n## Acceptance Criteria\n- [ ] Unit tests",
    labels=["task", "epic:user-auth"]
)

# Link tasks to epic
manager.add_comment(epic.number, f"""## Tasks Created

- [ ] #{task1.number} - Implement login endpoint
- [ ] #{task2.number} - Add tests

**Total:** 2 tasks
**Parallel:** 2 tasks
""")
```

### Progress Updates (CCPM)

```python
manager.add_comment(issue.number, f"""## 🔄 Progress Update - {datetime.now().isoformat()}

### ✅ Completed Work
- Created login endpoint
- Implemented JWT handling
- Added token validation

### 🔄 In Progress
- Adding SAML support
- Writing integration tests

### 📝 Technical Notes
- Using PyJWT library
- Token expiry: 1 hour
- Refresh token: 30 days

### 📊 Acceptance Criteria Status
- ✅ POST /login accepts credentials
- ✅ Returns JWT on success
- ✅ Validates tokens
- 🔄 SAML SSO support
- □ Token refresh flow

### 🚀 Next Steps
- Complete SAML implementation
- Add comprehensive tests
- Update API docs

### 💻 Recent Commits
- Issue #123: Create login endpoint
- Issue #123: Add JWT handling

---
*Progress: 75% | Synced at {datetime.now().isoformat()}*
""")
```

### Completion Comment

```python
manager.add_comment(issue.number, """## ✅ Task Completed

### 🎯 All Acceptance Criteria Met
- ✅ Login endpoint implemented
- ✅ JWT handling working
- ✅ Token validation complete
- ✅ SAML SSO support added
- ✅ Token refresh flow working

### 📦 Deliverables
- src/api/auth/login.py
- src/lib/jwt.py
- tests/auth/login_test.py
- docs/api/authentication.md

### 🧪 Testing
- Unit tests: ✅ 15/15 passing
- Integration tests: ✅ 5/5 passing
- Manual testing: ✅ Complete

### 📚 Documentation
- API docs: ✅ Updated
- Code comments: ✅ Complete
- README: ✅ Updated

Ready for review!
---
*Task completed: 100%*
""")

manager.update_status(issue.number, "closed")
```

## API Quick Reference

| Method | Parameters | Description |
|--------|-----------|-------------|
| `create_issue()` | title, body, labels | Create issue |
| `get_issue()` | number | Get issue details |
| `update_issue()` | number, title, body, state, labels | Update issue |
| `update_status()` | number, status | Set open/closed |
| `add_comment()` | number, comment | Add comment |
| `list_comments()` | number | List all comments |
| `create_pr()` | branch, title, body, base | Create pull request |
| `get_pr()` | number | Get PR details |
| `list_prs()` | state, head, base | List PRs |
| `check_repository_safe()` | - | Safety check |

## Common Labels

### Type
- `epic` - Epic issue
- `task` - Task issue
- `type:feature` - New feature
- `type:bug` - Bug fix
- `type:refactor` - Refactoring
- `type:docs` - Documentation
- `type:test` - Tests

### Priority
- `priority:critical` - Critical priority
- `priority:high` - High priority
- `priority:medium` - Medium priority
- `priority:low` - Low priority

### Status
- `status:backlog` - Not started
- `status:in-progress` - Working on it
- `status:review` - In review
- `status:done` - Completed

### CCPM Patterns
- `epic:name` - Group tasks under epic
- `task` - Task issue
- `feature` - Feature work

## Troubleshooting

### Authentication Error

```
ValueError: GitHub token required
```

**Solution:** Set GITHUB_TOKEN environment variable
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

### Repository Not Found

```
RuntimeError: Repository required
```

**Solution:** Set GITHUB_REPO or run from git repository
```bash
export GITHUB_REPO="owner/repo"
```

### Permission Denied

```
HTTPError: 403 Forbidden
```

**Solution:** Check token has `repo` scope and you have write access

### Rate Limit

```
HTTPError: 403 Rate limit exceeded
```

**Solution:** Wait for rate limit reset (typically 1 hour for authenticated requests)

## Next Steps

- 📖 Read full documentation: `README.md`
- 🧪 Run tests: `pytest .blackbox5/tests/test_github_integration.py`
- 🎮 Try demo: `python .blackbox5/integration/github/demo.py`
- 📝 Check implementation details: `IMPLEMENTATION-SUMMARY.md`

## Support

- GitHub API Docs: https://docs.github.com/en/rest
- CCPM Reference: `.docs/research/development-tools/ccpm/`
- Create issues for bugs or feature requests
