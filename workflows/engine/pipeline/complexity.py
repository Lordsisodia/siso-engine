"""
Task Complexity Analyzer for Blackbox5

Analyzes task descriptions to determine complexity and routing decisions.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ComplexityLevel(str, Enum):
    """Task complexity levels."""
    TRIVIAL = "trivial"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplexityScore:
    """
    Represents the complexity analysis of a task.

    Attributes:
        level: Overall complexity level
        score: Numeric score (0-100)
        factors: Dictionary of factors that influenced the score
        confidence: Confidence in the analysis (0-1)
        reasoning: Human-readable explanation of the score
    """

    level: ComplexityLevel
    score: int
    factors: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.8
    reasoning: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "score": self.score,
            "factors": self.factors,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


class TaskComplexityAnalyzer:
    """
    Analyzes task complexity for routing decisions.

    Uses multiple heuristics:
    - Text length and structure
    - Keyword analysis
    - Technical indicators
    - Ambiguity detection
    """

    # Complexity indicators
    HIGH_COMPLEXITY_KEYWORDS = [
        "architecture", "design", "system", "scalable",
        "integrate", "migration", "refactor", "optimize",
        "security", "performance", "distributed",
        "microservices", "infrastructure", "pipeline",
    ]

    MEDIUM_COMPLEXITY_KEYWORDS = [
        "implement", "create", "build", "develop",
        "feature", "function", "api", "endpoint",
        "database", "model", "service", "component",
        "test", "debug", "fix", "error",
    ]

    LOW_COMPLEXITY_KEYWORDS = [
        "update", "change", "modify", "adjust",
        "rename", "move", "delete", "remove",
        "format", "style", "comment", "document",
        "simple", "basic", "quick", "small",
    ]

    # Ambiguity indicators
    AMBIGUITY_PHRASES = [
        "etc", "and so on", "things", "stuff",
        "maybe", "possibly", "might", "could",
        "something", "somewhat", "somehow",
    ]

    def __init__(self, confidence_threshold: float = 0.6):
        """
        Initialize the analyzer.

        Args:
            confidence_threshold: Minimum confidence for analysis
        """
        self.confidence_threshold = confidence_threshold

    def analyze(self, task_description: str, task_type: str = "") -> ComplexityScore:
        """
        Analyze the complexity of a task.

        Args:
            task_description: The task description text
            task_type: Optional task type hint

        Returns:
            ComplexityScore with analysis results
        """
        factors = {}
        reasoning_parts = []

        # Factor 1: Text length
        length_score, length_reasoning = self._analyze_length(task_description)
        factors["length"] = length_score
        reasoning_parts.append(length_reasoning)

        # Factor 2: Keyword complexity
        keyword_score, keyword_reasoning = self._analyze_keywords(task_description)
        factors["keywords"] = keyword_score
        reasoning_parts.append(keyword_reasoning)

        # Factor 3: Technical complexity
        tech_score, tech_reasoning = self._analyze_technical(task_description)
        factors["technical"] = tech_score
        reasoning_parts.append(tech_reasoning)

        # Factor 4: Ambiguity
        ambiguity_score, ambiguity_reasoning = self._analyze_ambiguity(task_description)
        factors["ambiguity"] = ambiguity_score
        reasoning_parts.append(ambiguity_reasoning)

        # Factor 5: Structure complexity
        structure_score, structure_reasoning = self._analyze_structure(task_description)
        factors["structure"] = structure_score
        reasoning_parts.append(structure_reasoning)

        # Calculate overall score
        total_score = sum(factors.values()) / len(factors)

        # Determine level
        level = self._score_to_level(total_score)

        # Calculate confidence
        confidence = self._calculate_confidence(factors)

        # Build reasoning
        reasoning = ". ".join(reasoning_parts)

        return ComplexityScore(
            level=level,
            score=int(total_score),
            factors=factors,
            confidence=confidence,
            reasoning=reasoning,
        )

    def _analyze_length(self, text: str) -> Tuple[float, str]:
        """
        Analyze text length for complexity.

        Longer texts tend to be more complex.
        """
        word_count = len(text.split())

        if word_count < 10:
            score = 10
            reasoning = f"Brief task ({word_count} words) suggests simple work"
        elif word_count < 30:
            score = 30
            reasoning = f"Moderate length ({word_count} words) indicates standard task"
        elif word_count < 60:
            score = 50
            reasoning = f"Long description ({word_count} words) implies complexity"
        else:
            score = 70
            reasoning = f"Very long description ({word_count} words) indicates high complexity"

        return score, reasoning

    def _analyze_keywords(self, text: str) -> Tuple[float, str]:
        """
        Analyze keywords for complexity indicators.
        """
        text_lower = text.lower()
        high_count = sum(1 for kw in self.HIGH_COMPLEXITY_KEYWORDS if kw in text_lower)
        medium_count = sum(1 for kw in self.MEDIUM_COMPLEXITY_KEYWORDS if kw in text_lower)
        low_count = sum(1 for kw in self.LOW_COMPLEXITY_KEYWORDS if kw in text_lower)

        if high_count > 2:
            score = 80
            reasoning = f"Multiple high-complexity keywords detected ({high_count})"
        elif high_count > 0:
            score = 60
            reasoning = f"High-complexity keywords present ({high_count})"
        elif medium_count > 3:
            score = 45
            reasoning = f"Multiple medium-complexity keywords ({medium_count})"
        elif low_count > 2:
            score = 20
            reasoning = f"Low-complexity keywords suggest simple task ({low_count})"
        else:
            score = 40
            reasoning = "No strong complexity indicators"

        return score, reasoning

    def _analyze_technical(self, text: str) -> Tuple[float, str]:
        """
        Analyze technical complexity indicators.
        """
        tech_indicators = [
            r"\b[A-Z]{2,}\b",  # Acronyms
            r"\b\w+\.\w+\b",  # Dotted notation (modules, methods)
            r"<[^>]+>",  # Code/HTML tags
            r"```",  # Code blocks
            r"http[s]?://",  # URLs
            r"/\w+/",  # Paths
        ]

        tech_count = 0
        for pattern in tech_indicators:
            tech_count += len(re.findall(pattern, text))

        if tech_count > 10:
            score = 70
            reasoning = f"High technical content ({tech_count} technical elements)"
        elif tech_count > 5:
            score = 50
            reasoning = f"Moderate technical content ({tech_count} technical elements)"
        elif tech_count > 0:
            score = 30
            reasoning = f"Some technical elements ({tech_count})"
        else:
            score = 20
            reasoning = "Minimal technical content"

        return score, reasoning

    def _analyze_ambiguity(self, text: str) -> Tuple[float, str]:
        """
        Detect ambiguity which increases complexity.
        """
        text_lower = text.lower()
        ambiguity_count = sum(1 for phrase in self.AMBIGUITY_PHRASES if phrase in text_lower)

        # Also check for vague quantifiers
        vague_patterns = [
            r"\d+ or more",
            r"multiple",
            r"several",
            r"various",
            r"number of",
        ]
        vague_count = sum(len(re.findall(pattern, text_lower)) for pattern in vague_patterns)

        total_ambiguity = ambiguity_count + vague_count

        if total_ambiguity > 3:
            score = 70
            reasoning = f"High ambiguity detected ({total_ambiguity} vague phrases)"
        elif total_ambiguity > 1:
            score = 50
            reasoning = f"Some ambiguity present ({total_ambiguity} vague phrases)"
        else:
            score = 20
            reasoning = "Clear and specific description"

        return score, reasoning

    def _analyze_structure(self, text: str) -> Tuple[float, str]:
        """
        Analyze structural complexity.
        """
        # Check for lists, steps, or sections
        has_list = bool(re.search(r"^\s*[-*]\s", text, re.MULTILINE))
        has_numbering = bool(re.search(r"^\s*\d+\.", text, re.MULTILINE))
        has_sections = bool(re.search(r"^#+\s", text, re.MULTILINE))

        # Check for questions
        question_count = text.count("?")

        if has_list and has_numbering and has_sections:
            score = 60
            reasoning = "Highly structured with lists, numbering, and sections"
        elif has_list or has_numbering:
            score = 40
            reasoning = "Structured task with lists or steps"
        elif has_sections:
            score = 45
            reasoning = "Organized into sections"
        elif question_count > 2:
            score = 55
            reasoning = f"Multiple questions suggest complexity ({question_count})"
        else:
            score = 30
            reasoning = "Simple paragraph structure"

        return score, reasoning

    def _score_to_level(self, score: float) -> ComplexityLevel:
        """
        Convert numeric score to complexity level.
        """
        if score < 20:
            return ComplexityLevel.TRIVIAL
        elif score < 40:
            return ComplexityLevel.LOW
        elif score < 60:
            return ComplexityLevel.MEDIUM
        elif score < 80:
            return ComplexityLevel.HIGH
        else:
            return ComplexityLevel.CRITICAL

    def _calculate_confidence(self, factors: Dict[str, float]) -> float:
        """
        Calculate confidence in the analysis.

        High variance between factors lowers confidence.
        """
        if not factors:
            return 0.5

        values = list(factors.values())
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5

        # Lower variance = higher confidence
        # Normalize to 0-1 range
        confidence = max(0.3, min(1.0, 1.0 - (std_dev / 50)))

        return confidence

    def get_statistics(self) -> Dict:
        """Get analyzer statistics."""
        return {
            "type": "TaskComplexityAnalyzer",
            "confidence_threshold": self.confidence_threshold,
        }
