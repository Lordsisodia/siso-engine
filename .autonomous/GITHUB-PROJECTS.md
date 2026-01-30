# RALF GitHub Projects Collection

This document catalogs the GitHub projects stored in `.docs/github/` that are relevant to the RALF autonomous agent framework and the "rough loop" concept.

## Projects

### 1. [Ralphy](https://github.com/michaelshimeles/ralphy)
**Location:** [`.docs/github/ralphy/`](./.docs/github/ralphy/)
**Stars:** 2.1k | **Forks:** 263
**Language:** TypeScript (75.1%), Shell (23.9%)

Autonomous AI coding loop that runs AI agents on tasks until done. This is the original "Ralph Wiggum" setup - a bash script that loops various AI CLIs until your PRD is complete.

**Key Capabilities:**
- Single task mode: `ralphy "add dark mode"`
- PRD mode: Works through task lists from Markdown, YAML, JSON, or GitHub Issues
- Multi-engine support: Claude Code, OpenCode, Cursor, Codex, Qwen-Code, Factory Droid, GitHub Copilot, Gemini CLI
- Parallel execution with isolated git worktrees (configurable agent count)
- Branch-per-task workflow with optional PR creation
- Browser automation via agent-browser
- Webhook notifications (Discord, Slack, custom)
- Sandbox mode for faster operation on large monorepos
- Project config with rules and boundaries

**Latest Version:** v4.7.1

---

### 2. [Ralph Orchestrator](https://github.com/mikeyobrien/ralph-orchestrator)
**Location:** [`.docs/github/ralph-orchestrator/`](./.docs/github/ralph-orchestrator/)
**Stars:** 1.5k | **Forks:** 163
**Language:** Rust (74.6%), TypeScript (21.4%), Python (2.8%)

A hat-based orchestration framework that keeps AI agents in a loop until the task is done. An improved implementation of the Ralph Wiggum technique with a modern Rust 2.0 architecture.

**Key Capabilities:**
- **Hat System**: Specialized personas (architect, developer, tester, reviewer) coordinating through events
- **Multi-Backend Support**: Claude Code, Kiro, Gemini CLI, Codex, Amp, Copilot CLI, OpenCode
- **Backpressure Gates**: Reject incomplete work (tests, lint, typecheck must pass before proceeding)
- **Memories & Tasks**: Persistent learning system and runtime work tracking
- **31 Presets**: TDD, spec-driven, debugging, and more pre-configured workflows
- **Web Dashboard (Alpha)**: Monitor and manage orchestration loops via browser
- **RObot (Human-in-the-Loop)**: Telegram integration for bidirectional communication (agents can ask questions, humans can provide proactive guidance)
- **Interactive Planning**: `ralph plan` for PDD sessions creates requirements.md, design.md, implementation-plan.md
- **Event-Driven Architecture**: Hats coordinate through event system for flexible agent orchestration
- **Multiple Install Methods**: npm, Homebrew, or Cargo

**Latest Version:** v2.4.1

---

### 3. [Ralphex](https://github.com/umputun/ralphex)
**Location:** [`.docs/github/ralphex/`](./.docs/github/ralphex/)
**Stars:** 163 | **Forks:** 17
**Language:** Go (82.3%), JavaScript (7.3%), HTML (5.8%)

Extended Ralph loop for autonomous AI-driven plan execution with multi-phase code review. A standalone CLI tool that orchestrates Claude Code to execute implementation plans autonomously.

**Key Capabilities:**
- Zero setup autonomous plan execution with Claude Code
- Four-phase execution pipeline:
  1. Task execution (fresh Claude Code session per task)
  2. First code review (5 parallel agents: quality, implementation, testing, simplification, documentation)
  3. Codex external review (optional GPT-5.2 review)
  4. Second code review (2 agents for final validation)
- Interactive plan creation via `--plan` flag with Claude-guided dialogue
- Web dashboard for real-time progress monitoring (`--serve`)
- Automatic branch creation, commits, and plan completion tracking
- Fully customizable agents and prompts via `~/.config/ralphex/`
- Claude Code plugin integration (optional slash commands)
- Error pattern detection for quota/rate-limit issues

**Latest Version:** v0.6.0

---

### 4. [Smart Ralph](https://github.com/tzachbon/smart-ralph)
**Location:** [`.docs/github/smart-ralph/`](./.docs/github/smart-ralph/)
**Stars:** 147 | **Forks:** 10
**Language:** Shell (100%)

Spec-driven development for Claude Code with Ralph Loop integration. A Claude Code plugin that turns vague feature ideas into structured specs, then executes them task-by-task with fresh context per task.

**Key Capabilities:**
- Five-phase spec-driven workflow: Research → Requirements → Design → Tasks → Execution
- Ralph Loop dependency (official plugin) for task execution
- Two included plugins:
  - **ralph-specum**: Original spec workflow (stores specs in `./specs/`)
  - **ralph-speckit**: Spec-kit methodology with constitution-first governance (stores in `.specify/specs/`)
- Specialized sub-agents per phase:
  - Research phase: `research-analyst` (web search, codebase analysis)
  - Requirements: `product-manager` (user stories, acceptance criteria)
  - Design: `architect-reviewer` (architecture patterns, technical trade-offs)
  - Tasks: `task-planner` (POC-first breakdown, task sequencing)
  - Execution: `spec-executor` (autonomous implementation, quality gates)
- Task execution workflow: POC → Refactoring → Testing → Quality Gates
- Quick mode (`--quick` flag) to auto-generate all specs and execute
- Resume detection: automatically continues existing specs

**Latest Version:** v2.0.0

---

### 5. [Multi-Agent Ralph Loop](https://github.com/alfredolopez80/multi-agent-ralph-loop)
**Location:** [`.docs/github/multi-agent-ralph-loop/`](./.docs/github/multi-agent-ralph-loop/)
**Stars:** 71 | **Forks:** 14
**Language:** Shell (81.7%), Python (17.7%)

Smart Memory-Driven Orchestration system combining RLM-inspired routing, parallel memory search, multi-agent coordination, automatic learning, and quality-first validation. An advanced enhancement to Claude Code with hooks-based architecture.

**Key Capabilities:**
- **RLM-Inspired Routing**: 3-dimensional classification (complexity 1-10, information density, context requirement)
- **Memory System**: Parallel search across 4 memory systems:
  - Semantic memory via claude-mem MCP plugin
  - Episodic memory with 30-day TTL
  - Procedural memory with 1003+ learned rules
  - Handoffs and ledgers for agent coordination
- **Automatic Learning System (v2.81.2)**: GitHub repo curation, pattern extraction, rule validation, metrics tracking
- **67 Hooks System**: SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PreCompact, Stop events
- **Multi-Agent Coordination**: Native swarm mode with specialized teammates, inter-agent messaging
- **Quality Gates**: Adversarial validation, 3-fix rule (CORRECTNESS, QUALITY, CONSISTENCY), parallel quality gates
- **Checkpoints**: Save/restore orchestration state ("time travel" for orchestration state)
- **Intelligent Command Router (v2.82.0)**: Analyzes prompts and suggests optimal commands (9 patterns, multilingual EN/ES)
- **Promptify Integration (v2.82.0)**: Automatic prompt optimization using Ralph context and memory
- **Observability**: Statusline with dual context display, health checks, event logs, metrics dashboard
- **GLM-4.7 PRIMARY**: Universal model for all complexity levels

**Latest Version:** v2.83.1

---

### 6. [juno-code](https://github.com/askbudi/juno-code)
**Location:** [`.docs/github/juno-code/`](./.docs/github/juno-code/)
**Stars:** 47 | **Forks:** 4
**Language:** TypeScript (86.8%), Python (8.4%), Shell (4.8%)

"Ralph Wiggum meets Kanban!" - AI-powered code automation with structured task management. Takes the Ralph Method insight (AI works better in loops) and adds the structure needed for real iterative development work.

**Key Capabilities:**
- **Iteration Control**: No more overcooking with `-i` max iterations or run until kanban tasks complete
- **Structured Task Tracking**: NDJSON-based kanban (juno-kanban) instead of fragile markdown files like Ralph
- **Multi-AI Backend Support**: Claude, Codex, Gemini, Cursor - switch with one flag
- **Full Traceability**: Every task links to a git commit for time-travel debugging and high token efficiency
- **Hooks Without Lock-in**: Run scripts at any lifecycle point (START_ITERATION, END_ITERATION, SLACK_SYNC, etc.) - works with ANY backend
- **Human-Readable Logs**: `-v` gives structured output instead of raw JSON dumps
- **Slack Integration**: Monitor channels, create kanban tasks from messages, post agent responses as threaded replies
- **GitHub Integration**: Monitor repos, create tasks from issues, post responses as comments with auto-close
- **run_until_completion.sh**: Continuously runs juno-code until all kanban tasks are complete
- **Production-Ready Prompt**: `.juno_task/prompt.md` implements the Ralph method with guard rails
- **Session Management**: List, resume, and continue previous sessions

**Latest Version:** v1.0.44

---

### 7. [Claudeman](https://github.com/Ark0N/Claudeman)
**Location:** [`.docs/github/Claudeman/`](./.docs/github/Claudeman/)
**Stars:** 11 | **Forks:** 2
**Language:** TypeScript (70.2%), JavaScript (18.6%), CSS (5.5%)

Manage Claude Code sessions better than ever - a web-based session manager for autonomous Claude Code work. Enables running sessions 24/7 with persistent GNU Screen sessions, real-time notifications, and automatic respawn when idle.

**Key Capabilities:**
- **Notification System**: Real-time desktop notifications for permission prompts, elicitation dialogs, idle sessions (tab blinking: red for critical, yellow for idle)
- **Persistent Screen Sessions**: Every Claude session runs in GNU Screen - survives server restarts, network drops, machine sleep
- **Respawn Controller**: Core autonomous work - detects idle Claude, sends configurable update prompts, auto-cycles /clear → /init for fresh context
- **Ralph/Todo Tracking**: Auto-detects and tracks Ralph Loops (Promise tags, custom phrases, TodoWrite) with real-time progress percentage
- **Live Agent Visualization**: Floating windows with Matrix-style connection lines showing Claude Code background agents
- **Zero-Flicker Terminal**: 6-layer antiflicker system for butter-smooth 60fps terminal output (16ms server batching, DEC 2026 wrap, rAF client sync)
- **Smart Token Management**: Auto /compact at 110k tokens, auto /clear at 140k tokens - per-session configuration
- **Multi-Session Dashboard**: Run 20+ parallel sessions with 60fps xterm.js streaming, per-session token/cost tracking, tab-based navigation
- **Run Summary**: Complete timeline of "what happened while you were away" (respawn cycles, token milestones, Ralph completions, errors)
- **Project Insights Panel**: Real-time visibility into what Claude is reading and searching (Bash tools, clickable file paths, timeout indicators)

**Latest Version:** v0.1443

---

### 8. [Awesome Ralph](https://github.com/snwfdhmp/awesome-ralph)
**Location:** [`.docs/github/awesome-ralph/`](./.docs/github/awesome-ralph/)
**Stars:** 610 | **Forks:** 43
**Language:** Documentation/Curated List

A curated list of resources about Ralph (aka Ralph Wiggum), the AI coding technique that runs AI coding agents in automated loops until specifications are fulfilled. The definitive resource collection for all things Ralph.

**What it includes:**
- **Official Resources**: Primary sources from Geoffrey Huntley (creator of Ralph) including "Ralph Wiggum as a Software Engineer", "Everything is a Ralph Loop", and "Don't Waste Your Back Pressure"
- **Playbooks & Methodology**: Comprehensive implementation guides covering the "3 Phases, 2 Prompts, 1 Loop" workflow with diagrams and phase explanations
- **Implementations**: Curated list of:
  - Claude Code Plugins: ralph-claude-code, choo-choo-ralph
  - Standalone: snartank/ralph, iannuttall/ralph, smart-ralph, ralph-wiggum-bdd, ralph-orchestrator, nitodeco/ralph
  - Tool-Specific: ralph-wiggum-cursor, opencode-ralph-wiggum, ralph (GitHub Copilot), ralph-tui
  - Multi-Agent: ralph-loop-agent, multi-agent-ralph-loop
- **Tutorials & Guides**: Getting started guides, 11 tips for AI coding with Ralph, troubleshooting, and quickstart tutorials
- **Articles & Blog Posts**: Coverage from VentureBeat, technical explainers, "How Ralph Wiggum Went from The Simpsons to the Biggest Name in AI"
- **Videos & Podcasts**: Deep dives with Geoffrey Huntley, AI That Works Podcast, Dev Interrupted episodes
- **Community**: Hacker News discussions, Reddit (r/ralphcoding), Discord
- **Tools & Directories**: Related tooling and resource collections like Vibe Coding

**Latest Version:** N/A (curated documentation)

---

### 9. [Choo Choo Ralph](https://github.com/mj-meyer/choo-choo-ralph)
**Location:** [`.docs/github/choo-choo-ralph/`](./.docs/github/choo-choo-ralph/)
**Stars:** 12 | **Forks:** 0
**Language:** Shell (100%)

"Relentless like a train. Persistent like Ralph Wiggum." A Claude Code plugin that adds structured, customizable workflow formulas to the Ralph loop. Built on Beads (git-native task tracker) for team-friendly autonomous coding.

**Key Capabilities:**
- **Beads Integration**: Uses Beads (git-native task tracker with molecules) for team-friendly workflow without API latency
- **5-Phase Workflow**: Plan → Spec → Pour → Ralph → Harvest
- **Verified, Not Vibes**: Health checks before implementing, tests after, browser verification when needed
- **Team-Friendly**: Git-native sync, no API latency, works with how your team already collaborates
- **Traceable**: Bead IDs link commits to tasks, learnings to work with full history
- **Structured Phases**: Bearings → Implement → Verify → Commit (not just "do the thing")
- **Bounded Context**: Each task carries its own history via Beads, no context window bloat
- **Compounding Knowledge**: Agents capture learnings as they work; harvest them into skills and docs that make future sessions smarter
- **Customizable Workflows**: Local copies of shell scripts, formulas, and config on install (yours to modify per-project)
- **Parallel Execution**: Multiple tasks run concurrently with coordinated workflows

**Latest Version:** v0.2.0

---

### 10. [OpenHands](https://github.com/All-Hands-AI/OpenHands)
**Location:** [`.docs/github/OpenHands/`](./.docs/github/OpenHands/)
**Stars:** 49.2k | **Forks:** 5.4k
**Language:** Python (88.5%), TypeScript (9.8%)

Open-source autonomous AI software engineer (formerly OpenDevin). A comprehensive platform for autonomous coding with sandboxed execution, web UI, and multi-agent support.

**Key Capabilities:**
- **Sandboxed Environment**: Safe code execution in containerized runtime
- **Multi-Agent Support**: Claude, GPT-4, Gemini, and local models
- **Web-Based UI**: Browser interface for interaction and monitoring
- **Multi-Step Task Execution**: Complex planning and execution workflows
- **GitHub Integration**: Work with issues, PRs, and repositories
- **Extensible Architecture**: Plugin system for custom tools and agents
- **Evaluation Framework**: SWE-bench and other coding benchmarks

**Latest Version:** v0.28.0

---

### 11. [Aider](https://github.com/paul-gauthier/aider)
**Location:** [`.docs/github/aider/`](./.docs/github/aider/)
**Stars:** 31.8k | **Forks:** 2.8k
**Language:** Python (98.2%)

AI pair programming in your terminal. Aider lets you pair program with LLMs to edit code in your local git repository with full multi-file editing support.

**Key Capabilities:**
- **Multi-File Editing**: AI can edit multiple files in a single request
- **Git Integration**: Works seamlessly with local git repositories
- **Multiple LLM Support**: GPT-4, Claude, Gemini, local models via Ollama
- **Code Analysis**: Repository map for better context understanding
- **Voice-to-Code**: Speak to code with voice input support
- **Test-Driven Development**: Run tests and iterate automatically
- **Commit Messages**: AI-generated meaningful commit messages
- **Architect Mode**: Plan changes before implementing

**Latest Version:** Continuous releases

---

### 12. [SWE-agent](https://github.com/princeton-nlp/SWE-agent)
**Location:** [`.docs/github/SWE-agent/`](./.docs/github/SWE-agent/)
**Stars:** 15.6k | **Forks:** 1.5k
**Language:** Python (98.8%)

Agent-Computer Interfaces Enable Automated Software Engineering. Princeton NLP's research project that achieves state-of-the-art performance on SWE-bench.

**Key Capabilities:**
- **Agent-Computer Interface (ACI)**: Specialized tools for LM-codebase interaction
- **SWE-bench Performance**: State-of-the-art on real GitHub issues
- **Multi-Phase Execution**: Read → Explore → Edit → Test workflow
- **Configurable Agents**: Custom agent configurations for different tasks
- **Batch Mode**: Process multiple issues in parallel
- **Academic Research**: Published at NeurIPS 2024
- **Web UI**: Browser interface for monitoring and interaction

**Latest Version:** v1.0.0

---

### 13. [Devika](https://github.com/stitionai/devika)
**Location:** [`.docs/github/devika/`](./.docs/github/devika/)
**Stars:** 19.1k | **Forks:** 2.3k
**Language:** Python (85.4%), TypeScript (12.1%)

AI Software Engineer Agent - Open-source alternative to Devin. An autonomous coding agent with planning, web browsing, and multi-language support.

**Key Capabilities:**
- **Autonomous Planning**: Breaks down complex tasks into manageable steps
- **Web Browsing**: Searches and researches information online
- **Multi-Language Support**: Works with various programming languages
- **Code Execution**: Runs and tests code in sandboxed environment
- **Self-Correction**: Identifies and fixes its own mistakes
- **Project Management**: Organizes work into tasks and milestones
- **Browser Automation**: Interacts with web UIs for testing

**Latest Version:** v1.0.0

---

### 14. [how-to-ralph-wiggum](https://github.com/ghuntley/how-to-ralph-wiggum)
**Location:** [`.docs/github/how-to-ralph-wiggum/`](./.docs/github/how-to-ralph-wiggum/)
**Stars:** 2.8k | **Forks:** 312
**Language:** Shell (100%)

The Ralph Wiggum Technique by Geoffrey Huntley - the AI development methodology that reduces software costs through autonomous iteration loops.

**Key Capabilities:**
- **Core Ralph Loop**: `loop.sh` - the fundamental iteration script
- **Build Mode**: `PROMPT_build.md` for implementation
- **Plan Mode**: `PROMPT_plan.md` for requirements gathering
- **Agent Operations**: `AGENTS.md` loaded each iteration
- **Implementation Plan**: `IMPLEMENTATION_PLAN.md` for task tracking
- **Spec Directory**: `specs/` for requirement specifications
- **Fresh Context**: Each iteration starts with clean state
- **Git-Based Memory**: State persists through commits and files

**Latest Version:** N/A (methodology/template)

---

### 15. [ralph (snarktank)](https://github.com/snarktank/ralph)
**Location:** [`.docs/github/ralph/`](./.docs/github/ralph/)
**Stars:** 89 | **Forks:** 12
**Language:** Shell (100%)

Autonomous AI agent loop that runs repeatedly. A practical implementation of the Ralph Wiggum technique with PRD-based workflow.

**Key Capabilities:**
- **PRD-Based Workflow**: Works with Product Requirements Documents
- **Progress Tracking**: `prd.json` and `progress.txt` for state management
- **Customizable Prompts**: `prompt.md` for Amp, `CLAUDE.md` for Claude Code
- **Auto-Archiving**: Archives previous runs when starting new features
- **Debug Mode**: Check state via progress files
- **Cross-Model Support**: Works with Amp and Claude Code
- **Reference Implementation**: Based on Geoffrey Huntley's Ralph article

**Latest Version:** N/A

---

### 16. [ralph-claude-code](https://github.com/frankbria/ralph-claude-code)
**Location:** [`.docs/github/ralph-claude-code/`](./.docs/github/ralph-claude-code/)
**Stars:** 156 | **Forks:** 23
**Language:** Shell (100%)

Autonomous AI development loop for Claude Code. Purpose-built for Anthropic's Claude Code with fresh context per iteration.

**Key Capabilities:**
- **Claude Code Optimized**: Purpose-built for Anthropic's Claude Code
- **Fresh Context Per Iteration**: Solves context accumulation problems
- **Automatic Commits**: Git-based state persistence
- **Quality Gates**: Built-in testing and validation
- **Error Recovery**: Handles failures gracefully
- **Simple Setup**: Minimal configuration required
- **Cross-Platform**: Works on macOS and Linux

**Latest Version:** N/A

---

### 17. [opencode-ralph-wiggum](https://github.com/Th0rgal/opencode-ralph-wiggum)
**Location:** [`.docs/github/opencode-ralph-wiggum/`](./.docs/github/opencode-ralph-wiggum/)
**Stars:** 67 | **Forks:** 8
**Language:** Python (100%)

Type `ralph "prompt"` to start OpenCode in a Ralph loop. Simple CLI wrapper for OpenCode, Claude Code, and Codex.

**Key Capabilities:**
- **OpenCode Integration**: Works with SaaS Inc's OpenCode
- **Prompt File Support**: Load prompts from files
- **Status Checking**: Monitor loop progress
- **Simple CLI**: `ralph "your prompt here"` syntax
- **Claude Code Support**: Also works with Claude Code
- **Codex Support**: Compatible with OpenAI Codex CLI
- **Lightweight**: Minimal dependencies

**Latest Version:** N/A

---

### 18. [harrymunro-ralph-wiggum](https://github.com/harrymunro/ralph-wiggum)
**Location:** [`.docs/github/harrymunro-ralph-wiggum/`](./.docs/github/harrymunro-ralph-wiggum/)
**Stars:** 45 | **Forks:** 6
**Language:** Shell (100%)

A Claude Code specific implementation of the Ralph Wiggum loop. Tailored for Claude Code's capabilities.

**Key Capabilities:**
- **Claude Code Specific**: Tailored for Claude Code's capabilities
- **Simple Loop**: Minimal, focused implementation
- **Easy Setup**: Get started quickly
- **Customizable**: Adapt to your workflow

**Latest Version:** N/A

---

### 19. [ralph-wiggum-extension](https://github.com/AsyncFuncAI/ralph-wiggum-extension)
**Location:** [`.docs/github/ralph-wiggum-extension/`](./.docs/github/ralph-wiggum-extension/)
**Stars:** 34 | **Forks:** 4
**Language:** TypeScript (78%), JavaScript (22%)

Ralph Wiggum Gemini CLI Extension. Browser extension for web integration with Gemini CLI.

**Key Capabilities:**
- **Gemini CLI Integration**: Works with Google's Gemini CLI
- **Browser Extension**: Chrome/Edge extension for web integration
- **Loop Automation**: Automates the Ralph Wiggum pattern
- **Multi-Backend**: Can work with other CLIs too

**Latest Version:** N/A

---

See [`.docs/github/`](./.docs/github/) for the actual cloned repositories.
