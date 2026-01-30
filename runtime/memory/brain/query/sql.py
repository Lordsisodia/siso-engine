"""
Blackbox4 Brain v2.0 - Structured Query Interface
Query artifacts from PostgreSQL using structured filters.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from enum import Enum

from ..ingest.db import Database, execute_query


class QueryType(Enum):
    """Types of queries."""
    BY_TYPE = "by_type"
    BY_CATEGORY = "by_category"
    BY_TAG = "by_tag"
    BY_STATUS = "by_status"
    BY_PHASE = "by_phase"
    BY_LAYER = "by_layer"
    BY_OWNER = "by_owner"
    BY_DATE_RANGE = "by_date_range"
    DEPENDENCIES = "dependencies"
    DEPENDENTS = "dependents"
    RELATED = "related"
    FULL_TEXT = "full_text"
    COMPLEX = "complex"


class BrainQuery:
    """Structured query interface for Blackbox4 Brain."""

    def __init__(self):
        """Initialize query interface."""
        self._initialized = False

    async def initialize(self):
        """Initialize database connection."""
        if not self._initialized:
            await Database.initialize()
            self._initialized = True

    async def close(self):
        """Close database connection."""
        await Database.close()
        self._initialized = False

    # ---------------------------------------------------------------------
    # Basic Queries
    # ---------------------------------------------------------------------

    async def get_artifact_by_id(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get artifact by ID.

        Args:
            artifact_id: Artifact ID

        Returns:
            Artifact dictionary or None
        """
        await self.initialize()

        result = await execute_query(
            "SELECT * FROM artifacts WHERE id = $1",
            artifact_id,
            fetch='one'
        )

        if result:
            return dict(result)
        return None

    async def get_artifact_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get artifact by path.

        Args:
            path: Artifact path

        Returns:
            Artifact dictionary or None
        """
        await self.initialize()

        result = await execute_query(
            "SELECT * FROM artifacts WHERE path = $1",
            path,
            fetch='one'
        )

        if result:
            return dict(result)
        return None

    async def list_artifacts(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = 'name'
    ) -> List[Dict[str, Any]]:
        """List all artifacts with pagination.

        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            order_by: Field to order by

        Returns:
            List of artifact dictionaries
        """
        await self.initialize()

        results = await execute_query(
            f"SELECT * FROM artifacts ORDER BY {order_by} LIMIT $1 OFFSET $2",
            limit,
            offset,
            fetch='all'
        )

        return [dict(r) for r in results]

    async def count_artifacts(self) -> int:
        """Count total artifacts.

        Returns:
            Total count
        """
        await self.initialize()

        return await execute_query("SELECT COUNT(*) FROM artifacts", fetch='val')

    # ---------------------------------------------------------------------
    # Filter Queries
    # ---------------------------------------------------------------------

    async def find_by_type(
        self,
        artifact_type: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find all artifacts of a specific type.

        Args:
            artifact_type: Artifact type (e.g., 'agent', 'library')
            status: Optional status filter

        Returns:
            List of artifact dictionaries
        """
        await self.initialize()

        if status:
            results = await execute_query(
                "SELECT * FROM artifacts WHERE type = $1 AND status = $2 ORDER BY name",
                artifact_type,
                status,
                fetch='all'
            )
        else:
            results = await execute_query(
                "SELECT * FROM artifacts WHERE type = $1 ORDER BY name",
                artifact_type,
                fetch='all'
            )

        return [dict(r) for r in results]

    async def find_by_category(
        self,
        artifact_type: str,
        category: str
    ) -> List[Dict[str, Any]]:
        """Find all artifacts in a specific category.

        Args:
            artifact_type: Artifact type
            category: Category within type

        Returns:
            List of artifact dictionaries
        """
        await self.initialize()

        results = await execute_query(
            "SELECT * FROM artifacts WHERE type = $1 AND category = $2 ORDER BY name",
            artifact_type,
            category,
            fetch='all'
        )

        return [dict(r) for r in results]

    async def find_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Find all artifacts with a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of artifact dictionaries
        """
        await self.initialize()

        results = await execute_query(
            "SELECT * FROM artifacts WHERE $1 = ANY(tags) ORDER BY name",
            tag,
            fetch='all'
        )

        return [dict(r) for r in results]

    async def find_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict[str, Any]]:
        """Find artifacts with multiple tags.

        Args:
            tags: List of tags
            match_all: If True, must match all tags; if False, match any tag

        Returns:
            List of artifact dictionaries
        """
        await self.initialize()

        if match_all:
            # Must contain all tags
            results = await execute_query(
                "SELECT * FROM artifacts WHERE tags @> $1::text[] ORDER BY name",
                tags,
                fetch='all'
            )
        else:
            # Must contain at least one tag
            results = await execute_query(
                "SELECT * FROM artifacts WHERE tags && $1::text[] ORDER BY name",
                tags,
                fetch='all'
            )

        return [dict(r) for r in results]

    async def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Find all artifacts with a specific status.

        Args:
            status: Status (e.g., 'active', 'deprecated')

        Returns:
            List of artifact dictionaries
        """
        await self.initialize()

        results = await execute_query(
            "SELECT * FROM artifacts WHERE status = $1 ORDER BY name",
            status,
            fetch='all'
        )

        return [dict(r) for r in results]

    async def find_by_phase(self, phase: int) -> List[Dict[str, Any]]:
        """Find all artifacts in a specific phase.

        Args:
            phase: Phase number (1-4)

        Returns:
            List of artifact dictionaries
        """
        await self.initialize()

        results = await execute_query(
            "SELECT * FROM artifacts WHERE phase = $1 ORDER BY type, category, name",
            phase,
            fetch='all'
        )

        return [dict(r) for r in results]

    async def find_by_layer(self, layer: str) -> List[Dict[str, Any]]:
        """Find all artifacts in a specific layer.

        Args:
            layer: Layer (e.g., 'intelligence', 'execution')

        Returns:
            List of artifact dictionaries
        """
        await self.initialize()

        results = await execute_query(
            "SELECT * FROM artifacts WHERE layer = $1 ORDER BY name",
            layer,
            fetch='all'
        )

        return [dict(r) for r in results]

    async def find_by_owner(self, owner: str) -> List[Dict[str, Any]]:
        """Find all artifacts owned by a specific team/person.

        Args:
            owner: Owner name

        Returns:
            List of artifact dictionaries
        """
        await self.initialize()

        results = await execute_query(
            "SELECT * FROM artifacts WHERE owner = $1 ORDER BY name",
            owner,
            fetch='all'
        )

        return [dict(r) for r in results]

    async def find_by_date_range(
        self,
        start_date: str,
        end_date: str,
        date_field: str = 'created'
    ) -> List[Dict[str, Any]]:
        """Find artifacts created/modified within a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            date_field: 'created' or 'modified'

        Returns:
            List of artifact dictionaries
        """
        await self.initialize()

        results = await execute_query(
            f"SELECT * FROM artifacts WHERE {date_field} >= $1 AND {date_field} <= $2 ORDER BY {date_field} DESC",
            start_date,
            end_date,
            fetch='all'
        )

        return [dict(r) for r in results]

    async def find_recent(self, days: int = 30) -> List[Dict[str, Any]]:
        """Find recently modified artifacts.

        Args:
            days: Number of days to look back

        Returns:
            List of artifact dictionaries
        """
        await self.initialize()

        results = await execute_query(
            "SELECT * FROM artifacts WHERE modified >= CURRENT_DATE - INTERVAL '1 day' * $1 ORDER BY modified DESC",
            days,
            fetch='all'
        )

        return [dict(r) for r in results]

    # ---------------------------------------------------------------------
    # Relationship Queries
    # ---------------------------------------------------------------------

    async def find_dependencies(self, artifact_id: str) -> List[Dict[str, Any]]:
        """Find what this artifact depends on.

        Args:
            artifact_id: Artifact ID

        Returns:
            List of artifacts this artifact depends on
        """
        await self.initialize()

        results = await execute_query(
            """SELECT a.*
               FROM artifacts a
               JOIN relationships r ON r.to_id = a.id
               WHERE r.from_id = $1 AND r.relationship_type = 'depends_on'
               ORDER BY a.name""",
            artifact_id,
            fetch='all'
        )

        return [dict(r) for r in results]

    async def find_dependents(self, artifact_id: str) -> List[Dict[str, Any]]:
        """Find what depends on this artifact.

        Args:
            artifact_id: Artifact ID

        Returns:
            List of artifacts that depend on this artifact
        """
        await self.initialize()

        results = await execute_query(
            """SELECT a.*
               FROM artifacts a
               JOIN relationships r ON r.from_id = a.id
               WHERE r.to_id = $1 AND r.relationship_type = 'depends_on'
               ORDER BY a.name""",
            artifact_id,
            fetch='all'
        )

        return [dict(r) for r in results]

    async def find_related(self, artifact_id: str, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find artifacts related to this artifact.

        Args:
            artifact_id: Artifact ID
            relationship_type: Optional relationship type filter

        Returns:
            List of related artifacts
        """
        await self.initialize()

        if relationship_type:
            results = await execute_query(
                """SELECT DISTINCT a.*
                   FROM artifacts a
                   JOIN relationships r ON (r.from_id = $1 OR r.to_id = $1)
                   WHERE (r.from_id = a.id OR r.to_id = a.id)
                     AND a.id != $1
                     AND r.relationship_type = $2
                   ORDER BY a.name""",
                artifact_id,
                relationship_type,
                fetch='all'
            )
        else:
            results = await execute_query(
                """SELECT DISTINCT a.*
                   FROM artifacts a
                   JOIN relationships r ON (r.from_id = $1 OR r.to_id = $1)
                   WHERE (r.from_id = a.id OR r.to_id = a.id)
                     AND a.id != $1
                   ORDER BY a.name""",
                artifact_id,
                fetch='all'
            )

        return [dict(r) for r in results]

    # ---------------------------------------------------------------------
    # Complex Queries
    # ---------------------------------------------------------------------

    async def search(
        self,
        query: str,
        artifact_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Full-text search across artifacts.

        Args:
            query: Search query
            artifact_type: Optional type filter
            limit: Maximum results

        Returns:
            List of artifact dictionaries
        """
        await self.initialize()

        if artifact_type:
            results = await execute_query(
                """SELECT *
                   FROM artifacts
                   WHERE to_tsvector('english',
                       coalesce(name, '') || ' ' ||
                       coalesce(description, '') || ' ' ||
                       coalesce(array_to_string(tags, ' '), '')
                   ) @@ plainto_tsquery('english', $1)
                   AND type = $2
                   ORDER BY name
                   LIMIT $3""",
                query,
                artifact_type,
                limit,
                fetch='all'
            )
        else:
            results = await execute_query(
                """SELECT *
                   FROM artifacts
                   WHERE to_tsvector('english',
                       coalesce(name, '') || ' ' ||
                       coalesce(description, '') || ' ' ||
                       coalesce(array_to_string(tags, ' '), '')
                   ) @@ plainto_tsquery('english', $1)
                   ORDER BY name
                   LIMIT $2""",
                query,
                limit,
                fetch='all'
            )

        return [dict(r) for r in results]

    async def complex_query(
        self,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Execute a complex query with multiple filters.

        Args:
            filters: Dictionary of filters
                - type: Artifact type
                - category: Category
                - status: Status
                - phase: Phase number
                - layer: Layer
                - owner: Owner
                - tags: List of tags (AND logic)
                - created_after: Date string
                - created_before: Date string
                - modified_after: Date string
                - modified_before: Date string
            limit: Maximum results
            offset: Offset for pagination

        Returns:
            List of artifact dictionaries
        """
        await self.initialize()

        # Build query dynamically
        conditions = []
        params = []
        param_count = 1

        if 'type' in filters:
            conditions.append(f"type = ${param_count}")
            params.append(filters['type'])
            param_count += 1

        if 'category' in filters:
            conditions.append(f"category = ${param_count}")
            params.append(filters['category'])
            param_count += 1

        if 'status' in filters:
            conditions.append(f"status = ${param_count}")
            params.append(filters['status'])
            param_count += 1

        if 'phase' in filters:
            conditions.append(f"phase = ${param_count}")
            params.append(filters['phase'])
            param_count += 1

        if 'layer' in filters:
            conditions.append(f"layer = ${param_count}")
            params.append(filters['layer'])
            param_count += 1

        if 'owner' in filters:
            conditions.append(f"owner = ${param_count}")
            params.append(filters['owner'])
            param_count += 1

        if 'tags' in filters:
            conditions.append(f"tags @> ${param_count}::text[]")
            params.append(filters['tags'])
            param_count += 1

        if 'created_after' in filters:
            conditions.append(f"created >= ${param_count}")
            params.append(filters['created_after'])
            param_count += 1

        if 'created_before' in filters:
            conditions.append(f"created <= ${param_count}")
            params.append(filters['created_before'])
            param_count += 1

        if 'modified_after' in filters:
            conditions.append(f"modified >= ${param_count}")
            params.append(filters['modified_after'])
            param_count += 1

        if 'modified_before' in filters:
            conditions.append(f"modified <= ${param_count}")
            params.append(filters['modified_before'])
            param_count += 1

        # Build WHERE clause
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Execute query
        query = f"""
            SELECT * FROM artifacts
            {where_clause}
            ORDER BY name
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """

        params.extend([limit, offset])

        results = await execute_query(query, *params, fetch='all')

        return [dict(r) for r in results]

    # ---------------------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------------------

    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with statistics
        """
        await self.initialize()

        total = await execute_query("SELECT COUNT(*) FROM artifacts", fetch='val')
        by_type = await execute_query(
            "SELECT type, COUNT(*) as count FROM artifacts GROUP BY type ORDER BY count DESC",
            fetch='all'
        )
        by_status = await execute_query(
            "SELECT status, COUNT(*) as count FROM artifacts GROUP BY status ORDER BY count DESC",
            fetch='all'
        )
        relationships = await execute_query("SELECT COUNT(*) FROM relationships", fetch='val')

        return {
            'total_artifacts': total,
            'by_type': {r['type']: r['count'] for r in by_type},
            'by_status': {r['status']: r['count'] for r in by_status},
            'total_relationships': relationships,
        }


# Convenience singleton
_query_instance: Optional[BrainQuery] = None


def get_query() -> BrainQuery:
    """Get query instance."""
    global _query_instance
    if _query_instance is None:
        _query_instance = BrainQuery()
    return _query_instance


async def query_artifact(artifact_id: str) -> Optional[Dict[str, Any]]:
    """Quick query for single artifact."""
    q = get_query()
    return await q.get_artifact_by_id(artifact_id)


async def search_artifacts(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Quick full-text search."""
    q = get_query()
    return await q.search(query, limit=limit)
