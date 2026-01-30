# Neo4j Graph Database Setup

**Status:** Planned (Phase 2)
**Priority:** High

## Purpose

Neo4j for:
- Graph queries (relationships, traversals, paths)
- Impact analysis (what breaks if X changes)
- Dependency visualization

## Setup Instructions

```bash
# Install Neo4j Community Edition
brew install neo4j

# Start Neo4j
neo4j start

# Access Neo4j Browser
open http://localhost:7474

# Default credentials
# Username: neo4j
# Password: neo4j (change on first login)
```

## Connection String

```
bolt://localhost:7687
```

## Query Examples

```cypher
// Find all dependencies
MATCH (a:Artifact {id: 'orchestrator'})-[:DEPENDS_ON*]->(dep)
RETURN dep.name, dep.type, dep.path

// Find impact if X changes
MATCH (x:Artifact {id: 'ralph-runtime'})<-[:USED_BY*]-(affected)
RETURN affected.name, affected.type

// Find shortest path
MATCH path = shortestPath(
  (a:Artifact {id: 'agent-a'})-[:RELATES_TO*]-(b:Artifact {id: 'agent-b'})
)
RETURN path
```

## Requirements

- Neo4j 5+ (Community Edition OK)
- Python neo4j driver

## Status

⏳ Pending Phase 2 implementation
