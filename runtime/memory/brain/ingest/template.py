#!/usr/bin/env python3
"""
Blackbox4 Brain v2.0 - Metadata Template Generator
====================================================

Interactive script to generate metadata.yaml templates for Blackbox4 artifacts.

Usage:
    python template.py
    python template.py --type agent --name "My Agent" --category specialist

Author: Blackbox4 Core Team
Version: 1.0.0
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional


TYPE_CATEGORIES = {
    'agent': ['core', 'bmad', 'research', 'specialist', 'enhanced'],
    'skill': ['core', 'mcp', 'workflow'],
    'library': [
        'context-variables', 'hierarchical-tasks', 'task-breakdown',
        'spec-creation', 'ralph-runtime', 'circuit-breaker', 'response-analyzer'
    ],
    'script': ['agents', 'planning', 'testing', 'integration', 'validation'],
    'template': ['documents', 'plans', 'code', 'specs'],
    'document': [
        'getting-started', 'architecture', 'components', 'frameworks',
        'workflows', 'reference'
    ],
    'test': ['unit', 'integration', 'phase', 'e2e'],
    'plan': ['active', 'completed', 'archived'],
    'config': ['system', 'agent', 'memory', 'mcp'],
    'module': ['context', 'planning', 'research', 'kanban'],
    'framework': ['bmad', 'speckit', 'metagpt', 'swarm'],
    'tool': ['maintenance', 'migration', 'validation'],
    'workspace': ['workspace', 'project', 'artifact'],
    'example': ['agent', 'library', 'skill', 'workflow'],
}

STATUS_VALUES = ['active', 'development', 'experimental', 'beta', 'deprecated', 'archived']
STABILITY_VALUES = ['high', 'medium', 'low']
LAYER_VALUES = ['intelligence', 'execution', 'testing', 'documentation', 'system', 'planning', 'workspace']

PATH_PATTERNS = {
    'agent': '1-agents/{category}/{name}.md',
    'skill': '1-agents/.skills/{category}/{name}.md',
    'library': '4-scripts/lib/{category}/',
    'script': '4-scripts/{category}/{name}.sh',
    'template': '5-templates/{category}/{name}',
    'document': '.docs/{category}/{name}.md',
    'test': '8-testing/{category}/{name}.py',
    'plan': '.plans/{category}/{date}_{name}/',
    'config': '.config/{name}.yaml',
    'module': '3-modules/{category}/',
    'framework': '2-frameworks/{category}/',
    'tool': '6-tools/{category}/{name}.sh',
    'workspace': '7-workspace/{category}/{name}/',
    'example': '1-agents/4-specialists/{name}-examples/',
}


class TemplateGenerator:
    """Generate metadata.yaml templates."""

    def __init__(self):
        self.today = datetime.now().strftime('%Y-%m-%d')

    def generate(
        self,
        artifact_type: str,
        name: str,
        category: str,
        description: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate metadata template.

        Args:
            artifact_type: Type of artifact
            name: Name of the artifact
            category: Category within type
            description: Description (if None, will use placeholder)
            **kwargs: Additional fields

        Returns:
            YAML template as string
        """
        # Generate ID
        id_base = name.lower().replace(' ', '-').replace('_', '-')
        artifact_id = kwargs.get('id', f"{id_base}-{artifact_type}")

        # Generate path
        path_pattern = PATH_PATTERNS.get(artifact_type, '{name}/')
        path = path_pattern.format(
            category=category,
            name=name.lower().replace(' ', '-'),
            date=self.today
        )

        # Build template
        lines = [
            f"# Metadata for {name}",
            f"# Type: {artifact_type}",
            f"# Category: {category}",
            f"# Generated: {self.today}",
            "",
            "id: " + artifact_id,
            f"type: \"{artifact_type}\"",
            f"name: \"{name}\"",
            f"category: \"{category}\"",
        ]

        # Optional version
        if kwargs.get('version'):
            lines.append(f"version: \"{kwargs['version']}")

        # Location
        lines.extend([
            "",
            "# Location",
            f"path: \"{path}\"",
            f"created: \"{self.today}\"",
            f"modified: \"{self.today}\"",
        ])

        # Content
        lines.extend([
            "",
            "# Content",
            "description: |",
        ])

        if description:
            lines.append(f"  {description}")
        else:
            lines.extend([
                f"  Brief description of what this {name} does.",
                "",
                "  Key capabilities:",
                "  - Capability 1",
                "  - Capability 2",
                "  - Capability 3",
            ])

        # Tags
        tags = kwargs.get('tags', [category])
        lines.extend([
            "",
            "tags:",
        ])
        for tag in tags:
            lines.append(f"  - \"{tag}\"")

        # Optional keywords
        if kwargs.get('keywords'):
            lines.extend([
                "",
                "keywords:",
            ])
            for keyword in kwargs['keywords']:
                lines.append(f"  - \"{keyword}\"")

        # Relationships (optional)
        if any(k in kwargs for k in ['depends_on', 'used_by', 'relates_to']):
            lines.extend([
                "",
                "# Relationships",
            ])

            if kwargs.get('depends_on'):
                lines.extend([
                    "depends_on:",
                ])
                for dep in kwargs['depends_on']:
                    if isinstance(dep, str):
                        lines.append(f"  - id: \"{dep}\"")
                        lines.append(f"    type: \"unknown\"")
                    elif isinstance(dep, dict):
                        lines.append(f"  - id: \"{dep['id']}\"")
                        lines.append(f"    type: \"{dep.get('type', 'unknown')}\"")
                        if 'version' in dep:
                            lines.append(f"    version: \"{dep['version']}\"")

            if kwargs.get('used_by'):
                lines.extend([
                    "used_by:",
                ])
                for use in kwargs['used_by']:
                    if isinstance(use, str):
                        lines.append(f"  - id: \"{use}\"")
                        lines.append(f"    type: \"unknown\"")
                    elif isinstance(use, dict):
                        lines.append(f"  - id: \"{use['id']}\"")
                        lines.append(f"    type: \"{use.get('type', 'unknown')}\"")

            if kwargs.get('relates_to'):
                lines.extend([
                    "relates_to:",
                ])
                for rel in kwargs['relates_to']:
                    if isinstance(rel, dict):
                        lines.append(f"  - id: \"{rel['id']}\"")
                        lines.append(f"    type: \"{rel.get('type', 'unknown')}\"")
                        lines.append(f"    relationship: \"{rel.get('relationship', 'uses')}\"")

        # Classification
        lines.extend([
            "",
            "# Classification",
        ])

        if kwargs.get('phase'):
            lines.append(f"phase: {kwargs['phase']}")

        layer = kwargs.get('layer', self._default_layer(artifact_type))
        lines.append(f"layer: \"{layer}\"")

        # Status
        status = kwargs.get('status', 'development')
        stability = kwargs.get('stability', 'medium')

        lines.extend([
            "",
            "# Status",
            f"status: \"{status}\"",
            f"stability: \"{stability}\"",
        ])

        # Ownership
        owner = kwargs.get('owner', 'core-team')
        maintainer = kwargs.get('maintainer')

        lines.extend([
            "",
            "# Ownership",
            f"owner: \"{owner}\"",
        ])

        if maintainer:
            lines.append(f"maintainer: \"{maintainer}\"")

        # Documentation
        if kwargs.get('docs'):
            lines.extend([
                "",
                "# Documentation",
                "docs:",
            ])
            docs = kwargs['docs']
            if isinstance(docs, dict):
                if docs.get('primary'):
                    lines.append(f"  primary: \"{docs['primary']}\"")
                if docs.get('examples'):
                    lines.append(f"  examples: \"{docs['examples']}\"")
                if docs.get('api'):
                    lines.append(f"  api: \"{docs['api']}\"")
                if docs.get('guide'):
                    lines.append(f"  guide: \"{docs['guide']}\"")

        # Metrics
        if kwargs.get('usage_count'):
            lines.extend([
                "",
                "# Metrics",
                f"usage_count: {kwargs['usage_count']}",
                f"last_used: \"{kwargs.get('last_used', self.today)}\"",
            ])

            if 'success_rate' in kwargs:
                lines.append(f"success_rate: {kwargs['success_rate']}")

        return '\n'.join(lines)

    def _default_layer(self, artifact_type: str) -> str:
        """Get default layer for artifact type."""
        layer_map = {
            'agent': 'intelligence',
            'skill': 'intelligence',
            'library': 'execution',
            'script': 'execution',
            'test': 'testing',
            'document': 'documentation',
            'config': 'system',
            'plan': 'planning',
            'workspace': 'workspace',
            'module': 'system',
            'framework': 'documentation',
            'tool': 'execution',
            'template': 'planning',
            'example': 'intelligence',
        }
        return layer_map.get(artifact_type, 'system')


def interactive_prompt() -> dict:
    """Interactive prompt for template generation."""
    print("Blackbox4 Metadata Template Generator")
    print("=" * 40)
    print()

    # Type
    print("Available types:")
    for i, t in enumerate(sorted(TYPE_CATEGORIES.keys()), 1):
        print(f"  {i}. {t}")
    print()

    while True:
        type_input = input("Artifact type: ").strip().lower()
        if type_input in TYPE_CATEGORIES:
            artifact_type = type_input
            break
        print(f"Invalid type. Choose from: {', '.join(sorted(TYPE_CATEGORIES.keys()))}")

    # Category
    print()
    print(f"Available categories for {artifact_type}:")
    categories = TYPE_CATEGORIES[artifact_type]
    for i, cat in enumerate(categories, 1):
        print(f"  {i}. {cat}")
    print()

    while True:
        cat_input = input("Category: ").strip().lower()
        if cat_input in categories:
            category = cat_input
            break
        print(f"Invalid category. Choose from: {', '.join(categories)}")

    # Name
    print()
    name = input("Artifact name: ").strip()
    if not name:
        print("Name is required!")
        return interactive_prompt()

    # Description
    print()
    description = input("Description (optional, press Enter to skip): ").strip() or None

    # Tags
    print()
    tags_input = input(f"Tags (comma-separated, default: {category}): ").strip()
    if tags_input:
        tags = [t.strip() for t in tags_input.split(',')]
    else:
        tags = [category]

    # Additional options
    print()
    print("Additional options (press Enter to use defaults):")

    status = input(f"Status [{STATUS_VALUES[1]}]: ").strip() or STATUS_VALUES[1]
    stability = input(f"Stability [{STABILITY_VALUES[1]}]: ").strip() or STABILITY_VALUES[1]

    layer = input(f"Layer (default: auto): ").strip() or None

    return {
        'type': artifact_type,
        'name': name,
        'category': category,
        'description': description,
        'tags': tags,
        'status': status if status in STATUS_VALUES else STATUS_VALUES[1],
        'stability': stability if stability in STABILITY_VALUES else STABILITY_VALUES[1],
        'layer': layer,
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate Blackbox4 metadata.yaml templates'
    )
    parser.add_argument(
        '--type', '-t',
        choices=list(TYPE_CATEGORIES.keys()),
        help='Artifact type'
    )
    parser.add_argument(
        '--name', '-n',
        help='Artifact name'
    )
    parser.add_argument(
        '--category', '-c',
        help='Artifact category'
    )
    parser.add_argument(
        '--description', '-d',
        help='Artifact description'
    )
    parser.add_argument(
        '--tags',
        help='Comma-separated tags'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output file (default: stdout)'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Interactive mode'
    )

    args = parser.parse_args()

    generator = TemplateGenerator()

    # Interactive mode
    if args.interactive:
        inputs = interactive_prompt()
        template = generator.generate(**inputs)
    else:
        # Command-line mode
        if not args.type or not args.name or not args.category:
            print("Error: --type, --name, and --category are required in non-interactive mode")
            print("Use --interactive for guided setup")
            return 1

        kwargs = {
            'artifact_type': args.type,
            'name': args.name,
            'category': args.category,
            'description': args.description,
        }

        if args.tags:
            kwargs['tags'] = [t.strip() for t in args.tags.split(',')]

        template = generator.generate(**kwargs)

    # Output
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            f.write(template)
        print(f"Template written to: {args.output}")
    else:
        print(template)

    return 0


if __name__ == '__main__':
    sys.exit(main())
