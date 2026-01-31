# BlackBox5 Skills

This directory contains all skills for the BlackBox5 system, organized following the [Anthropic Agent Skills Standard](https://docs.anthropic.com/claude/skills).

## Structure

Each skill has its own folder containing:

```
skill-name/
├── SKILL.md              # Required: Skill definition with YAML frontmatter
├── scripts/              # Optional: Executable scripts
├── references/           # Optional: Documentation and context
└── assets/               # Optional: Templates, images, etc.
```

## Skills Index

### BMAD Agent Skills

| Skill | Agent | Description |
|-------|-------|-------------|
| [bmad-pm](bmad-pm/) | John | Product Manager - PRD creation and requirements |
| [bmad-architect](bmad-architect/) | Winston | Architect - System design and ADRs |
| [bmad-analyst](bmad-analyst/) | Mary | Business Analyst - Research and analysis |
| [bmad-sm](bmad-sm/) | Bob | Scrum Master - Process and coordination |
| [bmad-ux](bmad-ux/) | Sally | UX Designer - User experience and design |
| [bmad-dev](bmad-dev/) | Amelia | Developer - Implementation and coding |
| [bmad-qa](bmad-qa/) | Quinn | QA Engineer - Testing and quality |
| [bmad-tea](bmad-tea/) | TEA | Test Architect - Test strategy and infrastructure |
| [bmad-quick-flow](bmad-quick-flow/) | Barry | Solo Developer - Fast path for simple tasks |
| [bmad-planning](bmad-planning/) | Planner | Planning Agent - Task breakdown and organization |

### Protocol & Framework Skills

| Skill | Description |
|-------|-------------|
| [superintelligence-protocol](superintelligence-protocol/) | Complex problem-solving protocol |
| [continuous-improvement](continuous-improvement/) | Systematic self-improvement |
| [run-initialization](run-initialization/) | Run setup and documentation |

### Utility Skills

| Skill | Description |
|-------|-------------|
| [web-search](web-search/) | Web search via SearXNG |
| [codebase-navigation](codebase-navigation/) | Navigate and understand codebases |
| [supabase-operations](supabase-operations/) | Database operations for Supabase |

### Core System Skills

| Skill | Description |
|-------|-------------|
| [truth-seeking](truth-seeking/) | Validate assumptions and verify facts |
| [git-commit](git-commit/) | Safely commit changes to git |
| [task-selection](task-selection/) | Select next task from STATE.yaml |
| [state-management](state-management/) | Update STATE.yaml with progress |

### Infrastructure Skills

| Skill | Description |
|-------|-------------|
| [ralf-cloud-control](ralf-cloud-control/) | Manage RALF agents in Kubernetes |
| [github-codespaces-control](github-codespaces-control/) | Spawn agents in GitHub Codespaces |
| [legacy-cloud-control](legacy-cloud-control/) | Control Legacy agents in K8s |

## SKILL.md Format

All skills use YAML frontmatter with the following fields:

```yaml
---
name: skill-name                    # Unique identifier (lowercase, hyphens)
description: Clear description      # One-line description for discovery
category: agent|protocol|utility|infrastructure
trigger: When to use this skill
inputs:
  - name: input_name
    type: string|document|code
    description: What this input is
outputs:
  - name: output_name
    type: string|document|code
    description: What this output is
commands:                           # Optional: for agent skills
  - CP
  - VP
---
```

## Usage

Skills are automatically discovered and loaded by the SkillRouter. To use a skill:

1. The router analyzes the task description
2. Matches against skill keywords and triggers
3. Loads the appropriate SKILL.md
4. Executes according to the skill's instructions

## Adding New Skills

1. Create a new folder: `mkdir my-skill/`
2. Add SKILL.md with YAML frontmatter
3. Add any scripts, references, or assets
4. Update this README
5. The skill will be automatically discovered

## Related

- [Skill Router](../lib/skill_router.py) - Automatic skill routing
- [CLAUDE.md](../../../CLAUDE.md) - User instructions
