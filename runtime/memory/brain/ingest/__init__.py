"""
Blackbox4 Brain v2.0 - Ingestion Pipeline
Parse and ingest metadata into PostgreSQL.
"""

from .parser import parse_metadata_file, find_metadata_files
from .ingester import MetadataIngester
from .watcher import FileWatcher

__all__ = [
    'parse_metadata_file',
    'find_metadata_files',
    'MetadataIngester',
    'FileWatcher',
]
