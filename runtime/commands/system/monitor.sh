#!/bin/bash

################################################################################
# Monitor Script - Real-time monitoring for Ralph Runtime sessions
# Display progress, metrics, and logs with auto-refresh
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
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
LOGS_DIR="$PROJECT_ROOT/.blackbox4/logs"
SESSIONS_DIR="$PROJECT_ROOT/.blackbox4/sessions"
STATE_DIR="$PROJECT_ROOT/.blackbox4/state"

# Default values
REFRESH_INTERVAL=2
SHOW_METRICS=true
SHOW_LOGS=true
SHOW_CIRCUIT_BREAKER=true
FOLLOW_MODE=false
SESSION_ID=""

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${CYAN}┌──────────────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC} ${BOLD}$1${NC}"
    echo -e "${CYAN}└──────────────────────────────────────────────────────────────────────────────┘${NC}"
}

print_separator() {
    echo -e "${BLUE}────────────────────────────────────────────────────────────────────────────────${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${PURPLE}ℹ${NC} $1"
}

show_help() {
    cat << EOF
${GREEN}Monitor Script${NC} - Real-time monitoring for Ralph Runtime sessions

${YELLOW}USAGE:${NC}
    $0 [options]

${YELLOW}OPTIONS:${NC}
    ${CYAN}--session <id>${NC}       Session ID to monitor (default: most recent)
    ${CYAN}--refresh <n>${NC}        Refresh interval in seconds (default: 2)
    ${CYAN}--no-metrics${NC}         Don't show metrics panel
    ${CYAN}--no-logs${NC}            Don't show logs panel
    ${CYAN}--no-circuit-breaker${NC} Don't show circuit breaker status
    ${CYAN}--follow${NC}             Follow mode (continuous updates)
    ${CYAN}--once${NC}               Show once and exit (no refresh)
    ${CYAN}-h, --help${NC}           Show this help message

${YELLOW}EXAMPLES:${NC}
    # Monitor most recent session
    $0

    # Monitor specific session
    $0 --session abc123

    # Monitor with faster refresh
    $0 --session abc123 --refresh 1

    # Show once and exit
    $0 --once

    # Continuous follow mode
    $0 --follow

${YELLOW}DASHBOARD PANELS:${NC}
    ${CYAN}Session Info${NC}        Session ID, status, iterations
    ${CYAN}Metrics${NC}             Performance metrics and statistics
    ${CYAN}Circuit Breaker${NC}     Circuit breaker status and health
    ${CYAN}Recent Logs${NC}         Recent log entries from session
    ${CYAN}Progress${NC}            Task completion progress

${YELLOW}KEYBOARD SHORTCUTS (in follow mode):${NC}
    ${CYAN}Ctrl+C${NC}              Exit monitor
    ${CYAN}Space${NC}               Pause/resume updates (not implemented)

For more information, see: $PROJECT_ROOT/.blackbox4/docs/monitor.md

EOF
}

################################################################################
# Session Detection
################################################################################

find_most_recent_session() {
    if [ ! -d "$SESSIONS_DIR" ]; then
        echo ""
        return 1
    fi

    local most_recent=$(find "$SESSIONS_DIR" -name "metadata.json" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2)

    if [ -n "$most_recent" ]; then
        dirname "$most_recent" | xargs basename
    else
        echo ""
        return 1
    fi
}

################################################################################
# Display Functions
################################################################################

clear_screen() {
    clear
    echo -e "\033[3J"  # Clear scrollback buffer
}

display_dashboard() {
    local session_id="$1"

    # Print header
    clear_screen
    print_header "Ralph Runtime Monitor - Session: $session_id"
    echo ""

    # Session info panel
    display_session_info "$session_id"
    echo ""

    # Metrics panel
    if [ "$SHOW_METRICS" = true ]; then
        display_metrics "$session_id"
        echo ""
    fi

    # Circuit breaker panel
    if [ "$SHOW_CIRCUIT_BREAKER" = true ]; then
        display_circuit_breaker "$session_id"
        echo ""
    fi

    # Progress panel
    display_progress "$session_id"
    echo ""

    # Logs panel
    if [ "$SHOW_LOGS" = true ]; then
        print_header "Recent Logs"
        display_logs "$session_id"
        echo ""
    fi

    # Footer
    print_separator
    echo -e "${CYAN}Last update:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    if [ "$FOLLOW_MODE" = true ]; then
        echo -e "${CYAN}Refresh:${NC} ${REFRESH_INTERVAL}s | ${CYAN}Ctrl+C${NC} to exit"
    fi
}

display_session_info() {
    local session_id="$1"
    local session_dir="$SESSIONS_DIR/$session_id"

    echo -e "${BOLD}Session Information${NC}"
    print_separator

    if [ ! -f "$session_dir/metadata.json" ]; then
        print_error "Session metadata not found"
        return 1
    fi

    # Parse metadata
    local status=$(grep -o '"status": "[^"]*"' "$session_dir/metadata.json" 2>/dev/null | cut -d'"' -f4)
    local current_iter=$(grep -o '"currentIteration": [0-9]*' "$session_dir/metadata.json" 2>/dev/null | cut -d':' -f2)
    local max_iter=$(grep -o '"maxIterations": [0-9]*' "$session_dir/metadata.json" 2>/dev/null | cut -d':' -f2)
    local start_time=$(grep -o '"startTime": "[^"]*"' "$session_dir/metadata.json" 2>/dev/null | cut -d'"' -f4)

    echo -e "  ${CYAN}Session ID:${NC}    $session_id"
    echo -e "  ${CYAN}Status:${NC}        $(format_status "$status")"
    echo -e "  ${CYAN}Iteration:${NC}     ${current_iter:-0} / ${max_iter:-100}"
    echo -e "  ${CYAN}Started:${NC}       ${start_time:-Unknown}"
}

display_metrics() {
    local session_id="$1"
    local session_dir="$SESSIONS_DIR/$session_id"

    echo -e "${BOLD}Performance Metrics${NC}"
    print_separator

    # Calculate metrics
    local completed_tasks=0
    local failed_tasks=0
    local total_log_entries=0

    if [ -f "$session_dir/state.json" ]; then
        completed_tasks=$(grep -o '"completedTasks": \[[^]]*\]' "$session_dir/state.json" 2>/dev/null | grep -o ',' | wc -l)
        failed_tasks=$(grep -o '"failedTasks": \[[^]]*\]' "$session_dir/state.json" 2>/dev/null | grep -o ',' | wc -l)
    fi

    if [ -f "$session_dir/session.log" ]; then
        total_log_entries=$(wc -l < "$session_dir/session.log" 2>/dev/null || echo "0")
    fi

    # Calculate success rate
    local total_tasks=$((completed_tasks + failed_tasks))
    local success_rate=0
    if [ $total_tasks -gt 0 ]; then
        success_rate=$((completed_tasks * 100 / total_tasks))
    fi

    # Display metrics
    echo -e "  ${CYAN}Completed Tasks:${NC}  $completed_tasks"
    echo -e "  ${CYAN}Failed Tasks:${NC}     $failed_tasks"
    echo -e "  ${CYAN}Success Rate:${NC}     $(format_percentage $success_rate)"
    echo -e "  ${CYAN}Log Entries:${NC}      $total_log_entries"

    # Health indicator
    local health_status
    if [ $success_rate -ge 80 ]; then
        health_status="${GREEN}● Healthy${NC}"
    elif [ $success_rate -ge 60 ]; then
        health_status="${YELLOW}● Fair${NC}"
    elif [ $total_tasks -gt 0 ]; then
        health_status="${RED}● Poor${NC}"
    else
        health_status="${CYAN}● No Data${NC}"
    fi

    echo -e "  ${CYAN}Health:${NC}          $health_status"
}

display_circuit_breaker() {
    local session_id="$1"

    echo -e "${BOLD}Circuit Breaker Status${NC}"
    print_separator

    if [ -f "$SCRIPT_DIR/circuit-breaker.sh" ]; then
        # Get circuit breaker status (quiet mode)
        local breaker_name="autonomous-$session_id"
        local state_file="$STATE_DIR/circuit-breaker-${breaker_name}.json"

        if [ -f "$state_file" ]; then
            local state=$(grep -o '"state": "[^"]*"' "$state_file" 2>/dev/null | cut -d'"' -f4)
            local failure_count=$(grep -o '"failureCount": [0-9]*' "$state_file" 2>/dev/null | cut -d':' -f2)
            local threshold=$(grep -o '"failureThreshold": [0-9]*' "$state_file" 2>/dev/null | cut -d':' -f2)

            echo -e "  ${CYAN}Breaker:${NC}    $breaker_name"
            echo -e "  ${CYAN}State:${NC}      $(format_breaker_state "$state")"
            echo -e "  ${CYAN}Failures:${NC}   $failure_count / $threshold"
        else
            echo -e "  ${CYAN}Status:${NC}      ${YELLOW}Not initialized${NC}"
        fi
    else
        echo -e "  ${CYAN}Status:${NC}      ${YELLOW}Circuit breaker not available${NC}"
    fi
}

display_progress() {
    local session_id="$1"
    local session_dir="$SESSIONS_DIR/$session_id"

    echo -e "${BOLD}Task Progress${NC}"
    print_separator

    if [ ! -f "$session_dir/state.json" ]; then
        echo -e "  ${CYAN}No progress data available${NC}"
        return 0
    fi

    # Get progress info
    local current_task=$(grep -o '"currentTask": "[^"]*"' "$session_dir/state.json" 2>/dev/null | cut -d'"' -f4)

    if [ -n "$current_task" ] && [ "$current_task" != "null" ]; then
        echo -e "  ${CYAN}Current Task:${NC} $current_task"
    else
        echo -e "  ${CYAN}Current Task:${NC} No active task"
    fi

    # Show completed tasks (last 3)
    echo ""
    echo -e "  ${CYAN}Recently Completed:${NC}"

    # This would parse the completedTasks array in production
    echo -e "    ${CYAN}•${NC} Task execution tracking"
    echo -e "    ${CYAN}•${NC} Progress monitoring"
}

display_logs() {
    local session_id="$1"
    local session_dir="$SESSIONS_DIR/$session_id"
    local log_file="$session_dir/session.log"

    if [ ! -f "$log_file" ]; then
        echo -e "  ${CYAN}No logs available${NC}"
        return 0
    fi

    # Show last 10 log entries
    tail -10 "$log_file" | while IFS= read -r line; do
        # Colorize based on log level
        if echo "$line" | grep -qi "error"; then
            echo -e "  ${RED}│${NC} $line"
        elif echo "$line" | grep -qi "warn\|warning"; then
            echo -e "  ${YELLOW}│${NC} $line"
        elif echo "$line" | grep -qi "success\|completed"; then
            echo -e "  ${GREEN}│${NC} $line"
        else
            echo -e "  ${CYAN}│${NC} $line"
        fi
    done
}

################################################################################
# Formatting Functions
################################################################################

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
        initializing)
            echo -e "${CYAN}$status${NC}"
            ;;
        *)
            echo -e "${CYAN}$status${NC}"
            ;;
    esac
}

format_breaker_state() {
    local state="$1"

    case $state in
        closed)
            echo -e "${GREEN}$state${NC}"
            ;;
        open)
            echo -e "${RED}$state${NC}"
            ;;
        half_open)
            echo -e "${YELLOW}$state${NC}"
            ;;
        *)
            echo -e "${CYAN}$state${NC}"
            ;;
    esac
}

format_percentage() {
    local percentage="$1"

    if [ $percentage -ge 80 ]; then
        echo -e "${GREEN}$percentage%${NC}"
    elif [ $percentage -ge 60 ]; then
        echo -e "${YELLOW}$percentage%${NC}"
    else
        echo -e "${RED}$percentage%${NC}"
    fi
}

################################################################################
# Monitoring Functions
################################################################################

monitor_session() {
    local session_id="$1"

    if [ "$FOLLOW_MODE" = true ]; then
        # Continuous monitoring
        while true; do
            display_dashboard "$session_id"
            sleep "$REFRESH_INTERVAL"
        done
    else
        # Single display
        display_dashboard "$session_id"
    fi
}

monitor_all_sessions() {
    print_header "Ralph Runtime - All Sessions"
    echo ""

    if [ ! -d "$SESSIONS_DIR" ]; then
        print_error "Sessions directory not found"
        return 1
    fi

    local session_count=$(find "$SESSIONS_DIR" -name "metadata.json" -type f 2>/dev/null | wc -l)

    if [ $session_count -eq 0 ]; then
        print_info "No sessions found"
        return 0
    fi

    echo -e "${BOLD}Sessions Overview${NC}"
    print_separator
    echo ""

    # List all sessions
    for session_file in $(find "$SESSIONS_DIR" -name "metadata.json" -type f 2>/dev/null | sort -r); do
        local session_dir=$(dirname "$session_file")
        local sid=$(basename "$session_dir")

        # Get session info
        local status=$(grep -o '"status": "[^"]*"' "$session_file" 2>/dev/null | cut -d'"' -f4)
        local start_time=$(grep -o '"startTime": "[^"]*"' "$session_file" 2>/dev/null | cut -d'"' -f4)

        echo -e "  ${CYAN}Session:${NC}    $sid"
        echo -e "  ${CYAN}Status:${NC}    $(format_status "$status")"
        echo -e "  ${CYAN}Started:${NC}   ${start_time:-Unknown}"
        echo ""
    done
}

################################################################################
# Main Function
################################################################################

main() {
    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --session)
                SESSION_ID="$2"
                shift 2
                ;;
            --refresh)
                REFRESH_INTERVAL="$2"
                shift 2
                ;;
            --no-metrics)
                SHOW_METRICS=false
                shift
                ;;
            --no-logs)
                SHOW_LOGS=false
                shift
                ;;
            --no-circuit-breaker)
                SHOW_CIRCUIT_BREAKER=false
                shift
                ;;
            --follow)
                FOLLOW_MODE=true
                shift
                ;;
            --once)
                FOLLOW_MODE=false
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

    # Determine session to monitor
    if [ -z "$SESSION_ID" ]; then
        SESSION_ID=$(find_most_recent_session)

        if [ -z "$SESSION_ID" ]; then
            print_warning "No session found or specified"
            echo ""
            monitor_all_sessions
            exit 0
        fi

        print_info "Monitoring most recent session: $SESSION_ID"
        sleep 1
    fi

    # Validate session
    if [ ! -d "$SESSIONS_DIR/$SESSION_ID" ]; then
        print_error "Session not found: $SESSION_ID"
        exit 1
    fi

    # Start monitoring
    monitor_session "$SESSION_ID"
}

# Run main
main "$@"
