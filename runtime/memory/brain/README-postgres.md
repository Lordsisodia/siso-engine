# Blackbox4 Brain v2.0 - PostgreSQL Setup and Usage Guide

**Last Updated:** 2026-01-15
**Status:** Phase 2 - PostgreSQL Ingestion and Query System (Complete)
**Version:** 2.0.0

---

## Overview

Phase 2 of the Blackbox4 Brain v2.0 implements a complete PostgreSQL-based ingestion and query system. This system enables:

- **Structured Queries:** Query artifacts by type, category, tag, status, phase, owner, etc.
- **Relationship Tracking:** Understand dependencies and impacts
- **Full-Text Search:** Search across all artifact metadata
- **REST API:** HTTP endpoints for integration
- **File Watching:** Auto-update when metadata changes

---

## Quick Start

### 1. Start PostgreSQL with Docker

```bash
cd 9-brain/databases
docker-compose up -d

# Check logs
docker-compose logs -f postgres

# Stop
docker-compose down
```

This starts:
- PostgreSQL 16 with pgvector on port 5432
- (Optional) Neo4j on ports 7474, 7687 (use `--profile neo4j`)
- (Optional) pgAdmin on port 5050 (use `--profile admin`)

### 2. Install Dependencies

```bash
cd 9-brain/databases
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cd 9-brain/databases
cp .env.example .env

# Edit .env with your settings
# Default settings work with docker-compose
```

### 4. Initialize Database Schema

```bash
# Schema is auto-initialized by docker-compose
# Or manually:
psql -h localhost -U blackbox4 -d blackbox4_brain -f init.sql
```

### 5. Ingest Metadata

```bash
cd 9-brain/ingest
python ingester.py

# Or clean and re-ingest
python ingester.py --clean
```

### 6. Start File Watcher (Optional)

```bash
cd 9-brain/ingest
python watch_cli.py

# Or with custom settings
python watch_cli.py --directories ../1-agents --debounce 5 --verbose
```

### 7. Start REST API (Optional)

```bash
cd 9-brain/api
python brain_api.py

# Or with uvicorn
uvicorn brain_api:app --host 0.0.0.0 --port 8000 --reload
```

API available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Docker Commands

### Start Services

```bash
# Start PostgreSQL only
docker-compose up -d

# Start with Neo4j
docker-compose --profile neo4j up -d

# Start with pgAdmin
docker-compose --profile admin up -d

# Start everything
docker-compose --profile neo4j --profile admin up -d
```

### Stop Services

```bash
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f neo4j
```

### Execute Commands

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U blackbox4 -d blackbox4_brain

# Backup database
docker-compose exec postgres pg_dump -U blackbox4 blackbox4_brain > backup.sql

# Restore database
docker-compose exec -T postgres psql -U blackbox4 blackbox4_brain < backup.sql
```

---

## Database Schema

### Tables

**artifacts**
- Core artifact metadata
- Indexed on type, category, tags, status, phase, layer
- Full-text search on description

**embeddings**
- Vector embeddings for semantic search (pgvector)
- 1536-dimensional vectors (OpenAI text-embedding-ada-002)
- Indexed with IVFFlat for approximate search

**relationships**
- Artifact relationships (depends_on, used_by, relates_to)
- Composite primary key (from_id, to_id, relationship_type)
- Metadata JSONB for extra info

### Views

- **active_artifacts**: All artifacts with status='active'
- **phase_artifacts**: Artifacts with phase assigned
- **orphaned_artifacts**: Artifacts without relationships
- **popular_artifacts**: Artifacts with usage_count > 100

---

## Ingestion Pipeline

### Command-Line Usage

```bash
cd 9-brain/ingest

# Ingest all metadata
python ingester.py

# Ingest specific directory
python ingester.py --directory /path/to/dir

# Clean database first
python ingester.py --clean
```

### Programmatic Usage

```python
import asyncio
from ingest.ingester import MetadataIngester

async def ingest():
    ingester = MetadataIngester(root_dir='/path/to/blackbox4')
    await ingester.run(clean=False)

asyncio.run(ingest())
```

### What Gets Ingested

- Scans directories: `1-agents`, `2-skills`, `3-plans`, `4-scripts`, `5-libraries`, `6-modules`, `8-workspaces`, `9-brain`
- Finds all `metadata.yaml` files
- Validates against schema
- Inserts/updates artifacts
- Extracts relationships
- Handles deletions

---

## Query Interface

### Python API

```python
import asyncio
from query.sql import BrainQuery

async def query_artifacts():
    q = BrainQuery()
    await q.initialize()

    # Get artifact by ID
    artifact = await q.get_artifact_by_id('orchestrator-agent-v1')

    # Find by type
    agents = await q.find_by_type('agent', status='active')

    # Find by tag
    test_artifacts = await q.find_by_tag('test')

    # Find by phase
    phase4 = await q.find_by_phase(4)

    # Find dependencies
    deps = await q.find_dependencies('orchestrator-agent-v1')

    # Find dependents
    dependents = await q.find_dependents('orchestrator-agent-v1')

    # Full-text search
    results = await q.search('orchestration coordination')

    # Complex query
    results = await q.complex_query({
        'type': 'agent',
        'status': 'active',
        'phase': 4,
        'tags': ['orchestration']
    })

    # Get statistics
    stats = await q.get_statistics()

    await q.close()

asyncio.run(query_artifacts())
```

### REST API

#### Get Artifact by ID

```bash
curl http://localhost:8000/api/v1/artifacts/orchestrator-agent-v1
```

#### List Artifacts

```bash
curl "http://localhost:8000/api/v1/artifacts?limit=20&offset=0"
```

#### Query by Type

```bash
curl http://localhost:8000/api/v1/artifacts/type/agent
curl "http://localhost:8000/api/v1/artifacts/type/agent?status=active"
```

#### Query by Category

```bash
curl http://localhost:8000/api/v1/artifacts/category/agent/specialist
```

#### Query by Tag

```bash
curl http://localhost:8000/api/v1/artifacts/tag/orchestration
```

#### Query by Status

```bash
curl http://localhost:8000/api/v1/artifacts/status/active
```

#### Query by Phase

```bash
curl http://localhost:8000/api/v1/artifacts/phase/4
```

#### Full-Text Search

```bash
curl "http://localhost:8000/api/v1/query/search?q=orchestration"
curl "http://localhost:8000/api/v1/query/search?q=test&artifact_type=agent&limit=10"
```

#### Complex Query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "type": "agent",
      "status": "active",
      "phase": 4
    },
    "limit": 50,
    "offset": 0
  }'
```

#### Get Dependencies

```bash
curl http://localhost:8000/api/v1/artifacts/orchestrator-agent-v1/dependencies
```

#### Get Dependents

```bash
curl http://localhost:8000/api/v1/artifacts/orchestrator-agent-v1/dependents
```

#### Get Related

```bash
curl http://localhost:8000/api/v1/artifacts/orchestrator-agent-v1/related
```

#### Get Statistics

```bash
curl http://localhost:8000/api/v1/statistics
```

#### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

---

## File Watcher

### Command-Line Usage

```bash
cd 9-brain/ingest

# Watch all default directories
python watch_cli.py

# Watch specific directories
python watch_cli.py --directories ../1-agents --directories ../2-skills

# Custom debounce time
python watch_cli.py --debounce 5

# Verbose output
python watch_cli.py --verbose
```

### How It Works

1. Uses `watchdog` to monitor file system events
2. Watches for creation, modification, deletion of `metadata.yaml` files
3. Debounces changes (default 2 seconds) to handle rapid updates
4. Parses changed metadata files
5. Updates database (insert, update, or delete)
6. Handles relationship updates

### Programmatic Usage

```python
from ingest.watcher import FileWatcher
import asyncio

watcher = FileWatcher(
    watch_directories=['/path/to/1-agents', '/path/to/2-skills'],
    debounce_seconds=2,
    verbose=True
)

# Initialize database
asyncio.run(watcher.initialize_database())

# Start watching
watcher.start()
```

---

## Testing

### Run All Tests

```bash
cd 9-brain/tests
pytest test_postgres.py -v
```

### Run Specific Test

```bash
pytest test_postgres.py::test_database_connection -v
```

### Run with Coverage

```bash
pytest test_postgres.py --cov=.. --cov-report=html
```

### Test Categories

1. **Database Tests:** Connection, insertion, update, deletion
2. **Query Tests:** All query methods and filters
3. **Relationship Tests:** Dependency and relationship queries
4. **Parser Tests:** Metadata file parsing
5. **Integration Tests:** End-to-end workflows

---

## Troubleshooting

### PostgreSQL Connection Issues

**Problem:** Cannot connect to PostgreSQL

**Solutions:**
1. Check Docker is running: `docker ps`
2. Check PostgreSQL container: `docker-compose ps`
3. Check logs: `docker-compose logs postgres`
4. Verify environment variables in `.env`
5. Test connection: `psql -h localhost -U blackbox4 -d blackbox4_brain`

### Schema Not Found

**Problem:** "Database schema not found. Run init.sql first."

**Solutions:**
1. Check if schema was initialized: `docker-compose exec postgres psql -U blackbox4 -d blackbox4_brain -c "\dt"`
2. Manually run init.sql: `docker-compose exec -T postgres psql -U blackbox4 -d blackbox4_brain < init.sql`
3. Recreate container: `docker-compose down -v && docker-compose up -d`

### File Watcher Not Detecting Changes

**Problem:** File changes not detected

**Solutions:**
1. Verify directory paths are correct
2. Check file watcher has permissions
3. Increase debounce time
4. Use verbose mode to debug

### API Not Starting

**Problem:** API fails to start

**Solutions:**
1. Check PostgreSQL is running
2. Verify database connection settings in `.env`
3. Check port 8000 is not in use
4. Check dependencies installed: `pip install -r databases/requirements.txt`

### Import Errors

**Problem:** Module import errors

**Solutions:**
1. Install dependencies: `pip install -r databases/requirements.txt`
2. Check Python path: `export PYTHONPATH="${PYTHONPATH}:/path/to/9-brain"`
3. Use absolute imports in scripts

---

## Performance Optimization

### Database Indexes

The schema includes indexes for:
- Type, category, status, phase, layer, owner
- Tags and keywords (GIN indexes)
- Full-text search on description
- Vector embeddings (IVFFlat)
- Composite indexes for common queries

### Query Optimization

```python
# Use specific queries when possible
agents = await q.find_by_type('agent')  # Fast

# Avoid full-text search for simple queries
results = await q.search('agent')  # Slower

# Use filters instead of full-text search
results = await q.complex_query({'type': 'agent'})  # Faster
```

### Batch Ingestion

```python
# Ingest in batches for large repositories
ingester = MetadataIngester()
await ingester.run()
```

### Connection Pooling

The database connection pool is configured via:
- `CONNECTION_POOL_SIZE` in `.env` (default: 10)
- Automatically managed by `asyncpg`

---

## Production Deployment

### Security

1. **Change Default Passwords:**
   ```bash
   # Edit docker-compose.yml
   POSTGRES_PASSWORD=your-secure-password
   ```

2. **Restrict Network Access:**
   ```yaml
   ports:
     - "127.0.0.1:5432:5432"  # Localhost only
   ```

3. **Use Environment Variables:**
   ```bash
   # Never commit .env to git
   echo ".env" >> .gitignore
   ```

4. **Enable SSL:**
   ```yaml
   environment:
     POSTGRES_SSLMODE: require
   ```

### Monitoring

1. **Check Database Health:**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

2. **View Statistics:**
   ```bash
   curl http://localhost:8000/api/v1/statistics
   ```

3. **Monitor PostgreSQL:**
   ```bash
   docker-compose exec postgres psql -U blackbox4 -d blackbox4_brain \
     -c "SELECT * FROM pg_stat_activity;"
   ```

### Backups

```bash
# Automated backup
docker-compose exec postgres pg_dump -U blackbox4 blackbox4_brain \
  | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore
gunzip < backup_20260115.sql.gz | \
  docker-compose exec -T postgres psql -U blackbox4 blackbox4_brain
```

### Scaling

1. **Use External PostgreSQL:**
   ```bash
   # Edit .env
   POSTGRES_HOST=your-postgres-server
   ```

2. **Load Balance API:**
   ```bash
   # Run multiple API instances
   uvicorn brain_api:app --port 8000 &
   uvicorn brain_api:app --port 8001 &
   uvicorn brain_api:app --port 8002 &
   ```

3. **Enable Query Caching:**
   - Use Redis for frequent queries
   - Cache API responses with TTL

---

## Next Steps

### Phase 3: Query API (Planned)

- Natural language query parser
- Query routing to appropriate database
- Result aggregation and formatting
- AI integration interface

### Phase 4: Auto-Indexing (Planned)

- Embedding generation for all artifacts
- Semantic search with pgvector
- Incremental index updates
- Performance optimization

---

## API Reference

Complete API documentation available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/artifacts/{id}` - Get artifact by ID
- `GET /api/v1/artifacts` - List artifacts
- `GET /api/v1/artifacts/type/{type}` - Find by type
- `GET /api/v1/artifacts/category/{type}/{category}` - Find by category
- `GET /api/v1/artifacts/tag/{tag}` - Find by tag
- `GET /api/v1/artifacts/status/{status}` - Find by status
- `GET /api/v1/artifacts/phase/{phase}` - Find by phase
- `GET /api/v1/artifacts/{id}/dependencies` - Get dependencies
- `GET /api/v1/artifacts/{id}/dependents` - Get dependents
- `GET /api/v1/artifacts/{id}/related` - Get related
- `POST /api/v1/query` - Complex query
- `GET /api/v1/query/search` - Full-text search
- `GET /api/v1/statistics` - Database statistics
- `POST /api/v1/ingest` - Trigger ingestion

---

## Support

For questions or issues:
1. Check this README
2. Review API documentation at `/docs`
3. Check test files for examples
4. Consult main README.md

---

**Status:** Phase 2 Complete ✅
**Version:** 2.0.0
**Maintainer:** Blackbox4 Core Team
**Last Updated:** 2026-01-15
