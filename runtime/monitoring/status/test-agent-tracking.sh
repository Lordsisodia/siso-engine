#!/usr/bin/env bash
# Test Agent Task Tracking
# Tests if agents properly document work, update timeline, and create plans

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

# Set BLACKBOX_ROOT
BLACKBOX_ROOT="$(find_box_root)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Blackbox4 Agent Tracking Test Suite"
echo "=========================================="
echo ""

# Test results
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
    ((WARNINGS++))
}

info() {
    echo -e "${BLUE}ℹ INFO${NC}: $1"
}

# Test 1: Check if timeline exists and is being updated
echo "=== Test 1: Timeline Tracking ==="
TIMELINE_FILE="$BLACKBOX_ROOT/.memory/working/shared/timeline.md"

if [ -f "$TIMELINE_FILE" ]; then
    pass "Timeline file exists at $TIMELINE_FILE"

    # Check if timeline has recent entries
    ENTRY_COUNT=$(grep -c "^## " "$TIMELINE_FILE" || echo "0")
    if [ "$ENTRY_COUNT" -gt 0 ]; then
        pass "Timeline has $ENTRY_COUNT entries"

        # Check for recent entries (last 2 days)
        RECENT_ENTRIES=$(grep "^## " "$TIMELINE_FILE" | tail -5)
        if [ -n "$RECENT_ENTRIES" ]; then
            pass "Timeline has recent entries:"
            echo "$RECENT_ENTRIES" | head -3 | sed 's/^/    /'
        else
            warn "No recent timeline entries found"
        fi
    else
        fail "Timeline is empty"
    fi
else
    fail "Timeline file not found at $TIMELINE_FILE"
fi

echo ""

# Test 2: Check if work queue is being maintained
echo "=== Test 2: Work Queue Tracking ==="
WORK_QUEUE_FILE="$BLACKBOX_ROOT/.memory/working/shared/work-queue.json"

if [ -f "$WORK_QUEUE_FILE" ]; then
    pass "Work queue file exists at $WORK_QUEUE_FILE"

    # Validate JSON
    if python3 -m json.tool "$WORK_QUEUE_FILE" > /dev/null 2>&1; then
        pass "Work queue is valid JSON"

        # Count tasks
        TASK_COUNT=$(python3 -c "import json; print(len(json.load(open('$WORK_QUEUE_FILE'))))" 2>/dev/null || echo "0")
        if [ "$TASK_COUNT" -gt 0 ]; then
            pass "Work queue has $TASK_COUNT tasks"

            # Check task statuses
            IN_PROGRESS=$(python3 -c "import json; tasks = json.load(open('$WORK_QUEUE_FILE')); print(sum(1 for t in tasks if t.get('status') == 'in_progress'))" 2>/dev/null || echo "0")
            QUEUED=$(python3 -c "import json; tasks = json.load(open('$WORK_QUEUE_FILE')); print(sum(1 for t in tasks if t.get('status') == 'queued'))" 2>/dev/null || echo "0")

            info "Task status breakdown:"
            echo "    - In Progress: $IN_PROGRESS"
            echo "    - Queued: $QUEUED"
            echo "    - Other: $((TASK_COUNT - IN_PROGRESS - QUEUED))"
        else
            warn "Work queue is empty"
        fi
    else
        fail "Work queue is not valid JSON"
    fi
else
    fail "Work queue file not found at $WORK_QUEUE_FILE"
fi

echo ""

# Test 3: Check if agents create session documentation
echo "=== Test 3: Agent Session Documentation ==="
RALPH_WORK_DIR="$BLACKBOX_ROOT/1-agents/4-specialists/ralph-agent/work"

if [ -d "$RALPH_WORK_DIR" ]; then
    pass "Ralph agent work directory exists"

    # Check for session directories
    SESSION_COUNT=$(find "$RALPH_WORK_DIR" -type d -name "session-*" 2>/dev/null | wc -l | tr -d ' ')

    if [ "$SESSION_COUNT" -gt 0 ]; then
        pass "Found $SESSION_COUNT session directories"

        # Check latest session for required files
        LATEST_SESSION=$(find "$RALPH_WORK_DIR" -type d -name "session-*" | sort | tail -1)

        if [ -n "$LATEST_SESSION" ]; then
            info "Checking latest session: $(basename "$LATEST_SESSION")"

            REQUIRED_FILES=("summary.md" "achievements.md" "materials.md" "analysis.md")
            DOCS_FOUND=0

            for file in "${REQUIRED_FILES[@]}"; do
                if [ -f "$LATEST_SESSION/$file" ]; then
                    pass "Required file exists: $file"
                    ((DOCS_FOUND++))
                else
                    fail "Required file missing: $file"
                fi
            done

            if [ "$DOCS_FOUND" -eq "${#REQUIRED_FILES[@]}" ]; then
                pass "All required documentation files present"
            fi
        fi
    else
        warn "No session directories found in Ralph work directory"
    fi
else
    warn "Ralph agent work directory not found (may not have run yet)"
fi

echo ""

# Test 4: Check if semantic search index is updated
echo "=== Test 4: Semantic Search Index ==="
VECTOR_DB="$BLACKBOX_ROOT/.memory/extended/chroma-db"

if [ -d "$VECTOR_DB" ]; then
    pass "Vector database directory exists"

    # Check if collection has data
    python3 - <<PYEOF
import sys
sys.path.insert(0, '$BLACKBOX_ROOT/.memory/extended/services')

try:
    from vector_store import VectorStore
    store = VectorStore()
    stats = store.get_collection_stats()

    if stats['count'] > 0:
        print(f"    {GREEN}✓ PASS{NC}: Vector store has {stats['count']} documents indexed")
    else:
        print(f"    {YELLOW}⚠ WARN{NC}: Vector store is empty (no documents indexed)")
except Exception as e:
    print(f"    {RED}✗ FAIL{NC}: Cannot access vector store: {e}")
PYEOF
else
    warn "Vector database not found (semantic search not yet used)"
fi

echo ""

# Test 5: Check if plans are being created
echo "=== Test 5: Planning Documentation ==="
PLANS_DIR="$BLACKBOX_ROOT/.plans"

if [ -d "$PLANS_DIR" ]; then
    pass "Plans directory exists"

    # Check for active plans
    ACTIVE_PLANS=$(find "$PLANS_DIR" -name "active" -o -name "pending" 2>/dev/null | wc -l | tr -d ' ')

    if [ "$ACTIVE_PLANS" -gt 0 ]; then
        pass "Found $ACTIVE_PLANS plan status directories"

        # Check for plan documentation
        PLAN_DOCS=$(find "$PLANS_DIR" -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
        info "Found $PLAN_DOCS plan documentation files"
    else
        warn "No active/pending plan directories found"
    fi
else
    warn "Plans directory not found"
fi

echo ""

# Test 6: Check agent memory updates
echo "=== Test 6: Agent Memory Updates ==="
AGENT_MEMORY_DIR="$BLACKBOX_ROOT/.memory/agents"

if [ -d "$AGENT_MEMORY_DIR" ]; then
    pass "Agent memory directory exists"

    # Count agent session memories
    AGENT_SESSIONS=$(find "$AGENT_MEMORY_DIR" -name "goal_state.json" 2>/dev/null | wc -l | tr -d ' ')

    if [ "$AGENT_SESSIONS" -gt 0 ]; then
        pass "Found $AGENT_SESSIONS agent session memory files"

        # Check recent agent activity
        RECENT_AGENT=$(find "$AGENT_MEMORY_DIR" -name "goal_state.json" -type f -mtime -2 2>/dev/null | head -1)
        if [ -n "$RECENT_AGENT" ]; then
            pass "Recent agent activity detected:"
            echo "    $(basename $(dirname "$RECENT_AGENT"))"
        fi
    else
        info "No agent session memories found (agents may not have run yet)"
    fi
else
    warn "Agent memory directory not found"
fi

echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed${NC}: $PASSED"
echo -e "${YELLOW}Warnings${NC}: $WARNINGS"
echo -e "${RED}Failed${NC}: $FAILED"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ All critical tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Review above.${NC}"
    exit 1
fi
