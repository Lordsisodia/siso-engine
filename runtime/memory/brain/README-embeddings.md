# Blackbox4 Brain v2.0 - Embeddings and Semantic Search

**Version:** 1.0.0
**Last Updated:** 2026-01-15
**Status:** Phase 4 Implementation

---

## Overview

Phase 4 implements vector embeddings and semantic search for the Blackbox4 Brain system. This enables AI to find artifacts by meaning rather than just keywords, making the brain truly intelligent.

### What's New

- **Embedding Generation**: Generate vectors for artifacts using OpenAI or local models
- **Semantic Search**: Find similar artifacts by meaning
- **Hybrid Search**: Combine semantic and full-text search
- **Natural Language Queries**: Parse and route queries to appropriate search methods
- **Embedding Cache**: Avoid re-generating embeddings with local cache
- **API Endpoints**: RESTful API for all search operations

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              EMBEDDING SYSTEM ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. EMBEDDING GENERATION                                     │
│     ├── embedder.py (artifact → vector)                     │
│     ├── OpenAI: text-embedding-3-small (1536 dims)          │
│     ├── Local: all-MiniLM-L6-v2 (384 dims)                  │
│     └── Cache: SQLite (avoid re-generation)                 │
│                                                              │
│  2. SEMANTIC SEARCH                                          │
│     ├── vector.py (pgvector search)                         │
│     ├── Cosine similarity                                   │
│     ├── Filters: type, category, status, tags              │
│     └── Hybrid: semantic + full-text                        │
│                                                              │
│  3. NATURAL LANGUAGE PARSER                                  │
│     ├── nl_parser.py (query → intent)                       │
│     ├── Intents: placement, discovery, relationship         │
│     ├── Entity extraction                                   │
│     └── Query routing                                       │
│                                                              │
│  4. INGESTION PIPELINE                                      │
│     ├── ingester.py (metadata → DB + embeddings)            │
│     ├── Validate → Insert → Embed                           │
│     └── Graceful fallback on errors                         │
│                                                              │
│  5. REST API                                                │
│     ├── brain_api.py (FastAPI)                              │
│     ├── /api/v1/search/semantic                             │
│     ├── /api/v1/search/similar                              │
│     ├── /api/v1/search/hybrid                               │
│     └── /api/v1/query/nl                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

```bash
# Python 3.9+
python --version

# PostgreSQL 15+ with pgvector
psql --version

# Optional: Neo4j 5+ for graph queries
neo4j --version
```

### Dependencies

```bash
# Core dependencies
pip install psycopg2-binary pyyaml sentence-transformers

# OpenAI embeddings (optional, required for OpenAI models)
pip install openai

# API server
pip install fastapi uvicorn

# Development
pip install pytest pytest-cov
```

### Database Setup

```bash
# Start PostgreSQL with pgvector
docker run -d \
  --name blackbox4-postgres \
  -e POSTGRES_PASSWORD=blackbox4brain \
  -e POSTGRES_DB=blackbox4_brain \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Initialize schema
psql -h localhost -U postgres -d blackbox4_brain -f 9-brain/databases/init.sql
```

---

## Usage

### 1. Generate Embeddings

#### For a Single Artifact

```bash
cd 9-brain/ingest
python embedder.py path/to/metadata.yaml
```

#### For a Directory

```bash
python embedder.py path/to/directory --output embeddings.json
```

#### Using Local Model

```bash
python embedder.py path/to/directory \
  --local \
  --local-model all-MiniLM-L6-v2 \
  --output embeddings.json
```

#### Using OpenAI

```bash
export OPENAI_API_KEY="your-key-here"
python embedder.py path/to/directory \
  --model text-embedding-3-small \
  --output embeddings.json
```

### 2. Ingest Metadata

```bash
# Ingest single file
python ingester.py path/to/metadata.yaml

# Ingest directory
python ingester.py path/to/directory

# With custom database
python ingester.py path/to/directory \
  --db-host localhost \
  --db-name blackbox4_brain

# Disable embeddings
python ingester.py path/to/directory --no-embeddings
```

### 3. Semantic Search

#### Via API

```bash
# Start API server
cd 9-brain/api
python brain_api.py --host 0.0.0.0 --port 8000

# Semantic search
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "agents for data analysis and research",
    "limit": 10,
    "filters": {
      "type": "agent",
      "status": "active"
    },
    "min_similarity": 0.5
  }'

# Find similar artifacts
curl -X POST http://localhost:8000/api/v1/search/similar \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_id": "orchestrator-agent-v1",
    "limit": 10
  }'

# Hybrid search
curl -X POST http://localhost:8000/api/v1/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "data analysis tools",
    "limit": 10,
    "semantic_weight": 0.7
  }'

# Natural language query
curl -X POST http://localhost:8000/api/v1/query/nl \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find all active specialist agents for data analysis"
  }'
```

#### Via Python

```python
from query.vector import VectorSearch

# Initialize search
with VectorSearch() as search:
    # Semantic search
    query_vector = [0.1, 0.2, ...]  # Your query vector
    results = search.semantic_search(
        query_vector=query_vector,
        limit=10,
        filters={"type": "agent"},
        min_similarity=0.5
    )

    for result in results:
        print(f"{result.name}: {result.similarity:.3f}")

    # Find similar
    similar = search.find_similar(
        artifact_id="orchestrator-agent-v1",
        limit=10
    )
```

### 4. Natural Language Queries

```python
from query.nl_parser import NLQueryParser, QueryExecutor

# Parse query
parser = NLQueryParser()
parsed = parser.parse("Find all specialist agents")

print(f"Intent: {parsed.intent}")
print(f"Entities: {parsed.entities}")
print(f"Filters: {parsed.filters}")

# Execute query
executor = QueryExecutor(vector_search=search)
result = executor.execute("Find all specialist agents")
```

---

## Model Options

### OpenAI Models

| Model | Dimensions | Cost | Performance |
|-------|-----------|------|-------------|
| text-embedding-3-small | 1536 | $0.02/1M tokens | Excellent |
| text-embedding-3-large | 3072 | $0.13/1M tokens | Best |
| text-embedding-ada-002 | 1536 | $0.10/1M tokens | Good |

**Recommendation**: Use `text-embedding-3-small` for best value.

### Local Models

| Model | Dimensions | Speed | Performance |
|-------|-----------|-------|-------------|
| all-MiniLM-L6-v2 | 384 | Fast | Good |
| all-mpnet-base-v2 | 768 | Medium | Excellent |
| paraphrase-MiniLM-L6-v2 | 384 | Fast | Good |

**Recommendation**: Use `all-MiniLM-L6-v2` for speed, `all-mpnet-base-v2` for quality.

### Choosing Between OpenAI and Local

**Use OpenAI if:**
- You have API budget
- Want best quality
- Need consistent embeddings across environments

**Use Local if:**
- No internet access
- Want zero cost
- Need data privacy
- Have limited API rate limits

---

## Performance Tuning

### Embedding Generation

```python
# Use local model for speed
embedder = ArtifactEmbedder(
    generator=EmbeddingGenerator(
        model="all-MiniLM-L6-v2",
        use_local=True
    )
)

# Enable caching
embedder = ArtifactEmbedder(
    generator=EmbeddingGenerator(
        cache_dir="/path/to/cache"
    )
)
```

### Semantic Search

```python
# Adjust min_similarity for precision
results = search.semantic_search(
    query_vector=vector,
    min_similarity=0.7  # Higher = more precise
)

# Use filters to reduce search space
results = search.semantic_search(
    query_vector=vector,
    filters={"type": "agent", "status": "active"}
)
```

### Hybrid Search

```python
# Adjust semantic_weight for balance
results = search.hybrid_search(
    query_vector=vector,
    text_query="data analysis",
    semantic_weight=0.7  # 0.7 = 70% semantic, 30% full-text
)
```

### Database Indexes

```sql
-- Ensure vector index exists
CREATE INDEX idx_embeddings_vector
ON embeddings USING ivfflat(vector vector_cosine_ops)
WITH (lists = 100);

-- Adjust lists based on data size
-- lists = sqrt(num_rows) is a good heuristic
```

---

## API Examples

### Semantic Search

```json
POST /api/v1/search/semantic
{
  "query": "agents for automation and workflows",
  "limit": 10,
  "filters": {
    "type": "agent",
    "category": "specialist",
    "status": "active"
  },
  "min_similarity": 0.6
}
```

### Similar Artifacts

```json
POST /api/v1/search/similar
{
  "artifact_id": "orchestrator-agent-v1",
  "limit": 10,
  "exclude_self": true
}
```

### Hybrid Search

```json
POST /api/v1/search/hybrid
{
  "query": "context variables and state management",
  "limit": 10,
  "filters": {
    "type": "library"
  },
  "semantic_weight": 0.7
}
```

### Natural Language Query

```json
POST /api/v1/query/nl
{
  "query": "What depends on the orchestrator agent?"
}
```

---

## Query Examples

### Placement Queries

```
"Where should I put a new specialist agent for data analysis?"
→ Returns: suggested path based on type and category

"Where does a workflow skill go?"
→ Returns: 1-agents/.skills/
```

### Discovery Queries

```
"Find all specialist agents"
→ Returns: all agents with category=specialist

"Show me active libraries for context management"
→ Returns: libraries with "context" in description
```

### Relationship Queries

```
"What depends on the orchestrator?"
→ Returns: dependency tree

"Find unused artifacts"
→ Returns: artifacts with no dependents
```

### Semantic Queries

```
"Find artifacts about data analysis"
→ Returns: semantically similar artifacts

"Show me similar agents to the orchestrator"
→ Returns: agents with similar embeddings
```

---

## Error Handling

### Embedding Generation Failures

```python
# Automatic fallback to local model
embedder = ArtifactEmbedder(
    generator=EmbeddingGenerator(
        model="text-embedding-3-small",
        use_local=False  # Falls back on error
    )
)

# Graceful degradation in ingester
ingester = BrainIngester(
    enable_embeddings=True  # Disables on failure
)
```

### API Errors

```json
{
  "success": false,
  "error": "Vector search not available",
  "details": "Database connection failed"
}
```

---

## Testing

```bash
# Run tests
cd 9-brain/tests
pytest test_embeddings.py -v

# With coverage
pytest test_embeddings.py --cov=.. --cov-report=html

# Specific test
pytest test_embeddings.py::TestNLQueryParser::test_detect_placement_intent -v
```

---

## Troubleshooting

### Issue: Embedding generation fails

**Solution**: Check API key or use local model

```bash
# Use local model
python embedder.py path/to/metadata.yaml --local
```

### Issue: Slow semantic search

**Solution**: Create vector index

```sql
CREATE INDEX idx_embeddings_vector
ON embeddings USING ivfflat(vector vector_cosine_ops)
WITH (lists = 100);
```

### Issue: Poor search results

**Solution**: Adjust similarity threshold or use hybrid search

```python
# Increase minimum similarity
results = search.semantic_search(
    query_vector=vector,
    min_similarity=0.7  # Higher threshold
)

# Or use hybrid search
results = search.hybrid_search(
    query_vector=vector,
    text_query=your_query,
    semantic_weight=0.6  # Balance semantic and text
)
```

---

## Performance Benchmarks

### Embedding Generation

| Model | Speed | Quality |
|-------|-------|---------|
| all-MiniLM-L6-v2 | ~100 docs/sec | Good |
| all-mpnet-base-v2 | ~50 docs/sec | Excellent |
| text-embedding-3-small | ~10 docs/sec | Excellent |

### Semantic Search

| Database Size | Query Time | With Filters |
|--------------|-----------|--------------|
| 1,000 | <10ms | <5ms |
| 10,000 | ~50ms | ~20ms |
| 100,000 | ~200ms | ~50ms |

---

## Best Practices

1. **Always use caching** for embedding generation
2. **Batch process** embeddings for multiple artifacts
3. **Use filters** to reduce search space
4. **Set appropriate similarity thresholds** (0.5-0.7)
5. **Monitor cache size** and clean periodically
6. **Use hybrid search** for best results
7. **Index vector column** for performance
8. **Fallback to local models** if API fails

---

## Next Steps

1. **Setup databases**: PostgreSQL + pgvector
2. **Ingest metadata**: Run ingester on your artifacts
3. **Generate embeddings**: Run embedder
4. **Start API server**: Launch brain_api.py
5. **Test queries**: Try semantic and NL queries
6. **Monitor performance**: Tune indexes and thresholds

---

## Support

For issues or questions:

1. Check this README
2. Review test files for examples
3. Check API docs at `/docs` endpoint
4. Consult main brain README

---

**Status**: Phase 4 Complete ✅
**Version**: 1.0.0
**Maintainer**: Blackbox4 Core Team
