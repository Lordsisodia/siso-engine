# Neo4j Quick Reference

**Blackbox4 Brain v2.0 - Phase 3**

---

## Quick Start Commands

### Start Neo4j
```bash
cd 9-brain/databases/neo4j
./start.sh
```

### Stop Neo4j
```bash
./stop.sh
```

### Check Status
```bash
docker-compose ps
```

### View Logs
```bash
docker-compose logs -f neo4j
```

---

## Ingestion Commands

### Ingest All Artifacts
```bash
cd 9-brain/ingest
python graph_ingester.py --sync
```

### Ingest Single File
```bash
python graph_ingester.py --file /path/to/metadata.yaml
```

### Ingest Directory
```bash
python graph_ingester.py --directory /path/to/directory
```

### Delete Artifact
```bash
python graph_ingester.py --delete artifact-id
```

---

## Query Commands (CLI)

### Dependencies
```bash
cd 9-brain/query
python graph.py dependencies artifact-id
```

### Dependents (Impact)
```bash
python graph.py dependents artifact-id
```

### Impact Analysis
```bash
python graph.py impact artifact-id
```

### Shortest Path
```bash
python graph.py path artifact-a artifact-b
```

### Find Orphans
```bash
python graph.py orphans
```

### Find Circular Dependencies
```bash
python graph.py circular
```

### Find Unused
```bash
python graph.py unused
```

### Get Statistics
```bash
python graph.py stats
```

### Custom Cypher
```bash
python graph.py cypher "MATCH (a:Artifact) RETURN count(a)"
```

---

## API Endpoints

### Base URL
```
http://localhost:8000
```

### Graph Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/graph/query` | Execute Cypher |
| GET | `/api/v1/graph/dependencies/{id}` | Get dependencies |
| GET | `/api/v1/graph/dependents/{id}` | Get dependents |
| GET | `/api/v1/graph/impact/{id}` | Impact analysis |
| GET | `/api/v1/graph/path/{from}/{to}` | Shortest path |
| GET | `/api/v1/graph/orphans` | Find orphans |
| GET | `/api/v1/graph/circular` | Circular dependencies |
| GET | `/api/v1/graph/unused` | Unused artifacts |
| GET | `/api/v1/graph/relationships/{id}` | Get relationships |
| GET | `/api/v1/graph/stats` | Statistics |

### API Documentation
```
http://localhost:8000/docs
```

---

## Common Cypher Queries

### Count Artifacts
```cypher
MATCH (a:Artifact) RETURN count(a)
```

### Find by Type
```cypher
MATCH (a:Artifact {type: 'agent'})
RETURN a.name, a.status
ORDER BY a.name
```

### Find Dependencies
```cypher
MATCH (a:Artifact {id: 'artifact-id'})-[:DEPENDS_ON*]->(dep)
RETURN dep.name, dep.type
ORDER BY dep.name
```

### Find What Will Break
```cypher
MATCH (x:Artifact {id: 'artifact-id'})<-[:DEPENDS_ON*]-(affected)
RETURN DISTINCT affected.name, affected.type
ORDER BY affected.type, affected.name
```

### Shortest Path
```cypher
MATCH path = shortestPath(
  (a:Artifact {id: 'from'})-[*]-(b:Artifact {id: 'to'})
)
RETURN [n in nodes(path) | n.name] as names
```

### Find Orphans
```cypher
MATCH (a:Artifact)
WHERE NOT (a)-[:DEPENDS_ON|USED_BY|RELATES_TO]-()
RETURN a.name, a.type
ORDER BY a.type, a.name
```

---

## Python Usage

### Connect and Query
```python
from query.graph import GraphQuery

graph = GraphQuery()
graph.connect()

# Get dependencies
deps = graph.get_dependencies('artifact-id')

# Impact analysis
impact = graph.get_impact_analysis('artifact-id')

# Find orphans
orphans = graph.find_orphans()

# Get statistics
stats = graph.get_statistics()

graph.close()
```

### Ingest Metadata
```python
from ingest.graph_ingester import GraphIngester, Neo4jConnection

conn = Neo4jConnection()
conn.connect()

ingester = GraphIngester(conn)
success = ingester.ingest_metadata(metadata)

conn.close()
```

---

## Neo4j Browser

### Access
```
URL: http://localhost:7474
Username: neo4j
Password: blackbox4brain
```

### Useful Queries in Browser

### Visualize Dependencies
```cypher
MATCH path = (a:Artifact {id: 'artifact-id'})-[:DEPENDS_ON*1..3]->(dep)
RETURN path
LIMIT 50
```

### Visualize Impact
```cypher
MATCH path = (x:Artifact {id: 'artifact-id'})<-[:DEPENDS_ON*1..3]-(affected)
RETURN path
LIMIT 50
```

### All Relationships
```cypher
MATCH (a:Artifact {id: 'artifact-id'})-[r]-(other)
RETURN a, r, other
```

---

## Troubleshooting

### Connection Issues
```bash
# Check if Neo4j is running
docker-compose ps

# Restart Neo4j
docker-compose restart

# Check logs
docker-compose logs neo4j
```

### Clear All Data
```bash
docker-compose down -v
./start.sh
```

### Reset Password
```bash
docker-compose exec neo4j cypher-shell -u neo4j -p neo4j
# Enter new password when prompted
```

---

## Environment Variables

```bash
# Neo4j
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="blackbox4brain"

# API
export API_HOST="0.0.0.0"
export API_PORT="8000"
```

---

## File Locations

### Neo4j Setup
```
9-brain/databases/neo4j/
├── docker-compose.yml
├── init-cypher/
├── start.sh
└── stop.sh
```

### Ingestion
```
9-brain/ingest/
├── graph_ingester.py
└── unified_ingester.py
```

### Queries
```
9-brain/query/
└── graph.py
```

### API
```
9-brain/api/
└── brain_api.py
```

### Tests
```
9-brain/tests/
└── test_neo4j.py
```

### Documentation
```
9-brain/
├── README.md
├── README-neo4j.md
└── PHASE3-COMPLETE.md
```

---

## Key Concepts

### Relationship Types
- **DEPENDS_ON** - Direct dependency
- **USED_BY** - Reverse dependency
- **RELATES_TO** - General relationship

### Query Patterns
- **Dependency Tree**: `(a)-[:DEPENDS_ON*]->(dep)`
- **Impact Analysis**: `(x)<-[:DEPENDS_ON*]-(affected)`
- **Shortest Path**: `shortestPath((a)-[*]-(b))`
- **Orphans**: `NOT (a)-[]-()`

---

## Performance Tips

1. **Use indexes** - All indexed fields are fast
2. **Limit depth** - Use `*1..5` instead of `*`
3. **Use PROFILE** - Analyze slow queries
4. **Batch operations** - For bulk writes
5. **Cache results** - For repeated queries

---

**For full documentation, see README-neo4j.md**
