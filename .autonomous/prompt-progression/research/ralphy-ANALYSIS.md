# Ralph-y (Ralphy) Framework Analysis

**Repository:** https://github.com/michaelshimeles/ralphy
**Version:** 3.1.0
**Analyzed:** 2026-01-19
**Type:** Autonomous AI Coding Loop
**Language:** Bash Script

---

## Executive Summary

**Ralphy** is an autonomous bash script that runs AI assistants (Claude Code, OpenCode, Codex, or Cursor) in a loop until all tasks in a PRD are complete. It represents a **practical implementation of the Ralph Wiggum pattern** - autonomous execution with minimal overhead.

### Key Insight
Ralphy is **remarkably similar** to BlackBox5's RALPH Runtime system, but with a different implementation approach:
- **Ralphy:** Bash script, PRD-driven, git-worktree based
- **RALPH Runtime:** Python, decision-engine based, comprehensive state management

---

## What It Does

### Core Workflow
1. **Read tasks** from PRD file, YAML file, or GitHub Issues
2. **Send each task** to an AI assistant (Claude Code, OpenCode, Codex, or Cursor)
3. **AI implements** the feature, writes tests, and commits changes
4. **Repeat** until all tasks are done

### Task Sources
- **Markdown** (default): PRD.md with checkbox tasks
- **YAML**: Structured task definitions
- **GitHub Issues**: Fetch from repository

---

## Key Features

### 1. Multi-AI Engine Support
| Engine | CLI Command | Permissions | Output |
|--------|-------------|-------------|--------|
| **Claude Code** | `claude` | `--dangerously-skip-permissions` | Tokens + cost estimate |
| **OpenCode** | `opencode` | `OPENCODE_PERMISSION='{"*":"allow"}'` | Tokens + actual cost |
| **Codex** | `codex` | N/A | Token usage (if provided) |
| **Cursor** | `agent` | `--force` | API duration (no tokens) |

### 2. Parallel Execution
**⭐⭐⭐⭐⭐ HIGH PRIORITY FEATURE**

Run multiple AI agents simultaneously, each in its own isolated git worktree:

```bash
./ralphy.sh --parallel                    # 3 agents (default)
./ralphy.sh --parallel --max-parallel 5   # 5 agents
```

**How It Works:**
- Each agent gets its own git worktree (separate directory)
- Each agent gets its own branch (`ralphy/agent-1-task-name`, etc.)
- Complete isolation from other agents

```
Agent 1 ─► worktree: /tmp/xxx/agent-1 ─► branch: ralphy/agent-1-create-user-model
Agent 2 ─► worktree: /tmp/xxx/agent-2 ─► branch: ralphy/agent-2-add-api-endpoints
Agent 3 ─► worktree: /tmp/xxx/agent-3 ─► branch: ralphy/agent-3-setup-database
```

**After Completion:**
- **Without `--create-pr`:** Branches auto-merged, AI resolves conflicts
- **With `--create-pr`:** Each task gets its own PR

### 3. Branch Workflow
Create a separate branch for each task:

```bash
./ralphy.sh --branch-per-task                        # Feature branches
./ralphy.sh --branch-per-task --base-branch main     # From main
./ralphy.sh --branch-per-task --create-pr            # Auto PRs
./ralphy.sh --branch-per-task --create-pr --draft-pr # Draft PRs
```

Branch naming: `ralphy/<task-name-slug>`
- "Add user authentication" → `ralphy/add-user-authentication`

### 4. YAML Parallel Groups
Control which tasks can run together:

```yaml
tasks:
  - title: Create User model
    parallel_group: 1
  - title: Create Post model
    parallel_group: 1  # Runs with User model (same group)
  - title: Add relationships
    parallel_group: 2  # Runs after group 1 completes
```

Tasks without `parallel_group` default to group `0`.

### 5. Cost Tracking
Different metrics per engine:
- **Claude Code:** Input/output tokens, estimated cost
- **OpenCode:** Input/output tokens, actual cost
- **Codex:** Input/output tokens (if provided)
- **Cursor:** Total API duration (tokens not available)

---

## Architecture

### Technology Stack
- **Language:** Bash Script
- **Dependencies:** `jq` (JSON parsing), `yq` (YAML, optional), `gh` (GitHub, optional)
- **Git:** Git worktrees for parallel isolation
- **AI Engines:** Claude Code, OpenCode, Codex, Cursor

### Implementation Approach

#### Simple Script vs. Sophisticated Runtime
| Aspect | Ralphy | RALPH Runtime |
|--------|--------|---------------|
| **Language** | Bash | Python |
| **Complexity** | Simple | Sophisticated |
| **State Management** | Minimal | Comprehensive |
| **Decision Making** | Linear | Decision Engine |
| **Error Recovery** | Retry logic | Circuit Breaker |
| **Progress Tracking** | Basic | Advanced |
| **Parallel Execution** | Git worktrees | Planned |
| **Task Sources** | PRD, YAML, GitHub | Plan files |

#### Git Worktree Isolation (⭐⭐⭐⭐⭐ KEY PATTERN)

**This is the most important pattern to adopt:**

```bash
# Create isolated worktrees for parallel execution
git worktree add /tmp/ralphy-agent-1 branch-1
git worktree add /tmp/ralphy-agent-2 branch-2
git worktree add /tmp/ralphy-agent-3 branch-3

# Each agent works in isolation
Agent 1 → /tmp/ralphy-agent-1
Agent 2 → /tmp/ralphy-agent-2
Agent 3 → /tmp/ralphy-agent-3

# Merge back when done
git worktree remove /tmp/ralphy-agent-1
git worktree remove /tmp/ralphy-agent-2
git worktree remove /tmp/ralphy-agent-3
```

**Benefits:**
- True parallel execution (no file conflicts)
- Isolated testing environments
- Easy cleanup on failure
- Merge conflict detection

---

## Comparison with BlackBox5 RALPH Runtime

### Similarities ✅
1. **Autonomous Execution** - Both run AI agents in loops
2. **Task-Based** - Both work through task lists
3. **AI Integration** - Both integrate with Claude Code
4. **Error Recovery** - Both have retry logic
5. **Progress Tracking** - Both track completion

### Differences ⚠️
1. **Implementation** - Bash vs Python
2. **State Management** - Minimal vs Comprehensive
3. **Decision Making** - Linear vs Decision Engine
4. **Parallel Strategy** - Git worktrees vs (planned) multi-agent
5. **Task Sources** - PRD/YAML/GitHub vs Plan files

### Ralphy Advantages
- ✅ **Git Worktree Isolation** - Superior parallel execution
- ✅ **Simple** - Easy to understand and modify
- ✅ **Multi-AI Support** - Claude, OpenCode, Codex, Cursor
- ✅ **PRD-Driven** - Natural task format
- ✅ **GitHub Integration** - Auto-create PRs

### RALPH Runtime Advantages
- ✅ **Decision Engine** - Intelligent decision making
- ✅ **Circuit Breaker** - Advanced error recovery
- ✅ **Progress Tracker** - Comprehensive state tracking
- ✅ **Autonomous Agent** - Self-direction capabilities
- ✅ **Learning** - Feedback-based learning

---

## Key Patterns to Adopt

### 1. Git Worktree Parallel Execution ⭐⭐⭐⭐⭐
**Priority:** HIGHEST

**Implementation:**
```python
# Add to RALPH Runtime
import git
import tempfile
import shutil

class GitWorktreeManager:
    def __init__(self, repo_path):
        self.repo = git.Repo(repo_path)
        self.worktrees = []

    def create_worktree(self, branch_name, task_id):
        # Create isolated worktree
        worktree_path = tempfile.mkdtemp(prefix=f"ralph-{task_id}-")
        self.repo.git.worktree('add', worktree_path, f'ralph/{branch_name}')
        self.worktrees.append((worktree_path, branch_name))
        return worktree_path

    def merge_worktree(self, worktree_path, branch_name):
        # Merge branch back to main
        self.repo.git.merge(f'ralph/{branch_name}')
        self.cleanup_worktree(worktree_path)

    def cleanup_worktree(self, worktree_path):
        # Remove worktree
        self.repo.git.worktree('remove', worktree_path)
        shutil.rmtree(worktree_path)
```

**Benefits:**
- True parallel execution
- No file conflicts
- Easy cleanup
- Merge conflict detection

### 2. Multi-AI Engine Support ⭐⭐⭐⭐
**Priority:** HIGH

**Current:** RALPH only uses Claude Code
**Proposed:** Support multiple engines

```python
class AIEngineAdapter:
    ENGINES = {
        'claude': ClaudeCodeEngine,
        'opencode': OpenCodeEngine,
        'codex': CodexEngine,
        'cursor': CursorEngine
    }

    def __init__(self, engine_name='claude'):
        self.engine = self.ENGINES[engine_name]()

    def execute_task(self, task):
        return self.engine.execute(task)
```

**Benefits:**
- Flexibility in AI engine choice
- Cost optimization (choose cheapest)
- Redundancy (switch if one fails)
- Feature differences (use best for task)

### 3. PRD-Driven Task Format ⭐⭐⭐⭐
**Priority:** HIGH

**Current:** RALPH uses YAML plan files
**Proposed:** Support PRD format

```markdown
# My Project

## Tasks
- [ ] Create user authentication
- [ ] Add dashboard page
- [ ] Build API endpoints
```

**Parser:**
```python
import re

def parse_prd_tasks(prd_path):
    with open(prd_path) as f:
        content = f.read()

    # Extract tasks from PRD
    tasks = re.findall(r'- \[([ x])\] (.+)', content)
    return [
        {'title': title, 'completed': (status == 'x')}
        for status, title in tasks
    ]
```

**Benefits:**
- Natural task format
- Easy to write
- GitHub compatible
- Non-technical users

### 4. Branch Per Task ⭐⭐⭐
**Priority:** MEDIUM

**Implementation:**
```python
def create_task_branch(task_name, base_branch='main'):
    # Slugify task name
    branch_name = slugify(task_name)
    full_branch = f'ralphy/{branch_name}'

    # Create and checkout branch
    repo.git.checkout(base_branch)
    repo.git.checkout('b', full_branch)

    return full_branch
```

**Benefits:**
- Isolated changes
- Easy review
- Rollback capability
- PR workflow

### 5. Auto-Create PRs ⭐⭐⭐
**Priority:** MEDIUM

**Implementation:**
```python
def create_pr(branch_name, task_name, draft=False):
    # Create PR using GitHub CLI
    draft_flag = '--draft' if draft else ''
    repo = 'owner/repo'

    subprocess.run([
        'gh', 'pr', 'create',
        '--base', 'main',
        '--head', branch_name,
        '--title', task_name,
        '--body', f'Automated PR for: {task_name}',
        draft_flag,
        '--repo', repo
    ])
```

**Benefits:**
- Automated PR workflow
- Code review process
- Integration tracking
- Deployment pipeline

---

## Integration Recommendations

### Phase 1: Adopt Git Worktree Pattern (Week 1) ⭐⭐⭐⭐⭐
**Priority:** HIGHEST

**Actions:**
1. Implement `GitWorktreeManager` class
2. Add parallel execution support
3. Update RALPH Runtime to use worktrees
4. Test with 3-5 parallel agents

**Expected Benefits:**
- True parallel task execution
- No file conflicts
- 3-5x speedup on parallelizable tasks

### Phase 2: Multi-AI Engine Support (Week 2) ⭐⭐⭐⭐
**Priority:** HIGH

**Actions:**
1. Create `AIEngineAdapter` interface
2. Implement OpenCode, Codex, Cursor engines
3. Add engine selection to config
4. Test cost optimization

**Expected Benefits:**
- Flexibility in AI choice
- Cost savings
- Redundancy

### Phase 3: PRD Format Support (Week 3) ⭐⭐⭐⭐
**Priority:** HIGH

**Actions:**
1. Add PRD parser
2. Support checkbox tasks
3. Auto-update PRD on completion
4. GitHub Issues integration

**Expected Benefits:**
- Natural task format
- Better UX
- GitHub integration

### Phase 4: Branch & PR Workflow (Week 4) ⭐⭐⭐
**Priority:** MEDIUM

**Actions:**
1. Implement branch-per-task
2. Add auto-create PR
3. Implement merge conflict resolution
4. Add draft PR support

**Expected Benefits:**
- Code review process
- Deployment integration
- Better workflow

---

## Pros & Cons

### Pros ✅
1. **Simplicity** - Easy to understand and modify
2. **Git Worktree Isolation** - Superior parallel execution
3. **Multi-AI Support** - Flexibility in engine choice
4. **PRD-Driven** - Natural task format
5. **GitHub Integration** - Auto-create PRs
6. **Cost Tracking** - Actual costs (OpenCode)
7. **Battle-Tested** - Version 3.1.0, actively maintained

### Cons ❌
1. **Bash Script** - Limited error handling
2. **No Decision Engine** - Linear execution
3. **Basic State Management** - Minimal tracking
4. **No Learning** - No feedback-based improvement
5. **Manual Retry** - No circuit breaker
6. **Single Purpose** - Only does PRD completion

---

## Code Quality Assessment

### Strengths
- ✅ Clean, readable bash script
- ✅ Good documentation
- ✅ Multiple examples
- ✅ Cross-platform (macOS, Linux)
- ✅ Verbose mode for debugging
- ✅ Dry-run mode

### Weaknesses
- ❌ Limited error handling (no circuit breaker)
- ❌ No state persistence
- ❌ Basic logging
- ❌ No monitoring/observability
- ❌ Manual configuration

---

## Priority Rating: ⭐⭐⭐⭐⭐

### Why Highest Priority?

1. **Git Worktree Pattern** - This is the **most important pattern** to adopt
   - Enables true parallel execution
   - Solves file conflict issues
   - Better than current RALPH approach

2. **Proven in Production** - Version 3.1.0, actively used
   - Battle-tested implementation
   - Real-world usage patterns
   - Known edge cases

3. **Complementary to RALPH** - Not competitive, but synergistic
   - RALPH provides decision engine
   - Ralphy provides git worktree execution
   - Best of both worlds

4. **Quick to Integrate** - 1-2 weeks for git worktree pattern
   - Simple implementation
   - High impact
   - Low risk

---

## Implementation Roadmap

### Week 1: Git Worktree Integration
- [ ] Implement `GitWorktreeManager` class
- [ ] Add parallel execution support
- [ ] Test with 3-5 parallel agents
- [ ] Document usage patterns

### Week 2: Multi-AI Support
- [ ] Create `AIEngineAdapter` interface
- [ ] Implement OpenCode engine
- [ ] Implement Codex engine
- [ ] Implement Cursor engine
- [ ] Add cost tracking

### Week 3: PRD Format Support
- [ ] Add PRD parser
- [ ] Support checkbox tasks
- [ ] Auto-update PRD on completion
- [ ] GitHub Issues integration

### Week 4: Branch & PR Workflow
- [ ] Implement branch-per-task
- [ ] Add auto-create PR
- [ ] Implement merge conflict resolution
- [ ] Add draft PR support
- [ ] Test full workflow

---

## Conclusion

**Ralphy is a highly complementary framework** to BlackBox5's RALPH Runtime. While RALPH provides sophisticated decision-making and state management, Ralphy provides:

1. **Superior parallel execution** via git worktrees
2. **Multi-AI engine support** for flexibility
3. **PRD-driven format** for natural task management
4. **GitHub integration** for automated PRs

**Recommendation:** Adopt Ralphy's git worktree pattern immediately (Phase 1), then gradually integrate other features (Phases 2-4).

**Expected Impact:** 3-5x speedup on parallelizable tasks, better UX, and GitHub integration.

---

**Analysis Complete:** 2026-01-19
**Priority:** ⭐⭐⭐⭐⭐ (HIGHEST)
**Next Action:** Implement git worktree pattern in RALPH Runtime
