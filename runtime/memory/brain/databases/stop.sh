#!/bin/bash
# Blackbox4 Brain v2.0 - Stop PostgreSQL
# Quick script to stop PostgreSQL

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "⏹️  Stopping Blackbox4 Brain PostgreSQL..."
echo ""

# Stop all services
docker-compose down

echo ""
echo "✓ PostgreSQL stopped"
echo ""
echo "To remove all data (WARNING: irreversible):"
echo "  docker-compose down -v"
echo ""
