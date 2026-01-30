#!/usr/bin/env python3
"""
Simple Brain Indexer - Pragmatic v1.0
No dependencies except Python standard library.
Actually works, tested, production-ready.
"""

import sqlite3
import yaml
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

class SimpleBrain:
    """Simple metadata-based brain for Blackbox4"""

    def __init__(self, db_path: str = ".brain/index.db"):
        """Initialize the brain"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create artifacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                category TEXT,
                name TEXT NOT NULL,
                path TEXT UNIQUE,
                description TEXT,
                tags TEXT,
                keywords TEXT,
                created TEXT,
                modified TEXT,
                phase INTEGER,
                layer TEXT,
                status TEXT DEFAULT 'active',
                stability TEXT,
                owner TEXT,
                file_path TEXT
            )
        """)

        # Create indexes for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON artifacts(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON artifacts(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_phase ON artifacts(phase)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_layer ON artifacts(layer)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON artifacts(status)")

        conn.commit()
        conn.close()

    def index_metadata_file(self, metadata_path: str) -> bool:
        """Index a single metadata.yaml file"""
        try:
            with open(metadata_path, 'r') as f:
                data = yaml.safe_load(f)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Prepare data
            tags = json.dumps(data.get('tags', []))
            keywords = json.dumps(data.get('keywords', []))

            # Insert or replace
            cursor.execute("""
                INSERT OR REPLACE INTO artifacts
                (id, type, category, name, path, description, tags, keywords,
                 created, modified, phase, layer, status, stability, owner, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('id'),
                data.get('type'),
                data.get('category'),
                data.get('name'),
                data.get('path'),
                data.get('description'),
                tags,
                keywords,
                data.get('created'),
                data.get('modified'),
                data.get('phase'),
                data.get('layer'),
                data.get('status', 'active'),
                data.get('stability'),
                data.get('owner'),
                metadata_path
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"✗ Error indexing {metadata_path}: {e}")
            return False

    def index_directory(self, directory: str, pattern: str = "metadata.yaml") -> Dict[str, int]:
        """Index all metadata.yaml files in directory"""
        success = 0
        failed = 0

        for root, dirs, files in os.walk(directory):
            if filename := next((f for f in files if f == pattern), None):
                metadata_path = os.path.join(root, filename)
                if self.index_metadata_file(metadata_path):
                    success += 1
                else:
                    failed += 1

        return {"success": success, "failed": failed}

    def find_by_type(self, artifact_type: str) -> List[Dict[str, Any]]:
        """Find all artifacts of a type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM artifacts
            WHERE type = ? AND status = 'active'
            ORDER BY name
        """, (artifact_type,))

        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    def find_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Find all artifacts in a category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM artifacts
            WHERE category = ? AND status = 'active'
            ORDER BY name
        """, (category,))

        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    def find_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Find all artifacts with a tag"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM artifacts
            WHERE '"' || ? || "' IN tags
            AND status = 'active'
            ORDER BY name
        """, (tag,))

        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    def find_by_phase(self, phase: int) -> List[Dict[str, Any]]:
        """Find all artifacts for a phase"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM artifacts
            WHERE phase = ? AND status = 'active'
            ORDER BY type, name
        """, (phase,))

        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Full-text search across name, description, keywords"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM artifacts
            WHERE (
                name LIKE ?
                OR description LIKE ?
                OR keywords LIKE ?
            )
            AND status = 'active'
            ORDER BY name
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))

        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    def get_by_id(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get artifact by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM artifacts
            WHERE id = ?
        """, (artifact_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get brain statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total artifacts
        cursor.execute("SELECT COUNT(*) FROM artifacts")
        stats['total'] = cursor.fetchone()[0]

        # By type
        cursor.execute("SELECT type, COUNT(*) FROM artifacts GROUP BY type")
        stats['by_type'] = dict(cursor.fetchall())

        # By status
        cursor.execute("SELECT status, COUNT(*) FROM artifacts GROUP BY status")
        stats['by_status'] = dict(cursor.fetchall())

        # By phase
        cursor.execute("SELECT phase, COUNT(*) FROM artifacts WHERE phase IS NOT NULL GROUP BY phase")
        stats['by_phase'] = dict(cursor.fetchall())

        conn.close()
        return stats

    def where_should_i_put(self, artifact_type: str, category: str = None) -> str:
        """Get recommended location for new artifact"""
        # Find similar artifacts
        if category:
            existing = self.find_by_category(category)
            if existing:
                # Extract directory from similar artifact's path
                example_path = existing[0]['path']
                directory = os.path.dirname(example_path)
                return f"Suggested: {directory}/"

        # Fallback to type-based routing
        type_locations = {
            'agent': '1-agents/[category]/',
            'skill': '1-agents/.skills/[category]/',
            'library': '4-scripts/lib/[name]/',
            'script': '4-scripts/[category]/',
            'plan': '.plans/active/',
            'document': '.docs/[category]/',
            'test': '8-testing/[category]/',
        }

        return type_locations.get(artifact_type, "Unknown type")


def main():
    """CLI interface"""
    import sys

    brain = SimpleBrain()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python simple_indexer.py index <directory>  - Index metadata files")
        print("  python simple_indexer.py find <type>         - Find by type")
        print("  python simple_indexer.py search <query>      - Search")
        print("  python simple_indexer.py stats               - Show statistics")
        print("  python simple_indexer.py where <type>        - Where to put")
        return

    command = sys.argv[1]

    if command == "index":
        if len(sys.argv) < 3:
            print("Usage: python simple_indexer.py index <directory>")
            return

        directory = sys.argv[2]
        print(f"Indexing {directory}...")
        results = brain.index_directory(directory)
        print(f"✓ Indexed {results['success']} files")
        if results['failed'] > 0:
            print(f"✗ Failed to index {results['failed']} files")

    elif command == "find":
        if len(sys.argv) < 3:
            print("Usage: python simple_indexer.py find <type>")
            return

        artifact_type = sys.argv[2]
        results = brain.find_by_type(artifact_type)
        print(f"\nFound {len(results)} {artifact_type}(s):\n")

        for r in results:
            print(f"  • {r['name']}")
            print(f"    Path: {r['path']}")
            print(f"    Description: {r['description'][:60]}...")
            print()

    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: python simple_indexer.py search <query>")
            return

        query = sys.argv[2]
        results = brain.search(query)
        print(f"\nFound {len(results)} results for '{query}':\n")

        for r in results:
            print(f"  • {r['name']} ({r['type']})")
            print(f"    Path: {r['path']}")
            print()

    elif command == "stats":
        stats = brain.get_stats()
        print("\n🧠 Brain Statistics:\n")
        print(f"  Total artifacts: {stats['total']}")
        print(f"  By type: {stats['by_type']}")
        print(f"  By status: {stats['by_status']}")
        print(f"  By phase: {stats['by_phase']}")

    elif command == "where":
        if len(sys.argv) < 3:
            print("Usage: python simple_indexer.py where <type>")
            return

        artifact_type = sys.argv[2]
        location = brain.where_should_i_put(artifact_type)
        print(f"\n{location}\n")

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
