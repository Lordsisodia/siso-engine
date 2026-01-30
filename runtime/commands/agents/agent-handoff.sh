#!/usr/bin/env bash
#
# Agent Handoff Script
# Facilitates clean handoffs between agents with context preservation
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SHARED_MEMORY="$PROJECT_ROOT/runtime/shared_memory.py"
HANDOFF_DIR="$PROJECT_ROOT/.memory/handoffs"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create handoff directory
mkdir -p "$HANDOFF_DIR"

# Handoff function
handoff() {
    local from_agent="$1"
    local to_agent="$2"
    local context_dir="$3"
    local message="${4:-Handing off work}"

    log_info "Handoff: $from_agent -> $to_agent"
    log_debug "Context: $context_dir"
    log_debug "Message: $message"

    # Create handoff package
    local handoff_id
    handoff_id="$(date +%Y%m%d%H%M%S)-${from_agent}-to-${to_agent}"
    local handoff_file="$HANDOFF_DIR/${handoff_id}.json"

    # Gather context
    local context_data
    context_data=$(cat << EOF
{
  "handoff_id": "$handoff_id",
  "from_agent": "$from_agent",
  "to_agent": "$to_agent",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "message": "$message",
  "context_directory": "$context_dir"
}
EOF
)

    # Add context directory contents if exists
    if [[ -d "$context_dir" ]]; then
        log_info "Capturing context from $context_dir"

        # Get file list
        local files
        files=$(find "$context_dir" -type f 2>/dev/null || true)

        if [[ -n "$files" ]]; then
            # Add file info
            local file_info
            file_info=$(echo "$files" | while read -r file; do
                local tokens
                tokens=$(python3 "$PROJECT_ROOT/4-scripts/utils/token-count.py" "$file" 2>/dev/null || echo "0")
                echo "{\"path\": \"$file\", \"tokens\": $tokens},"
            done | sed '$ s/,$//')

            context_data=$(echo "$context_data" | jq --argjson files "[$file_info]" '. + {"context_files": $files}')
        fi
    fi

    # Save handoff package
    echo "$context_data" | jq '.' > "$handoff_file"

    log_info "Handoff package created: $handoff_file"

    # Update shared memory
    if [[ -f "$SHARED_MEMORY" ]]; then
        log_debug "Updating shared memory..."
        python3 "$SHARED_MEMORY" \
            --agent-id "$from_agent" \
            --update "handoff" "{\"type\": \"handoff\", \"to\": \"$to_agent\", \"handoff_id\": \"$handoff_id\"}" \
            2>/dev/null || true
    fi

    # Unregister from agent
    if [[ -f "$SHARED_MEMORY" ]]; then
        python3 "$SHARED_MEMORY" --agent-id "$from_agent" --unregister 2>/dev/null || true
    fi

    log_info "Handoff complete!"
    echo ""
    echo "Next agent ($to_agent) should load context from:"
    echo "  $handoff_file"
}

# Load handoff
load_handoff() {
    local agent_id="$1"
    local handoff_file="$2"

    log_info "Loading handoff for $agent_id"

    if [[ ! -f "$handoff_file" ]]; then
        log_error "Handoff file not found: $handoff_file"
        exit 1
    fi

    # Parse handoff
    local from_agent
    local message
    local context_dir

    from_agent=$(jq -r '.from_agent' "$handoff_file")
    message=$(jq -r '.message' "$handoff_file")
    context_dir=$(jq -r '.context_directory' "$handoff_file")

    log_info "Received from: $from_agent"
    log_info "Message: $message"
    log_info "Context: $context_dir"

    # Register new agent
    if [[ -f "$SHARED_MEMORY" ]]; then
        log_debug "Registering with shared memory..."
        python3 "$SHARED_MEMORY" \
            --agent-id "$agent_id" \
            --register \
            2>/dev/null || true
    fi

    # Show context files
    local context_files
    context_files=$(jq -r '.context_files[]?.path // empty' "$handoff_file")

    if [[ -n "$context_files" ]]; then
        echo ""
        echo "Context files:"
        echo "$context_files" | while read -r file; do
            echo "  - $file"
        done
    fi

    log_info "Handoff loaded successfully!"
}

# List handoffs
list_handoffs() {
    log_info "Handoff history:"
    echo ""

    if [[ ! -d "$HANDOFF_DIR" ]] || [[ -z "$(ls -A "$HANDOFF_DIR" 2>/dev/null)" ]]; then
        log_warn "No handoffs found"
        return
    fi

    for handoff_file in "$HANDOFF_DIR"/*.json; do
        if [[ -f "$handoff_file" ]]; then
            local timestamp
            local from_agent
            local to_agent

            timestamp=$(jq -r '.timestamp' "$handoff_file")
            from_agent=$(jq -r '.from_agent' "$handoff_file")
            to_agent=$(jq -r '.to_agent' "$handoff_file")

            echo "  $timestamp: $from_agent -> $to_agent"
            echo "    File: $handoff_file"
        fi
    done
}

# Show help
show_help() {
    cat << EOF
Agent Handoff Script

Usage: $0 <command> [args]

Commands:
  handoff <from> <to> <context_dir> [message]
                      Handoff from one agent to another
  load <agent_id> <handoff_file>
                      Load a handoff
  list                List handoff history

Examples:
  $0 handoff agent-1 agent-2 .plans/active/context "Design complete, starting implementation"
  $0 load agent-2 .memory/handoffs/20240101120000-agent-1-to-agent-2.json
  $0 list
EOF
}

# Main
main() {
    local command="${1:-help}"

    case "$command" in
        handoff)
            if [[ $# -lt 4 ]]; then
                log_error "Usage: $0 handoff <from> <to> <context_dir> [message]"
                exit 1
            fi
            handoff "$2" "$3" "$4" "${5:-}"
            ;;
        load)
            if [[ $# -lt 3 ]]; then
                log_error "Usage: $0 load <agent_id> <handoff_file>"
                exit 1
            fi
            load_handoff "$2" "$3"
            ;;
        list)
            list_handoffs
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
