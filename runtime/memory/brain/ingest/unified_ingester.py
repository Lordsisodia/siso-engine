#!/usr/bin/env python3
"""
Blackbox4 Brain - Unified Ingestion Pipeline
Ingests metadata into both PostgreSQL and Neo4j simultaneously

Usage:
    python unified_ingester.py --sync
    python unified_ingester.py --file /path/to/metadata.yaml
    python unified_ingester.py --directory /path/to/directory
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Try imports
try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Install with: pip install pyyaml")
    sys.exit(1)

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("WARNING: neo4j driver not installed. Graph features disabled.")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedIngester:
    """Ingests metadata into both PostgreSQL and Neo4j"""

    def __init__(self,
                 postgresql_uri: str = "postgresql://localhost:5432/blackbox4_brain",
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "blackbox4brain"):

        self.postgresql_uri = postgresql_uri
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password

        self.neo4j_driver = None
        self.postgresql_pool = None

        self.stats = {
            'scanned': 0,
            'parsed': 0,
            'postgresql_inserted': 0,
            'postgresql_updated': 0,
            'postgresql_failed': 0,
            'neo4j_ingested': 0,
            'neo4j_failed': 0,
            'relationships': 0,
        }

    async def connect_postgresql(self):
        """Connect to PostgreSQL"""
        try:
            import asyncpg

            self.postgresql_pool = await asyncpg.create_pool(
                self.postgresql_uri,
                min_size=2,
                max_size=10
            )
            logger.info("Connected to PostgreSQL")
            return True

        except ImportError:
            logger.warning("asyncpg not installed. PostgreSQL features disabled.")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False

    def connect_neo4j(self):
        """Connect to Neo4j"""
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j driver not installed")
            return False

        try:
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            self.neo4j_driver.verify_connectivity()
            logger.info("Connected to Neo4j")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False

    async def connect_all(self):
        """Connect to both databases"""
        pg_ok = await self.connect_postgresql()
        neo4j_ok = self.connect_neo4j()

        if not pg_ok and not neo4j_ok:
            logger.error("Failed to connect to any database")
            return False

        return True

    async def close_postgresql(self):
        """Close PostgreSQL connection"""
        if self.postgresql_pool:
            await self.postgresql_pool.close()
            logger.info("PostgreSQL connection closed")

    def close_neo4j(self):
        """Close Neo4j connection"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
            logger.info("Neo4j connection closed")

    async def close_all(self):
        """Close all database connections"""
        await self.close_postgresql()
        self.close_neo4j()

    def find_metadata_files(self, directory: str) -> List[str]:
        """Find all metadata.yaml files"""
        metadata_files = []
        path = Path(directory)

        for metadata_file in path.rglob('metadata.yaml'):
            metadata_files.append(str(metadata_file))

        return metadata_files

    def load_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load metadata from YAML file"""
        try:
            with open(file_path, 'r') as f:
                metadata = yaml.safe_load(f)
                if not metadata:
                    logger.error(f"Empty metadata file: {file_path}")
                    return None
                return metadata
        except Exception as e:
            logger.error(f"Failed to load metadata from {file_path}: {e}")
            return None

    async def ingest_postgresql(self, metadata: Dict[str, Any]) -> str:
        """Ingest into PostgreSQL"""
        if not self.postgresql_pool:
            return 'skipped'

        try:
            async with self.postgresql_pool.acquire() as conn:
                # Check if exists
                existing = await conn.fetchval(
                    "SELECT id FROM artifacts WHERE id = $1",
                    metadata.get('id')
                )

                if existing:
                    # Update
                    await conn.execute("""
                        UPDATE artifacts SET
                            type = $2, category = $3, name = $4, version = $5,
                            path = $6, created = $7, modified = $8,
                            description = $9, tags = $10, keywords = $11,
                            phase = $12, layer = $13, status = $14,
                            stability = $15, owner = $16, maintainer = $17,
                            usage_count = $18, last_used = $19, success_rate = $20
                        WHERE id = $1
                    """,
                    metadata.get('id'), metadata.get('type'), metadata.get('category'),
                    metadata.get('name'), metadata.get('version'), metadata.get('path'),
                    metadata.get('created'), metadata.get('modified'),
                    metadata.get('description'), metadata.get('tags', []),
                    metadata.get('keywords', []), metadata.get('phase'),
                    metadata.get('layer'), metadata.get('status'),
                    metadata.get('stability'), metadata.get('owner'),
                    metadata.get('maintainer'), metadata.get('usage_count'),
                    metadata.get('last_used'), metadata.get('success_rate')
                    )
                    return 'updated'
                else:
                    # Insert
                    await conn.execute("""
                        INSERT INTO artifacts (
                            id, type, category, name, version, path, created, modified,
                            description, tags, keywords, phase, layer, status, stability,
                            owner, maintainer, usage_count, last_used, success_rate
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                            $15, $16, $17, $18, $19, $20)
                    """,
                    metadata.get('id'), metadata.get('type'), metadata.get('category'),
                    metadata.get('name'), metadata.get('version'), metadata.get('path'),
                    metadata.get('created'), metadata.get('modified'),
                    metadata.get('description'), metadata.get('tags', []),
                    metadata.get('keywords', []), metadata.get('phase'),
                    metadata.get('layer'), metadata.get('status'),
                    metadata.get('stability'), metadata.get('owner'),
                    metadata.get('maintainer'), metadata.get('usage_count'),
                    metadata.get('last_used'), metadata.get('success_rate')
                    )
                    return 'inserted'

        except Exception as e:
            logger.error(f"PostgreSQL ingestion failed: {e}")
            return 'failed'

    def ingest_neo4j(self, metadata: Dict[str, Any]) -> bool:
        """Ingest into Neo4j"""
        if not self.neo4j_driver:
            return False

        try:
            with self.neo4j_driver.session() as session:
                # Create/update artifact node
                session.run("""
                    MERGE (a:Artifact {id: $id})
                    ON CREATE SET
                        a.created_at = datetime(),
                        a.first_seen = datetime()
                    ON MATCH SET
                        a.updated_at = datetime()
                    SET
                        a.type = $type, a.name = $name, a.category = $category,
                        a.version = $version, a.path = $path, a.created = $created,
                        a.modified = $modified, a.description = $description,
                        a.tags = $tags, a.keywords = $keywords, a.status = $status,
                        a.stability = $stability, a.owner = $owner, a.maintainer = $maintainer,
                        a.phase = $phase, a.layer = $layer, a.usage_count = $usage_count,
                        a.last_used = $last_used, a.success_rate = $success_rate,
                        a.docs = $docs, a.embedding_id = $embedding_id
                """,
                id=metadata.get('id'), type=metadata.get('type'), name=metadata.get('name'),
                category=metadata.get('category'), version=metadata.get('version'),
                path=metadata.get('path'), created=metadata.get('created'),
                modified=metadata.get('modified'), description=metadata.get('description'),
                tags=metadata.get('tags', []), keywords=metadata.get('keywords', []),
                status=metadata.get('status'), stability=metadata.get('stability'),
                owner=metadata.get('owner'), maintainer=metadata.get('maintainer'),
                phase=metadata.get('phase'), layer=metadata.get('layer'),
                usage_count=metadata.get('usage_count'), last_used=metadata.get('last_used'),
                success_rate=metadata.get('success_rate'), docs=metadata.get('docs'),
                embedding_id=metadata.get('embedding_id')
                )

                # Create relationships
                artifact_id = metadata.get('id')

                # DEPENDS_ON
                for dep in metadata.get('depends_on', []):
                    session.run("""
                        MATCH (from:Artifact {id: $from_id})
                        MATCH (to:Artifact {id: $to_id})
                        MERGE (from)-[r:DEPENDS_ON]->(to)
                        SET r.strength = $strength, r.version = $version
                    """,
                    from_id=artifact_id, to_id=dep.get('id'),
                    strength='required', version=dep.get('version')
                    )

                # USED_BY
                for user in metadata.get('used_by', []):
                    session.run("""
                        MATCH (from:Artifact {id: $from_id})
                        MATCH (to:Artifact {id: $to_id})
                        MERGE (from)-[r:USED_BY]->(to)
                        SET r.strength = $strength
                    """,
                    from_id=artifact_id, to_id=user.get('id'),
                    strength='direct'
                    )

                # RELATES_TO
                for related in metadata.get('relates_to', []):
                    session.run("""
                        MATCH (from:Artifact {id: $from_id})
                        MATCH (to:Artifact {id: $to_id})
                        MERGE (from)-[r:RELATES_TO]->(to)
                        SET r.relationship = $relationship, r.strength = $strength
                    """,
                    from_id=artifact_id, to_id=related.get('id'),
                    relationship=related.get('relationship'), strength='strong'
                    )

                return True

        except Exception as e:
            logger.error(f"Neo4j ingestion failed: {e}")
            return False

    async def ingest_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Ingest metadata into both databases"""
        artifact_id = metadata.get('id')

        # PostgreSQL
        pg_result = await self.ingest_postgresql(metadata)
        if pg_result == 'inserted':
            self.stats['postgresql_inserted'] += 1
        elif pg_result == 'updated':
            self.stats['postgresql_updated'] += 1
        elif pg_result == 'failed':
            self.stats['postgresql_failed'] += 1

        # Neo4j
        neo4j_result = self.ingest_neo4j(metadata)
        if neo4j_result:
            self.stats['neo4j_ingested'] += 1
        else:
            self.stats['neo4j_failed'] += 1

        # Count relationships
        rel_count = (
            len(metadata.get('depends_on', [])) +
            len(metadata.get('used_by', [])) +
            len(metadata.get('relates_to', []))
        )
        self.stats['relationships'] += rel_count

        return pg_result != 'failed' or neo4j_result

    async def ingest_file(self, file_path: str) -> bool:
        """Ingest a single metadata file"""
        metadata = self.load_metadata(file_path)
        if not metadata:
            return False

        self.stats['parsed'] += 1
        return await self.ingest_metadata(metadata)

    async def ingest_directory(self, directory: str, clean: bool = False):
        """Ingest all metadata files in directory"""
        logger.info(f"Scanning {directory} for metadata files...")

        # Find all metadata files
        files = self.find_metadata_files(directory)
        self.stats['scanned'] = len(files)

        logger.info(f"Found {len(files)} metadata files")

        if clean:
            logger.info("Cleaning databases...")
            # Clean PostgreSQL
            if self.postgresql_pool:
                async with self.postgresql_pool.acquire() as conn:
                    await conn.execute("DELETE FROM relationships")
                    await conn.execute("DELETE FROM artifacts")
            # Clean Neo4j
            if self.neo4j_driver:
                with self.neo4j_driver.session() as session:
                    session.run("MATCH (a:Artifact) DETACH DELETE a")
            logger.info("Databases cleaned")

        # Ingest all files
        for file_path in files:
            await self.ingest_file(file_path)

    def print_summary(self):
        """Print ingestion summary"""
        print("\n" + "=" * 60)
        print("Ingestion Summary")
        print("=" * 60)
        print(f"Scanned:     {self.stats['scanned']} files")
        print(f"Parsed:      {self.stats['parsed']} files")
        print(f"\nPostgreSQL:")
        print(f"  Inserted:  {self.stats['postgresql_inserted']}")
        print(f"  Updated:   {self.stats['postgresql_updated']}")
        print(f"  Failed:    {self.stats['postgresql_failed']}")
        print(f"\nNeo4j:")
        print(f"  Ingested:  {self.stats['neo4j_ingested']}")
        print(f"  Failed:    {self.stats['neo4j_failed']}")
        print(f"\nRelationships: {self.stats['relationships']}")
        print("=" * 60)


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Ingest Blackbox4 metadata into PostgreSQL and Neo4j'
    )
    parser.add_argument('--sync', action='store_true',
                       help='Sync all artifacts from Blackbox4 root')
    parser.add_argument('--directory', '-d', help='Directory to scan')
    parser.add_argument('--file', '-f', help='Single file to ingest')
    parser.add_argument('--clean', '-c', action='store_true',
                       help='Clean databases before ingesting')
    parser.add_argument('--postgresql-uri',
                       default='postgresql://localhost:5432/blackbox4_brain',
                       help='PostgreSQL connection URI')
    parser.add_argument('--neo4j-uri', default='bolt://localhost:7687',
                       help='Neo4j connection URI')
    parser.add_argument('--neo4j-user', default='neo4j',
                       help='Neo4j username')
    parser.add_argument('--neo4j-password', default='blackbox4brain',
                       help='Neo4j password')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create ingester
    ingester = UnifiedIngester(
        args.postgresql_uri,
        args.neo4j_uri,
        args.neo4j_user,
        args.neo4j_password
    )

    # Connect
    if not await ingester.connect_all():
        print("ERROR: Failed to connect to databases")
        print("Make sure PostgreSQL and Neo4j are running")
        sys.exit(1)

    try:
        # Determine what to ingest
        if args.file:
            await ingester.ingest_file(args.file)
        elif args.directory or args.sync:
            directory = args.directory or os.getcwd()
            await ingester.ingest_directory(directory, clean=args.clean)
        else:
            print("ERROR: Specify --file, --directory, or --sync")
            sys.exit(1)

        # Print summary
        ingester.print_summary()

    finally:
        await ingester.close_all()


if __name__ == '__main__':
    asyncio.run(main())
