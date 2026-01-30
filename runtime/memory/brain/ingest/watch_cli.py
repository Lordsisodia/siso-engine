"""
Blackbox4 Brain v2.0 - File Watcher CLI
Command-line interface for the file watcher.
"""

import sys
import asyncio
import click
from click import secho, option, argument

from .watcher import FileWatcher


@click.command()
@option('--directories', '-d', multiple=True, help='Directories to watch (can be specified multiple times)')
@option('--debounce', '-b', default=2, type=int, help='Debounce time in seconds (default: 2)')
@option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def watch(directories, debounce, verbose):
    """Watch for metadata file changes and auto-update PostgreSQL."""
    watcher = FileWatcher(
        watch_directories=list(directories) if directories else None,
        debounce_seconds=debounce,
        verbose=verbose
    )

    # Initialize database
    asyncio.run(watcher.initialize_database())

    # Start watching
    watcher.start()


if __name__ == '__main__':
    watch()
