#!/bin/bash
# view-logs.sh - View structured logs for Blackbox 5
# Usage: ./view-logs.sh [options]
#   --all       : Show all logs including debug
#   --tail      : Tail the log file (follow mode)
#   --json      : Output raw JSON (no formatting)
#   --today     : Only show today's logs (default)
#   N           : Show last N lines (default: 50)

set -e

# Configuration
LOG_DIR="blackbox5/logs"
LOG_FILE="$LOG_DIR/$(date +%Y-%m-%d).log"
DEFAULT_LINES=50

# Parse arguments
SHOW_DEBUG=false
TAIL_MODE=false
JSON_MODE=false
LINES=$DEFAULT_LINES

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            SHOW_DEBUG=true
            shift
            ;;
        --tail)
            TAIL_MODE=true
            shift
            ;;
        --json)
            JSON_MODE=true
            shift
            ;;
        --today)
            # Already default
            shift
            ;;
        [0-9]*)
            LINES=$1
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --all       Show all logs including debug"
            echo "  --tail      Tail the log file (follow mode)"
            echo "  --json      Output raw JSON (no formatting)"
            echo "  --today     Only show today's logs (default)"
            echo "  N           Show last N lines (default: 50)"
            echo "  -h, --help  Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h for help"
            exit 1
            ;;
    esac
done

# Check if log directory exists
if [ ! -d "$LOG_DIR" ]; then
    echo "Log directory not found: $LOG_DIR"
    echo "Logs will be created when the system runs."
    exit 1
fi

# Check if today's log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "No log file found for today: $LOG_FILE"
    echo ""
    echo "Available log files:"
    ls -1 "$LOG_DIR"/*.log 2>/dev/null | tail -5 || echo "  (none)"
    exit 1
fi

# Display header
echo "=============================================="
echo "Blackbox 5 Logs"
echo "=============================================="
echo "File: $LOG_FILE"
echo "Date: $(date +%Y-%m-%d)"
if [ "$SHOW_DEBUG" = false ]; then
    echo "Filter: Excluding DEBUG level"
fi
echo "=============================================="
echo ""

# Process logs based on mode
if [ "$JSON_MODE" = true ]; then
    # Raw JSON output
    if [ "$TAIL_MODE" = true ]; then
        tail -f "$LOG_FILE"
    else
        tail -n "$LINES" "$LOG_FILE"
    fi
elif command -v jq &> /dev/null; then
    # Pretty print JSON logs with jq
    if [ "$TAIL_MODE" = true ]; then
        tail -f "$LOG_FILE" | jq -r '
            if .level == "debug" then empty
            elif .event == "task.start" then
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): Task started - \(.task_description // "N/A")"
            elif .event == "task.progress" then
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): Task progress \(.progress // 0)% - \(.message // "")"
            elif .event == "task.success" then
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): Task completed successfully"
            elif .event == "task.failed" then
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): Task FAILED - \(.error // "Unknown error")"
            elif .event == "operation.start" then
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): Operation started - \(.description // "N/A")"
            elif .event == "operation.complete" then
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): Operation completed (\(.duration_seconds // "N/A")s)"
            elif .event == "operation.failed" then
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): Operation FAILED - \(.error // "Unknown error")"
            elif .event == "agent.task_decomposed" then
                "\(.timestamp) [\(.level | ascii_upcase)] Manager: Task decomposed into \(.subtasks // "N/A") subtasks"
            elif .event == "agent.subtask_assigned" then
                "\(.timestamp) [\(.level | ascii_upcase)] Manager: Subtask assigned to \(.specialist // "unknown")"
            else
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): \(.message // .event // "N/A")"
            end
        ' | grep -v "^$"
    else
        tail -n "$LINES" "$LOG_FILE" | jq -r '
            if .level == "debug" then empty
            elif .event == "task.start" then
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): Task started - \(.task_description // "N/A")"
            elif .event == "task.progress" then
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): Task progress \(.progress // 0)% - \(.message // "")"
            elif .event == "task.success" then
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): Task completed successfully"
            elif .event == "task.failed" then
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): Task FAILED - \(.error // "Unknown error")"
            elif .event == "operation.start" then
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): Operation started - \(.description // "N/A")"
            elif .event == "operation.complete" then
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): Operation completed (\(.duration_seconds // "N/A")s)"
            elif .event == "operation.failed" then
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): Operation FAILED - \(.error // "Unknown error")"
            elif .event == "agent.task_decomposed" then
                "\(.timestamp) [\(.level | ascii_upcase)] Manager: Task decomposed into \(.subtasks // "N/A") subtasks"
            elif .event == "agent.subtask_assigned" then
                "\(.timestamp) [\(.level | ascii_upcase)] Manager: Subtask assigned to \(.specialist // "unknown")"
            else
                "\(.timestamp) [\(.level | ascii_upcase)] \(.agent_type // "system"): \(.message // .event // "N/A")"
            end
        ' | grep -v "^$"
    fi
else
    # Fallback: grep for important events if jq is not available
    echo "Note: jq not found. Showing filtered log lines."
    echo "Install jq for better formatting: brew install jq (macOS) or apt install jq (Linux)"
    echo ""

    if [ "$TAIL_MODE" = true ]; then
        tail -f "$LOG_FILE" | grep -E "(task\.(start|progress|success|failed)|operation\.(start|complete|failed)|\"level\":\s*\"(info|warning|error)\")"
    else
        tail -n "$LINES" "$LOG_FILE" | grep -E "(task\.(start|progress|success|failed)|operation\.(start|complete|failed)|\"level\":\s*\"(info|warning|error)\")"
    fi
fi

echo ""
echo "=============================================="
