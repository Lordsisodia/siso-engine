#!/usr/bin/env python3
"""
Blackbox4 Hybrid Embedding System
Supports GLM API and local models with automatic fallback
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Union, Optional
from functools import lru_cache

class HybridEmbedder:
    """Hybrid embedding system with GLM API and local model fallback"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            blackbox_root = Path(__file__).parent.parent.parent.parent
            config_path = blackbox_root / ".config" / "memory-config.json"

        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Initialize backends
        self.glm_client = None
        self.local_model = None

        # Setup based on config
        self._setup_backends()

    def _load_config(self) -> dict:
        """Load configuration from file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)

        # Default config
        return {
            "embedding": {
                "mode": "local",  # Changed to local since GLM API key doesn't have embedding access
                "primary_backend": "local",
                "fallback_backend": "glm"
            },
            "vector_store": {
                "path": ".memory/extended/chroma-db"
            }
        }

    def _setup_backends(self):
        """Initialize embedding backends"""
        mode = self.config.get("embedding", {}).get("mode", "hybrid")
        primary = self.config.get("embedding", {}).get("primary_backend", "glm")

        if mode in ["hybrid", "glm"]:
            self._setup_glm_backend()

        if mode in ["hybrid", "local"]:
            self._setup_local_backend()

    def _setup_glm_backend(self):
        """Setup GLM API client"""
        try:
            # Try new zai-sdk first
            from zai import ZhipuAiClient

            api_key = os.environ.get(
                "ZHIPUAI_API_KEY",
                "531d930091214b2a985befa0210b9185.3Mb5KI1czB84IPUb"
            )

            if not api_key:
                print("Warning: ZHIPUAI_API_KEY not found, GLM backend disabled")
                return

            self.glm_client = ZhipuAiClient(api_key=api_key)
            self.glm_sdk = "zai"
            print("✓ GLM API backend initialized (zai-sdk)")

        except ImportError:
            try:
                # Fallback to old zhipuai SDK
                from zhipuai import ZhipuAI

                api_key = os.environ.get(
                    "ZHIPUAI_API_KEY",
                    "531d930091214b2a985befa0210b9185.3Mb5KI1czB84IPUb"
                )

                if not api_key:
                    print("Warning: ZHIPUAI_API_KEY not found, GLM backend disabled")
                    return

                self.glm_client = ZhipuAI(api_key=api_key)
                self.glm_sdk = "zhipuai"
                print("✓ GLM API backend initialized (zhipuai)")

            except ImportError:
                print("Warning: Neither zai-sdk nor zhipuai installed. Install with: pip install zai-sdk")
            except Exception as e:
                print(f"Warning: GLM backend failed to initialize: {e}")
        except Exception as e:
            print(f"Warning: GLM backend failed to initialize: {e}")

    def _setup_local_backend(self):
        """Setup local embedding model"""
        try:
            from sentence_transformers import SentenceTransformer

            model_config = self.config.get("embedding", {}).get("backends", {}).get("local", {})
            model_name = model_config.get("model", "nomic-ai/nomic-embed-text-v1")

            print(f"Loading local model: {model_name}...")
            # Add trust_remote_code=True for models that require it (like Nomic)
            self.local_model = SentenceTransformer(model_name, trust_remote_code=True)
            print("✓ Local embedding backend initialized")

        except ImportError:
            print("Warning: sentence-transformers not installed. Install with: pip install sentence-transformers")
        except Exception as e:
            print(f"Warning: Local backend failed to initialize: {e}")

    def embed(
        self,
        texts: Union[str, List[str]],
        backend: Optional[str] = None,
        normalize: bool = True
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s)

        Args:
            texts: Single text or list of texts
            backend: Force specific backend ("glm" or "local")
            normalize: Normalize embeddings to unit length

        Returns:
            Embedding vector(s)
        """
        single_input = isinstance(texts, str)
        if single_input:
            texts = [texts]

        embeddings = self._embed_batch(texts, backend)

        if normalize:
            embeddings = self._normalize(embeddings)

        if single_input:
            return embeddings[0]

        return embeddings

    def _embed_batch(self, texts: List[str], backend: Optional[str] = None) -> List[List[float]]:
        """Embed a batch of texts"""
        mode = self.config.get("embedding", {}).get("mode", "hybrid")
        primary = self.config.get("embedding", {}).get("primary_backend", "glm")

        # Determine which backend to use
        if backend:
            target_backend = backend
        elif mode == "glm":
            target_backend = "glm"
        elif mode == "local":
            target_backend = "local"
        else:  # hybrid
            target_backend = primary

        # Try primary backend
        if target_backend == "glm" and self.glm_client:
            try:
                return self._embed_with_glm(texts)
            except Exception as e:
                print(f"GLM embedding failed: {e}, falling back to local")
                if self.local_model:
                    return self._embed_with_local(texts)
                raise

        elif target_backend == "local" and self.local_model:
            return self._embed_with_local(texts)

        # Fallback
        if self.local_model:
            return self._embed_with_local(texts)

        raise RuntimeError("No embedding backend available")

    def _embed_with_glm(self, texts: List[str]) -> List[List[float]]:
        """Embed using GLM API"""
        glm_config = self.config.get("embedding", {}).get("backends", {}).get("glm", {})
        model_name = glm_config.get("model", "embedding-2")  # Changed to embedding-2 as it's more commonly available
        dimensions = glm_config.get("dimensions", 1024)

        embeddings = []

        # Check which SDK we're using
        sdk = getattr(self, 'glm_sdk', 'zhipuai')

        # GLM API processes texts (can handle batch)
        try:
            if sdk == "zai":
                # New zai-sdk format
                response = self.glm_client.embeddings.create(
                    model=model_name,
                    input=texts,
                    dimensions=dimensions
                )
                # Extract embeddings
                for item in response.data:
                    embeddings.append(item.embedding)
            else:
                # Old zhipuai SDK format
                for text in texts:
                    response = self.glm_client.embeddings.create(
                        model=model_name,
                        input=text
                    )
                    embeddings.append(response.data[0].embedding)

        except Exception as e:
            raise RuntimeError(f"GLM API call failed: {e}")

        return embeddings

    def _embed_with_local(self, texts: List[str]) -> List[List[float]]:
        """Embed using local model"""
        local_config = self.config.get("embedding", {}).get("backends", {}).get("local", {})
        normalize = local_config.get("normalize_embeddings", True)

        embeddings = self.local_model.encode(
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )

        return embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings

    def _normalize(self, embeddings: List[List[float]]) -> List[List[float]]:
        """Normalize embeddings to unit length"""
        import numpy as np

        embeddings_array = np.array(embeddings)
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        normalized = embeddings_array / (norms + 1e-8)

        return normalized.tolist()

    @lru_cache(maxsize=1000)
    def embed_cached(self, text: str, backend: Optional[str] = None) -> List[float]:
        """Embed with caching for frequently used texts"""
        return self.embed(text, backend=backend)

    def get_embedding_dim(self) -> int:
        """Get the dimension of embeddings"""
        if self.glm_client:
            return self.config.get("embedding", {}).get("backends", {}).get("glm", {}).get("dimensions", 1024)
        elif self.local_model:
            return self.local_model.get_sentence_embedding_dimension()
        return 768  # Default

    def get_backend_status(self) -> dict:
        """Get status of all backends"""
        return {
            "glm_available": self.glm_client is not None,
            "local_available": self.local_model is not None,
            "current_mode": self.config.get("embedding", {}).get("mode", "hybrid"),
            "primary_backend": self.config.get("embedding", {}).get("primary_backend", "glm"),
            "embedding_dim": self.get_embedding_dim()
        }


# CLI interface for testing
if __name__ == "__main__":
    import sys

    embedder = HybridEmbedder()

    print("\n=== Hybrid Embedder Status ===")
    status = embedder.get_backend_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = "Blackbox4 semantic search system"

    print(f"\n=== Embedding Test ===")
    print(f"Text: {text}")

    try:
        embedding = embedder.embed(text)
        print(f"✓ Embedding generated successfully")
        print(f"  Dimension: {len(embedding)}")
        print(f"  Sample (first 5): {embedding[:5]}")
    except Exception as e:
        print(f"✗ Embedding failed: {e}")
