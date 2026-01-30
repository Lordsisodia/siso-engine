# GitHub Projects - Rough Loop Collection

This directory contains GitHub projects related to the "rough loop" concept for the RALF autonomous agent framework.

## Projects

### [Ralphy](./ralphy/)
**Repository:** https://github.com/michaelshimeles/ralphy
**Description:** Autonomous AI coding loop. Runs AI agents on tasks until done.
**Language:** TypeScript (75.1%), Shell (23.9%)
**Stars:** 2.1k | **Forks:** 263

**Key Features:**
- Two modes: Single task or task list (PRD)
- Multiple AI engine support: Claude Code, OpenCode, Cursor, Codex, Qwen-Code, Factory Droid, GitHub Copilot, Gemini CLI
- Parallel execution with isolated worktrees
- Branch-per-task workflow with PR creation
- Browser automation via agent-browser
- Webhook notifications (Discord, Slack, custom)
- Sandbox mode for large repos
- Project config with rules and boundaries

**Install:**
```bash
npm install -g ralphy-cli
ralphy "add login button"
ralphy --prd PRD.md
```

---

### [Ralph Orchestrator](./ralph-orchestrator/)
**Repository:** https://github.com/mikeyobrien/ralph-orchestrator
**Description:** A hat-based orchestration framework that keeps AI agents in a loop until the task is done
**Language:** Rust (74.6%), TypeScript (21.4%), Python (2.8%)
**Stars:** 1.5k | **Forks:** 163
**Latest:** v2.4.1

**Key Features:**
- **Hat System**: Specialized personas (architect, developer, tester, reviewer) coordinating through events
- **Multi-Backend Support**: Claude Code, Kiro, Gemini CLI, Codex, Amp, Copilot CLI, OpenCode
- **Backpressure Gates**: Reject incomplete work (tests, lint, typecheck must pass)
- **Memories & Tasks**: Persistent learning system and runtime work tracking
- **31 Presets**: TDD, spec-driven, debugging, and more
- **Web Dashboard (Alpha)**: Monitor and manage orchestration loops
- **RObot (Human-in-the-Loop)**: Telegram integration for agent questions and proactive guidance
- **Interactive Planning**: `ralph plan` for PDD sessions (requirements, design, implementation-plan)
- **Rust 2.0 Rewrite**: Modern architecture with hat-based system

**Install:**
```bash
npm install -g @ralph-orchestrator/ralph-cli
# or
brew install ralph-orchestrator
# or
cargo install ralph-cli

# Plan feature
ralph plan "Add user authentication with JWT"

# Run loop
ralph run -p "Implement the feature in specs/user-authentication/"
```

---

### [Ralphex](./ralphex/)
**Repository:** https://github.com/umputun/ralphex
**Description:** Extended Ralph loop for autonomous AI-driven plan execution with multi-phase code review
**Language:** Go (82.3%), JavaScript (7.3%), HTML (5.8%)
**Stars:** 163 | **Forks:** 17
**Latest:** v0.6.0

**Key Features:**
- Zero setup autonomous plan execution with Claude Code
- Four-phase execution: Task loop → 5-agent review → Codex review → 2-agent final review
- Interactive plan creation via `--plan` flag with Claude-guided dialogue
- Multi-phase code review pipeline (quality, implementation, testing, simplification, documentation)
- Web dashboard for real-time progress monitoring (`--serve`)
- Automatic branch creation, commits, and plan completion tracking
- Fully customizable agents and prompts via `~/.config/ralphex/`
- Claude Code plugin integration (optional)

**Install:**
```bash
go install github.com/umputun/ralphex/cmd/ralphex@latest
# or
brew install umputun/apps/ralphex

ralphex docs/plans/feature.md
ralphex --plan "add user authentication"
ralphex --serve docs/plans/feature.md  # web dashboard
```

---

### [Smart Ralph](./smart-ralph/)
**Repository:** https://github.com/tzachbon/smart-ralph
**Description:** Spec-driven development for Claude Code with Ralph Loop integration
**Language:** Shell (100%)
**Stars:** 147 | **Forks:** 10
**Latest:** v2.0.0

**Key Features:**
- Spec-driven workflow: Research → Requirements → Design → Tasks → Execution
- Claude Code plugin that turns vague ideas into structured specs
- Ralph Loop dependency for task execution (official plugin)
- Two plugins included:
  - **ralph-specum**: Original spec workflow (./specs/)
  - **ralph-speckit**: Spec-kit methodology with constitution-first governance (.specify/specs/)
- Specialized sub-agents per phase (research-analyst, product-manager, architect-reviewer, task-planner, spec-executor)
- Task execution workflow: POC → Refactoring → Testing → Quality Gates
- Quick mode: `--quick` flag to auto-generate all specs and execute
- Resume detection: automatically continues existing specs

**Install:**
```bash
# Install Ralph Loop dependency first
/plugin install ralph-loop@claude-plugins-official

# Install Smart Ralph from marketplace
/plugin marketplace add tzachbon/smart-ralph
/plugin install ralph-specum@smart-ralph

# Quick start
/ralph-specum:start user-auth Add JWT authentication
/ralph-specum:start "Add user auth" --quick
```

---

### [Multi-Agent Ralph Loop](./multi-agent-ralph-loop/)
**Repository:** https://github.com/alfredolopez80/multi-agent-ralph-loop
**Description:** Smart Memory-Driven Orchestration with parallel memory search, RLM-inspired routing, quality-first validation, checkpoints, agent handoffs, and automatic learning
**Language:** Shell (81.7%), Python (17.7%)
**Stars:** 71 | **Forks:** 14
**Latest:** v2.83.1

**Key Features:**
- RLM-Inspired Routing: 3-dimensional classification (complexity 1-10, information density, context requirement)
- Memory System: Parallel search across semantic (claude-mem MCP), episodic (30-day TTL), and procedural (1003+ rules) memory
- Automatic Learning System (v2.81.2): GitHub repo curation, pattern extraction, rule validation
- 67 Hooks System: SessionStart, PreToolUse, PostToolUse, PreCompact, Stop events
- Multi-Agent Coordination: Native swarm mode with specialized teammates
- Quality Gates: Adversarial validation, 3-fix rule, parallel quality gates
- Checkpoints: Save/restore orchestration state (time travel)
- Intelligent Command Router (v2.82.0): Analyzes prompts and suggests optimal commands
- Promptify Integration (v2.82.0): Automatic prompt optimization using Ralph context
- GLM-4.7 PRIMARY model for all complexity levels

**Install:**
```bash
git clone https://github.com/alfredolopez80/multi-agent-ralph-loop.git
cd multi-agent-ralph-loop

# Verify installation
ralph health --compact

# Run orchestration
/orchestrator "Create a REST API endpoint"
/orchestrator "Implement distributed caching system" --launch-swarm --teammate-count 3
```

---

### [juno-code](./juno-code/)
**Repository:** https://github.com/askbudi/juno-code
**Description:** Ralph Wiggum meets Kanban! AI-powered code automation with structured task management
**Language:** TypeScript (86.8%), Python (8.4%), Shell (4.8%)
**Stars:** 47 | **Forks:** 4
**Latest:** v1.0.44

**Key Features:**
- **Ralph Method, But Better**: Takes the Ralph insight (AI works better in loops) and adds structure
- **Iteration Control**: No more overcooking with `-i` max iterations or run until kanban tasks complete
- **Structured Task Tracking**: NDJSON-based kanban (not fragile markdown like Ralph)
- **Multi-AI Backend Support**: Claude, Codex, Gemini, Cursor - switch with one flag
- **Full Traceability**: Every task links to a git commit for time-travel debugging
- **Hooks Without Lock-in**: Run scripts at any lifecycle point with ANY backend
- **Human-Readable Logs**: `-v` gives structured output instead of raw JSON dumps
- **Slack Integration**: Monitor channels, create tasks from messages, post responses as threaded replies
- **GitHub Integration**: Monitor repos, create tasks from issues, auto-close with responses
- **run_until_completion.sh**: Continuously runs until all kanban tasks complete

**Install:**
```bash
npm install -g juno-code

# Initialize project
juno-code init --task "Your task description" --subagent claude

# Start execution (uses .juno_task/prompt.md - production-ready Ralph prompt)
juno-code start -b shell -s claude -i 5 -v

# Run until all tasks complete
./.juno_task/scripts/run_until_completion.sh -s claude -i 1 -v
```

---

### [Claudeman](./Claudeman/)
**Repository:** https://github.com/Ark0N/Claudeman
**Description:** Manage Claude Code sessions better than ever - Autonomous work while you sleep
**Language:** TypeScript (70.2%), JavaScript (18.6%), CSS (5.5%)
**Stars:** 11 | **Forks:** 2
**Latest:** v0.1443

**Key Features:**
- **Notification System**: Real-time desktop notifications for permission prompts, idle sessions, stops (tab blinking alerts)
- **Persistent Screen Sessions**: Every Claude session runs in GNU Screen - survives server restarts, network drops, machine sleep
- **Respawn Controller**: Core autonomous work - detects idle Claude, sends update prompts, auto-cycles /clear → /init
- **Ralph/Todo Tracking**: Auto-detects Ralph Loops (Promise tags, custom phrases, TodoWrite) and tracks progress in real-time
- **Live Agent Visualization**: Floating windows with Matrix-style connection lines showing background agents
- **Zero-Flicker Terminal**: 6-layer antiflicker system for butter-smooth 60fps terminal output (16ms batching, DEC 2026, rAF)
- **Smart Token Management**: Auto /compact at 110k tokens, auto /clear at 140k tokens
- **Multi-Session Dashboard**: Run 20+ parallel sessions with full visibility, per-session token/cost tracking
- **Run Summary**: Complete timeline of what happened (respawn cycles, token milestones, Ralph completions, errors)

**Install:**
```bash
curl -fsSL https://raw.githubusercontent.com/Ark0N/claudeman/master/install.sh | bash
# or
npm install -g claudeman

# Start web dashboard
claudeman web
# Open http://localhost:3000
# Press Ctrl+Enter to start your first session
```

---

### [Awesome Ralph](./awesome-ralph/)
**Repository:** https://github.com/snwfdhmp/awesome-ralph
**Description:** A curated list of resources about Ralph (aka Ralph Wiggum), the AI coding technique
**Language:** (Documentation/Lists)
**Stars:** 610 | **Forks:** 43

**What it includes:**
- **Official Resources**: Primary sources from Geoffrey Huntley (creator of Ralph)
- **Playbooks & Methodology**: Comprehensive implementation guides (3 Phases, 2 Prompts, 1 Loop workflow)
- **Implementations**: Claude Code plugins, standalone implementations, tool-specific implementations, multi-agent systems
- **Tutorials & Guides**: Getting started guides, tips, and troubleshooting
- **Articles & Blog Posts**: Coverage from VentureBeat, technical explainers, analysis
- **Videos & Podcasts**: Deep dives, demos, and podcast episodes
- **Community**: Hacker News discussions, Reddit (r/ralphcoding), Discord
- **Tools & Directories**: Related tooling and resource collections

**Categories Covered:**
- Claude Code Plugins: ralph-claude-code, choo-choo-ralph
- Standalone: snartank/ralph, iannuttall/ralph, smart-ralph, ralph-wiggum-bdd, ralph-orchestrator, nitodeco/ralph
- Tool-Specific: ralph-wiggum-cursor, opencode-ralph-wiggum, ralph (GitHub Copilot), ralph-tui
- Multi-Agent: ralph-loop-agent, multi-agent-ralph-loop

**Install:**
```bash
git clone https://github.com/snwfdhmp/awesome-ralph.git
# This is a curated list - explore the README for all resources
```

---

### [Choo Choo Ralph](./choo-choo-ralph/)
**Repository:** https://github.com/mj-meyer/choo-choo-ralph
**Description:** Beads-powered 5-phase workflow with structured specs, verified implementations, and compounding knowledge
**Language:** Shell (100%)
**Stars:** 12 | **Forks:** 0
**Latest:** v0.2.0

**Key Features:**
- **Beads Integration**: Uses Beads (git-native task tracker) for team-friendly workflow without API latency
- **5-Phase Workflow**: Plan → Spec → Pour → Ralph → Harvest
- **Verified, Not Vibes**: Health checks before implementing, tests after, browser verification when needed
- **Team-Friendly**: Git-native sync, no API latency, works with how your team already collaborates
- **Traceable**: Bead IDs link commits to tasks, learnings to work with full history
- **Structured Phases**: Bearings → Implement → Verify → Commit (not just "do the thing")
- **Bounded Context**: Each task carries its own history via Beads, no context window bloat
- **Compounding Knowledge**: Agents capture learnings as they work; harvest them into skills and docs
- **Customizable Workflows**: Formulas and scripts are yours to modify (local copies on install)
- **Parallel Execution Support**: Run multiple tasks concurrently with coordinated workflows

**Install:**
```bash
# Requires: Claude Code, Beads (bd command), jq
/plugin marketplace add mj-meyer/choo-choo-ralph
/plugin install choo-choo-ralph@choo-choo-ralph

# Set up project
/choo-choo-ralph:install

# Generate spec from your plan
/choo-choo-ralph:spec plans/my-feature.md

# Review the spec, then pour into beads
/choo-choo-ralph:pour

# Start the loop
./ralph.sh
```

---

### [OpenHands](./OpenHands/)
**Repository:** https://github.com/All-Hands-AI/OpenHands
**Description:** Open-source autonomous AI software engineer (formerly OpenDevin)
**Language:** Python (88.5%), TypeScript (9.8%)
**Stars:** 49.2k | **Forks:** 5.4k
**Latest:** v0.28.0

**Key Features:**
- **Sandboxed Environment**: Safe code execution in containerized runtime
- **Multi-Agent Support**: Claude, GPT-4, Gemini, and local models
- **Web-Based UI**: Browser interface for interaction and monitoring
- **Multi-Step Task Execution**: Complex planning and execution workflows
- **GitHub Integration**: Work with issues, PRs, and repositories
- **Extensible Architecture**: Plugin system for custom tools and agents
- **Evaluation Framework**: SWE-bench and other coding benchmarks

**Install:**
```bash
docker pull ghcr.io/all-hands-ai/opopenhands:latest
docker run -it --rm -p 3000:3000 ghcr.io/all-hands-ai/opopenhands:latest

# Or development install
git clone https://github.com/All-Hands-AI/OpenHands.git
cd OpenHands
make build
make run
```

---

### [Aider](./aider/)
**Repository:** https://github.com/paul-gauthier/aider
**Description:** AI pair programming in your terminal
**Language:** Python (98.2%)
**Stars:** 31.8k | **Forks:** 2.8k

**Key Features:**
- **Multi-File Editing**: AI can edit multiple files in a single request
- **Git Integration**: Works seamlessly with local git repositories
- **Multiple LLM Support**: GPT-4, Claude, Gemini, local models via Ollama
- **Code Analysis**: Repository map for better context understanding
- **Voice-to-Code**: Speak to code with voice input support
- **Test-Driven Development**: Run tests and iterate automatically
- **Commit Messages**: AI-generated meaningful commit messages
- **Architect Mode**: Plan changes before implementing

**Install:**
```bash
pip install aider-chat

# Or with pipx
pipx install aider-chat

# Start coding
aider --model gpt-4 file1.py file2.py
aider --model claude-3-5-sonnet-20241022
```

---

### [SWE-agent](./SWE-agent/)
**Repository:** https://github.com/princeton-nlp/SWE-agent
**Description:** Agent-Computer Interfaces Enable Automated Software Engineering
**Language:** Python (98.8%)
**Stars:** 15.6k | **Forks:** 1.5k

**Key Features:**
- **Agent-Computer Interface (ACI)**: Specialized tools for LM-codebase interaction
- **SWE-bench Performance**: State-of-the-art on real GitHub issues
- **Multi-Phase Execution**: Read → Explore → Edit → Test workflow
- **Configurable Agents**: Custom agent configurations for different tasks
- **Batch Mode**: Process multiple issues in parallel
- **Academic Research**: Published at NeurIPS 2024
- **Web UI**: Browser interface for monitoring and interaction

**Install:**
```bash
pip install swe-agent

# Or from source
git clone https://github.com/princeton-nlp/SWE-agent.git
cd SWE-agent
pip install -e .

# Run on a GitHub issue
sweagent run --agent.name default --problem_statement.github_url https://github.com/django/django/issues/12345
```

---

### [Devika](./devika/)
**Repository:** https://github.com/stitionai/devika
**Description:** AI Software Engineer Agent - Open-source alternative to Devin
**Language:** Python (85.4%), TypeScript (12.1%)
**Stars:** 19.1k | **Forks:** 2.3k

**Key Features:**
- **Autonomous Planning**: Breaks down complex tasks into manageable steps
- **Web Browsing**: Searches and researches information online
- **Multi-Language Support**: Works with various programming languages
- **Code Execution**: Runs and tests code in sandboxed environment
- **Self-Correction**: Identifies and fixes its own mistakes
- **Project Management**: Organizes work into tasks and milestones
- **Browser Automation**: Interacts with web UIs for testing

**Install:**
```bash
git clone https://github.com/stitionai/devika.git
cd devika
pip install -r requirements.txt

# Start the backend
python devika.py

# Start the UI (in another terminal)
cd ui/
bun install
bun run dev
```

---

### [how-to-ralph-wiggum](./how-to-ralph-wiggum/)
**Repository:** https://github.com/ghuntley/how-to-ralph-wiggum
**Description:** The Ralph Wiggum Technique - AI development methodology by Geoffrey Huntley
**Language:** Shell (100%)
**Stars:** 2.8k | **Forks:** 312

**Key Features:**
- **Core Ralph Loop**: `loop.sh` - the fundamental iteration script
- **Build Mode**: `PROMPT_build.md` for implementation
- **Plan Mode**: `PROMPT_plan.md` for requirements gathering
- **Agent Operations**: `AGENTS.md` loaded each iteration
- **Implementation Plan**: `IMPLEMENTATION_PLAN.md` for task tracking
- **Spec Directory**: `specs/` for requirement specifications
- **Fresh Context**: Each iteration starts with clean state
- **Git-Based Memory**: State persists through commits and files

**Install:**
```bash
git clone https://github.com/ghuntley/how-to-ralph-wiggum.git
cd how-to-ralph-wiggum

# Read the methodology
cat AGENTS.md
cat PROMPT_build.md

# Start the loop
./loop.sh
```

---

### [ralph (snarktank)](./ralph/)
**Repository:** https://github.com/snarktank/ralph
**Description:** Autonomous AI agent loop that runs repeatedly
**Language:** Shell (100%)
**Stars:** 89 | **Forks:** 12

**Key Features:**
- **PRD-Based Workflow**: Works with Product Requirements Documents
- **Progress Tracking**: `prd.json` and `progress.txt` for state management
- **Customizable Prompts**: `prompt.md` for Amp, `CLAUDE.md` for Claude Code
- **Auto-Archiving**: Archives previous runs when starting new features
- **Debug Mode**: Check state via progress files
- **Cross-Model Support**: Works with Amp and Claude Code
- **Reference Implementation**: Based on Geoffrey Huntley's Ralph article

**Install:**
```bash
git clone https://github.com/snarktank/ralph.git
cd ralph

# Customize for your setup
cp prompt.md.example prompt.md
# Edit prompt.md with your preferences

# Start the loop
./ralph.sh
```

---

### [ralph-claude-code](./ralph-claude-code/)
**Repository:** https://github.com/frankbria/ralph-claude-code
**Description:** Autonomous AI development loop for Claude Code
**Language:** Shell (100%)
**Stars:** 156 | **Forks:** 23

**Key Features:**
- **Claude Code Optimized**: Purpose-built for Anthropic's Claude Code
- **Fresh Context Per Iteration**: Solves context accumulation problems
- **Automatic Commits**: Git-based state persistence
- **Quality Gates**: Built-in testing and validation
- **Error Recovery**: Handles failures gracefully
- **Simple Setup**: Minimal configuration required
- **Cross-Platform**: Works on macOS and Linux

**Install:**
```bash
git clone https://github.com/frankbria/ralph-claude-code.git
cd ralph-claude-code

# Make executable
chmod +x ralph.sh

# Configure your prompts
# Edit the PROMPT file with your requirements

# Run the loop
./ralph.sh
```

---

### [opencode-ralph-wiggum](./opencode-ralph-wiggum/)
**Repository:** https://github.com/Th0rgal/opencode-ralph-wiggum
**Description:** Type `ralph "prompt"` to start OpenCode in a Ralph loop
**Language:** Python (100%)
**Stars:** 67 | **Forks:** 8

**Key Features:**
- **OpenCode Integration**: Works with SaaS Inc's OpenCode
- **Prompt File Support**: Load prompts from files
- **Status Checking**: Monitor loop progress
- **Simple CLI**: `ralph "your prompt here"` syntax
- **Claude Code Support**: Also works with Claude Code
- **Codex Support**: Compatible with OpenAI Codex CLI
- **Lightweight**: Minimal dependencies

**Install:**
```bash
git clone https://github.com/Th0rgal/opencode-ralph-wiggum.git
cd opencode-ralph-wiggum
pip install -e .

# Run with a prompt
ralph "Implement a REST API"

# Or with a prompt file
ralph --file prompt.md
```

---

### [harrymunro-ralph-wiggum](./harrymunro-ralph-wiggum/)
**Repository:** https://github.com/harrymunro/ralph-wiggum
**Description:** A Claude Code specific implementation of the Ralph Wiggum loop
**Language:** Shell (100%)
**Stars:** 45 | **Forks:** 6

**Key Features:**
- **Claude Code Specific**: Tailored for Claude Code's capabilities
- **Simple Loop**: Minimal, focused implementation
- **Easy Setup**: Get started quickly
- **Customizable**: Adapt to your workflow

**Install:**
```bash
git clone https://github.com/harrymunro/ralph-wiggum.git harrymunro-ralph-wiggum
cd harrymunro-ralph-wiggum
chmod +x ralph.sh
./ralph.sh
```

---

### [ralph-wiggum-extension](./ralph-wiggum-extension/)
**Repository:** https://github.com/AsyncFuncAI/ralph-wiggum-extension
**Description:** Ralph Wiggum Gemini CLI Extension
**Language:** TypeScript (78%), JavaScript (22%)
**Stars:** 34 | **Forks:** 4

**Key Features:**
- **Gemini CLI Integration**: Works with Google's Gemini CLI
- **Browser Extension**: Chrome/Edge extension for web integration
- **Loop Automation**: Automates the Ralph Wiggum pattern
- **Multi-Backend**: Can work with other CLIs too

**Install:**
```bash
git clone https://github.com/AsyncFuncAI/ralph-wiggum-extension.git
cd ralph-wiggum-extension
npm install
npm run build

# Load as unpacked extension in Chrome
```

<!-- More projects to be added -->
