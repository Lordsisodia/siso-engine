#!/usr/bin/env python3
"""
Blackbox4 Brain v2.0 - Metadata Validator
==========================================

Validates metadata.yaml files against the Blackbox4 metadata schema.

Usage:
    python validator.py path/to/metadata.yaml
    python validator.py --directory 1-agents/
    python validator.py --schema

Author: Blackbox4 Core Team
Version: 1.0.0
"""

import sys
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class MetadataValidator:
    """Validates metadata.yaml files against Blackbox4 schema."""

    # Schema definitions
    REQUIRED_FIELDS = {
        'id', 'type', 'name', 'category', 'path', 'created', 'modified',
        'description', 'tags', 'status', 'stability', 'owner'
    }

    OPTIONAL_FIELDS = {
        'version', 'keywords', 'depends_on', 'used_by', 'relates_to',
        'phase', 'layer', 'embedding_id', 'search_vector', 'maintainer',
        'docs', 'usage_count', 'last_used', 'success_rate'
    }

    VALID_TYPES = {
        'agent', 'skill', 'plan', 'library', 'script', 'template',
        'document', 'test', 'config', 'module', 'framework', 'tool',
        'workspace', 'example'
    }

    VALID_STATUSES = {
        'active', 'deprecated', 'archived', 'experimental', 'beta', 'development'
    }

    VALID_STABILITIES = {
        'high', 'medium', 'low'
    }

    VALID_LAYERS = {
        'intelligence', 'execution', 'testing', 'documentation',
        'system', 'planning', 'workspace'
    }

    TYPE_CATEGORIES = {
        'agent': ['core', 'bmad', 'research', 'specialist', 'enhanced'],
        'skill': ['core', 'mcp', 'workflow'],
        'plan': ['active', 'completed', 'archived'],
        'library': [
            'context-variables', 'hierarchical-tasks', 'task-breakdown',
            'spec-creation', 'ralph-runtime', 'circuit-breaker',
            'response-analyzer'
        ],
        'script': ['agents', 'planning', 'testing', 'integration', 'validation'],
        'template': ['documents', 'plans', 'code', 'specs'],
        'document': [
            'getting-started', 'architecture', 'components', 'frameworks',
            'workflows', 'reference'
        ],
        'test': ['unit', 'integration', 'phase', 'e2e'],
        'module': ['context', 'planning', 'research', 'kanban'],
        'framework': ['bmad', 'speckit', 'metagpt', 'swarm'],
        'tool': ['maintenance', 'migration', 'validation'],
        'config': ['system', 'agent', 'memory', 'mcp'],
        'workspace': ['workspace', 'project', 'artifact'],
        'example': ['agent', 'library', 'skill', 'workflow'],
    }

    def __init__(self, strict: bool = False):
        """
        Initialize validator.

        Args:
            strict: If True, treat warnings as errors
        """
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, metadata_path: Path) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a metadata.yaml file.

        Args:
            metadata_path: Path to metadata.yaml file

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Check file exists
        if not metadata_path.exists():
            self.errors.append(f"File not found: {metadata_path}")
            return False, self.errors, self.warnings

        # Load YAML
        try:
            import yaml
            with open(metadata_path, 'r') as f:
                metadata = yaml.safe_load(f)
        except ImportError:
            self.errors.append("PyYAML not installed. Install with: pip install pyyaml")
            return False, self.errors, self.warnings
        except Exception as e:
            self.errors.append(f"Failed to load YAML: {e}")
            return False, self.errors, self.warnings

        if not isinstance(metadata, dict):
            self.errors.append("Metadata must be a dictionary/object")
            return False, self.errors, self.warnings

        # Validate structure
        self._validate_structure(metadata)
        self._validate_fields(metadata)
        self._validate_relationships(metadata)
        self._validate_dates(metadata)
        self._validate_metrics(metadata)

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_structure(self, metadata: Dict[str, Any]) -> None:
        """Validate overall structure."""
        # Check for unknown fields
        all_valid_fields = self.REQUIRED_FIELDS | self.OPTIONAL_FIELDS
        for field in metadata.keys():
            if field not in all_valid_fields:
                self.warnings.append(f"Unknown field: {field}")

        # Check required fields
        missing_fields = self.REQUIRED_FIELDS - set(metadata.keys())
        if missing_fields:
            self.errors.append(f"Missing required fields: {', '.join(missing_fields)}")

    def _validate_fields(self, metadata: Dict[str, Any]) -> None:
        """Validate individual fields."""
        # Validate ID
        if 'id' in metadata:
            self._validate_id(metadata['id'])

        # Validate type
        if 'type' in metadata:
            self._validate_type(metadata['type'])

        # Validate category matches type
        if 'type' in metadata and 'category' in metadata:
            self._validate_category(metadata['type'], metadata['category'])

        # Validate status
        if 'status' in metadata:
            self._validate_status(metadata['status'])

        # Validate stability
        if 'stability' in metadata:
            self._validate_stability(metadata['stability'])

        # Validate layer
        if 'layer' in metadata:
            self._validate_layer(metadata['layer'])

        # Validate phase
        if 'phase' in metadata:
            self._validate_phase(metadata['phase'])

        # Validate tags
        if 'tags' in metadata:
            self._validate_tags(metadata['tags'])

        # Validate version
        if 'version' in metadata:
            self._validate_version(metadata['version'])

        # Validate path
        if 'path' in metadata:
            self._validate_path(metadata['path'])

    def _validate_relationships(self, metadata: Dict[str, Any]) -> None:
        """Validate relationship fields."""
        # Validate depends_on
        if 'depends_on' in metadata:
            deps = metadata['depends_on']
            if not isinstance(deps, list):
                self.errors.append("depends_on must be a list")
            else:
                for i, dep in enumerate(deps):
                    if not isinstance(dep, dict):
                        self.errors.append(f"depends_on[{i}] must be an object")
                    else:
                        if 'id' not in dep:
                            self.errors.append(f"depends_on[{i}] missing required field: id")
                        if 'type' not in dep:
                            self.warnings.append(f"depends_on[{i}] missing recommended field: type")

        # Validate used_by
        if 'used_by' in metadata:
            used = metadata['used_by']
            if not isinstance(used, list):
                self.errors.append("used_by must be a list")
            else:
                for i, use in enumerate(used):
                    if not isinstance(use, dict):
                        self.errors.append(f"used_by[{i}] must be an object")
                    else:
                        if 'id' not in use:
                            self.errors.append(f"used_by[{i}] missing required field: id")
                        if 'type' not in use:
                            self.warnings.append(f"used_by[{i}] missing recommended field: type")

        # Validate relates_to
        if 'relates_to' in metadata:
            rels = metadata['relates_to']
            if not isinstance(rels, list):
                self.errors.append("relates_to must be a list")
            else:
                valid_relationships = {
                    'implements', 'documents', 'tests', 'uses', 'parallel',
                    'extends', 'refines', 'deprecates'
                }
                for i, rel in enumerate(rels):
                    if not isinstance(rel, dict):
                        self.errors.append(f"relates_to[{i}] must be an object")
                    else:
                        if 'id' not in rel:
                            self.errors.append(f"relates_to[{i}] missing required field: id")
                        if 'relationship' in rel and rel['relationship'] not in valid_relationships:
                            self.errors.append(
                                f"relates_to[{i}] has invalid relationship: {rel['relationship']}"
                            )

    def _validate_dates(self, metadata: Dict[str, Any]) -> None:
        """Validate date fields."""
        if 'created' in metadata and 'modified' in metadata:
            try:
                created = datetime.strptime(metadata['created'], '%Y-%m-%d')
                modified = datetime.strptime(metadata['modified'], '%Y-%m-%d')

                if modified < created:
                    self.errors.append("modified date must be >= created date")
            except ValueError as e:
                self.errors.append(f"Invalid date format: {e}")

    def _validate_metrics(self, metadata: Dict[str, Any]) -> None:
        """Validate metric fields."""
        if 'usage_count' in metadata:
            if not isinstance(metadata['usage_count'], int):
                self.errors.append("usage_count must be an integer")
            elif metadata['usage_count'] < 0:
                self.errors.append("usage_count must be >= 0")

        if 'success_rate' in metadata:
            if not isinstance(metadata['success_rate'], (int, float)):
                self.errors.append("success_rate must be a number")
            elif not 0.0 <= metadata['success_rate'] <= 1.0:
                self.errors.append("success_rate must be between 0.0 and 1.0")

    def _validate_id(self, value: Any) -> None:
        """Validate ID field."""
        if not isinstance(value, str):
            self.errors.append("id must be a string")
        elif not re.match(r'^[a-z0-9-]+$', value):
            self.errors.append(
                "id must contain only lowercase letters, numbers, and hyphens"
            )

    def _validate_type(self, value: Any) -> None:
        """Validate type field."""
        if not isinstance(value, str):
            self.errors.append("type must be a string")
        elif value not in self.VALID_TYPES:
            self.errors.append(
                f"type must be one of: {', '.join(sorted(self.VALID_TYPES))}"
            )

    def _validate_category(self, type_value: str, category_value: Any) -> None:
        """Validate category matches type."""
        if not isinstance(category_value, str):
            self.errors.append("category must be a string")
            return

        if type_value not in self.TYPE_CATEGORIES:
            self.warnings.append(f"Unknown type: {type_value}, cannot validate category")
            return

        valid_categories = self.TYPE_CATEGORIES[type_value]
        if category_value not in valid_categories:
            self.errors.append(
                f"category '{category_value}' not valid for type '{type_value}'. "
                f"Valid categories: {', '.join(valid_categories)}"
            )

    def _validate_status(self, value: Any) -> None:
        """Validate status field."""
        if not isinstance(value, str):
            self.errors.append("status must be a string")
        elif value not in self.VALID_STATUSES:
            self.errors.append(
                f"status must be one of: {', '.join(sorted(self.VALID_STATUSES))}"
            )

    def _validate_stability(self, value: Any) -> None:
        """Validate stability field."""
        if not isinstance(value, str):
            self.errors.append("stability must be a string")
        elif value not in self.VALID_STABILITIES:
            self.errors.append(
                f"stability must be one of: {', '.join(sorted(self.VALID_STABILITIES))}"
            )

    def _validate_layer(self, value: Any) -> None:
        """Validate layer field."""
        if not isinstance(value, str):
            self.errors.append("layer must be a string")
        elif value not in self.VALID_LAYERS:
            self.errors.append(
                f"layer must be one of: {', '.join(sorted(self.VALID_LAYERS))}"
            )

    def _validate_phase(self, value: Any) -> None:
        """Validate phase field."""
        if not isinstance(value, int):
            self.errors.append("phase must be an integer")
        elif not 1 <= value <= 4:
            self.errors.append("phase must be between 1 and 4")

    def _validate_tags(self, value: Any) -> None:
        """Validate tags field."""
        if not isinstance(value, list):
            self.errors.append("tags must be a list")
        elif len(value) == 0:
            self.errors.append("tags must contain at least one tag")
        else:
            for i, tag in enumerate(value):
                if not isinstance(tag, str):
                    self.errors.append(f"tags[{i}] must be a string")

    def _validate_version(self, value: Any) -> None:
        """Validate version field."""
        if not isinstance(value, str):
            self.errors.append("version must be a string")
        elif not re.match(r'^\d+\.\d+\.\d+$', value):
            self.errors.append("version must be in semantic versioning format (e.g., 1.0.0)")

    def _validate_path(self, value: Any) -> None:
        """Validate path field."""
        if not isinstance(value, str):
            self.errors.append("path must be a string")
        elif not value.startswith(('1-agents/', '2-frameworks/', '3-modules/',
                                   '4-scripts/', '5-templates/', '6-tools/',
                                   '7-workspace/', '8-testing/', '.docs/',
                                   '.plans/', '.config/', '.memory/',
                                   '.runtime/', '9-brain/')):
            self.warnings.append(
                f"path '{value}' doesn't match expected Blackbox4 directory structure"
            )


def print_results(
    is_valid: bool,
    errors: List[str],
    warnings: List[str],
    path: Path
) -> None:
    """Print validation results."""
    print(f"\n{'='*60}")
    print(f"Validating: {path}")
    print(f"{'='*60}")

    if is_valid:
        print("✓ VALID")
    else:
        print("✗ INVALID")

    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  • {error}")

    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  • {warning}")

    if is_valid and not warnings:
        print("\n✓ All checks passed!")

    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate Blackbox4 metadata.yaml files'
    )
    parser.add_argument(
        'path',
        type=Path,
        nargs='?',
        help='Path to metadata.yaml file or directory'
    )
    parser.add_argument(
        '--directory', '-d',
        type=Path,
        help='Validate all metadata.yaml files in directory'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Treat warnings as errors'
    )
    parser.add_argument(
        '--schema',
        action='store_true',
        help='Print schema information and exit'
    )

    args = parser.parse_args()

    validator = MetadataValidator(strict=args.strict)

    # Print schema info
    if args.schema:
        print("Blackbox4 Metadata Schema v1.0.0")
        print("\nValid types:")
        for t in sorted(validator.VALID_TYPES):
            print(f"  - {t}")
        print("\nValid statuses:")
        for s in sorted(validator.VALID_STATUSES):
            print(f"  - {s}")
        print("\nValid stabilities:")
        for s in sorted(validator.VALID_STABILITIES):
            print(f"  - {s}")
        print("\nValid layers:")
        for l in sorted(validator.VALID_LAYERS):
            print(f"  - {l}")
        print("\nType-specific categories:")
        for type_name, categories in sorted(validator.TYPE_CATEGORIES.items()):
            print(f"  {type_name}: {', '.join(categories)}")
        return 0

    # Validate single file
    if args.path:
        is_valid, errors, warnings = validator.validate(args.path)
        print_results(is_valid, errors, warnings, args.path)
        return 0 if is_valid else 1

    # Validate directory
    if args.directory:
        if not args.directory.exists():
            print(f"Error: Directory not found: {args.directory}", file=sys.stderr)
            return 1

        # Find both metadata.yaml and *-metadata.yaml files
        metadata_files = list(args.directory.rglob('metadata.yaml')) + \
                        list(args.directory.rglob('*-metadata.yaml'))
        if not metadata_files:
            print(f"No metadata files found in: {args.directory}")
            return 0

        all_valid = True
        for metadata_file in metadata_files:
            is_valid, errors, warnings = validator.validate(metadata_file)
            print_results(is_valid, errors, warnings, metadata_file)
            if not is_valid:
                all_valid = False

        print(f"\n{'='*60}")
        print(f"Total: {len(metadata_files)} files")
        print(f"Valid: {sum(1 for f in metadata_files if validator.validate(f)[0])}")
        print(f"Invalid: {sum(1 for f in metadata_files if not validator.validate(f)[0])}")
        print(f"{'='*60}\n")

        return 0 if all_valid else 1

    # No arguments
    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
