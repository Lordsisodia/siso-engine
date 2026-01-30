# Blackbox4 Brain v2.0

**Last Updated:** 2026-01-15
**Status:** Phase 2 - PostgreSQL Ingestion and Query System (Complete)
**Version:** 2.0.0

---

## Overview

The **Blackbox4 Brain** is a machine-native, queryable intelligence system that enables AI to understand, navigate, and reason about the entire Blackbox4 architecture. Unlike v1 (documentation-based), v2 uses structured metadata, databases, and semantic search to provide instant answers to complex questions.

### What It Does

- **Instant Discovery:** Find any artifact in seconds
- **Intelligent Routing:** Know exactly where to place new artifacts
- **Relationship Mapping:** Understand dependencies and impact
- **Semantic Search:** Find related artifacts by meaning, not just keywords
- **Auto-Indexing:** Automatically stay up-to-date as files change

### Key Benefits

| Feature | v1 (Documentation) | v2 (Brain System) |
|---------|-------------------|-------------------|
| Query Speed | Manual search | <1 second |
| Placement | Manual lookup | Automatic routing |
| Relationships | Implied | Explicit graph |
| Discovery | Keywords | Semantic similarity |
| Maintenance | High (manual) | Low (automatic) |
| AI Integration | Read docs | Query databases |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  BLACKBOX4 BRAIN v2.0                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PHASE 1: Metadata Schema ✅                                │
│  ├── Every artifact has metadata.yaml                       │
│  ├── Complete schema definition                             │
│  ├── Validation script                                      │
│  └── Template generator                                     │
│                                                              │
│  PHASE 2: Databases ✅                                      │
│  ├── PostgreSQL (structured queries) ✅                     │
│  ├── Metadata ingestion pipeline ✅                         │
│  ├── Query interface ✅                                      │
│  ├── REST API ✅                                             │
│  ├── File watcher ✅                                         │
│  └── Tests ✅                                                │
│                                                              │
│  PHASE 3: Enhanced Query API (Planned)                      │
│  ├── Natural language parser                                │
│  ├── Query routing                                         │
│  ├── Result aggregation                                    │
│  └── AI integration interface                              │
│                                                              │
│  PHASE 4: Semantic Search (Planned)                         │
│  ├── Embedding generation                                  │
│  ├── Vector similarity search                              │
│  ├── Auto-tagging                                          │
│  └── Recommendations                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
9-brain/
├── metadata/                  # Metadata specifications
│   ├── schema.yaml           # Complete schema definition
│   └── examples/             # Example metadata files
│       ├── agent-metadata.yaml
│       ├── skill-metadata.yaml
│       ├── library-metadata.yaml
│       └── plan-metadata.yaml
│
├── ingest/                    # Ingestion scripts
│   ├── validator.py          # Validate metadata.yaml files
│   └── template.py           # Generate metadata templates
│
├── query/                     # Query interface (Phase 3)
│   └── (planned)
│
├── databases/                 # Database configs (Phase 2)
│   ├── postgresql/           # PostgreSQL setup
│   ├── neo4j/                # Neo4j setup
│   └── init.sql              # Schema initialization
│
├── api/                       # Query API (Phase 3)
│   └── (planned)
│
├── tests/                     # Tests
│   └── (planned)
│
├── README.md                  # This file
└── .purpose.md               # Purpose statement
```

---

## Quick Start with Neo4j

```bash
# Start Neo4j
cd 9-brain/databases/neo4j
./start.sh

# Ingest metadata
cd ../../ingest
python graph_ingester.py --sync

# Query the graph
cd ../query
python graph.py dependencies orchestrator-agent-v1
python graph.py impact context-variables-lib
python graph.py orphans

# Start API
cd ../api
python brain_api.py
# Access at http://localhost:8000
```

For detailed Neo4j setup, see [README-neo4j.md](README-neo4j.md)

---

## Quick Start (Phase 2: PostgreSQL)

### 1. Start PostgreSQL

```bash
cd 9-brain/databases
./start.sh
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Ingest Metadata

```bash
cd ../ingest
python ingester.py
```

### 4. Query Artifacts

**Python API:**
```python
from query.sql import BrainQuery
import asyncio

async def query():
    q = BrainQuery()
    await q.initialize()

    # Find all agents
    agents = await q.find_by_type('agent')

    # Find dependencies
    deps = await q.find_dependencies('orchestrator-agent-v1')

    # Full-text search
    results = await q.search('orchestration')

    await q.close()

asyncio.run(query())
```

**REST API:**
```bash
# Start API
cd ../api
python brain_api.py

# Query (in another terminal)
curl http://localhost:8000/api/v1/artifacts/type/agent
curl "http://localhost:8000/api/v1/query/search?q=orchestration"
curl http://localhost:8000/api/v1/statistics
```

### 5. Start File Watcher (Optional)

```bash
cd ../ingest
python watch_cli.py
```

**For detailed setup and usage, see [README-postgres.md](README-postgres.md)**

---

## Phase 1: Metadata Schema System

### What's Implemented

✅ **Complete Metadata Schema** (`metadata/schema.yaml`)
- Full field definitions with types and validation rules
- Type-specific categories and constraints
- Relationship definitions
- Examples for all artifact types

✅ **Example Metadata Files** (`metadata/examples/`)
- Agent metadata example
- Skill metadata example
- Library metadata example
- Plan metadata example

✅ **Metadata Validator** (`ingest/validator.py`)
- Validate metadata.yaml files against schema
- Command-line interface
- Directory-wide validation
- Clear error messages

✅ **Template Generator** (`ingest/template.py`)
- Interactive template generation
- Command-line interface
- Type-specific templates
- Sensible defaults

### How to Use

#### 1. Create Metadata for Your Artifact

**Interactive Mode:**
```bash
cd 9-brain/ingest
python template.py --interactive
```

**Command-Line Mode:**
```bash
python template.py \
  --type agent \
  --name "My Specialist Agent" \
  --category specialist \
  --description "Does amazing things" \
  --tags "specialist,automation,workflow" \
  --output /path/to/artifact/metadata.yaml
```

#### 2. Validate Metadata

**Validate Single File:**
```bash
cd 9-brain/ingest
python validator.py /path/to/metadata.yaml
```

**Validate Directory:**
```bash
python validator.py --directory /path/to/directory
```

**Check Schema:**
```bash
python validator.py --schema
```

#### 3. Add to Your Artifact

Place the generated `metadata.yaml` in your artifact directory:

```
my-agent/
├── metadata.yaml          ← REQUIRED
├── my-agent.md            (or .py, .sh, etc.)
├── examples/
│   └── metadata.yaml      ← REQUIRED (if examples exist)
└── tests/
    └── metadata.yaml      ← REQUIRED (if tests exist)
```

---

## Metadata Schema

### Required Fields

Every artifact MUST have these fields:

```yaml
# Core Identification
id: "unique-id"                    # Required: Unique identifier
type: "agent"                      # Required: Artifact type
name: "My Agent"                   # Required: Human-readable name
category: "specialist"             # Required: Category within type

# Location
path: "1-agents/4-specialists/"    # Required: Relative path
created: "2026-01-15"              # Required: Creation date
modified: "2026-01-15"             # Required: Last modification

# Content
description: "Does X, Y, Z"        # Required: Detailed description
tags: ["tag1", "tag2"]             # Required: At least one tag

# Status
status: "active"                   # Required: current status
stability: "high"                  # Required: stability level

# Ownership
owner: "core-team"                 # Required: responsible team
```

### Optional Fields

These fields are recommended but not required:

```yaml
# Version
version: "1.0.0"                   # Optional: Semantic version

# Search
keywords: ["synonym", "alt"]       # Optional: Search keywords

# Relationships
depends_on:                         # Optional: Dependencies
  - id: "other-artifact"
    type: "library"

used_by:                            # Optional: Dependents
  - id: "dependent-agent"
    type: "agent"

relates_to:                         # Optional: Related artifacts
  - id: "related"
    type: "library"
    relationship: "uses"

# Classification
phase: 4                           # Optional: Phase 1-4
layer: "intelligence"              # Optional: System layer

# Documentation
docs:                              # Optional: Documentation links
  primary: ".docs/reference.md"
  examples: "path/to/examples/"
  api: ".docs/api.md"

# Metrics
usage_count: 100                   # Optional: Usage tracking
last_used: "2026-01-15"           # Optional: Last use date
success_rate: 0.95                 # Optional: Success rate
```

### Valid Types

- `agent` - AI agent definition
- `skill` - Reusable workflow/framework skill
- `plan` - Project plan with tasks
- `library` - Reusable code library
- `script` - Executable script
- `template` - Template/pattern
- `document` - Documentation
- `test` - Test code
- `config` - Configuration file
- `module` - Functional module
- `framework` - Framework pattern
- `tool` - Maintenance/utility tool
- `workspace` - Workspace/project
- `example` - Example code/usage

### Valid Categories by Type

**Agent:** core, bmad, research, specialist, enhanced
**Skill:** core, mcp, workflow
**Library:** context-variables, hierarchical-tasks, task-breakdown, spec-creation, ralph-runtime, circuit-breaker, response-analyzer
**Script:** agents, planning, testing, integration, validation
**Test:** unit, integration, phase, e2e
**Document:** getting-started, architecture, components, frameworks, workflows, reference
**Template:** documents, plans, code, specs
**Module:** context, planning, research, kanban
**Framework:** bmad, speckit, metagpt, swarm
**Tool:** maintenance, migration, validation

---

## Examples

### Agent Metadata

```yaml
id: "orchestrator-agent-v1"
type: "agent"
name: "Orchestrator Agent"
category: "specialist"
version: "1.0.0"

path: "1-agents/4-specialists/orchestrator.md"
created: "2026-01-15"
modified: "2026-01-15"

description: |
  Main orchestrator agent for coordinating other agents and
  managing complex workflows.

tags:
  - "orchestration"
  - "coordination"
  - "agent-handoff"

status: "active"
stability: "high"
owner: "core-team"
```

See `metadata/examples/agent-metadata.yaml` for complete example.

### Library Metadata

```yaml
id: "context-variables-lib"
type: "library"
name: "Context Variables Library"
category: "context-variables"
version: "1.0.0"

path: "4-scripts/lib/context-variables/"
created: "2026-01-15"
modified: "2026-01-15"

description: |
  Python library for managing context variables in AI agent
  workflows.

tags:
  - "context"
  - "variables"
  - "state-management"

phase: 1
layer: "execution"

status: "active"
stability: "high"
owner: "core-team"
```

See `metadata/examples/library-metadata.yaml` for complete example.

---

## Validation

The validator checks:

✅ **Required fields** - All required fields present
✅ **Data types** - Correct data types for all fields
✅ **Valid values** - Enums, ranges, patterns
✅ **Type-Category consistency** - Category valid for type
✅ **Date consistency** - Modified >= Created
✅ **Relationship structure** - Valid relationship objects
✅ **Path format** - Matches Blackbox4 structure

Run validation:
```bash
python ingest/validator.py path/to/metadata.yaml
```

---

## Template Generator

The template generator provides:

✅ **Type-specific templates** - Pre-configured for each type
✅ **Interactive mode** - Guided setup
✅ **Sensible defaults** - Auto-fill common values
✅ **Path generation** - Auto-generate correct paths
✅ **Category validation** - Only valid categories

Run generator:
```bash
# Interactive
python ingest/template.py --interactive

# Command-line
python ingest/template.py \
  --type agent \
  --name "My Agent" \
  --category specialist \
  --output metadata.yaml
```

---

## Phase 2: Databases ✅

### PostgreSQL Database

**Status:** Complete

Setup:
```bash
# See databases/postgresql/README.md for full setup
createdb blackbox4_brain
psql blackbox4_brain < databases/init.sql
```

### Neo4j Graph Database

**Status:** Complete

Setup:
```bash
cd databases/neo4j
./start.sh
```

Features:
- ✅ Docker Compose configuration
- ✅ Graph ingestion pipeline
- ✅ Graph query interface
- ✅ REST API endpoints
- ✅ Relationship queries
- ✅ Impact analysis
- ✅ Path finding
- ✅ Orphan detection
- ✅ Circular dependency detection

Documentation: [README-neo4j.md](README-neo4j.md)

---

## Phase 3: Query API ✅

### Graph Query Interface

**Location:** `query/graph.py`

```python
from query.graph import GraphQuery

graph = GraphQuery()
graph.connect()

# Dependency analysis
deps = graph.get_dependencies('artifact-id')

# Impact analysis
impact = graph.get_impact_analysis('artifact-id')

# Path finding
path = graph.get_shortest_path('artifact-a', 'artifact-b')

# Find orphans
orphans = graph.find_orphans()

# Circular dependencies
cycles = graph.find_circular_dependencies()
```

### REST API

**Location:** `api/brain_api.py`

Start server:
```bash
cd api
python brain_api.py
```

Available endpoints:
- `POST /api/v1/graph/query` - Execute Cypher query
- `GET /api/v1/graph/dependencies/{id}` - Get dependency tree
- `GET /api/v1/graph/dependents/{id}` - Get dependents
- `GET /api/v1/graph/impact/{id}` - Impact analysis
- `GET /api/v1/graph/path/{from}/{to}` - Shortest path
- `GET /api/v1/graph/orphans` - Find orphans
- `GET /api/v1/graph/circular` - Find circular dependencies
- `GET /api/v1/graph/unused` - Find unused artifacts
- `GET /api/v1/graph/relationships/{id}` - Get relationships
- `GET /api/v1/graph/stats` - Graph statistics

API Documentation: http://localhost:8000/docs

---

## Next Phases

### Phase 4: Auto-Indexing (Planned)

- File watcher for automatic updates
- Embedding generation
- Incremental index updates
- Performance optimization

---

## Integration with AI

Once Phase 2-4 are complete, AI will be able to:

**Placement:**
```
AI: "Where should I put a new specialist agent for data analysis?"
Brain: "Place at: 1-agents/4-specialists/data-analyst.md"
```

**Discovery:**
```
AI: "Find all libraries related to task management"
Brain: [Returns ranked list with similarity scores]
```

**Relationships:**
```
AI: "What will break if I modify the orchestrator?"
Brain: [Returns dependency tree]
```

**Similarity:**
```
AI: "Find agents similar to the orchestrator"
Brain: [Returns similar agents with scores]
```

---

## Requirements

### Phase 1 (Current)

- Python 3.9+
- PyYAML (`pip install pyyaml`)

### Phase 2-4 (Planned)

- PostgreSQL 15+ with pgvector
- Neo4j 5+
- OpenAI API or sentence-transformers
- Additional Python packages

---

## Contributing

When adding new artifacts to Blackbox4:

1. **Create metadata.yaml** using the template generator
2. **Place it** in your artifact directory
3. **Validate it** using the validator
4. **Commit it** with your artifact

This ensures the brain system can index and query your artifact.

---

## Support

For questions or issues:
1. Check this README
2. Review examples in `metadata/examples/`
3. Run `python ingest/validator.py --schema` for field info
4. Consult `.docs/BRAIN-ARCHITECTURE-v2.md` for design details

---

**Status:** Phase 3 Complete ✅
**Version:** 2.0.0
**Maintainer:** Blackbox4 Core Team
**Last Updated:** 2026-01-15
