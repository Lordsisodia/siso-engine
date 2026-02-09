# Vercel Integration for BlackBox5

Manage Vercel deployments, projects, and environment variables directly from your BlackBox5 workflows.

## Features

- **Deploy to Vercel**: Create and manage deployments from git repositories
- **Monitor Deployments**: Track deployment status and wait for completion
- **Retrieve Logs**: Get deployment and build logs
- **Project Management**: List and access project information
- **Environment Variables**: Manage environment variables for projects
- **Team Support**: Full support for Vercel team deployments

## Architecture

### Components

- **`VercelManager`**: Main manager class for all Vercel operations
- **`DeploymentStatus`**: Data class for deployment information
- **`DeploymentSpec`**: Specification for creating deployments
- **`ReadyState`**: Enum for deployment states (READY, FAILED, CANCELED, ERROR)

## Requirements

### Authentication

1. **Get API Token**:
   - Navigate to https://vercel.com/account/tokens
   - Create a new token with appropriate permissions
   - Copy token and set as environment variable:
     ```bash
     export VERCEL_TOKEN="your_token_here"
     ```

2. **Team Configuration** (optional):
   - If using team accounts, get your team ID from Vercel dashboard
   - Set as environment variable:
     ```bash
     export VERCEL_TEAM_ID="your_team_id"
     ```

### Python Dependencies

```bash
pip install httpx
```

Add to `.blackbox5/engine/requirements.txt`:
```txt
httpx>=0.25.0
```

## Usage

### Basic Usage

```python
import asyncio
from integration.vercel import VercelManager

async def main():
    # Initialize manager
    manager = VercelManager(token="your_token")

    # Create a deployment
    deployment = await manager.create_deployment(
        project_name="my-app",
        git_repo="https://github.com/user/repo",
        ref="main"
    )

    # Wait for deployment to complete
    result = await manager.wait_for_deployment(deployment.id)
    print(f"Deployed to: {result.url}")

    # Close connection
    await manager.close()

asyncio.run(main())
```

### Advanced Usage

#### Deployment with Environment

```python
from integration.vercel import VercelManager, DeploymentTarget

async with VercelManager() as manager:
    # Deploy to production
    deployment = await manager.create_deployment(
        project_name="my-app",
        git_repo="https://github.com/user/repo",
        ref="main",
        target=DeploymentTarget.PRODUCTION,
        metadata={"githubCommitSha": "abc123"}
    )

    # Monitor and wait
    result = await manager.wait_for_deployment(
        deployment.id,
        timeout=600,
        interval=10
    )

    if result.is_ready:
        print(f"✅ Production deployment: {result.url}")
    else:
        print(f"❌ Deployment failed: {result.ready_state}")
```

#### Manage Environment Variables

```python
async with VercelManager() as manager:
    project_id = "prj_123..."

    # Create environment variable
    await manager.create_env_variable(
        project_id=project_id,
        key="API_KEY",
        value="secret_value",
        environment=["production", "preview"],
        target=["production", "preview"]
    )

    # List environment variables
    env_vars = await manager.get_env_variables(project_id)
    for env in env_vars:
        print(f"{env['key']}: {env['type']}")
```

#### List Projects and Deployments

```python
async with VercelManager() as manager:
    # List all projects
    projects = await manager.list_projects(limit=20)
    for project in projects:
        print(f"{project['name']} - {project['framework']}")

    # Get deployments for a project
    deployments = await manager.list_deployments(
        project_id="prj_123...",
        limit=10
    )

    for deployment in deployments:
        print(f"{deployment.id}: {deployment.ready_state}")
```

#### Get Deployment Logs

```python
async with VercelManager() as manager:
    deployment_id = "dpl_123..."

    # Get logs (URLs expire after 1 minute)
    logs = await manager.get_deployment_logs(deployment_id)

    for log in logs:
        print(f"[{log.get('timestamp')}] {log.get('message')}")
```

#### Cancel Deployment

```python
async with VercelManager() as manager:
    deployment_id = "dpl_123..."

    # Cancel a running deployment
    success = await manager.cancel_deployment(deployment_id)

    if success:
        print("Deployment cancelled successfully")
```

## API Reference

### Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `create_deployment` | Create new deployment | `project_name`, `git_repo`, `ref`, `target`, `metadata` | `DeploymentStatus` |
| `get_deployment` | Get deployment by ID | `deployment_id` | `DeploymentStatus` or `None` |
| `list_deployments` | List deployments | `project_id`, `limit` | `list[DeploymentStatus]` |
| `wait_for_deployment` | Wait for completion | `deployment_id`, `timeout`, `interval` | `DeploymentStatus` |
| `get_deployment_logs` | Get build logs | `deployment_id`, `build_id` | `list[dict]` |
| `cancel_deployment` | Cancel deployment | `deployment_id` | `bool` |
| `list_projects` | List projects | `limit` | `list[dict]` |
| `get_project` | Get project details | `project_id` | `dict` or `None` |
| `get_env_variables` | Get env vars | `project_id` | `list[dict]` |
| `create_env_variable` | Create env var | `project_id`, `key`, `value`, `environment`, `target` | `dict` |
| `delete_env_variable` | Delete env var | `project_id`, `env_id` | `bool` |
| `check_connection` | Verify API access | None | `bool` |

### Data Classes

#### `DeploymentStatus`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Deployment ID |
| `status` | `str` | Current status |
| `url` | `str` | Deployment URL |
| `ready_state` | `str` | Ready state (READY, ERROR, etc.) |
| `created_at` | `datetime` | Creation timestamp |
| `project_id` | `str` | Project ID |
| `build_id` | `str` | Build ID |
| `meta` | `dict` | Metadata |

**Properties**:
- `is_ready: bool` - Check if deployment is ready
- `is_failed: bool` - Check if deployment failed
- `is_building: bool` - Check if still building

#### `DeploymentSpec`

| Field | Type | Description |
|-------|------|-------------|
| `project_name` | `str` | Project name |
| `git_repo` | `str` | Git repository URL |
| `ref` | `str` | Git ref (branch/tag) |
| `target` | `str | None` | Deployment target |
| `metadata` | `dict | None` | Additional metadata |

## Error Handling

```python
from httpx import HTTPStatusError

async with VercelManager() as manager:
    try:
        deployment = await manager.create_deployment(
            project_name="my-app",
            git_repo="https://github.com/user/repo",
            ref="main"
        )
        result = await manager.wait_for_deployment(deployment.id)

        if result.is_failed:
            print(f"Deployment failed: {result.ready_state}")
            # Get logs to debug
            logs = await manager.get_deployment_logs(deployment.id)

    except HTTPStatusError as e:
        print(f"API error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except TimeoutError as e:
        print(f"Deployment timeout: {e}")
```

## Rate Limits

- **Rate Limit**: 100 deployments per day per project
- **Headers**: Monitor `X-RateLimit-*` headers for quota
- **Best Practices**:
  - Check rate limit headers in responses
  - Implement exponential backoff for retries
  - Use preview deployments for testing

## Testing

```bash
# Run demo
python .blackbox5/integration/vercel/demo.py
```

## Troubleshooting

### Common Issues

**Issue**: Authentication failed
- **Solution**: Verify VERCEL_TOKEN is set correctly. Get a new token from https://vercel.com/account/tokens

**Issue**: Project not found
- **Solution**: Ensure the project exists in your Vercel account. Use `list_projects()` to find the correct project_id

**Issue**: Deployment timeout
- **Solution**: Increase timeout in `wait_for_deployment()`. Large projects may take longer to build

**Issue**: Team access denied
- **Solution**: Set VERCEL_TEAM_ID environment variable or pass `team_id` parameter

**Issue**: Rate limit exceeded
- **Solution**: Wait for rate limit reset (shown in X-RateLimit-Reset header). Reduce deployment frequency

## See Also

- Vercel Documentation: https://vercel.com/docs
- API Reference: https://vercel.com/docs/rest-api
- Deployment API: https://vercel.com/docs/rest-api#endpoints/deployments
