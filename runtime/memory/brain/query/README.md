# Query Interface

**Status:** Planned (Phase 3)
**Priority:** High

## Purpose

Natural language query interface for AI agents to interact with the brain system.

## Components

- `parser.py` - Parse natural language into structured queries
- `sql.py` - PostgreSQL query execution
- `graph.py` - Neo4j query execution
- `vector.py` - Vector similarity search

## Usage

```python
from query import BrainQuery

brain = BrainQuery()

# Natural language query
result = brain.query("Find all specialist agents")

# Structured query
result = brain.query({
    "type": "agent",
    "category": "specialist",
    "status": "active"
})
```

## Query Types

1. **Structured Queries** - Exact match, filters, aggregations
2. **Graph Queries** - Relationships, paths, impact analysis
3. **Semantic Queries** - Similarity search, fuzzy matching
4. **Hybrid Queries** - Combination of above

## Status

⏳ Pending Phase 3 implementation
