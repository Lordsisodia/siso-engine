#!/usr/bin/env python3
"""
Blackbox4 Brain v2.0 - Vector Search Interface
Semantic search using pgvector for finding similar artifacts.

Version: 1.0.0
Last Updated: 2026-01-15
"""

import os
import sys
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Semantic search result with similarity score."""
    artifact_id: str
    name: str
    type: str
    category: str
    description: str
    path: str
    similarity: float
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "artifact_id": self.artifact_id,
            "name": self.name,
            "type": self.type,
            "category": self.category,
            "description": self.description,
            "path": self.path,
            "similarity": self.similarity,
            "metadata": self.metadata
        }


class VectorSearch:
    """Semantic search using pgvector."""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None
    ):
        """
        Initialize vector search.

        Args:
            host: PostgreSQL host (default: from env or localhost)
            port: PostgreSQL port (default: from env or 5432)
            database: Database name (default: from env or blackbox4_brain)
            user: Database user (default: from env or postgres)
            password: Database password (default: from env)
        """
        self.host = host or os.getenv("PGHOST", "localhost")
        self.port = port or int(os.getenv("PGPORT", "5432"))
        self.database = database or os.getenv("PGDATABASE", "blackbox4_brain")
        self.user = user or os.getenv("PGUSER", "postgres")
        self.password = password or os.getenv("PGPASSWORD", "")

        self.conn = None
        self._connect()

    def _connect(self):
        """Establish database connection."""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                cursor_factory=RealDictCursor
            )
            logger.info(f"Connected to PostgreSQL: {self.host}:{self.port}/{self.database}")

        except ImportError:
            logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _parse_vector(self, vector_str: str) -> List[float]:
        """Parse vector string from database."""
        # Remove brackets and split
        vector_str = vector_str.strip("[]")
        return [float(x) for x in vector_str.split(",")]

    def semantic_search(
        self,
        query_vector: List[float],
        limit: int = 10,
        filters: Dict[str, Any] = None,
        min_similarity: float = 0.0
    ) -> List[SearchResult]:
        """
        Perform semantic search using cosine similarity.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            filters: Optional filters (type, category, status, etc.)
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of SearchResult objects
        """
        if not self.conn:
            raise RuntimeError("Not connected to database")

        # Build query
        vector_str = f"[{','.join(map(str, query_vector))}]"

        base_query = """
            SELECT
                a.id,
                a.name,
                a.type,
                a.category,
                a.description,
                a.path,
                a.status,
                a.tags,
                1 - (e.vector <=> %s::vector) as similarity
            FROM artifacts a
            JOIN embeddings e ON e.artifact_id = a.id
            WHERE 1 - (e.vector <=> %s::vector) >= %s
        """

        params = [vector_str, vector_str, min_similarity]

        # Add filters
        if filters:
            if "type" in filters:
                base_query += " AND a.type = %s"
                params.append(filters["type"])

            if "category" in filters:
                base_query += " AND a.category = %s"
                params.append(filters["category"])

            if "status" in filters:
                base_query += " AND a.status = %s"
                params.append(filters["status"])

            if "tags" in filters:
                # Filter by tags (array overlap)
                base_query += " AND a.tags && %s"
                params.append(filters["tags"])

            if "phase" in filters:
                base_query += " AND a.phase = %s"
                params.append(filters["phase"])

        # Order by similarity and limit
        base_query += " ORDER BY e.vector <=> %s::vector LIMIT %s"
        params.extend([vector_str, limit])

        try:
            with self.conn.cursor() as cur:
                cur.execute(base_query, params)
                rows = cur.fetchall()

            results = []
            for row in rows:
                result = SearchResult(
                    artifact_id=row["id"],
                    name=row["name"],
                    type=row["type"],
                    category=row["category"],
                    description=row["description"],
                    path=row["path"],
                    similarity=float(row["similarity"]),
                    metadata={
                        "status": row["status"],
                        "tags": row["tags"]
                    }
                )
                results.append(result)

            logger.info(f"Semantic search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise

    def find_similar(
        self,
        artifact_id: str,
        limit: int = 10,
        exclude_self: bool = True
    ) -> List[SearchResult]:
        """
        Find artifacts similar to a given artifact.

        Args:
            artifact_id: ID of reference artifact
            limit: Maximum number of results
            exclude_self: Exclude the reference artifact from results

        Returns:
            List of SearchResult objects
        """
        if not self.conn:
            raise RuntimeError("Not connected to database")

        # Get embedding for reference artifact
        get_vector_query = """
            SELECT vector FROM embeddings WHERE artifact_id = %s
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(get_vector_query, (artifact_id,))
                row = cur.fetchone()

                if not row:
                    logger.error(f"No embedding found for artifact: {artifact_id}")
                    return []

                vector_str = str(row["vector"])

            # Find similar artifacts
            similarity_query = """
                SELECT
                    a.id,
                    a.name,
                    a.type,
                    a.category,
                    a.description,
                    a.path,
                    a.status,
                    a.tags,
                    1 - (e.vector <=> %s::vector) as similarity
                FROM artifacts a
                JOIN embeddings e ON e.artifact_id = a.id
                WHERE e.vector <=> %s::vector < 0.3
            """

            params = [vector_str, vector_str]

            if exclude_self:
                similarity_query += " AND a.id != %s"
                params.append(artifact_id)

            similarity_query += " ORDER BY e.vector <=> %s::vector LIMIT %s"
            params.extend([vector_str, limit])

            with self.conn.cursor() as cur:
                cur.execute(similarity_query, params)
                rows = cur.fetchall()

            results = []
            for row in rows:
                result = SearchResult(
                    artifact_id=row["id"],
                    name=row["name"],
                    type=row["type"],
                    category=row["category"],
                    description=row["description"],
                    path=row["path"],
                    similarity=float(row["similarity"]),
                    metadata={
                        "status": row["status"],
                        "tags": row["tags"]
                    }
                )
                results.append(result)

            logger.info(f"Found {len(results)} artifacts similar to {artifact_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to find similar artifacts: {e}")
            raise

    def hybrid_search(
        self,
        query_vector: List[float],
        text_query: str = None,
        limit: int = 10,
        filters: Dict[str, Any] = None,
        semantic_weight: float = 0.7
    ) -> List[SearchResult]:
        """
        Hybrid search combining semantic and full-text search.

        Args:
            query_vector: Query embedding vector
            text_query: Optional text query for full-text search
            limit: Maximum number of results
            filters: Optional filters
            semantic_weight: Weight for semantic search (0-1, default 0.7)

        Returns:
            List of SearchResult objects with combined scores
        """
        if not self.conn:
            raise RuntimeError("Not connected to database")

        # Semantic search
        semantic_results = self.semantic_search(
            query_vector=query_vector,
            limit=limit * 2,  # Get more for reranking
            filters=filters
        )

        # If no text query, return semantic results
        if not text_query:
            return semantic_results[:limit]

        # Full-text search
        fts_query = """
            SELECT
                a.id,
                a.name,
                a.type,
                a.category,
                a.description,
                a.path,
                a.status,
                a.tags,
                ts_rank(to_tsvector('english', a.description), plainto_tsquery('english', %s)) as rank
            FROM artifacts a
            WHERE to_tsvector('english', a.description) @@ plainto_tsquery('english', %s)
        """

        params = [text_query, text_query]

        # Add filters
        if filters:
            if "type" in filters:
                fts_query += " AND a.type = %s"
                params.append(filters["type"])

            if "category" in filters:
                fts_query += " AND a.category = %s"
                params.append(filters["category"])

        fts_query += " ORDER BY rank DESC LIMIT %s"
        params.append(limit * 2)

        try:
            with self.conn.cursor() as cur:
                cur.execute(fts_query, params)
                fts_rows = cur.fetchall()

            # Combine scores
            fts_scores = {row["id"]: float(row["rank"]) for row in fts_rows}

            # Rerank semantic results
            combined_results = []
            for result in semantic_results:
                fts_score = fts_scores.get(result.artifact_id, 0)
                # Normalize and combine
                combined_score = (
                    semantic_weight * result.similarity +
                    (1 - semantic_weight) * min(fts_score, 1.0)
                )

                combined_result = SearchResult(
                    artifact_id=result.artifact_id,
                    name=result.name,
                    type=result.type,
                    category=result.category,
                    description=result.description,
                    path=result.path,
                    similarity=combined_score,
                    metadata={
                        **result.metadata,
                        "semantic_score": result.similarity,
                        "fts_score": fts_score
                    }
                )
                combined_results.append(combined_result)

            # Sort by combined score
            combined_results.sort(key=lambda x: x.similarity, reverse=True)

            logger.info(f"Hybrid search returned {len(combined_results[:limit])} results")
            return combined_results[:limit]

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise

    def get_embedding(self, artifact_id: str) -> Optional[List[float]]:
        """
        Get embedding vector for an artifact.

        Args:
            artifact_id: Artifact ID

        Returns:
            Embedding vector or None if not found
        """
        if not self.conn:
            raise RuntimeError("Not connected to database")

        query = "SELECT vector FROM embeddings WHERE artifact_id = %s"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (artifact_id,))
                row = cur.fetchone()

                if not row:
                    return None

                # Parse vector
                vector_str = str(row["vector"]).strip("[]")
                return [float(x) for x in vector_str.split(",")]

        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            raise

    def count_embeddings(self) -> int:
        """Get total number of embeddings in database."""
        if not self.conn:
            raise RuntimeError("Not connected to database")

        query = "SELECT COUNT(*) as count FROM embeddings"

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                row = cur.fetchone()
                return row["count"]
        except Exception as e:
            logger.error(f"Failed to count embeddings: {e}")
            raise


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Command-line interface for vector search."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Semantic search for Blackbox4 artifacts"
    )
    parser.add_argument(
        "query",
        help="Query text or artifact ID for --similar"
    )
    parser.add_argument(
        "--similar",
        action="store_true",
        help="Find artifacts similar to given artifact ID"
    )
    parser.add_argument(
        "--type",
        help="Filter by artifact type"
    )
    parser.add_argument(
        "--category",
        help="Filter by category"
    )
    parser.add_argument(
        "--status",
        help="Filter by status"
    )
    parser.add_argument(
        "--tags",
        help="Filter by tags (comma-separated)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)"
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.0,
        help="Minimum similarity threshold (default: 0.0)"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize search
    try:
        with VectorSearch() as search:
            if args.similar:
                # Find similar artifacts
                results = search.find_similar(
                    artifact_id=args.query,
                    limit=args.limit
                )
            else:
                # Need to generate embedding for query text
                # This requires the embedder module
                logger.error("Text query requires embedding generation. Use --similar for artifact-based search.")
                sys.exit(1)

            # Print results
            print(f"\nFound {len(results)} results:\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.name} ({result.type}/{result.category})")
                print(f"   Similarity: {result.similarity:.3f}")
                print(f"   Description: {result.description[:100]}...")
                print(f"   Path: {result.path}")
                print()

            # Save to file
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump([r.to_dict() for r in results], f, indent=2)
                print(f"Results saved to: {args.output}")

    except Exception as e:
        logger.error(f"Search failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
