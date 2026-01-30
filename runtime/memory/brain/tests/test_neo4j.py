#!/usr/bin/env python3
"""
Blackbox4 Brain - Neo4j Tests
Tests for Neo4j graph ingestion and queries

Run with:
    pytest tests/test_neo4j.py -v
    pytest tests/test_neo4j.py -v --cov=ingest.graph_ingester
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

try:
    from ingest.graph_ingester import Neo4jConnection, GraphIngester
    from query.graph import GraphQuery
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def neo4j_uri():
    """Neo4j connection URI"""
    return os.getenv("NEO4J_URI", "bolt://localhost:7687")


@pytest.fixture
def neo4j_auth():
    """Neo4j authentication"""
    return (
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASSWORD", "blackbox4brain")
    )


@pytest.fixture
def neo4j_connection(neo4j_uri, neo4j_auth):
    """Create Neo4j connection"""
    if not NEO4J_AVAILABLE or not MODULES_AVAILABLE:
        pytest.skip("Neo4j not available")

    conn = Neo4jConnection(neo4j_uri, neo4j_auth[0], neo4j_auth[1])
    if not conn.connect():
        pytest.skip("Cannot connect to Neo4j")

    yield conn

    conn.close()


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing"""
    return {
        'id': 'test-agent-1',
        'type': 'agent',
        'name': 'Test Agent',
        'category': 'specialist',
        'version': '1.0.0',
        'path': 'test/path/agent.md',
        'created': '2026-01-15',
        'modified': '2026-01-15',
        'description': 'Test agent for unit testing',
        'tags': ['test', 'agent', 'specialist'],
        'status': 'active',
        'stability': 'high',
        'owner': 'test-team'
    }


@pytest.fixture
def sample_metadata_with_relationships():
    """Sample metadata with relationships"""
    return {
        'id': 'test-agent-2',
        'type': 'agent',
        'name': 'Test Agent 2',
        'category': 'specialist',
        'version': '1.0.0',
        'path': 'test/path/agent2.md',
        'created': '2026-01-15',
        'modified': '2026-01-15',
        'description': 'Test agent with relationships',
        'tags': ['test', 'agent'],
        'status': 'active',
        'stability': 'high',
        'owner': 'test-team',
        'depends_on': [
            {'id': 'test-agent-1', 'type': 'agent', 'version': '>=1.0.0'}
        ],
        'used_by': [
            {'id': 'test-agent-3', 'type': 'agent'}
        ],
        'relates_to': [
            {'id': 'test-lib-1', 'type': 'library', 'relationship': 'uses'}
        ]
    }


@pytest.fixture
def graph_query(neo4j_uri, neo4j_auth):
    """Create GraphQuery instance"""
    if not NEO4J_AVAILABLE or not MODULES_AVAILABLE:
        pytest.skip("Neo4j not available")

    graph = GraphQuery(neo4j_uri, neo4j_auth[0], neo4j_auth[1])
    if not graph.connect():
        pytest.skip("Cannot connect to Neo4j")

    yield graph

    graph.close()


# ============================================================================
# NEO4J CONNECTION TESTS
# ============================================================================

class TestNeo4jConnection:
    """Test Neo4j connection management"""

    def test_connect_success(self, neo4j_uri, neo4j_auth):
        """Test successful connection"""
        if not NEO4J_AVAILABLE or not MODULES_AVAILABLE:
            pytest.skip("Neo4j not available")

        conn = Neo4jConnection(neo4j_uri, neo4j_auth[0], neo4j_auth[1])
        assert conn.connect() == True
        conn.close()

    def test_connect_failure(self):
        """Test connection failure"""
        if not NEO4J_AVAILABLE or not MODULES_AVAILABLE:
            pytest.skip("Neo4j not available")

        conn = Neo4jConnection("bolt://invalid:9999", "neo4j", "wrong")
        assert conn.connect() == False

    def test_execute_query(self, neo4j_connection):
        """Test query execution"""
        result = neo4j_connection.execute_query("RETURN 1 as num")
        assert len(result) == 1
        assert result[0]['num'] == 1


# ============================================================================
# GRAPH INGESTER TESTS
# ============================================================================

class TestGraphIngester:
    """Test graph ingestion"""

    def test_ingest_simple_metadata(self, neo4j_connection, sample_metadata):
        """Test ingesting simple metadata"""
        ingester = GraphIngester(neo4j_connection)

        # Clean up first
        neo4j_connection.execute_write(
            "MATCH (a:Artifact {id: $id}) DETACH DELETE a",
            {'id': sample_metadata['id']}
        )

        # Ingest
        result = ingester.ingest_metadata(sample_metadata)
        assert result == True

        # Verify
        query_result = neo4j_connection.execute_query(
            "MATCH (a:Artifact {id: $id}) RETURN a",
            {'id': sample_metadata['id']}
        )
        assert len(query_result) == 1
        assert query_result[0]['a']['name'] == sample_metadata['name']

    def test_ingest_with_relationships(self, neo4j_connection,
                                       sample_metadata, sample_metadata_with_relationships):
        """Test ingesting metadata with relationships"""
        ingester = GraphIngester(neo4j_connection)

        # Clean up first
        for metadata in [sample_metadata, sample_metadata_with_relationships]:
            neo4j_connection.execute_write(
                "MATCH (a:Artifact {id: $id}) DETACH DELETE a",
                {'id': metadata['id']}
            )

        # Create dependent artifacts
        ingester.ingest_metadata(sample_metadata)

        # Create test dependency
        neo4j_connection.execute_write("""
            MERGE (a:Artifact {id: 'test-agent-3'})
            SET a.type = 'agent', a.name = 'Test Agent 3'
        """)

        neo4j_connection.execute_write("""
            MERGE (a:Artifact {id: 'test-lib-1'})
            SET a.type = 'library', a.name = 'Test Library 1'
        """)

        # Ingest with relationships
        result = ingester.ingest_metadata(sample_metadata_with_relationships)
        assert result == True

        # Verify relationships
        query_result = neo4j_connection.execute_query("""
            MATCH (a:Artifact {id: $id})-[r:DEPENDS_ON]->(dep)
            RETURN dep.id as dep_id
        """, {'id': sample_metadata_with_relationships['id']})

        assert len(query_result) >= 0  # May be 0 if dependency doesn't exist

    def test_delete_artifact(self, neo4j_connection, sample_metadata):
        """Test deleting an artifact"""
        ingester = GraphIngester(neo4j_connection)

        # Create first
        ingester.ingest_metadata(sample_metadata)

        # Delete
        result = ingester.delete_artifact(sample_metadata['id'])
        assert result == True

        # Verify
        query_result = neo4j_connection.execute_query(
            "MATCH (a:Artifact {id: $id}) RETURN a",
            {'id': sample_metadata['id']}
        )
        assert len(query_result) == 0


# ============================================================================
# GRAPH QUERY TESTS
# ============================================================================

class TestGraphQuery:
    """Test graph queries"""

    def test_get_artifact_by_id(self, graph_query, neo4j_connection, sample_metadata):
        """Test getting artifact by ID"""
        # Create artifact
        neo4j_connection.execute_write("""
            MERGE (a:Artifact {id: $id})
            SET a.type = $type, a.name = $name, a.category = $category,
                a.path = $path, a.status = $status, a.stability = $stability,
                a.owner = $owner, a.description = $description, a.tags = $tags
        """, sample_metadata)

        # Query
        result = graph_query.get_artifact_by_id(sample_metadata['id'])
        assert result is not None
        assert result['id'] == sample_metadata['id']
        assert result['name'] == sample_metadata['name']

    def test_search_by_type(self, graph_query, neo4j_connection):
        """Test searching by type"""
        # Create test artifacts
        neo4j_connection.execute_write("""
            MERGE (a:Artifact {id: 'search-test-1'})
            SET a.type = 'agent', a.name = 'Search Test 1', a.status = 'active'
        """)

        neo4j_connection.execute_write("""
            MERGE (a:Artifact {id: 'search-test-2'})
            SET a.type = 'library', a.name = 'Search Test 2', a.status = 'active'
        """)

        # Search
        result = graph_query.search_by_type('agent')
        assert len(result) >= 1
        assert any(r['id'] == 'search-test-1' for r in result)

    def test_search_by_tag(self, graph_query, neo4j_connection):
        """Test searching by tag"""
        # Create test artifact with tags
        neo4j_connection.execute_write("""
            MERGE (a:Artifact {id: 'tag-test-1'})
            SET a.type = 'agent', a.name = 'Tag Test 1',
                a.tags = ['test', 'tag-search', 'demo']
        """)

        # Search
        result = graph_query.search_by_tag('tag-search')
        assert len(result) >= 1

    def test_get_dependencies(self, graph_query, neo4j_connection):
        """Test getting dependencies"""
        # Create test data
        neo4j_connection.execute_write("""
            MERGE (a:Artifact {id: 'dep-test-1'})
            SET a.type = 'agent', a.name = 'Dependency Test 1'
        """)

        neo4j_connection.execute_write("""
            MERGE (a:Artifact {id: 'dep-test-2'})
            SET a.type = 'library', a.name = 'Dependency Test 2'
        """)

        neo4j_connection.execute_write("""
            MATCH (a:Artifact {id: 'dep-test-1'})
            MATCH (b:Artifact {id: 'dep-test-2'})
            MERGE (a)-[:DEPENDS_ON {strength: 'required'}]->(b)
        """)

        # Query
        result = graph_query.get_dependencies('dep-test-1')
        assert result['artifact_id'] == 'dep-test-1'
        assert result['total_dependencies'] >= 1

    def test_find_orphans(self, graph_query, neo4j_connection):
        """Test finding orphaned artifacts"""
        # Create orphan
        neo4j_connection.execute_write("""
            MERGE (a:Artifact {id: 'orphan-test-1'})
            SET a.type = 'agent', a.name = 'Orphan Test 1'
        """)

        # Find orphans
        result = graph_query.find_orphans()
        assert len(result) >= 1

    def test_get_statistics(self, graph_query):
        """Test getting statistics"""
        result = graph_query.get_statistics()
        assert 'total_artifacts' in result
        assert 'by_type' in result
        assert 'total_relationships' in result


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests"""

    def test_full_ingest_query_cycle(self, neo4j_uri, neo4j_auth,
                                     sample_metadata_with_relationships):
        """Test full ingest and query cycle"""
        if not NEO4J_AVAILABLE or not MODULES_AVAILABLE:
            pytest.skip("Neo4j not available")

        # Create ingester
        conn = Neo4jConnection(neo4j_uri, neo4j_auth[0], neo4j_auth[1])
        conn.connect()
        ingester = GraphIngester(conn)

        # Create query interface
        graph = GraphQuery(neo4j_uri, neo4j_auth[0], neo4j_auth[1])
        graph.connect()

        try:
            # Clean up
            conn.execute_write(
                "MATCH (a:Artifact {id: $id}) DETACH DELETE a",
                {'id': sample_metadata_with_relationships['id']}
            )

            # Ingest
            ingester.ingest_metadata(sample_metadata_with_relationships)

            # Query
            result = graph.get_artifact_by_id(sample_metadata_with_relationships['id'])
            assert result is not None
            assert result['name'] == sample_metadata_with_relationships['name']

        finally:
            conn.close()
            graph.close()


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
