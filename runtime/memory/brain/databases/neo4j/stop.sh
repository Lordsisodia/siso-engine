#!/bin/bash
# Blackbox4 Brain - Stop Neo4j Script
# Stops Neo4j container

echo "Stopping Neo4j..."
cd "$(dirname "$0")"
docker-compose down

echo "Neo4j stopped."
echo ""
echo "To restart, run: ./start.sh"
echo "To remove all data, run: docker-compose down -v"
