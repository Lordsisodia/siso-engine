# BlackBox5 Examples

This directory contains example scripts and demonstrations for the BlackBox5 engine.

## Directory Structure

```
examples/
├── README.md                    # This file
├── autonomous/                  # Autonomous system examples
│   ├── basic_demo.py           # Basic autonomous demo
│   └── redis_latency_test.py   # Redis latency testing
├── integrations/                # Integration examples
│   ├── cloudflare_demo.py      # Cloudflare DNS, Workers, KV, R2
│   ├── github_demo.py          # GitHub issues, PRs, comments
│   ├── github_actions_demo.py  # GitHub Actions workflows
│   ├── mcp_demo.py             # Model Context Protocol
│   ├── notion_demo.py          # Notion pages, databases, blocks
│   ├── obsidian_demo.py        # Obsidian vault operations
│   ├── supabase_demo.py        # Supabase DB, storage, functions
│   ├── vercel_demo.py          # Vercel deployments
│   └── vibe_demo.py            # Vibe Kanban card management
└── orchestration/               # Orchestration examples
    ├── memory_demo.py          # Memory system operations
    ├── state_manager_demo.py   # State management patterns
    └── state_manager_demo_race_conditions.py  # Concurrency handling
```

## Integration Examples

### Cloudflare (`cloudflare_demo.py`)
Demonstrates Cloudflare API integration:
- DNS record management
- Workers deployment
- KV store operations
- R2 storage operations

### GitHub (`github_demo.py`)
Shows GitHub integration patterns:
- Creating issues and pull requests
- Adding comments
- Updating issue status
- CCPM-style progress tracking

### GitHub Actions (`github_actions_demo.py`)
GitHub Actions workflow examples:
- Triggering workflows
- Monitoring workflow runs
- Managing workflow configurations

### MCP (`mcp_demo.py`)
Model Context Protocol demonstrations:
- MCP client initialization
- Tool calling patterns
- Context management

### Notion (`notion_demo.py`)
Notion API integration examples:
- Page creation and management
- Database operations
- Block content manipulation
- Markdown conversion

### Obsidian (`obsidian_demo.py`)
Obsidian vault operations:
- Vault file management
- Note creation and updates
- Metadata handling

### Supabase (`supabase_demo.py`)
Supabase integration patterns:
- Database CRUD operations
- Storage file management
- Edge Function invocation
- Realtime subscriptions

### Vercel (`vercel_demo.py`)
Vercel deployment examples:
- Deployment management
- Domain configuration
- Project settings

### Vibe Kanban (`vibe_demo.py`)
Vibe Kanban card management:
- Card creation and movement
- Status-to-column mapping
- CCPM-style sync patterns
- Progress tracking

## Orchestration Examples

### Memory Demo (`memory_demo.py`)
Memory system operations:
- Working memory management
- Extended memory operations
- Brain episode storage
- Memory queries and retrieval

### State Manager Demo (`state_manager_demo.py`)
State management patterns:
- State initialization
- State transitions
- State persistence
- Error recovery

### Race Condition Fixes (`state_manager_demo_race_conditions.py`)
Concurrency handling examples:
- Race condition prevention
- Lock management
- Atomic operations
- Thread-safe patterns

## Autonomous System Examples

### Basic Demo (`autonomous/basic_demo.py`)
Basic autonomous agent demonstration:
- Agent initialization
- Task execution patterns
- Redis coordination

### Redis Latency Test (`autonomous/redis_latency_test.py`)
Performance testing for Redis coordination:
- Pub/sub latency measurement
- Task queue performance
- Coordinator benchmarking

## Running Examples

Most examples can be run directly:

```bash
# Autonomous examples
python examples/autonomous/basic_demo.py
python examples/autonomous/redis_latency_test.py

# Integration examples
python examples/integrations/github_demo.py
python examples/integrations/notion_demo.py

# Orchestration examples
python examples/orchestration/memory_demo.py
python examples/orchestration/state_manager_demo.py
```

**Note**: Many examples require environment variables for API authentication. Check the individual demo files for required variables.

## Environment Variables

Common environment variables used across examples:

```bash
# GitHub
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_REPO="owner/repo"

# Notion
export NOTION_TOKEN="secret_xxxxxxxxxxxx"

# Supabase
export SUPABASE_PROJECT_REF="your_project_ref"
export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"

# Cloudflare
export CLOUDFLARE_API_TOKEN="your_token"
export CLOUDFLARE_ACCOUNT_ID="your_account_id"

# Vibe Kanban
export VIBE_API_URL="http://localhost:3001"
```

## Adding New Examples

When adding new examples:

1. Place integration demos in `examples/integrations/`
2. Place orchestration demos in `examples/orchestration/`
3. Use descriptive naming: `{integration_name}_demo.py`
4. Include docstring with description and requirements
5. Add entry to this README

## See Also

- [Integration Documentation](../tools/integrations/)
- [Core Orchestration](../core/orchestration/)
- [Runtime Memory](../runtime/memory/)
