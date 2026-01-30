# System Prompts Collection (GitHub)

This folder is for downloaded system prompts from GitHub repositories.

## Expected Contents

Place downloaded system prompt collections here, such as:

- `awesome-system-prompts/` - Curated system prompts from various AI systems
- `claude-system-prompts/` - Anthropic Claude system prompts
- `gpt-system-prompts/` - OpenAI GPT system prompts
- `company-system-prompts/` - Collection from major AI companies

## Sources to Download

1. **f/awesome-system-prompts** - Community collection of system prompts
2. **Company leak repositories** - Historical system prompt leaks
3. **AI research papers** - Academic system prompt patterns
4. **Discord/Reddit collections** - Community gathered prompts

## Usage

These prompts are for research purposes to understand:
- Role definition patterns
- Constraint specification techniques
- Tool use instruction formats
- Safety and alignment approaches
- Multi-agent orchestration patterns

## Integration

Insights from these prompts should be:
1. Analyzed for patterns
2. Documented in framework analysis files
3. Incorporated into version upgrades
4. Referenced in IMPROVEMENTS.md

## Contents

### Claude System Prompts

| File | Source | Description |
|------|--------|-------------|
| `claude-sonnet-3.7.md` | [dontriskit/awesome-ai-system-prompts](https://github.com/dontriskit/awesome-ai-system-prompts) | Claude 3.7 Sonnet full system prompt with reasoning mode |
| `claude-code.md` | [dontriskit/awesome-ai-system-prompts](https://github.com/dontriskit/awesome-ai-system-prompts) | Claude Code CLI system prompt |
| `claude-math-reasoning.md` | [langgptai/awesome-claude-prompts](https://github.com/langgptai/awesome-claude-prompts) | Math reasoning patterns and meta-prompts |

### Piebald AI - Claude Code System Prompts

| File | Source | Description |
|------|--------|-------------|
| `piebald-task-tool.md` | [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Task tool agent - ONE TASK PER LOOP pattern |
| `piebald-explore-agent.md` | [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Explore subagent - read-only file search |
| `piebald-plan-mode-enhanced.md` | [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Plan mode agent - 4-step planning process |
| `piebald-agent-architect.md` | [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Agent creation specialist - JSON output format |
| `piebald-remember-skill.md` | [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | /remember skill - pattern extraction |
| `piebald-bash-safety.md` | [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Bash command injection detection |
| `piebald-main-system-prompt.md` | [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Core identity and capabilities |
| `piebald-doing-tasks.md` | [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Task execution guidelines |
| `piebald-task-management.md` | [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | TodoWrite usage patterns |
| `piebald-tone-and-style.md` | [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Communication style rules |
| `piebald-tool-usage-policy.md` | [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Parallel vs sequential tool use |
| `piebald-todowrite-tool.md` | [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | TodoWrite tool description |
| `piebald-plan-mode-5-phase.md` | [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Complete 5-phase planning process |
| `piebald-hooks-configuration.md` | [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Hooks system for lifecycle events |

## Key Insights for RALF

### From Claude 3.7 Sonnet
- **Extended thinking mode**: Allows reasoning before responding
- **Concise by default**: Shortest answer possible
- **Active participant**: Can lead conversation

### From Claude Code
- **Minimal tokens**: Minimize output while maintaining quality
- **No comments unless asked**: Clean code focus
- **Parallel tool use**: Efficiency through parallelization
- **Never commit unless asked**: Safety constraint

### For Math/Reasoning
- Use `<thinking>` tags for complex problems
- Step-by-step breakdown for verification
- Error checking patterns for validation

### From Piebald AI Collection (Most Relevant for RALF)

**Task Tool Pattern:**
- ONE TASK PER LOOP - do what has been asked, nothing more/nothing less
- Absolute paths only (cwd resets between bash calls)
- No emojis, no colons before tool calls

**Explore Subagent:**
- Read-only mode - STRICT prohibition on file modifications
- Parallel tool calls for speed
- Fast agent pattern - return output as quickly as possible

**Plan Mode:**
- 4-step process: Understand → Explore → Design → Detail
- Must identify 3-5 critical files for implementation
- Read-only during planning phase

**Agent Creation:**
- JSON output: `{identifier, whenToUse, systemPrompt}`
- Include usage examples in whenToUse field
- 2-4 word hyphenated identifiers

**Remember Skill:**
- Pattern threshold: must appear in 2+ sessions
- Use AskUserQuestion tool for ALL confirmations
- Never ask questions via plain text

**Bash Safety:**
- Command prefix detection
- Command injection detection returns `command_injection_detected`
- Prefix-based allowlisting for safety

**Task Management:**
- Mark todos complete IMMEDIATELY (don't batch)
- Exactly ONE `in_progress` task at any time
- Never mark complete if: tests failing, errors unresolved, partial implementation

**Tool Usage:**
- Parallel when independent, sequential when dependent
- Use specialized tools over bash
- NEVER use bash to communicate to user
- ALWAYS use Task tool for exploration (not direct search)

**Plan Mode (5 Phase):**
- Phase 1: Launch explore agents in parallel
- Phase 2: Design with Plan agent
- Phase 3: Review and clarify
- Phase 4: Write final plan
- Phase 5: ExitPlanMode to request approval

**Tone & Style:**
- NO time estimates ever
- Prioritize accuracy over validating user's beliefs
- Objective guidance over false agreement
- No emojis unless requested

**Hooks System:**
- PreToolUse for validation/blocking
- PostToolUse for logging/testing
- Stop hooks for cleanup
- Agent hooks for verification

## Sources

1. [dontriskit/awesome-ai-system-prompts](https://github.com/dontriskit/awesome-ai-system-prompts) - 30+ AI system prompts including Claude, GPT, Cursor, etc.
2. [langgptai/awesome-claude-prompts](https://github.com/langgptai/awesome-claude-prompts) - 100+ Claude-specific prompts
3. [f/awesome-chatgpt-prompts](https://github.com/f/awesome-chatgpt-prompts) - Original prompt library (143k+ stars)
4. [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) - Complete Claude Code agent prompts (60+ files)

---

**Last Updated:** 2026-01-30
