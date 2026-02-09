# Client Libraries

> Client libraries for interacting with BlackBox5 agents and AI models

## Overview

The `client/` directory provides Python client libraries for:
- **AgentClient** - Generic agent client factory with caching and capability detection
- **ClaudeCodeClient** - Execute tasks via Claude Code CLI with MCP profile support
- **GLMClient** - GLM API client (Zhipu AI) with token optimization
- **TokenOptimizer** - First-principles token optimization for cost reduction
- **ClaudeCodeAgentMixin** - Mixin to add Claude Code execution to any agent

## File Structure

```
client/
├── __init__.py                    # Package marker
├── AgentClient.py                 # Generic agent client factory
├── ClaudeCodeClient.py            # Claude Code CLI client
├── ClaudeCodeAgentMixin.py        # Agent mixin for Claude Code execution
├── GLMClient.py                   # GLM API client
├── TokenOptimizer.py              # Token optimization engine
├── output_format.py               # Agent output format instructions
├── add_output_format_to_agents.py # Migration script for output format
├── test_claude_code_format.py     # Tests for Claude Code format
├── test_output_format.py          # Tests for output format
└── TOKEN-OPTIMIZATION-GUIDE.md    # Token optimization documentation
```

## Components

### AgentClient.py
Generic agent client factory adapted from Auto-Claude:
- Project capability detection (Electron, Tauri, Expo, React Native, etc.)
- Tool permission management per agent type
- Project caching with 5-minute TTL
- MCP server configuration support

**Key Functions:**
- `create_client(project_dir, model, agent_type)` - Create agent configuration
- `detect_project_capabilities(project_index)` - Detect project frameworks
- `get_tools_for_agent(agent_type, capabilities)` - Get allowed tools
- `invalidate_project_cache(project_dir)` - Clear cache

### ClaudeCodeClient.py
Python interface to execute tasks through Claude Code CLI:
- Auto-detects MCP profiles based on task keywords
- Synchronous and asynchronous execution
- File creation tracking
- Timeout and error handling

**MCP Profiles:**
| Profile | Startup | MCP Servers | Best For |
|---------|---------|-------------|----------|
| minimal | ~1s | None | Pure coding |
| filesystem | ~2s | filesystem | File operations |
| standard | ~5s | filesystem, fetch, search | APIs + web |
| data | ~10s | +context7, wikipedia | Research |
| automation | ~15s | +playwright, chrome | Browser automation |
| full | ~30s | All | Everything |

**Usage:**
```python
from client.ClaudeCodeClient import ClaudeCodeClient

client = ClaudeCodeClient()
result = client.execute(
    prompt="Implement user authentication",
    mcp_profile="standard",  # or auto-detect
    timeout=300
)
```

### GLMClient.py
GLM API client (Zhipu AI) compatible with BlackBox5:
- Drop-in replacement for Anthropic Claude API
- Prompt compression via LLMLingua
- Token optimization integration
- Streaming support
- Mock client for testing

**Models:** glm-4.7, glm-4-plus, glm-4-air, glm-4-flash, glm-4-long

**Usage:**
```python
from client.GLMClient import GLMClient

client = GLMClient(api_key="your-key")
response = client.create_optimized(
    system_prompt="You are an expert...",
    agent_persona="Manager agent...",
    conversation_history=history,
    code_context=code,
    user_query="Build API",
    task_type='implement'
)
```

### TokenOptimizer.py
First-principles token optimization (50-70% reduction):
- Client-side prompt caching
- Token-aware conversation trimming
- Dynamic budget allocation per task type
- Message consolidation

**Task Type Budgets:**
| Type | Input | Output | Use Case |
|------|-------|--------|----------|
| classify | 8K | 256 | Classification |
| quick_fix | 16K | 1K | Bug fixes |
| implement | 32K | 4K | Feature dev |
| review | 24K | 2K | Code review |
| refactor | 64K | 4K | Refactoring |
| coordinate | 128K | 8K | Orchestration |

### ClaudeCodeAgentMixin.py
Mixin to add Claude Code CLI execution to any BaseAgent:
- `execute_with_claude()` - Execute tasks via Claude Code
- `build_claude_prompt()` - Build structured prompts
- Automatic output format enforcement

**Usage:**
```python
from agents.framework.base_agent import BaseAgent
from client.ClaudeCodeAgentMixin import ClaudeCodeAgentMixin

class MyAgent(BaseAgent, ClaudeCodeAgentMixin):
    async def execute(self, task):
        return await self.execute_with_claude(task.description)
```

### output_format.py
Standardized output format for agent-to-agent communication:
```markdown
<output>
{
  "status": "success|partial|failed",
  "summary": "One sentence description",
  "deliverables": ["file1.ts"],
  "next_steps": ["action1"],
  "metadata": {"agent": "name", "task_id": "id"}
}
---
[Human-readable explanation]
</output>
```

## Related Components

- **AgentOutputBus** (`../AgentOutputBus.py`) - Routes agent outputs
- **AgentOutputParser** (`../AgentOutputParser.py`) - Parses structured outputs
- **Handlers** (`../handlers/`) - Process outputs (Kanban, notifications, etc.)

## Documentation

See [TOKEN-OPTIMIZATION-GUIDE.md](./TOKEN-OPTIMIZATION-GUIDE.md) for detailed token optimization usage.
