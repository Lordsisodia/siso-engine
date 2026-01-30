#!/bin/bash
# Test run for Legacy - Single iteration with visible output
# Run this from the project root: ./blackbox5/5-project-memory/siso-internal/.Autonomous/test-run.sh
#
# Usage: ./test-run.sh [--dry-run] [--verbose]

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source dry-run library
source "$SCRIPT_DIR/../lib/dry_run.sh"

# Initialize dry-run mode and get remaining args
REMAINING_ARGS=$(dry_run_init "$@")
set -- $REMAINING_ARGS

# Configuration
PROMPT_FILE="$SCRIPT_DIR/LEGACY.md"
LOG_DIR="$SCRIPT_DIR/LOGS"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SESSION_LOG="$LOG_DIR/test-run-$TIMESTAMP.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log() {
    if dry_run_is_active; then
        echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
    else
        echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$SESSION_LOG"
    fi
}

log_section() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Check we're in the right place
if [[ ! -f "$PROMPT_FILE" ]]; then
    echo -e "${RED}ERROR: Cannot find LEGACY.md at $PROMPT_FILE${NC}"
    echo "Make sure you're running from the project root"
    exit 1
fi

# Check branch
dry_run_cd "$PROJECT_DIR"
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
log "Current branch: $CURRENT_BRANCH"

if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
    echo -e "${RED}ERROR: Cannot run on $CURRENT_BRANCH branch${NC}"
    exit 1
fi

log_section "LEGACY TEST RUN"
log "Project: $PROJECT_DIR"
log "Prompt: $PROMPT_FILE"
log "Log: $SESSION_LOG"
log "Working directory: $(pwd)"

if ! dry_run_is_active; then
    echo ""
    echo -e "${YELLOW}Legacy will analyze the Blackbox5 system${NC}"
    echo -e "${YELLOW}Starting in 3 seconds...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to cancel${NC}"
    sleep 3
fi

# Create log directory
dry_run_mkdir "$LOG_DIR"

# Run Legacy with visible output
log "Executing Legacy..."
echo ""
echo -e "${CYAN}--- LEGACY OUTPUT START ---${NC}"
echo ""

# Use claude-code with the prompt, running from project root
if dry_run_is_active; then
    dry_run_echo "Execute claude/claude-code with LEGACY.md prompt"
    dry_run_echo "Output would be logged to: $SESSION_LOG"
    EXIT_CODE=0
elif command -v claude &> /dev/null; then
    cd "$PROJECT_DIR" && cat "$PROMPT_FILE" | claude -p --dangerously-skip-permissions 2>&1 | tee -a "$SESSION_LOG"
    EXIT_CODE=${PIPESTATUS[0]}
elif command -v claude-code &> /dev/null; then
    cd "$PROJECT_DIR" && cat "$PROMPT_FILE" | claude-code -p --dangerously-skip-permissions 2>&1 | tee -a "$SESSION_LOG"
    EXIT_CODE=${PIPESTATUS[0]}
else
    echo -e "${RED}ERROR: Neither 'claude' nor 'claude-code' found in PATH${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}--- LEGACY OUTPUT END ---${NC}"
echo ""

log "Exit code: $EXIT_CODE"
log "Log saved to: $SESSION_LOG"

echo ""
if dry_run_is_active; then
    echo -e "${GREEN}Dry-run complete!${NC}"
else
    echo -e "${GREEN}Test run complete!${NC}"
fi
echo ""
echo "To view the run folder created:"
echo "  ls -la $SCRIPT_DIR/runs/ | tail -5"
echo ""
echo "To view documentation created:"
echo "  ls -la $SCRIPT_DIR/.docs/"
echo ""

if ! dry_run_is_active; then
    echo "To watch logs in real-time (another terminal):"
    echo "  tail -f $SESSION_LOG"
    echo ""
fi

# Print dry-run summary
dry_run_summary

exit $EXIT_CODE
