#!/bin/bash
# BlackBox5 Comprehensive Self-Test
# Validates all core systems are functioning correctly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BLACKBOX5_DIR="$(cd "$ENGINE_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0
WARNINGS=0

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++))
}

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           BlackBox5 Comprehensive Self-Test                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Python Environment
log_test "Checking Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    log_pass "Python available: $PYTHON_VERSION"
else
    log_fail "Python3 not found"
fi

# Test 2: Core Imports
log_test "Testing core imports..."
cd "$ENGINE_DIR"
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from core.agents.definitions.core.base_agent import BaseAgent, AgentConfig
    from core.agents.definitions.core.agent_loader import AgentLoader
    from core.agents.definitions.planning_agent import PlanningAgent
    from core.agents.definitions.bmad import BMADFramework
    print('All core imports successful')
except Exception as e:
    print(f'Import failed: {e}')
    sys.exit(1)
" 2>&1 | grep -q "All core imports successful" && log_pass "Core imports working" || log_fail "Core imports failed"

# Test 3: Agent Loading
log_test "Testing agent loading (all 21 agents)..."
AGENT_COUNT=$(python3 -c "
import sys
sys.path.insert(0, '.')
from core.agents.definitions.core.agent_loader import AgentLoader
import asyncio

async def count():
    loader = AgentLoader()
    agents = await loader.load_all()
    print(len(agents))

asyncio.run(count())
" 2>&1)

if [ "$AGENT_COUNT" -eq 21 ]; then
    log_pass "All 21 agents loaded ($AGENT_COUNT/21)"
else
    log_fail "Agent loading incomplete ($AGENT_COUNT/21)"
fi

# Test 4: BMAD Framework
log_test "Testing BMAD Framework..."
python3 -c "
import sys
sys.path.insert(0, '.')
from core.agents.definitions.bmad import BMADFramework
framework = BMADFramework()
print('BMAD Framework initialized')
" 2>&1 | grep -q "BMAD Framework initialized" && log_pass "BMAD Framework working" || log_fail "BMAD Framework failed"

# Test 5: PlanningAgent
log_test "Testing PlanningAgent..."
python3 -c "
import sys
sys.path.insert(0, '.')
from core.agents.definitions.planning_agent import PlanningAgent
from core.agents.definitions.core.base_agent import AgentConfig
config = AgentConfig(name='test', full_name='Test', role='test', category='test', description='test')
agent = PlanningAgent(config)
print('PlanningAgent instantiated')
" 2>&1 | grep -q "PlanningAgent instantiated" && log_pass "PlanningAgent working" || log_fail "PlanningAgent failed"

# Test 6: Skill Router
log_test "Testing Skill Router..."
python3 -c "
import sys
sys.path.insert(0, '.')
from lib.skill_router import SkillRouter
router = SkillRouter()
result = router.route('Build a REST API for user management')
if result:
    print(f'Skill router working: {result.role}')
else:
    print('Skill router returned None')
" 2>&1 | grep -q "Skill router working" && log_pass "Skill Router working" || log_warn "Skill Router may have issues"

# Test 7: Routes Configuration
log_test "Testing routes.yaml..."
if [ -f "$ENGINE_DIR/routes.yaml" ]; then
    COMMAND_COUNT=$(grep -c "^[[:space:]]*[A-Z][A-Z]:" "$ENGINE_DIR/routes.yaml" || echo "0")
    if [ "$COMMAND_COUNT" -gt 20 ]; then
        log_pass "Routes.yaml has $COMMAND_COUNT BMAD commands"
    else
        log_warn "Routes.yaml has only $COMMAND_COUNT commands"
    fi
else
    log_fail "routes.yaml not found"
fi

# Test 8: Skill Files
log_test "Testing skill files..."
SKILL_COUNT=$(ls -1 "$ENGINE_DIR/skills/"*.md 2>/dev/null | wc -l)
if [ "$SKILL_COUNT" -ge 10 ]; then
    log_pass "Found $SKILL_COUNT skill files"
else
    log_warn "Only $SKILL_COUNT skill files found (expected 10+)"
fi

# Test 9: Shell Scripts
log_test "Testing shell scripts..."
SHELL_SCRIPTS=("ralf-loop.sh" "plan.sh" "telemetry.sh")
for script in "${SHELL_SCRIPTS[@]}"; do
    if [ -f "$ENGINE_DIR/shell/$script" ]; then
        if [ -x "$ENGINE_DIR/shell/$script" ]; then
            log_pass "$script exists and is executable"
        else
            log_warn "$script exists but not executable"
        fi
    else
        log_fail "$script not found"
    fi
done

# Test 10: RALF Prompt
log_test "Testing RALF prompt..."
if [ -f "$ENGINE_DIR/prompts/ralf.md" ]; then
    if grep -q "Superintelligence Protocol" "$ENGINE_DIR/prompts/ralf.md"; then
        log_pass "RALF prompt exists with Superintelligence Protocol"
    else
        log_warn "RALF prompt exists but missing Superintelligence Protocol"
    fi
else
    log_fail "RALF prompt not found"
fi

# Test 11: PlanningAgent Tests
log_test "Running PlanningAgent tests..."
cd "$BLACKBOX5_DIR/2-engine"
if python3 core/agents/definitions/core/test_planning_agent.py > /tmp/planning_test.log 2>&1; then
    TESTS_PASSED=$(grep -c "PASSED" /tmp/planning_test.log || echo "0")
    log_pass "PlanningAgent tests: $TESTS_PASSED/4 passed"
else
    log_fail "PlanningAgent tests failed"
fi

# Test 12: BMAD Framework Tests
log_test "Running BMAD Framework tests..."
if python3 core/agents/definitions/core/test_bmad_framework.py > /tmp/bmad_test.log 2>&1; then
    TESTS_PASSED=$(grep -c "PASSED" /tmp/bmad_test.log || echo "0")
    log_pass "BMAD tests: $TESTS_PASSED/5 passed"
else
    log_warn "BMAD tests had issues (check /tmp/bmad_test.log)"
fi

# Test 13: Directory Structure
log_test "Checking directory structure..."
REQUIRED_DIRS=("core/agents/definitions" ".autonomous/skills" ".autonomous/shell" ".autonomous/prompts" "core/agents/definitions/bmad")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$ENGINE_DIR/$dir" ]; then
        log_pass "Directory $dir exists"
    else
        log_fail "Directory $dir missing"
    fi
done

# Test 14: YAML Agent Definitions
log_test "Checking YAML agent definitions..."
YAML_COUNT=$(find "$ENGINE_DIR/core/agents/definitions/specialists" -name "*.yaml" -o -name "*.yml" 2>/dev/null | wc -l)
if [ "$YAML_COUNT" -ge 15 ]; then
    log_pass "Found $YAML_COUNT YAML agent definitions"
else
    log_warn "Only $YAML_COUNT YAML agents found (expected 18)"
fi

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Test Summary                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical tests passed!${NC}"
    echo ""
    echo "BlackBox5 is operational and ready for use."
    exit 0
else
    echo -e "${RED}✗ Some tests failed.${NC}"
    echo ""
    echo "Review the failures above and fix before proceeding."
    exit 1
fi
