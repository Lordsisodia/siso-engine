---
name: github-codespaces-control
description: Spawn and manage Claude Code agents running in GitHub Codespaces from your local machine
category: infrastructure
trigger: Need to create cloud agents for 24/7 autonomous work on Blackbox5
inputs:
  - name: repository
    type: string
    description: Repository to work on
  - name: branch
    type: string
    description: Branch to checkout
  - name: machine_type
    type: string
    description: Machine type (basicLinux32gb, standardLinux32gb, premiumLinux)
outputs:
  - name: codespace
    type: document
    description: Running Codespace with autonomous agent
---

# GitHub Codespaces Control

## Overview

This skill enables local agents to spawn and control cloud-based Legacy agents running in GitHub Codespaces. Each Codespace agent:
- Runs Claude Code autonomously
- Works on Blackbox5 (self-improvement loop)
- Uses GLM 4.7 (not Kimi 2.5)
- Streams logs/output for visibility
- Runs 24/7 within free tier limits (60 hrs/month)

## Prerequisites

1. GitHub CLI (`gh`) installed and authenticated
2. GitHub account with Codespaces access
3. Repository with Blackbox5 code
4. ANTHROPIC_API_KEY available

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `gh codespace create` | Create new Codespace | `gh codespace create --repo blackbox5/blackbox5 --branch main` |
| `gh codespace list` | List all Codespaces | `gh codespace list` |
| `gh codespace ssh` | SSH into Codespace | `gh codespace ssh -c CODESPACE_NAME` |
| `gh codespace delete` | Delete Codespace | `gh codespace delete -c CODESPACE_NAME` |
| `gh codespace stop` | Stop Codespace | `gh codespace stop -c CODESPACE_NAME` |
| `gh codespace logs` | View logs | `gh codespace logs -c CODESPACE_NAME` |

## Procedure

### 1. Create a Legacy Agent Codespace

```bash
# Create Codespace for Blackbox5
gh codespace create \
  --repo blackbox5/blackbox5 \
  --branch main \
  --machine-type standardLinux32gb \
  --display-name "legacy-agent-$(date +%s)"
```

Machine types:
- `basicLinux32gb` - 2-core, 4GB RAM, 15GB storage (free tier)
- `standardLinux32gb` - 4-core, 8GB RAM, 32GB storage
- `premiumLinux` - 8-core, 16GB RAM, 64GB storage

### 2. Configure the Agent

SSH into the Codespace and set up:

```bash
# Get Codespace name
CODESPACE=$(gh codespace list --json name,displayName -q '.[] | select(.displayName | contains("legacy-agent")) | .name' | head -1)

# SSH and setup
gh codespace ssh -c $CODESPACE -- -t '
  # Install Claude Code
  curl -fsSL https://claude.ai/install.sh | sh

  # Configure for GLM 4.7
  mkdir -p ~/.config/claude
  cat > ~/.config/claude/settings.json << EOF
{
  "model": "glm-4.7",
  "preferredModel": "glm-4.7",
  "fallbackModels": ["claude-sonnet-4", "claude-haiku-4"]
}
EOF

  # Set API key
  export ANTHROPIC_API_KEY="your-key-here"

  # Create Legacy loop script
  cat > ~/legacy-loop.sh << \'INNEREOF'
#!/bin/bash
set -e
cd /workspaces/blackbox5

echo "═══════════════════════════════════════════════════════════"
echo "  Legacy Agent Starting"
echo "  Model: GLM 4.7"
echo "  Task: Improve Blackbox5"
echo "═══════════════════════════════════════════════════════════"

# Legacy improvement loop
while true; do
  echo ""
  echo "[$(date)] Starting improvement cycle..."

  # Check for tasks
  if [ -d ".autonomous/tasks/active" ]; then
    TASK=$(ls .autonomous/tasks/active/ 2>/dev/null | head -1)
    if [ -n "$TASK" ]; then
      echo "Found task: $TASK"
      claude -p "Execute task from .autonomous/tasks/active/$TASK" < /dev/null
    else
      echo "No active tasks, running general improvement..."
      claude -p "Analyze Blackbox5 codebase and suggest improvements. Look for: 1) Bugs 2) Missing features 3) Documentation gaps 4) Performance issues" < /dev/null
    fi
  fi

  echo "[$(date)] Cycle complete. Sleeping 60 seconds..."
  sleep 60
done
INNEREOF

  chmod +x ~/legacy-loop.sh
'
```

### 3. Start the Agent

```bash
# Start Legacy loop in background
gh codespace ssh -c $CODESPACE -- -t 'nohup ~/legacy-loop.sh > ~/legacy.log 2>&1 &'

# Verify it's running
gh codespace ssh -c $CODESPACE -- 'ps aux | grep legacy-loop'
```

### 4. Stream Logs (See What's Happening)

```bash
# Real-time log streaming
gh codespace ssh -c $CODESPACE -- -t 'tail -f ~/legacy.log'

# Or view recent logs
gh codespace ssh -c $CODESPACE -- 'tail -100 ~/legacy.log'
```

### 5. Manage Multiple Agents

```bash
# List all Legacy agents
gh codespace list --json displayName,name,state,lastUsedAt -q '.[] | select(.displayName | contains("legacy-agent"))'

# Stop all agents
for cs in $(gh codespace list --json name,displayName -q '.[] | select(.displayName | contains("legacy-agent")) | .name'); do
  echo "Stopping $cs..."
  gh codespace stop -c $cs
done

# Delete all agents
for cs in $(gh codespace list --json name,displayName -q '.[] | select(.displayName | contains("legacy-agent")) | .name'); do
  echo "Deleting $cs..."
  gh codespace delete -c $cs --force
done
```

## Self-Improvement Configuration

Create a `.devcontainer/legacy-agent.json` in your repo:

```json
{
  "name": "Legacy Agent",
  "image": "mcr.microsoft.com/devcontainers/universal:2",
  "features": {
    "ghcr.io/devcontainers/features/node:1": {},
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },
  "postCreateCommand": "curl -fsSL https://claude.ai/install.sh | sh",
  "customizations": {
    "vscode": {
      "extensions": ["anthropic.claude-code"]
    }
  },
  "remoteEnv": {
    "ANTHROPIC_API_KEY": "${localEnv:ANTHROPIC_API_KEY}"
  }
}
```

## Integration with BMAD

### As a Product Manager (John)

```
I need to improve Blackbox5 documentation.

Run: gh codespace create --repo blackbox5/blackbox5 --branch main --display-name "legacy-docs-$(date +%s)"
Run: gh codespace ssh -c <name> -- -t '~/legacy-loop.sh docs-improvement &'

Now I have an agent working on docs in the cloud.
```

### As a Developer (Amelia)

```
The engine needs refactoring. I'll spawn a specialized agent.

Run: gh codespace create --repo blackbox5/blackbox5 --branch refactor-branch --machine-type premiumLinux
Run: gh codespace ssh -c <name> -- -t 'claude -p "Refactor engine core for performance"'
```

### As a Scrum Master (Sam)

```
Let me check all our cloud agents.

Run: gh codespace list --json displayName,state,lastUsedAt | jq '.[] | select(.displayName | contains("legacy"))'

We have 3 agents running. Let me check their logs.
```

## Cost Management

| Usage | Cost |
|-------|------|
| Free tier | 60 hours/month, 2-core, 4GB |
| Additional | $0.18/hour for 2-core |
| 4-core | $0.36/hour |
| 8-core | $0.72/hour |

**Budget tips:**
- Use `basicLinux32gb` for free tier
- Stop agents when not needed: `gh codespace stop`
- Set up spending limits in GitHub settings
- Monitor usage: `gh codespace list`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Codespace won't start | Check GitHub status, try different region |
| Claude Code not found | Re-run install: `curl -fsSL https://claude.ai/install.sh | sh` |
| API key not set | Export in SSH session or use `.env` file |
| Agent stopped unexpectedly | Check logs: `tail -f ~/legacy.log` |
| Out of free hours | Stop inactive agents, upgrade to paid, or wait for next month |

## Architecture

```
Your MacBook (Local)
├─ BMAD Agent (You/RALF)
├─ GitHub CLI (gh)
└─ SSH keys
         │
         ▼
GitHub Codespaces (Cloud)
├─ Codespace 1: legacy-agent-001
│  ├─ Ubuntu environment
│  ├─ Claude Code (GLM 4.7)
│  ├─ Blackbox5 repo
│  └─ legacy-loop.sh (running)
├─ Codespace 2: legacy-agent-002
│  └─ (another task)
└─ Codespace 3: legacy-agent-003
   └─ (another task)
```

## Notes

- Each Codespace is isolated
- Agents can work on different branches
- Logs are ephemeral (save to repo for persistence)
- Free tier resets monthly
- Use `screen` or `tmux` for persistent sessions

## Related Files

- `bin/legacy-codespace` - CLI helper for Codespace management
