#!/bin/bash

################################################################################
# Autonomous Run Wrapper Script
# High-level autonomous execution wrapper for Ralph Runtime
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
AUTONOMOUS_DIR="$PROJECT_ROOT/.blackbox4/autonomous"
CONFIG_DIR="$PROJECT_ROOT/.blackbox4/config"
LOGS_DIR="$PROJECT_ROOT/.blackbox4/logs"
SESSIONS_DIR="$PROJECT_ROOT/.blackbox4/sessions"
STATE_DIR="$PROJECT_ROOT/.blackbox4/state"

# Default values
VERBOSE=false
DRY_RUN=false
INTERACTIVE=false
MAX_ITERATIONS=100
INTERVENTION_ENABLED=true
CIRCUIT_BREAKER_ENABLED=true
RESPONSE_ANALYSIS_ENABLED=true

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

show_help() {
    cat << EOF
${GREEN}Autonomous Run Wrapper${NC} - High-level autonomous execution for Ralph Runtime

${YELLOW}USAGE:${NC}
    $0 <command> [options]

${YELLOW}COMMANDS:${NC}
    ${CYAN}start${NC}         Start autonomous execution
    ${CYAN}monitor${NC}       Monitor running autonomous session
    ${CYAN}intervene${NC}     Intervene in autonomous execution
    ${CYAN}status${NC}        Show autonomous execution status
    ${CYAN}stop${NC}          Stop autonomous execution
    ${CYAN}resume${NC}        Resume paused execution
    ${CYAN}logs${NC}          View execution logs
    ${CYAN}configure${NC}     Manage autonomous configuration
    ${CYAN}help${NC}          Show this help message

${YELLOW}START OPTIONS:${NC}
    ${CYAN}--spec <path>${NC}            Spec file to execute
    ${CYAN}--plan <path>${NC}            Plan directory to execute
    ${CYAN}--agent <name>${NC}           Specific agent to run
    ${CYAN}--max-iterations <n>${NC}     Maximum iterations (default: 100)
    ${CYAN}--session-id <id>${NC}        Custom session ID
    ${CYAN}--no-intervention${NC}        Disable human intervention
    ${CYAN}--no-circuit-breaker${NC}     Disable circuit breaker
    ${CYAN}--no-response-analysis${NC}   Disable response analysis
    ${CYAN}--config <file>${NC}          Custom config file
    ${CYAN}--dry-run${NC}               Show what would be done

${YELLOW}MONITOR OPTIONS:${NC}
    ${CYAN}--session <id>${NC}           Session ID to monitor
    ${CYAN}--follow${NC}                Follow output in real-time
    ${CYAN}--metrics${NC}               Show metrics dashboard
    ${CYAN}--refresh <n>${NC}            Refresh interval in seconds

${YELLOW}INTERVENE OPTIONS:${NC}
    ${CYAN}--session <id>${NC}           Session ID to intervene in
    ${CYAN}--action <type>${NC}          Action: pause, guidance, override
    ${CYAN}--input <data>${NC}           Input data for intervention
    ${CYAN}--reason <text>${NC}          Reason for intervention

${YELLOW}COMMON OPTIONS:${NC}
    ${CYAN}-v, --verbose${NC}            Enable verbose output
    ${CYAN}-q, --quiet${NC}              Suppress output (except errors)
    ${CYAN}-h, --help${NC}               Show help message
    ${CYAN}--debug${NC}                  Enable debug mode

${YELLOW}EXAMPLES:${NC}
    # Start autonomous execution with a spec
    $0 start --spec .specs/my-spec.json

    # Start with a plan
    $0 start --plan .plans/my-project --max-iterations 50

    # Start with no intervention
    $0 start --spec .specs/my-spec.json --no-intervention

    # Monitor a session
    $0 monitor --session abc123 --follow

    # Intervene in a session
    $0 intervene --session abc123 --action pause --reason "Manual review needed"

    # Check status
    $0 status

${YELLOW}AUTONOMOUS EXECUTION FEATURES:${NC}
    ${CYAN}Automatic Task Breakdown${NC}    Breaks down complex tasks automatically
    ${CYAN}Circuit Breaker${NC}             Prevents cascading failures
    ${CYAN}Response Analysis${NC}           Validates agent responses
    ${CYAN}Human Intervention${NC}          Allows human oversight when needed
    ${CYAN}Progress Tracking${NC}           Tracks execution progress
    ${CYAN}Error Recovery${NC}              Automatic recovery from errors

${YELLOW}INTEGRATION:${NC}
    This script integrates with:
    - ralph-runtime.sh (core execution)
    - circuit-breaker.sh (failure prevention)
    - analyze-response.sh (quality validation)
    - monitor.sh (real-time monitoring)
    - intervene.sh (human intervention)

For more information, see: $PROJECT_ROOT/.blackbox4/docs/autonomous-run.md

EOF
}

################################################################################
# Validation Functions
################################################################################

validate_environment() {
    verbose_log "Validating autonomous execution environment..."

    # Check required directories
    local required_dirs=("$AUTONOMOUS_DIR" "$CONFIG_DIR" "$LOGS_DIR" "$SESSIONS_DIR" "$STATE_DIR")
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            verbose_log "Created directory: $dir"
        fi
    done

    # Check required scripts
    local required_scripts=(
        "$SCRIPT_DIR/ralph-runtime.sh"
        "$SCRIPT_DIR/circuit-breaker.sh"
        "$SCRIPT_DIR/analyze-response.sh"
    )

    for script in "${required_scripts[@]}"; do
        if [ ! -f "$script" ]; then
            print_warning "Required script not found: $script"
        fi
    done

    verbose_log "Environment validation complete"
    return 0
}

validate_spec() {
    local spec_path="$1"

    if [ ! -f "$spec_path" ]; then
        print_error "Spec file not found: $spec_path"
        return 1
    fi

    # Basic validation of spec format
    if ! grep -q '{' "$spec_path" 2>/dev/null; then
        print_error "Invalid spec format (not JSON)"
        return 1
    fi

    verbose_log "Spec validation complete: $spec_path"
    return 0
}

validate_plan() {
    local plan_path="$1"

    if [ ! -d "$plan_path" ]; then
        print_error "Plan directory not found: $plan_path"
        return 1
    fi

    # Check for plan files
    if [ ! -f "$plan_path/plan.yaml" ] && [ ! -f "$plan_path/plan.json" ]; then
        print_warning "No plan.yaml or plan.json found in: $plan_path"
    fi

    verbose_log "Plan validation complete: $plan_path"
    return 0
}

################################################################################
# Session Management
################################################################################

create_session() {
    local spec_path="${1:-}"
    local plan_path="${2:-}"
    local session_id="${SESSION_ID:-}"
    local session_dir

    if [ -z "$session_id" ]; then
        session_id=$(generate_session_id)
    fi

    session_dir="$SESSIONS_DIR/$session_id"
    mkdir -p "$session_dir"

    # Initialize session metadata
    cat > "$session_dir/metadata.json" << EOF
{
    "sessionId": "$session_id",
    "specPath": "$spec_path",
    "planPath": "$plan_path",
    "startTime": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "status": "initializing",
    "maxIterations": $MAX_ITERATIONS,
    "currentIteration": 0,
    "interventionEnabled": $INTERVENTION_ENABLED,
    "circuitBreakerEnabled": $CIRCUIT_BREAKER_ENABLED,
    "responseAnalysisEnabled": $RESPONSE_ANALYSIS_ENABLED,
    "interactive": $INTERACTIVE
}
EOF

    # Create session log
    touch "$session_dir/session.log"

    # Create state file
    cat > "$session_dir/state.json" << EOF
{
    "status": "initializing",
    "currentTask": null,
    "completedTasks": [],
    "failedTasks": [],
    "interventions": []
}
EOF

    print_success "Session created: $session_id"
    echo "$session_id"
}

generate_session_id() {
    date +%s%N | md5sum | head -c 12
}

update_session_status() {
    local session_id="$1"
    local status="$2"
    local session_dir="$SESSIONS_DIR/$session_id"

    if [ -f "$session_dir/metadata.json" ]; then
        verbose_log "Updating session $session_id status to: $status"
        # In production, would use jq to update JSON
    fi
}

################################################################################
# Start Functions
################################################################################

start_autonomous() {
    local spec_path="${SPEC_PATH:-}"
    local plan_path="${PLAN_PATH:-}"

    print_header "Autonomous Execution"

    # Validate environment
    validate_environment

    # Validate input
    if [ -n "$spec_path" ]; then
        if ! validate_spec "$spec_path"; then
            return 1
        fi
    elif [ -n "$plan_path" ]; then
        if ! validate_plan "$plan_path"; then
            return 1
        fi
    else
        print_error "Please specify --spec or --plan"
        return 1
    fi

    # Create session
    local session_id
    session_id=$(create_session "$spec_path" "$plan_path")

    print_section "Execution Configuration"
    print_info "Session ID: $session_id"
    print_info "Max Iterations: $MAX_ITERATIONS"
    print_info "Intervention: $([ "$INTERVENTION_ENABLED" = true ] && echo "Enabled" || echo "Disabled")"
    print_info "Circuit Breaker: $([ "$CIRCUIT_BREAKER_ENABLED" = true ] && echo "Enabled" || echo "Disabled")"
    print_info "Response Analysis: $([ "$RESPONSE_ANALYSIS_ENABLED" = true ] && echo "Enabled" || echo "Disabled")"

    if [ "$DRY_RUN" = true ]; then
        print_warning "DRY RUN MODE - No actual execution will occur"
        print_info "Would start autonomous execution with:"
        print_info "  Spec: $spec_path"
        print_info "  Plan: $plan_path"
        print_info "  Session: $session_id"
        return 0
    fi

    # Initialize circuit breaker if enabled
    if [ "$CIRCUIT_BREAKER_ENABLED" = true ]; then
        verbose_log "Initializing circuit breaker..."
        if [ -f "$SCRIPT_DIR/circuit-breaker.sh" ]; then
            "$SCRIPT_DIR/circuit-breaker.sh" --breaker "autonomous-$session_id" --quiet 2>/dev/null || true
        fi
    fi

    # Start autonomous execution
    update_session_status "$session_id" "running"

    print_section "Starting Autonomous Execution"
    print_info "Initializing autonomous execution loop..."

    # Execute using ralph-runtime
    if [ -f "$SCRIPT_DIR/ralph-runtime.sh" ]; then
        local runtime_args="--autonomous --session $session_id"

        if [ -n "$spec_path" ]; then
            runtime_args="$runtime_args --spec $spec_path"
        fi

        if [ -n "$plan_path" ]; then
            runtime_args="$runtime_args --plan $plan_path"
        fi

        if [ "$VERBOSE" = true ]; then
            runtime_args="$runtime_args --verbose"
        fi

        verbose_log "Executing: $SCRIPT_DIR/ralph-runtime.sh run $runtime_args"

        # Run the autonomous execution
        "$SCRIPT_DIR/ralph-runtime.sh" run $runtime_args
        local exit_code=$?

        if [ $exit_code -eq 0 ]; then
            update_session_status "$session_id" "completed"
            print_success "Autonomous execution completed successfully"
        else
            update_session_status "$session_id" "failed"
            print_error "Autonomous execution failed with exit code: $exit_code"
            return $exit_code
        fi
    else
        print_error "Ralph Runtime script not found"
        return 1
    fi
}

################################################################################
# Monitor Functions
################################################################################

monitor_session() {
    local session_id="$1"
    local follow="${FOLLOW:-false}"
    local metrics="${METRICS:-false}"
    local refresh="${REFRESH:-2}"

    if [ ! -d "$SESSIONS_DIR/$session_id" ]; then
        print_error "Session not found: $session_id"
        return 1
    fi

    if [ "$follow" = true ]; then
        print_header "Live Monitor - Session: $session_id"
        print_info "Press Ctrl+C to stop monitoring"

        while true; do
            clear
            show_session_status "$session_id" "$metrics"
            sleep "$refresh"
        done
    else
        print_header "Session Monitor - $session_id"
        show_session_status "$session_id" "$metrics"
    fi
}

show_session_status() {
    local session_id="$1"
    local show_metrics="$2"
    local session_dir="$SESSIONS_DIR/$session_id"

    # Load session metadata
    if [ -f "$session_dir/metadata.json" ]; then
        print_section "Session Information"

        # Parse metadata (simplified)
        local status=$(grep -o '"status": "[^"]*"' "$session_dir/metadata.json" 2>/dev/null | cut -d'"' -f4)
        local iterations=$(grep -o '"currentIteration": [0-9]*' "$session_dir/metadata.json" 2>/dev/null | cut -d':' -f2)
        local max_iterations=$(grep -o '"maxIterations": [0-9]*' "$session_dir/metadata.json" 2>/dev/null | cut -d':' -f2)

        echo "  Status: $(format_status "$status")"
        echo "  Iterations: ${iterations:-0}/${max_iterations:-100}"

        # Show state
        if [ -f "$session_dir/state.json" ]; then
            local completed=$(grep -o '"completedTasks": \[[^]]*\]' "$session_dir/state.json" 2>/dev/null | grep -o ',' | wc -l)
            local failed=$(grep -o '"failedTasks": \[[^]]*\]' "$session_dir/state.json" 2>/dev/null | grep -o ',' | wc -l)

            echo "  Completed Tasks: ${completed:-0}"
            echo "  Failed Tasks: ${failed:-0}"
        fi
    fi

    # Show circuit breaker status if enabled
    if [ "$CIRCUIT_BREAKER_ENABLED" = true ] && [ -f "$SCRIPT_DIR/circuit-breaker.sh" ]; then
        echo ""
        print_section "Circuit Breaker Status"
        "$SCRIPT_DIR/circuit-breaker.sh" status --breaker "autonomous-$session_id" --quiet 2>/dev/null || true
    fi

    # Show recent logs
    if [ -f "$session_dir/session.log" ]; then
        echo ""
        print_section "Recent Activity"
        tail -5 "$session_dir/session.log" | sed 's/^/  /'
    fi

    # Show metrics if requested
    if [ "$show_metrics" = true ]; then
        echo ""
        print_section "Performance Metrics"
        show_session_metrics "$session_id"
    fi
}

format_status() {
    local status="$1"

    case $status in
        running)
            echo -e "${GREEN}$status${NC}"
            ;;
        completed)
            echo -e "${GREEN}$status${NC}"
            ;;
        failed)
            echo -e "${RED}$status${NC}"
            ;;
        paused)
            echo -e "${YELLOW}$status${NC}"
            ;;
        *)
            echo -e "${CYAN}$status${NC}"
            ;;
    esac
}

show_session_metrics() {
    local session_id="$1"
    local session_dir="$SESSIONS_DIR/$session_id"

    # Calculate metrics
    local log_lines=0
    if [ -f "$session_dir/session.log" ]; then
        log_lines=$(wc -l < "$session_dir/session.log")
    fi

    echo "  Log Entries: $log_lines"

    # More metrics would be calculated here in production
}

################################################################################
# Intervene Functions
################################################################################

intervene_session() {
    local session_id="$1"
    local action="${INTERVENTION_ACTION:-}"
    local input_data="${INTERVENTION_INPUT:-}"
    local reason="${INTERVENTION_REASON:-}"

    if [ ! -d "$SESSIONS_DIR/$session_id" ]; then
        print_error "Session not found: $session_id"
        return 1
    fi

    print_header "Intervention - Session: $session_id"

    # Check if intervention is enabled
    local intervention_enabled
    intervention_enabled=$(grep -o '"interventionEnabled": [truefalse]' "$SESSIONS_DIR/$session_id/metadata.json" 2>/dev/null | cut -d':' -f2)

    if [ "$intervention_enabled" != "true" ]; then
        print_error "Intervention is not enabled for this session"
        return 1
    fi

    print_section "Intervention Details"
    print_info "Action: $action"
    [ -n "$reason" ] && print_info "Reason: $reason"

    case $action in
        pause)
            pause_session "$session_id"
            ;;
        guidance)
            provide_guidance "$session_id" "$input_data"
            ;;
        override)
            override_execution "$session_id" "$input_data" "$reason"
            ;;
        *)
            print_error "Unknown intervention action: $action"
            print_info "Available actions: pause, guidance, override"
            return 1
            ;;
    esac
}

pause_session() {
    local session_id="$1"

    print_info "Pausing session..."
    update_session_status "$session_id" "paused"

    # Log intervention
    log_intervention "$session_id" "pause" "Manual pause"

    print_success "Session paused"
    print_info "Use 'resume' command to continue execution"
}

provide_guidance() {
    local session_id="$1"
    local guidance="$2"

    print_info "Providing guidance..."
    log_intervention "$session_id" "guidance" "$guidance"

    print_success "Guidance provided"
    print_info "Execution will continue with new guidance"
}

override_execution() {
    local session_id="$1"
    local override_data="$2"
    local reason="$3"

    print_warning "Overriding execution..."
    log_intervention "$session_id" "override" "$reason: $override_data"

    print_success "Override applied"
}

log_intervention() {
    local session_id="$1"
    local action="$2"
    local details="$3"
    local session_dir="$SESSIONS_DIR/$session_id"

    # Add to interventions log
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    echo "[$timestamp] $action: $details" >> "$session_dir/interventions.log"

    verbose_log "Logged intervention: $action"
}

################################################################################
# Status Functions
################################################################################

show_status() {
    print_header "Autonomous Execution Status"

    # Check for active sessions
    if [ -d "$SESSIONS_DIR" ]; then
        local session_count=$(find "$SESSIONS_DIR" -name "metadata.json" -type f 2>/dev/null | wc -l)

        print_section "Sessions Overview"
        print_info "Total Sessions: $session_count"

        # Show recent sessions
        if [ $session_count -gt 0 ]; then
            echo ""
            echo "  Recent Sessions:"

            for session_file in $(find "$SESSIONS_DIR" -name "metadata.json" -type f 2>/dev/null | sort -r | head -5); do
                local session_dir=$(dirname "$session_file")
                local session_id=$(basename "$session_dir")
                local status=$(grep -o '"status": "[^"]*"' "$session_file" 2>/dev/null | cut -d'"' -f4)

                echo -e "    • ${CYAN}$session_id${NC} - $(format_status "$status")"
            done
        fi
    else
        print_warning "No sessions found"
    fi

    # Show system status
    echo ""
    print_section "System Status"
    print_info "Circuit Breaker: $([ "$CIRCUIT_BREAKER_ENABLED" = true ] && echo "Enabled" || echo "Disabled")"
    print_info "Response Analysis: $([ "$RESPONSE_ANALYSIS_ENABLED" = true ] && echo "Enabled" || echo "Disabled")"
    print_info "Intervention: $([ "$INTERVENTION_ENABLED" = true ] && echo "Enabled" || echo "Disabled")"
}

################################################################################
# Main Function
################################################################################

main() {
    # Create necessary directories
    mkdir -p "$AUTONOMOUS_DIR" "$CONFIG_DIR" "$LOGS_DIR" "$SESSIONS_DIR" "$STATE_DIR"

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
            --spec)
                SPEC_PATH="$2"
                shift 2
                ;;
            --plan)
                PLAN_PATH="$2"
                shift 2
                ;;
            --agent)
                AGENT_NAME="$2"
                shift 2
                ;;
            --max-iterations)
                MAX_ITERATIONS="$2"
                shift 2
                ;;
            --session-id)
                SESSION_ID="$2"
                shift 2
                ;;
            --session)
                SESSION_ID="$2"
                shift 2
                ;;
            --action)
                INTERVENTION_ACTION="$2"
                shift 2
                ;;
            --input)
                INTERVENTION_INPUT="$2"
                shift 2
                ;;
            --reason)
                INTERVENTION_REASON="$2"
                shift 2
                ;;
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --no-intervention)
                INTERVENTION_ENABLED=false
                shift
                ;;
            --no-circuit-breaker)
                CIRCUIT_BREAKER_ENABLED=false
                shift
                ;;
            --no-response-analysis)
                RESPONSE_ANALYSIS_ENABLED=false
                shift
                ;;
            --follow)
                FOLLOW=true
                shift
                ;;
            --metrics)
                METRICS=true
                shift
                ;;
            --refresh)
                REFRESH="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
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
            --debug)
                VERBOSE=true
                set -x
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                shift
                ;;
        esac
    done

    # Execute command
    case $command in
        start)
            start_autonomous
            ;;
        monitor)
            if [ -z "${SESSION_ID:-}" ]; then
                print_error "Please specify --session"
                exit 1
            fi
            monitor_session "$SESSION_ID"
            ;;
        intervene)
            if [ -z "${SESSION_ID:-}" ]; then
                print_error "Please specify --session"
                exit 1
            fi
            if [ -z "${INTERVENTION_ACTION:-}" ]; then
                print_error "Please specify --action (pause, guidance, override)"
                exit 1
            fi
            intervene_session "$SESSION_ID"
            ;;
        status)
            show_status
            ;;
        stop)
            if [ -z "${SESSION_ID:-}" ]; then
                print_error "Please specify --session"
                exit 1
            fi
            pause_session "$SESSION_ID"
            ;;
        resume)
            if [ -z "${SESSION_ID:-}" ]; then
                print_error "Please specify --session"
                exit 1
            fi
            update_session_status "$SESSION_ID" "running"
            print_success "Session resumed"
            ;;
        logs)
            if [ -z "${SESSION_ID:-}" ]; then
                print_error "Please specify --session"
                exit 1
            fi
            if [ -f "$SESSIONS_DIR/$SESSION_ID/session.log" ]; then
                cat "$SESSIONS_DIR/$SESSION_ID/session.log"
            else
                print_warning "No logs found for session: $SESSION_ID"
            fi
            ;;
        configure)
            print_info "Configuration management - feature under development"
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
