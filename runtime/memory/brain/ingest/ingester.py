"""
Blackbox4 Brain v2.0 - Metadata Ingestion Pipeline
Parse metadata.yaml files and insert into PostgreSQL.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from click import echo, secho, option, argument, command
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .db import Database, execute_query, execute_many
from .parser import parse_metadata_file, find_metadata_files


class MetadataIngester:
    """Ingest metadata files into PostgreSQL."""

    def __init__(self, root_dir: str = None):
        """Initialize ingester.

        Args:
            root_dir: Root directory to scan for metadata files
        """
        if root_dir is None:
            # Default to parent directories
            script_dir = Path(__file__).parent
            root_dir = script_dir.parent.parent

        self.root_dir = Path(root_dir).resolve()
        self.stats = {
            'scanned': 0,
            'parsed': 0,
            'inserted': 0,
            'updated': 0,
            'deleted': 0,
            'failed': 0,
            'relationships': 0,
        }

    async def initialize_database(self):
        """Initialize database connection and verify schema."""
        try:
            await Database.initialize()

            # Check if tables exist
            result = await execute_query("""
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_name = 'artifacts'
            """, fetch='val')

            if result == 0:
                secho("✗ Database schema not found. Run init.sql first.", fg='red')
                sys.exit(1)

            secho("✓ Database initialized", fg='green')

        except Exception as e:
            secho(f"✗ Failed to initialize database: {e}", fg='red')
            sys.exit(1)

    async def find_all_metadata(self) -> List[str]:
        """Find all metadata files.

        Returns:
            List of metadata file paths
        """
        secho(f"\nScanning {self.root_dir} for metadata files...", fg='blue')

        # Directories to scan
        scan_dirs = [
            self.root_dir / '1-agents',
            self.root_dir / '2-skills',
            self.root_dir / '3-plans',
            self.root_dir / '4-scripts',
            self.root_dir / '5-libraries',
            self.root_dir / '6-modules',
            self.root_dir / '8-workspaces',
            self.root_dir / '9-brain',
        ]

        metadata_files = []
        for scan_dir in scan_dirs:
            if scan_dir.exists():
                files = find_metadata_files(str(scan_dir))
                metadata_files.extend(files)

        self.stats['scanned'] = len(metadata_files)
        secho(f"✓ Found {len(metadata_files)} metadata files", fg='green')

        return metadata_files

    async def parse_metadata_files(self, metadata_files: List[str]) -> List[Dict[str, Any]]:
        """Parse all metadata files.

        Args:
            metadata_files: List of metadata file paths

        Returns:
            List of parsed metadata dictionaries
        """
        secho(f"\nParsing metadata files...", fg='blue')

        parsed = []
        failed = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            transient=True,
        ) as progress:

            task = progress.add_task("Parsing...", total=len(metadata_files))

            for file_path in metadata_files:
                result = parse_metadata_file(file_path)
                if result:
                    parsed.append(result)
                    self.stats['parsed'] += 1
                else:
                    failed.append(file_path)
                    self.stats['failed'] += 1

                progress.update(task, advance=1)

        secho(f"✓ Parsed {len(parsed)} files", fg='green')
        if failed:
            secho(f"✗ Failed to parse {len(failed)} files", fg='red')
            for f in failed[:5]:  # Show first 5
                echo(f"  - {f}")
            if len(failed) > 5:
                echo(f"  ... and {len(failed) - 5} more")

        return parsed

    async def ingest_artifact(self, artifact: Dict[str, Any]) -> str:
        """Ingest a single artifact.

        Args:
            artifact: Artifact dictionary from parser

        Returns:
            'inserted', 'updated', or 'failed'
        """
        try:
            # Check if artifact exists
            existing = await execute_query(
                "SELECT id FROM artifacts WHERE id = $1",
                artifact['id'],
                fetch='one'
            )

            if existing:
                # Update existing artifact
                await execute_query("""
                    UPDATE artifacts SET
                        type = $2,
                        category = $3,
                        name = $4,
                        version = $5,
                        path = $6,
                        created = $7,
                        modified = $8,
                        description = $9,
                        tags = $10,
                        keywords = $11,
                        phase = $12,
                        layer = $13,
                        status = $14,
                        stability = $15,
                        owner = $16,
                        maintainer = $17,
                        usage_count = $18,
                        last_used = $19,
                        success_rate = $20
                    WHERE id = $1
                """,
                artifact['id'],
                artifact['type'],
                artifact['category'],
                artifact['name'],
                artifact['version'],
                artifact['path'],
                artifact['created'],
                artifact['modified'],
                artifact['description'],
                artifact['tags'],
                artifact['keywords'],
                artifact['phase'],
                artifact['layer'],
                artifact['status'],
                artifact['stability'],
                artifact['owner'],
                artifact['maintainer'],
                artifact['usage_count'],
                artifact['last_used'],
                artifact['success_rate']
                )

                return 'updated'

            else:
                # Insert new artifact
                await execute_query("""
                    INSERT INTO artifacts (
                        id, type, category, name, version, path, created, modified,
                        description, tags, keywords, phase, layer, status, stability,
                        owner, maintainer, usage_count, last_used, success_rate
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                        $15, $16, $17, $18, $19, $20
                    )
                """,
                artifact['id'],
                artifact['type'],
                artifact['category'],
                artifact['name'],
                artifact['version'],
                artifact['path'],
                artifact['created'],
                artifact['modified'],
                artifact['description'],
                artifact['tags'],
                artifact['keywords'],
                artifact['phase'],
                artifact['layer'],
                artifact['status'],
                artifact['stability'],
                artifact['owner'],
                artifact['maintainer'],
                artifact['usage_count'],
                artifact['last_used'],
                artifact['success_rate']
                )

                return 'inserted'

        except Exception as e:
            echo(f"✗ Failed to ingest {artifact.get('id', 'unknown')}: {e}")
            return 'failed'

    async def ingest_relationships(self, relationships: List[Dict[str, Any]]):
        """Ingest relationships.

        Args:
            relationships: List of relationship dictionaries
        """
        if not relationships:
            return

        try:
            # Delete existing relationships for these artifacts
            artifact_ids = set(r['from_id'] for r in relationships)
            artifact_ids.update(r['to_id'] for r in relationships)

            for artifact_id in artifact_ids:
                await execute_query(
                    "DELETE FROM relationships WHERE from_id = $1 OR to_id = $1",
                    artifact_id
                )

            # Insert new relationships
            for rel in relationships:
                await execute_query("""
                    INSERT INTO relationships (from_id, to_id, relationship_type, strength, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (from_id, to_id, relationship_type) DO UPDATE SET
                        strength = EXCLUDED.strength,
                        metadata = EXCLUDED.metadata
                """,
                rel['from_id'],
                rel['to_id'],
                rel['relationship_type'],
                rel['strength'],
                rel.get('metadata')
                )

                self.stats['relationships'] += 1

        except Exception as e:
            echo(f"✗ Failed to ingest relationships: {e}")

    async def run(self, clean: bool = False):
        """Run the ingestion pipeline.

        Args:
            clean: If True, delete all artifacts before ingesting
        """
        start_time = datetime.now()

        secho("=" * 60, fg='blue')
        secho("Blackbox4 Brain v2.0 - Metadata Ingestion", fg='blue', bold=True)
        secho("=" * 60, fg='blue')

        # Initialize database
        await self.initialize_database()

        # Clean if requested
        if clean:
            secho("\nCleaning database...", fg='yellow')
            await execute_query("DELETE FROM relationships")
            await execute_query("DELETE FROM artifacts")
            secho("✓ Database cleaned", fg='green')

        # Find all metadata files
        metadata_files = await self.find_all_metadata()

        if not metadata_files:
            secho("\nNo metadata files found. Exiting.", fg='yellow')
            return

        # Parse all files
        parsed_data = await self.parse_metadata_files(metadata_files)

        if not parsed_data:
            secho("\nNo valid metadata files found. Exiting.", fg='yellow')
            return

        # Ingest artifacts
        secho(f"\nIngesting artifacts...", fg='blue')

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            transient=True,
        ) as progress:

            task = progress.add_task("Ingesting...", total=len(parsed_data))

            all_relationships = []

            for data in parsed_data:
                result = await self.ingest_artifact(data['artifact'])

                if result == 'inserted':
                    self.stats['inserted'] += 1
                elif result == 'updated':
                    self.stats['updated'] += 1
                else:
                    self.stats['failed'] += 1

                # Collect relationships
                all_relationships.extend(data['relationships'])

                progress.update(task, advance=1)

        # Ingest relationships
        if all_relationships:
            secho(f"\nIngesting {len(all_relationships)} relationships...", fg='blue')
            await self.ingest_relationships(all_relationships)
            secho(f"✓ Ingested {self.stats['relationships']} relationships", fg='green')

        # Print summary
        elapsed = (datetime.now() - start_time).total_seconds()

        secho("\n" + "=" * 60, fg='blue')
        secho("Ingestion Complete", fg='blue', bold=True)
        secho("=" * 60, fg='blue')
        secho(f"Scanned:     {self.stats['scanned']} files", fg='cyan')
        secho(f"Parsed:      {self.stats['parsed']} files", fg='cyan')
        secho(f"Inserted:    {self.stats['inserted']} artifacts", fg='green')
        secho(f"Updated:     {self.stats['updated']} artifacts", fg='yellow')
        secho(f"Deleted:     {self.stats['deleted']} artifacts", fg='red')
        secho(f"Failed:      {self.stats['failed']} artifacts", fg='red')
        secho(f"Relationships: {self.stats['relationships']} relationships", fg='cyan')
        secho(f"Time:        {elapsed:.2f}s", fg='cyan')
        secho("=" * 60, fg='blue')

        # Close database
        await Database.close()


# CLI Interface
@command()
@option('--directory', '-d', default=None, help='Root directory to scan')
@option('--clean', '-c', is_flag=True, help='Clean database before ingesting')
def ingest(directory: Optional[str], clean: bool):
    """Ingest metadata files into PostgreSQL."""
    async def run():
        ingester = MetadataIngester(directory)
        await ingester.run(clean=clean)

    asyncio.run(run())


if __name__ == '__main__':
    ingest()
