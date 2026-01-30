"""
Blackbox4 Brain v2.0 - Query Interface
Query artifacts from PostgreSQL.
"""

from .sql import BrainQuery, get_query, query_artifact, search_artifacts

__all__ = [
    'BrainQuery',
    'get_query',
    'query_artifact',
    'search_artifacts',
]
