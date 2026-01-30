#!/usr/bin/env python3
"""
Blackbox4 Brain v2.0 - Natural Language Query Parser
Parse natural language queries and route to appropriate database.

Version: 1.0.0
Last Updated: 2026-01-15
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Detected query intent."""
    PLACEMENT = "placement"           # "Where should I put X?"
    DISCOVERY = "discovery"           # "Find all X"
    RELATIONSHIP = "relationship"     # "What depends on X?"
    SEMANTIC = "semantic"             # "Find artifacts about X"
    SIMILARITY = "similarity"         # "Find similar to X"
    STATUS = "status"                 # "What's the status of X?"
    METRIC = "metric"                 # "Most used artifacts"
    UNKNOWN = "unknown"


@dataclass
class ParsedQuery:
    """Parsed natural language query."""
    intent: QueryIntent
    entities: Dict[str, Any]
    filters: Dict[str, Any]
    original_query: str
    confidence: float

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "intent": self.intent.value,
            "entities": self.entities,
            "filters": self.filters,
            "original_query": self.original_query,
            "confidence": self.confidence
        }


class NLQueryParser:
    """Parse natural language queries into structured database queries."""

    # Artifact types
    ARTIFACT_TYPES = [
        "agent", "skill", "plan", "library", "script",
        "template", "document", "test", "config", "module",
        "framework", "tool", "workspace", "example"
    ]

    # Categories by type
    CATEGORIES = {
        "agent": ["core", "bmad", "research", "specialist", "enhanced"],
        "skill": ["core", "mcp", "workflow"],
        "library": [
            "context-variables", "hierarchical-tasks", "task-breakdown",
            "spec-creation", "ralph-runtime", "circuit-breaker", "response-analyzer"
        ],
        "script": ["agents", "planning", "testing", "integration", "validation"],
        "document": ["getting-started", "architecture", "components", "frameworks", "workflows", "reference"],
        "test": ["unit", "integration", "phase", "e2e"],
        "module": ["context", "planning", "research", "kanban"],
        "framework": ["bmad", "speckit", "metagpt", "swarm"],
        "tool": ["maintenance", "migration", "validation"]
    }

    # Status values
    STATUSES = ["active", "deprecated", "archived", "experimental", "beta", "development"]

    # Phases
    PHASES = [1, 2, 3, 4]

    # Layers
    LAYERS = ["intelligence", "execution", "testing", "documentation", "system", "planning", "workspace"]

    # Intent patterns
    INTENT_PATTERNS = {
        QueryIntent.PLACEMENT: [
            r"where\s+(should\s+i\s+)?(put|place|locate|store|save)",
            r"where\s+(does|would)\s+\w+\s+go",
            r"correct\s+(location|path|place)\s+for",
            r"organize\s+.+?\s+into"
        ],
        QueryIntent.DISCOVERY: [
            r"find\s+(all\s+)?(.+?)\s+(agents|artifacts|files|items)",
            r"list\s+(all\s+)?(.+?)\s+(agents|artifacts|files|items)",
            r"show\s+me\s+(all\s+)?",
            r"get\s+(all\s+)?",
            r"search\s+for",
            r"what\s+.+?\s+(exist|are\s+available)"
        ],
        QueryIntent.RELATIONSHIP: [
            r"what\s+(does|do)\s+.+?\s+(depend\s+on|need|require)",
            r"what\s+(will|would)\s+break\s+if",
            r"what\s+uses\s+.+?",
            r"dependencies?\s+of",
            r"relationship(s)?\s+between",
            r"related\s+to"
        ],
        QueryIntent.SEMANTIC: [
            r"find\s+.+?\s+about",
            r"search\s+for\s+.+?\s+(about|related\s+to)",
            r"show\s+me\s+.+?\s+about",
            r"anything\s+about",
            r"information\s+on"
        ],
        QueryIntent.SIMILARITY: [
            r"find\s+(artifacts|agents|items)?\s+similar\s+to",
            r"like\s+.+?",
            r"alternatives?\s+to",
            r"similar\s+(to|as)"
        ],
        QueryIntent.STATUS: [
            r"what\s+(is|'s)\s+the\s+status\s+of",
            r"status\s+of",
            r"is\s+.+?\s+(complete|done|ready)",
            r"check\s+status"
        ],
        QueryIntent.METRIC: [
            r"most\s+(popular|used|frequented)",
            r"least\s+(popular|used|frequented)",
            r"top\s+\d+",
            r"highest\s+(success\s+rate|usage)",
            r"lowest\s+(success\s+rate|usage)"
        ]
    }

    def __init__(self):
        """Initialize parser."""
        # Compile regex patterns
        self.compiled_patterns = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            self.compiled_patterns[intent] = [
                re.compile(pattern, re.IGNORECASE)
                for pattern in patterns
            ]

    def parse(self, query: str) -> ParsedQuery:
        """
        Parse natural language query.

        Args:
            query: Natural language query string

        Returns:
            ParsedQuery object
        """
        query = query.strip()
        logger.info(f"Parsing query: {query}")

        # Detect intent
        intent, confidence = self._detect_intent(query)

        # Extract entities and filters
        entities = self._extract_entities(query)
        filters = self._extract_filters(query, entities)

        parsed = ParsedQuery(
            intent=intent,
            entities=entities,
            filters=filters,
            original_query=query,
            confidence=confidence
        )

        logger.info(f"Parsed: {parsed.to_dict()}")
        return parsed

    def _detect_intent(self, query: str) -> Tuple[QueryIntent, float]:
        """
        Detect query intent using pattern matching.

        Returns:
            Tuple of (intent, confidence)
        """
        query_lower = query.lower()
        scores = {}

        # Score each intent
        for intent, patterns in self.compiled_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern.search(query):
                    score += 1
            scores[intent] = score

        # Get highest scoring intent
        if not scores or max(scores.values()) == 0:
            return QueryIntent.UNKNOWN, 0.0

        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent] * 0.3, 1.0)

        return best_intent, confidence

    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from query."""
        entities = {}
        query_lower = query.lower()

        # Extract artifact type
        for artifact_type in self.ARTIFACT_TYPES:
            # Check for singular and plural
            if artifact_type in query_lower or f"{artifact_type}s" in query_lower:
                entities["type"] = artifact_type
                break

        # Extract category
        for type_name, categories in self.CATEGORIES.items():
            for category in categories:
                if category in query_lower:
                    entities["category"] = category
                    # If type not found, infer from category
                    if "type" not in entities:
                        entities["type"] = type_name
                    break

        # Extract status
        for status in self.STATUSES:
            if status in query_lower:
                entities["status"] = status
                break

        # Extract phase
        phase_match = re.search(r"phase\s+(\d)", query_lower)
        if phase_match:
            entities["phase"] = int(phase_match.group(1))

        # Extract layer
        for layer in self.LAYERS:
            if layer in query_lower:
                entities["layer"] = layer
                break

        # Extract tags (after 'tagged', 'with', 'marked as')
        tag_match = re.search(r"(?:tagged|with|marked\s+as):\s*([^,.]+)", query_lower)
        if tag_match:
            tags = [t.strip() for t in tag_match.group(1).split(",")]
            entities["tags"] = tags

        # Extract artifact ID (alphanumeric with hyphens)
        id_match = re.search(r"\b([a-z0-9-]{10,})\b", query_lower)
        if id_match:
            entities["artifact_id"] = id_match.group(1)

        # Extract description/topic (for semantic search)
        # Remove common words and extract remaining phrases
        topic = self._extract_topic(query)
        if topic:
            entities["topic"] = topic

        return entities

    def _extract_filters(self, query: str, entities: Dict) -> Dict[str, Any]:
        """Extract filters from query."""
        filters = {}
        query_lower = query.lower()

        # Date filters
        date_match = re.search(
            r"(before|after|since|until)\s+(\d{4}-\d{2}-\d{2})",
            query_lower
        )
        if date_match:
            filters["date"] = {
                "operator": date_match.group(1),
                "value": date_match.group(2)
            }

        # Quantity filters
        quantity_match = re.search(r"(top|bottom|first|last)\s+(\d+)", query_lower)
        if quantity_match:
            filters["limit"] = int(quantity_match.group(2))

        # Similarity threshold
        similarity_match = re.search(r"similarity\s+(above|over|greater\s+than)\s+([\d.]+)", query_lower)
        if similarity_match:
            filters["min_similarity"] = float(similarity_match.group(2))

        # Usage count filter
        usage_match = re.search(r"used\s+(more|less)\s+than\s+(\d+)\s+times", query_lower)
        if usage_match:
            filters["usage_count"] = {
                "operator": "gt" if usage_match.group(1) == "more" else "lt",
                "value": int(usage_match.group(2))
            }

        # Success rate filter
        rate_match = re.search(r"success\s+rate\s+(above|over|below)\s+([\d.]+)", query_lower)
        if rate_match:
            filters["success_rate"] = float(rate_match.group(2))

        return filters

    def _extract_topic(self, query: str) -> Optional[str]:
        """Extract topic/subject for semantic search."""
        # Remove common query words
        stop_words = {
            "find", "show", "get", "list", "search", "about", "for", "me", "the",
            "a", "an", "all", "any", "some", "what", "where", "when", "how", "why",
            "agent", "agents", "artifact", "artifacts", "file", "files", "item", "items"
        }

        # Tokenize
        words = re.findall(r"\w+", query.lower())

        # Filter stop words
        content_words = [w for w in words if w not in stop_words and len(w) > 2]

        if content_words:
            return " ".join(content_words)

        return None

    def explain(self, parsed: ParsedQuery) -> str:
        """
        Generate human-readable explanation of parsed query.

        Args:
            parsed: ParsedQuery object

        Returns:
            Explanation string
        """
        explanation = f"Query: {parsed.original_query}\n"
        explanation += f"Intent: {parsed.intent.value} (confidence: {parsed.confidence:.2f})\n"

        if parsed.entities:
            explanation += "\nEntities:\n"
            for key, value in parsed.entities.items():
                explanation += f"  - {key}: {value}\n"

        if parsed.filters:
            explanation += "\nFilters:\n"
            for key, value in parsed.filters.items():
                explanation += f"  - {key}: {value}\n"

        return explanation


class QueryExecutor:
    """Execute parsed queries against databases."""

    def __init__(self, vector_search=None, structured_search=None):
        """
        Initialize query executor.

        Args:
            vector_search: VectorSearch instance for semantic queries
            structured_search: Structured search instance (PostgreSQL)
        """
        self.vector_search = vector_search
        self.structured_search = structured_search
        self.parser = NLQueryParser()

    def execute(self, query: str) -> Dict[str, Any]:
        """
        Execute natural language query.

        Args:
            query: Natural language query string

        Returns:
            Query results with metadata
        """
        # Parse query
        parsed = self.parser.parse(query)

        # Route to appropriate executor
        try:
            if parsed.intent == QueryIntent.SEMANTIC:
                results = self._execute_semantic(parsed)
            elif parsed.intent == QueryIntent.SIMILARITY:
                results = self._execute_similarity(parsed)
            elif parsed.intent == QueryIntent.DISCOVERY:
                results = self._execute_discovery(parsed)
            elif parsed.intent == QueryIntent.RELATIONSHIP:
                results = self._execute_relationship(parsed)
            elif parsed.intent == QueryIntent.STATUS:
                results = self._execute_status(parsed)
            elif parsed.intent == QueryIntent.METRIC:
                results = self._execute_metric(parsed)
            elif parsed.intent == QueryIntent.PLACEMENT:
                results = self._execute_placement(parsed)
            else:
                results = {
                    "error": "Unknown query intent",
                    "suggestion": "Try rephrasing your query"
                }

            return {
                "query": query,
                "parsed": parsed.to_dict(),
                "results": results,
                "explanation": self.parser.explain(parsed)
            }

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {
                "query": query,
                "parsed": parsed.to_dict(),
                "error": str(e)
            }

    def _execute_semantic(self, parsed: ParsedQuery) -> Dict[str, Any]:
        """Execute semantic search query."""
        if not self.vector_search:
            return {"error": "Vector search not configured"}

        # Need to generate embedding for topic
        # This would be done by integrating with embedder
        return {
            "message": "Semantic search requires embedding generation",
            "topic": parsed.entities.get("topic", ""),
            "filters": parsed.filters
        }

    def _execute_similarity(self, parsed: ParsedQuery) -> Dict[str, Any]:
        """Execute similarity search query."""
        if not self.vector_search:
            return {"error": "Vector search not configured"}

        artifact_id = parsed.entities.get("artifact_id")
        if not artifact_id:
            return {"error": "Artifact ID not found in query"}

        results = self.vector_search.find_similar(
            artifact_id=artifact_id,
            limit=parsed.filters.get("limit", 10)
        )

        return {
            "artifact_id": artifact_id,
            "similar_artifacts": [r.to_dict() for r in results]
        }

    def _execute_discovery(self, parsed: ParsedQuery) -> Dict[str, Any]:
        """Execute discovery query (structured search)."""
        if not self.structured_search:
            return {"error": "Structured search not configured"}

        # Build filter dict
        filters = {}
        if "type" in parsed.entities:
            filters["type"] = parsed.entities["type"]
        if "category" in parsed.entities:
            filters["category"] = parsed.entities["category"]
        if "status" in parsed.entities:
            filters["status"] = parsed.entities["status"]

        return {
            "message": "Discovery query execution",
            "filters": filters,
            "limit": parsed.filters.get("limit", 50)
        }

    def _execute_relationship(self, parsed: ParsedQuery) -> Dict[str, Any]:
        """Execute relationship query."""
        artifact_id = parsed.entities.get("artifact_id")
        if not artifact_id:
            return {"error": "Artifact ID not found in query"}

        return {
            "message": "Relationship query execution",
            "artifact_id": artifact_id,
            "query_type": "dependencies"
        }

    def _execute_status(self, parsed: ParsedQuery) -> Dict[str, Any]:
        """Execute status query."""
        artifact_id = parsed.entities.get("artifact_id")
        if not artifact_id:
            return {"error": "Artifact ID not found in query"}

        return {
            "message": "Status query execution",
            "artifact_id": artifact_id
        }

    def _execute_metric(self, parsed: ParsedQuery) -> Dict[str, Any]:
        """Execute metric query."""
        return {
            "message": "Metric query execution",
            "filters": parsed.filters
        }

    def _execute_placement(self, parsed: ParsedQuery) -> Dict[str, Any]:
        """Execute placement query."""
        artifact_type = parsed.entities.get("type", "unknown")
        category = parsed.entities.get("category", "")

        # Suggest path based on type and category
        path = self._suggest_path(artifact_type, category)

        return {
            "artifact_type": artifact_type,
            "category": category,
            "suggested_path": path
        }

    def _suggest_path(self, artifact_type: str, category: str) -> str:
        """Suggest path for artifact."""
        # Simplified path suggestions
        path_map = {
            "agent": "1-agents/",
            "skill": "1-agents/.skills/",
            "library": "4-scripts/lib/",
            "script": "4-scripts/",
            "document": ".docs/",
            "test": "tests/",
            "plan": ".plans/"
        }

        base_path = path_map.get(artifact_type, "misc/")

        # Add category-specific path
        if artifact_type == "agent":
            category_path = {
                "core": "1-core/",
                "bmad": "2-bmad/",
                "research": "3-research/",
                "specialist": "4-specialists/",
                "enhanced": "5-enhanced/"
            }.get(category, "")
            base_path += category_path

        return base_path


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Command-line interface for NL query parser."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Parse natural language queries for Blackbox4 Brain"
    )
    parser.add_argument(
        "query",
        help="Natural language query"
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Show explanation of parsed query"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse query
    parser_instance = NLQueryParser()
    parsed = parser_instance.parse(args.query)

    # Output
    if args.explain:
        print(parser_instance.explain(parsed))
    else:
        print(json.dumps(parsed.to_dict(), indent=2))

    # Save to file
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(parsed.to_dict(), f, indent=2)
        print(f"\nResult saved to: {args.output}")


if __name__ == "__main__":
    main()
