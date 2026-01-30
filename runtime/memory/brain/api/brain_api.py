#!/usr/bin/env python3
"""
Blackbox4 Brain v2.0 - Query API
REST API for querying the brain system with semantic search.

Version: 1.0.0
Last Updated: 2026-01-15
"""

import os
import sys
import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Query, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from uvicorn import run

# Import brain modules
from ingest.embedder import EmbeddingGenerator, ArtifactEmbedder
from query.vector import VectorSearch, SearchResult
from query.nl_parser import NLQueryParser, QueryExecutor

# Import graph query
try:
    from query.graph import GraphQuery
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False
    logger.warning("Graph query not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# API APPLICATION
# ============================================================================

app = FastAPI(
    title="Blackbox4 Brain API",
    description="Query API for Blackbox4 Brain v2.0 with semantic search",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ArtifactMetadata(BaseModel):
    """Artifact metadata model."""
    id: str
    type: str
    name: str
    category: str
    version: Optional[str] = None
    path: str
    created: str
    modified: str
    description: str
    tags: List[str]
    keywords: Optional[List[str]] = None
    status: str = "active"
    stability: str = "medium"
    owner: str
    phase: Optional[int] = None
    layer: Optional[str] = None


class SemanticSearchRequest(BaseModel):
    """Semantic search request."""
    query: str = Field(..., description="Query text for semantic search")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters (type, category, status, etc.)")
    min_similarity: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")


class SimilarSearchRequest(BaseModel):
    """Find similar artifacts request."""
    artifact_id: str = Field(..., description="Reference artifact ID")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    exclude_self: bool = Field(True, description="Exclude reference artifact from results")


class HybridSearchRequest(BaseModel):
    """Hybrid search request (semantic + full-text)."""
    query: str = Field(..., description="Query text")
    query_vector: Optional[List[float]] = Field(None, description="Pre-computed query vector")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters")
    semantic_weight: float = Field(0.7, ge=0.0, le=1.0, description="Weight for semantic search")


class NLQueryRequest(BaseModel):
    """Natural language query request."""
    query: str = Field(..., description="Natural language query")


class ApiResponse(BaseModel):
    """Standard API response."""
    success: bool
    data: Any
    meta: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_vector_search():
    """Get vector search instance."""
    if not hasattr(app.state, 'vector_search'):
        try:
            app.state.vector_search = VectorSearch()
        except Exception as e:
            logger.error(f"Failed to initialize vector search: {e}")
            raise HTTPException(status_code=503, detail="Vector search not available")
    return app.state.vector_search


def get_embedder():
    """Get embedding generator instance."""
    if not hasattr(app.state, 'embedder'):
        try:
            app.state.embedder = ArtifactEmbedder(
                generator=EmbeddingGenerator(
                    model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                    use_local=os.getenv("USE_LOCAL_EMBEDDINGS", "false").lower() == "true"
                )
            )
        except Exception as e:
            logger.error(f"Failed to initialize embedder: {e}")
            raise HTTPException(status_code=503, detail="Embedding generator not available")
    return app.state.embedder


def get_nl_executor():
    """Get natural language query executor."""
    if not hasattr(app.state, 'nl_executor'):
        try:
            vector_search = get_vector_search()
            app.state.nl_executor = QueryExecutor(
                vector_search=vector_search,
                structured_search=None  # TODO: Add structured search
            )
        except Exception as e:
            logger.error(f"Failed to initialize NL executor: {e}")
            raise HTTPException(status_code=503, detail="NL query executor not available")
    return app.state.nl_executor


def get_graph_query():
    """Get graph query instance."""
    if not GRAPH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Graph query not available")

    if not hasattr(app.state, 'graph_query'):
        try:
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("NEO4J_PASSWORD", "blackbox4brain")

            app.state.graph_query = GraphQuery(neo4j_uri, neo4j_user, neo4j_password)
            if not app.state.graph_query.connect():
                raise Exception("Failed to connect to Neo4j")
        except Exception as e:
            logger.error(f"Failed to initialize graph query: {e}")
            raise HTTPException(status_code=503, detail="Graph database not available")
    return app.state.graph_query


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    status = {
        "status": "healthy",
        "version": "2.0.0",
        "services": {}
    }

    # Check vector search
    try:
        vector_search = get_vector_search()
        count = vector_search.count_embeddings()
        status["services"]["vector_search"] = "connected"
        status["services"]["embeddings_count"] = count
    except Exception as e:
        status["services"]["vector_search"] = f"error: {e}"
        status["status"] = "degraded"

    # Check embedder
    try:
        get_embedder()
        status["services"]["embedder"] = "available"
    except Exception as e:
        status["services"]["embedder"] = f"error: {e}"

    return status


# ============================================================================
# SEMANTIC SEARCH ENDPOINTS
# ============================================================================

@app.post("/api/v1/search/semantic", response_model=ApiResponse, tags=["Search"])
async def semantic_search(
    request: SemanticSearchRequest,
    embedder: ArtifactEmbedder = Depends(get_embedder),
    vector_search: VectorSearch = Depends(get_vector_search)
):
    """
    Semantic search using vector embeddings.

    Finds artifacts similar to the query text using semantic similarity.
    Supports filtering by type, category, status, tags, etc.

    Example:
    ```json
    {
      "query": "agents for data analysis and research",
      "limit": 10,
      "filters": {
        "type": "agent",
        "status": "active"
      },
      "min_similarity": 0.5
    }
    ```
    """
    start_time = time.time()

    try:
        # Generate embedding for query
        query_metadata = {
            "id": "query-temp",
            "name": request.query,
            "description": request.query,
            "type": "query",
            "category": "search",
            "tags": []
        }

        _, query_vector = embedder.embed(query_metadata)

        # Perform semantic search
        results = vector_search.semantic_search(
            query_vector=query_vector,
            limit=request.limit,
            filters=request.filters,
            min_similarity=request.min_similarity
        )

        execution_time = (time.time() - start_time) * 1000

        return ApiResponse(
            success=True,
            data=[r.to_dict() for r in results],
            meta={
                "query_type": "semantic",
                "execution_time_ms": round(execution_time, 2),
                "result_count": len(results),
                "query": request.query
            }
        )

    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/search/similar", response_model=ApiResponse, tags=["Search"])
async def find_similar(
    request: SimilarSearchRequest,
    vector_search: VectorSearch = Depends(get_vector_search)
):
    """
    Find artifacts similar to a given artifact.

    Uses the artifact's embedding to find semantically similar artifacts.

    Example:
    ```json
    {
      "artifact_id": "orchestrator-agent-v1",
      "limit": 10,
      "exclude_self": true
    }
    ```
    """
    start_time = time.time()

    try:
        results = vector_search.find_similar(
            artifact_id=request.artifact_id,
            limit=request.limit,
            exclude_self=request.exclude_self
        )

        execution_time = (time.time() - start_time) * 1000

        return ApiResponse(
            success=True,
            data=[r.to_dict() for r in results],
            meta={
                "query_type": "similarity",
                "execution_time_ms": round(execution_time, 2),
                "result_count": len(results),
                "reference_artifact": request.artifact_id
            }
        )

    except Exception as e:
        logger.error(f"Similarity search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/search/hybrid", response_model=ApiResponse, tags=["Search"])
async def hybrid_search(
    request: HybridSearchRequest,
    embedder: ArtifactEmbedder = Depends(get_embedder),
    vector_search: VectorSearch = Depends(get_vector_search)
):
    """
    Hybrid search combining semantic and full-text search.

    Combines vector similarity with full-text search for improved results.
    Can use pre-computed query vector or generate one from text.

    Example:
    ```json
    {
      "query": "data analysis tools",
      "limit": 10,
      "filters": {
        "type": "library"
      },
      "semantic_weight": 0.7
    }
    ```
    """
    start_time = time.time()

    try:
        # Generate embedding if not provided
        if request.query_vector is None:
            query_metadata = {
                "id": "query-temp",
                "name": request.query,
                "description": request.query,
                "type": "query",
                "category": "search",
                "tags": []
            }
            _, query_vector = embedder.embed(query_metadata)
        else:
            query_vector = request.query_vector

        # Perform hybrid search
        results = vector_search.hybrid_search(
            query_vector=query_vector,
            text_query=request.query,
            limit=request.limit,
            filters=request.filters,
            semantic_weight=request.semantic_weight
        )

        execution_time = (time.time() - start_time) * 1000

        return ApiResponse(
            success=True,
            data=[r.to_dict() for r in results],
            meta={
                "query_type": "hybrid",
                "execution_time_ms": round(execution_time, 2),
                "result_count": len(results),
                "query": request.query,
                "semantic_weight": request.semantic_weight
            }
        )

    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NATURAL LANGUAGE QUERY ENDPOINT
# ============================================================================

@app.post("/api/v1/query/nl", response_model=ApiResponse, tags=["Query"])
async def natural_language_query(
    request: NLQueryRequest,
    executor: QueryExecutor = Depends(get_nl_executor)
):
    """
    Natural language query interface.

    Parses natural language queries and routes to appropriate search method.

    Supports queries like:
    - "Find all specialist agents"
    - "What depends on the orchestrator?"
    - "Find artifacts similar to X"
    - "Where should I put a new data analysis agent?"

    Example:
    ```json
    {
      "query": "Find all active specialist agents for data analysis"
    }
    ```
    """
    start_time = time.time()

    try:
        result = executor.execute(request.query)
        execution_time = (time.time() - start_time) * 1000

        return ApiResponse(
            success=True,
            data=result,
            meta={
                "query_type": "natural_language",
                "execution_time_ms": round(execution_time, 2)
            }
        )

    except Exception as e:
        logger.error(f"NL query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ARTIFACT ENDPOINTS
# ============================================================================

@app.get("/api/v1/artifacts/{artifact_id}", response_model=ApiResponse, tags=["Artifacts"])
async def get_artifact(
    artifact_id: str,
    vector_search: VectorSearch = Depends(get_vector_search)
):
    """Get artifact by ID."""
    try:
        # TODO: Implement full artifact retrieval from PostgreSQL
        embedding = vector_search.get_embedding(artifact_id)

        if embedding is None:
            raise HTTPException(status_code=404, detail="Artifact not found")

        return ApiResponse(
            success=True,
            data={
                "artifact_id": artifact_id,
                "has_embedding": True,
                "embedding_dimensions": len(embedding)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/artifacts", response_model=ApiResponse, tags=["Artifacts"])
async def list_artifacts(
    type: Optional[str] = Query(None, description="Filter by type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    vector_search: VectorSearch = Depends(get_vector_search)
):
    """List artifacts with optional filters."""
    try:
        # TODO: Implement full artifact listing from PostgreSQL
        filters = {}
        if type:
            filters["type"] = type
        if category:
            filters["category"] = category
        if status:
            filters["status"] = status

        # Get embedding count as proxy for artifact count
        count = vector_search.count_embeddings()

        return ApiResponse(
            success=True,
            data={
                "artifacts": [],
                "total_with_embeddings": count
            },
            meta={
                "filters": filters,
                "limit": limit
            }
        )

    except Exception as e:
        logger.error(f"Failed to list artifacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GRAPH QUERY ENDPOINTS
# ============================================================================

@app.post("/api/v1/graph/query", tags=["Graph"])
async def execute_cypher(
    query: str = Body(..., description="Cypher query string", embed=True),
    parameters: Optional[Dict[str, Any]] = Body(None, description="Query parameters"),
    graph_query: GraphQuery = Depends(get_graph_query)
):
    """
    Execute a custom Cypher query.

    Example:
    ```json
    {
      "query": "MATCH (a:Artifact) WHERE a.type = 'agent' RETURN a LIMIT 10"
    }
    ```
    """
    try:
        results = graph_query.execute_cypher(query, parameters)
        return ApiResponse(
            success=True,
            data=results,
            meta={
                "query_type": "cypher",
                "result_count": len(results)
            }
        )
    except Exception as e:
        logger.error(f"Cypher query failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/graph/dependencies/{artifact_id}", response_model=ApiResponse, tags=["Graph"])
async def get_dependencies(
    artifact_id: str,
    depth: int = Query(10, ge=1, le=20, description="Maximum depth to traverse"),
    graph_query: GraphQuery = Depends(get_graph_query)
):
    """
    Get all dependencies for an artifact.

    Returns the complete dependency tree showing what this artifact depends on.
    """
    try:
        result = graph_query.get_dependencies(artifact_id, depth)
        return ApiResponse(
            success=True,
            data=result,
            meta={
                "artifact_id": artifact_id,
                "depth": depth
            }
        )
    except Exception as e:
        logger.error(f"Dependency query failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/graph/dependents/{artifact_id}", response_model=ApiResponse, tags=["Graph"])
async def get_dependents(
    artifact_id: str,
    depth: int = Query(10, ge=1, le=20, description="Maximum depth to traverse"),
    graph_query: GraphQuery = Depends(get_graph_query)
):
    """
    Get all artifacts that depend on this one.

    Shows what will break if this artifact is modified or removed.
    """
    try:
        result = graph_query.get_dependents(artifact_id, depth)
        return ApiResponse(
            success=True,
            data=result,
            meta={
                "artifact_id": artifact_id,
                "depth": depth
            }
        )
    except Exception as e:
        logger.error(f"Dependents query failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/graph/impact/{artifact_id}", response_model=ApiResponse, tags=["Graph"])
async def get_impact_analysis(
    artifact_id: str,
    graph_query: GraphQuery = Depends(get_graph_query)
):
    """
    Analyze impact if this artifact changes or breaks.

    Provides comprehensive impact analysis including severity assessment.
    """
    try:
        result = graph_query.get_impact_analysis(artifact_id)
        return ApiResponse(
            success=True,
            data=result,
            meta={
                "artifact_id": artifact_id
            }
        )
    except Exception as e:
        logger.error(f"Impact analysis failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/graph/path/{from_id}/{to_id}", response_model=ApiResponse, tags=["Graph"])
async def get_shortest_path(
    from_id: str,
    to_id: str,
    graph_query: GraphQuery = Depends(get_graph_query)
):
    """
    Find shortest path between two artifacts.

    Useful for understanding relationships and dependencies.
    """
    try:
        result = graph_query.get_shortest_path(from_id, to_id)
        return ApiResponse(
            success=True,
            data=result,
            meta={
                "from_id": from_id,
                "to_id": to_id
            }
        )
    except Exception as e:
        logger.error(f"Path query failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/graph/orphans", response_model=ApiResponse, tags=["Graph"])
async def find_orphans(
    graph_query: GraphQuery = Depends(get_graph_query)
):
    """
    Find all orphaned artifacts (no relationships).

    These artifacts have no dependencies or dependents.
    """
    try:
        result = graph_query.find_orphans()
        return ApiResponse(
            success=True,
            data={
                "orphans": result,
                "count": len(result)
            }
        )
    except Exception as e:
        logger.error(f"Orphans query failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/graph/circular", response_model=ApiResponse, tags=["Graph"])
async def find_circular_dependencies(
    graph_query: GraphQuery = Depends(get_graph_query)
):
    """
    Find all circular dependencies in the graph.

    Circular dependencies can cause issues and should be resolved.
    """
    try:
        result = graph_query.find_circular_dependencies()
        return ApiResponse(
            success=True,
            data={
                "cycles": result,
                "count": len(result)
            }
        )
    except Exception as e:
        logger.error(f"Circular dependency query failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/graph/unused", response_model=ApiResponse, tags=["Graph"])
async def find_unused_artifacts(
    graph_query: GraphQuery = Depends(get_graph_query)
):
    """
    Find artifacts that are not used by anything.

    These may be candidates for deprecation or removal.
    """
    try:
        result = graph_query.find_unused_artifacts()
        return ApiResponse(
            success=True,
            data={
                "unused": result,
                "count": len(result)
            }
        )
    except Exception as e:
        logger.error(f"Unused artifacts query failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/graph/relationships/{artifact_id}", response_model=ApiResponse, tags=["Graph"])
async def get_relationships(
    artifact_id: str,
    graph_query: GraphQuery = Depends(get_graph_query)
):
    """
    Get all relationships for an artifact.

    Returns both incoming and outgoing relationships.
    """
    try:
        result = graph_query.get_relationships(artifact_id)
        return ApiResponse(
            success=True,
            data=result,
            meta={
                "artifact_id": artifact_id
            }
        )
    except Exception as e:
        logger.error(f"Relationships query failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/graph/stats", response_model=ApiResponse, tags=["Graph"])
async def get_graph_statistics(
    graph_query: GraphQuery = Depends(get_graph_query)
):
    """
    Get overall graph statistics.

    Provides metrics about the artifact graph.
    """
    try:
        result = graph_query.get_statistics()
        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Statistics query failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# DOCUMENTATION
# ============================================================================

@app.get("/", tags=["Documentation"])
async def root():
    """API documentation."""
    return {
        "name": "Blackbox4 Brain API",
        "version": "2.0.0",
        "description": "Query API for Blackbox4 Brain v2.0 with semantic search",
        "endpoints": {
            "semantic_search": "/api/v1/search/semantic",
            "similar_search": "/api/v1/search/similar",
            "hybrid_search": "/api/v1/search/hybrid",
            "nl_query": "/api/v1/query/nl",
            "get_artifact": "/api/v1/artifacts/{id}",
            "list_artifacts": "/api/v1/artifacts",
            "health": "/health"
        },
        "documentation": "/docs"
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the API server."""
    import argparse

    parser = argparse.ArgumentParser(description="Blackbox4 Brain API Server")
    parser.add_argument(
        "--host",
        default=os.getenv("API_HOST", "0.0.0.0"),
        help="Host to bind to"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("API_PORT", "8000")),
        help="Port to bind to"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    logger.info(f"Starting Blackbox4 Brain API v2.0")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")

    run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
