#!/bin/bash
# Blackbox4 Brain v2.0 - Quick Start Script
# Get up and running with PostgreSQL brain system in minutes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Blackbox4 Brain v2.0 - PostgreSQL Quick Start             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker and Docker Compose found"
echo ""

# Step 1: Start PostgreSQL
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Starting PostgreSQL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd databases
./start.sh

echo ""
echo "Waiting for PostgreSQL to be ready..."
until docker-compose exec -T postgres pg_isready -U blackbox4 &> /dev/null; do
    sleep 1
done
echo "✓ PostgreSQL is ready"
echo ""

# Step 2: Install dependencies
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Installing Python Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
else
    echo "✓ .env file already exists"
fi

echo ""
echo "Installing Python packages..."
pip install -q -r requirements.txt
echo "✓ Python dependencies installed"
echo ""

# Step 3: Ingest metadata
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Ingesting Metadata"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd ../ingest
echo "Running ingestion pipeline..."
python ingester.py

echo ""

# Step 4: Query example
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Example Query"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 - <<'EOF'
import asyncio
from query.sql import BrainQuery

async def query_example():
    q = BrainQuery()
    await q.initialize()

    # Get statistics
    stats = await q.get_statistics()

    print("📊 Database Statistics:")
    print(f"   Total artifacts: {stats['total_artifacts']}")
    print(f"   Total relationships: {stats['total_relationships']}")
    print("")
    print("   By type:")
    for artifact_type, count in stats['by_type'].items():
        print(f"     - {artifact_type}: {count}")

    print("")
    print("   By status:")
    for status, count in stats['by_status'].items():
        print(f"     - {status}: {count}")

    await q.close()

asyncio.run(query_example())
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Your Blackbox4 Brain v2.0 PostgreSQL system is now ready!"
echo ""
echo "📖 Documentation:"
echo "   - PostgreSQL Guide: databases/README-postgres.md"
echo "   - Main README: README.md"
echo ""
echo "🔧 Useful Commands:"
echo "   - Start file watcher: cd ingest && python watch_cli.py"
echo "   - Start REST API: cd api && python brain_api.py"
echo "   - Query database: cd ingest && python -c 'from query.sql import *; ...'"
echo "   - Stop PostgreSQL: cd databases && ./stop.sh"
echo ""
echo "🌐 API Endpoints (if API is running):"
echo "   - Swagger UI: http://localhost:8000/docs"
echo "   - Health check: curl http://localhost:8000/api/v1/health"
echo "   - Statistics: curl http://localhost:8000/api/v1/statistics"
echo ""
echo "📝 Next Steps:"
echo "   1. Add metadata.yaml to your artifacts"
echo "   2. Run ingestion: python ingester.py"
echo "   3. Start file watcher for auto-updates: python watch_cli.py"
echo "   4. Query via Python API or REST API"
echo ""
