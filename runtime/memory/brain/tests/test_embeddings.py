#!/usr/bin/env python3
"""
Blackbox4 Brain v2.0 - Embedding Tests
Tests for embedding generation and semantic search.

Version: 1.0.0
Last Updated: 2026-01-15
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.embedder import EmbeddingCache, EmbeddingGenerator, ArtifactEmbedder
from query.vector import VectorSearch, SearchResult
from query.nl_parser import NLQueryParser, QueryIntent, QueryExecutor


# ============================================================================
# EMBEDDING CACHE TESTS
# ============================================================================

class TestEmbeddingCache(unittest.TestCase):
    """Test embedding cache functionality."""

    def setUp(self):
        """Set up test cache."""
        import tempfile
        self.cache_dir = Path(tempfile.mkdtemp())
        self.cache = EmbeddingCache(self.cache_dir)

    def tearDown(self):
        """Clean up cache."""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)

    def test_cache_miss(self):
        """Test cache miss returns None."""
        result = self.cache.get("nonexistent")
        self.assertIsNone(result)

    def test_cache_set_get(self):
        """Test cache set and get."""
        vector = [0.1, 0.2, 0.3]
        self.cache.set("hash123", "artifact-1", vector, "test-model")

        result = self.cache.get("hash123")
        self.assertEqual(result, vector)

    def test_cache_clear(self):
        """Test cache clear."""
        vector = [0.1, 0.2, 0.3]
        self.cache.set("hash123", "artifact-1", vector, "test-model")

        self.cache.clear("artifact-1")
        result = self.cache.get("hash123")
        self.assertIsNone(result)


# ============================================================================
# EMBEDDING GENERATOR TESTS
# ============================================================================

class TestEmbeddingGenerator(unittest.TestCase):
    """Test embedding generator."""

    def setUp(self):
        """Set up test generator."""
        self.generator = EmbeddingGenerator(
            model="test-model",
            use_local=True,
            cache_dir=None  # Disable caching for tests
        )

    @patch('ingest.embedder.SentenceTransformer')
    def test_init_local_model(self, mock_transformer):
        """Test local model initialization."""
        mock_model = Mock()
        mock_transformer.return_value = mock_model

        generator = EmbeddingGenerator(model="test-model", use_local=True)
        self.assertTrue(generator.use_local)
        self.assertIsNotNone(generator.local_model)

    def test_hash_content(self):
        """Test content hashing."""
        text1 = "test content"
        text2 = "test content"
        text3 = "different content"

        hash1 = self.generator._hash_content(text1)
        hash2 = self.generator._hash_content(text2)
        hash3 = self.generator._hash_content(text3)

        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)


# ============================================================================
# ARTIFACT EMBEDDER TESTS
# ============================================================================

class TestArtifactEmbedder(unittest.TestCase):
    """Test artifact embedder."""

    def setUp(self):
        """Set up test embedder."""
        self.mock_generator = Mock(spec=EmbeddingGenerator)
        self.embedder = ArtifactEmbedder(generator=self.mock_generator)

    def test_prepare_text(self):
        """Test text preparation from metadata."""
        metadata = {
            "name": "Test Agent",
            "description": "A test agent for testing",
            "type": "agent",
            "category": "specialist",
            "tags": ["test", "agent"],
            "keywords": ["testing"]
        }

        text = self.embedder._prepare_text(metadata)

        self.assertIn("Test Agent", text)
        self.assertIn("A test agent for testing", text)
        self.assertIn("test, agent", text)

    def test_embed_missing_id(self):
        """Test embedding with missing ID."""
        metadata = {
            "name": "Test",
            "description": "Test description"
        }

        with self.assertRaises(ValueError):
            self.embedder.embed(metadata)

    def test_embed_success(self):
        """Test successful embedding."""
        metadata = {
            "id": "test-1",
            "name": "Test Agent",
            "description": "Test",
            "type": "agent",
            "category": "specialist",
            "tags": ["test"]
        }

        self.mock_generator.generate.return_value = [0.1, 0.2, 0.3]

        artifact_id, vector = self.embedder.embed(metadata)

        self.assertEqual(artifact_id, "test-1")
        self.assertEqual(vector, [0.1, 0.2, 0.3])


# ============================================================================
# VECTOR SEARCH TESTS
# ============================================================================

class TestVectorSearch(unittest.TestCase):
    """Test vector search functionality."""

    def setUp(self):
        """Set up test search."""
        # Mock database connection
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()

    @patch('query.vector.psycopg2.connect')
    def test_init_success(self, mock_connect):
        """Test successful initialization."""
        mock_connect.return_value = self.mock_conn

        search = VectorSearch(host="localhost", database="test_db")
        self.assertIsNotNone(search.conn)

    def test_search_result_to_dict(self):
        """Test SearchResult serialization."""
        result = SearchResult(
            artifact_id="test-1",
            name="Test",
            type="agent",
            category="specialist",
            description="Test agent",
            path="/test",
            similarity=0.95,
            metadata={"status": "active"}
        )

        result_dict = result.to_dict()

        self.assertEqual(result_dict["artifact_id"], "test-1")
        self.assertEqual(result_dict["similarity"], 0.95)


# ============================================================================
# NL PARSER TESTS
# ============================================================================

class TestNLQueryParser(unittest.TestCase):
    """Test natural language query parser."""

    def setUp(self):
        """Set up parser."""
        self.parser = NLQueryParser()

    def test_detect_placement_intent(self):
        """Test placement intent detection."""
        query = "Where should I put a new data analysis agent?"
        parsed = self.parser.parse(query)

        self.assertEqual(parsed.intent, QueryIntent.PLACEMENT)

    def test_detect_discovery_intent(self):
        """Test discovery intent detection."""
        query = "Find all specialist agents"
        parsed = self.parser.parse(query)

        self.assertEqual(parsed.intent, QueryIntent.DISCOVERY)

    def test_detect_relationship_intent(self):
        """Test relationship intent detection."""
        query = "What depends on the orchestrator?"
        parsed = self.parser.parse(query)

        self.assertEqual(parsed.intent, QueryIntent.RELATIONSHIP)

    def test_extract_type_entity(self):
        """Test type extraction."""
        query = "Find all specialist agents"
        parsed = self.parser.parse(query)

        self.assertEqual(parsed.entities.get("type"), "agent")

    def test_extract_category_entity(self):
        """Test category extraction."""
        query = "Find all specialist agents"
        parsed = self.parser.parse(query)

        self.assertEqual(parsed.entities.get("category"), "specialist")

    def test_extract_status_entity(self):
        """Test status extraction."""
        query = "Find all active agents"
        parsed = self.parser.parse(query)

        self.assertEqual(parsed.entities.get("status"), "active")

    def test_extract_phase_entity(self):
        """Test phase extraction."""
        query = "Find all phase 4 artifacts"
        parsed = self.parser.parse(query)

        self.assertEqual(parsed.entities.get("phase"), 4)

    def test_extract_limit_filter(self):
        """Test limit filter extraction."""
        query = "Find top 10 agents"
        parsed = self.parser.parse(query)

        self.assertEqual(parsed.filters.get("limit"), 10)


# ============================================================================
# QUERY EXECUTOR TESTS
# ============================================================================

class TestQueryExecutor(unittest.TestCase):
    """Test query executor."""

    def setUp(self):
        """Set up executor."""
        self.mock_vector_search = Mock()
        self.executor = QueryExecutor(
            vector_search=self.mock_vector_search,
            structured_search=None
        )

    def test_execute_similarity_query(self):
        """Test similarity query execution."""
        self.mock_vector_search.find_similar.return_value = [
            SearchResult(
                artifact_id="similar-1",
                name="Similar Agent",
                type="agent",
                category="specialist",
                description="A similar agent",
                path="/similar",
                similarity=0.9,
                metadata={}
            )
        ]

        result = self.executor.execute("Find artifacts similar to test-agent-1")

        self.assertTrue("results" in result)
        self.assertEqual(len(result["results"]["similar_artifacts"]), 1)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestEmbeddingIntegration(unittest.TestCase):
    """Integration tests for embedding system."""

    def test_end_to_end_embedding(self):
        """Test end-to-end embedding generation and search."""
        # This would require a real database
        # Placeholder for integration test
        pass

    def test_cache_integration(self):
        """Test cache integration with embedder."""
        # This would test real cache usage
        # Placeholder for integration test
        pass


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
