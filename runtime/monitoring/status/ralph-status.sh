#!/bin/bash
#
# Quick Ralph status check
# Shows current Ralph state and recent activity
#

BB4_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RALPH_DIR="$BB4_ROOT/.runtime/.ralph"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Ralph Status ===${NC}"
echo

# Check if Ralph is running
if [[ -f "$RALPH_DIR/pid" ]]; then
    pid=$(cat "$RALPH_DIR/pid")
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${GREEN}● Ralph is running${NC} (PID: $pid)"
    else
        echo -e "${YELLOW}○ Ralph stopped (stale PID file)${NC}"
    fi
else
    echo -e "${RED}○ Ralph is not running${NC}"
fi
echo

# Show state
if [[ -f "$RALPH_DIR/state.json" ]]; then
    state=$(jq -r '.state // "unknown"' "$RALPH_DIR/state.json" 2>/dev/null)
    echo "State: $state"
fi

# Show current PRD
if [[ -f "$RALPH_DIR/prd.json" ]]; then
    prd=$(jq -r '.title // "No PRD"' "$RALPH_DIR/prd.json" 2>/dev/null | head -1)
    echo "Current PRD: $prd"
fi
echo

# Show recent runs
if [[ -d "$RALPH_DIR/runs" ]]; then
    echo "Recent runs:"
    find "$RALPH_DIR/runs" -name "run-*.json" -type f -printf '%T@ %p\n' 2>/dev/null | \
        sort -rn | head -3 | while read -r timestamp file; do
        run_id=$(basename "$file" .json)
        status=$(jq -r '.status // "unknown"' "$file" 2>/dev/null)
        echo "  - $run_id ($status)"
    done
fi

echo
echo "For full dashboard: .monitoring/dashboard.sh"
