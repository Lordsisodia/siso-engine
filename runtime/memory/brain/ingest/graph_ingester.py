#!/usr/bin/env python3
"""
Blackbox4 Brain - Graph Ingestion Pipeline
Ingests metadata.yaml files into Neo4j graph database

Usage:
    python graph_ingester.py --file /path/to/metadata.yaml
    python graph_ingester.py --directory /path/to/directory
    python graph_ingester.py --blackbox4 /path/to/blackbox4
    python graph_ingester.py --sync  # Sync all artifacts
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Try to import neo4j driver
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("WARNING: neo4j driver not installed. Install with: pip install neo4j")
    print("Graph ingestion will be skipped.")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Manages Neo4j database connection"""

    def __init__(self, uri: str = "bolt://localhost:7687",
                 user: str = "neo4j", password: str = "blackbox4brain"):
        if not NEO4J_AVAILABLE:
            raise ImportError("neo4j driver not installed")

        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None

    def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Test connection
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False

    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def execute_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Execute a Cypher query and return results"""
        if not self.driver:
            raise ConnectionError("Not connected to Neo4j")

        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def execute_write(self, query: str, parameters: Dict = None) -> Any:
        """Execute a write query"""
        if not self.driver:
            raise ConnectionError("Not connected to Neo4j")

        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                summary = result.consume()
                return summary
        except Exception as e:
            logger.error(f"Write query failed: {e}")
            raise


class GraphIngester:
    """Ingests metadata into Neo4j graph database"""

    def __init__(self, connection: Neo4jConnection):
        self.connection = connection

    def ingest_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Ingest a single metadata file into Neo4j

        Args:
            metadata: Parsed metadata dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            artifact_id = metadata.get('id')
            if not artifact_id:
                logger.error("Metadata missing 'id' field")
                return False

            # Create or update artifact node
            self._create_or_update_artifact(metadata)

            # Handle relationships
            self._ingest_relationships(metadata, artifact_id)

            logger.info(f"Successfully ingested artifact: {artifact_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to ingest metadata: {e}")
            return False

    def _create_or_update_artifact(self, metadata: Dict[str, Any]):
        """Create or update an artifact node"""
        query = """
        MERGE (a:Artifact {id: $id})
        ON CREATE SET
            a.created_at = datetime(),
            a.first_seen = datetime()
        ON MATCH SET
            a.updated_at = datetime()
        SET
            a.type = $type,
            a.name = $name,
            a.category = $category,
            a.version = $version,
            a.path = $path,
            a.created = $created,
            a.modified = $modified,
            a.description = $description,
            a.tags = $tags,
            a.keywords = $keywords,
            a.status = $status,
            a.stability = $stability,
            a.owner = $owner,
            a.maintainer = $maintainer,
            a.phase = $phase,
            a.layer = $layer,
            a.usage_count = $usage_count,
            a.last_used = $last_used,
            a.success_rate = $success_rate,
            a.docs = $docs,
            a.embedding_id = $embedding_id
        RETURN a
        """

        # Prepare parameters
        params = {
            'id': metadata.get('id'),
            'type': metadata.get('type'),
            'name': metadata.get('name'),
            'category': metadata.get('category'),
            'version': metadata.get('version'),
            'path': metadata.get('path'),
            'created': metadata.get('created'),
            'modified': metadata.get('modified'),
            'description': metadata.get('description', ''),
            'tags': metadata.get('tags', []),
            'keywords': metadata.get('keywords', []),
            'status': metadata.get('status', 'development'),
            'stability': metadata.get('stability', 'medium'),
            'owner': metadata.get('owner'),
            'maintainer': metadata.get('maintainer'),
            'phase': metadata.get('phase'),
            'layer': metadata.get('layer'),
            'usage_count': metadata.get('usage_count', 0),
            'last_used': metadata.get('last_used'),
            'success_rate': metadata.get('success_rate'),
            'docs': metadata.get('docs'),
            'embedding_id': metadata.get('embedding_id')
        }

        self.connection.execute_write(query, params)

    def _ingest_relationships(self, metadata: Dict[str, Any], artifact_id: str):
        """Ingest all relationships for an artifact"""
        # Handle DEPENDS_ON relationships
        for dep in metadata.get('depends_on', []):
            self._create_relationship(
                artifact_id,
                dep.get('id'),
                'DEPENDS_ON',
                {
                    'strength': 'required',
                    'version': dep.get('version'),
                    'created_at': datetime.now().isoformat()
                }
            )

        # Handle USED_BY relationships
        for user in metadata.get('used_by', []):
            self._create_relationship(
                artifact_id,
                user.get('id'),
                'USED_BY',
                {
                    'strength': 'direct',
                    'created_at': datetime.now().isoformat()
                }
            )

        # Handle RELATES_TO relationships
        for related in metadata.get('relates_to', []):
            self._create_relationship(
                artifact_id,
                related.get('id'),
                'RELATES_TO',
                {
                    'relationship': related.get('relationship'),
                    'strength': 'strong',
                    'created_at': datetime.now().isoformat()
                }
            )

    def _create_relationship(self, from_id: str, to_id: str,
                           rel_type: str, properties: Dict[str, Any]):
        """Create a relationship between two artifacts"""
        query = f"""
        MATCH (from:Artifact {{id: $from_id}})
        MATCH (to:Artifact {{id: $to_id}})
        MERGE (from)-[r:{rel_type}]->(to)
        SET r += $properties
        RETURN r
        """

        params = {
            'from_id': from_id,
            'to_id': to_id,
            'properties': properties
        }

        try:
            self.connection.execute_write(query, params)
        except Exception as e:
            logger.warning(f"Failed to create relationship {from_id}-[{rel_type}]->{to_id}: {e}")

    def delete_artifact(self, artifact_id: str) -> bool:
        """Delete an artifact and all its relationships"""
        query = """
        MATCH (a:Artifact {id: $artifact_id})
        DETACH DELETE a
        RETURN count(*) as deleted
        """

        try:
            result = self.connection.execute_write(query, {'artifact_id': artifact_id})
            logger.info(f"Deleted artifact: {artifact_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete artifact {artifact_id}: {e}")
            return False

    def batch_ingest(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Ingest multiple metadata files

        Returns:
            Dictionary with success/failure counts
        """
        results = {'success': 0, 'failed': 0, 'errors': []}

        for metadata in metadata_list:
            try:
                if self.ingest_metadata(metadata):
                    results['success'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'id': metadata.get('id', 'unknown'),
                    'error': str(e)
                })

        return results


def load_metadata(file_path: str) -> Optional[Dict[str, Any]]:
    """Load metadata from a YAML file"""
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


def find_metadata_files(directory: str) -> List[str]:
    """Find all metadata.yaml files in a directory"""
    metadata_files = []
    path = Path(directory)

    # Find all metadata.yaml files
    for metadata_file in path.rglob('metadata.yaml'):
        metadata_files.append(str(metadata_file))

    return metadata_files


def main():
    parser = argparse.ArgumentParser(
        description='Ingest Blackbox4 metadata into Neo4j graph database'
    )
    parser.add_argument('--file', help='Single metadata file to ingest')
    parser.add_argument('--directory', help='Directory containing metadata files')
    parser.add_argument('--blackbox4', help='Path to Blackbox4 root')
    parser.add_argument('--sync', action='store_true',
                       help='Sync all artifacts from Blackbox4 root')
    parser.add_argument('--uri', default='bolt://localhost:7687',
                       help='Neo4j URI (default: bolt://localhost:7687)')
    parser.add_argument('--user', default='neo4j',
                       help='Neo4j user (default: neo4j)')
    parser.add_argument('--password', default='blackbox4brain',
                       help='Neo4j password (default: blackbox4brain)')
    parser.add_argument('--delete', help='Delete artifact by ID')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check if neo4j is available
    if not NEO4J_AVAILABLE:
        print("ERROR: neo4j driver not installed")
        print("Install with: pip install neo4j")
        sys.exit(1)

    # Connect to Neo4j
    connection = Neo4jConnection(args.uri, args.user, args.password)
    if not connection.connect():
        print("ERROR: Failed to connect to Neo4j")
        print(f"Make sure Neo4j is running at {args.uri}")
        print("Start with: cd 9-brain/databases/neo4j && docker-compose up -d")
        sys.exit(1)

    ingester = GraphIngester(connection)

    try:
        # Handle delete operation
        if args.delete:
            success = ingester.delete_artifact(args.delete)
            sys.exit(0 if success else 1)

        # Find files to process
        files_to_process = []

        if args.file:
            files_to_process = [args.file]
        elif args.directory:
            files_to_process = find_metadata_files(args.directory)
        elif args.blackbox4 or args.sync:
            # Use current directory if not specified
            bb4_root = args.blackbox4 or os.getcwd()
            files_to_process = find_metadata_files(bb4_root)

        if not files_to_process:
            print("No metadata.yaml files found")
            sys.exit(1)

        print(f"Found {len(files_to_process)} metadata files")

        # Load and ingest all metadata
        metadata_list = []
        for file_path in files_to_process:
            metadata = load_metadata(file_path)
            if metadata:
                metadata_list.append(metadata)

        # Batch ingest
        results = ingester.batch_ingest(metadata_list)

        # Print results
        print(f"\nIngestion complete:")
        print(f"  Success: {results['success']}")
        print(f"  Failed: {results['failed']}")

        if results['errors']:
            print(f"\nErrors:")
            for error in results['errors']:
                print(f"  - {error['id']}: {error['error']}")

        sys.exit(0 if results['failed'] == 0 else 1)

    finally:
        connection.close()


if __name__ == '__main__':
    main()
