# Memory System Structure

> Complete map of the runtime/memory/ directory

## Overview

The memory system provides multi-tier persistent storage for agent operations:
- **Working Memory** - Short-term, session-based
- **Agent Memory** - Per-agent persistent storage
- **Episodic Memory** - Long-term event/episode storage
- **Brain** - Knowledge graph (Neo4j + embeddings)
- **Consolidation** - Memory optimization and archiving
- **Importance** - Importance scoring system

## Directory Structure

```
memory/
├── systems/              # Core memory system implementations
│   ├── ProductionMemorySystem.py
│   ├── EnhancedProductionMemorySystem.py
│   ├── AgentMemory.py
│   └── SummaryTier.py
│
├── working/              # Working Memory (short-term)
│   ├── agents/          # Per-agent working memory
│   ├── compact/         # Compressed working data
│   ├── handoffs/        # Agent handoff data
│   ├── kanban/          # Kanban board state
│   └── shared/          # Shared working context
│
├── episodic/             # Episodic Memory (long-term events)
│   ├── Episode.py
│   └── EpisodicMemory.py
│
├── brain/                # Knowledge Graph (Neo4j)
│   ├── api/             # Brain API endpoints
│   ├── databases/       # Database implementations
│   ├── ingest/          # Data ingestion
│   ├── metadata/        # Metadata management
│   ├── query/           # Query interfaces
│   └── README-*.md      # Database-specific docs
│
├── consolidation/        # Memory consolidation
│   └── MemoryConsolidation.py
│
├── importance/           # Importance scoring
│
├── extended/             # Extended memory features
│
├── memory-bank/          # Memory bank storage
│
├── archival/             # Archived memories
│
├── docs/                 # Documentation
│   ├── THREE-TIER-MEMORY-GUIDE.md
│   ├── MEMORY-CONSOLIDATION-COMPLETE.md
│   ├── USAGE.md
│   ├── protocol.md
│   ├── context.md
│   └── information-routing.md
│
├── utils/                # Utilities and demos
│   ├── demo.py
│   ├── validate_production.py
│   └── manifest.yaml
│
├── archive/              # Archived/temp files
│   ├── agent-sessions/   # Demo agent sessions
│   ├── scratchpad.md
│   ├── journal.md
│   ├── tasks.md
│   └── docs-ledger.md
│
├── tests/                # Test suite
│
├── README.md             # Main memory documentation
└── __init__.py
```

## Core Systems

### ProductionMemorySystem.py
Main memory orchestrator that coordinates all memory tiers.

### EnhancedProductionMemorySystem.py
Extended version with additional features and optimizations.

### AgentMemory.py
Per-agent persistent memory management.

### SummaryTier.py
Memory summarization and compression.

## Memory Tiers

| Tier | Location | Purpose | Persistence |
|------|----------|---------|-------------|
| Working | `working/` | Short-term session data | Session |
| Agent | `systems/AgentMemory.py` | Per-agent persistent storage | Permanent |
| Episodic | `episodic/` | Long-term events/episodes | Permanent |
| Brain | `brain/` | Knowledge graph | Permanent |

## Quick Reference

### Find Memory System Code
```
systems/           # Main implementations
```

### Find Working Memory Data
```
working/agents/    # Per-agent working memory
working/shared/    # Shared context
working/kanban/    # Kanban state
```

### Find Long-term Storage
```
episodic/          # Events/episodes
brain/             # Knowledge graph
consolidation/     # Memory optimization
```

### Find Documentation
```
docs/              # All documentation
brain/README-*.md  # Database-specific guides
```

## For AI Agents

**Navigation Tips:**
1. Check `MEMORY-STRUCTURE.md` first when exploring memory/
2. Main system code is in `systems/` (not root)
3. Working data is in `working/` subdirectories
4. Brain/knowledge graph is in `brain/`
5. Documentation is consolidated in `docs/`

**Important Files:**
- `systems/ProductionMemorySystem.py` - Main entry point
- `README.md` - Usage guide
- `docs/THREE-TIER-MEMORY-GUIDE.md` - Architecture guide
