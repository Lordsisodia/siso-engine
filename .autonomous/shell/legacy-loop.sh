#!/bin/bash
# Legacy Autonomous Loop for SISO Internal
# Uses BlackBox 5 infrastructure for task tracking

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROMPT_FILE="$PROJECT_DIR/.Autonomous/LEGACY.md"
LOG_DIR="$PROJECT_DIR/.Autonomous/LOGS"
TELEMETRY_SCRIPT="$PROJECT_DIR/.Autonomous/telemetry.sh"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SESSION_LOG="$LOG_DIR/ralph-session-$TIMESTAMP.log"
TELEMETRY_FILE=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$SESSION_LOG"
    if [ -n "$TELEMETRY_FILE" ]; then
        "$TELEMETRY_SCRIPT" event info "$1" "$TELEMETRY_FILE" 2>/dev/null || true
    fi
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$SESSION_LOG"
    if [ -n "$TELEMETRY_FILE" ]; then
        "$TELEMETRY_SCRIPT" event error "$1" "$TELEMETRY_FILE" 2>/dev/null || true
    fi
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$SESSION_LOG"
    if [ -n "$TELEMETRY_FILE" ]; then
        "$TELEMETRY_SCRIPT" event success "$1" "$TELEMETRY_FILE" 2>/dev/null || true
    fi
}

log_phase() {
    echo -e "${CYAN}[PHASE]${NC} $1" | tee -a "$SESSION_LOG"
    if [ -n "$TELEMETRY_FILE" ]; then
        "$TELEMETRY_SCRIPT" phase "$1" "in_progress" "$TELEMETRY_FILE" 2>/dev/null || true
    fi
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$SESSION_LOG"
    if [ -n "$TELEMETRY_FILE" ]; then
        "$TELEMETRY_SCRIPT" event warning "$1" "$TELEMETRY_FILE" 2>/dev/null || true
    fi
}

# Initialize telemetry for this run
init_run() {
    if [ -x "$TELEMETRY_SCRIPT" ]; then
        TELEMETRY_FILE=$("$TELEMETRY_SCRIPT" init)
        log "Telemetry initialized: $(basename "$TELEMETRY_FILE")"
    fi
}

# Check we're on safe branch (not main/master)
check_branch() {
    cd "$PROJECT_DIR"
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")

    if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
        log_error "CRITICAL: On '$CURRENT_BRANCH' branch! Legacy cannot run here."
        exit 1
    fi

    # Allow dev, feature/*, and any other non-main branches
    log "Running on branch: $CURRENT_BRANCH"
}

# Check prerequisites
check_prerequisites() {
    log_phase "prerequisites"

    # Check claude is available
    if ! command -v claude &> /dev/null; then
        log_error "claude command not found in PATH"
        exit 1
    fi
    log "✓ claude found"

    # Check prompt file exists
    if [ ! -f "$PROMPT_FILE" ]; then
        log_error "LEGACY.md not found at $PROMPT_FILE"
        exit 1
    fi
    log "✓ LEGACY.md found"

    # Check active tasks exist
    local active_tasks=$(find "$PROJECT_DIR/.Autonomous/tasks/active" -name "*.md" -type f ! -name "index.md" ! -name "TEMPLATE.md" 2>/dev/null | wc -l)
    if [ "$active_tasks" -eq 0 ]; then
        log_warning "No active tasks found"
    else
        log "✓ $active_tasks active task(s) found"
    fi

    # Check jq is available for telemetry
    if ! command -v jq &> /dev/null; then
        log_warning "jq not found - telemetry will be limited"
    fi

    if [ -n "$TELEMETRY_FILE" ]; then
        "$TELEMETRY_SCRIPT" phase prerequisites "complete" "$TELEMETRY_FILE" 2>/dev/null || true
    fi
}

# Display run summary
show_summary() {
    echo ""
    echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
    echo -e "${MAGENTA}  Run Summary${NC}"
    echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
    echo ""
    log "Session log: $SESSION_LOG"
    if [ -n "$TELEMETRY_FILE" ]; then
        log "Telemetry: $TELEMETRY_FILE"
        "$TELEMETRY_SCRIPT" status 2>/dev/null || true
    fi
    echo ""
}

# Main loop
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║              Legacy Autonomous System - SISO Internal      ║"
    echo "║              First Principles Build System                 ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    mkdir -p "$LOG_DIR"

    # Initialize telemetry
    init_run

    log "Starting Legacy loop..."
    log "Project: $PROJECT_DIR"
    log "Prompt: $PROMPT_FILE"
    log "Logs: $LOG_DIR"

    check_branch
    check_prerequisites

    show_summary

    LOOP_COUNT=0

    while true; do
        LOOP_COUNT=$((LOOP_COUNT + 1))
        log ""
        log "════════════════════════════════════════════════════════════"
        log "Loop iteration: $LOOP_COUNT"
        log "Time: $(date)"
        log "════════════════════════════════════════════════════════════"

        log_phase "execution"

        # Run Legacy with BB5 context
        # The LEGACY.md will initialize run, read tasks, and execute
        log "Executing: cat LEGACY.md | claude -p --dangerously-skip-permissions"
        echo ""
        echo -e "${YELLOW}--- Legacy Output Start ---${NC}"
        echo ""

        if ! cat "$PROMPT_FILE" | claude -p --dangerously-skip-permissions 2>&1 | tee -a "$SESSION_LOG"; then
            EXIT_CODE=${PIPESTATUS[0]}
            echo ""
            echo -e "${YELLOW}--- Legacy Output End ---${NC}"
            echo ""
            log_error "Legacy execution failed with exit code $EXIT_CODE"

            if [ -n "$TELEMETRY_FILE" ]; then
                "$TELEMETRY_SCRIPT" phase execution "failed" "$TELEMETRY_FILE" 2>/dev/null || true
                "$TELEMETRY_SCRIPT" complete "failed" "$TELEMETRY_FILE" 2>/dev/null || true
            fi

            sleep 30
            continue
        fi

        echo ""
        echo -e "${YELLOW}--- Legacy Output End ---${NC}"
        echo ""

        # Capture the result for analysis
        RESULT=$(cat "$SESSION_LOG" | tail -100)

        if [ -n "$TELEMETRY_FILE" ]; then
            "$TELEMETRY_SCRIPT" phase execution "complete" "$TELEMETRY_FILE" 2>/dev/null || true
        fi

        # Check for completion
        if echo "$RESULT" | grep -q "<promise>COMPLETE</promise>"; then
            log_success "All tasks complete!"
            log "Legacy is done. Exiting loop."

            if [ -n "$TELEMETRY_FILE" ]; then
                "$TELEMETRY_SCRIPT" complete "success" "$TELEMETRY_FILE" 2>/dev/null || true
            fi

            show_summary
            exit 0
        fi

        # Check for blocked status
        if echo "$RESULT" | grep -q "Status: BLOCKED"; then
            log_error "Legacy is blocked. Check logs for details."
            log "Continuing in case blockers resolve..."

            if [ -n "$TELEMETRY_FILE" ]; then
                "$TELEMETRY_SCRIPT" event warning "Run blocked" "$TELEMETRY_FILE" 2>/dev/null || true
            fi
        fi

        # Check for partial completion
        if echo "$RESULT" | grep -q "Status: PARTIAL"; then
            log_warning "Task partially completed"

            if [ -n "$TELEMETRY_FILE" ]; then
                "$TELEMETRY_SCRIPT" event warning "Partial completion" "$TELEMETRY_FILE" 2>/dev/null || true
            fi
        fi

        # Brief pause between loops
        log "Waiting 10 seconds before next iteration..."
        sleep 10
    done
}

# Handle interrupts
trap 'log "Interrupted by user"; show_summary; exit 130' INT TERM

# Run
main "$@"
