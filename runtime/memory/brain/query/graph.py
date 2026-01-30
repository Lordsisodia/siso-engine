#!/usr/bin/env python3
"""
Blackbox4 Brain - Graph Query Interface
Provides high-level query methods for Neo4j graph database

Usage:
    from query.graph import GraphQuery

    graph = GraphQuery()
    result = graph.get_dependencies('orchestrator-agent-v1')
    impact = graph.get_impact_analysis('context-variables-lib')
    path = graph.get_shortest_path('agent-a', 'agent-b')
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Try to import neo4j driver
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

logger = logging.getLogger(__name__)


class GraphQuery:
    """High-level interface for querying the Blackbox4 graph database"""

    def __init__(self, uri: str = "bolt://localhost:7687",
                 user: str = "neo4j", password: str = "blackbox4brain"):
        if not NEO4J_AVAILABLE:
            raise ImportError("neo4j driver not installed. Install with: pip install neo4j")

        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None

    def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
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

    # =========================================================================
    # DEPENDENCY QUERIES
    # =========================================================================

    def get_dependencies(self, artifact_id: str, depth: int = 10) -> Dict[str, Any]:
        """
        Get all dependencies for an artifact

        Args:
            artifact_id: ID of the artifact
            depth: Maximum depth to traverse (default: 10)

        Returns:
            Dictionary with dependency tree
        """
        query = """
        MATCH path = (a:Artifact {id: $artifact_id})-[:DEPENDS_ON*1..%d]->(dep)
        RETURN a, dep, relationships(path) as rels, length(path) as depth
        ORDER BY depth, dep.name
        """ % depth

        results = self.execute_query(query, {'artifact_id': artifact_id})

        dependencies = []
        seen = set()

        for result in results:
            dep_node = result['dep']
            dep_id = dep_node['id']

            if dep_id not in seen:
                seen.add(dep_id)
                dependencies.append({
                    'id': dep_id,
                    'name': dep_node.get('name'),
                    'type': dep_node.get('type'),
                    'category': dep_node.get('category'),
                    'path': dep_node.get('path'),
                    'status': dep_node.get('status'),
                    'version': dep_node.get('version'),
                    'depth': result['depth']
                })

        return {
            'artifact_id': artifact_id,
            'total_dependencies': len(dependencies),
            'dependencies': dependencies
        }

    def get_dependents(self, artifact_id: str, depth: int = 10) -> Dict[str, Any]:
        """
        Get all artifacts that depend on this one (reverse dependencies)

        Args:
            artifact_id: ID of the artifact
            depth: Maximum depth to traverse (default: 10)

        Returns:
            Dictionary with dependent artifacts
        """
        query = """
        MATCH path = (dependent:Artifact)-[:DEPENDS_ON*1..%d]->(a:Artifact {id: $artifact_id})
        RETURN a, dependent, relationships(path) as rels, length(path) as depth
        ORDER BY depth, dependent.name
        """ % depth

        results = self.execute_query(query, {'artifact_id': artifact_id})

        dependents = []
        seen = set()

        for result in results:
            dep_node = result['dependent']
            dep_id = dep_node['id']

            if dep_id not in seen:
                seen.add(dep_id)
                dependents.append({
                    'id': dep_id,
                    'name': dep_node.get('name'),
                    'type': dep_node.get('type'),
                    'category': dep_node.get('category'),
                    'path': dep_node.get('path'),
                    'status': dep_node.get('status'),
                    'depth': result['depth']
                })

        return {
            'artifact_id': artifact_id,
            'total_dependents': len(dependents),
            'dependents': dependents
        }

    def get_impact_analysis(self, artifact_id: str) -> Dict[str, Any]:
        """
        Analyze impact if this artifact changes or breaks

        Args:
            artifact_id: ID of the artifact to analyze

        Returns:
            Dictionary with impact analysis
        """
        # Get direct dependents
        direct_query = """
        MATCH (a:Artifact {id: $artifact_id})<-[:DEPENDS_ON]-(dependent)
        RETURN dependent
        ORDER BY dependent.name
        """

        direct_results = self.execute_query(direct_query, {'artifact_id': artifact_id})

        # Get all transitive dependents
        all_query = """
        MATCH (a:Artifact {id: $artifact_id})<-[:DEPENDS_ON*]-(dependent)
        RETURN count(DISTINCT dependent) as total_impacted
        """

        all_results = self.execute_query(all_query, {'artifact_id': artifact_id})

        # Get by type
        by_type_query = """
        MATCH (a:Artifact {id: $artifact_id})<-[:DEPENDS_ON*]-(dependent)
        RETURN dependent.type as type, count(DISTINCT dependent) as count
        ORDER BY count DESC
        """

        by_type_results = self.execute_query(by_type_query, {'artifact_id': artifact_id})

        # Get critical path (agents that depend on this)
        critical_query = """
        MATCH (a:Artifact {id: $artifact_id})<-[:DEPENDS_ON*]-(agent:Artifact {type: 'agent'})
        RETURN DISTINCT agent.id, agent.name, agent.status
        ORDER BY agent.name
        """

        critical_results = self.execute_query(critical_query, {'artifact_id': artifact_id})

        return {
            'artifact_id': artifact_id,
            'direct_impact': len(direct_results),
            'total_impacted': all_results[0]['total_impacted'] if all_results else 0,
            'impact_by_type': [
                {'type': r['type'], 'count': r['count']}
                for r in by_type_results
            ],
            'critical_agents': [
                {'id': r['agent.id'], 'name': r['agent.name'], 'status': r['agent.status']}
                for r in critical_results
            ],
            'severity': self._calculate_severity(direct_results, all_results)
        }

    def _calculate_severity(self, direct_results: List, all_results: List) -> str:
        """Calculate impact severity"""
        total_impacted = all_results[0]['total_impacted'] if all_results else 0

        if total_impacted == 0:
            return 'none'
        elif total_impacted <= 2:
            return 'low'
        elif total_impacted <= 10:
            return 'medium'
        else:
            return 'high'

    # =========================================================================
    # PATH QUERIES
    # =========================================================================

    def get_shortest_path(self, from_id: str, to_id: str,
                         relationship_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Find shortest path between two artifacts

        Args:
            from_id: Starting artifact ID
            to_id: Ending artifact ID
            relationship_types: List of relationship types to follow (default: all)

        Returns:
            Dictionary with path information
        """
        if relationship_types:
            rel_pattern = '|'.join(relationship_types)
            query = f"""
            MATCH path = shortestPath(
              (from:Artifact {{id: $from_id}})-[:{rel_pattern}*]-(to:Artifact {{id: $to_id}})
            )
            RETURN path, length(path) as length, [node in nodes(path) | {{
                id: node.id,
                name: node.name,
                type: node.type
            }}] as nodes
            """
        else:
            query = """
            MATCH path = shortestPath(
              (from:Artifact {id: $from_id})-[*]-(to:Artifact {id: $to_id})
            )
            RETURN path, length(path) as length, [node in nodes(path) | {
                id: node.id,
                name: node.name,
                type: node.type
            }] as nodes
            """

        results = self.execute_query(query, {'from_id': from_id, 'to_id': to_id})

        if not results:
            return {
                'from_id': from_id,
                'to_id': to_id,
                'path_found': False,
                'path': []
            }

        result = results[0]
        return {
            'from_id': from_id,
            'to_id': to_id,
            'path_found': True,
            'length': result['length'],
            'nodes': result['nodes']
        }

    def get_all_paths(self, from_id: str, to_id: str,
                      max_length: int = 5) -> Dict[str, Any]:
        """
        Find all paths between two artifacts up to max_length

        Args:
            from_id: Starting artifact ID
            to_id: Ending artifact ID
            max_length: Maximum path length

        Returns:
            Dictionary with all paths
        """
        query = """
        MATCH path = (from:Artifact {id: $from_id})-[*1..%d]-(to:Artifact {id: $to_id})
        RETURN [node in nodes(path) | {
          id: node.id,
          name: node.name,
          type: node.type
        }] as nodes, length(path) as length
        ORDER BY length
        """ % max_length

        results = self.execute_query(query, {'from_id': from_id, 'to_id': to_id})

        return {
            'from_id': from_id,
            'to_id': to_id,
            'total_paths': len(results),
            'paths': [r['nodes'] for r in results]
        }

    # =========================================================================
    # ORPHAN AND CIRCULAR DEPENDENCY QUERIES
    # =========================================================================

    def find_orphans(self) -> List[Dict[str, Any]]:
        """
        Find all orphaned artifacts (no relationships)

        Returns:
            List of orphaned artifacts
        """
        query = """
        MATCH (a:Artifact)
        WHERE NOT (a)-[:DEPENDS_ON|USED_BY|RELATES_TO]-()
        RETURN a
        ORDER BY a.type, a.name
        """

        results = self.execute_query(query)

        return [
            {
                'id': r['a']['id'],
                'name': r['a'].get('name'),
                'type': r['a'].get('type'),
                'category': r['a'].get('category'),
                'path': r['a'].get('path'),
                'status': r['a'].get('status')
            }
            for r in results
        ]

    def find_circular_dependencies(self) -> List[Dict[str, Any]]:
        """
        Find all circular dependencies in the graph

        Returns:
            List of circular dependency cycles
        """
        query = """
        MATCH (a:Artifact)-[:DEPENDS_ON*1..]->(a)
        WHERE size([n in nodes(a) WHERE n.id = a.id]) > 1
        WITH DISTINCT [node in nodes(a) | {
          id: node.id,
          name: node.name,
          type: node.type
        }] as cycle
        RETURN cycle
        ORDER BY size(cycle)
        """

        results = self.execute_query(query)

        return [
            {
                'cycle_length': len(r['cycle']),
                'artifacts': r['cycle']
            }
            for r in results
        ]

    def find_unused_artifacts(self) -> List[Dict[str, Any]]:
        """
        Find artifacts that are not used by anything

        Returns:
            List of unused artifacts
        """
        query = """
        MATCH (a:Artifact)
        WHERE NOT (a)<-[:USED_BY|DEPENDS_ON]-()
        RETURN a
        ORDER BY a.type, a.name
        """

        results = self.execute_query(query)

        return [
            {
                'id': r['a']['id'],
                'name': r['a'].get('name'),
                'type': r['a'].get('type'),
                'category': r['a'].get('category'),
                'status': r['a'].get('status')
            }
            for r in results
        ]

    # =========================================================================
    # RELATIONSHIP QUERIES
    # =========================================================================

    def get_relationships(self, artifact_id: str) -> Dict[str, Any]:
        """
        Get all relationships for an artifact

        Args:
            artifact_id: ID of the artifact

        Returns:
            Dictionary with all relationships
        """
        query = """
        MATCH (a:Artifact {id: $artifact_id})-[r]-(other:Artifact)
        RETURN type(r) as relationship_type,
               startNode(r).id as from_id,
               endNode(r).id as to_id,
               other.id as other_id,
               other.name as other_name,
               other.type as other_type,
               properties(r) as properties
        ORDER BY relationship_type, other_name
        """

        results = self.execute_query(query, {'artifact_id': artifact_id})

        relationships = {
            'outgoing': [],
            'incoming': [],
            'bidirectional': []
        }

        for r in results:
            rel_info = {
                'type': r['relationship_type'],
                'artifact': {
                    'id': r['other_id'],
                    'name': r['other_name'],
                    'type': r['other_type']
                },
                'properties': r['properties']
            }

            if r['from_id'] == artifact_id and r['to_id'] != artifact_id:
                relationships['outgoing'].append(rel_info)
            elif r['to_id'] == artifact_id and r['from_id'] != artifact_id:
                relationships['incoming'].append(rel_info)

        return {
            'artifact_id': artifact_id,
            'total_relationships': len(results),
            'relationships': relationships
        }

    # =========================================================================
    # SEARCH AND DISCOVERY QUERIES
    # =========================================================================

    def search_by_type(self, artifact_type: str) -> List[Dict[str, Any]]:
        """Search artifacts by type"""
        query = """
        MATCH (a:Artifact {type: $type})
        RETURN a
        ORDER BY a.name
        """

        results = self.execute_query(query, {'type': artifact_type})

        return [
            {
                'id': r['a']['id'],
                'name': r['a'].get('name'),
                'type': r['a'].get('type'),
                'category': r['a'].get('category'),
                'status': r['a'].get('status'),
                'description': r['a'].get('description')
            }
            for r in results
        ]

    def search_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Search artifacts by tag"""
        query = """
        MATCH (a:Artifact)
        WHERE $tag IN a.tags
        RETURN a
        ORDER BY a.name
        """

        results = self.execute_query(query, {'tag': tag})

        return [
            {
                'id': r['a']['id'],
                'name': r['a'].get('name'),
                'type': r['a'].get('type'),
                'tags': r['a'].get('tags'),
                'status': r['a'].get('status')
            }
            for r in results
        ]

    def search_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Search artifacts by status"""
        query = """
        MATCH (a:Artifact {status: $status})
        RETURN a
        ORDER BY a.type, a.name
        """

        results = self.execute_query(query, {'status': status})

        return [
            {
                'id': r['a']['id'],
                'name': r['a'].get('name'),
                'type': r['a'].get('type'),
                'category': r['a'].get('category'),
                'stability': r['a'].get('stability')
            }
            for r in results
        ]

    # =========================================================================
    # UTILITY QUERIES
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall graph statistics"""
        queries = {
            'total_artifacts': 'MATCH (a:Artifact) RETURN count(a) as count',
            'by_type': '''
                MATCH (a:Artifact)
                RETURN a.type as type, count(a) as count
                ORDER BY count DESC
            ''',
            'by_status': '''
                MATCH (a:Artifact)
                RETURN a.status as status, count(a) as count
                ORDER BY count DESC
            ''',
            'total_relationships': '''
                MATCH ()-[r]->()
                RETURN count(r) as count
            ''',
            'by_relationship_type': '''
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            '''
        }

        stats = {}

        # Total artifacts
        results = self.execute_query(queries['total_artifacts'])
        stats['total_artifacts'] = results[0]['count'] if results else 0

        # By type
        results = self.execute_query(queries['by_type'])
        stats['by_type'] = [
            {'type': r['type'], 'count': r['count']}
            for r in results
        ]

        # By status
        results = self.execute_query(queries['by_status'])
        stats['by_status'] = [
            {'status': r['status'], 'count': r['count']}
            for r in results
        ]

        # Total relationships
        results = self.execute_query(queries['total_relationships'])
        stats['total_relationships'] = results[0]['count'] if results else 0

        # By relationship type
        results = self.execute_query(queries['by_relationship_type'])
        stats['by_relationship_type'] = [
            {'type': r['type'], 'count': r['count']}
            for r in results
        ]

        return stats

    def get_artifact_by_id(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get a single artifact by ID"""
        query = """
        MATCH (a:Artifact {id: $artifact_id})
        RETURN a
        """

        results = self.execute_query(query, {'artifact_id': artifact_id})

        if not results:
            return None

        node = results[0]['a']
        return {
            'id': node['id'],
            'type': node.get('type'),
            'name': node.get('name'),
            'category': node.get('category'),
            'version': node.get('version'),
            'path': node.get('path'),
            'created': node.get('created'),
            'modified': node.get('modified'),
            'description': node.get('description'),
            'tags': node.get('tags', []),
            'status': node.get('status'),
            'stability': node.get('stability'),
            'owner': node.get('owner'),
            'phase': node.get('phase'),
            'layer': node.get('layer')
        }

    def execute_cypher(self, query: str, params: Dict = None) -> List[Dict]:
        """
        Execute a custom Cypher query

        Args:
            query: Cypher query string
            params: Optional parameters

        Returns:
            Query results
        """
        return self.execute_query(query, params)


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Query Blackbox4 graph database')
    parser.add_argument('--uri', default='bolt://localhost:7687')
    parser.add_argument('--user', default='neo4j')
    parser.add_argument('--password', default='blackbox4brain')

    subparsers = parser.add_subparsers(dest='command', help='Query command')

    # Dependencies
    subparsers.add_parser('dependencies', help='Get dependencies').add_argument('id')
    subparsers.add_parser('dependents', help='Get dependents').add_argument('id')
    subparsers.add_parser('impact', help='Impact analysis').add_argument('id')

    # Paths
    path_parser = subparsers.add_parser('path', help='Find shortest path')
    path_parser.add_argument('from_id')
    path_parser.add_argument('to_id')

    # Orphans
    subparsers.add_parser('orphans', help='Find orphaned artifacts')
    subparsers.add_parser('circular', help='Find circular dependencies')
    subparsers.add_parser('unused', help='Find unused artifacts')

    # Search
    subparsers.add_parser('stats', help='Get statistics')

    # Custom Cypher
    cypher_parser = subparsers.add_parser('cypher', help='Execute custom Cypher')
    cypher_parser.add_argument('query')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Connect and query
    graph = GraphQuery(args.uri, args.user, args.password)
    if not graph.connect():
        print("ERROR: Failed to connect to Neo4j")
        return

    try:
        result = None

        if args.command == 'dependencies':
            result = graph.get_dependencies(args.id)
        elif args.command == 'dependents':
            result = graph.get_dependents(args.id)
        elif args.command == 'impact':
            result = graph.get_impact_analysis(args.id)
        elif args.command == 'path':
            result = graph.get_shortest_path(args.from_id, args.to_id)
        elif args.command == 'orphans':
            result = graph.find_orphans()
        elif args.command == 'circular':
            result = graph.find_circular_dependencies()
        elif args.command == 'unused':
            result = graph.find_unused_artifacts()
        elif args.command == 'stats':
            result = graph.get_statistics()
        elif args.command == 'cypher':
            result = graph.execute_cypher(args.query)

        print(json.dumps(result, indent=2, default=str))

    finally:
        graph.close()


if __name__ == '__main__':
    main()
