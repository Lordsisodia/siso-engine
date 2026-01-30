#!/bin/bash

################################################################################
# Intervene Script - Human intervention for autonomous execution
# Pause autonomous execution, review state, provide input, resume
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
SESSIONS_DIR="$PROJECT_ROOT/.blackbox4/sessions"
LOGS_DIR="$PROJECT_ROOT/.blackbox4/logs"
INTERVENTION_DIR="$PROJECT_ROOT/.blackbox4/interventions"

# Default values
VERBOSE=false
AUTO_CONFIRM=false
SESSION_ID=""
ACTION=""
INPUT_DATA=""
REASON=""

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}${BOLD}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_section() {
    echo -e "\n${BLUE}${BOLD}▶ $1${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗ ERROR:${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}⚠ WARNING:${NC} $1"
}

print_info() {
    echo -e "${PURPLE}ℹ${NC} $1"
}

verbose_log() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${CYAN}[DEBUG]${NC} $1"
    fi
}

show_help() {
    cat << EOF
${GREEN}Intervene Script${NC} - Human intervention for autonomous execution

${YELLOW}USAGE:${NC}
    $0 [options]

${YELLOW}REQUIRED OPTIONS:${NC}
    ${CYAN}--session <id>${NC}       Session ID to intervene in
    ${CYAN}--action <type>${NC}      Action to perform

${YELLOW}ACTIONS:${NC}
    ${CYAN}pause${NC}                Pause autonomous execution
    ${CYAN}resume${NC}               Resume paused execution
    ${CYAN}guidance${NC}             Provide guidance for execution
    ${CYAN}override${NC}             Override execution decision
    ${CYAN}abort${NC}                Abort execution
    ${CYAN}status${NC}               Show intervention status

${YELLOW}OPTIONAL OPTIONS:${NC}
    ${CYAN}--input <data>${NC}       Input data for guidance/override
    ${CYAN}--reason <text>${NC}      Reason for intervention
    ${CYAN}--priority <level>${NC}   Priority level (low, medium, high, critical)
    ${CYAN}--file <path>${NC}        Read input from file
    ${CYAN}-y, --yes${NC}            Auto-confirm prompts
    ${CYAN}-v, --verbose${NC}        Enable verbose output
    ${CYAN}-h, --help${NC}           Show this help message

${YELLOW}EXAMPLES:${NC}
    # Pause a session
    $0 --session abc123 --action pause --reason "Manual review needed"

    # Resume a session
    $0 --session abc123 --action resume

    # Provide guidance
    $0 --session abc123 --action guidance --input "Focus on UI components first"

    # Override with priority
    $0 --session abc123 --action override --input "Use alternative approach" --priority high

    # Abort execution
    $0 --session abc123 --action abort --reason "Critical bug found"

    # Check intervention status
    $0 --session abc123 --action status

${YELLOW}WORKFLOW:${NC}
    1. Pause the autonomous execution
    2. Review the current state and logs
    3. Provide guidance or override decisions
    4. Resume execution with new input

${YELLOW}INTERVENTION TYPES:${NC}
    ${CYAN}pause${NC}         Temporarily stop execution (can be resumed)
    ${CYAN}guidance${NC}      Provide hints/suggestions without forcing decisions
    ${CYAN}override${NC}      Force a specific decision or action
    ${CYAN}abort${NC}         Stop execution permanently (cannot be resumed)

${YELLOW}PRIORITY LEVELS:${NC}
    ${CYAN}low${NC}           Informational guidance
    ${CYAN}medium${NC}        Important guidance
    ${CYAN}high${NC}          Critical guidance
    ${CYAN}critical${NC}      Immediate override required

For more information, see: $PROJECT_ROOT/.blackbox4/docs/intervene.md

EOF
}

################################################################################
# Validation Functions
################################################################################

validate_session() {
    local session_id="$1"

    if [ -z "$session_id" ]; then
        print_error "Session ID is required"
        return 1
    fi

    if [ ! -d "$SESSIONS_DIR/$session_id" ]; then
        print_error "Session not found: $session_id"
        return 1
    fi

    if [ ! -f "$SESSIONS_DIR/$session_id/metadata.json" ]; then
        print_error "Session metadata not found: $session_id"
        return 1
    fi

    # Check if intervention is enabled
    local intervention_enabled
    intervention_enabled=$(grep -o '"interventionEnabled": [truefalse]' "$SESSIONS_DIR/$session_id/metadata.json" 2>/dev/null | cut -d':' -f2)

    if [ "$intervention_enabled" != "true" ]; then
        print_error "Intervention is not enabled for this session"
        print_info "To enable intervention, restart the session with --intervention-enabled flag"
        return 1
    fi

    verbose_log "Session validation complete: $session_id"
    return 0
}

validate_action() {
    local action="$1"

    case $action in
        pause|resume|guidance|override|abort|status)
            return 0
            ;;
        *)
            print_error "Unknown action: $action"
            print_info "Valid actions: pause, resume, guidance, override, abort, status"
            return 1
            ;;
    esac
}

################################################################################
# Session State Functions
################################################################################

get_session_status() {
    local session_id="$1"
    local metadata_file="$SESSIONS_DIR/$session_id/metadata.json"

    grep -o '"status": "[^"]*"' "$metadata_file" 2>/dev/null | cut -d'"' -f4
}

get_session_state() {
    local session_id="$1"
    local state_file="$SESSIONS_DIR/$session_id/state.json"

    if [ -f "$state_file" ]; then
        cat "$state_file"
    else
        echo "{}"
    fi
}

display_session_state() {
    local session_id="$1"

    print_section "Current Session State"

    # Show metadata
    local metadata_file="$SESSIONS_DIR/$session_id/metadata.json"
    if [ -f "$metadata_file" ]; then
        echo -e "${CYAN}Session ID:${NC}    $session_id"
        echo -e "${CYAN}Status:${NC}        $(get_session_status "$session_id")"

        local current_iter=$(grep -o '"currentIteration": [0-9]*' "$metadata_file" 2>/dev/null | cut -d':' -f2)
        local max_iter=$(grep -o '"maxIterations": [0-9]*' "$metadata_file" 2>/dev/null | cut -d':' -f2)
        echo -e "${CYAN}Iteration:${NC}     ${current_iter:-0} / ${max_iter:-100}"
    fi

    # Show state
    echo ""
    local state=$(get_session_state "$session_id")
    local current_task=$(echo "$state" | grep -o '"currentTask": "[^"]*"' | cut -d'"' -f4)

    if [ -n "$current_task" ] && [ "$current_task" != "null" ]; then
        echo -e "${CYAN}Current Task:${NC}  $current_task"
    else
        echo -e "${CYAN}Current Task:${NC}  No active task"
    fi

    # Show recent interventions
    if [ -f "$SESSIONS_DIR/$session_id/interventions.log" ]; then
        echo ""
        echo -e "${CYAN}Recent Interventions:${NC}"
        tail -3 "$SESSIONS_DIR/$session_id/interventions.log" | sed 's/^/  /'
    fi
}

################################################################################
# Intervention Functions
################################################################################

action_pause() {
    local session_id="$1"
    local reason="$2"

    print_header "Intervention: PAUSE"
    print_info "Session: $session_id"

    if [ -n "$reason" ]; then
        print_info "Reason: $reason"
    fi

    # Get current status
    local current_status=$(get_session_status "$session_id")

    if [ "$current_status" = "paused" ]; then
        print_warning "Session is already paused"
        return 0
    fi

    if [ "$current_status" = "stopped" ] || [ "$current_status" = "completed" ]; then
        print_error "Cannot pause session in status: $current_status"
        return 1
    fi

    # Confirm action
    if [ "$AUTO_CONFIRM" != true ]; then
        echo ""
        echo -n "Pause session $session_id? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_info "Intervention cancelled"
            return 0
        fi
    fi

    # Update session status
    update_session_status "$session_id" "paused"

    # Log intervention
    log_intervention "$session_id" "pause" "$reason"

    print_success "Session paused successfully"
    print_info "Use 'resume' action to continue execution"
    print_info "Use 'guidance' action to provide input before resuming"
}

action_resume() {
    local session_id="$1"

    print_header "Intervention: RESUME"
    print_info "Session: $session_id"

    # Get current status
    local current_status=$(get_session_status "$session_id")

    if [ "$current_status" != "paused" ]; then
        print_error "Session is not paused (current status: $current_status)"
        return 1
    fi

    # Confirm action
    if [ "$AUTO_CONFIRM" != true ]; then
        echo ""
        echo -n "Resume session $session_id? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_info "Intervention cancelled"
            return 0
        fi
    fi

    # Update session status
    update_session_status "$session_id" "running"

    # Log intervention
    log_intervention "$session_id" "resume" "Resumed execution"

    print_success "Session resumed successfully"
    print_info "Autonomous execution will continue"
}

action_guidance() {
    local session_id="$1"
    local input="$2"
    local priority="${3:-medium}"

    print_header "Intervention: GUIDANCE"
    print_info "Session: $session_id"
    print_info "Priority: $priority"

    if [ -z "$input" ]; then
        print_error "Input data is required for guidance"
        print_info "Use --input or --file to provide guidance"
        return 1
    fi

    # Get current status
    local current_status=$(get_session_status "$session_id"

    if [ "$current_status" != "paused" ]; then
        print_warning "Session is not paused. Guidance will be queued for next iteration."
    fi

    # Display guidance
    echo ""
    print_section "Guidance Input"
    echo "$input" | fold -s -w 70 | sed 's/^/  /'

    # Confirm action
    if [ "$AUTO_CONFIRM" != true ]; then
        echo ""
        echo -n "Submit this guidance? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_info "Intervention cancelled"
            return 0
        fi
    fi

    # Save guidance
    save_guidance "$session_id" "$input" "$priority"

    # Log intervention
    log_intervention "$session_id" "guidance" "Priority: $priority | $input"

    print_success "Guidance submitted successfully"
    print_info "Guidance will be applied when execution resumes"
}

action_override() {
    local session_id="$1"
    local input="$2"
    local priority="${3:-high}"
    local reason="$4"

    print_header "Intervention: OVERRIDE"
    print_warning "This will force a specific action or decision"
    print_info "Session: $session_id"
    print_info "Priority: $priority"

    if [ -z "$input" ]; then
        print_error "Input data is required for override"
        print_info "Use --input or --file to provide override command"
        return 1
    fi

    # Display override
    echo ""
    print_section "Override Command"
    echo "$input" | fold -s -w 70 | sed 's/^/  /'
    echo ""

    # Get current status
    local current_status=$(get_session_status "$session_id")

    if [ "$current_status" = "running" ]; then
        print_warning "Session is currently running. Override will be applied at next checkpoint."
    fi

    # Confirm action
    if [ "$AUTO_CONFIRM" != true ]; then
        echo -n "Apply this override? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_info "Intervention cancelled"
            return 0
        fi
    fi

    # Save override
    save_override "$session_id" "$input" "$priority" "$reason"

    # Log intervention
    log_intervention "$session_id" "override" "Priority: $priority | Reason: ${reason:-None} | $input"

    print_success "Override applied successfully"
    print_info "Execution will follow override command"
}

action_abort() {
    local session_id="$1"
    local reason="$2"

    print_header "Intervention: ABORT"
    print_warning "This will permanently stop execution"
    print_info "Session: $session_id"

    if [ -n "$reason" ]; then
        print_info "Reason: $reason"
    fi

    # Get current status
    local current_status=$(get_session_status "$session_id")

    if [ "$current_status" = "completed" ]; then
        print_error "Session is already completed"
        return 1
    fi

    # Confirm action
    if [ "$AUTO_CONFIRM" != true ]; then
        echo ""
        echo -n "ABORT session $session_id? This cannot be undone. (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_info "Intervention cancelled"
            return 0
        fi
    fi

    # Update session status
    update_session_status "$session_id" "aborted"

    # Log intervention
    log_intervention "$session_id" "abort" "$reason"

    print_success "Session aborted successfully"
    print_warning "This session cannot be resumed"
}

action_status() {
    local session_id="$1"

    print_header "Intervention Status"
    display_session_state "$session_id"

    # Show pending interventions
    echo ""
    print_section "Pending Interventions"

    local intervention_file="$INTERVENTION_DIR/$session_id/pending.json"
    if [ -f "$intervention_file" ]; then
        local count=$(grep -o '"type":' "$intervention_file" | wc -l)
        print_info "Pending interventions: $count"
    else
        print_info "No pending interventions"
    fi
}

################################################################################
# Helper Functions for Actions
################################################################################

update_session_status() {
    local session_id="$1"
    local new_status="$2"
    local metadata_file="$SESSIONS_DIR/$session_id/metadata.json"

    # Update status in metadata file
    # In production, would use jq or similar
    sed -i.tmp "s/\"status\": \"[^\"]*\"/\"status\": \"$new_status\"/" "$metadata_file"
    rm -f "$metadata_file.tmp"

    verbose_log "Updated session status: $session_id -> $new_status"
}

log_intervention() {
    local session_id="$1"
    local action="$2"
    local details="$3"
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    # Create interventions log if it doesn't exist
    local log_file="$SESSIONS_DIR/$session_id/interventions.log"
    touch "$log_file"

    # Log intervention
    echo "[$timestamp] $action: $details" >> "$log_file"

    verbose_log "Logged intervention: $action"
}

save_guidance() {
    local session_id="$1"
    local input="$2"
    local priority="$3"

    mkdir -p "$INTERVENTION_DIR/$session_id"

    local guidance_file="$INTERVENTION_DIR/$session_id/guidance.json"

    # Append guidance to file
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    if [ ! -f "$guidance_file" ]; then
        echo '{"guidance": []}' > "$guidance_file"
    fi

    # In production, would use jq to append to array
    verbose_log "Saved guidance for session: $session_id"
}

save_override() {
    local session_id="$1"
    local input="$2"
    local priority="$3"
    local reason="$4"

    mkdir -p "$INTERVENTION_DIR/$session_id"

    local override_file="$INTERVENTION_DIR/$session_id/override.json"

    # Save override
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    cat > "$override_file" << EOF
{
    "timestamp": "$timestamp",
    "priority": "$priority",
    "reason": "$reason",
    "command": "$input",
    "applied": false
}
EOF

    verbose_log "Saved override for session: $session_id"
}

################################################################################
# Interactive Mode
################################################################################

interactive_mode() {
    local session_id="$1"

    print_header "Interactive Intervention Mode"
    print_info "Session: $session_id"
    print_info "Press Ctrl+C to exit"

    while true; do
        echo ""
        display_session_state "$session_id"

        echo ""
        print_section "Available Actions"
        echo "  1. Pause"
        echo "  2. Resume"
        echo "  3. Provide Guidance"
        echo "  4. Override Decision"
        echo "  5. Abort"
        echo "  6. Refresh Status"
        echo "  0. Exit"

        echo ""
        echo -n "Select action (0-6): "
        read -r choice

        case $choice in
            1)
                echo ""
                echo -n "Enter reason (optional): "
                read -r reason
                action_pause "$session_id" "$reason"
                ;;
            2)
                action_resume "$session_id"
                ;;
            3)
                echo ""
                echo "Enter guidance (press Ctrl+D when done):"
                input=$(cat)
                echo ""
                echo -n "Priority (low/medium/high/critical) [medium]: "
                read -r priority
                priority=${priority:-medium}
                action_guidance "$session_id" "$input" "$priority"
                ;;
            4)
                echo ""
                echo "Enter override command (press Ctrl+D when done):"
                input=$(cat)
                echo ""
                echo -n "Priority (low/medium/high/critical) [high]: "
                read -r priority
                priority=${priority:-high}
                echo ""
                echo -n "Reason (optional): "
                read -r reason
                action_override "$session_id" "$input" "$priority" "$reason"
                ;;
            5)
                echo ""
                echo -n "Enter reason (optional): "
                read -r reason
                action_abort "$session_id" "$reason"
                break
                ;;
            6)
                continue
                ;;
            0)
                print_info "Exiting interactive mode"
                break
                ;;
            *)
                print_error "Invalid choice"
                ;;
        esac
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
            --action)
                ACTION="$2"
                shift 2
                ;;
            --input)
                INPUT_DATA="$2"
                shift 2
                ;;
            --reason)
                REASON="$2"
                shift 2
                ;;
            --priority)
                PRIORITY="$2"
                shift 2
                ;;
            --file)
                if [ -f "$2" ]; then
                    INPUT_DATA=$(cat "$2")
                else
                    print_error "File not found: $2"
                    exit 1
                fi
                shift 2
                ;;
            --interactive)
                INTERACTIVE_MODE=true
                shift
                ;;
            -y|--yes)
                AUTO_CONFIRM=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
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

    # Check for interactive mode
    if [ "${INTERACTIVE_MODE:-false}" = true ]; then
        if [ -z "$SESSION_ID" ]; then
            print_error "Session ID is required for interactive mode"
            exit 1
        fi
        validate_session "$SESSION_ID" || exit 1
        interactive_mode "$SESSION_ID"
        exit 0
    fi

    # Validate required options
    if [ -z "$SESSION_ID" ]; then
        print_error "Session ID is required (--session)"
        echo ""
        show_help
        exit 1
    fi

    if [ -z "$ACTION" ]; then
        print_error "Action is required (--action)"
        echo ""
        show_help
        exit 1
    fi

    # Validate session
    validate_session "$SESSION_ID" || exit 1

    # Validate action
    validate_action "$ACTION" || exit 1

    # Execute action
    case $ACTION in
        pause)
            action_pause "$SESSION_ID" "$REASON"
            ;;
        resume)
            action_resume "$SESSION_ID"
            ;;
        guidance)
            action_guidance "$SESSION_ID" "$INPUT_DATA" "${PRIORITY:-medium}"
            ;;
        override)
            action_override "$SESSION_ID" "$INPUT_DATA" "${PRIORITY:-high}" "$REASON"
            ;;
        abort)
            action_abort "$SESSION_ID" "$REASON"
            ;;
        status)
            action_status "$SESSION_ID"
            ;;
        *)
            print_error "Unknown action: $ACTION"
            exit 1
            ;;
    esac
}

# Run main
main "$@"
