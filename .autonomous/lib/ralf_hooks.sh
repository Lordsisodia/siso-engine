#!/bin/bash
# RALF Hooks - Post-execution analysis and feedback
# Source this from ralf-loop.sh to enable automatic log ingestion

RALF_HOOKS_VERSION="1.0.0"

# Colors
HOOK_RED='\033[0;31m'
HOOK_GREEN='\033[0;32m'
HOOK_YELLOW='\033[1;33m'
HOOK_BLUE='\033[0;34m'
HOOK_CYAN='\033[0;36m'
HOOK_NC='\033[0m'

# Paths
HOOK_BLACKBOX5_DIR="${RALF_BLACKBOX5_DIR:-/Users/shaansisodia/.blackbox5}"
HOOK_ENGINE_DIR="${RALF_ENGINE_DIR:-$HOOK_BLACKBOX5_DIR/2-engine/.autonomous}"
HOOK_LOG_INGESTOR="$HOOK_ENGINE_DIR/lib/log_ingestor.py"
HOOK_KNOWLEDGE_DIR="$HOOK_BLACKBOX5_DIR/5-project-memory/blackbox5/knowledge/ralf-patterns"

# Hook: Called after each RALF loop completes
ralf_hook_post_loop() {
    local loop_num="$1"
    local session_log="$2"
    local exit_code="${3:-0}"

    echo ""
    echo -e "${HOOK_CYAN}[RALF Hook] Post-loop analysis...${HOOK_NC}"

    # Run log ingestor
    if [ -f "$HOOK_LOG_INGESTOR" ]; then
        local insights
        insights=$(python3 "$HOOK_LOG_INGESTOR" --limit 5 --json 2>/dev/null)

        if [ -n "$insights" ]; then
            local success_rate
            success_rate=$(echo "$insights" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success_rate', 0))")

            echo -e "${HOOK_BLUE}  Success rate (last 5 loops): ${success_rate}%${HOOK_NC}"

            # Alert on low success rate
            if [ "${success_rate%.*}" -lt 50 ]; then
                echo -e "${HOOK_RED}  ⚠ Low success rate detected${HOOK_NC}"
            fi
        fi
    fi

    # Extract key learnings from session log
    if [ -f "$session_log" ]; then
        local errors
        errors=$(grep -c "ERROR\|✗" "$session_log" 2>/dev/null || echo "0")

        if [ "$errors" -gt 0 ]; then
            echo -e "${HOOK_YELLOW}  Errors in session: $errors${HOOK_NC}"
        fi
    fi

    echo -e "${HOOK_GREEN}  ✓ Hook complete${HOOK_NC}"
}

# Hook: Called when RALF detects a failure pattern
ralf_hook_pattern_detected() {
    local pattern_type="$1"
    local context="$2"

    echo -e "${HOOK_YELLOW}[RALF Hook] Pattern detected: $pattern_type${HOOK_NC}"

    # Log to pattern registry
    local pattern_file="$HOOK_KNOWLEDGE_DIR/detected-patterns.jsonl"
    mkdir -p "$(dirname "$pattern_file")"

    printf '{"timestamp":"%s","pattern":"%s","context":%s}\n' \
        "$(date -Iseconds)" \
        "$pattern_type" \
        "$(echo "$context" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" \
        >> "$pattern_file"
}

# Hook: Generate prompt enhancement recommendations
ralf_hook_generate_recommendations() {
    echo ""
    echo -e "${HOOK_CYAN}[RALF Hook] Generating recommendations...${HOOK_NC}"

    if [ -f "$HOOK_LOG_INGESTOR" ]; then
        local enhancements
        enhancements=$(python3 "$HOOK_LOG_INGESTOR" --prompt-enhancements 2>/dev/null)

        if [ -n "$enhancements" ]; then
            echo -e "${HOOK_YELLOW}Suggested prompt enhancements:${HOOK_NC}"
            echo "$enhancements" | sed 's/^/  /'
        fi
    fi
}

# Export hook functions
export -f ralf_hook_post_loop
export -f ralf_hook_pattern_detected
export -f ralf_hook_generate_recommendations
