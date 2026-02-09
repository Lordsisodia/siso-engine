# Coordinator Agent Quick Start

## Concept

You act as a **Coordinator Agent** - a persistent conversational interface that spawns and manages ephemeral execution agents. This allows you to maintain continuous conversation with the user while offloading execution work to background agents.

## Workflow

```
1. User gives you a task
2. You decompose it into subtasks
3. You spawn execution agents for each subtask
4. You monitor their progress
5. You report back to user when complete
```

## Usage

### Spawning an Agent

```bash
# Spawn a researcher
./claude-coordinator.sh spawn researcher \
  "Analyze XP footer component" \
  "Find the XP footer component, analyze its current implementation, and suggest 3 improvements"

# Spawn an implementer
./claude-coordinator.sh spawn implementer \
  "Redesign XP footer with progress rows" \
  "Replace task cards with horizontal progress rows showing earned/max XP"
```

### Monitoring Agents

```bash
# Check specific agent
./claude-coordinator.sh monitor agent-1738051200-a1b2c3d4

# List all agents
./claude-coordinator.sh monitor --all
```

### Waiting for Completion

```bash
# Wait for agent (5 minute timeout)
./claude-coordinator.sh wait agent-1738051200-a1b2c3d4

# Wait with custom timeout
./claude-coordinator.sh wait agent-1738051200-a1b2c3d4 600
```

### Generating Reports

```bash
# Show all agent status
./claude-coordinator.sh report
```

## Agent Types

| Type | Purpose | Temperature |
|------|---------|-------------|
| **researcher** | Explore and analyze codebase | 0.3 |
| **implementer** | Write code and features | 0.5 |
| **tester** | Test and validate | 0.4 |
| **planner** | Create implementation plans | 0.6 |

## Example Conversation

### User Request
```
"Improve the morning routine XP footer component"
```

### Coordinator Response
```
I'll break this down into subtasks and spawn agents to handle them:

1. **Research**: Analyze current implementation
2. **Design**: Plan the new UI approach
3. **Implement**: Build the redesigned component

Spawning agents now...
```

### Spawn Commands
```bash
# Agent 1: Research
research_agent=$(./claude-coordinator.sh spawn researcher \
  "Analyze XP footer implementation" \
  "Find and analyze the XP Footer Summary component, document current structure, identify improvement opportunities")

# Agent 2: Design
plan_agent=$(./claude-coordinator.sh spawn planner \
  "Design XP footer improvements" \
  "Create a detailed plan for redesigning the XP footer with progress rows instead of cards")

# Agent 3: Implement
implement_agent=$(./claude-coordinator.sh spawn implementer \
  "Implement XP footer redesign" \
  "Implement the redesigned XP footer with horizontal progress rows showing earned/max XP for each task")
```

### Monitoring
```bash
# Check all agents
./claude-coordinator.sh monitor --all

# Wait for completion
./claude-coordinator.sh wait $research_agent
./claude-coordinator.sh wait $plan_agent
./claude-coordinator.sh wait $implement_agent
```

### Report Back
```
✅ All agents completed!

Research: Found 3 key areas for improvement
  - Replace cards with progress rows
  - Show earned/max XP ratios
  - Integrate bonus display inline

Planning: Created detailed implementation plan with 5 steps
  - 1. Redesign component structure
  - 2. Add progress bar rows
  - 3. Implement max XP tracking
  - 4. Add bonus badges
  - 5. Test and validate

Implementation: Successfully redesigned component
  - Modified: XPFooterSummary.tsx
  - Tests: ✅ Passing
  - Typecheck: ✅ Clean

Ready for your review!
```

## Best Practices

### 1. Task Decomposition
Break complex tasks into focused subtasks:
- ✅ "Research XP footer component"
- ✅ "Design progress row layout"
- ✅ "Implement progress bars"
- ❌ "Do everything at once"

### 2. Agent Selection
Match agent type to the work:
- **researcher**: Exploration, analysis, discovery
- **planner**: Architecture, design, breakdown
- **implementer**: Coding, features, fixes
- **tester**: Validation, QA, testing

### 3. Parallel Execution
Spawn independent tasks in parallel:
```bash
# These can run simultaneously
agent1=$(./claude-coordinator.sh spawn researcher "Task A" "...")
agent2=$(./claude-coordinator.sh spawn researcher "Task B" "...")
agent3=$(./claude-coordinator.sh spawn planner "Task C" "...")
```

### 4. Status Updates
Keep user informed:
```
🔄 Agent 1 (researcher): Running - 60s elapsed
🔄 Agent 2 (planner): Running - 45s elapsed
⏳ Agent 3 (implementer): Queued
```

### 5. Error Handling
If an agent fails, spawn a replacement:
```bash
if ! ./claude-coordinator.sh wait $agent_id 300; then
  echo "Agent failed, spawning replacement..."
  new_agent=$(./claude-coordinator.sh spawn implementer "Retry task" "...")
fi
```

## Advanced Usage

### Custom Agent Definitions

Modify the `AGENTS_CONFIG` in the script to add custom agents:

```json
{
  "optimizer": {
    "description": "Optimizes code for performance",
    "prompt": "You are a performance optimizer. Profile code, identify bottlenecks, and implement optimizations.",
    "temperature": 0.4
  },
  "documenter": {
    "description": "Writes documentation",
    "prompt": "You are a technical writer. Create clear, comprehensive documentation with examples.",
    "temperature": 0.5
  }
}
```

### Structured Output

Agents return JSON responses:
```json
{
  "status": "success",
  "summary": "Redesigned XP footer with progress rows",
  "files_modified": ["XPFooterSummary.tsx"],
  "tests_run": true,
  "errors": [],
  "next_steps": ["Review with user", "Merge to main"],
  "artifacts": {
    "screenshot": "/path/to/screenshot.png",
    "performance_metrics": {"render_time_ms": 16}
  }
}
```

### Cleanup

Remove old agent data:
```bash
# Cleanup agents older than 1 hour
./claude-coordinator.sh cleanup 3600

# Cleanup agents older than 1 day
./claude-coordinator.sh cleanup 86400
```

## Troubleshooting

### Agent Stuck
```bash
# Check if process is running
ps aux | grep claude

# Kill stuck agent
kill $(cat /tmp/claude-coordination/agents/agent-*.pid)
```

### No Output
```bash
# Check output file
cat /tmp/claude-coordination/results/agent-*.json

# Check logs
tail -f /tmp/claude-coordination/logs/coordinator.log
```

### Context Loss
Agents work independently - they don't share context. Include all necessary information in the task description.

## Integration with Blackbox5

This coordinator system integrates with existing Blackbox5:
- Uses same AGENTS.md guidelines
- Updates WORK-LOG.md automatically
- Creates ADRs in decisions/
- Respects project structure

See `COORDINATOR-AGENT-DESIGN.md` for full architecture details.
