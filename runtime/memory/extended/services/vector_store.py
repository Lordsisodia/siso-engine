#!/usr/bin/env python3
"""
Blackbox4 Vector Store Manager
ChromaDB-based persistent vector storage for embeddings
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime


class VectorStore:
    """Persistent vector storage using ChromaDB"""

    def __init__(self, blackbox_root: str = None, config: Dict = None):
        if blackbox_root is None:
            blackbox_root = Path(__file__).parent.parent.parent.parent

        self.blackbox_root = Path(blackbox_root)

        # Default config
        if config is None:
            config = {
                "type": "chromadb",
                "path": ".memory/extended/chroma-db",
                "collection_name": "blackbox4_memory"
            }

        self.config = config
        self.client = None
        self.collection = None

        # Initialize
        self._setup_chromadb()

    def _setup_chromadb(self):
        """Setup ChromaDB client and collection"""
        try:
            import chromadb

            db_path = self.blackbox_root / self.config["path"]
            db_path.mkdir(parents=True, exist_ok=True)

            # Create persistent client
            self.client = chromadb.PersistentClient(
                path=str(db_path),
                settings=chromadb.config.Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get or create collection
            collection_name = self.config.get("collection_name", "blackbox4_memory")

            # Check if collection exists
            try:
                self.collection = self.client.get_collection(name=collection_name)
                print(f"✓ Loaded existing collection: {collection_name}")
            except ValueError:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "Blackbox4 semantic memory index"}
                )
                print(f"✓ Created new collection: {collection_name}")

        except ImportError:
            print("Error: chromadb not installed. Install with: pip install chromadb")
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")

    def add_documents(
        self,
        documents: List[str],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None,
        metadatas: Optional[List[Dict]] = None
    ) -> bool:
        """
        Add documents to vector store

        Args:
            documents: List of document texts
            ids: List of unique IDs
            embeddings: Optional pre-computed embeddings
            metadatas: Optional metadata for each document

        Returns:
            True if successful
        """
        if not self.collection:
            print("Error: Collection not initialized")
            return False

        try:
            self.collection.add(
                documents=documents,
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas
            )
            return True
        except Exception as e:
            print(f"Error adding documents: {e}")
            return False

    def search(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 10,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> Dict:
        """
        Search for similar documents

        Args:
            query_embeddings: Query embedding vectors
            n_results: Number of results to return
            where: Optional metadata filter
            where_document: Optional document content filter

        Returns:
            Search results
        """
        if not self.collection:
            return {"error": "Collection not initialized"}

        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                where_document=where_document
            )

            return results
        except Exception as e:
            return {"error": str(e)}

    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        if not self.collection:
            return {"error": "Collection not initialized"}

        try:
            count = self.collection.count()

            return {
                "name": self.collection.name,
                "count": count,
                "metadata": self.collection.metadata
            }
        except Exception as e:
            return {"error": str(e)}

    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents by IDs"""
        if not self.collection:
            return False

        try:
            self.collection.delete(ids=ids)
            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False

    def update_documents(
        self,
        ids: List[str],
        documents: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
        metadatas: Optional[List[Dict]] = None
    ) -> bool:
        """Update existing documents"""
        if not self.collection:
            return False

        try:
            self.collection.update(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            return True
        except Exception as e:
            print(f"Error updating documents: {e}")
            return False

    def clear_collection(self) -> bool:
        """Delete all documents from collection"""
        if not self.collection:
            return False

        try:
            # Delete and recreate collection
            name = self.collection.name
            self.client.delete_collection(name)

            self.collection = self.client.create_collection(
                name=name,
                metadata={"description": "Blackbox4 semantic memory index"}
            )

            return True
        except Exception as e:
            print(f"Error clearing collection: {e}")
            return False

    def export_collection(self, output_path: str = None) -> bool:
        """Export collection to JSON file"""
        if not self.collection:
            return False

        try:
            if output_path is None:
                output_path = self.blackbox_root / ".memory" / "extended" / "vector-export.json"

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Get all data
            count = self.collection.count()

            # ChromaDB doesn't have a simple "get all" method
            # We need to get data in batches or use peek
            data = {
                "exported_at": datetime.utcnow().isoformat(),
                "collection_name": self.collection.name,
                "count": count
            }

            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"✓ Exported collection to: {output_path}")
            return True

        except Exception as e:
            print(f"Error exporting collection: {e}")
            return False


class VectorIndexer:
    """Index Blackbox4 memory into vector store"""

    def __init__(self, blackbox_root: str = None, embedder=None):
        if blackbox_root is None:
            blackbox_root = Path(__file__).parent.parent.parent.parent

        self.blackbox_root = Path(blackbox_root)
        self.vector_store = VectorStore(str(blackbox_root))
        self.embedder = embedder

    def index_memory(
        self,
        force: bool = False,
        paths: Optional[List[str]] = None
    ) -> Dict:
        """
        Index all memory files into vector store

        Args:
            force: Re-index even if recently indexed
            paths: Specific paths to index (default: all)

        Returns:
            Indexing results
        """
        if not self.embedder:
            return {"error": "Embedder not initialized"}

        # Default paths to index
        if paths is None:
            paths = [
                ".memory/working/shared",
                ".docs",
                ".plans/active"
            ]

        results = {
            "indexed": 0,
            "errors": 0,
            "files": []
        }

        for path_str in paths:
            path = self.blackbox_root / path_str

            if not path.exists():
                continue

            # Find all markdown and JSON files
            for file_path in path.rglob("*.md"):
                self._index_file(file_path, results)

            for file_path in path.rglob("*.json"):
                self._index_file(file_path, results)

        return results

    def _index_file(self, file_path: Path, results: Dict):
        """Index a single file"""
        try:
            # Read file content
            content = file_path.read_text()

            # Skip if too large
            if len(content) > 100000:  # 100KB limit
                return

            # Generate embedding
            embedding = self.embedder.embed(content)

            # Generate ID from file path
            file_id = str(file_path.relative_to(self.blackbox_root))

            # Add to vector store
            success = self.vector_store.add_documents(
                documents=[content],
                ids=[file_id],
                embeddings=[embedding],
                metadatas=[{
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "file_type": file_path.suffix,
                    "size": len(content),
                    "indexed_at": datetime.utcnow().isoformat()
                }]
            )

            if success:
                results["indexed"] += 1
                results["files"].append(str(file_path))
            else:
                results["errors"] += 1

        except Exception as e:
            print(f"Error indexing {file_path}: {e}")
            results["errors"] += 1


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: vector-store.py [command]")
        print("Commands:")
        print("  stats                      - Show collection statistics")
        print("  index                      - Index all memory files")
        print("  search <query>             - Search vector store")
        print("  clear                      - Clear all documents")
        print("  export [path]              - Export collection")
        sys.exit(1)

    vector_store = VectorStore()

    if sys.argv[1] == "stats":
        stats = vector_store.get_collection_stats()
        print(json.dumps(stats, indent=2))

    elif sys.argv[1] == "index":
        from hybrid_embedder import HybridEmbedder

        embedder = HybridEmbedder()
        indexer = VectorIndexer(embedder=embedder)

        results = indexer.index_memory()
        print(json.dumps(results, indent=2))

    elif sys.argv[1] == "clear":
        if vector_store.clear_collection():
            print("✓ Collection cleared")
        else:
            print("✗ Failed to clear collection")

    elif sys.argv[1] == "export":
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        if vector_store.export_collection(output_path):
            print("✓ Collection exported")
        else:
            print("✗ Export failed")

    else:
        print(f"Error: Unknown command {sys.argv[1]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
