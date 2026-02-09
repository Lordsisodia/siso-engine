# Claude Native Sub-Agents for BlackBox5

**Location:** `2-engine/agents/definitions/claude-native/`

**Purpose:** Sub-agent definitions that work with Claude Code's native Task tool, following GSD (Get-Shit-Done) patterns for thin orchestration and fresh context execution.

---

## Philosophy

These agents follow the GSD principle:

> "The orchestrator never does heavy lifting. It spawns agents, waits, integrates results."

Each agent:
- Gets fresh 200k context (no accumulated garbage)
- Returns brief confirmation (preserves orchestrator context)
- Does one thing well
- Outputs structured data (YAML/JSON, not verbose prose)

---

## Directory Structure

```
claude-native/
├── README.md                    # This file
├── researchers/                 # 4 parallel research agents
│   ├── bb5-stack-researcher.md
│   ├── bb5-architecture-researcher.md
│   ├── bb5-convention-researcher.md
│   └── bb5-risk-researcher.md
└── execution/                   # Task execution agents
    ├── bb5-executor.md
    └── bb5-verifier.md
```

---

## Usage

### 4 Parallel Researchers

Spawn all 4 simultaneously for comprehensive codebase analysis:

```python
# In orchestrator (thin - stays at 30-40% context)
research_tasks = [
    Task(prompt="Analyze auth module", subagent_type="bb5-stack-researcher"),
    Task(prompt="Analyze auth module", subagent_type="bb5-architecture-researcher"),
    Task(prompt="Analyze auth module", subagent_type="bb5-convention-researcher"),
    Task(prompt="Analyze auth module", subagent_type="bb5-risk-researcher"),
]
# All 4 run in parallel with fresh context
```

### Execution Flow

```python
# 1. Execute with fresh context
result = Task(prompt="Implement login", subagent_type="bb5-executor")

# 2. Verify the work
verification = Task(prompt="Verify login", subagent_type="bb5-verifier")

# 3. Brief results preserve orchestrator context
```

---

## Agent Reference

### Researchers

| Agent | Purpose | Output |
|-------|---------|--------|
| `bb5-stack-researcher` | Tech stack, dependencies | YAML: languages, frameworks, versions |
| `bb5-architecture-researcher` | System design, patterns | YAML: components, data flows, interfaces |
| `bb5-convention-researcher` | Coding standards | YAML: naming, style, organization |
| `bb5-risk-researcher` | Pitfalls, edge cases | YAML: risks, anti-patterns, mitigations |

### Execution

| Agent | Purpose | Key Feature |
|-------|---------|-------------|
| `bb5-executor` | Fresh context task execution | XML task input, atomic commits |
| `bb5-verifier` | 3-level verification | Existence → Substantive → Wired |

---

## GSD Patterns Applied

1. **Fresh Context Per Agent** - 200k tokens, zero accumulated garbage
2. **Parallel Where Possible** - 4 researchers run simultaneously
3. **Sequential When Dependent** - Verify after execute
4. **Brief Confirmations** - Status only, not full output
5. **Thin Orchestrator** - Main context stays at 30-40%

---

## Integration with BB5

These agents complement (don't replace) existing BB5 infrastructure:

- **BMAD Skills** - Still used for quick, single-agent tasks
- **RALF** - Can spawn these agents for complex work
- **Orchestrator** - Can use thin mode with these agents
- **Existing Sub-Agents** - Documented ones remain for reference

---

## Source

Based on research from:
- [GSD Framework](https://github.com/glittercowboy/get-shit-done) by @glittercowboy
- BlackBox5 sub-agent architecture research
