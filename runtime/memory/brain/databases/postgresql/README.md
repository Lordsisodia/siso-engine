# PostgreSQL Database Setup

**Status:** Planned (Phase 2)
**Priority:** High

## Purpose

PostgreSQL with pgvector extension for:
- Structured queries (exact match, filters, aggregations)
- Vector similarity search (semantic search)
- Relationship storage (with foreign keys)

## Schema

See `../init.sql` for complete schema.

## Setup Instructions

```bash
# Install PostgreSQL 15+
brew install postgresql@15

# Install pgvector extension
git clone --branch v0.5.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
make install # may need sudo

# Create database
createdb blackbox4_brain

# Enable pgvector
psql blackbox4_brain -c "CREATE EXTENSION vector;"

# Run schema
psql blackbox4_brain < ../init.sql
```

## Connection String

```
postgresql://localhost:5432/blackbox4_brain
```

## Requirements

- PostgreSQL 15+
- pgvector extension
- Python asyncpg driver

## Status

⏳ Pending Phase 2 implementation
