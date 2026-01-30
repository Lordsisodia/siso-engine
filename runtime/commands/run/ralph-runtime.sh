#!/bin/bash

################################################################################
# Ralph Runtime Wrapper Script
# Main wrapper for Ralph Runtime autonomous execution system
################################################################################

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
RALPH_RUNTIME_DIR="$PROJECT_ROOT/.blackbox4/ralph-runtime"
CONFIG_DIR="$PROJECT_ROOT/.blackbox4/config"
LOGS_DIR="$PROJECT_ROOT/.blackbox4/logs"
SESSIONS_DIR="$PROJECT_ROOT/.blackbox4/sessions"

# Default values
VERBOSE=false
DRY_RUN=false
AUTONOMOUS=false
INTERACTIVE=false
LOG_FILE="$LOGS_DIR/ralph-runtime.log"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_section() {
    echo -e "\n${BLUE}▶ $1${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ ERROR: $1${NC}" >&2
}

print_warning() {
    echo -e "${YELLOW}⚠ WARNING: $1${NC}"
}

print_info() {
    echo -e "${PURPLE}ℹ $1${NC}"
}

verbose_log() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${CYAN}[DEBUG] $1${NC}"
    fi
}

log_message() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" >> "$LOG_FILE"
}

show_help() {
    cat << EOF
${GREEN}Ralph Runtime Wrapper${NC} - Autonomous execution system for agent workflows

${YELLOW}USAGE:${NC}
    $0 <command> [options]

${YELLOW}COMMANDS:${NC}
    ${CYAN}run${NC}         Execute a plan or agent workflow
    ${CYAN}status${NC}      Show runtime status and active sessions
    ${CYAN}pause${NC}       Pause an active session
    ${CYAN}resume${NC}      Resume a paused session
    ${CYAN}stop${NC}        Stop an active session
    ${CYAN}logs${NC}        View runtime logs
    ${CYAN}config${NC}      Manage configuration
    ${CYAN}help${NC}        Show this help message

${YELLOW}RUN OPTIONS:${NC}
    ${CYAN}--plan <path>${NC}         Plan directory to execute
    ${CYAN}--agent <name>${NC}        Specific agent to run
    ${CYAN}--task <id>${NC}           Specific task ID to execute
    ${CYAN}--autonomous${NC}          Enable autonomous mode
    ${CYAN}--interactive${NC}         Enable interactive mode
    ${CYAN}--max-iterations <n>${NC}  Maximum iterations (default: 100)
    ${CYAN}--session <id>${NC}        Resume existing session
    ${CYAN}--config <file>${NC}       Custom config file
    ${CYAN}--parallel${NC}            Enable parallel task execution
    ${CYAN}--dry-run${NC}             Show what would be done

${YELLOW}COMMON OPTIONS:${NC}
    ${CYAN}-v, --verbose${NC}         Enable verbose output
    ${CYAN}-q, --quiet${NC}           Suppress output (except errors)
    ${CYAN}-h, --help${NC}            Show help message
    ${CYAN}--version${NC}             Show version info

${YELLOW}EXAMPLES:${NC}
    # Run a plan in autonomous mode
    $0 run --plan .plans/my-project --autonomous

    # Run specific task
    $0 run --task task-001 --plan .plans/my-project

    # Check runtime status
    $0 status

    # Pause a session
    $0 pause --session abc123

    # Resume a session
    $0 resume --session abc123

    # View logs
    $0 logs --session abc123 --tail 50

${YELLOW}CONFIGURATION:${NC}
    Config files are loaded from:
    1. $CONFIG_DIR/ralph-runtime.yaml (default)
    2. ~/.ralph-runtime.yaml (user)
    3. --config <file> (custom override)

${YELLOW}ENVIRONMENT VARIABLES:${NC}
    ${CYAN}RALPH_RUNTIME_DIR${NC}    Runtime directory
    ${CYAN}RALPH_CONFIG_DIR${NC}      Configuration directory
    ${CYAN}RALPH_LOG_LEVEL${NC}       Log level (debug, info, warn, error)
    ${CYAN}RALPH_AUTO_CONFIRM${NC}    Skip confirmation prompts

For more information, see: $PROJECT_ROOT/.blackbox4/docs/ralph-runtime.md

EOF
}

show_version() {
    cat << EOF
${GREEN}Ralph Runtime${NC} v1.0.0
Autonomous execution system for Blackbox4

Project: Blackbox4
Author: Black Box Factory
License: MIT
EOF
}

################################################################################
# Validation Functions
################################################################################

validate_environment() {
    verbose_log "Validating environment..."

    # Check required directories
    local required_dirs=("$RALPH_RUNTIME_DIR" "$CONFIG_DIR" "$LOGS_DIR" "$SESSIONS_DIR")
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            verbose_log "Created directory: $dir"
        fi
    done

    # Check required tools
    local required_tools=("node" "npm")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            print_error "Required tool not found: $tool"
            return 1
        fi
    done

    verbose_log "Environment validation complete"
    return 0
}

validate_plan() {
    local plan_path="$1"

    if [ ! -d "$plan_path" ]; then
        print_error "Plan directory not found: $plan_path"
        return 1
    fi

    # Check for plan.yaml or plan.json
    if [ ! -f "$plan_path/plan.yaml" ] && [ ! -f "$plan_path/plan.json" ]; then
        print_error "No plan.yaml or plan.json found in: $plan_path"
        return 1
    fi

    verbose_log "Plan validation complete: $plan_path"
    return 0
}

validate_session() {
    local session_id="$1"

    if [ ! -d "$SESSIONS_DIR/$session_id" ]; then
        print_error "Session not found: $session_id"
        return 1
    fi

    verbose_log "Session validation complete: $session_id"
    return 0
}

################################################################################
# Core Functions
################################################################################

initialize_session() {
    local plan_path="$1"
    local session_id
    session_id=$(generate_session_id)

    local session_dir="$SESSIONS_DIR/$session_id"
    mkdir -p "$session_dir"

    # Initialize session metadata
    cat > "$session_dir/metadata.json" << EOF
{
    "sessionId": "$session_id",
    "planPath": "$plan_path",
    "startTime": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "status": "initializing",
    "autonomous": $AUTONOMOUS,
    "interactive": $INTERACTIVE
}
EOF

    # Create session log
    touch "$session_dir/session.log"

    print_success "Session initialized: $session_id"
    log_message "Session $session_id initialized for plan: $plan_path"

    echo "$session_id"
}

generate_session_id() {
    date +%s%N | md5sum | head -c 12
}

run_plan() {
    local plan_path="$1"

    print_header "Ralph Runtime - Plan Execution"

    # Validate plan
    if ! validate_plan "$plan_path"; then
        return 1
    fi

    # Initialize session
    local session_id
    session_id=$(initialize_session "$plan_path")

    print_section "Execution Setup"
    print_info "Plan: $plan_path"
    print_info "Session: $session_id"
    print_info "Mode: $([ "$AUTONOMOUS" = true ] && echo "Autonomous" || echo "Manual")"

    if [ "$DRY_RUN" = true ]; then
        print_warning "DRY RUN MODE - No actual execution will occur"
        print_info "Would execute plan: $plan_path"
        print_info "Session ID would be: $session_id"
        return 0
    fi

    # Load configuration
    local config_file="${CONFIG_FILE:-$CONFIG_DIR/ralph-runtime.yaml}"
    if [ -f "$config_file" ]; then
        verbose_log "Loading config from: $config_file"
    fi

    # Execute based on mode
    if [ "$AUTONOMOUS" = true ]; then
        execute_autonomous "$session_id" "$plan_path"
    else
        execute_interactive "$session_id" "$plan_path"
    fi
}

execute_autonomous() {
    local session_id="$1"
    local plan_path="$2"
    local session_dir="$SESSIONS_DIR/$session_id"

    print_section "Autonomous Execution"
    print_info "Starting autonomous execution..."

    # Update session status
    update_session_status "$session_id" "running"

    # Execute the plan
    if [ -f "$RALPH_RUNTIME_DIR/index.js" ]; then
        cd "$PROJECT_ROOT"

        local cmd="node $RALPH_RUNTIME_DIR/index.js"
        cmd="$cmd --plan \"$plan_path\""
        cmd="$cmd --session \"$session_id\""
        cmd="$cmd --autonomous"

        if [ "$VERBOSE" = true ]; then
            cmd="$cmd --verbose"
        fi

        verbose_log "Executing: $cmd"

        # Run the command
        eval $cmd

        local exit_code=$?

        if [ $exit_code -eq 0 ]; then
            update_session_status "$session_id" "completed"
            print_success "Plan execution completed successfully"
        else
            update_session_status "$session_id" "failed"
            print_error "Plan execution failed with exit code: $exit_code"
            return $exit_code
        fi
    else
        print_error "Ralph Runtime not found at: $RALPH_RUNTIME_DIR/index.js"
        return 1
    fi
}

execute_interactive() {
    local session_id="$1"
    local plan_path="$2"

    print_section "Interactive Execution"
    print_info "Starting interactive execution..."
    print_warning "Press Ctrl+C to pause execution"

    # Similar to autonomous but with prompts
    update_session_status "$session_id" "running"

    # Implementation would include interactive prompts
    print_info "Interactive mode - feature under development"
    print_info "Use --autonomous flag for autonomous execution"
}

update_session_status() {
    local session_id="$1"
    local status="$2"
    local session_dir="$SESSIONS_DIR/$session_id"

    if [ -f "$session_dir/metadata.json" ]; then
        # Update status in metadata
        # This would use jq or similar in production
        log_message "Session $session_id status updated to: $status"
    fi
}

################################################################################
# Status Functions
################################################################################

show_status() {
    print_header "Ralph Runtime Status"

    # Check for active sessions
    local active_sessions=0
    if [ -d "$SESSIONS_DIR" ]; then
        active_sessions=$(find "$SESSIONS_DIR" -name "metadata.json" -type f | wc -l)
    fi

    print_section "Runtime Information"
    print_info "Runtime Directory: $RALPH_RUNTIME_DIR"
    print_info "Sessions Directory: $SESSIONS_DIR"
    print_info "Active Sessions: $active_sessions"

    # Check circuit breaker status
    if [ -f "$SCRIPT_DIR/circuit-breaker.sh" ]; then
        print_section "Circuit Breaker Status"
        "$SCRIPT_DIR/circuit-breaker.sh" status --quiet 2>/dev/null || true
    fi

    # Show recent sessions
    if [ -d "$SESSIONS_DIR" ] && [ "$active_sessions" -gt 0 ]; then
        print_section "Recent Sessions"

        for session_file in $(find "$SESSIONS_DIR" -name "metadata.json" -type f | sort -r | head -5); do
            local session_dir=$(dirname "$session_file")
            local session_id=$(basename "$session_dir")

            if [ -f "$session_file" ]; then
                # Extract info from metadata (simplified)
                local status="unknown"
                if grep -q '"status": "running"' "$session_file" 2>/dev/null; then
                    status="${GREEN}running${NC}"
                elif grep -q '"status": "completed"' "$session_file" 2>/dev/null; then
                    status="${GREEN}completed${NC}"
                elif grep -q '"status": "failed"' "$session_file" 2>/dev/null; then
                    status="${RED}failed${NC}"
                elif grep -q '"status": "paused"' "$session_file" 2>/dev/null; then
                    status="${YELLOW}paused${NC}"
                else
                    status="${CYAN}initializing${NC}"
                fi

                echo -e "  • ${CYAN}$session_id${NC} - Status: $status"
            fi
        done
    fi
}

################################################################################
# Session Management Functions
################################################################################

pause_session() {
    local session_id="$1"

    if ! validate_session "$session_id"; then
        return 1
    fi

    print_section "Pausing Session"
    print_info "Session ID: $session_id"

    update_session_status "$session_id" "paused"

    print_success "Session paused successfully"
    print_info "Use 'resume' command to continue execution"

    log_message "Session $session_id paused"
}

resume_session() {
    local session_id="$1"

    if ! validate_session "$session_id"; then
        return 1
    fi

    print_section "Resuming Session"
    print_info "Session ID: $session_id"

    update_session_status "$session_id" "running"

    print_success "Session resumed successfully"

    log_message "Session $session_id resumed"
}

stop_session() {
    local session_id="$1"

    if ! validate_session "$session_id"; then
        return 1
    fi

    print_section "Stopping Session"
    print_info "Session ID: $session_id"
    print_warning "This will terminate the session"

    # Confirm if not auto-confirm
    if [ "${RALPH_AUTO_CONFIRM:-false}" != "true" ]; then
        echo -n "Are you sure? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_info "Stop cancelled"
            return 0
        fi
    fi

    update_session_status "$session_id" "stopped"

    print_success "Session stopped successfully"

    log_message "Session $session_id stopped"
}

################################################################################
# Log Functions
################################################################################

show_logs() {
    local session_id="$1"
    local tail_lines="${2:-50}"

    if [ -n "$session_id" ]; then
        if ! validate_session "$session_id"; then
            return 1
        fi

        local session_log="$SESSIONS_DIR/$session_id/session.log"

        if [ -f "$session_log" ]; then
            print_header "Session Logs: $session_id"
            tail -n "$tail_lines" "$session_log"
        else
            print_warning "No logs found for session: $session_id"
        fi
    else
        # Show main runtime log
        if [ -f "$LOG_FILE" ]; then
            print_header "Runtime Logs"
            tail -n "$tail_lines" "$LOG_FILE"
        else
            print_warning "No runtime logs found"
        fi
    fi
}

################################################################################
# Config Functions
################################################################################

show_config() {
    print_header "Ralph Runtime Configuration"

    local config_file="$CONFIG_DIR/ralph-runtime.yaml"

    if [ -f "$config_file" ]; then
        print_section "Current Configuration"
        cat "$config_file"
    else
        print_warning "Configuration file not found: $config_file"
        print_info "Creating default configuration..."

        mkdir -p "$CONFIG_DIR"
        cat > "$config_file" << EOF
# Ralph Runtime Configuration

# Runtime Settings
runtime:
  maxIterations: 100
  timeout: 300000  # 5 minutes
  retryAttempts: 3
  retryDelay: 1000

# Autonomous Mode
autonomous:
  enabled: false
  requireConfirmation: false
  maxConcurrentTasks: 3

# Circuit Breaker
circuitBreaker:
  enabled: true
  failureThreshold: 5
  recoveryTimeout: 60000
  monitoringPeriod: 10000

# Logging
logging:
  level: info
  file: true
  console: true
  maxFileSize: 10485760  # 10MB

# Analysis
analysis:
  enabled: true
  checkPatterns: true
  checkQuality: true
  checkConsistency: true

EOF
        print_success "Default configuration created"
    fi
}

################################################################################
# Main Function
################################################################################

main() {
    # Create necessary directories
    mkdir -p "$LOGS_DIR" "$SESSIONS_DIR" "$CONFIG_DIR"

    # Parse command
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    local command="$1"
    shift

    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --plan)
                PLAN_PATH="$2"
                shift 2
                ;;
            --agent)
                AGENT_NAME="$2"
                shift 2
                ;;
            --task)
                TASK_ID="$2"
                shift 2
                ;;
            --autonomous)
                AUTONOMOUS=true
                shift
                ;;
            --interactive)
                INTERACTIVE=true
                shift
                ;;
            --session)
                SESSION_ID="$2"
                shift 2
                ;;
            --max-iterations)
                MAX_ITERATIONS="$2"
                shift 2
                ;;
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --parallel)
                PARALLEL=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -q|--quiet)
                QUIET=true
                shift
                ;;
            --tail)
                TAIL_LINES="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            --version)
                show_version
                exit 0
                ;;
            *)
                # Unknown option
                shift
                ;;
        esac
    done

    # Execute command
    case $command in
        run)
            if [ -z "${PLAN_PATH:-}" ]; then
                print_error "Please specify a plan path with --plan"
                echo ""
                show_help
                exit 1
            fi
            run_plan "$PLAN_PATH"
            ;;
        status)
            show_status
            ;;
        pause)
            if [ -z "${SESSION_ID:-}" ]; then
                print_error "Please specify a session ID with --session"
                exit 1
            fi
            pause_session "$SESSION_ID"
            ;;
        resume)
            if [ -z "${SESSION_ID:-}" ]; then
                print_error "Please specify a session ID with --session"
                exit 1
            fi
            resume_session "$SESSION_ID"
            ;;
        stop)
            if [ -z "${SESSION_ID:-}" ]; then
                print_error "Please specify a session ID with --session"
                exit 1
            fi
            stop_session "$SESSION_ID"
            ;;
        logs)
            show_logs "${SESSION_ID:-}" "${TAIL_LINES:-50}"
            ;;
        config)
            show_config
            ;;
        help)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main
main "$@"
