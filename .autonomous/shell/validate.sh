#!/bin/bash
# Pre-flight validation for Legacy
#
# Usage: ./validate.sh [--dry-run] [--verbose]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source dry-run library
source "$SCRIPT_DIR/../lib/dry_run.sh"

# Initialize dry-run mode and get remaining args
REMAINING_ARGS=$(dry_run_init "$@")
set -- $REMAINING_ARGS

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

check() {
    local name="$1"
    local condition="$2"
    local required="$3"

    if eval "$condition"; then
        echo -e "${GREEN}✓${NC} $name"
        return 0
    else
        if [ "$required" = "required" ]; then
            echo -e "${RED}✗${NC} $name (REQUIRED)"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "${YELLOW}⚠${NC} $name (optional)"
            WARNINGS=$((WARNINGS + 1))
        fi
        return 1
    fi
}

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Legacy Pre-Flight Check                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if dry_run_is_active; then
    echo -e "${YELLOW}[DRY-RUN MODE]${NC} Validating without making changes"
    echo ""
fi

echo -e "${BLUE}Environment:${NC}"
check "Running on macOS/Linux" "[ $(uname) = 'Darwin' ] || [ $(uname) = 'Linux' ]" "required"
check "Bash version >= 4.0" "[ ${BASH_VERSINFO[0]} -ge 4 ]" "optional"

echo ""
echo -e "${BLUE}Dependencies:${NC}"
check "claude CLI installed" "command -v claude &> /dev/null" "required"
check "git available" "command -v git &> /dev/null" "required"
check "jq available (for telemetry)" "command -v jq &> /dev/null" "optional"

echo ""
echo -e "${BLUE}Project Structure:${NC}"
check ".Autonomous directory exists" "[ -d '$PROJECT_DIR/.Autonomous' ]" "required"
check "LEGACY.md exists" "[ -f '$PROJECT_DIR/.Autonomous/LEGACY.md' ]" "required"
check "legacy-loop.sh exists" "[ -f '$PROJECT_DIR/.Autonomous/legacy-loop.sh' ]" "required"
check "telemetry.sh exists" "[ -f '$PROJECT_DIR/.Autonomous/telemetry.sh' ]" "optional"
check "tasks/active/ exists" "[ -d '$PROJECT_DIR/.Autonomous/tasks/active' ]" "required"
check "runs/ exists" "[ -d '$PROJECT_DIR/.Autonomous/runs' ]" "optional"
check ".docs/ exists" "[ -d '$PROJECT_DIR/.Autonomous/.docs' ]" "optional"
check "LOGS/ exists" "[ -d '$PROJECT_DIR/.Autonomous/LOGS' ]" "optional"

echo ""
echo -e "${BLUE}Prompt Components:${NC}"
check "prompts/system/identity.md" "[ -f '$PROJECT_DIR/.Autonomous/prompts/system/identity.md' ]" "required"
check "prompts/context/bb5-infrastructure.md" "[ -f '$PROJECT_DIR/.Autonomous/prompts/context/bb5-infrastructure.md' ]" "required"
check "prompts/context/branch-safety.md" "[ -f '$PROJECT_DIR/.Autonomous/prompts/context/branch-safety.md' ]" "required"
check "prompts/context/project-specific.md" "[ -f '$PROJECT_DIR/.Autonomous/prompts/context/project-specific.md' ]" "required"
check "prompts/procedures/task-selection.md" "[ -f '$PROJECT_DIR/.Autonomous/prompts/procedures/task-selection.md' ]" "required"
check "prompts/procedures/execution-protocol.md" "[ -f '$PROJECT_DIR/.Autonomous/prompts/procedures/execution-protocol.md' ]" "required"

echo ""
echo -e "${BLUE}Git Status:${NC}"
dry_run_cd "$PROJECT_DIR"
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
check "Git repository initialized" "[ -d '$PROJECT_DIR/.git' ]" "required"
check "Not on main/master branch" "[ '$CURRENT_BRANCH' != 'main' ] && [ '$CURRENT_BRANCH' != 'master' ]" "required"

echo "  Current branch: $CURRENT_BRANCH"

echo ""
echo -e "${BLUE}Active Tasks:${NC}"
ACTIVE_COUNT=$(find "$PROJECT_DIR/.Autonomous/tasks/active" -name "*.md" -type f ! -name "index.md" ! -name "TEMPLATE.md" 2>/dev/null | wc -l)
if [ "$ACTIVE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Found $ACTIVE_COUNT active task(s)"
    find "$PROJECT_DIR/.Autonomous/tasks/active" -name "*.md" -type f ! -name "index.md" ! -name "TEMPLATE.md" 2>/dev/null | while read -r task; do
        TASK_NAME=$(basename "$task" .md)
        echo "    - $TASK_NAME"
    done
else
    echo -e "${YELLOW}⚠${NC} No active tasks found"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}VALIDATION FAILED${NC}"
    echo "  Errors: $ERRORS"
    echo "  Warnings: $WARNINGS"
    echo ""
    echo "Fix the errors above before running Legacy."
    dry_run_summary
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}VALIDATION PASSED WITH WARNINGS${NC}"
    echo "  Errors: $ERRORS"
    echo "  Warnings: $WARNINGS"
    echo ""
    echo "Legacy can run, but some features may be limited."
    dry_run_summary
    exit 0
else
    echo -e "${GREEN}VALIDATION PASSED${NC}"
    echo "  All checks passed. Legacy is ready to run."
    echo ""
    echo "Start with: ./.Autonomous/legacy-loop.sh"
    dry_run_summary
    exit 0
fi
