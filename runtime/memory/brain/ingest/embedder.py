#!/usr/bin/env python3
"""
Blackbox4 Brain v2.0 - Embedding Generator
Generates vector embeddings for artifacts using OpenAI or local models.

Version: 1.0.0
Last Updated: 2026-01-15
"""

import os
import sys
import json
import hashlib
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmbeddingCache:
    """Local cache for embeddings to avoid re-generation."""

    def __init__(self, cache_dir: Path):
        """Initialize embedding cache."""
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "embeddings.db"
        self._init_db()

    def _init_db(self):
        """Initialize SQLite cache database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    content_hash TEXT PRIMARY KEY,
                    artifact_id TEXT NOT NULL,
                    vector TEXT NOT NULL,
                    model TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def get(self, content_hash: str) -> Optional[List[float]]:
        """Get cached embedding by content hash."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT vector FROM embeddings WHERE content_hash = ?",
                (content_hash,)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return None

    def set(self, content_hash: str, artifact_id: str, vector: List[float], model: str):
        """Cache embedding."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO embeddings
                   (content_hash, artifact_id, vector, model, created_at)
                   VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (content_hash, artifact_id, json.dumps(vector), model)
            )

    def clear(self, artifact_id: Optional[str] = None):
        """Clear cache (optionally for specific artifact)."""
        with sqlite3.connect(self.db_path) as conn:
            if artifact_id:
                conn.execute("DELETE FROM embeddings WHERE artifact_id = ?", (artifact_id,))
            else:
                conn.execute("DELETE FROM embeddings")


class EmbeddingGenerator:
    """Generate embeddings using OpenAI or local models."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        cache_dir: Optional[Path] = None,
        openai_api_key: Optional[str] = None,
        use_local: bool = False
    ):
        """
        Initialize embedding generator.

        Args:
            model: Model name (OpenAI: text-embedding-3-small, text-embedding-3-large;
                   Local: all-MiniLM-L6-v2, etc.)
            cache_dir: Directory for embedding cache
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            use_local: Use local sentence-transformers model instead of OpenAI
        """
        self.model = model
        self.use_local = use_local
        self.cache_dir = cache_dir or Path.home() / ".blackbox4" / "cache" / "embeddings"
        self.cache = EmbeddingCache(self.cache_dir)

        # Initialize model
        if use_local:
            self._init_local_model()
        else:
            self._init_openai(openai_api_key)

    def _init_openai(self, api_key: Optional[str]):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
            if not self.openai_client.api_key:
                raise ValueError("OpenAI API key not provided")
            logger.info(f"Initialized OpenAI embedding generator with model: {self.model}")
        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            raise

    def _init_local_model(self):
        """Initialize local sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.local_model = SentenceTransformer(self.model)
            logger.info(f"Initialized local embedding model: {self.model}")
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize local model: {e}")
            raise

    def _hash_content(self, content: str) -> str:
        """Generate hash of content for cache key."""
        return hashlib.sha256(content.encode()).hexdigest()

    def generate(self, text: str, artifact_id: str) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed
            artifact_id: Artifact ID for cache tracking

        Returns:
            Embedding vector as list of floats
        """
        content_hash = self._hash_content(text)

        # Check cache
        cached = self.cache.get(content_hash)
        if cached:
            logger.debug(f"Cache hit for artifact {artifact_id}")
            return cached

        # Generate embedding
        try:
            if self.use_local:
                vector = self._generate_local(text)
            else:
                vector = self._generate_openai(text)

            # Cache result
            self.cache.set(content_hash, artifact_id, vector, self.model)
            logger.info(f"Generated embedding for {artifact_id} (dim={len(vector)})")
            return vector

        except Exception as e:
            logger.error(f"Failed to generate embedding for {artifact_id}: {e}")
            raise

    def _generate_openai(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        try:
            response = self.openai_client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def _generate_local(self, text: str) -> List[float]:
        """Generate embedding using local model."""
        try:
            embedding = self.local_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Local model error: {e}")
            raise


class ArtifactEmbedder:
    """Generate embeddings for artifacts from metadata."""

    def __init__(
        self,
        generator: EmbeddingGenerator,
        embed_fields: List[str] = None
    ):
        """
        Initialize artifact embedder.

        Args:
            generator: EmbeddingGenerator instance
            embed_fields: Fields to include in embedding text
        """
        self.generator = generator
        self.embed_fields = embed_fields or [
            "name",
            "description",
            "tags",
            "keywords",
            "category",
            "type"
        ]

    def _prepare_text(self, metadata: Dict) -> str:
        """
        Prepare text for embedding from metadata.

        Combines relevant fields into a single text representation.
        """
        parts = []

        # Name (highest weight)
        if "name" in metadata:
            parts.append(f"Name: {metadata['name']}")

        # Description
        if "description" in metadata:
            parts.append(f"Description: {metadata['description']}")

        # Type and category
        if "type" in metadata:
            parts.append(f"Type: {metadata['type']}")
        if "category" in metadata:
            parts.append(f"Category: {metadata['category']}")

        # Tags
        if "tags" in metadata and metadata["tags"]:
            parts.append(f"Tags: {', '.join(metadata['tags'])}")

        # Keywords
        if "keywords" in metadata and metadata["keywords"]:
            parts.append(f"Keywords: {', '.join(metadata['keywords'])}")

        return "\n".join(parts)

    def embed(self, metadata: Dict) -> Tuple[str, List[float]]:
        """
        Generate embedding for artifact metadata.

        Args:
            metadata: Artifact metadata dictionary

        Returns:
            Tuple of (artifact_id, embedding_vector)
        """
        artifact_id = metadata.get("id")
        if not artifact_id:
            raise ValueError("Metadata missing required 'id' field")

        # Prepare text
        text = self._prepare_text(metadata)

        # Generate embedding
        vector = self.generator.generate(text, artifact_id)

        return artifact_id, vector

    def embed_batch(self, metadata_list: List[Dict]) -> Dict[str, List[float]]:
        """
        Generate embeddings for multiple artifacts.

        Args:
            metadata_list: List of metadata dictionaries

        Returns:
            Dictionary mapping artifact_id to embedding_vector
        """
        embeddings = {}
        for metadata in metadata_list:
            try:
                artifact_id, vector = self.embed(metadata)
                embeddings[artifact_id] = vector
            except Exception as e:
                logger.error(f"Failed to embed artifact {metadata.get('id', 'unknown')}: {e}")
        return embeddings


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Command-line interface for embedding generator."""
    import argparse
    import yaml

    parser = argparse.ArgumentParser(
        description="Generate embeddings for Blackbox4 artifacts"
    )
    parser.add_argument(
        "path",
        help="Path to metadata.yaml or directory containing metadata files"
    )
    parser.add_argument(
        "--model",
        default="text-embedding-3-small",
        help="Embedding model (default: text-embedding-3-small)"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local sentence-transformers model"
    )
    parser.add_argument(
        "--local-model",
        default="all-MiniLM-L6-v2",
        help="Local model name (default: all-MiniLM-L6-v2)"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file for embeddings"
    )
    parser.add_argument(
        "--cache-dir",
        help="Custom cache directory"
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

    # Initialize generator
    try:
        model = args.local_model if args.local else args.model
        generator = EmbeddingGenerator(
            model=model,
            cache_dir=Path(args.cache_dir) if args.cache_dir else None,
            use_local=args.local
        )
        embedder = ArtifactEmbedder(generator)
    except Exception as e:
        logger.error(f"Failed to initialize embedding generator: {e}")
        sys.exit(1)

    # Load metadata
    path = Path(args.path)
    metadata_files = []

    if path.is_file() and path.name == "metadata.yaml":
        metadata_files = [path]
    elif path.is_dir():
        metadata_files = list(path.rglob("metadata.yaml"))
    else:
        logger.error(f"Invalid path: {path}")
        sys.exit(1)

    if not metadata_files:
        logger.warning(f"No metadata.yaml files found in {path}")
        sys.exit(0)

    # Process files
    embeddings = {}
    for metadata_file in metadata_files:
        try:
            with open(metadata_file, 'r') as f:
                metadata = yaml.safe_load(f)

            artifact_id, vector = embedder.embed(metadata)
            embeddings[artifact_id] = {
                "vector": vector,
                "model": model,
                "metadata_file": str(metadata_file)
            }

            print(f"✓ Embedded: {artifact_id}")

        except Exception as e:
            logger.error(f"Failed to process {metadata_file}: {e}")

    # Output results
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(embeddings, f, indent=2)
        print(f"\nEmbeddings saved to: {output_path}")
    else:
        print(f"\nGenerated {len(embeddings)} embeddings")

    # Print summary
    print(f"\nSummary:")
    print(f"  Files processed: {len(metadata_files)}")
    print(f"  Embeddings generated: {len(embeddings)}")
    print(f"  Model: {model}")
    print(f"  Vector dimensions: {len(list(embeddings.values())[0]['vector']) if embeddings else 'N/A'}")


if __name__ == "__main__":
    main()
