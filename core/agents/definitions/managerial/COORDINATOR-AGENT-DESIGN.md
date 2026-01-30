# Coordinator Agent Design

**Concept:** A persistent conversational agent that spawns and monitors ephemeral execution agents

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  USER                                                       │
│  (Persistent conversation)                                  │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  COORDINATOR AGENT (You)                                    │
│  - Receives user requests                                   │
│  - Plans task decomposition                                 │
│  - Spawns execution agents                                  │
│  - Monitors progress                                        │
│  - Reports back to user                                     │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├─── spawns (via CLI)
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  EXECUTION AGENTS (Ephemeral)                               │
│  - Receive task brief via --system-prompt                  │
│  - Execute via --print --output-format json                 │
│  - Report results via JSON output                          │
│  - Self-terminate after completion                          │
└─────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  SHARED STATE                                                │
│  - /tmp/coordination/agent-{id}.json (status, progress)    │
│  - /tmp/coordination/results/{id}/ (outputs, artifacts)    │
└─────────────────────────────────────────────────────────────┘
```

## Implementation

### 1. Agent Spawning Function

```bash
# Coordinator spawns an execution agent
claude --print \
  --output-format json \
  --session-id "${agent_id}" \
  --agent "executor" \
  --system-prompt "$(cat <<'EOF'
You are an execution agent. Your task is to:
${task_briefing}

You MUST output your results as JSON:
{
  "status": "success|failure|partial",
  "summary": "Brief summary of work done",
  "files_modified": ["file1.ts", "file2.ts"],
  "next_steps": ["Step 1", "Step 2"],
  "artifacts": {"key": "value"}
}

Execute the task and report back.
EOF
)" \
  "${task_description}"
```

### 2. Progress Monitoring

```bash
# Coordinator checks agent status
claude --resume "${agent_id}" --print --output-format json <<EOF
Are you still working? If complete, output your final status.
EOF
```

### 3. Custom Agent Definition

```json
{
  "executor": {
    "description": "Executes tasks and reports back",
    "prompt": "You are a task executor. Work efficiently and report results in JSON format.",
    "temperature": 0.7
  },
  "researcher": {
    "description": "Researches and explores codebase",
    "prompt": "You are a codebase researcher. Find patterns and report findings.",
    "temperature": 0.3
  },
  "implementer": {
    "description": "Implements features",
    "prompt": "You are a feature implementer. Write clean, tested code.",
    "temperature": 0.5
  }
}
```

## Coordination Protocol

### Task Briefing Format

```markdown
## Task: ${task_title}

**Context:**
- Working directory: ${pwd}
- Git branch: ${git_branch}
- Recent changes: ${recent_commits}

**Objectives:**
1. ${objective_1}
2. ${objective_2}

**Constraints:**
- Follow AGENTS.md guidelines
- Update WORK-LOG.md
- Create ADRs for decisions

**Output Format:**
You MUST respond with valid JSON matching this schema:
{
  "type": "object",
  "properties": {
    "status": {"type": "string", "enum": ["success", "failure", "partial"]},
    "summary": {"type": "string"},
    "files_modified": {"type": "array", "items": {"type": "string"}},
    "tests_run": {"type": "boolean"},
    "errors": {"type": "array", "items": {"type": "string"}},
    "next_steps": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["status", "summary"]
}
```

### State Management

```bash
# Shared state directory
mkdir -p /tmp/claude-coordination/{agents,results,logs}

# Agent state file
cat > /tmp/claude-coordination/agents/${agent_id}.json <<EOF
{
  "agent_id": "${agent_id}",
  "task": "${task_title}",
  "status": "spawned",
  "spawned_at": "${timestamp}",
  "coordinator_pid": "${$}",
  "working_directory": "${pwd}"
}
EOF

# Progress updates
echo '{"status": "in_progress", "percent": 50, "message": "Processing..."}' \
  > /tmp/claude-coordination/agents/${agent_id}-progress.json
```

## Coordinator Workflow

### 1. Receive Task
```
User: "Improve the XP footer UI"
```

### 2. Decompose & Plan
```
Coordinator:
- Breaking into subtasks:
  1. Research current implementation
  2. Design new UI approach
  3. Implement changes
  4. Test and validate
```

### 3. Spawn Agents
```bash
# Spawn researcher
agent_1=$(uuidgen)
claude --print --output-format json \
  --agent "researcher" \
  --session-id "$agent_1" \
  --system-prompt "$(briefing "Research XP footer")" \
  "Analyze the current XP footer component and suggest improvements"

# Spawn implementer
agent_2=$(uuidgen)
claude --print --output-format json \
  --agent "implementer" \
  --session-id "$agent_2" \
  --system-prompt "$(briefing "Implement XP footer changes")" \
  "Implement the redesigned XP footer component"
```

### 4. Monitor Progress
```bash
# Check in on agents
for agent_id in "$agent_1" "$agent_2"; do
  status=$(cat /tmp/claude-coordination/agents/${agent_id}-progress.json 2>/dev/null || echo "{}")
  echo "Agent $agent_id: $status"
done
```

### 5. Report to User
```
Coordinator:
✅ Research complete: Found 3 improvement opportunities
🔄 Implementation in progress: 60% complete
   - Progress bar rows implemented
   - Hero section updated
   - Pending: Bonus display refinements
```

## Error Handling

### Agent Failure Recovery
```bash
# If agent fails, spawn replacement
if [[ $status == "failure" ]]; then
  new_agent=$(uuidgen)
  claude --print --output-format json \
    --agent "executor" \
    --session-id "$new_agent" \
    --system-prompt "$(cat <<EOF
Previous agent failed on: ${failed_task}
Error was: ${error_message}

Please retry with a different approach.
EOF
)" \
    "${retry_task}"
fi
```

### Timeout Handling
```bash
# Kill stuck agents after timeout
timeout 300 claude --print ... || {
  echo "Agent timed out, spawning replacement..."
  # Spawn replacement
}
```

## Advantages

1. **Continuous Conversation**: User stays with coordinator, never loses context
2. **Parallel Execution**: Multiple agents work simultaneously
3. **Fault Tolerance**: Failed agents can be replaced
4. **Progress Visibility**: Real-time status updates
5. **Resource Management**: Agents self-terminate, no leaks
6. **Scalability**: Spawn as many agents as needed

## Next Steps

1. Create custom agent definitions
2. Implement coordination state management
3. Build CLI helper scripts for spawning/monitoring
4. Create coordinator prompt template
5. Test with simple parallel task execution
