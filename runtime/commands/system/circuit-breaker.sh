#!/bin/bash

################################################################################
# Circuit Breaker Wrapper Script
# Wrapper for circuit breaker operations in Ralph Runtime
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
CIRCUIT_BREAKER_DIR="$PROJECT_ROOT/.blackbox4/ralph-runtime/circuit-breaker"
CONFIG_DIR="$PROJECT_ROOT/.blackbox4/config"
STATE_DIR="$PROJECT_ROOT/.blackbox4/state"
LOGS_DIR="$PROJECT_ROOT/.blackbox4/logs"

# Default values
VERBOSE=false
QUIET=false
BREAKER_NAME="ralph-main"
JSON_OUTPUT=false

################################################################################
# Helper Functions
################################################################################

print_header() {
    [ "$QUIET" = false ] || return 0
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_section() {
    [ "$QUIET" = false ] || return 0
    echo -e "\n${BLUE}▶ $1${NC}\n"
}

print_success() {
    [ "$QUIET" = false ] || return 0
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ ERROR: $1${NC}" >&2
}

print_warning() {
    [ "$QUIET" = false ] || return 0
    echo -e "${YELLOW}⚠ WARNING: $1${NC}"
}

print_info() {
    [ "$QUIET" = false ] || return 0
    echo -e "${PURPLE}ℹ $1${NC}"
}

verbose_log() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${CYAN}[DEBUG] $1${NC}"
    fi
}

show_help() {
    cat << EOF
${GREEN}Circuit Breaker Wrapper${NC} - Circuit breaker operations for Ralph Runtime

${YELLOW}USAGE:${NC}
    $0 <command> [options]

${YELLOW}COMMANDS:${NC}
    ${CYAN}status${NC}      Show circuit breaker status
    ${CYAN}reset${NC}       Reset circuit breaker to closed state
    ${CYAN}test${NC}        Test circuit breaker behavior
    ${CYAN}metrics${NC}     Show circuit breaker metrics
    ${CYAN}history${NC}     Show circuit breaker state history
    ${CYAN}configure${NC}   Manage circuit breaker configuration
    ${CYAN}simulate${NC}    Simulate circuit breaker scenarios
    ${CYAN}help${NC}        Show this help message

${YELLOW}OPTIONS:${NC}
    ${CYAN}--breaker <name>${NC}     Circuit breaker name (default: ralph-main)
    ${CYAN}--json${NC}               Output in JSON format
    ${CYAN}--timeout <ms>${NC}       Recovery timeout in milliseconds
    ${CYAN}--threshold <n>${NC}      Failure threshold
    ${CYAN}-v, --verbose${NC}        Enable verbose output
    ${CYAN}-q, --quiet${NC}          Suppress output (except errors)
    ${CYAN}-h, --help${NC}           Show help message

${YELLOW}STATUS OPTIONS:${NC}
    ${CYAN}--detailed${NC}           Show detailed status information
    ${CYAN}--watch${NC}              Continuously monitor status

${YELLOW}TEST OPTIONS:${NC}
    ${CYAN}--scenario <type>${NC}    Scenario to test (failure, timeout, success)
    ${CYAN}--iterations <n>${NC}     Number of test iterations

${YELLOW}METRICS OPTIONS:${NC}
    ${CYAN}--period <duration>${NC}  Time period for metrics
    ${CYAN}--top <n>${NC}            Show top n metrics

${YELLOW}EXAMPLES:${NC}
    # Check circuit breaker status
    $0 status

    # Check specific breaker
    $0 status --breaker agent-execution

    # Reset circuit breaker
    $0 reset --breaker ralph-main

    # Test failure scenario
    $0 test --scenario failure --iterations 5

    # Show metrics in JSON
    $0 metrics --json

    # Detailed status with watch
    $0 status --detailed --watch

${YELLOW}CIRCUIT BREAKER STATES:${NC}
    ${GREEN}CLOSED${NC}      Normal operation, requests pass through
    ${YELLOW}OPEN${NC}       Circuit is tripped, requests are blocked
    ${PURPLE}HALF_OPEN${NC}  Testing if system has recovered

${YELLOW}STATE TRANSITIONS:${NC}
    CLOSED → OPEN:           When failure threshold is reached
    OPEN → HALF_OPEN:        After recovery timeout expires
    HALF_OPEN → CLOSED:      When test requests succeed
    HALF_OPEN → OPEN:        When test requests fail

For more information, see: $PROJECT_ROOT/.blackbox4/docs/circuit-breaker.md

EOF
}

################################################################################
# State Management
################################################################################

get_breaker_state_file() {
    local breaker_name="$1"
    echo "$STATE_DIR/circuit-breaker-${breaker_name}.json"
}

initialize_breaker() {
    local breaker_name="$1"
    local state_file
    state_file=$(get_breaker_state_file "$breaker_name")

    if [ ! -f "$state_file" ]; then
        verbose_log "Initializing circuit breaker: $breaker_name"
        mkdir -p "$STATE_DIR"

        cat > "$state_file" << EOF
{
    "name": "$breaker_name",
    "state": "closed",
    "failureCount": 0,
    "successCount": 0,
    "lastFailureTime": null,
    "lastSuccessTime": null,
    "lastStateChange": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "failureThreshold": 5,
    "recoveryTimeout": 60000,
    "history": []
}
EOF

        print_success "Initialized circuit breaker: $breaker_name"
    fi
}

read_breaker_state() {
    local breaker_name="$1"
    local state_file
    state_file=$(get_breaker_state_file "$breaker_name")

    if [ ! -f "$state_file" ]; then
        initialize_breaker "$breaker_name"
    fi

    cat "$state_file"
}

update_breaker_state() {
    local breaker_name="$1"
    local new_state="$2"
    local state_file
    state_file=$(get_breaker_state_file "$breaker_name")

    if [ ! -f "$state_file" ]; then
        initialize_breaker "$breaker_name"
    fi

    # Update state
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local current_state=$(cat "$state_file")

    # Add to history
    local history_entry="{
        \"timestamp\": \"$timestamp\",
        \"state\": \"$new_state\",
        \"previousState\": $(echo "$current_state" | grep -o '"state": "[^"]*"' | cut -d'"' -f4)
    }"

    # Update the state file
    # This is simplified - production would use jq or similar
    echo "$current_state" | sed "s/\"state\": \"[^\"]*\"/\"state\": \"$new_state\"/" | \
        sed "s/\"lastStateChange\": \"[^\"]*\"/\"lastStateChange\": \"$timestamp\"/" > "$state_file"

    verbose_log "Updated breaker state: $breaker_name -> $new_state"
}

################################################################################
# Status Functions
################################################################################

show_status() {
    local detailed="${DETAILED:-false}"
    local watch="${WATCH:-false}"

    if [ "$watch" = true ]; then
        while true; do
            clear
            print_header "Circuit Breaker Status (Live Monitor)"
            show_breaker_status "$BREAKER_NAME" "$detailed"
            sleep 2
        done
    else
        print_header "Circuit Breaker Status"
        show_breaker_status "$BREAKER_NAME" "$detailed"
    fi
}

show_breaker_status() {
    local breaker_name="$1"
    local detailed="$2"

    local state_data
    state_data=$(read_breaker_state "$breaker_name")

    if [ "$JSON_OUTPUT" = true ]; then
        echo "$state_data"
        return 0
    fi

    # Parse state
    local state=$(echo "$state_data" | grep -o '"state": "[^"]*"' | cut -d'"' -f4)
    local failure_count=$(echo "$state_data" | grep -o '"failureCount": [0-9]*' | cut -d':' -f2)
    local success_count=$(echo "$state_data" | grep -o '"successCount": [0-9]*' | cut -d':' -f2)
    local threshold=$(echo "$state_data" | grep -o '"failureThreshold": [0-9]*' | cut -d':' -f2)
    local last_change=$(echo "$state_data" | grep -o '"lastStateChange": "[^"]*"' | cut -d'"' -f4)

    # Display status
    print_section "Breaker: $breaker_name"

    # State with color
    case $state in
        closed)
            echo -e "  State:           ${GREEN}$state${NC}"
            ;;
        open)
            echo -e "  State:           ${RED}$state${NC}"
            ;;
        half_open)
            echo -e "  State:           ${PURPLE}$state${NC}"
            ;;
        *)
            echo -e "  State:           ${CYAN}$state${NC}"
            ;;
    esac

    echo "  Failures:        $failure_count / $threshold"
    echo "  Successes:       $success_count"
    echo "  Last Changed:    $last_change"

    if [ "$detailed" = true ]; then
        echo ""
        print_section "Detailed Metrics"

        # Calculate uptime percentage
        local total=$((failure_count + success_count))
        if [ $total -gt 0 ]; then
            local success_rate=$((success_count * 100 / total))
            echo "  Total Requests:  $total"
            echo "  Success Rate:    $success_rate%"
        else
            echo "  Total Requests:  0"
            echo "  Success Rate:    N/A"
        fi

        # Recent history
        echo ""
        print_section "Recent State Changes"
        local history=$(echo "$state_data" | grep -o '"history": \[[^]]*\]')
        if [ -n "$history" ]; then
            echo "  (History tracking - detailed view available)"
        else
            echo "  No history available"
        fi
    fi

    # Health indicator
    echo ""
    local health
    if [ "$state" = "closed" ]; then
        health="${GREEN}● Healthy${NC}"
    elif [ "$state" = "open" ]; then
        health="${RED}● Unhealthy${NC}"
    else
        health="${YELLOW}● Recovering${NC}"
    fi
    echo -e "  Status:          $health"
}

################################################################################
# Reset Functions
################################################################################

reset_breaker() {
    print_header "Reset Circuit Breaker"
    print_info "Breaker: $BREAKER_NAME"

    local state_file
    state_file=$(get_breaker_state_file "$BREAKER_NAME")

    if [ ! -f "$state_file" ]; then
        print_error "Circuit breaker not found: $BREAKER_NAME"
        return 1
    fi

    # Confirm reset
    if [ "${RALPH_AUTO_CONFIRM:-false}" != "true" ]; then
        echo -n "Reset circuit breaker to closed state? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_info "Reset cancelled"
            return 0
        fi
    fi

    # Reset state
    cat > "$state_file" << EOF
{
    "name": "$BREAKER_NAME",
    "state": "closed",
    "failureCount": 0,
    "successCount": 0,
    "lastFailureTime": null,
    "lastSuccessTime": null,
    "lastStateChange": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "failureThreshold": 5,
    "recoveryTimeout": 60000,
    "history": []
}
EOF

    print_success "Circuit breaker reset successfully"
    print_info "State: closed"
    print_info "Failures: 0"

    verbose_log "Reset circuit breaker: $BREAKER_NAME"
}

################################################################################
# Test Functions
################################################################################

test_breaker() {
    local scenario="${SCENARIO:-success}"
    local iterations="${ITERATIONS:-1}"

    print_header "Circuit Breaker Test"
    print_info "Breaker: $BREAKER_NAME"
    print_info "Scenario: $scenario"
    print_info "Iterations: $iterations"

    initialize_breaker "$BREAKER_NAME"

    for ((i=1; i<=iterations; i++)); do
        print_section "Iteration $i/$iterations"

        case $scenario in
            failure)
                simulate_failure
                ;;
            timeout)
                simulate_timeout
                ;;
            success)
                simulate_success
                ;;
            *)
                print_error "Unknown scenario: $scenario"
                return 1
                ;;
        esac

        sleep 1
    done

    print_success "Test completed"
}

simulate_failure() {
    print_info "Simulating failure..."

    local state_file
    state_file=$(get_breaker_state_file "$BREAKER_NAME")

    # Increment failure count
    local state_data=$(cat "$state_file")
    local failure_count=$(echo "$state_data" | grep -o '"failureCount": [0-9]*' | cut -d':' -f2)
    local threshold=$(echo "$state_data" | grep -o '"failureThreshold": [0-9]*' | cut -d':' -f2)
    local new_count=$((failure_count + 1))

    # Update state
    update_failure_count "$BREAKER_NAME" "$new_count"

    print_warning "Failure recorded: $new_count/$threshold"

    # Check if threshold reached
    if [ $new_count -ge $threshold ]; then
        update_breaker_state "$BREAKER_NAME" "open"
        print_error "Failure threshold reached! Circuit opened."
    fi
}

simulate_timeout() {
    print_info "Simulating timeout..."
    simulate_failure
}

simulate_success() {
    print_info "Simulating success..."

    local state_file
    state_file=$(get_breaker_state_file "$BREAKER_NAME")

    # Increment success count
    local state_data=$(cat "$state_file")
    local success_count=$(echo "$state_data" | grep -o '"successCount": [0-9]*' | cut -d':' -f2)
    local new_count=$((success_count + 1))

    update_success_count "$BREAKER_NAME" "$new_count"

    print_success "Success recorded: $new_count"

    # If in half_open, transition to closed
    local state=$(echo "$state_data" | grep -o '"state": "[^"]*"' | cut -d'"' -f4)
    if [ "$state" = "half_open" ]; then
        update_breaker_state "$BREAKER_NAME" "closed"
        print_success "Circuit recovered! State: closed"
    fi
}

update_failure_count() {
    local breaker_name="$1"
    local count="$2"
    local state_file
    state_file=$(get_breaker_state_file "$breaker_name")

    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    cat "$state_file" | sed "s/\"failureCount\": [0-9]*/\"failureCount\": $count/" | \
        sed "s/\"lastFailureTime\": \"[^\"]*\"/\"lastFailureTime\": \"$timestamp\"/" > "$state_file.tmp"
    mv "$state_file.tmp" "$state_file"
}

update_success_count() {
    local breaker_name="$1"
    local count="$2"
    local state_file
    state_file=$(get_breaker_state_file "$breaker_name")

    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    cat "$state_file" | sed "s/\"successCount\": [0-9]*/\"successCount\": $count/" | \
        sed "s/\"lastSuccessTime\": \"[^\"]*\"/\"lastSuccessTime\": \"$timestamp\"/" > "$state_file.tmp"
    mv "$state_file.tmp" "$state_file"
}

################################################################################
# Metrics Functions
################################################################################

show_metrics() {
    print_header "Circuit Breaker Metrics"

    local state_data
    state_data=$(read_breaker_state "$BREAKER_NAME")

    if [ "$JSON_OUTPUT" = true ]; then
        # Calculate and output metrics as JSON
        cat << EOF
{
    "breakerName": "$BREAKER_NAME",
    "state": $(echo "$state_data" | grep -o '"state": "[^"]*"' | cut -d'"' -f4),
    "failureCount": $(echo "$state_data" | grep -o '"failureCount": [0-9]*' | cut -d':' -f2),
    "successCount": $(echo "$state_data" | grep -o '"successCount": [0-9]*' | cut -d':' -f2),
    "threshold": $(echo "$state_data" | grep -o '"failureThreshold": [0-9]*' | cut -d':' -f2),
    "successRate": $(calculate_success_rate "$state_data"),
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
        return 0
    fi

    print_section "Performance Metrics"

    # Parse data
    local failure_count=$(echo "$state_data" | grep -o '"failureCount": [0-9]*' | cut -d':' -f2)
    local success_count=$(echo "$state_data" | grep -o '"successCount": [0-9]*' | cut -d':' -f2)
    local threshold=$(echo "$state_data" | grep -o '"failureThreshold": [0-9]*' | cut -d':' -f2)
    local total=$((failure_count + success_count))

    echo "  Total Requests:  $total"
    echo "  Successful:      $success_count"
    echo "  Failed:          $failure_count"
    echo "  Threshold:       $threshold"

    if [ $total -gt 0 ]; then
        local success_rate=$((success_count * 100 / total))
        echo "  Success Rate:    $success_rate%"
    fi

    # Health score
    echo ""
    print_section "Health Score"
    local health_score
    if [ $total -eq 0 ]; then
        health_score=100
    else
        health_score=$((success_count * 100 / total))
    fi

    if [ $health_score -ge 80 ]; then
        echo -e "  ${GREEN}● $health_score% - Excellent${NC}"
    elif [ $health_score -ge 60 ]; then
        echo -e "  ${YELLOW}● $health_score% - Good${NC}"
    elif [ $health_score -ge 40 ]; then
        echo -e "  ${YELLOW}● $health_score% - Fair${NC}"
    else
        echo -e "  ${RED}● $health_score% - Poor${NC}"
    fi
}

calculate_success_rate() {
    local state_data="$1"
    local failure_count=$(echo "$state_data" | grep -o '"failureCount": [0-9]*' | cut -d':' -f2)
    local success_count=$(echo "$state_data" | grep -o '"successCount": [0-9]*' | cut -d':' -f2)
    local total=$((failure_count + success_count))

    if [ $total -eq 0 ]; then
        echo "100"
    else
        echo $((success_count * 100 / total))
    fi
}

################################################################################
# History Functions
################################################################################

show_history() {
    print_header "Circuit Breaker History"
    print_info "Breaker: $BREAKER_NAME"

    local state_data
    state_data=$(read_breaker_state "$BREAKER_NAME")

    print_section "State Change History"
    echo "  Last State Change: $(echo "$state_data" | grep -o '"lastStateChange": "[^"]*"' | cut -d'"' -f4)"

    # Show recent history if available
    if [ "$JSON_OUTPUT" = true ]; then
        echo "$state_data" | grep -o '"history": \[[^]]*\]'
    else
        echo "  (Full history tracking requires state persistence)"
    fi
}

################################################################################
# Configuration Functions
################################################################################

configure_breaker() {
    print_header "Circuit Breaker Configuration"
    print_info "Breaker: $BREAKER_NAME"

    local state_file
    state_file=$(get_breaker_state_file "$BREAKER_NAME")

    initialize_breaker "$BREAKER_NAME"

    print_section "Current Configuration"

    local state_data=$(cat "$state_file")
    local threshold=$(echo "$state_data" | grep -o '"failureThreshold": [0-9]*' | cut -d':' -f2)
    local timeout=$(echo "$state_data" | grep -o '"recoveryTimeout": [0-9]*' | cut -d':' -f2)

    echo "  Failure Threshold: $threshold"
    echo "  Recovery Timeout:  ${timeout}ms ($((timeout / 1000))s)"
    echo ""
    echo "To configure, edit: $state_file"
}

################################################################################
# Simulate Functions
################################################################################

simulate_scenario() {
    local scenario="${1:-}"

    print_header "Circuit Breaker Simulation"
    print_info "Scenario: $scenario"

    case $scenario in
        failure-spike)
            print_info "Simulating sudden spike in failures..."
            test_breaker
            ;;
        slow-degradation)
            print_info "Simulating slow degradation..."
            ;;
        recovery)
            print_info "Simulating recovery scenario..."
            ;;
        *)
            print_error "Unknown scenario: $scenario"
            print_info "Available scenarios: failure-spike, slow-degradation, recovery"
            return 1
            ;;
    esac
}

################################################################################
# Main Function
################################################################################

main() {
    # Create necessary directories
    mkdir -p "$STATE_DIR" "$LOGS_DIR" "$CONFIG_DIR"

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
            --breaker)
                BREAKER_NAME="$2"
                shift 2
                ;;
            --json)
                JSON_OUTPUT=true
                shift
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --threshold)
                THRESHOLD="$2"
                shift 2
                ;;
            --detailed)
                DETAILED=true
                shift
                ;;
            --watch)
                WATCH=true
                shift
                ;;
            --scenario)
                SCENARIO="$2"
                shift 2
                ;;
            --iterations)
                ITERATIONS="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -q|--quiet)
                QUIET=true
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
        status)
            show_status
            ;;
        reset)
            reset_breaker
            ;;
        test)
            test_breaker
            ;;
        metrics)
            show_metrics
            ;;
        history)
            show_history
            ;;
        configure)
            configure_breaker
            ;;
        simulate)
            simulate_scenario "$SCENARIO"
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
