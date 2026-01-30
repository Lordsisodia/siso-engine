# GitHub Actions Integration for BlackBox5

Complete integration with GitHub Actions API for managing workflows, triggering deployments, and downloading artifacts.

## Features

- **Workflow Management**: List and inspect workflows
- **Workflow Dispatch**: Trigger workflows with inputs
- **Run Monitoring**: Track workflow runs and wait for completion
- **Log Downloads**: Download workflow run logs (ZIP archives)
- **Artifact Management**: List and download workflow artifacts
- **Rate Limit Tracking**: Automatic GitHub API rate limit monitoring

## Architecture

### Components

- **`GitHubActionsManager`**: Main manager class for all GitHub Actions operations
- **`Workflow`**: Data class for workflow information
- **`WorkflowRun`**: Data class for workflow run status and results
- **`Artifact`**: Data class for workflow artifacts
- **`WorkflowRunStatus`**: Enum for run statuses (queued, in_progress, completed)
- **`WorkflowRunConclusion`**: Enum for final outcomes (success, failure, etc.)

## Requirements

### Authentication

1. **Get GitHub Personal Access Token**:
   - Navigate to https://github.com/settings/tokens
   - Generate a new token (Classic or Fine-grained)
   - Required permissions:
     - `repo` - Full repository access
     - `workflow` - Workflow access (for triggering)
   - Copy token and set as environment variable:
     ```bash
     export GITHUB_TOKEN="ghp_your_token_here"
     ```

2. **Repository Information**:
   - You need the repository owner (organization or user)
   - You need the repository name

### Python Dependencies

```bash
pip install requests
```

Add to `.blackbox5/engine/requirements.txt`:
```txt
requests>=2.31.0
```

## Usage

### Basic Usage

```python
from integration.github_actions import GitHubActionsManager

# Initialize manager
manager = GitHubActionsManager(
    owner="myorg",
    repo="myrepo"
)

# List workflows
workflows = manager.list_workflows()
for workflow in workflows:
    print(f"{workflow.name}: {workflow.state}")

# Trigger a workflow
manager.trigger_workflow(
    workflow_id=123456,
    ref="main",
    inputs={"environment": "production"}
)

# Wait for completion
run = manager.wait_for_deployment(run_id=789012, timeout=1800)
print(f"Deployment result: {run.conclusion}")

# Close connection
manager.close()
```

### Context Manager Usage

```python
with GitHubActionsManager(owner="myorg", repo="myrepo") as manager:
    # Workflows are automatically managed
    workflows = manager.list_workflows()
    # Connection automatically closed
```

### Advanced Usage

#### Monitor Deployments

```python
# Trigger workflow and wait for completion
with GitHubActionsManager(owner="myorg", repo="myrepo") as manager:
    # Trigger deployment
    manager.trigger_workflow(123456, "main", {"env": "staging"})

    # Get latest run
    runs = manager.list_workflow_runs(branch="main", per_page=1)
    latest = runs[0]

    # Wait for completion (30 min timeout)
    completed = manager.wait_for_deployment(latest.id, timeout=1800)

    if completed.conclusion == "success":
        print("✅ Deployment successful")
    else:
        print(f"❌ Deployment failed: {completed.conclusion}")

    # Download logs for debugging
    log_path = manager.download_logs(latest.id, output_path="./logs")
    print(f"Logs: {log_path}")
```

#### Download Artifacts

```python
with GitHubActionsManager(owner="myorg", repo="myrepo") as manager:
    # List artifacts from a run
    artifacts = manager.list_artifacts(run_id=789012)

    for artifact in artifacts:
        print(f"{artifact.name}: {artifact.size_in_bytes} bytes")

        # Download if it's a build artifact
        if artifact.name.startswith("build-"):
            path = manager.download_artifact(
                artifact_id=artifact.id,
                output_path="./artifacts"
            )
            print(f"Downloaded to: {path}")
```

#### Filter Workflow Runs

```python
with GitHubActionsManager(owner="myorg", repo="myrepo") as manager:
    # Get failed runs on main branch
    failed_runs = manager.list_workflow_runs(
        status="completed",
        branch="main"
    )

    for run in failed_runs:
        if run.conclusion == "failure":
            print(f"Run {run.run_number}: {run.html_url}")
```

## API Reference

### Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `list_workflows()` | List all workflows | `per_page`, `page` | `list[Workflow]` |
| `get_workflow(workflow_id)` | Get specific workflow | `workflow_id` | `Workflow \| None` |
| `trigger_workflow(workflow_id, ref, inputs)` | Trigger workflow | `workflow_id`, `ref`, `inputs` | `bool` |
| `list_workflow_runs(status, branch, workflow_id)` | List runs | `status`, `branch`, `workflow_id`, `per_page`, `page` | `list[WorkflowRun]` |
| `get_workflow_run(run_id)` | Get specific run | `run_id` | `WorkflowRun \| None` |
| `wait_for_deployment(run_id, timeout, poll_interval)` | Wait for completion | `run_id`, `timeout`, `poll_interval` | `WorkflowRun` |
| `download_logs(run_id, output_path)` | Download run logs | `run_id`, `output_path` | `str` |
| `list_artifacts(run_id)` | List artifacts | `run_id`, `per_page`, `page` | `list[Artifact]` |
| `download_artifact(artifact_id, output_path, run_id)` | Download artifact | `artifact_id`, `output_path`, `run_id` | `str` |
| `get_rate_limit()` | Get rate limit info | - | `RateLimitInfo \| None` |
| `check_connection()` | Test API connection | - | `bool` |

### Data Classes

#### `Workflow`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Workflow ID |
| `name` | `str` | Workflow name |
| `path` | `str` | Workflow file path |
| `state` | `str` | Workflow state (active, deleted, etc.) |
| `created_at` | `datetime` | Creation timestamp |
| `updated_at` | `datetime` | Last update timestamp |
| `url` | `str` | API URL |
| `html_url` | `str` | Web UI URL |
| `badge_url` | `str \| None` | Status badge URL |
| `workflow_dispatch` | `bool` | Whether manual dispatch is enabled |
| `metadata` | `dict \| None` | Additional metadata |

#### `WorkflowRun`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Run ID |
| `name` | `str` | Run name |
| `run_number` | `int` | Run number |
| `status` | `WorkflowRunStatus` | Current status |
| `conclusion` | `WorkflowRunConclusion \| None` | Final result |
| `head_branch` | `str` | Branch name |
| `head_sha` | `str` | Commit SHA |
| `created_at` | `datetime` | Creation timestamp |
| `updated_at` | `datetime` | Last update timestamp |
| `url` | `str` | API URL |
| `html_url` | `str` | Web UI URL |
| `event` | `str` | Trigger event |
| `actor` | `dict` | Triggering actor info |
| `workflow_id` | `int` | Parent workflow ID |
| `run_started_at` | `datetime \| None` | Start timestamp |
| `cancelled_at` | `datetime \| None` | Cancellation timestamp |
| `metadata` | `dict \| None` | Additional metadata |

#### `Artifact`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Artifact ID |
| `name` | `str` | Artifact name |
| `size_in_bytes` | `int` | Size in bytes |
| `expired` | `bool` | Whether expired |
| `created_at` | `datetime` | Creation timestamp |
| `updated_at` | `datetime` | Last update timestamp |
| `download_url` | `str` | Download URL |
| `archive_download_url` | `str` | Archive download URL |
| `workflow_run_id` | `int \| None` | Parent run ID |
| `metadata` | `dict \| None` | Additional metadata |

## Error Handling

```python
from requests.exceptions import HTTPError

try:
    manager.trigger_workflow(workflow_id, "main")
except HTTPError as e:
    if e.response.status_code == 404:
        print("Workflow not found")
    elif e.response.status_code == 409:
        print("Workflow does not support dispatch")
    else:
        print(f"API error: {e}")
```

## Rate Limits

GitHub API has the following rate limits:

- **Authenticated requests**: 5,000 requests per hour
- **Rate limit headers**: Automatically tracked
- **Reset behavior**: Limits reset at the top of each hour

The manager automatically tracks rate limits via response headers:

```python
rate_limit = manager.get_rate_limit()
print(f"Remaining: {rate_limit.remaining}/{rate_limit.limit}")
print(f"Resets at: {rate_limit.reset_at}")
```

When rate limit drops below 100, a warning is logged.

## Important Implementation Notes

### Workflow Dispatch Requirements

- Workflow must have `workflow_dispatch` event in YAML:
  ```yaml
  on:
    workflow_dispatch:
      inputs:
        environment:
          description: 'Deployment environment'
          required: true
          type: choice
          options:
            - staging
            - production
  ```

### Log Download Expiration

- Log download URLs expire after **1 minute**
- Always download immediately after getting the URL
- Logs are returned as ZIP archives

### Artifact Download Expiration

- Artifact download URLs expire after **1 minute**
- Always download immediately after getting the URL
- Artifacts are returned as ZIP archives

### API Version

- Uses GitHub API version `2022-11-28`
- Set via `X-GitHub-Api-Version` header
- May be updated via `API_VERSION` constant in manager

## Testing

```bash
# Set environment variables
export GITHUB_TOKEN="ghp_your_token"
export GITHUB_OWNER="myorg"
export GITHUB_REPO="myrepo"

# Run demo
python .blackbox5/integration/github-actions/demo.py
```

## Troubleshooting

### Common Issues

**Issue**: `409 Conflict` when triggering workflow
- **Solution**: Workflow must have `workflow_dispatch` event enabled in YAML

**Issue**: `404 Not Found` for workflow
- **Solution**: Check workflow ID and repository permissions

**Issue**: Timeout waiting for deployment
- **Solution**: Increase timeout parameter or check workflow duration

**Issue**: Empty log download
- **Solution**: Some runs may not have logs (cancelled, queued)

**Issue**: Rate limit exceeded
- **Solution**: Wait for hourly reset or cache results

## See Also

- GitHub Actions Documentation: https://docs.github.com/en/actions
- REST API Reference: https://docs.github.com/en/rest/actions
- Workflow Syntax: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions
