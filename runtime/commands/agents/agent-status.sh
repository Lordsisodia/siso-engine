#!/bin/bash
# agent-status.sh - Check agent status for Blackbox 5
# Usage: ./agent-status.sh [options]
#   --verbose    : Show detailed information
#   --services   : Only check service status
#   --agents     : Only list loaded agents

set -e

# Parse arguments
VERBOSE=false
SERVICES_ONLY=false
AGENTS_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --services|-s)
            SERVICES_ONLY=true
            shift
            ;;
        --agents|-a)
            AGENTS_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --verbose, -v  Show detailed information"
            echo "  --services, -s Only check service status"
            echo "  --agents, -a   Only list loaded agents"
            echo "  --help, -h     Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h for help"
            exit 1
            ;;
    esac
done

# Function to check service status
check_service() {
    local service_name=$1
    local check_command=$2
    local running_symbol=$3

    if eval "$check_command" > /dev/null 2>&1; then
        echo "  $running_symbol $service_name: Running"
        return 0
    else
        echo "  ✗ $service_name: Not running"
        return 1
    fi
}

# Function to check Redis
check_redis() {
    if command -v redis-cli &> /dev/null; then
        redis-cli ping > /dev/null 2>&1
    else
        return 1
    fi
}

# Function to check ChromaDB
check_chromadb() {
    # ChromaDB typically runs on port 8000
    if command -v curl &> /dev/null; then
        curl -s http://localhost:8000/health > /dev/null 2>&1 || \
        curl -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1
    else
        return 1
    fi
}

# Function to check Neo4j
check_neo4j() {
    # Neo4j typically runs on port 7474 (HTTP) or 7687 (Bolt)
    if command -v curl &> /dev/null; then
        curl -s http://localhost:7474 > /dev/null 2>&1 || \
        curl -s http://localhost:7473 > /dev/null 2>&1
    else
        return 1
    fi
}

# Function to list loaded agents
list_agents() {
    local python_cmd="
import sys
from pathlib import Path

# Add engine to path
engine_path = Path('blackbox5/engine')
if engine_path.exists():
    sys.path.insert(0, str(engine_path))

try:
    from agents.core.AgentLoader import AgentLoader
    import asyncio

    async def load_agents():
        loader = AgentLoader()
        agents = await loader.load_all()

        if not agents:
            print('  (No agents loaded)')
            return

        for name, agent in agents.items():
            agent_type = agent.__class__.__name__
            category = getattr(agent, 'category', 'unknown')
            icon = getattr(agent, 'icon', '🤖')
            print(f'  {icon} {name}: {agent_type} [{category}]')

    asyncio.run(load_agents())
except Exception as e:
    print(f'  Error loading agents: {e}')
    print('  Make sure the engine is properly set up.')
"

    if command -v python3 &> /dev/null; then
        python3 -c "$python_cmd"
    else
        echo "  Error: python3 not found"
    fi
}

# Main output
echo "=============================================="
echo "Blackbox 5 Agent Status"
echo "=============================================="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="
echo ""

# Check services (unless --agents only)
if [ "$AGENTS_ONLY" = false ]; then
    echo "Service Status:"
    echo "---------------"

    # Check Redis (Event Bus)
    if check_redis; then
        if [ "$VERBOSE" = true ]; then
            REDIS_INFO=$(redis-cli info server 2>/dev/null | grep "redis_version" | cut -d: -f2 | tr -d '\r')
            echo "  ✓ Event Bus (Redis): Running - v$REDIS_INFO"
        else
            echo "  ✓ Event Bus (Redis): Running"
        fi
    else
        echo "  ✗ Event Bus (Redis): Not running"
        echo "    Start with: ./start-redis.sh"
    fi

    # Check ChromaDB (Vector Store)
    if check_chromadb; then
        echo "  ✓ Vector Store (ChromaDB): Running"
    else
        echo "  ✗ Vector Store (ChromaDB): Not running"
    fi

    # Check Neo4j (Graph Database)
    if check_neo4j; then
        echo "  ✓ Graph Database (Neo4j): Running"
    else
        echo "  ✗ Graph Database (Neo4j): Not running"
    fi

    echo ""
fi

# List agents (unless --services only)
if [ "$SERVICES_ONLY" = false ]; then
    echo "Loaded Agents:"
    echo "--------------"
    list_agents
    echo ""
fi

# Additional info in verbose mode
if [ "$VERBOSE" = true ]; then
    echo "System Information:"
    echo "-------------------"

    # Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        echo "  Python: $PYTHON_VERSION"
    fi

    # Redis version
    if command -v redis-server &> /dev/null; then
        REDIS_SERVER_VERSION=$(redis-server --version 2>&1 | cut -d' ' -f4 | cut -d'=' -f2)
        echo "  Redis Server: v$REDIS_SERVER_VERSION"
    fi

    # Check if jq is available
    if command -v jq &> /dev/null; then
        echo "  jq: Available (for log parsing)"
    else
        echo "  jq: Not found (install for better log viewing)"
    fi

    echo ""
    echo "Paths:"
    echo "  Engine: .blackbox5/engine"
    echo "  Logs: .blackbox5/logs"
    echo "  Manifests: .blackbox5/scratch/manifests"
    echo ""
fi

echo "=============================================="
echo ""
echo "Quick Actions:"
echo "  Start Redis: ./start-redis.sh"
echo "  View logs: ./view-logs.sh"
echo "  View manifests: ./view-manifest.sh"
echo "=============================================="
