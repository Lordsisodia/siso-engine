---
name: legacy-cloud-control
description: Control multiple Legacy agents running in Kubernetes, each with different projects, tasks, and system prompts
category: infrastructure
trigger: Need to create, start, stop, or manage cloud Legacy agents for specific projects
inputs:
  - name: instance_name
    type: string
    description: Unique name for the Legacy instance
  - name: project
    type: string
    description: Project to work on (blackbox5, siso-internal, etc.)
  - name: task
    type: string
    description: Task description for the agent
  - name: prompt
    type: string
    description: Optional custom system prompt
outputs:
  - name: status
    type: document
    description: Agent status, logs, or confirmation
---

# Legacy Cloud Control

## Overview

This skill enables local agents (including yourself) to manage multiple Legacy agents running autonomously in Kubernetes. Each Legacy instance has:
- **Unique identity** (instance name)
- **Specific project** (blackbox5, siso-internal, etc.)
- **Defined task** (what to work on)
- **Custom system prompt** (how to behave)
- **Isolated project memory** (tasks, runs, logs)

## Prerequisites

1. Kubernetes cluster running (Hetzner Cloud with k3s)
2. `kubectl` configured with kubeconfig
3. `legacy-cloud` CLI in PATH
4. Environment variables (optional):
   - `LEGACY_KUBECONFIG` - Path to kubeconfig (default: ~/.kube/config)
   - `LEGACY_NAMESPACE` - K8s namespace (default: legacy)

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `legacy-cloud status` | Show all running agents | `legacy-cloud status` |
| `legacy-cloud list` | List all Legacy configurations | `legacy-cloud list` |
| `legacy-cloud create` | Create new Legacy instance | `legacy-cloud create --name bb5-docs --project blackbox5 --task "Improve documentation"` |
| `legacy-cloud start <name>` | Start a Legacy instance | `legacy-cloud start bb5-docs` |
| `legacy-cloud stop <name>` | Stop a Legacy instance | `legacy-cloud stop bb5-docs` |
| `legacy-cloud logs <name>` | View agent logs | `legacy-cloud logs bb5-docs -f` |
| `legacy-cloud exec <name> <cmd>` | Run command in agent | `legacy-cloud exec bb5-docs "git status"` |
| `legacy-cloud scale <name> <n>` | Scale instance to N replicas | `legacy-cloud scale bb5-docs 3` |

## How Legacy Instances Work

### Each Instance Has Its Own:

1. **ConfigMap** with custom system prompt
   - `legacy-config-<instance-name>`
   - Contains SYSTEM_PROMPT and legacy.md

2. **Deployment** for the agent
   - `legacy-agent-<instance-name>`
   - Can be scaled independently

3. **Project Directory**
   - `/opt/blackbox5/5-project-memory/<project>`
   - Isolated task memory

4. **Environment Variables**
   - `LEGACY_PROJECT_NAME` - Which project
   - `LEGACY_PROJECT_DIR` - Where to work
   - `LEGACY_TASK_DESCRIPTION` - What to do

### Example Instances

| Instance Name | Project | Task | Replicas |
|---------------|---------|------|----------|
| bb5-docs | blackbox5 | Improve documentation | 2 |
| bb5-refactor | blackbox5 | Refactor engine code | 1 |
| siso-api | siso-internal | Build API endpoints | 3 |
| research-k8s | research | Explore K8s patterns | 1 |

## Procedure

### Create a New Legacy Instance

1. Define the instance:
   - **Name**: Unique identifier (e.g., `bb5-docs`)
   - **Project**: Which project to work on (e.g., `blackbox5`)
   - **Task**: What to focus on (e.g., "Improve all documentation files")

2. Create the instance:
   ```bash
   legacy-cloud create \
     --name bb5-docs \
     --project blackbox5 \
     --task "Improve documentation and add examples"
   ```

3. (Optional) Add custom system prompt:
   ```bash
   legacy-cloud create \
     --name bb5-refactor \
     --project blackbox5 \
     --task "Refactor the engine code" \
     --prompt "You are a refactoring expert. Focus on code quality and performance."
   ```

### Start an Instance

```bash
legacy-cloud start bb5-docs
```

This creates a pod running Legacy with:
- The custom system prompt for this instance
- Access to the specified project
- Its own isolated task memory

### Check Status

```bash
legacy-cloud status
```

Shows:
```
Instance              Project              Replicas   Status
bb5-docs              blackbox5            2          2/2 running
bb5-refactor          blackbox5            1          1/1 running
siso-api              siso-internal        0          stopped
```

### Scale an Instance

Run multiple copies of the same agent:

```bash
legacy-cloud scale bb5-docs 3
```

This creates 3 pods all working on `bb5-docs` tasks in parallel.

### Monitor Logs

```bash
# Stream logs from specific instance
legacy-cloud logs bb5-docs -f

# View logs from one of the replicas
legacy-cloud logs bb5-docs
```

### Stop an Instance

```bash
legacy-cloud stop bb5-docs
```

### Execute Command in Instance

```bash
# Check git status
legacy-cloud exec bb5-docs "cd /opt/blackbox5 && git status"

# View active tasks
legacy-cloud exec bb5-docs "ls /opt/blackbox5/5-project-memory/blackbox5/.autonomous/tasks/active/"

# Restart the Legacy loop
legacy-cloud exec bb5-docs "pkill -f claude && sleep 5 && /home/legacy/entrypoint.sh"
```

## Integration with BMAD

### As a Product Manager (John)

```
I need to improve Blackbox5 documentation.
Let me create a dedicated Legacy instance for this.

Run: legacy-cloud create --name bb5-docs --project blackbox5 --task "Improve all documentation"
Run: legacy-cloud start bb5-docs
Run: legacy-cloud scale bb5-docs 2

Now I have 2 agents working on documentation in parallel.
```

### As a Developer (Amelia)

```
The engine needs refactoring. I'll spawn a specialized agent.

Run: legacy-cloud create --name bb5-refactor --project blackbox5 --task "Refactor engine core" --prompt "Focus on performance optimization"
Run: legacy-cloud start bb5-refactor
Run: legacy-cloud logs bb5-refactor -f
```

### As a Scrum Master (Sam)

```
Let me check all our cloud agents.

Run: legacy-cloud status

We have:
- 2 agents on documentation
- 1 agent on refactoring
- 3 agents on API development

Run: legacy-cloud logs siso-api | tail -50
```

## Project Structure in Kubernetes

```
Namespace: legacy
├── ConfigMaps (one per instance)
│   ├── legacy-config-bb5-docs
│   ├── legacy-config-bb5-refactor
│   └── legacy-config-siso-api
├── Deployments (one per instance)
│   ├── legacy-agent-bb5-docs (replicas: 2)
│   ├── legacy-agent-bb5-refactor (replicas: 1)
│   └── legacy-agent-siso-api (replicas: 3)
├── Pods (actual running agents)
│   ├── legacy-agent-bb5-docs-xxx
│   ├── legacy-agent-bb5-docs-yyy
│   ├── legacy-agent-bb5-refactor-xxx
│   └── etc.
└── Persistent Volumes
    ├── blackbox5-code (shared)
    └── legacy-data (shared)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Instance not found" | Check `legacy-cloud list` for correct name |
| "No pods found" | Run `legacy-cloud start <name>` |
| Wrong project | Create new instance with correct `--project` |
| Need different task | Create new instance with different `--task` |
| Custom behavior | Use `--prompt` to customize system prompt |

## Notes

- Each instance is completely independent
- Instances can work on the same project with different tasks
- Scaling creates more pods with identical configuration
- Stopping an instance preserves the configuration (just scales to 0)
- To delete an instance completely, use `kubectl delete deployment legacy-agent-<name>`

## Related Files

- `bin/legacy-cloud` - CLI script for controlling Legacy agents
