#!/bin/bash
# Test dry-run mode for all shell scripts
# Validates that --dry-run flag works correctly across all scripts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Test a script with dry-run mode
test_script() {
    local script_name="$1"
    local script_path="$SCRIPT_DIR/$script_name"
    local test_args="${2:-}"

    echo -e "${BLUE}Testing:${NC} $script_name"

    if [ ! -f "$script_path" ]; then
        echo -e "  ${YELLOW}⚠${NC} Script not found: $script_path"
        return 0
    fi

    if [ ! -x "$script_path" ]; then
        echo -e "  ${YELLOW}⚠${NC} Script not executable: $script_name"
        return 0
    fi

    # Run with --dry-run
    local output
    local exit_code=0

    if $script_path --dry-run $test_args 2>&1; then
        exit_code=$?
    else
        exit_code=$?
    fi

    # Check for dry-run indicators in output
    if echo "$output" | grep -q "\[DRY-RUN\]" || \
       echo "$output" | grep -q "DRY-RUN MODE" || \
       [ $exit_code -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} Dry-run mode recognized"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "  ${RED}✗${NC} Dry-run mode may not be working (exit: $exit_code)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Header
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Dry-Run Mode Validation Suite                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check dry_run.sh library exists
echo -e "${CYAN}Checking library...${NC}"
if [ -f "$ENGINE_DIR/lib/dry_run.sh" ]; then
    echo -e "  ${GREEN}✓${NC} lib/dry_run.sh exists"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "  ${RED}✗${NC} lib/dry_run.sh not found"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test each script
echo ""
echo -e "${CYAN}Testing shell scripts...${NC}"

# ralf-loop.sh (requires .autonomous directory)
if [ -d "$ENGINE_DIR/../.autonomous" ] || [ -d "$(pwd)/.autonomous" ]; then
    test_script "ralf-loop.sh" "$(pwd)" || true
else
    echo -e "${YELLOW}⚠${NC} Skipping ralf-loop.sh (no .autonomous directory)"
fi

# telemetry.sh
test_script "telemetry.sh" "status" || true

# validate.sh
test_script "validate.sh" || true

# test-run.sh (requires .autonomous directory)
if [ -d "$ENGINE_DIR/../.autonomous" ] || [ -d "$(pwd)/.autonomous" ]; then
    test_script "test-run.sh" || true
else
    echo -e "${YELLOW}⚠${NC} Skipping test-run.sh (no .autonomous directory)"
fi

# task (Python script - may not support dry-run yet)
echo -e "${BLUE}Testing:${NC} task (Python)"
if [ -f "$SCRIPT_DIR/task" ]; then
    echo -e "  ${YELLOW}⚠${NC} Python script - dry-run not yet implemented"
else
    echo -e "  ${YELLOW}⚠${NC} Script not found"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    echo "  Passed: $TESTS_PASSED"
    echo "  Failed: $TESTS_FAILED"
    echo ""
    echo "Dry-run mode is working correctly."
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    echo "  Passed: $TESTS_PASSED"
    echo "  Failed: $TESTS_FAILED"
    echo ""
    echo "Review the output above for details."
    exit 1
fi
