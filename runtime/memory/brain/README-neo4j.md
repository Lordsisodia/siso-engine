# Neo4j Graph Database - Setup and Usage Guide

**Last Updated:** 2026-01-15
**Status:** Phase 3 - Implementation Complete
**Version:** 2.0.0

---

## Overview

Neo4j is used in the Blackbox4 Brain system to store and query relationships between artifacts. It enables powerful graph queries like:

- **Dependency Analysis:** What does X depend on?
- **Impact Analysis:** What will break if I change X?
- **Path Finding:** Find shortest path between artifacts
- **Orphan Detection:** Find artifacts with no relationships
- **Circular Dependencies:** Detect problematic dependency cycles

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Docker Setup](#docker-setup)
3. [Manual Setup](#manual-setup)
4. [Configuration](#configuration)
5. [Ingestion](#ingestion)
6. [Querying](#querying)
7. [API Usage](#api-usage)
8. [Cypher Examples](#cypher-examples)
9. [Troubleshooting](#troubleshooting)
10. [Performance](#performance)

---

## Quick Start

### 1. Start Neo4j with Docker

```bash
cd 9-brain/databases/neo4j
docker-compose up -d
```

### 2. Verify Connection

```bash
# Check if Neo4j is running
docker-compose ps

# Access Neo4j Browser
open http://localhost:7474
# Username: neo4j
# Password: blackbox4brain
```

### 3. Install Python Dependencies

```bash
pip install neo4j
```

### 4. Ingest Metadata

```bash
cd 9-brain/ingest
python graph_ingester.py --sync
```

### 5. Query the Graph

```bash
cd 9-brain/query
python graph.py dependencies orchestrator-agent-v1
python graph.py impact context-variables-lib
python graph.py orphans
```

---

## Docker Setup

### Docker Compose Configuration

The `docker-compose.yml` file provides:

- **Neo4j 5.15 Community Edition**
- **APOC Plugin** (for advanced procedures)
- **Persistent volumes** for data and logs
- **Health checks** for monitoring
- **Custom memory settings**

### Starting/Stopping

```bash
# Start Neo4j
docker-compose up -d

# Stop Neo4j
docker-compose down

# Restart Neo4j
docker-compose restart

# View logs
docker-compose logs -f neo4j

# Remove all data (WARNING: deletes everything)
docker-compose down -v
```

### Accessing Neo4j Browser

```
URL: http://localhost:7474
Username: neo4j
Password: blackbox4brain
```

---

## Manual Setup

### Install Neo4j

**macOS:**
```bash
brew install neo4j
neo4j start
```

**Ubuntu/Debian:**
```bash
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j
sudo systemctl start neo4j
```

**Windows:**
Download from https://neo4j.com/download/

### Configure Neo4j

Edit `conf/neo4j.conf`:

```properties
# Bolt connector
dbms.default_listen_address=0.0.0.0

# HTTP connector
dbms.connector.http.listen_address=:7474
dbms.connector.bolt.listen_address=:7687

# Memory
dbms.memory.heap.initial_size=512m
dbms.memory.heap.max_size=2G
dbms.memory.pagecache.size=512m
```

### Change Default Password

```bash
# First login - change password
cypher-shell -u neo4j -p neo4j
# Enter new password when prompted
```

---

## Configuration

### Environment Variables

```bash
# Neo4j Connection
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="blackbox4brain"

# API Configuration
export API_HOST="0.0.0.0"
export API_PORT="8000"
```

### Python Configuration

```python
from query.graph import GraphQuery

# Custom connection
graph = GraphQuery(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="blackbox4brain"
)
graph.connect()
```

---

## Ingestion

### Using Graph Ingester

```bash
# Ingest single file
python graph_ingester.py --file /path/to/metadata.yaml

# Ingest directory
python graph_ingester.py --directory /path/to/directory

# Ingest all artifacts
python graph_ingester.py --sync

# Ingest with verbose output
python graph_ingester.py --sync --verbose

# Custom connection
python graph_ingester.py --sync \
  --uri bolt://localhost:7687 \
  --user neo4j \
  --password blackbox4brain
```

### Using Unified Ingester

The unified ingester updates both PostgreSQL and Neo4j simultaneously:

```bash
python unified_ingester.py --sync
```

### Programmatic Ingestion

```python
from ingest.graph_ingester import GraphIngester, Neo4jConnection

# Connect
conn = Neo4jConnection("bolt://localhost:7687", "neo4j", "blackbox4brain")
conn.connect()

# Create ingester
ingester = GraphIngester(conn)

# Ingest metadata
metadata = {
    'id': 'my-artifact',
    'type': 'agent',
    'name': 'My Agent',
    'category': 'specialist',
    'path': 'path/to/agent.md',
    'created': '2026-01-15',
    'modified': '2026-01-15',
    'description': 'My artifact',
    'tags': ['test', 'agent'],
    'status': 'active',
    'stability': 'high',
    'owner': 'me'
}

success = ingester.ingest_metadata(metadata)
print(f"Success: {success}")

# Delete artifact
ingester.delete_artifact('my-artifact')

# Close connection
conn.close()
```

---

## Querying

### Using Command Line

```bash
cd 9-brain/query

# Get dependencies
python graph.py dependencies orchestrator-agent-v1

# Get dependents (what uses this)
python graph.py dependents context-variables-lib

# Impact analysis
python graph.py impact context-variables-lib

# Shortest path
python graph.py path agent-a agent-b

# Find orphans
python graph.py orphans

# Find circular dependencies
python graph.py circular

# Find unused artifacts
python graph.py unused

# Get statistics
python graph.py stats

# Custom Cypher
python graph.py cypher "MATCH (a:Artifact) RETURN count(a) as count"
```

### Programmatic Queries

```python
from query.graph import GraphQuery

# Connect
graph = GraphQuery()
graph.connect()

# Get dependencies
deps = graph.get_dependencies('orchestrator-agent-v1')
print(f"Total dependencies: {deps['total_dependencies']}")

# Impact analysis
impact = graph.get_impact_analysis('context-variables-lib')
print(f"Severity: {impact['severity']}")
print(f"Total impacted: {impact['total_impacted']}")

# Shortest path
path = graph.get_shortest_path('agent-a', 'agent-b')
if path['path_found']:
    print(f"Path length: {path['length']}")
    print(f"Nodes: {path['nodes']}")

# Find orphans
orphans = graph.find_orphans()
print(f"Found {len(orphans)} orphans")

# Get statistics
stats = graph.get_statistics()
print(f"Total artifacts: {stats['total_artifacts']}")
print(f"Total relationships: {stats['total_relationships']}")

# Close
graph.close()
```

---

## API Usage

### Start API Server

```bash
cd 9-brain/api
python brain_api.py

# Or with custom configuration
API_HOST=0.0.0.0 API_PORT=8000 \
NEO4J_URI=bolt://localhost:7687 \
NEO4J_USER=neo4j \
NEO4J_PASSWORD=blackbox4brain \
python brain_api.py
```

### API Endpoints

#### Execute Cypher Query

```bash
curl -X POST "http://localhost:8000/api/v1/graph/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "MATCH (a:Artifact {type: \"agent\"}) RETURN a LIMIT 10"
  }'
```

#### Get Dependencies

```bash
curl "http://localhost:8000/api/v1/graph/dependencies/orchestrator-agent-v1?depth=10"
```

#### Get Impact Analysis

```bash
curl "http://localhost:8000/api/v1/graph/impact/context-variables-lib"
```

#### Get Shortest Path

```bash
curl "http://localhost:8000/api/v1/graph/path/agent-a/agent-b"
```

#### Find Orphans

```bash
curl "http://localhost:8000/api/v1/graph/orphans"
```

#### Find Circular Dependencies

```bash
curl "http://localhost:8000/api/v1/graph/circular"
```

#### Find Unused Artifacts

```bash
curl "http://localhost:8000/api/v1/graph/unused"
```

#### Get Relationships

```bash
curl "http://localhost:8000/api/v1/graph/relationships/orchestrator-agent-v1"
```

#### Get Statistics

```bash
curl "http://localhost:8000/api/v1/graph/stats"
```

---

## Cypher Examples

### Find All Dependencies

```cypher
MATCH (a:Artifact {id: 'orchestrator-agent-v1'})-[:DEPENDS_ON*]->(dep)
RETURN dep.name, dep.type, dep.path
ORDER BY dep.name
```

### Find What Will Break

```cypher
MATCH (x:Artifact {id: 'context-variables-lib'})<-[:DEPENDS_ON*]-(affected)
RETURN DISTINCT affected.name, affected.type, affected.status
ORDER BY affected.type, affected.name
```

### Find Shortest Path

```cypher
MATCH path = shortestPath(
  (a:Artifact {id: 'agent-a'})-[:DEPENDS_ON|USED_BY|RELATES_TO*]-(b:Artifact {id: 'agent-b'})
)
RETURN [node in nodes(path) | node.name] as path_names, length(path) as hops
```

### Find Orphans

```cypher
MATCH (a:Artifact)
WHERE NOT (a)-[:DEPENDS_ON|USED_BY|RELATES_TO]-()
RETURN a.id, a.name, a.type, a.status
ORDER BY a.type, a.name
```

### Find Circular Dependencies

```cypher
MATCH (a:Artifact)-[:DEPENDS_ON*1..]->(a)
WHERE size([n in nodes(a) WHERE n.id = a.id]) > 1
RETURN DISTINCT [node in nodes(a) | node.name] as cycle
ORDER BY size(cycle)
```

### Find All Agents

```cypher
MATCH (a:Artifact {type: 'agent'})
RETURN a.id, a.name, a.category, a.status
ORDER BY a.category, a.name
```

### Find by Tag

```cypher
MATCH (a:Artifact)
WHERE 'research' IN a.tags
RETURN a.id, a.name, a.type, a.tags
ORDER BY a.name
```

### Dependency Tree

```cypher
MATCH path = (a:Artifact {id: 'orchestrator-agent-v1'})-[:DEPENDS_ON*1..3]->(dep)
WITH path, length(path) as depth
ORDER BY depth, dep.name
RETURN dep.name, dep.type, depth
```

### Impact by Type

```cypher
MATCH (lib:Artifact {id: 'context-variables-lib'})<-[:DEPENDS_ON*]-(affected)
RETURN affected.type as type, count(DISTINCT affected) as count
ORDER BY count DESC
```

### Full-Text Search

```cypher
CALL db.index.fulltext.queryNodes('artifact_fulltext', 'research agent')
YIELD node, score
RETURN node.id, node.name, node.description, score
ORDER BY score DESC
LIMIT 10
```

---

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to Neo4j

**Solutions:**
1. Check if Neo4j is running:
   ```bash
   docker-compose ps  # Docker
   neo4j status       # Manual install
   ```

2. Check firewall settings
3. Verify connection details (URI, user, password)
4. Check Neo4j logs:
   ```bash
   docker-compose logs neo4j
   ```

### Memory Issues

**Problem:** Out of memory errors

**Solutions:**
1. Increase heap size in `docker-compose.yml`:
   ```yaml
   environment:
     - NEO4J_dbms_memory_heap_max__size=4G
   ```

2. Increase page cache:
   ```yaml
   environment:
     - NEO4J_dbms_memory_pagecache_size=1G
   ```

### Slow Queries

**Problem:** Queries are slow

**Solutions:**
1. Check if indexes exist:
   ```cypher
   SHOW INDEXES
   ```

2. Create missing indexes (see `init-cypher/01-constraints.cypher`)

3. Use query profiling:
   ```cypher
   PROFILE MATCH (a:Artifact) RETURN a
   ```

4. Limit depth in variable-length queries:
   ```cypher
   MATCH path = (a)-[:DEPENDS_ON*1..5]->(b)  # Limit to 5 hops
   ```

### Data Inconsistency

**Problem:** Graph has orphaned relationships

**Solution:**
```cypher
MATCH ()-[r]->()
WHERE NOT startNode(r).id IN ['valid-id-1', 'valid-id-2']
DELETE r
```

---

## Performance

### Indexes

The following indexes are created automatically:

- **Unique:** `id`, `path`
- **Lookup:** `type`, `category`, `status`, `layer`, `phase`, `name`, `tags`, `created`, `modified`
- **Full-text:** `name`, `description`, `tags`

### Query Optimization Tips

1. **Use indexed properties** in WHERE clauses
2. **Limit variable-length paths** (e.g., `*1..5` instead of `*`)
3. **Use PROFILE** to analyze slow queries
4. **Avoid Cartesian products**
5. **Use EXISTS** instead of optional patterns

### Batch Operations

For bulk operations:

```python
# Use batch operations
with driver.session() as session:
    session.run("UNWIND $batch AS row MERGE (a:Artifact {id: row.id}) SET a += row",
               batch=[...])
```

---

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "neo4j": "connected",
  "postgresql": "connected"
}
```

### Graph Statistics

```bash
curl http://localhost:8000/api/v1/graph/stats
```

Response:
```json
{
  "total_artifacts": 150,
  "by_type": [
    {"type": "agent", "count": 45},
    {"type": "library", "count": 30}
  ],
  "total_relationships": 320,
  "by_relationship_type": [
    {"type": "DEPENDS_ON", "count": 180},
    {"type": "USED_BY", "count": 90}
  ]
}
```

---

## Security

### Production Deployment

1. **Change default password:**
   ```bash
   cypher-shell -u neo4j -p neo4j
   # Enter new password
   ```

2. **Use environment variables:**
   ```bash
   export NEO4J_PASSWORD="strong-password-here"
   ```

3. **Enable SSL/TLS:**
   ```yaml
   environment:
     - NEO4J_dbms_ssl_policy_bolt_enabled=true
   ```

4. **Restrict network access:**
   ```yaml
   ports:
     - "127.0.0.1:7687:7687"  # Local only
   ```

---

## Backup and Restore

### Backup

```bash
# Docker
docker-compose exec neo4j neo4j-admin database dump neo4j --to-path=/backups

# Manual
neo4j-admin dump --database=neo4j --to=/backups/neo4j-backup
```

### Restore

```bash
# Docker
docker-compose exec neo4j neo4j-admin database load neo4j --from-path=/backups --force

# Manual
neo4j-admin load --from=/backups/neo4j-backup --database=neo4j --force
```

---

## Resources

- **Neo4j Documentation:** https://neo4j.com/docs/
- **Cypher Manual:** https://neo4j.com/docs/cypher-manual/
- **Python Driver:** https://neo4j.com/docs/python-manual/
- **Neo4j Browser:** http://localhost:7474

---

## Support

For issues or questions:
1. Check this documentation
2. Review Neo4j logs: `docker-compose logs neo4j`
3. Check query performance with `PROFILE`
4. Consult Blackbox4 Brain README: `9-brain/README.md`

---

**Status:** Phase 3 Complete ✅
**Version:** 2.0.0
**Maintainer:** Blackbox4 Core Team
**Last Updated:** 2026-01-15
