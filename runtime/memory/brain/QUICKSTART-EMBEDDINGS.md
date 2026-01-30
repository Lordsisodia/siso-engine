# Quick Start Guide - Brain v2.0 Embeddings

Get started with semantic search in 5 minutes.

---

## Option 1: Docker (Recommended)

### 1. Start Services

```bash
cd /Users/shaansisodia/DEV/AI-HUB/Black\ Box\ Factory/current/.blackbox4

# Start databases and API
docker-compose up -d postgres neo4j brain-api

# Wait for services to be healthy (check with docker-compose ps)
```

### 2. Ingest Metadata

```bash
cd 9-brain/ingest

# Ingest all artifacts
python ingester.py ../../

# Or ingest specific directory
python ingester.py ../../1-agents/ --local
```

### 3. Test Semantic Search

```bash
# Find similar artifacts
curl -X POST http://localhost:8000/api/v1/search/similar \
  -H "Content-Type: application/json" \
  -d '{"artifact_id": "orchestrator-agent-v1", "limit": 5}'

# Natural language query
curl -X POST http://localhost:8000/api/v1/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Find all specialist agents"}'
```

---

## Option 2: Local Python

### 1. Install Dependencies

```bash
cd /Users/shaansisodia/DEV/AI-HUB/Black\ Box\ Factory/current/.blackbox4/9-brain

pip install -r api/requirements.txt
```

### 2. Setup Database

```bash
# Start PostgreSQL
brew services start postgresql
# or
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=blackbox4brain pgvector/pgvector:pg16

# Create database
createdb blackbox4_brain

# Initialize schema
psql -d blackbox4_brain -f databases/init.sql
```

### 3. Configure Environment

```bash
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=blackbox4_brain
export PGUSER=postgres
export PGPASSWORD=blackbox4brain
```

### 4. Ingest and Search

```bash
# Ingest
cd ingest
python ingester.py ../../ --local

# Start API
cd ../api
python brain_api.py

# In another terminal, test
curl -X POST http://localhost:8000/api/v1/search/similar \
  -H "Content-Type: application/json" \
  -d '{"artifact_id": "orchestrator-agent-v1", "limit": 5}'
```

---

## Option 3: Use OpenAI Embeddings

```bash
# Set API key
export OPENAI_API_KEY="your-key-here"

# Ingest with OpenAI
cd 9-brain/ingest
python ingester.py ../../ --model text-embedding-3-small
```

---

## Verify Installation

### Check Database

```bash
psql -d blackbox4_brain -c "SELECT COUNT(*) FROM artifacts;"
psql -d blackbox4_brain -c "SELECT COUNT(*) FROM embeddings;"
```

### Check API

```bash
curl http://localhost:8000/health
```

### Test Search

```python
from query.vector import VectorSearch

with VectorSearch() as search:
    count = search.count_embeddings()
    print(f"Embeddings in database: {count}")
```

---

## Common Commands

### Generate Embeddings

```bash
# Single file
python embedder.py path/to/metadata.yaml

# Directory with local model
python embedder.py path/to/directory --local --local-model all-MiniLM-L6-v2

# With OpenAI
python embedder.py path/to/directory --model text-embedding-3-small
```

### Ingest Metadata

```bash
# With embeddings
python ingester.py path/to/directory

# Without embeddings
python ingester.py path/to/directory --no-embeddings

# Using local model
python ingester.py path/to/directory --local
```

### Parse Queries

```bash
# Test parser
python query/nl_parser.py "Find all specialist agents"

# With explanation
python query/nl_parser.py "What depends on the orchestrator?" --explain
```

### Run Tests

```bash
cd 9-brain/tests

# All tests
pytest test_embeddings.py -v

# Specific test
pytest test_embeddings.py::TestNLQueryParser -v

# With coverage
pytest test_embeddings.py --cov=.. --cov-report=html
```

---

## Troubleshooting

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart
docker-compose restart postgres
```

### Embedding Generation Failed

```bash
# Use local model instead
python embedder.py path/to/metadata.yaml --local

# Check API key
echo $OPENAI_API_KEY
```

### API Not Responding

```bash
# Check API is running
docker-compose ps brain-api

# Check logs
docker-compose logs brain-api

# Restart
docker-compose restart brain-api
```

### Poor Search Results

```python
# Adjust similarity threshold
results = search.semantic_search(
    query_vector=vector,
    min_similarity=0.7  # Increase for more precise results
)

# Use hybrid search
results = search.hybrid_search(
    query_vector=vector,
    text_query="your query",
    semantic_weight=0.7  # Balance semantic and text search
)
```

---

## Next Steps

1. ✅ Start services with Docker
2. ✅ Ingest your metadata
3. ✅ Test semantic search
4. 📖 Read full documentation: `README-embeddings.md`
5. 🧪 Run tests: `pytest 9-brain/tests/test_embeddings.py`
6. 🚀 Integrate with your workflow

---

## Getting Help

- **Full Guide**: `9-brain/README-embeddings.md`
- **API Docs**: http://localhost:8000/docs
- **Examples**: Check `9-brain/tests/` for usage examples
- **Issues**: Check `PHASE4-COMPLETE.md` for known issues

---

**Status**: Ready to use! 🚀
**Version**: 2.0.0
**Last Updated**: 2026-01-15
