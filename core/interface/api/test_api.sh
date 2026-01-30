#!/bin/bash
# Test script for Blackbox 5 REST API

echo "Testing Blackbox 5 REST API..."
echo ""

# Test 1: Health check
echo "1. Testing /health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool
echo -e "\n"

# Test 2: List agents
echo "2. Testing /agents endpoint..."
curl -s http://localhost:8000/agents | python3 -m json.tool
echo -e "\n"

# Test 3: Chat request
echo "3. Testing /chat endpoint..."
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a simple Python function to calculate fibonacci numbers",
    "session_id": "test_session_001"
  }' | python3 -m json.tool
echo -e "\n"

# Test 4: List skills
echo "4. Testing /skills endpoint..."
curl -s http://localhost:8000/skills | python3 -m json.tool
echo -e "\n"

# Test 5: Get specific agent
echo "5. Testing /agents/{agent_name} endpoint..."
curl -s http://localhost:8000/agents/developer | python3 -m json.tool
echo -e "\n"

# Test 6: Search guides
echo "6. Testing /guides/search endpoint..."
curl -s "http://localhost:8000/guides/search?q=python" | python3 -m json.tool
echo -e "\n"

# Test 7: Find guides by intent
echo "7. Testing /guides/intent endpoint..."
curl -s "http://localhost:8000/guides/intent?intent=how%20to%20create%20a%20function" | python3 -m json.tool
echo -e "\n"

echo "All tests complete!"
