"""
Context Extraction for Task Planning

This module provides context extraction capabilities for the BlackBox5
task planning system. It extracts relevant information from codebase,
documentation, and conversation history to provide better context
for LLM-based task planning.

Component 5 of the GSD (Goal-Driven Development) framework.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import re
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FileContext:
    """
    Context extracted from a source file.

    Attributes:
        file_path: Relative path to the file
        language: Programming language
        relevant_lines: Lines matching task keywords
        summary: Brief summary of file content
        size_bytes: File size in bytes
        last_modified: When file was last modified
    """
    file_path: str
    language: str
    relevant_lines: List[str]
    summary: str
    size_bytes: int
    last_modified: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'file_path': self.file_path,
            'language': self.language,
            'relevant_lines': self.relevant_lines,
            'summary': self.summary,
            'size_bytes': self.size_bytes,
            'last_modified': self.last_modified.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileContext':
        """Create from dictionary."""
        if 'last_modified' in data:
            data['last_modified'] = datetime.fromisoformat(data['last_modified'])
        return cls(**data)


@dataclass
class DocSection:
    """
    Context extracted from documentation.

    Attributes:
        section_path: Path to documentation file
        title: Section title
        content: Relevant content
        relevance_score: How relevant this section is (0-1)
        heading_level: Heading level in document (1-6)
    """
    section_path: str
    title: str
    content: str
    relevance_score: float
    heading_level: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'section_path': self.section_path,
            'title': self.title,
            'content': self.content,
            'relevance_score': self.relevance_score,
            'heading_level': self.heading_level
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocSection':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ConversationContext:
    """
    Context extracted from conversation history.

    Attributes:
        summary: Summary of conversation
        relevant_messages: Messages relevant to task
        participant_count: Number of participants
        message_count: Number of messages analyzed
    """
    summary: str
    relevant_messages: List[Dict[str, str]]
    participant_count: int
    message_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'summary': self.summary,
            'relevant_messages': self.relevant_messages,
            'participant_count': self.participant_count,
            'message_count': self.message_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class TaskContext:
    """
    Complete context package for task planning.

    This is what gets passed to the LLM for planning. Contains all
    relevant information extracted from codebase, documentation, and
    conversation history.

    Attributes:
        task_id: Task identifier
        task_description: Original task description
        relevant_files: Files relevant to this task
        relevant_docs: Documentation sections relevant to this task
        conversation_summary: Optional conversation context
        total_tokens: Estimated token count
        extraction_time: Time taken for extraction
        sources_searched: Number of sources analyzed
        keywords: Keywords extracted for this task
    """
    task_id: str
    task_description: str
    relevant_files: List[FileContext]
    relevant_docs: List[DocSection]
    conversation_context: Optional[ConversationContext]
    total_tokens: int
    extraction_time: float
    sources_searched: int
    keywords: List[str]
    extracted_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'task_id': self.task_id,
            'task_description': self.task_description,
            'relevant_files': [f.to_dict() for f in self.relevant_files],
            'relevant_docs': [d.to_dict() for d in self.relevant_docs],
            'conversation_context': self.conversation_context.to_dict() if self.conversation_context else None,
            'total_tokens': self.total_tokens,
            'extraction_time': self.extraction_time,
            'sources_searched': self.sources_searched,
            'keywords': self.keywords,
            'extracted_at': self.extracted_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskContext':
        """Create from dictionary."""
        if 'extracted_at' in data:
            data['extracted_at'] = datetime.fromisoformat(data['extracted_at'])
        if 'relevant_files' in data:
            data['relevant_files'] = [FileContext.from_dict(f) for f in data['relevant_files']]
        if 'relevant_docs' in data:
            data['relevant_docs'] = [DocSection.from_dict(d) for d in data['relevant_docs']]
        if 'conversation_context' in data and data['conversation_context']:
            data['conversation_context'] = ConversationContext.from_dict(data['conversation_context'])
        return cls(**data)


class ContextExtractor:
    """
    Extracts relevant context for task planning.

    Gathers information from:
    - Codebase (source files matching task keywords)
    - Documentation (README, docs/, etc.)
    - Conversation history (if available)

    The extracted context is then formatted for LLM consumption,
    providing better grounding for task planning decisions.

    Example:
        ```python
        extractor = ContextExtractor(
            codebase_path=Path('/path/to/code'),
            docs_path=Path('/path/to/docs'),
            max_context_tokens=10000
        )

        context = await extractor.extract_context(
            task_id='task-123',
            task_description='Add authentication to the API',
            conversation_history=[...]
        )

        # Format for LLM
        llm_prompt = extractor.format_context_for_llm(context)
        ```
    """

    # File extensions by language
    LANGUAGE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.jsx': 'javascript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.cs': 'csharp',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'zsh',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.less': 'less',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.xml': 'xml',
        '.md': 'markdown',
    }

    # Common directories to skip during search
    SKIP_DIRECTORIES = {
        'node_modules',
        '.git',
        '__pycache__',
        'venv',
        'env',
        '.venv',
        'dist',
        'build',
        'target',
        'bin',
        'obj',
        '.next',
        '.nuxt',
        'coverage',
        '.pytest_cache',
        '.mypy_cache',
        '.tox',
        '.eggs',
        '*.egg-info',
    }

    # Common stop words to filter out
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
        'could', 'may', 'might', 'can', 'need', 'make', 'create', 'add', 'update',
        'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their',
        'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there',
        'use', 'used', 'using', 'get', 'got', 'want', 'wants', 'like',
    }

    def __init__(
        self,
        codebase_path: Path,
        docs_path: Optional[Path] = None,
        max_context_tokens: int = 10000,
        max_files: int = 10,
        max_docs: int = 5,
    ):
        """
        Initialize context extractor.

        Args:
            codebase_path: Path to source code
            docs_path: Optional path to documentation
            max_context_tokens: Maximum tokens to extract
            max_files: Maximum number of files to include
            max_docs: Maximum number of doc sections to include
        """
        self.codebase_path = Path(codebase_path)
        self.docs_path = Path(docs_path) if docs_path else None
        self.max_context_tokens = max_context_tokens
        self.max_files = max_files
        self.max_docs = max_docs

        # Validate paths
        if not self.codebase_path.exists():
            raise ValueError(f"Codebase path does not exist: {codebase_path}")

        if self.docs_path and not self.docs_path.exists():
            logger.warning(f"Docs path does not exist: {docs_path}")
            self.docs_path = None

    def extract_keywords(self, task_description: str) -> List[str]:
        """
        Extract relevant keywords from task description.

        Uses simple NLP techniques:
        - Extract nouns and verbs (remove common stop words)
        - Extract technical terms (capitalized words, hyphenated words)
        - Extract file paths and identifiers

        Args:
            task_description: Task description text

        Returns:
            List of relevant keywords
        """
        keywords = set()

        # Extract file paths with extensions
        path_matches = re.findall(
            r'[\w./-]+\.(?:py|js|ts|jsx|tsx|java|go|rs|cpp|c|h|rb|php|swift|kt|scala|cs|sh|sql|md|yaml|yml|json|xml)',
            task_description
        )
        keywords.update(path_matches)

        # Extract identifiers (camelCase, PascalCase)
        pascal_matches = re.findall(r'\b[A-Z][a-zA-Z0-9]*\b', task_description)
        keywords.update(pascal_matches)

        # Extract camelCase identifiers (including those starting with lowercase)
        camel_matches = re.findall(r'\b[a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*\b', task_description)
        keywords.update(camel_matches)

        # Extract snake_case identifiers
        snake_matches = re.findall(r'\b[a-z][a-z0-9_]{2,}\b', task_description)
        keywords.update(snake_matches)

        # Extract hyphenated terms
        hyphenated_matches = re.findall(r'\b[a-z]+-[a-z]+(?:-[a-z]+)*\b', task_description.lower())
        keywords.update(hyphenated_matches)

        # Extract quoted terms (often technical concepts)
        quoted_matches = re.findall(r'"([^"]+)"|\'([^\']+)\'', task_description)
        for match in quoted_matches:
            if match[0]:
                keywords.add(match[0])
            if match[1]:
                keywords.add(match[1])

        # Extract numbers (versions, sizes, etc.)
        number_matches = re.findall(r'\b\d+(?:\.\d+)?\b', task_description)
        keywords.update(number_matches[:5])  # Limit numbers

        # Remove stop words and short terms
        filtered_keywords = [
            k for k in keywords
            if k.lower() not in self.STOP_WORDS
            and len(k) > 2
            and not k.isdigit()
        ]

        # Sort by length (longer terms are usually more specific)
        filtered_keywords.sort(key=len, reverse=True)

        return filtered_keywords[:20]  # Limit to top 20 keywords

    async def search_codebase(
        self,
        keywords: List[str],
        file_patterns: Optional[List[str]] = None
    ) -> List[FileContext]:
        """
        Search codebase for files relevant to task.

        Args:
            keywords: List of keywords to search for
            file_patterns: Optional file glob patterns

        Returns:
            List of FileContext for relevant files
        """
        if file_patterns is None:
            file_patterns = ['*.py', '*.js', '*.ts', '*.tsx', '*.jsx', '*.java', '*.go', '*.rs']

        relevant_files = []

        # Search for each file pattern
        for pattern in file_patterns:
            try:
                for file_path in self.codebase_path.rglob(pattern):
                    # Skip common non-source directories
                    if any(skip in str(file_path) for skip in self.SKIP_DIRECTORIES):
                        continue

                    # Read file and check for keywords
                    try:
                        stat = file_path.stat()
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        # Check if file contains keywords
                        relevant_lines = []
                        content_lower = content.lower()

                        for keyword in keywords:
                            if keyword.lower() in content_lower:
                                # Find lines containing keyword
                                for line_num, line in enumerate(content.splitlines(), 1):
                                    if keyword.lower() in line.lower():
                                        relevant_lines.append(f"{line_num}: {line.strip()}")
                                        if len(relevant_lines) >= 20:
                                            break
                                if len(relevant_lines) >= 20:
                                    break

                        if relevant_lines:
                            # Determine language
                            ext = file_path.suffix
                            language = self.LANGUAGE_EXTENSIONS.get(ext, 'text')

                            file_context = FileContext(
                                file_path=str(file_path.relative_to(self.codebase_path)),
                                language=language,
                                relevant_lines=relevant_lines[:20],
                                summary=self._summarize_file(content, keywords),
                                size_bytes=stat.st_size,
                                last_modified=datetime.fromtimestamp(stat.st_mtime)
                            )
                            relevant_files.append(file_context)

                    except (UnicodeDecodeError, PermissionError) as e:
                        logger.debug(f"Could not read {file_path}: {e}")
                        continue
                    except Exception as e:
                        logger.debug(f"Error processing {file_path}: {e}")
                        continue

            except Exception as e:
                logger.warning(f"Error searching pattern {pattern}: {e}")
                continue

        # Sort by relevance (number of matching lines)
        relevant_files.sort(key=lambda f: len(f.relevant_lines), reverse=True)

        # Limit to top N files
        return relevant_files[:self.max_files]

    def _summarize_file(self, content: str, keywords: List[str]) -> str:
        """
        Generate summary of file content.

        Looks for docstrings, comments, class/function definitions.

        Args:
            content: File content
            keywords: Keywords to look for

        Returns:
            Summary string
        """
        lines = content.splitlines()

        # Look for docstrings, comments, class/function definitions
        summary_lines = []

        # Check first 100 lines for important patterns
        for line in lines[:100]:
            stripped = line.strip()

            # Python docstrings
            if stripped.startswith('"""') or stripped.startswith("'''"):
                summary_lines.append(stripped[:100])

            # Comments
            elif stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*'):
                summary_lines.append(stripped[:100])

            # Definitions
            elif any(stripped.startswith(prefix) for prefix in [
                'class ', 'def ', 'function ', 'const ', 'let ', 'var ',
                'export ', 'import ', 'interface ', 'type ', 'struct ',
                'func ', 'package ', 'public ', 'private '
            ]):
                summary_lines.append(stripped[:100])

            # Keywords in important lines
            elif any(keyword.lower() in stripped.lower() for keyword in keywords[:5]):
                summary_lines.append(stripped[:100])

            if len(summary_lines) >= 5:
                break

        summary = ' '.join(summary_lines)

        # Truncate if too long
        if len(summary) > 300:
            summary = summary[:300] + '...'

        return summary

    async def search_docs(
        self,
        keywords: List[str]
    ) -> List[DocSection]:
        """
        Search documentation for relevant sections.

        Args:
            keywords: List of keywords to search for

        Returns:
            List of DocSection for relevant documentation
        """
        if not self.docs_path or not self.docs_path.exists():
            return []

        relevant_docs = []

        # Search common doc files
        doc_patterns = ['README*.md', '*.md', 'docs/**/*.md', 'docs/**/*.txt']

        for pattern in doc_patterns:
            try:
                for doc_path in self.docs_path.rglob(pattern):
                    # Skip hidden files
                    if doc_path.name.startswith('.'):
                        continue

                    try:
                        with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        # Check for keywords
                        keyword_matches = sum(
                            1 for keyword in keywords
                            if keyword.lower() in content.lower()
                        )

                        if keyword_matches > 0:
                            # Extract sections
                            sections = self._extract_doc_sections(
                                content,
                                keywords,
                                max_sections=3
                            )

                            for section in sections:
                                doc_section = DocSection(
                                    section_path=str(doc_path.relative_to(self.docs_path)),
                                    title=section['title'],
                                    content=section['content'],
                                    relevance_score=keyword_matches / len(keywords),
                                    heading_level=section.get('level', 1)
                                )
                                relevant_docs.append(doc_section)

                    except Exception as e:
                        logger.debug(f"Could not read {doc_path}: {e}")
                        continue

            except Exception as e:
                logger.debug(f"Error searching docs pattern {pattern}: {e}")
                continue

        # Sort by relevance
        relevant_docs.sort(key=lambda d: d.relevance_score, reverse=True)

        return relevant_docs[:self.max_docs]

    def _extract_doc_sections(
        self,
        content: str,
        keywords: List[str],
        max_sections: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Extract relevant sections from documentation.

        Args:
            content: Documentation content
            keywords: Keywords to search for
            max_sections: Maximum sections to extract

        Returns:
            List of section dictionaries
        """
        sections = []
        lines = content.splitlines()

        for i, line in enumerate(lines):
            # Check if line contains keywords
            if any(keyword.lower() in line.lower() for keyword in keywords):
                # Extract surrounding context
                start = max(0, i - 3)
                end = min(len(lines), i + 10)
                section_content = '\n'.join(lines[start:end])

                # Get section title (nearest heading)
                title = "Unknown Section"
                level = 1
                for j in range(i, max(0, i - 20), -1):
                    if lines[j].startswith('#'):
                        # Count heading level
                        level = len(lines[j]) - len(lines[j].lstrip('#'))
                        title = lines[j].lstrip('#').strip()
                        break

                sections.append({
                    'title': title,
                    'content': section_content,
                    'level': level
                })

                if len(sections) >= max_sections:
                    break

        return sections

    async def extract_conversation_context(
        self,
        conversation_history: Optional[List[Dict]],
        keywords: List[str]
    ) -> Optional[ConversationContext]:
        """
        Extract relevant context from conversation history.

        Args:
            conversation_history: List of conversation messages
            keywords: Keywords to filter by

        Returns:
            ConversationContext if history provided, None otherwise
        """
        if not conversation_history or len(conversation_history) == 0:
            return ConversationContext(
                summary="No conversation history available",
                relevant_messages=[],
                participant_count=0,
                message_count=0
            )

        # Extract relevant messages (those containing keywords)
        relevant_messages = []
        participants = set()

        for msg in conversation_history[-20:]:  # Last 20 messages
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            participants.add(role)

            # Check if message contains keywords
            if any(keyword.lower() in content.lower() for keyword in keywords):
                relevant_messages.append({
                    'role': role,
                    'content': content[:500]  # Truncate long messages
                })

        # Create summary
        if relevant_messages:
            summary_parts = []
            for msg in relevant_messages[:5]:  # Last 5 relevant messages
                role = msg['role']
                content = msg['content'][:200]
                summary_parts.append(f"{role}: {content}")

            summary = ' | '.join(summary_parts)
        else:
            # Fallback: just join recent messages
            recent = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
            summary_parts = []
            for msg in recent:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:200]
                summary_parts.append(f"{role}: {content}")
            summary = ' | '.join(summary_parts)

        return ConversationContext(
            summary=summary,
            relevant_messages=relevant_messages[:10],  # Limit to 10
            participant_count=len(participants),
            message_count=len(conversation_history)
        )

    async def extract_context(
        self,
        task_id: str,
        task_description: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> TaskContext:
        """
        Extract complete context package for task.

        Args:
            task_id: Task identifier
            task_description: Task description
            conversation_history: Optional conversation messages

        Returns:
            TaskContext with all extracted information
        """
        start_time = time.time()

        # Extract keywords
        keywords = self.extract_keywords(task_description)
        logger.info(f"Extracted {len(keywords)} keywords for task {task_id}: {keywords[:5]}")

        # Search codebase
        relevant_files = await self.search_codebase(keywords)
        logger.info(f"Found {len(relevant_files)} relevant files")

        # Search documentation
        relevant_docs = await self.search_docs(keywords)
        logger.info(f"Found {len(relevant_docs)} relevant docs")

        # Extract conversation context
        conversation_context = await self.extract_conversation_context(
            conversation_history,
            keywords
        )

        # Calculate total tokens (rough estimate: 1 token ≈ 4 characters)
        file_chars = sum(len(f.summary) + sum(len(line) for line in f.relevant_lines) for f in relevant_files)
        doc_chars = sum(len(d.content) for d in relevant_docs)
        conv_chars = len(conversation_context.summary) if conversation_context else 0

        total_tokens = (file_chars + doc_chars + conv_chars) // 4

        extraction_time = time.time() - start_time

        return TaskContext(
            task_id=task_id,
            task_description=task_description,
            relevant_files=relevant_files,
            relevant_docs=relevant_docs,
            conversation_context=conversation_context,
            total_tokens=total_tokens,
            extraction_time=extraction_time,
            sources_searched=len(relevant_files) + len(relevant_docs),
            keywords=keywords
        )

    def format_context_for_llm(self, context: TaskContext) -> str:
        """
        Format extracted context for LLM consumption.

        Returns a structured string that can be passed as system prompt
        or context to the LLM for task planning.

        Args:
            context: Extracted task context

        Returns:
            Formatted string for LLM consumption
        """
        parts = [
            f"# Context for Task: {context.task_id}",
            "",
            "## Task Description",
            context.task_description,
            "",
            f"**Extracted Keywords:** {', '.join(context.keywords[:10])}",
            "",
        ]

        # Add file context
        if context.relevant_files:
            parts.append(f"## Relevant Code Files ({len(context.relevant_files)} found)")
            for file_ctx in context.relevant_files[:5]:  # Limit to 5 files
                parts.append(f"\n### {file_ctx.file_path} ({file_ctx.language})")
                parts.append(f"**Size:** {file_ctx.size_bytes:,} bytes")
                parts.append(f"**Summary:** {file_ctx.summary}")

                if file_ctx.relevant_lines:
                    parts.append("**Key lines:**")
                    for line in file_ctx.relevant_lines[:5]:  # Limit to 5 lines
                        parts.append(f"  {line}")
            parts.append("")

        # Add documentation context
        if context.relevant_docs:
            parts.append(f"## Relevant Documentation ({len(context.relevant_docs)} found)")
            for doc in context.relevant_docs[:3]:  # Limit to 3 docs
                parts.append(f"\n### {doc.section_path}")
                parts.append(f"**Section:** {doc.title}")
                parts.append(f"**Relevance:** {doc.relevance_score:.2f}")
                parts.append(f"**Content:**")
                parts.append(doc.content[:500])  # Truncate
                if len(doc.content) > 500:
                    parts.append("...(truncated)")
            parts.append("")

        # Add conversation context
        if context.conversation_context:
            parts.append("## Conversation Context")
            parts.append(f"**Participants:** {context.conversation_context.participant_count}")
            parts.append(f"**Messages Analyzed:** {context.conversation_context.message_count}")
            parts.append(f"**Summary:**")
            parts.append(context.conversation_context.summary)
            parts.append("")

        # Add metadata
        parts.append("## Metadata")
        parts.append(f"**Total Tokens:** {context.total_tokens:,}")
        parts.append(f"**Sources Searched:** {context.sources_searched}")
        parts.append(f"**Extraction Time:** {context.extraction_time:.2f}s")
        parts.append(f"**Extracted At:** {context.extracted_at.isoformat()}")

        return '\n'.join(parts)

    def format_context_compact(self, context: TaskContext) -> str:
        """
        Format context in a compact format for quick reference.

        Args:
            context: Extracted task context

        Returns:
            Compact formatted string
        """
        lines = [
            f"Task: {context.task_id}",
            f"Files: {len(context.relevant_files)}, Docs: {len(context.relevant_docs)}, "
            f"Tokens: {context.total_tokens:,}",
        ]

        if context.relevant_files:
            lines.append("Top files:")
            for f in context.relevant_files[:3]:
                lines.append(f"  - {f.file_path} ({f.language})")

        if context.relevant_docs:
            lines.append("Top docs:")
            for d in context.relevant_docs[:2]:
                lines.append(f"  - {d.section_path}: {d.title}")

        return '\n'.join(lines)

    async def extract_context_compressed(
        self,
        task_id: str,
        task_description: str,
        max_tokens: int = 8000
    ) -> TaskContext:
        """
        Extract and compress context to fit within token limits.

        This is a convenience method that combines extraction and compression.

        Args:
            task_id: Task identifier
            task_description: Task description
            max_tokens: Maximum token limit

        Returns:
            Compressed TaskContext
        """
        # Extract context first
        context = await self.extract_context(task_id, task_description)

        # Import compressor (lazy import to avoid circular dependencies)
        from .token_compressor import TokenCompressor

        # Compress if needed
        compressor = TokenCompressor(max_tokens=max_tokens)
        result = compressor.compress(context, keywords=context.keywords)

        if result.warnings:
            logger.warning(f"Compression warnings: {result.warnings}")

        return result.compressed_context
