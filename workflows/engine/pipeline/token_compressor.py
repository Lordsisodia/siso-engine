"""
Token Compression System for Context Management

This module provides intelligent token compression capabilities for the BlackBox5
task planning system. It automatically compresses context when it exceeds token limits,
preserving important information while reducing token usage.

Strategies:
1. Relevance-based pruning - Remove least relevant files/sections
2. Extractive summarization - Keep only key sentences
3. Abstractive summarization - LLM-based compression
4. Code summarization - Summarize code to function signatures
5. Deduplication - Remove redundant information

Component 10 of the enhanced GSD framework.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class CompressionStrategy(str, Enum):
    """Compression strategy types."""
    RELEVANCE = "relevance"  # Remove least relevant items
    EXTRACTIVE = "extractive"  # Keep key sentences
    ABSTRACTIVE = "abstractive"  # LLM-based summarization
    CODE_SUMMARY = "code_summary"  # Function signatures only
    DEDUPLICATE = "deduplicate"  # Remove redundant info
    HYBRID = "hybrid"  # Combine multiple strategies


@dataclass
class CompressionMetrics:
    """Metrics about compression operation."""
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float  # compressed / original
    strategy_used: CompressionStrategy
    items_removed: int
    items_kept: int
    time_taken: float
    quality_score: float  # Estimated quality preservation (0-1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_tokens': self.original_tokens,
            'compressed_tokens': self.compressed_tokens,
            'compression_ratio': self.compression_ratio,
            'strategy_used': self.strategy_used.value,
            'items_removed': self.items_removed,
            'items_kept': self.items_kept,
            'time_taken': self.time_taken,
            'quality_score': self.quality_score
        }


@dataclass
class CompressionResult:
    """Result of compression operation."""
    compressed_context: Any  # TaskContext or similar
    metrics: CompressionMetrics
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'compressed_context': self.compressed_context.to_dict() if hasattr(self.compressed_context, 'to_dict') else self.compressed_context,
            'metrics': self.metrics.to_dict(),
            'warnings': self.warnings
        }


class TokenEstimator:
    """Estimate token count for text."""

    # Approximate tokens per character for different languages
    TOKENS_PER_CHAR = {
        'python': 0.3,  # Code is more token-dense
        'javascript': 0.3,
        'typescript': 0.3,
        'java': 0.25,
        'cpp': 0.25,
        'markdown': 0.5,  # Text is less dense
        'yaml': 0.4,
        'json': 0.35,
        'default': 0.4
    }

    @classmethod
    def estimate(cls, text: str, language: str = 'default') -> int:
        """
        Estimate token count for text.

        Args:
            text: Text to estimate
            language: Language type for better accuracy

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        char_count = len(text)
        ratio = cls.TOKENS_PER_CHAR.get(language, cls.TOKENS_PER_CHAR['default'])
        return int(char_count * ratio)

    @classmethod
    def estimate_file_context(cls, file_context: Any) -> int:
        """Estimate tokens for a FileContext object."""
        # Estimate relevant lines
        lines_text = '\n'.join(getattr(file_context, 'relevant_lines', []))
        tokens = cls.estimate(lines_text, getattr(file_context, 'language', 'default'))

        # Add summary tokens
        summary = getattr(file_context, 'summary', '')
        tokens += cls.estimate(summary, 'markdown')

        return tokens

    @classmethod
    def estimate_doc_section(cls, doc_section: Any) -> int:
        """Estimate tokens for a DocSection object."""
        content = getattr(doc_section, 'content', '')
        return cls.estimate(content, 'markdown')

    @classmethod
    def estimate_task_context(cls, task_context: Any) -> int:
        """Estimate total tokens for a TaskContext object."""
        total = 0

        # Task description
        total += cls.estimate(getattr(task_context, 'task_description', ''), 'markdown')

        # Files
        for file_ctx in getattr(task_context, 'relevant_files', []):
            total += cls.estimate_file_context(file_ctx)

        # Docs
        for doc_ctx in getattr(task_context, 'relevant_docs', []):
            total += cls.estimate_doc_section(doc_ctx)

        # Conversation
        conv_ctx = getattr(task_context, 'conversation_context', None)
        if conv_ctx:
            total += cls.estimate(getattr(conv_ctx, 'summary', ''), 'markdown')
            for msg in getattr(conv_ctx, 'relevant_messages', []):
                total += cls.estimate(str(msg), 'markdown')

        return total


class RelevanceScorer:
    """Score relevance of context items."""

    def score_file_context(self, file_context: Any, keywords: List[str]) -> float:
        """
        Score relevance of a file context (0-1).

        Factors:
        - Keyword matches in relevant_lines
        - Keyword matches in file_path
        - Recency (last_modified)
        - Size (smaller files may be more focused)
        """
        score = 0.0

        # Keyword matches in relevant lines (most important)
        relevant_lines = getattr(file_context, 'relevant_lines', [])
        if relevant_lines:
            keyword_matches = sum(
                sum(1 for line in relevant_lines if kw.lower() in line.lower())
                for kw in keywords
            )
            score += min(keyword_matches / 10.0, 0.5)  # Max 0.5 from keywords

        # Keyword matches in file path
        file_path = getattr(file_context, 'file_path', '')
        path_matches = sum(1 for kw in keywords if kw.lower() in file_path.lower())
        score += min(path_matches * 0.1, 0.2)  # Max 0.2 from path

        # Recency bonus (more recent = slightly more relevant)
        last_modified = getattr(file_context, 'last_modified', None)
        if last_modified:
            days_old = (datetime.utcnow() - last_modified).days
            if days_old < 7:
                score += 0.1
            elif days_old < 30:
                score += 0.05

        # Size penalty (smaller files may be more focused)
        size = getattr(file_context, 'size_bytes', 0)
        if size < 1000:
            score += 0.1
        elif size > 100000:
            score -= 0.1

        return min(score, 1.0)

    def score_doc_section(self, doc_section: Any, keywords: List[str]) -> float:
        """Score relevance of a doc section (0-1)."""
        score = 0.0

        # Title matches (most important)
        title = getattr(doc_section, 'title', '')
        title_matches = sum(1 for kw in keywords if kw.lower() in title.lower())
        score += min(title_matches * 0.3, 0.6)

        # Content matches
        content = getattr(doc_section, 'content', '')
        content_matches = sum(
            content.lower().count(kw.lower())
            for kw in keywords
        )
        score += min(content_matches / 20.0, 0.3)

        # Relevance score if already present
        existing_score = getattr(doc_section, 'relevance_score', 0.0)
        score = (score + existing_score) / 2

        return min(score, 1.0)


class ExtractiveSummarizer:
    """Extractive summarization - keep key sentences."""

    def __init__(self, max_sentences: int = 5):
        self.max_sentences = max_sentences

    def summarize_text(self, text: str, keywords: List[str]) -> str:
        """
        Summarize text by extracting key sentences.

        Args:
            text: Text to summarize
            keywords: Keywords to prioritize

        Returns:
            Summarized text
        """
        if not text:
            return ""

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        if len(sentences) <= self.max_sentences:
            return text

        # Score each sentence
        scored = []
        for sentence in sentences:
            score = self._score_sentence(sentence, keywords)
            scored.append((score, sentence))

        # Sort by score and keep top N
        scored.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [s for score, s in scored[:self.max_sentences]]

        # Maintain original order
        sentence_order = {s: i for i, s in enumerate(sentences)}
        top_sentences.sort(key=lambda s: sentence_order.get(s, float('inf')))

        return ' '.join(top_sentences)

    def _score_sentence(self, sentence: str, keywords: List[str]) -> float:
        """Score a sentence's importance."""
        score = 0.0

        # Keyword matches
        for kw in keywords:
            if kw.lower() in sentence.lower():
                score += 2.0

        # Length (medium sentences are often more informative)
        words = len(sentence.split())
        if 10 <= words <= 30:
            score += 1.0
        elif words < 5:
            score -= 0.5

        # Contains important patterns
        if any(pattern in sentence.lower() for pattern in [
            'important', 'note', 'warning', 'error', 'fix',
            'implement', 'function', 'class', 'method'
        ]):
            score += 1.0

        return score


class CodeSummarizer:
    """Summarize code to function signatures and key structures."""

    def summarize_code(self, code: str, language: str) -> str:
        """
        Summarize code by extracting function/class signatures.

        Args:
            code: Code to summarize
            language: Programming language

        Returns:
            Summarized code
        """
        if not code:
            return ""

        lines = code.split('\n')
        summary = []

        # Python patterns
        if language == 'python':
            summary.extend(self._summarize_python(lines))

        # JavaScript/TypeScript patterns
        elif language in ['javascript', 'typescript']:
            summary.extend(self._summarize_javascript(lines))

        # Default: keep first 20 lines
        else:
            summary = lines[:20]

        return '\n'.join(summary)

    def _summarize_python(self, lines: List[str]) -> List[str]:
        """Extract Python function/class signatures."""
        summary = []
        for line in lines:
            stripped = line.strip()
            # Function/class definitions
            if stripped.startswith(('def ', 'class ')):
                summary.append(line)
            # Import statements
            elif stripped.startswith('import ') or stripped.startswith('from '):
                summary.append(line)
            # Decorators
            elif stripped.startswith('@'):
                summary.append(line)
            # Docstring start
            elif stripped.startswith('"""') or stripped.startswith("'''"):
                summary.append(line)
                break  # Only show first line of docstring

        return summary[:20]  # Limit to 20 lines

    def _summarize_javascript(self, lines: List[str]) -> List[str]:
        """Extract JavaScript/TypeScript function/class signatures."""
        summary = []
        for line in lines:
            stripped = line.strip()
            # Function/class definitions
            if any(stripped.startswith(p) for p in ['function ', 'class ', 'const ', 'let ', 'var ']):
                summary.append(line)
            # Arrow functions
            if '=>' in stripped:
                summary.append(line)
            # Export/import
            if stripped.startswith(('export ', 'import ')):
                summary.append(line)

        return summary[:20]


class Deduplicator:
    """Remove redundant information from context."""

    def deduplicate_file_contexts(self, file_contexts: List[Any]) -> List[Any]:
        """
        Remove duplicate or very similar file contexts.

        Args:
            file_contexts: List of FileContext objects

        Returns:
            Deduplicated list
        """
        if not file_contexts:
            return []

        # Group by file path (remove exact duplicates)
        seen_paths = set()
        unique = []
        for fc in file_contexts:
            path = getattr(fc, 'file_path', '')
            if path not in seen_paths:
                seen_paths.add(path)
                unique.append(fc)

        # Remove near-duplicates based on content similarity
        deduplicated = []
        seen_signatures = set()

        for fc in unique:
            signature = self._create_signature(fc)
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                deduplicated.append(fc)

        return deduplicated

    def _create_signature(self, file_context: Any) -> str:
        """Create a simple signature for deduplication."""
        relevant_lines = getattr(file_context, 'relevant_lines', [])
        # Use first few non-empty lines as signature
        signature_lines = [line.strip() for line in relevant_lines[:5] if line.strip()]
        return '|'.join(signature_lines[:3])


class TokenCompressor:
    """
    Main token compression engine.

    Automatically compresses context to fit within token limits
    while preserving important information.
    """

    def __init__(
        self,
        max_tokens: int = 8000,
        target_ratio: float = 0.8,  # Target 80% of max
        strategies: List[CompressionStrategy] = None
    ):
        """
        Initialize token compressor.

        Args:
            max_tokens: Maximum token limit
            target_ratio: Target compression ratio (0-1)
            strategies: Compression strategies to try (in order)
        """
        self.max_tokens = max_tokens
        self.target_tokens = int(max_tokens * target_ratio)
        self.strategies = strategies or [
            CompressionStrategy.RELEVANCE,
            CompressionStrategy.EXTRACTIVE,
            CompressionStrategy.CODE_SUMMARY,
            CompressionStrategy.DEDUPLICATE
        ]

        self.estimator = TokenEstimator()
        self.scorer = RelevanceScorer()
        self.extractor = ExtractiveSummarizer()
        self.code_summarizer = CodeSummarizer()
        self.deduplicator = Deduplicator()

    def compress(
        self,
        task_context: Any,
        keywords: List[str] = None,
        strategy: CompressionStrategy = CompressionStrategy.HYBRID
    ) -> CompressionResult:
        """
        Compress task context to fit within token limits.

        Args:
            task_context: TaskContext to compress
            keywords: Keywords for relevance scoring
            strategy: Compression strategy to use

        Returns:
            CompressionResult with compressed context and metrics
        """
        start_time = datetime.utcnow()

        # Estimate current tokens
        original_tokens = self.estimator.estimate_task_context(task_context)
        keywords = keywords or getattr(task_context, 'keywords', [])

        logger.info(f"Compressing context: {original_tokens} tokens → {self.target_tokens} target")

        # If already under limit, return as-is
        if original_tokens <= self.target_tokens:
            return CompressionResult(
                compressed_context=task_context,
                metrics=CompressionMetrics(
                    original_tokens=original_tokens,
                    compressed_tokens=original_tokens,
                    compression_ratio=1.0,
                    strategy_used=CompressionStrategy.RELEVANCE,
                    items_removed=0,
                    items_kept=self._count_items(task_context),
                    time_taken=(datetime.utcnow() - start_time).total_seconds(),
                    quality_score=1.0
                )
            )

        # Apply compression strategy
        if strategy == CompressionStrategy.HYBRID:
            compressed = self._apply_hybrid_strategy(task_context, keywords)
        else:
            compressed = self._apply_single_strategy(task_context, keywords, strategy)

        # Estimate compressed tokens
        compressed_tokens = self.estimator.estimate_task_context(compressed)

        # Calculate metrics
        time_taken = (datetime.utcnow() - start_time).total_seconds()
        metrics = CompressionMetrics(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / original_tokens if original_tokens > 0 else 1.0,
            strategy_used=strategy,
            items_removed=self._count_items(task_context) - self._count_items(compressed),
            items_kept=self._count_items(compressed),
            time_taken=time_taken,
            quality_score=self._estimate_quality(compressed, keywords)
        )

        logger.info(
            f"Compression complete: {original_tokens} → {compressed_tokens} tokens "
            f"({metrics.compression_ratio:.1%} reduction) in {time_taken:.2f}s"
        )

        return CompressionResult(
            compressed_context=compressed,
            metrics=metrics,
            warnings=self._generate_warnings(compressed_tokens, metrics)
        )

    def _apply_hybrid_strategy(self, task_context: Any, keywords: List[str]) -> Any:
        """Apply multiple compression strategies in sequence."""
        context = task_context

        for strategy in self.strategies:
            # Check if we need more compression
            current_tokens = self.estimator.estimate_task_context(context)
            if current_tokens <= self.target_tokens:
                break

            # Apply strategy
            context = self._apply_single_strategy(context, keywords, strategy)

        return context

    def _apply_single_strategy(self, task_context: Any, keywords: List[str], strategy: CompressionStrategy) -> Any:
        """Apply a single compression strategy."""
        if strategy == CompressionStrategy.RELEVANCE:
            return self._compress_by_relevance(task_context, keywords)
        elif strategy == CompressionStrategy.EXTRACTIVE:
            return self._compress_extractive(task_context, keywords)
        elif strategy == CompressionStrategy.CODE_SUMMARY:
            return self._compress_code(task_context)
        elif strategy == CompressionStrategy.DEDUPLICATE:
            return self._deduplicate(task_context)
        else:
            return task_context

    def _compress_by_relevance(self, task_context: Any, keywords: List[str]) -> Any:
        """Compress by removing least relevant items."""
        from .context_extractor import TaskContext, FileContext, DocSection

        # Score and sort files
        files = getattr(task_context, 'relevant_files', [])
        scored_files = [
            (self.scorer.score_file_context(f, keywords), f)
            for f in files
        ]
        scored_files.sort(key=lambda x: x[0], reverse=True)

        # Keep most relevant files
        kept_files = []
        for score, file_ctx in scored_files:
            current_tokens = self.estimator.estimate_file_context(file_ctx)
            if self.estimator.estimate_task_context(
                TaskContext(
                    task_id='temp',
                    task_description='',
                    relevant_files=kept_files + [file_ctx],
                    relevant_docs=[],
                    conversation_context=None,
                    total_tokens=0,
                    extraction_time=0,
                    sources_searched=0,
                    keywords=[]
                )
            ) < self.target_tokens:
                kept_files.append(file_ctx)
            else:
                break  # Stop if adding this file would exceed limit

        # Score and sort docs
        docs = getattr(task_context, 'relevant_docs', [])
        scored_docs = [
            (self.scorer.score_doc_section(d, keywords), d)
            for d in docs
        ]
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        # Keep most relevant docs
        kept_docs = []
        for score, doc_ctx in scored_docs:
            current_tokens = self.estimator.estimate_doc_section(doc_ctx)
            # Estimate total with current kept files
            total = sum(self.estimator.estimate_file_context(f) for f in kept_files)
            total += current_tokens
            if total < self.target_tokens:
                kept_docs.append(doc_ctx)
            else:
                break

        # Return new TaskContext with compressed data
        return TaskContext(
            task_id=getattr(task_context, 'task_id'),
            task_description=getattr(task_context, 'task_description'),
            relevant_files=kept_files,
            relevant_docs=kept_docs,
            conversation_context=getattr(task_context, 'conversation_context'),
            total_tokens=0,  # Will be recalculated
            extraction_time=getattr(task_context, 'extraction_time'),
            sources_searched=getattr(task_context, 'sources_searched'),
            keywords=getattr(task_context, 'keywords', []),
            extracted_at=getattr(task_context, 'extracted_at')
        )

    def _compress_extractive(self, task_context: Any, keywords: List[str]) -> Any:
        """Compress using extractive summarization."""
        from .context_extractor import TaskContext, FileContext, DocSection

        # Summarize file contexts
        compressed_files = []
        for file_ctx in getattr(task_context, 'relevant_files', []):
            # Summarize relevant lines
            relevant_lines = getattr(file_ctx, 'relevant_lines', [])
            summary = self.extractor.summarize_text(
                '\n'.join(relevant_lines),
                keywords
            )

            compressed_files.append(FileContext(
                file_path=getattr(file_ctx, 'file_path'),
                language=getattr(file_ctx, 'language'),
                relevant_lines=summary.split('\n'),
                summary=getattr(file_ctx, 'summary'),
                size_bytes=getattr(file_ctx, 'size_bytes'),
                last_modified=getattr(file_ctx, 'last_modified')
            ))

        # Summarize doc sections
        compressed_docs = []
        for doc_ctx in getattr(task_context, 'relevant_docs', []):
            content = getattr(doc_ctx, 'content', '')
            summary = self.extractor.summarize_text(content, keywords)

            compressed_docs.append(DocSection(
                section_path=getattr(doc_ctx, 'section_path'),
                title=getattr(doc_ctx, 'title'),
                content=summary,
                relevance_score=getattr(doc_ctx, 'relevance_score', 0.5),
                heading_level=getattr(doc_ctx, 'heading_level', 1)
            ))

        return TaskContext(
            task_id=getattr(task_context, 'task_id'),
            task_description=getattr(task_context, 'task_description'),
            relevant_files=compressed_files,
            relevant_docs=compressed_docs,
            conversation_context=getattr(task_context, 'conversation_context'),
            total_tokens=0,
            extraction_time=getattr(task_context, 'extraction_time'),
            sources_searched=getattr(task_context, 'sources_searched'),
            keywords=getattr(task_context, 'keywords', []),
            extracted_at=getattr(task_context, 'extracted_at')
        )

    def _compress_code(self, task_context: Any) -> Any:
        """Compress by summarizing code."""
        from .context_extractor import TaskContext, FileContext

        compressed_files = []
        for file_ctx in getattr(task_context, 'relevant_files', []):
            # Summarize code in relevant lines
            relevant_lines = getattr(file_ctx, 'relevant_lines', [])
            code = '\n'.join(relevant_lines)
            summary = self.code_summarizer.summarize_code(
                code,
                getattr(file_ctx, 'language', 'python')
            )

            compressed_files.append(FileContext(
                file_path=getattr(file_ctx, 'file_path'),
                language=getattr(file_ctx, 'language'),
                relevant_lines=summary.split('\n') if summary else [],
                summary=getattr(file_ctx, 'summary'),
                size_bytes=getattr(file_ctx, 'size_bytes'),
                last_modified=getattr(file_ctx, 'last_modified')
            ))

        return TaskContext(
            task_id=getattr(task_context, 'task_id'),
            task_description=getattr(task_context, 'task_description'),
            relevant_files=compressed_files,
            relevant_docs=getattr(task_context, 'relevant_docs', []),
            conversation_context=getattr(task_context, 'conversation_context'),
            total_tokens=0,
            extraction_time=getattr(task_context, 'extraction_time'),
            sources_searched=getattr(task_context, 'sources_searched'),
            keywords=getattr(task_context, 'keywords', []),
            extracted_at=getattr(task_context, 'extracted_at')
        )

    def _deduplicate(self, task_context: Any) -> Any:
        """Remove duplicate items."""
        from .context_extractor import TaskContext

        # Deduplicate files
        files = self.deduplicator.deduplicate_file_contexts(
            getattr(task_context, 'relevant_files', [])
        )

        return TaskContext(
            task_id=getattr(task_context, 'task_id'),
            task_description=getattr(task_context, 'task_description'),
            relevant_files=files,
            relevant_docs=getattr(task_context, 'relevant_docs', []),
            conversation_context=getattr(task_context, 'conversation_context'),
            total_tokens=0,
            extraction_time=getattr(task_context, 'extraction_time'),
            sources_searched=getattr(task_context, 'sources_searched'),
            keywords=getattr(task_context, 'keywords', []),
            extracted_at=getattr(task_context, 'extracted_at')
        )

    def _count_items(self, task_context: Any) -> int:
        """Count total items in task context."""
        count = 0
        count += len(getattr(task_context, 'relevant_files', []))
        count += len(getattr(task_context, 'relevant_docs', []))
        return count

    def _estimate_quality(self, compressed_context: Any, keywords: List[str]) -> float:
        """Estimate quality preservation (0-1)."""
        # Simple heuristic: higher relevance scores = better quality
        files = getattr(compressed_context, 'relevant_files', [])
        docs = getattr(compressed_context, 'relevant_docs', [])

        if not files and not docs:
            return 0.5  # No items = unknown quality

        # Average relevance score
        file_scores = [
            self.scorer.score_file_context(f, keywords)
            for f in files
        ]
        doc_scores = [
            self.scorer.score_doc_section(d, keywords)
            for d in docs
        ]

        all_scores = file_scores + doc_scores
        if not all_scores:
            return 0.5

        return sum(all_scores) / len(all_scores)

    def _generate_warnings(self, compressed_tokens: int, metrics: CompressionMetrics) -> List[str]:
        """Generate warnings about compression."""
        warnings = []

        if compressed_tokens > self.max_tokens:
            warnings.append(
                f"Still over token limit: {compressed_tokens} > {self.max_tokens}"
            )

        if metrics.compression_ratio > 0.5:
            warnings.append(
                f"High compression ratio: {metrics.compression_ratio:.1%} - quality may be reduced"
            )

        if metrics.quality_score < 0.5:
            warnings.append(
                f"Low quality score: {metrics.quality_score:.2f} - consider reviewing compressed context"
            )

        return warnings
