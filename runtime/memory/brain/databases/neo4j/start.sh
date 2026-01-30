#!/bin/bash
# Blackbox4 Brain - Neo4j Quick Start Script
# Starts Neo4j and performs initial setup

set -e

echo "=========================================="
echo "Blackbox4 Brain - Neo4j Quick Start"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    echo "Install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed"
    echo "Install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

# Navigate to script directory
cd "$(dirname "$0")"

echo "1. Starting Neo4j container..."
docker-compose up -d

echo ""
echo "2. Waiting for Neo4j to be ready..."
sleep 10

# Check if Neo4j is running
if docker-compose ps | grep -q "Up"; then
    echo "   ✓ Neo4j is running"
else
    echo "   ✗ Failed to start Neo4j"
    echo "   Check logs with: docker-compose logs neo4j"
    exit 1
fi

echo ""
echo "3. Installing Python dependencies..."
cd ../..
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "   ✓ Dependencies installed"
else
    echo "   ! No requirements.txt found, skipping"
fi

echo ""
echo "4. Testing connection..."
cd ingest
if python -c "from query.graph import GraphQuery; g = GraphQuery(); g.connect(); print('✓ Connected to Neo4j'); g.close()" 2>/dev/null; then
    echo "   ✓ Connection successful"
else
    echo "   ! Connection test failed (this is OK if you haven't installed dependencies yet)"
    echo "   Install with: pip install -r requirements.txt"
fi

echo ""
echo "=========================================="
echo "Neo4j Setup Complete!"
echo "=========================================="
echo ""
echo "Neo4j Browser:  http://localhost:7474"
echo "Username:       neo4j"
echo "Password:       blackbox4brain"
echo ""
echo "Next Steps:"
echo "  1. Open Neo4j Browser: http://localhost:7474"
echo "  2. Log in with credentials above"
echo "  3. Run: MATCH (a:Artifact) RETURN count(a)"
echo ""
echo "Commands:"
echo "  Stop Neo4j:    docker-compose down"
echo "  Restart Neo4j: docker-compose restart"
echo "  View logs:     docker-compose logs -f neo4j"
echo ""
echo "For full documentation, see: README-neo4j.md"
echo "=========================================="
