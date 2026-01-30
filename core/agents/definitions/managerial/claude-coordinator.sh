#!/bin/bash
# Claude Coordinator - Multi-Agent Orchestration System
# Usage: ./claude-coordinator.sh spawn|monitor|report [args]

set -euo pipefail

# Configuration
COORDINATION_DIR="${TMPDIR:-/tmp}/claude-coordination"
AGENTS_DIR="$COORDINATION_DIR/agents"
RESULTS_DIR="$COORDINATION_DIR/results"
LOGS_DIR="$COORDINATION_DIR/logs"

# Create directories
mkdir -p "$AGENTS_DIR" "$RESULTS_DIR" "$LOGS_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
  local level=$1
  shift
  local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*"
  echo -e "${msg}" | tee -a "$LOGS_DIR/coordinator.log"
}

# Generate unique agent ID (valid RFC 4122 UUID for Claude Code session-id)
generate_agent_id() {
  # Generate a proper UUID - uuidgen on macOS/Linux produces valid format
  uuidgen | tr '[:upper:]' '[:lower:]'
}

# Agent definitions
AGENTS_CONFIG='{
  "researcher": {
    "description": "Researches and explores codebase",
    "prompt": "You are a codebase researcher. Your job is to explore, analyze, and report findings clearly and concisely. Use grep, find, and read tools extensively. Always provide specific file paths and line numbers.",
    "temperature": 0.3
  },
  "implementer": {
    "description": "Implements features and fixes",
    "prompt": "You are a feature implementer. Write clean, tested, well-documented code. Follow existing patterns in the codebase. Always run typecheck before reporting completion.",
    "temperature": 0.5
  },
  "tester": {
    "description": "Tests and validates implementations",
    "prompt": "You are a QA tester. Create comprehensive test plans, execute tests, and report bugs clearly. Prioritize edge cases and integration testing.",
    "temperature": 0.4
  },
  "planner": {
    "description": "Creates detailed implementation plans",
    "prompt": "You are a technical planner. Break down complex tasks into clear, actionable steps. Identify dependencies and risks. Provide time estimates.",
    "temperature": 0.6
  }
}'

# Spawn a new execution agent
spawn_agent() {
  local agent_type=$1
  local task_title=$2
  local task_description=$3
  local agent_id
  agent_id=$(generate_agent_id)

  log INFO "Spawning $agent_type agent: $agent_id"
  log INFO "Task: $task_title"

  # Create agent state file
  cat > "$AGENTS_DIR/${agent_id}.json" <<EOF
{
  "agent_id": "$agent_id",
  "agent_type": "$agent_type",
  "task_title": "$task_title",
  "status": "spawned",
  "spawned_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "coordinator_pid": "$$",
  "working_directory": "$(pwd)",
  "git_branch": "$(git branch --show-current 2>/dev/null || echo 'no-git')"
}
EOF

  # Create system prompt with task briefing
  local system_prompt
  system_prompt=$(cat <<EOF
You are a $agent_type agent working on task: $task_title

CONTEXT:
- Working directory: $(pwd)
- Git branch: $(git branch --show-current 2>/dev/null || echo 'no-git')
- Recent commits:
$(git log -5 --oneline 2>/dev/null || echo 'No git history')

YOUR TASK:
$task_description

CONSTRAINTS:
- Follow AGENTS.md guidelines if present
- Update WORK-LOG.md with your actions
- Create ADRs for significant decisions
- Run typecheck before completion
- Validate your work

REQUIRED OUTPUT FORMAT:
You MUST output valid JSON as your final response matching this schema:
{
  "status": "success|failure|partial",
  "summary": "Brief summary of what was accomplished",
  "files_modified": ["file1.ts", "file2.ts"],
  "tests_run": true|false,
  "errors": ["error message 1", "error message 2"],
  "next_steps": ["Next action 1", "Next action 2"],
  "artifacts": {"key": "value"}
}

Execute the task now. When complete, output ONLY the JSON response.
EOF
)

  # Spawn the agent
  log INFO "Starting agent process..."
  local output_file="$RESULTS_DIR/${agent_id}.json"

  claude --print \
    --output-format json \
    --session-id "$agent_id" \
    --agents "$AGENTS_CONFIG" \
    --agent "$agent_type" \
    --system-prompt "$system_prompt" \
    "$task_description" \
    > "$output_file" 2>&1 &

  local agent_pid=$!
  echo "$agent_pid" > "$AGENTS_DIR/${agent_id}.pid"

  # Update agent state
  update_agent_status "$agent_id" "running" "{\"pid\": $agent_pid, \"output_file\": \"$output_file\"}"

  log INFO "Agent $agent_id spawned with PID $agent_pid"
  echo "$agent_id"
}

# Update agent status
update_agent_status() {
  local agent_id=$1
  local status=$2
  local extra_data=${3:-"{}"}

  local state_file="$AGENTS_DIR/${agent_id}.json"
  if [[ -f "$state_file" ]]; then
    # Update existing state
    local current_state
    current_state=$(cat "$state_file")
    local updated_state
    updated_state=$(echo "$current_state" | jq --arg status "$status" --argjson extra "$extra_data" '
      .status = $status |
      .updated_at = now |
      . += $extra
    ')
    echo "$updated_state" > "$state_file"
  fi
}

# Monitor agent progress
monitor_agent() {
  local agent_id=$1
  local state_file="$AGENTS_DIR/${agent_id}.json"

  if [[ ! -f "$state_file" ]]; then
    log ERROR "Agent $agent_id not found"
    return 1
  fi

  local status
  status=$(jq -r '.status' "$state_file")
  local agent_type
  agent_type=$(jq -r '.agent_type' "$state_file")
  local task_title
  task_title=$(jq -r '.task_title' "$state_file")

  echo -e "${BLUE}Agent: ${NC}$agent_id"
  echo -e "${BLUE}Type:  ${NC}$agent_type"
  echo -e "${BLUE}Task:  ${NC}$task_title"
  echo -e "${BLUE}Status:${NC} $status"

  # Check if process is still running
  local pid_file="$AGENTS_DIR/${agent_id}.pid"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid=$(cat "$pid_file")
    if ps -p "$pid" > /dev/null 2>&1; then
      echo -e "${GREEN}✓${NC} Process running (PID: $pid)"
    else
      echo -e "${YELLOW}⚠${NC} Process completed"
      # Try to get results
      local output_file="$RESULTS_DIR/${agent_id}.json"
      if [[ -f "$output_file" ]]; then
        echo -e "${BLUE}Results:${NC}"
        jq '.' "$output_file" 2>/dev/null || cat "$output_file"
      fi
    fi
  fi
}

# List all agents
list_agents() {
  log INFO "Listing all agents..."
  echo -e "\n${BLUE}=== Active Agents ===${NC}\n"

  for state_file in "$AGENTS_DIR"/*.json; do
    if [[ -f "$state_file" ]]; then
      local agent_id
      agent_id=$(basename "$state_file" .json)
      monitor_agent "$agent_id"
      echo ""
    fi
  done
}

# Wait for agent completion
wait_for_agent() {
  local agent_id=$1
  local timeout=${2:-300}  # 5 minutes default
  local pid_file="$AGENTS_DIR/${agent_id}.pid"

  if [[ ! -f "$pid_file" ]]; then
    log ERROR "Agent $agent_id PID file not found"
    return 1
  fi

  local pid
  pid=$(cat "$pid_file")

  log INFO "Waiting for agent $agent_id (PID: $pid, timeout: ${timeout}s)..."

  local elapsed=0
  while kill -0 "$pid" 2>/dev/null; do
    if [[ $elapsed -ge $timeout ]]; then
      log ERROR "Agent $agent_id timed out after ${timeout}s"
      update_agent_status "$agent_id" "timeout" "{\"timeout_seconds\": $timeout}"
      return 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))

    # Update progress every 10 seconds
    if [[ $((elapsed % 10)) -eq 0 ]]; then
      log INFO "Agent $agent_id still running (${elapsed}s elapsed)"
    fi
  done

  log INFO "Agent $agent_id completed"
  update_agent_status "$agent_id" "completed" "{\"elapsed_seconds\": $elapsed}"

  # Show results
  local output_file="$RESULTS_DIR/${agent_id}.json"
  if [[ -f "$output_file" ]]; then
    echo -e "\n${GREEN}=== Agent Results ===${NC}"
    jq '.' "$output_file" 2>/dev/null || cat "$output_file"
    return 0
  else
    log ERROR "No output file found for agent $agent_id"
    return 1
  fi
}

# Generate summary report
generate_report() {
  log INFO "Generating coordination report..."

  echo -e "\n${BLUE}=== Claude Coordinator Report ===${NC}"
  echo -e "${BLUE}Generated: ${NC}$(date)"
  echo ""

  local total_agents=0
  local completed=0
  local failed=0
  local running=0

  for state_file in "$AGENTS_DIR"/*.json; do
    if [[ -f "$state_file" ]]; then
      total_agents=$((total_agents + 1))
      local status
      status=$(jq -r '.status' "$state_file")

      case $status in
        completed|success) completed=$((completed + 1)) ;;
        failed|failure|timeout) failed=$((failed + 1)) ;;
        running|spawned) running=$((running + 1)) ;;
      esac
    fi
  done

  echo -e "${BLUE}Total Agents:${NC} $total_agents"
  echo -e "${GREEN}Completed:${NC}   $completed"
  echo -e "${YELLOW}Running:${NC}     $running"
  echo -e "${RED}Failed:${NC}       $failed"
  echo ""

  # Recent activity
  echo -e "${BLUE}=== Recent Activity ===${NC}"
  tail -20 "$LOGS_DIR/coordinator.log" 2>/dev/null || echo "No recent activity"
}

# Cleanup old agents
cleanup() {
  local older_than=${1:-3600}  # 1 hour default
  local cutoff_time
  cutoff_time=$(date -v-${older_than}s +%s 2>/dev/null || date -d "-${older_than} seconds" +%s)

  log INFO "Cleaning up agents older than ${older_than}s..."

  for state_file in "$AGENTS_DIR"/*.json; do
    if [[ -f "$state_file" ]]; then
      local spawned_at
      spawned_at=$(jq -r '.spawned_at' "$state_file" | tr -d '"')
      local spawned_timestamp
      spawned_timestamp=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$spawned_at" +%s 2>/dev/null || date -d "$spawned_at" +%s)

      if [[ $spawned_timestamp -lt $cutoff_time ]]; then
        local agent_id
        agent_id=$(basename "$state_file" .json)
        log INFO "Cleaning up old agent: $agent_id"

        # Kill process if running
        local pid_file="$AGENTS_DIR/${agent_id}.pid"
        if [[ -f "$pid_file" ]]; then
          local pid
          pid=$(cat "$pid_file")
          kill "$pid" 2>/dev/null || true
        fi

        # Remove files
        rm -f "$state_file" "$pid_file" "$RESULTS_DIR/${agent_id}.json"
      fi
    fi
  done
}

# Main command dispatcher
case "${1:-help}" in
  spawn)
    if [[ $# -lt 3 ]]; then
      echo "Usage: $0 spawn <agent_type> <task_title> <task_description>"
      echo ""
      echo "Available agent types: researcher, implementer, tester, planner"
      exit 1
    fi
    spawn_agent "$2" "$3" "${4:-}"
    ;;

  monitor)
    if [[ $# -lt 2 ]]; then
      echo "Usage: $0 monitor <agent_id>|--all"
      exit 1
    fi
    if [[ "$2" == "--all" ]]; then
      list_agents
    else
      monitor_agent "$2"
    fi
    ;;

  wait)
    if [[ $# -lt 2 ]]; then
      echo "Usage: $0 wait <agent_id> [timeout_seconds]"
      exit 1
    fi
    wait_for_agent "$2" "${3:-300}"
    ;;

  report)
    generate_report
    ;;

  cleanup)
    cleanup "${2:-3600}"
    ;;

  *)
    cat <<EOF
Claude Coordinator - Multi-Agent Orchestration System

Usage: $0 <command> [args]

Commands:
  spawn <agent_type> <task_title> [task_description]
      Spawn a new execution agent

  monitor <agent_id>|--all
      Monitor agent progress or list all agents

  wait <agent_id> [timeout]
      Wait for agent completion (default timeout: 300s)

  report
      Generate coordination summary report

  cleanup [seconds]
      Cleanup agents older than specified seconds (default: 3600)

Examples:
  # Spawn researcher to analyze code
  $0 spawn researcher "Analyze XP footer" "Analyze the XP footer component and suggest improvements"

  # Monitor all agents
  $0 monitor --all

  # Wait for specific agent
  $0 wait agent-1234567890-abc123

  # Generate report
  $0 report

Available Agent Types:
  - researcher: Explores and analyzes codebase
  - implementer: Implements features and fixes
  - tester: Tests and validates implementations
  - planner: Creates detailed implementation plans
EOF
    ;;
esac
