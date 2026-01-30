"""
Blackbox4 Brain v2.0 - PostgreSQL Tests
Test PostgreSQL ingestion and query system.
"""

import pytest
import asyncio
from datetime import datetime, date
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.db import Database, execute_query
from ingest.parser import parse_metadata_file
from ingest.ingester import MetadataIngester
from query.sql import BrainQuery


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def db(event_loop):
    """Initialize database for tests."""
    await Database.initialize()
    yield

    # Cleanup
    await execute_query("DELETE FROM relationships")
    await execute_query("DELETE FROM artifacts")
    await Database.close()


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {
        'artifact': {
            'id': 'test-agent-1',
            'type': 'agent',
            'category': 'specialist',
            'name': 'Test Agent',
            'version': '1.0.0',
            'path': '1-agents/4-specialists/test-agent.md',
            'created': '2026-01-15',
            'modified': '2026-01-15',
            'description': 'A test agent for unit testing',
            'tags': ['test', 'agent', 'specialist'],
            'keywords': ['testing', 'automation'],
            'phase': 4,
            'layer': 'intelligence',
            'status': 'active',
            'stability': 'high',
            'owner': 'test-team',
            'maintainer': 'test-user',
            'usage_count': 0,
            'last_used': None,
            'success_rate': None,
        },
        'relationships': [
            {
                'from_id': 'test-agent-1',
                'to_id': 'test-lib-1',
                'relationship_type': 'depends_on',
                'strength': 1.0,
                'metadata': {'id': 'test-lib-1', 'type': 'library'}
            }
        ],
        'docs': {},
        'metadata_path': '/tmp/test-metadata.yaml'
    }


# -----------------------------------------------------------------------------
# Database Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_database_connection(db):
    """Test database connection."""
    result = await execute_query("SELECT 1", fetch='val')
    assert result == 1


@pytest.mark.asyncio
async def test_insert_artifact(db, sample_metadata):
    """Test inserting an artifact."""
    artifact = sample_metadata['artifact']

    await execute_query("""
        INSERT INTO artifacts (
            id, type, category, name, version, path, created, modified,
            description, tags, keywords, phase, layer, status, stability,
            owner, maintainer, usage_count, last_used, success_rate
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
            $15, $16, $17, $18, $19, $20
        )
    """,
    artifact['id'], artifact['type'], artifact['category'], artifact['name'],
    artifact['version'], artifact['path'], artifact['created'], artifact['modified'],
    artifact['description'], artifact['tags'], artifact['keywords'], artifact['phase'],
    artifact['layer'], artifact['status'], artifact['stability'], artifact['owner'],
    artifact['maintainer'], artifact['usage_count'], artifact['last_used'],
    artifact['success_rate']
    )

    # Verify insertion
    result = await execute_query(
        "SELECT * FROM artifacts WHERE id = $1",
        artifact['id'],
        fetch='one'
    )

    assert result is not None
    assert result['id'] == artifact['id']
    assert result['name'] == artifact['name']


@pytest.mark.asyncio
async def test_update_artifact(db, sample_metadata):
    """Test updating an artifact."""
    artifact = sample_metadata['artifact']

    # Insert
    await execute_query("""
        INSERT INTO artifacts (id, type, category, name, path, created, modified, description, tags, status, stability, owner)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """,
    artifact['id'], artifact['type'], artifact['category'], artifact['name'],
    artifact['path'], artifact['created'], artifact['modified'], artifact['description'],
    artifact['tags'], artifact['status'], artifact['stability'], artifact['owner']
    )

    # Update
    await execute_query("""
        UPDATE artifacts SET name = $1, description = $2 WHERE id = $3
    """, "Updated Test Agent", "Updated description", artifact['id'])

    # Verify update
    result = await execute_query(
        "SELECT name, description FROM artifacts WHERE id = $1",
        artifact['id'],
        fetch='one'
    )

    assert result['name'] == "Updated Test Agent"
    assert result['description'] == "Updated description"


@pytest.mark.asyncio
async def test_delete_artifact(db, sample_metadata):
    """Test deleting an artifact."""
    artifact = sample_metadata['artifact']

    # Insert
    await execute_query("""
        INSERT INTO artifacts (id, type, category, name, path, created, modified, description, tags, status, stability, owner)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """,
    artifact['id'], artifact['type'], artifact['category'], artifact['name'],
    artifact['path'], artifact['created'], artifact['modified'], artifact['description'],
    artifact['tags'], artifact['status'], artifact['stability'], artifact['owner']
    )

    # Delete
    await execute_query("DELETE FROM artifacts WHERE id = $1", artifact['id'])

    # Verify deletion
    result = await execute_query(
        "SELECT * FROM artifacts WHERE id = $1",
        artifact['id'],
        fetch='one'
    )

    assert result is None


# -----------------------------------------------------------------------------
# Relationship Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_insert_relationships(db, sample_metadata):
    """Test inserting relationships."""
    artifact = sample_metadata['artifact']
    relationships = sample_metadata['relationships']

    # Insert artifacts first
    await execute_query("""
        INSERT INTO artifacts (id, type, category, name, path, created, modified, description, tags, status, stability, owner)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """,
    artifact['id'], artifact['type'], artifact['category'], artifact['name'],
    artifact['path'], artifact['created'], artifact['modified'], artifact['description'],
    artifact['tags'], artifact['status'], artifact['stability'], artifact['owner']
    )

    await execute_query("""
        INSERT INTO artifacts (id, type, category, name, path, created, modified, description, tags, status, stability, owner)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """,
    'test-lib-1', 'library', 'test-lib', 'Test Library',
    '5-libraries/test-lib/', '2026-01-15', '2026-01-15', 'A test library',
    ['test'], 'active', 'high', 'test-team'
    )

    # Insert relationship
    for rel in relationships:
        await execute_query("""
            INSERT INTO relationships (from_id, to_id, relationship_type, strength, metadata)
            VALUES ($1, $2, $3, $4, $5)
        """,
        rel['from_id'], rel['to_id'], rel['relationship_type'], rel['strength'], rel.get('metadata')
        )

    # Verify
    result = await execute_query(
        "SELECT * FROM relationships WHERE from_id = $1 AND to_id = $2",
        artifact['id'], 'test-lib-1',
        fetch='one'
    )

    assert result is not None
    assert result['relationship_type'] == 'depends_on'


# -----------------------------------------------------------------------------
# Query Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_query_by_id(db, sample_metadata):
    """Test querying artifact by ID."""
    query = BrainQuery()
    await query.initialize()

    # Insert test data
    artifact = sample_metadata['artifact']
    await execute_query("""
        INSERT INTO artifacts (id, type, category, name, path, created, modified, description, tags, status, stability, owner)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """,
    artifact['id'], artifact['type'], artifact['category'], artifact['name'],
    artifact['path'], artifact['created'], artifact['modified'], artifact['description'],
    artifact['tags'], artifact['status'], artifact['stability'], artifact['owner']
    )

    # Query
    result = await query.get_artifact_by_id(artifact['id'])

    assert result is not None
    assert result['id'] == artifact['id']
    assert result['name'] == artifact['name']

    await query.close()


@pytest.mark.asyncio
async def test_query_by_type(db, sample_metadata):
    """Test querying artifacts by type."""
    query = BrainQuery()
    await query.initialize()

    # Insert test data
    artifact = sample_metadata['artifact']
    await execute_query("""
        INSERT INTO artifacts (id, type, category, name, path, created, modified, description, tags, status, stability, owner)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """,
    artifact['id'], artifact['type'], artifact['category'], artifact['name'],
    artifact['path'], artifact['created'], artifact['modified'], artifact['description'],
    artifact['tags'], artifact['status'], artifact['stability'], artifact['owner']
    )

    # Query
    results = await query.find_by_type('agent')

    assert len(results) > 0
    assert any(r['id'] == artifact['id'] for r in results)

    await query.close()


@pytest.mark.asyncio
async def test_query_by_tag(db, sample_metadata):
    """Test querying artifacts by tag."""
    query = BrainQuery()
    await query.initialize()

    # Insert test data
    artifact = sample_metadata['artifact']
    await execute_query("""
        INSERT INTO artifacts (id, type, category, name, path, created, modified, description, tags, status, stability, owner)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """,
    artifact['id'], artifact['type'], artifact['category'], artifact['name'],
    artifact['path'], artifact['created'], artifact['modified'], artifact['description'],
    artifact['tags'], artifact['status'], artifact['stability'], artifact['owner']
    )

    # Query
    results = await query.find_by_tag('test')

    assert len(results) > 0
    assert any(r['id'] == artifact['id'] for r in results)

    await query.close()


@pytest.mark.asyncio
async def test_query_dependencies(db, sample_metadata):
    """Test querying dependencies."""
    query = BrainQuery()
    await query.initialize()

    # Insert test data
    artifact = sample_metadata['artifact']
    await execute_query("""
        INSERT INTO artifacts (id, type, category, name, path, created, modified, description, tags, status, stability, owner)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """,
    artifact['id'], artifact['type'], artifact['category'], artifact['name'],
    artifact['path'], artifact['created'], artifact['modified'], artifact['description'],
    artifact['tags'], artifact['status'], artifact['stability'], artifact['owner']
    )

    await execute_query("""
        INSERT INTO artifacts (id, type, category, name, path, created, modified, description, tags, status, stability, owner)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """,
    'test-lib-1', 'library', 'test-lib', 'Test Library',
    '5-libraries/test-lib/', '2026-01-15', '2026-01-15', 'A test library',
    ['test'], 'active', 'high', 'test-team'
    )

    # Insert relationship
    await execute_query("""
        INSERT INTO relationships (from_id, to_id, relationship_type, strength)
        VALUES ($1, $2, $3, $4)
    """, artifact['id'], 'test-lib-1', 'depends_on', 1.0)

    # Query
    results = await query.find_dependencies(artifact['id'])

    assert len(results) > 0
    assert any(r['id'] == 'test-lib-1' for r in results)

    await query.close()


# -----------------------------------------------------------------------------
# Parser Tests
# -----------------------------------------------------------------------------

def test_parser_sample_metadata():
    """Test parsing sample metadata file."""
    # Use example metadata file
    example_file = Path(__file__).parent.parent / 'metadata' / 'examples' / 'agent-metadata.yaml'

    if not example_file.exists():
        pytest.skip("Example metadata file not found")

    result = parse_metadata_file(str(example_file))

    assert result is not None
    assert 'artifact' in result
    assert 'relationships' in result
    assert result['artifact']['id'] == 'orchestrator-agent-v1'


# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_ingestion_workflow(db, sample_metadata):
    """Test complete ingestion workflow."""
    ingester = MetadataIngester()

    # This would require actual metadata files
    # For now, just test database operations
    artifact = sample_metadata['artifact']

    await execute_query("""
        INSERT INTO artifacts (id, type, category, name, path, created, modified, description, tags, status, stability, owner)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """,
    artifact['id'], artifact['type'], artifact['category'], artifact['name'],
    artifact['path'], artifact['created'], artifact['modified'], artifact['description'],
    artifact['tags'], artifact['status'], artifact['stability'], artifact['owner']
    )

    # Verify
    query = BrainQuery()
    await query.initialize()

    result = await query.get_artifact_by_id(artifact['id'])
    assert result is not None

    await query.close()


# -----------------------------------------------------------------------------
# Run Tests
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
