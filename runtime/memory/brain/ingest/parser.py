"""
Blackbox4 Brain v2.0 - Metadata Parser
Parse metadata.yaml files and extract artifact information.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime


class MetadataParser:
    """Parse metadata.yaml files."""

    REQUIRED_FIELDS = [
        'id', 'type', 'name', 'category', 'path',
        'created', 'modified', 'description', 'tags',
        'status', 'stability', 'owner'
    ]

    def __init__(self, metadata_path: str):
        """Initialize parser.

        Args:
            metadata_path: Path to metadata.yaml file
        """
        self.metadata_path = Path(metadata_path)
        self.metadata: Optional[Dict[str, Any]] = None
        self.errors: List[str] = []

    def load(self) -> bool:
        """Load metadata from file.

        Returns:
            True if successful, False otherwise
        """
        if not self.metadata_path.exists():
            self.errors.append(f"File not found: {self.metadata_path}")
            return False

        try:
            with open(self.metadata_path, 'r') as f:
                self.metadata = yaml.safe_load(f)

            if not self.metadata:
                self.errors.append("Empty metadata file")
                return False

            return True

        except yaml.YAMLError as e:
            self.errors.append(f"YAML parsing error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading file: {e}")
            return False

    def validate(self) -> bool:
        """Validate metadata has required fields.

        Returns:
            True if valid, False otherwise
        """
        if not self.metadata:
            self.errors.append("No metadata loaded")
            return False

        # Check required fields
        missing = [field for field in self.REQUIRED_FIELDS
                   if field not in self.metadata or not self.metadata[field]]

        if missing:
            self.errors.append(f"Missing required fields: {', '.join(missing)}")
            return False

        # Validate dates
        try:
            datetime.strptime(self.metadata['created'], '%Y-%m-%d')
            datetime.strptime(self.metadata['modified'], '%Y-%m-%d')
        except ValueError as e:
            self.errors.append(f"Invalid date format: {e}")
            return False

        return True

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert metadata to database dictionary.

        Returns:
            Dictionary ready for database insertion
        """
        if not self.metadata:
            raise ValueError("No metadata loaded")

        m = self.metadata

        # Build database record
        record = {
            'id': m['id'],
            'type': m['type'],
            'category': m.get('category'),
            'name': m['name'],
            'version': m.get('version'),
            'path': m['path'],
            'created': m['created'],
            'modified': m['modified'],
            'description': m.get('description', ''),
            'tags': m.get('tags', []),
            'keywords': m.get('keywords', []),
            'phase': m.get('phase'),
            'layer': m.get('layer'),
            'status': m['status'],
            'stability': m['stability'],
            'owner': m['owner'],
            'maintainer': m.get('maintainer'),
            'usage_count': m.get('usage_count', 0),
            'last_used': m.get('last_used'),
            'success_rate': m.get('success_rate'),
        }

        return record

    def get_relationships(self) -> List[Dict[str, Any]]:
        """Extract relationships from metadata.

        Returns:
            List of relationship dictionaries
        """
        if not self.metadata:
            raise ValueError("No metadata loaded")

        relationships = []
        artifact_id = self.metadata['id']

        # Process depends_on
        for dep in self.metadata.get('depends_on', []):
            relationships.append({
                'from_id': artifact_id,
                'to_id': dep['id'],
                'relationship_type': 'depends_on',
                'strength': dep.get('strength', 1.0),
                'metadata': dep
            })

        # Process used_by
        for usage in self.metadata.get('used_by', []):
            relationships.append({
                'from_id': usage['id'],
                'to_id': artifact_id,
                'relationship_type': 'depends_on',
                'strength': usage.get('strength', 1.0),
                'metadata': usage
            })

        # Process relates_to
        for rel in self.metadata.get('relates_to', []):
            relationships.append({
                'from_id': artifact_id,
                'to_id': rel['id'],
                'relationship_type': rel.get('relationship', 'relates_to'),
                'strength': rel.get('strength', 1.0),
                'metadata': rel
            })

        return relationships

    def get_documentation_links(self) -> Dict[str, str]:
        """Extract documentation links.

        Returns:
            Dictionary of doc types to paths
        """
        if not self.metadata:
            raise ValueError("No metadata loaded")

        return self.metadata.get('docs', {})


def parse_metadata_file(metadata_path: str) -> Optional[Dict[str, Any]]:
    """Parse a metadata file and return database record.

    Args:
        metadata_path: Path to metadata.yaml

    Returns:
        Dictionary with 'artifact' and 'relationships' keys, or None if invalid
    """
    parser = MetadataParser(metadata_path)

    if not parser.load():
        print(f"✗ Failed to load {metadata_path}: {parser.errors}")
        return None

    if not parser.validate():
        print(f"✗ Invalid metadata in {metadata_path}: {parser.errors}")
        return None

    return {
        'artifact': parser.to_db_dict(),
        'relationships': parser.get_relationships(),
        'docs': parser.get_documentation_links(),
        'metadata_path': str(parser.metadata_path)
    }


def find_metadata_files(root_dir: str, pattern: str = 'metadata.yaml') -> List[str]:
    """Find all metadata files in directory tree.

    Args:
        root_dir: Root directory to search
        pattern: File pattern (default: metadata.yaml)

    Returns:
        List of metadata file paths
    """
    metadata_files = []
    root = Path(root_dir)

    if not root.exists():
        return metadata_files

    for file_path in root.rglob(pattern):
        if file_path.is_file():
            metadata_files.append(str(file_path))

    return sorted(metadata_files)
