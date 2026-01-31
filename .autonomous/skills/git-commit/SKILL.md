---
id: git-commit
name: Git Commit
version: 1.0.0
category: core
description: Safely commit changes to git with validation and documentation
trigger: After task completion, at end of run, when saving work
inputs:
  - name: message
    type: string
    required: true
    description: Commit message
  - name: branch
    type: string
    required: false
    default: dev
    description: Target branch
  - name: files
    type: array
    required: false
    description: "Specific files to commit (default: all staged)"
outputs:
  - name: commit_hash
    type: string
    description: Git commit hash
  - name: commit_status
    type: string
    description: success | failure
commands:
  - commit
  - validate-branch
  - stage-files
  - verify-commit
---

# Git Commit

## Purpose

Safely persist work to git with branch protection, validation, and clear commit messages.

## When to Use

- After completing a task
- At the end of every run
- When explicitly asked to save work

---

## Safety Rules

### Branch Protection

**FORBIDDEN branches (will exit BLOCKED):**
- `main`
- `master`
- `production`
- `release/*`

**ALLOWED branches:**
- `dev`
- `develop`
- `feature/*`
- `bugfix/*`
- `legacy/*`

### Pre-Commit Checks

1. **Branch check**
   - Verify not on forbidden branch
   - Verify branch exists remotely (if pushing)

2. **Status check**
   - Working tree clean? (nothing to commit)
   - Staged changes? (ready to commit)
   - Untracked files? (decide what to do)

3. **Validation check**
   - Tests pass (if required)
   - No obvious errors
   - Documentation updated

---

## Command: commit

### Input
- `message`: Commit message
- `branch`: Target branch (default: dev)
- `files`: Specific files or all staged

### Process

1. **Validate branch**
   ```bash
   git branch --show-current
   ```
   - If forbidden: EXIT BLOCKED
   - If allowed: Continue

2. **Check status**
   ```bash
   git status
   ```
   - Nothing to commit: Exit with note
   - Changes present: Continue

3. **Stage files**
   - If `files` specified: `git add <files>`
   - If no `files`: `git add -A` (all changes)

4. **Validate staged**
   - Review what will be committed
   - Check for:
     - Secrets/credentials
     - Large binaries
     - Generated files that should be gitignored

5. **Run pre-commit checks (if configured)**
   - Tests
   - Linting
   - Type checking

6. **Create commit**
   ```bash
   git commit -m "message"
   ```

7. **Verify commit**
   ```bash
   git log -1 --oneline
   git show --stat HEAD
   ```

8. **Push (optional)**
   ```bash
   git push origin <branch>
   ```

9. **Trigger State Management**
   → Invoke skill:state-management
   → Pass commit_hash
   → Update task status to completed

### Output

```yaml
commit_result:
  status: "success"
  commit_hash: "abc123def456"
  branch: "dev"
  message: "feat: implement user authentication"
  files_changed: 5
  insertions: 120
  deletions: 15
  pushed: true
  remote: "origin"
```

---

## Command: validate-branch

### Process

1. Get current branch
2. Check against forbidden list
3. Return validation result

### Output

```yaml
branch_validation:
  current_branch: "dev"
  is_allowed: true
  is_forbidden: false
  can_commit: true
```

### Forbidden Branch Response

```yaml
branch_validation:
  current_branch: "main"
  is_allowed: false
  is_forbidden: true
  can_commit: false
  action: "EXIT_BLOCKED"
  message: "Committing to main/master is forbidden. Switch to dev branch."
```

---

## Commit Message Format

### Standard Format

```
<type>: <subject>

<body>

Co-Authored-By: Legacy (Autonomous) <legacy@siso.internal>
```

### Types

| Type | Use When |
|------|----------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code change, no feature change |
| `test` | Adding tests |
| `chore` | Maintenance |

### Examples

```
feat: add user authentication with OAuth

- Implement OAuth2 flow for Google and GitHub
- Add user session management
- Create login/logout UI components

Validates: LEGACY-2026-01-30-001
Run: run-0017
```

```
fix: resolve database connection timeout

- Increase connection pool size
- Add retry logic with exponential backoff
- Log connection failures for monitoring

Validates: LEGACY-2026-01-30-002
Run: run-0018
```

---

## Examples

### Example 1: Successful Commit

```markdown
**Input:**
- message: "feat: implement user auth"
- branch: "dev"
- files: null (all staged)

**Process:**
1. Branch: dev ✓ (allowed)
2. Status: 5 files modified
3. Stage: All files
4. Validate: No secrets found
5. Tests: Passing
6. Commit: Created abc123
7. Verify: 5 files, +120 -15 lines
8. Push: Success

**Output:**
commit_result:
  status: "success"
  commit_hash: "abc123"
  pushed: true
```

### Example 2: Blocked - Wrong Branch

```markdown
**Input:**
- message: "feat: implement user auth"
- branch: "main"

**Process:**
1. Branch: main ✗ (FORBIDDEN)
2. Action: EXIT_BLOCKED

**Output:**
branch_validation:
  current_branch: "main"
  can_commit: false
  action: "EXIT_BLOCKED"
  message: "Committing to main is forbidden"
```

### Example 3: Nothing to Commit

```markdown
**Input:**
- message: "feat: implement user auth"

**Process:**
1. Branch: dev ✓
2. Status: Working tree clean
3. Action: Exit with note

**Output:**
commit_result:
  status: "nothing_to_commit"
  message: "Working tree clean, nothing to commit"
```

---

## Error Handling

### Pre-Commit Hook Failure

```yaml
error: "PRE_COMMIT_FAILED"
message: "Tests failed, commit blocked"
failures:
  - test: "auth.test.ts"
    error: "Expected 200, got 401"
action: "Fix tests before committing"
```

### Merge Conflict

```yaml
error: "MERGE_CONFLICT"
message: "Cannot push, pull required"
action: "Pull latest changes, resolve conflicts, retry"
```

### Remote Rejection

```yaml
error: "REMOTE_REJECTED"
message: "Push rejected by remote"
reason: "Branch protection rule"
action: "Create pull request instead"
```
