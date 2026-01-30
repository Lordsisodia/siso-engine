#!/usr/bin/env python3
"""
Test suite for Blackbox4 hybrid memory system
Tests GLM API, local embeddings, and vector storage
"""

import sys
import os
from pathlib import Path

# Add services directory to path
services_dir = Path(__file__).parent
sys.path.insert(0, str(services_dir))


def test_embedder():
    """Test hybrid embedder"""
    print("\n=== Testing Hybrid Embedder ===")

    try:
        from hybrid_embedder import HybridEmbedder

        embedder = HybridEmbedder()

        # Test status
        status = embedder.get_backend_status()
        print("✓ Embedder initialized")
        print(f"  GLM available: {status['glm_available']}")
        print(f"  Local available: {status['local_available']}")
        print(f"  Mode: {status['current_mode']}")

        # Test embedding
        test_text = "Blackbox4 semantic search system"
        embedding = embedder.embed(test_text)

        print(f"✓ Embedding generated")
        print(f"  Dimension: {len(embedding)}")
        print(f"  Sample (first 5): {embedding[:5]}")

        return True

    except Exception as e:
        print(f"✗ Embedder test failed: {e}")
        return False


def test_vector_store():
    """Test vector store"""
    print("\n=== Testing Vector Store ===")

    try:
        from vector_store import VectorStore

        store = VectorStore()

        # Test stats
        stats = store.get_collection_stats()
        print("✓ Vector store initialized")
        print(f"  Collection: {stats.get('name')}")
        print(f"  Documents: {stats.get('count')}")

        return True

    except Exception as e:
        print(f"✗ Vector store test failed: {e}")
        return False


def test_semantic_search():
    """Test semantic search"""
    print("\n=== Testing Semantic Search ===")

    try:
        from semantic_search_upgraded import SemanticContextSearch

        searcher = SemanticContextSearch()

        # Test status
        status = searcher.get_status()
        print("✓ Semantic search initialized")
        print(f"  Embeddings enabled: {status['use_embeddings']}")
        print(f"  Embedder available: {status['embedder_available']}")

        # Test search
        query = "database performance"
        results = searcher.search(query, max_results=3)

        print(f"✓ Search completed")
        print(f"  Query: {query}")
        print(f"  Method: {results.get('method')}")
        print(f"  Total matches: {results.get('total_matches')}")

        if results.get('relevant_tasks'):
            print(f"  Top task: {results['relevant_tasks'][0].get('title', 'N/A')}")

        return True

    except Exception as e:
        print(f"✗ Semantic search test failed: {e}")
        return False


def test_integration():
    """Test full integration"""
    print("\n=== Testing Full Integration ===")

    try:
        from hybrid_embedder import HybridEmbedder
        from vector_store import VectorStore
        from semantic_search_upgraded import SemanticContextSearch

        # Initialize components
        embedder = HybridEmbedder()
        store = VectorStore()
        searcher = SemanticContextSearch()

        print("✓ All components initialized")

        # Test embedding and search
        test_queries = [
            "authentication bug",
            "database optimization",
            "API documentation"
        ]

        for query in test_queries:
            results = searcher.search(query, max_results=1)
            print(f"✓ Query '{query}': {results.get('total_matches', 0)} matches")

        return True

    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Blackbox4 Hybrid Memory System - Test Suite")
    print("=" * 60)

    results = {
        "embedder": test_embedder(),
        "vector_store": test_vector_store(),
        "semantic_search": test_semantic_search(),
        "integration": test_integration()
    }

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
