#!/bin/bash
# Telemetry and monitoring for Legacy runs
# Tracks performance, errors, and system health
#
# Usage: ./telemetry.sh [--dry-run] [--verbose] {init|event|phase|metric|complete|status|watch}

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source dry-run library
source "$SCRIPT_DIR/../lib/dry_run.sh"

# Initialize dry-run mode and get remaining args
REMAINING_ARGS=$(dry_run_init "$@")
set -- $REMAINING_ARGS

TELEMETRY_DIR="$PROJECT_DIR/.Autonomous/telemetry"
CURRENT_RUN_DIR=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Initialize telemetry
init_telemetry() {
    dry_run_mkdir "$TELEMETRY_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    TELEMETRY_FILE="$TELEMETRY_DIR/run-$TIMESTAMP.json"

    local json_content="{
  \"run_id\": \"$TIMESTAMP\",
  \"start_time\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
  \"status\": \"starting\",
  \"events\": [],
  \"metrics\": {
    \"files_read\": 0,
    \"files_written\": 0,
    \"commands_executed\": 0,
    \"errors\": 0,
    \"warnings\": 0
  },
  \"phases\": {
    \"initialization\": \"pending\",
    \"task_selection\": \"pending\",
    \"execution\": \"pending\",
    \"documentation\": \"pending\",
    \"completion\": \"pending\"
  }
}"

    if dry_run_is_active; then
        dry_run_echo "Create telemetry file: $TELEMETRY_FILE"
        if dry_run_is_verbose; then
            echo "$json_content"
        fi
    else
        echo "$json_content" > "$TELEMETRY_FILE"
    fi

    echo "$TELEMETRY_FILE"
}

# Log an event
log_event() {
    local type="$1"
    local message="$2"
    local file="$3"

    if [ -z "$file" ]; then
        file=$(ls -t "$TELEMETRY_DIR"/run-*.json 2>/dev/null | head -1)
    fi

    if [ -f "$file" ]; then
        local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
        local event="{\"time\": \"$timestamp\", \"type\": \"$type\", \"message\": \"$message\"}"

        if dry_run_is_active; then
            dry_run_echo "Log event [$type]: $message"
            dry_run_echo "Update metric: $type += 1"
        else
            # Update metrics based on type
            case "$type" in
                "error")
                    jq '.metrics.errors += 1' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
                    echo -e "${RED}[ERROR]${NC} $message"
                    ;;
                "warning")
                    jq '.metrics.warnings += 1' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
                    echo -e "${YELLOW}[WARN]${NC} $message"
                    ;;
                "success")
                    echo -e "${GREEN}[OK]${NC} $message"
                    ;;
                "info")
                    echo -e "${BLUE}[INFO]${NC} $message"
                    ;;
                "phase")
                    echo -e "${CYAN}[PHASE]${NC} $message"
                    ;;
            esac

            # Add event to array
            jq ".events += [$event]" "$file" > "$file.tmp" && mv "$file.tmp" "$file"
        fi
    fi
}

# Update phase status
update_phase() {
    local phase="$1"
    local status="$2"
    local file=$(ls -t "$TELEMETRY_DIR"/run-*.json 2>/dev/null | head -1)

    if [ -f "$file" ]; then
        if dry_run_is_active; then
            dry_run_echo "Update phase '$phase' to status: $status"
        else
            jq ".phases.$phase = \"$status\"" "$file" > "$file.tmp" && mv "$file.tmp" "$file"
            log_event "phase" "Phase '$phase' is now $status" "$file"
        fi
    fi
}

# Increment metric
increment_metric() {
    local metric="$1"
    local file=$(ls -t "$TELEMETRY_DIR"/run-*.json 2>/dev/null | head -1)

    if [ -f "$file" ]; then
        if dry_run_is_active; then
            dry_run_echo "Increment metric: $metric += 1"
        else
            jq ".metrics.$metric += 1" "$file" > "$file.tmp" && mv "$file.tmp" "$file"
        fi
    fi
}

# Mark run complete
complete_run() {
    local status="$1"
    local file=$(ls -t "$TELEMETRY_DIR"/run-*.json 2>/dev/null | head -1)

    if [ -f "$file" ]; then
        if dry_run_is_active; then
            dry_run_echo "Mark run complete with status: $status"
            dry_run_echo "Set end_time to: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        else
            jq ".status = \"$status\" | .end_time = \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"" "$file" > "$file.tmp" && mv "$file.tmp" "$file"
            log_event "info" "Run completed with status: $status" "$file"
        fi
    fi
}

# Display current status
show_status() {
    local file=$(ls -t "$TELEMETRY_DIR"/run-*.json 2>/dev/null | head -1)

    if dry_run_is_active; then
        dry_run_echo "Display telemetry status"
        if [ -f "$file" ]; then
            dry_run_echo "Read from: $file"
        else
            dry_run_echo "No telemetry file found"
        fi
        return 0
    fi

    if [ -f "$file" ]; then
        echo ""
        echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
        echo -e "${CYAN}  Legacy Telemetry${NC}"
        echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
        echo ""

        # Show phases
        echo -e "${BLUE}Phases:${NC}"
        jq -r '.phases | to_entries[] | "  \(.key): \(.value)"' "$file" | while read line; do
            if echo "$line" | grep -q "complete"; then
                echo -e "  ${GREEN}✓${NC} $line"
            elif echo "$line" | grep -q "in_progress"; then
                echo -e "  ${YELLOW}▶${NC} $line"
            elif echo "$line" | grep -q "failed"; then
                echo -e "  ${RED}✗${NC} $line"
            else
                echo -e "  ${BLUE}○${NC} $line"
            fi
        done

        echo ""
        echo -e "${BLUE}Metrics:${NC}"
        jq -r '.metrics | to_entries[] | "  \(.key): \(.value)"' "$file"

        echo ""
        echo -e "${BLUE}Recent Events:${NC}"
        jq -r '.events[-5:] | .[] | "  [\(.type)] \(.message)"' "$file" 2>/dev/null || echo "  No events yet"

        echo ""
    fi
}

# Watch mode - continuous monitoring
watch_mode() {
    if dry_run_is_active; then
        dry_run_echo "Start watch mode (would refresh every 5 seconds)"
        return 0
    fi

    while true; do
        clear
        show_status
        sleep 5
    done
}

# Command dispatch
case "$1" in
    init)
        init_telemetry
        ;;
    event)
        log_event "$2" "$3"
        ;;
    phase)
        update_phase "$2" "$3"
        ;;
    metric)
        increment_metric "$2"
        ;;
    complete)
        complete_run "$2"
        ;;
    status)
        show_status
        ;;
    watch)
        watch_mode
        ;;
    *)
        echo "Usage: $0 [--dry-run] [--verbose] {init|event|phase|metric|complete|status|watch}"
        echo ""
        echo "Commands:"
        echo "  init              - Initialize telemetry for new run"
        echo "  event <type> <msg> - Log an event (error|warning|success|info)"
        echo "  phase <name> <status> - Update phase status"
        echo "  metric <name>     - Increment a metric"
        echo "  complete <status> - Mark run complete"
        echo "  status            - Show current status"
        echo "  watch             - Continuous monitoring"
        echo ""
        echo "Options:"
        echo "  --dry-run         - Show what would be done without making changes"
        echo "  --verbose, -v     - Show detailed output in dry-run mode"
        ;;
esac

# Print dry-run summary
dry_run_summary
