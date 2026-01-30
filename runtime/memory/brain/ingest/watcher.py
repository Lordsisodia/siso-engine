"""
Blackbox4 Brain v2.0 - File Watcher
Watch for metadata.yaml changes and auto-update PostgreSQL.
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from typing import Set, Dict, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileDeletedEvent
from click import secho, echo

from .db import Database
from .parser import parse_metadata_file


class MetadataFileHandler(FileSystemEventHandler):
    """Handle metadata file system events."""

    def __init__(self, ingester: 'FileWatcher'):
        """Initialize handler.

        Args:
            ingester: Parent FileWatcher instance
        """
        super().__init__()
        self.ingester = ingester
        self.pending_changes: Set[str] = set()
        self.debounce_seconds = ingester.debounce_seconds

    def on_created(self, event):
        """Handle file creation."""
        if event.is_directory:
            return

        if self._is_metadata_file(event.src_path):
            self._schedule_update(event.src_path, 'created')

    def on_modified(self, event):
        """Handle file modification."""
        if event.is_directory:
            return

        if self._is_metadata_file(event.src_path):
            self._schedule_update(event.src_path, 'modified')

    def on_deleted(self, event):
        """Handle file deletion."""
        if event.is_directory:
            return

        if self._is_metadata_file(event.src_path):
            self._schedule_update(event.src_path, 'deleted')

    def _is_metadata_file(self, path: str) -> bool:
        """Check if file is a metadata file.

        Args:
            path: File path

        Returns:
            True if metadata file
        """
        filename = os.path.basename(path)
        return filename == 'metadata.yaml' or filename.endswith('-metadata.yaml')

    def _schedule_update(self, path: str, event_type: str):
        """Schedule a file update.

        Args:
            path: File path
            event_type: Event type (created, modified, deleted)
        """
        self.pending_changes.add(path)
        echo(f"📄 {event_type}: {path}")

        if self.ingester.verbose:
            echo(f"  Pending changes: {len(self.pending_changes)} files")


class FileWatcher:
    """Watch for metadata file changes and update database."""

    def __init__(
        self,
        watch_directories: Optional[list] = None,
        debounce_seconds: int = 2,
        verbose: bool = False
    ):
        """Initialize file watcher.

        Args:
            watch_directories: List of directories to watch
            debounce_seconds: Seconds to wait before processing changes
            verbose: Enable verbose output
        """
        self.watch_directories = watch_directories or []
        self.debounce_seconds = debounce_seconds
        self.verbose = verbose
        self.observer = Observer()
        self.handler = MetadataFileHandler(self)
        self.running = False
        self.stats = {
            'processed': 0,
            'inserted': 0,
            'updated': 0,
            'deleted': 0,
            'failed': 0,
        }

    def _get_default_directories(self) -> list:
        """Get default directories to watch.

        Returns:
            List of directory paths
        """
        script_dir = Path(__file__).parent.parent.parent
        base_dirs = [
            '1-agents',
            '2-skills',
            '3-plans',
            '4-scripts',
            '5-libraries',
            '6-modules',
            '8-workspaces',
            '9-brain',
        ]

        watch_dirs = []
        for dir_name in base_dirs:
            dir_path = script_dir / dir_name
            if dir_path.exists():
                watch_dirs.append(str(dir_path))

        return watch_dirs

    async def initialize_database(self):
        """Initialize database connection."""
        try:
            await Database.initialize()
            secho("✓ Database connected", fg='green')
        except Exception as e:
            secho(f"✗ Failed to connect to database: {e}", fg='red')
            sys.exit(1)

    async def process_file(self, file_path: str) -> bool:
        """Process a single metadata file.

        Args:
            file_path: Path to metadata file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse metadata
            result = parse_metadata_file(file_path)

            if not result:
                # Invalid metadata, delete from database if exists
                await self._delete_by_path(file_path)
                return True

            artifact = result['artifact']

            # Check if artifact exists
            existing = await Database.execute(
                "SELECT id FROM artifacts WHERE path = $1",
                file_path,
                fetch='one'
            )

            if existing:
                # Update existing
                await self._update_artifact(artifact)
                await self._update_relationships(result['relationships'], artifact['id'])
                self.stats['updated'] += 1
            else:
                # Insert new
                await self._insert_artifact(artifact)
                await self._insert_relationships(result['relationships'], artifact['id'])
                self.stats['inserted'] += 1

            self.stats['processed'] += 1
            return True

        except Exception as e:
            echo(f"✗ Failed to process {file_path}: {e}")
            self.stats['failed'] += 1
            return False

    async def _insert_artifact(self, artifact: dict):
        """Insert artifact into database.

        Args:
            artifact: Artifact dictionary
        """
        await Database.execute("""
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

    async def _update_artifact(self, artifact: dict):
        """Update artifact in database.

        Args:
            artifact: Artifact dictionary
        """
        await Database.execute("""
            UPDATE artifacts SET
                type = $2, category = $3, name = $4, version = $5,
                created = $6, modified = $7, description = $8,
                tags = $9, keywords = $10, phase = $11, layer = $12,
                status = $13, stability = $14, owner = $15, maintainer = $16,
                usage_count = $17, last_used = $18, success_rate = $19
            WHERE id = $1
        """,
        artifact['id'],
        artifact['type'],
        artifact['category'],
        artifact['name'],
        artifact['version'],
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

    async def _delete_by_path(self, path: str):
        """Delete artifact by path.

        Args:
            path: File path
        """
        # Get artifact ID
        result = await Database.execute(
            "SELECT id FROM artifacts WHERE path = $1",
            path,
            fetch='one'
        )

        if result:
            artifact_id = result['id']
            await Database.execute("DELETE FROM relationships WHERE from_id = $1 OR to_id = $1", artifact_id)
            await Database.execute("DELETE FROM artifacts WHERE id = $1", artifact_id)
            self.stats['deleted'] += 1

    async def _insert_relationships(self, relationships: list, artifact_id: str):
        """Insert relationships for artifact.

        Args:
            relationships: List of relationship dictionaries
            artifact_id: Artifact ID
        """
        # Delete existing relationships
        await Database.execute(
            "DELETE FROM relationships WHERE from_id = $1",
            artifact_id
        )

        # Insert new relationships
        for rel in relationships:
            await Database.execute("""
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

    async def _update_relationships(self, relationships: list, artifact_id: str):
        """Update relationships for artifact.

        Args:
            relationships: List of relationship dictionaries
            artifact_id: Artifact ID
        """
        await self._insert_relationships(relationships, artifact_id)

    async def process_pending_changes(self):
        """Process all pending file changes."""
        if not self.handler.pending_changes:
            return

        changes = list(self.handler.pending_changes)
        self.handler.pending_changes.clear()

        echo(f"\n⚙️  Processing {len(changes)} file(s)...")

        for file_path in changes:
            await self.process_file(file_path)

        if self.verbose:
            echo(f"✓ Processed: {self.stats['processed']}, "
                 f"Inserted: {self.stats['inserted']}, "
                 f"Updated: {self.stats['updated']}, "
                 f"Deleted: {self.stats['deleted']}, "
                 f"Failed: {self.stats['failed']}")

    async def _debounce_loop(self):
        """Debounce loop to process changes in batches."""
        while self.running:
            await asyncio.sleep(self.debounce_seconds)
            await self.process_pending_changes()

    def start(self):
        """Start watching files."""
        if not self.watch_directories:
            self.watch_directories = self._get_default_directories()

        if not self.watch_directories:
            secho("✗ No directories to watch", fg='red')
            sys.exit(1)

        secho("🔍 Starting Blackbox4 Brain File Watcher", fg='blue')
        secho(f"   Watching {len(self.watch_directories)} directories", fg='cyan')

        for watch_dir in self.watch_directories:
            if os.path.exists(watch_dir):
                self.observer.schedule(self.handler, watch_dir, recursive=True)
                echo(f"   ✓ {watch_dir}")
            else:
                echo(f"   ✗ {watch_dir} (not found)")

        secho(f"   Debounce: {self.debounce_seconds}s", fg='cyan')
        secho("   Press Ctrl+C to stop\n", fg='yellow')

        self.observer.start()
        self.running = True

        # Run debounce loop
        try:
            asyncio.run(self._debounce_loop())
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop watching files."""
        secho("\n\n⏹️  Stopping file watcher...", fg='yellow')
        self.running = False
        self.observer.stop()
        self.observer.join()

        secho("📊 Final Statistics:", fg='cyan')
        secho(f"   Processed: {self.stats['processed']}", fg='cyan')
        secho(f"   Inserted:  {self.stats['inserted']}", fg='green')
        secho(f"   Updated:   {self.stats['updated']}", fg='yellow')
        secho(f"   Deleted:   {self.stats['deleted']}", fg='red')
        secho(f"   Failed:    {self.stats['failed']}", fg='red')

        asyncio.run(Database.close())
        secho("✓ File watcher stopped", fg='green')
