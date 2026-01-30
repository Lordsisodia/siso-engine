# Prompt Progression System

This folder tracks the evolution of RALF prompts through versions.

## Structure

```
prompt-progression/
├── research/                    # Prompt engineering research
│   ├── system-prompts-github/   # Downloaded GitHub system prompts collection
│   ├── openai-swarm-ANALYSIS.md
│   ├── google-adk-python-ANALYSIS.md
│   ├── METAGPT-GITHUB-ANALYSIS.md
│   ├── FRAMEWORK-PATTERNS-SYNTHESIS.md
│   └── ... (other framework analyses)
│
└── versions/
    ├── v1/                      # Version 1.0
    │   ├── AGENT.md            # Agent definition
    │   ├── agents/             # Sub-agent prompts
    │   └── IMPROVEMENTS.md     # Feedback & planned improvements
    │
    ├── v2/                      # Version 2.0 (next iteration)
    │   ├── AGENT.md
    │   ├── agents/
    │   └── IMPROVEMENTS.md
    │
    └── vN/                      # Future versions
```

## Current Version

**v2.2** - Agent-2.2 (The Enforcement Release) with:
- **Phase Gate Enforcement**: Mandatory validation before phase progression
- **Context Budget Enforcement**: Auto-actions at 70%/85%/95% thresholds
- **Decision Registry**: Structured decisions with reversibility tracking
- **All 2.1 features**: BMAD + Claude best practices preserved

**Previous Versions:**
- **v2.1** - Agent-2.1 (BMAD + Claude): Combined methodology and best practices
- **v2.0** - Agent-2.0 (Claude-Only): Claude best practices without BMAD
- **v1.0** - Agent-1.3 (BMAD-Enhanced): BMAD methodology without Claude optimizations

## Research Sources

Framework analyses from billion-dollar companies:
- **OpenAI Swarm** - Multi-agent orchestration patterns
- **Google ADK** - Tool use and agent patterns
- **MetaGPT** - Role-based agent frameworks
- **Microsoft Azure AI** - Enterprise agent patterns
- **ByteDance DeerFlow** - Research agent patterns
- **Alibaba AgentScope** - Multi-agent communication

## Version Upgrade Process

1. Review `versions/vN/IMPROVEMENTS.md` for feedback
2. Research new patterns from `research/`
3. Create new version folder `versions/v{N+1}/`
4. Update `AGENT.md` with improvements
5. Document changes in new `IMPROVEMENTS.md`
6. Update root `ralf.md` to point to new version

## Integration with Blackbox5

This progression system integrates with:
- `~/.blackbox5/2-engine/.autonomous/prompts/` - Active prompts
- `~/.blackbox5/5-project-memory/ralf-core/.autonomous/` - RALF project memory
- `~/.blackbox5/ralf.md` - Main entry point
