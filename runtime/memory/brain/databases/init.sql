-- Blackbox4 Brain v2.0 - Database Schema
-- PostgreSQL 15+ with pgvector extension
-- Version: 1.0.0

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- ARTIFACTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS artifacts (
    -- Core Identification
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    category TEXT,
    name TEXT NOT NULL,
    version TEXT,

    -- Location
    path TEXT UNIQUE NOT NULL,
    created DATE NOT NULL,
    modified DATE NOT NULL,

    -- Content
    description TEXT,
    tags TEXT[] NOT NULL,
    keywords TEXT[],

    -- Classification
    phase INTEGER,
    layer TEXT,

    -- Status
    status TEXT NOT NULL,
    stability TEXT NOT NULL,

    -- Ownership
    owner TEXT NOT NULL,
    maintainer TEXT,

    -- Metrics
    usage_count INTEGER DEFAULT 0,
    last_used DATE,
    success_rate FLOAT,

    -- Timestamps
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- EMBEDDINGS TABLE (pgvector)
-- ============================================================================

CREATE TABLE IF NOT EXISTS embeddings (
    artifact_id TEXT PRIMARY KEY,
    vector vector(1536),  -- OpenAI text-embedding-ada-002 size
    model TEXT DEFAULT 'text-embedding-ada-002',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE CASCADE
);

-- ============================================================================
-- RELATIONSHIPS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS relationships (
    from_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    strength FLOAT DEFAULT 1.0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (from_id, to_id, relationship_type),
    FOREIGN KEY (from_id) REFERENCES artifacts(id) ON DELETE CASCADE,
    FOREIGN KEY (to_id) REFERENCES artifacts(id) ON DELETE CASCADE
);

-- ============================================================================
-- INDEXES (Performance)
-- ============================================================================

-- Artifact indexes
CREATE INDEX idx_artifacts_type ON artifacts(type);
CREATE INDEX idx_artifacts_category ON artifacts(category);
CREATE INDEX idx_artifacts_phase ON artifacts(phase) WHERE phase IS NOT NULL;
CREATE INDEX idx_artifacts_layer ON artifacts(layer);
CREATE INDEX idx_artifacts_status ON artifacts(status);
CREATE INDEX idx_artifacts_stability ON artifacts(stability);
CREATE INDEX idx_artifacts_owner ON artifacts(owner);

-- Tag/keyword indexes (GIN for array search)
CREATE INDEX idx_artifacts_tags ON artifacts USING GIN(tags);
CREATE INDEX idx_artifacts_keywords ON artifacts USING GIN(keywords);

-- Full-text search
CREATE INDEX idx_artifacts_description_fts ON artifacts USING GIN(to_tsvector('english', description));

-- Path index for wildcard searches
CREATE INDEX idx_artifacts_path ON artifacts(path);

-- Embedding vector index (IVFFlat for approximate search)
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat(vector vector_cosine_ops) WITH (lists = 100);

-- Relationship indexes
CREATE INDEX idx_relationships_from ON relationships(from_id);
CREATE INDEX idx_relationships_to ON relationships(to_id);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);

-- Composite indexes for common queries
CREATE INDEX idx_artifacts_type_category ON artifacts(type, category);
CREATE INDEX idx_artifacts_type_status ON artifacts(type, status);
CREATE INDEX idx_artifacts_phase_type ON artifacts(phase, type) WHERE phase IS NOT NULL;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_artifacts_updated_at BEFORE UPDATE ON artifacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS (Common Queries)
-- ============================================================================

-- Active artifacts view
CREATE OR REPLACE VIEW active_artifacts AS
SELECT * FROM artifacts WHERE status = 'active';

-- Artifacts by phase view
CREATE OR REPLACE VIEW phase_artifacts AS
SELECT * FROM artifacts WHERE phase IS NOT NULL;

-- Orphaned artifacts (no relationships)
CREATE OR REPLACE VIEW orphaned_artifacts AS
SELECT a.*
FROM artifacts a
WHERE a.id NOT IN (SELECT from_id FROM relationships)
  AND a.id NOT IN (SELECT to_id FROM relationships);

-- Popular artifacts (high usage)
CREATE OR REPLACE VIEW popular_artifacts AS
SELECT * FROM artifacts
WHERE usage_count > 100
ORDER BY usage_count DESC;

-- ============================================================================
-- SAMPLE QUERIES (Reference)
-- ============================================================================

-- Find all specialist agents
-- SELECT name, path, description
-- FROM artifacts
-- WHERE type = 'agent' AND category = 'specialist' AND status = 'active';

-- Find all Phase 4 artifacts
-- SELECT type, category, COUNT(*)
-- FROM artifacts
-- WHERE phase = 4
-- GROUP BY type, category;

-- Find unused artifacts (not used in >30 days)
-- SELECT name, path, last_used
-- FROM artifacts
-- WHERE last_used < CURRENT_DATE - INTERVAL '30 days';

-- Find agents by tag
-- SELECT name, path
-- FROM artifacts
-- WHERE type = 'agent' AND 'orchestration' = ANY(tags);

-- Find what depends on a library
-- SELECT a.name, a.path, r.relationship_type
-- FROM artifacts a
-- JOIN relationships r ON r.from_id = a.id
-- WHERE r.to_id = 'ralph-runtime';

-- Semantic search (find similar artifacts)
-- SELECT a.name, a.path, a.description,
--        1 - (e.vector <=> '[query_vector]') as similarity
-- FROM artifacts a
-- JOIN embeddings e ON e.artifact_id = a.id
-- ORDER BY e.vector <=> '[query_vector]'
-- LIMIT 10;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
