# Three-Tier Memory System - Complete Guide

## Overview

BlackBox5 now features a complete **three-tier memory hierarchy** based on research from MemoryOS, MemGPT, and H-MEM (2025-2026). This system provides efficient memory management with automatic consolidation and intelligent retrieval.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    THREE-TIER MEMORY HIERARCHY                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Tier 1     │    │   Tier 2     │    │   Tier 3     │      │
│  │ WorkingMemory│───▶│  SummaryTier │───▶│ PersistentMem│      │
│  │              │    │              │    │              │      │
│  │ Last 10 msgs │    │ Last 10 sums │    │ All messages │      │
│  │ Fast access  │    │ Mid-term     │    │ Long-term    │      │
│  │ Detailed     │    │ Compressed   │    │ Full detail  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│        │                    │                    │             │
│        └────────────────────┴────────────────────┘             │
│                            │                                   │
│                            ▼                                   │
│                   Memory Consolidation                         │
│                   (Every 10 messages)                          │
│                   Preserves importance                         │
│                   LLM-based summarization                      │
└─────────────────────────────────────────────────────────────────┘
```

## Tier Details

### Tier 1: WorkingMemory (Immediate Context)

**Purpose**: Keep recent messages accessible for immediate context

**Configuration**:
- `max_messages`: 10 (default) - Messages to keep detailed
- Storage: In-memory (deque)
- Access: O(1) for recent messages

**Usage**:
```python
from storage.EnhancedProductionMemorySystem import create_enhanced_memory_system

memory = create_enhanced_memory_system(project_path)

# Add messages
memory.add(create_message(role="user", content="Hello"))

# Get immediate context
context = memory.working.get_context(limit=10)
```

**When to use**:
- Recent conversation context (last 10 messages)
- Fast access to current state
- Immediate response generation

---

### Tier 2: SummaryTier (Mid-Term Context) ⭐ NEW

**Purpose**: Store consolidated summaries for mid-term context without hitting persistent storage

**Configuration**:
- `max_summaries`: 10 (default) - Summaries to keep
- Storage: In-memory (deque with ConsolidatedSummary objects)
- Access: Faster than querying persistent storage

**Key Features**:
- Automatic population from memory consolidation
- Rich metadata (task_ids, agent_ids, timestamps)
- Keyword search support
- Context string generation

**Usage**:
```python
# Get summary tier stats
stats = memory.get_summary_tier_stats()
print(f"Summaries: {stats['count']}/{stats['max_summaries']}")

# Get summaries
summaries = memory.get_summary_tier_summaries(limit=5)

# Search summaries
results = memory.search_summaries("authentication", limit=3)

# Get formatted context string
context = memory.summary_tier.get_context_string(limit=5)
```

**When to use**:
- Mid-term conversation context (last 10 consolidation cycles)
- Faster than querying persistent storage
- Understanding conversation history without full detail
- Token-efficient context retrieval

**Data Structure**:
```python
@dataclass
class ConsolidatedSummary:
    summary: str                      # Compressed summary
    consolidated_count: int           # How many messages summarized
    oldest_timestamp: str             # Timestamp range
    newest_timestamp: str
    consolidated_at: str              # When consolidation happened
    metadata: Dict[str, Any]          # task_ids, agent_ids, etc.
```

---

### Tier 3: PersistentMemory (Long-Term Storage)

**Purpose**: Store all messages ever for long-term retention

**Configuration**:
- Storage: SQLite database
- Location: `{project_path}/.blackbox/memory/{project_name}/messages.db`
- Access: Full-text search, SQL queries

**Usage**:
```python
# Query persistent memory
messages = memory.persistent.get_messages(limit=100)

# Filter by task/agent
messages = memory.persistent.get_messages(
    task_id="task-123",
    agent_id="agent-456"
)

# Full-text search
results = memory.persistent.search("authentication error")
```

**When to use**:
- Historical analysis
- Audit trails
- Long-term pattern discovery
- Full message reconstruction

---

## Memory Consolidation

### How It Works

1. **Trigger**: Every 10 messages added (configurable via `max_messages`)
2. **Split**:
   - Recent: Last 10 messages → Keep detailed in WorkingMemory
   - Old: Messages beyond last 10 → Summarize
3. **Preserve**: High-importance messages (importance ≥ 0.7) → Keep in WorkingMemory
4. **Summarize**: Old messages → Generate summary (LLM or simple)
5. **Store**:
   - **SummaryTier**: Rich ConsolidatedSummary object (new!)
   - **WorkingMemory**: Lightweight consolidated message

### Configuration

```python
from storage.EnhancedProductionMemorySystem import create_enhanced_memory_system
from storage.consolidation.MemoryConsolidation import ConsolidationConfig

config = ConsolidationConfig(
    max_messages=10,              # Trigger consolidation
    recent_keep=10,               # Keep last N detailed
    min_importance=0.7,           # Preserve high-importance
    auto_consolidate=True,        # Auto-trigger
    max_summary_length=500        # Max summary chars
)

memory = create_enhanced_memory_system(
    project_path=Path("/path/to/project"),
    enable_consolidation=True,
    consolidation_config=config
)
```

### Consolidation Flow

```python
# Add messages
for i in range(15):
    memory.add(create_message(role="user", content=f"Message {i}"))

# Automatic consolidation triggered at message 10
# SummaryTier now has 1 summary
# WorkingMemory has: preserved important + 1 consolidated + 10 recent

# Force manual consolidation
result = memory.force_consolidate()
print(result)
# {
#   "status": "success",
#   "original_count": 15,
#   "consolidated_count": 5,
#   "preserved_count": 2,
#   "recent_count": 10,
#   "final_count": 13,
#   "summary_length": 245,
#   "token_reduction": 2
# }
```

---

## Complete Usage Examples

### Basic Setup

```python
from pathlib import Path
from storage.EnhancedProductionMemorySystem import create_enhanced_memory_system
from storage.ProductionMemorySystem import create_message

# Create memory system with three tiers
memory = create_enhanced_memory_system(
    project_path=Path("./my-project"),
    project_name="my-agent",
    enable_consolidation=True,    # Enable auto-consolidation
    max_summaries=10             # Tier 2 capacity
)

# Add messages
memory.add(create_message(role="user", content="Hello!"))
memory.add(create_message(role="assistant", content="Hi there!"))
```

### Getting Context

```python
# Option 1: WorkingMemory only (immediate context)
context = memory.working.get_context(limit=10)

# Option 2: Three-tier context (includes summaries)
context = memory.get_three_tier_context(
    limit=10,
    include_summaries=True
)
# Returns:
# === IMMEDIATE CONTEXT (WorkingMemory) ===
# user: Message 9
# assistant: Response 9
# ...
#
# === MID-TERM CONTEXT (SummaryTier) ===
# [CONSOLIDATED SUMMARY 1] (5 messages from ...)
# Summary of discussion about authentication
# ...
```

### Semantic Retrieval

```python
# Get context with semantic retrieval
context = memory.get_context(
    query="authentication issues",
    limit=10,
    strategy="hybrid",          # 50% recent + 30% semantic + 20% importance
    min_importance=0.5
)

# Search summaries
results = memory.search_summaries("authentication", limit=3)
for summary in results:
    print(f"{summary.consolidated_count} messages: {summary.summary}")
```

### Statistics and Monitoring

```python
# WorkingMemory stats
working_size = memory.working.size()

# SummaryTier stats
summary_stats = memory.get_summary_tier_stats()
print(f"Summaries: {summary_stats['count']}/{summary_stats['max_summaries']}")
print(f"Utilization: {summary_stats['utilization']:.1%}")
print(f"Total consolidated: {summary_stats['total_messages_consolidated']}")

# Consolidation stats
consolidation_stats = memory.get_consolidation_stats()
print(f"Should consolidate: {consolidation_stats['should_consolidate']}")
print(f"Can consolidate: {consolidation_stats['can_consolidate']}")
```

---

## Research Validation

This implementation is based on research from 80+ sources (2025-2026):

### MemoryOS (2025)
- Three-tier hierarchy: Buffer → Summaries → Long-term
- **Implemented**: ✅ WorkingMemory → SummaryTier → PersistentMemory

### MemGPT (2024)
- OS-inspired memory management
- Fixed-size buffers with overflow to long-term
- **Implemented**: ✅ Deque-based storage with automatic consolidation

### H-MEM (2025)
- Hierarchical memory for agents
- Importance-based retention
- **Implemented**: ✅ Importance scoring with configurable thresholds

### mem0.ai (2025)
- 90% token reduction through semantic retrieval
- Automatic summarization
- **Implemented**: ✅ Semantic retrieval, auto-consolidation every 10 messages

---

## Performance Characteristics

### Memory Usage

- **WorkingMemory**: ~1-2 MB (10 messages × 2 KB per message)
- **SummaryTier**: ~50-100 KB (10 summaries × 5-10 KB per summary)
- **PersistentMemory**: Grows with usage (SQLite with compression)

### Token Efficiency

Without consolidation:
- 100 messages × 200 tokens = 20,000 tokens

With consolidation (10 cycles):
- 10 recent messages × 200 tokens = 2,000 tokens
- 10 summaries × 100 tokens = 1,000 tokens
- **Total**: 3,000 tokens (85% reduction)

### Access Speed

- **WorkingMemory**: O(1) - Immediate access
- **SummaryTier**: O(1) - Immediate access
- **PersistentMemory**: O(log n) - Indexed SQL query

---

## API Reference

### EnhancedProductionMemorySystem

```python
class EnhancedProductionMemorySystem:
    def __init__(
        self,
        project_path: Path,
        max_working_messages: int = 100,
        project_name: str = "default",
        enable_consolidation: bool = False,
        max_summaries: int = 10  # NEW: SummaryTier size
    )

    # Three-tier context
    def get_three_tier_context(
        self,
        limit: int = 10,
        include_summaries: bool = True,
        query: Optional[str] = None,
        strategy: str = "recent",
        min_importance: float = 0.0
    ) -> str

    # SummaryTier methods (NEW)
    def get_summary_tier_stats(self) -> Dict[str, Any]
    def get_summary_tier_summaries(
        limit: Optional[int] = None,
        after_timestamp: Optional[str] = None
    ) -> List[ConsolidatedSummary]
    def search_summaries(
        query: str,
        limit: int = 5
    ) -> List[ConsolidatedSummary]

    # Consolidation
    async def consolidate(self) -> Dict[str, Any]
    def force_consolidate(self) -> Dict[str, Any]
```

### SummaryTier

```python
class SummaryTier:
    def __init__(self, max_summaries: int = 10)

    def add_summary(self, summary: ConsolidatedSummary) -> None
    def get_summaries(
        limit: Optional[int] = None,
        after_timestamp: Optional[str] = None
    ) -> List[ConsolidatedSummary]
    def get_latest_summary(self) -> Optional[ConsolidatedSummary]
    def get_context_string(self, limit: Optional[int] = None) -> str
    def find_relevant_summaries(
        query: str,
        limit: int = 5
    ) -> List[ConsolidatedSummary]
    def get_stats(self) -> Dict[str, Any]
    def size(self) -> int
    def clear(self) -> None
```

### ConsolidatedSummary

```python
@dataclass
class ConsolidatedSummary:
    summary: str                      # Compressed summary text
    consolidated_count: int           # Number of messages summarized
    oldest_timestamp: str             # Oldest message timestamp
    newest_timestamp: str             # Newest message timestamp
    consolidated_at: str              # When consolidation happened
    metadata: Dict[str, Any]          # task_ids, agent_ids, etc.

    def to_dict(self) -> Dict[str, Any]
    @classmethod
    def from_dict(cls, data: Dict) -> ConsolidatedSummary
```

---

## Migration Guide

### From Two-Tier to Three-Tier

**Before** (Two-Tier):
```python
memory = create_enhanced_memory_system(
    project_path=Path("./project"),
    enable_consolidation=True
)

# Only WorkingMemory + PersistentMemory
context = memory.get_context(limit=10)
```

**After** (Three-Tier):
```python
memory = create_enhanced_memory_system(
    project_path=Path("./project"),
    enable_consolidation=True,
    max_summaries=10  # NEW: Configure SummaryTier
)

# Use three-tier context
context = memory.get_three_tier_context(limit=10)

# Or access SummaryTier directly
summaries = memory.get_summary_tier_summaries()
```

### Backward Compatibility

All existing APIs continue to work:
- `memory.get_context()` - WorkingMemory only
- `memory.working.get_context()` - WorkingMemory only
- `memory.persistent.get_messages()` - PersistentMemory only

**New APIs**:
- `memory.get_three_tier_context()` - All three tiers
- `memory.get_summary_tier_stats()` - SummaryTier stats
- `memory.search_summaries()` - Search summaries

---

## Troubleshooting

### Consolidation Not Running

**Problem**: Summaries not appearing in SummaryTier

**Solution**:
```python
# Check consolidation is enabled
stats = memory.get_consolidation_stats()
print(f"Enabled: {stats.get('enabled', False)}")

# Check if consolidation should run
print(f"Should consolidate: {stats['should_consolidate']}")
print(f"Can consolidate: {stats['can_consolidate']}")

# Force manual consolidation
result = memory.force_consolidate()
print(result)
```

### SummaryTier Empty

**Problem**: `memory.summary_tier.size()` returns 0

**Solution**:
- Add at least 20 messages (10 + 10 to trigger consolidation)
- Wait for auto-consolidation (every 10 messages)
- Or force consolidation: `memory.force_consolidate()`

### Context Too Large

**Problem**: Token count exceeds limits

**Solution**:
```python
# Use three-tier context with tighter limits
context = memory.get_three_tier_context(
    limit=5,              # Fewer messages from WorkingMemory
    include_summaries=True  # But keep summaries
)

# Or reduce SummaryTier size
memory = create_enhanced_memory_system(
    project_path=Path("./project"),
    max_summaries=5  # Fewer summaries
)
```

---

## Best Practices

### 1. Configuration Tuning

**For token efficiency** (aggressive compression):
```python
config = ConsolidationConfig(
    max_messages=10,      # Consolidate frequently
    recent_keep=5,        # Keep fewer recent
    min_importance=0.8    # Only preserve very important
)
```

**For context retention** (more detail):
```python
config = ConsolidationConfig(
    max_messages=20,      # Consolidate less often
    recent_keep=15,       # Keep more recent
    min_importance=0.5    # Preserve moderately important
)
```

### 2. SummaryTier Sizing

```python
# Small projects (minimal history)
max_summaries=5  # ~50-100 KB

# Medium projects (typical usage)
max_summaries=10  # ~100-200 KB (default)

# Large projects (extensive history)
max_summaries=20  # ~200-400 KB
```

### 3. Query Patterns

```python
# For immediate response generation
context = memory.working.get_context(limit=10)

# For understanding conversation history
context = memory.get_three_tier_context(
    limit=10,
    include_summaries=True
)

# For research/analysis
messages = memory.persistent.get_messages(
    task_id="task-123",
    limit=1000
)
```

---

## Testing

Run the three-tier memory test suite:

```bash
cd .blackbox5/2-engine/03-knowledge/storage
python -m pytest tests/test_three_tier_memory.py -v
```

Test coverage:
- SummaryTier creation and operations
- Three-tier integration
- Memory consolidation with SummaryTier
- Importance preservation
- Realistic agent workflows

---

## Future Enhancements

Potential improvements (not yet implemented):

1. **Vector Embeddings**: Semantic search in SummaryTier
2. **Adaptive Thresholds**: Dynamic consolidation triggers
3. **Cross-Session Memory**: Persistent SummaryTier across restarts
4. **Hierarchical Summaries**: Summaries of summaries
5. **LLM-Based Importance**: Better importance scoring with LLM

---

## References

- **MemoryOS (2025)**: Three-tier hierarchy architecture
- **MemGPT (2024)**: OS-inspired memory management
- **H-MEM (2025)**: Hierarchical memory for agents
- **mem0.ai (2025)**: 90% token reduction through semantic retrieval
- **REMem (2025)**: Episodic memory with semantic indexing

## Version History

- **2026-01-19**: Three-tier memory implementation complete
  - ✅ SummaryTier created
  - ✅ MemoryConsolidation integration
  - ✅ EnhancedProductionMemorySystem updates
  - ✅ Test suite created
  - ✅ Documentation complete

---

## Quick Reference

```python
# Setup
from pathlib import Path
from storage.EnhancedProductionMemorySystem import create_enhanced_memory_system
from storage.ProductionMemorySystem import create_message

memory = create_enhanced_memory_system(
    project_path=Path("./project"),
    enable_consolidation=True,
    max_summaries=10
)

# Add messages
memory.add(create_message(role="user", content="Hello"))

# Get context (three-tier)
context = memory.get_three_tier_context(limit=10)

# Check stats
stats = memory.get_summary_tier_stats()
print(f"Summaries: {stats['count']}/{stats['max_summaries']}")

# Search summaries
results = memory.search_summaries("query", limit=5)
```

**That's it!** You now have a complete three-tier memory system with automatic consolidation, efficient retrieval, and token optimization.
