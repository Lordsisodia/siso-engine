# Query API

**Status:** Planned (Phase 3)
**Priority:** High

## Purpose

REST API for querying the brain system, designed for AI integration.

## Endpoints

```
GET    /api/v1/query               - Natural language query
POST   /api/v1/query/structured    - Structured query
GET    /api/v1/artifacts/:id       - Get artifact by ID
GET    /api/v1/artifacts           - List artifacts (with filters)
POST   /api/v1/artifacts           - Create artifact
PUT    /api/v1/artifacts/:id       - Update artifact
DELETE /api/v1/artifacts/:id       - Delete artifact
GET    /api/v1/relationships/:id   - Get relationships
POST   /api/v1/relationships       - Create relationship
GET    /api/v1/similar/:id         - Find similar artifacts
GET    /api/v1/impact/:id          - Get impact analysis
```

## Usage

```bash
# Natural language query
curl "http://localhost:8000/api/v1/query?q=Find%20all%20specialist%20agents"

# Structured query
curl -X POST "http://localhost:8000/api/v1/query/structured" \
  -H "Content-Type: application/json" \
  -d '{"type": "agent", "category": "specialist"}'

# Get artifact
curl "http://localhost:8000/api/v1/artifacts/orchestrator-agent-v1"

# Find similar
curl "http://localhost:8000/api/v1/similar/orchestrator-agent-v1?limit=10"

# Impact analysis
curl "http://localhost:8000/api/v1/impact/orchestrator-agent-v1"
```

## Response Format

```json
{
  "success": true,
  "data": [...],
  "meta": {
    "query_type": "structured",
    "execution_time_ms": 15,
    "result_count": 5
  }
}
```

## Status

⏳ Pending Phase 3 implementation
