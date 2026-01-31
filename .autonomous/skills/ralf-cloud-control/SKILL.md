---
name: ralf-cloud-control
description: Control RALF agents running in Kubernetes from local machine
category: infrastructure
trigger: Need to start, stop, monitor, or manage cloud RALF agents
inputs:
  - name: command
    type: string
    description: Command to execute (start/stop/logs/scale)
  - name: agent_id
    type: string
    description: Optional agent ID for targeted commands
outputs:
  - name: status
    type: document
    description: Agent status, logs, or confirmation
---

# RALF Cloud Control

## Overview

This skill enables local agents (including yourself) to manage RALF agents running autonomously in Kubernetes. The `ralf-cloud` CLI provides a simple interface to control cloud-based RALF instances.

## Prerequisites

1. Kubernetes cluster running (Hetzner Cloud with k3s)
2. `kubectl` configured with kubeconfig
3. `ralf-cloud` CLI in PATH
4. Environment variables (optional):
   - `RALF_KUBECONFIG` - Path to kubeconfig (default: ~/.kube/config)
   - `RALF_NAMESPACE` - K8s namespace (default: ralf)

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `ralf-cloud status` | Show all running agents | `ralf-cloud status` |
| `ralf-cloud start` | Start a new RALF agent | `ralf-cloud start` |
| `ralf-cloud stop <id>` | Stop a specific agent | `ralf-cloud stop ralf-agent-abc` |
| `ralf-cloud logs <id>` | View agent logs | `ralf-cloud logs -f` |
| `ralf-cloud exec <id> <cmd>` | Run command in agent | `ralf-cloud exec ralf-agent-abc "ls"` |
| `ralf-cloud scale <n>` | Scale to N agents | `ralf-cloud scale 3` |

## Procedure

### Check Agent Status

1. Run: `ralf-cloud status`
2. Review output for:
   - Number of running agents
   - Agent health (Ready ✓ or ✗)
   - Pod names for reference

### Start a New RALF Agent

1. Run: `ralf-cloud start`
2. Wait for agent to be ready (usually 30-60 seconds)
3. Verify with: `ralf-cloud status`
4. View logs: `ralf-cloud logs -f`

### Monitor Agent Activity

1. Stream logs: `ralf-cloud logs -f`
2. Watch for:
   - Task selection
   - Claude Code execution
   - Git commits
   - Errors or crashes
3. Press Ctrl+C to exit log stream

### Stop an Agent

1. Get agent ID: `ralf-cloud status`
2. Stop: `ralf-cloud stop <agent-id>`
3. Verify: `ralf-cloud status` (should show 0 agents or terminating)

### Scale Multiple Agents

1. Run: `ralf-cloud scale 3`
2. This creates 3 parallel RALF agents
3. Each agent works independently on different tasks
4. Monitor: `ralf-cloud status`

### Execute Command in Agent

Useful for debugging or manual intervention:

```bash
# Check disk space
ralf-cloud exec ralf-agent-xxx "df -h"

# Check git status
ralf-cloud exec ralf-agent-xxx "cd /opt/blackbox5 && git status"

# Restart RALF loop
ralf-cloud exec ralf-agent-xxx "pkill -f claude && sleep 5 && /home/ralf/entrypoint.sh"
```

## Integration with BMAD

### As a Developer Agent (Amelia)

When working on a task that needs cloud compute:

```
I need to run this long-running optimization task.
Let me spawn a cloud RALF agent to handle it.

Run: ralf-cloud start
Run: ralf-cloud logs -f

The agent will work on this autonomously. I'll check back later.
```

### As a Scrum Master (Sam)

Monitor team progress:

```
Let me check how our cloud agents are performing.

Run: ralf-cloud status

We have 2 agents running. Let me check their recent activity.
Run: ralf-cloud logs ralf-agent-1 | tail -50
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No agents running" | Run `ralf-cloud start` |
| "Connection refused" | Check kubeconfig, verify cluster is up |
| Agent stuck | Run `ralf-cloud exec <id> "pkill -9 claude"` |
| Logs not streaming | Add `-f` flag: `ralf-cloud logs -f` |
| Permission denied | Verify `kubectl` works: `kubectl get nodes` |

## Architecture

```
Local Machine (Your Mac)
├─ ralf-cloud CLI (Python script)
├─ kubectl (talks to K8s API)
└─ kubeconfig (Hetzner cluster credentials)
         │
         ▼
Hetzner Cloud (k3s Kubernetes)
├─ Namespace: ralf
├─ Deployment: ralf-agent
│  └─ Pod(s): ralf-agent-xxx
│     ├─ Container: ralf
│     │  ├─ Claude Code CLI
│     │  ├─ RALF loop script
│     │  └─ Blackbox5 repo
│     └─ Volumes: code, data
└─ Service: ralf-agent (for future API)
```

## Notes

- Each agent runs independently
- Agents share the code volume (git repo)
- Agents have separate data volumes (runs, logs)
- Scaling up creates more parallel workers
- Scaling down terminates pods gracefully

## Related Files

- `bin/ralf-cloud` - CLI script for controlling RALF agents
