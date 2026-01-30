# Vercel Integration - Quick Start

Get started with the Vercel integration in 5 minutes.

## 1. Get Your API Token

1. Visit https://vercel.com/account/tokens
2. Click "Create Token"
3. Give it a name (e.g., "BlackBox5 Integration")
4. Select appropriate scopes:
   - Deployments: Create, Read, Delete
   - Projects: Read
   - Environment Variables: Create, Read, Delete
5. Copy the generated token

## 2. Configure Environment Variables

```bash
# Add to your .env or shell profile
export VERCEL_TOKEN="your_token_here"

# Optional: If using team accounts
export VERCEL_TEAM_ID="your_team_id"
```

## 3. Install Dependencies

```bash
pip install httpx
```

Add to `.blackbox5/engine/requirements.txt`:
```txt
httpx>=0.25.0
```

## 4. Basic Usage

### Initialize Manager

```python
from integration.vercel import VercelManager

manager = VercelManager()
```

### Common Operations

#### List Projects

```python
projects = await manager.list_projects(limit=10)
for project in projects:
    print(f"{project['name']} - {project['framework']}")
```

#### Create Deployment

```python
deployment = await manager.create_deployment(
    project_name="my-app",
    git_repo="https://github.com/user/repo",
    ref="main"
)
print(f"Deployment ID: {deployment.id}")
```

#### Wait for Deployment

```python
result = await manager.wait_for_deployment(
    deployment.id,
    timeout=600,
    interval=5
)

if result.is_ready:
    print(f"✅ Deployed to: {result.url}")
else:
    print(f"❌ Deployment failed")
```

#### Check Deployment Status

```python
deployment = await manager.get_deployment("dpl_abc123")
print(f"Status: {deployment.ready_state}")
print(f"Building: {deployment.is_building}")
print(f"Ready: {deployment.is_ready}")
```

#### List Deployments

```python
deployments = await manager.list_deployments(
    project_id="prj_xyz789",
    limit=20
)

for d in deployments:
    print(f"{d.id[:8]}... - {d.ready_state} - {d.url}")
```

#### Get Deployment Logs

```python
logs = await manager.get_deployment_logs("dpl_abc123")
for log in logs:
    print(f"[{log['timestamp']}] {log['message']}")
```

#### Cancel Deployment

```python
success = await manager.cancel_deployment("dpl_abc123")
if success:
    print("Deployment cancelled")
```

#### Manage Environment Variables

```python
# Create env variable
await manager.create_env_variable(
    project_id="prj_xyz789",
    key="DATABASE_URL",
    value="postgresql://...",
    environment=["production", "preview"],
    target=["production"]
)

# List env variables
env_vars = await manager.get_env_variables("prj_xyz789")
for env in env_vars:
    print(f"{env['key']}: {env['type']}")
```

## 5. Full Example

```python
import asyncio
from integration.vercel import VercelManager

async def deploy_application():
    async with VercelManager() as manager:
        # Create a deployment
        deployment = await manager.create_deployment(
            project_name="my-nextjs-app",
            git_repo="https://github.com/user/nextjs-app",
            ref="main"
        )

        print(f"Created deployment: {deployment.id}")
        print(f"URL: {deployment.url}")

        # Wait for completion
        result = await manager.wait_for_deployment(
            deployment.id,
            timeout=600
        )

        if result.is_ready:
            print(f"✅ Deployment successful!")
            print(f"   URL: {result.url}")
        else:
            print(f"❌ Deployment failed: {result.ready_state}")

            # Get logs for debugging
            logs = await manager.get_deployment_logs(deployment.id)
            print("\nBuild logs:")
            for log in logs:
                print(f"  {log}")

asyncio.run(deploy_application())
```

## 6. Using with Team Accounts

```python
from integration.vercel import VercelManager

# Method 1: Environment variable
# export VERCEL_TEAM_ID="team_xyz123"
manager = VercelManager()

# Method 2: Pass directly
manager = VercelManager(team_id="team_xyz123")

# All operations will use the team context
projects = await manager.list_projects()
```

## Next Steps

- Read the [full documentation](README.md)
- Check out [demo.py](demo.py) for more examples
- Review the [API reference](README.md#api-reference)
- Learn about [rate limiting](README.md#rate-limits)

## Common Patterns

### Deploy with Monitoring

```python
async def deploy_with_monitoring(repo_url: str, branch: str):
    async with VercelManager() as manager:
        # Create deployment
        deployment = await manager.create_deployment(
            project_name="production-app",
            git_repo=repo_url,
            ref=branch,
            target="production"
        )

        print(f"Deploying {branch} to production...")

        # Monitor with status updates
        while True:
            status = await manager.get_deployment(deployment.id)

            if status.is_ready:
                print(f"✅ Success: {status.url}")
                break
            elif status.is_failed:
                print(f"❌ Failed: {status.ready_state}")

                # Get logs
                logs = await manager.get_deployment_logs(deployment.id)
                for log in logs:
                    print(f"  {log}")
                break
            else:
                print(f"⏳ Building... {status.ready_state}")
                await asyncio.sleep(10)
```

### Deploy to Preview Environment

```python
async def deploy_preview(pr_number: int):
    async with VercelManager() as manager:
        deployment = await manager.create_deployment(
            project_name="my-app",
            git_repo="https://github.com/user/repo",
            ref=f"pull/{pr_number}/head",
            metadata={"githubPullRequest": str(pr_number)}
        )

        result = await manager.wait_for_deployment(deployment.id)

        return result.url
```
