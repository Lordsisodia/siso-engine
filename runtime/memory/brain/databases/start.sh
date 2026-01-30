#!/bin/bash
# Blackbox4 Brain v2.0 - Start PostgreSQL
# Quick script to start PostgreSQL with Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Blackbox4 Brain PostgreSQL..."
echo ""

# Start PostgreSQL
docker-compose up -d postgres

echo ""
echo "✓ PostgreSQL started"
echo ""
echo "Connection details:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: blackbox4_brain"
echo "  User: blackbox4"
echo "  Password: blackbox4_brain_pass"
echo ""
echo "To connect:"
echo "  docker-compose exec postgres psql -U blackbox4 -d blackbox4_brain"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f postgres"
echo ""
echo "To stop:"
echo "  docker-compose down"
echo ""
