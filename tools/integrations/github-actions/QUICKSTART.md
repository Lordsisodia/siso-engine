# GitHub Actions Integration - Quick Start

Get started with the GitHub Actions integration in 5 minutes.

## 1. Get Your API Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" (Classic or Fine-grained)
3. Select required permissions:
   - `repo` - Full repository access
   - `workflow` - Workflow access
4. Generate and copy the token

## 2. Configure Environment Variables

```bash
# Add to your .env or shell profile
export GITHUB_TOKEN="ghp_your_token_here"

# For convenience (optional)
export GITHUB_OWNER="your_org_or_username"
export GITHUB_REPO="your_repository"
```

## 3. Install Dependencies

```bash
pip install requests
```

## 4. Basic Usage

### Initialize Manager

```python
from integration.github_actions import GitHubActionsManager

manager = GitHubActionsManager(
    owner="myorg",
    repo="myrepo"
)
```

### Common Operations

#### List Workflows

```python
workflows = manager.list_workflows()
for wf in workflows:
    print(f"{wf.name}: {wf.workflow_dispatch}")
```

#### Trigger a Workflow

```python
# Trigger workflow on main branch
manager.trigger_workflow(
    workflow_id=123456,
    ref="main",
    inputs={"environment": "staging"}
)
```

#### Monitor Workflow Runs

```python
# List recent runs
runs = manager.list_workflow_runs(branch="main")
for run in runs:
    print(f"Run {run.run_number}: {run.status} - {run.conclusion}")
```

#### Wait for Deployment

```python
# Wait for specific run to complete (max 30 min)
completed = manager.wait_for_deployment(
    run_id=789012,
    timeout=1800
)
print(f"Result: {completed.conclusion}")
```

#### Download Logs

```python
# Download logs to directory
log_path = manager.download_logs(
    run_id=789012,
    output_path="./logs"
)
print(f"Logs saved to: {log_path}")
```

#### List Artifacts

```python
# List artifacts from a run
artifacts = manager.list_artifacts(run_id=789012)
for art in artifacts:
    size_mb = art.size_in_bytes / (1024 * 1024)
    print(f"{art.name}: {size_mb:.2f} MB")
```

#### Download Artifact

```python
# Download specific artifact
path = manager.download_artifact(
    artifact_id=456789,
    output_path="./artifacts"
)
print(f"Artifact saved to: {path}")
```

## 5. Full Example

### Deployment Pipeline

```python
from integration.github_actions import GitHubActionsManager

def deploy_to_staging():
    """Trigger deployment to staging and monitor."""

    with GitHubActionsManager(owner="myorg", repo="myrepo") as manager:
        # Trigger staging deployment
        print("Triggering staging deployment...")
        manager.trigger_workflow(
            workflow_id=123456,
            ref="main",
            inputs={"environment": "staging"}
        )

        # Get the triggered run
        runs = manager.list_workflow_runs(
            branch="main",
            per_page=1
        )
        latest = runs[0]

        print(f"Monitoring run {latest.run_number}...")

        # Wait for completion
        completed = manager.wait_for_deployment(
            run_id=latest.id,
            timeout=1800  # 30 minutes
        )

        # Check result
        if completed.conclusion == "success":
            print("✅ Staging deployment successful!")

            # Download logs
            log_path = manager.download_logs(
                run_id=latest.id,
                output_path="./logs/staging"
            )
            print(f"Logs: {log_path}")

            # Download artifacts
            artifacts = manager.list_artifacts(run_id=latest.id)
            for art in artifacts:
                if art.name.startswith("build-"):
                    path = manager.download_artifact(
                        artifact_id=art.id,
                        output_path="./artifacts/staging"
                    )
                    print(f"Artifact: {path}")
        else:
            print(f"❌ Deployment failed: {completed.conclusion}")
            return False

    return True

if __name__ == "__main__":
    success = deploy_to_staging()
    exit(0 if success else 1)
```

## 6. Run the Demo

```bash
# Make sure GITHUB_TOKEN is set
echo $GITHUB_TOKEN

# Run the interactive demo
python .blackbox5/integration/github-actions/demo.py
```

## Tips

- **Context Manager**: Use `with` statement for automatic cleanup
- **Rate Limits**: 5,000 requests/hour, check with `manager.get_rate_limit()`
- **URL Expiration**: Log and artifact URLs expire in 1 minute
- **Timeouts**: Adjust `timeout` parameter for long-running workflows
- **Inputs**: Match input names exactly with workflow YAML

## Next Steps

- Read the [full documentation](README.md)
- Check out [examples](demo.py)
- Review the [API reference](README.md#api-reference)
- Learn about [workflow syntax](https://docs.github.com/en/actions/using-workflows)
