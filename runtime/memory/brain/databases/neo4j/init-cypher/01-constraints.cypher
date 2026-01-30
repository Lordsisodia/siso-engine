// Blackbox4 Brain - Neo4j Initialization Script
// Creates constraints and indexes for optimal performance

// Create unique constraint on Artifact ID
CREATE CONSTRAINT artifact_id_unique IF NOT EXISTS
FOR (a:Artifact) REQUIRE a.id IS UNIQUE;

// Create unique constraint on Artifact path
CREATE CONSTRAINT artifact_path_unique IF NOT EXISTS
FOR (a:Artifact) REQUIRE a.path IS UNIQUE;

// Create indexes for common queries
CREATE INDEX artifact_type_index IF NOT EXISTS
FOR (a:Artifact) ON (a.type);

CREATE INDEX artifact_category_index IF NOT EXISTS
FOR (a:Artifact) ON (a.category);

CREATE INDEX artifact_status_index IF NOT EXISTS
FOR (a:Artifact) ON (a.status);

CREATE INDEX artifact_layer_index IF NOT EXISTS
FOR (a:Artifact) ON (a.layer);

CREATE INDEX artifact_phase_index IF NOT EXISTS
FOR (a:Artifact) ON (a.phase);

CREATE INDEX artifact_name_index IF NOT EXISTS
FOR (a:Artifact) ON (a.name);

CREATE INDEX artifact_tags_index IF NOT EXISTS
FOR (a:Artifact) ON (a.tags);

CREATE INDEX artifact_created_index IF NOT EXISTS
FOR (a:Artifact) ON (a.created);

CREATE INDEX artifact_modified_index IF NOT EXISTS
FOR (a:Artifact) ON (a.modified);

// Full-text search index
CREATE FULLTEXT INDEX artifact_fulltext IF NOT EXISTS
FOR (a:Artifact) ON EACH [a.name, a.description, a.tags]
OPTIONS {
  indexConfig: {
    `fulltext.analyzer`: "standard"
  }
};
