# The .docs Folder System

**Status**: Proposed
**Purpose**: AI-managed documentation within each project memory folder

---

## Problem Statement

Project memory has two types of documentation:
1. **Human-readable docs** - Official, curated, stable
2. **AI-generated context** - Dynamic, cross-referenced, frequently updated

Currently, these are mixed together, causing:
- Clutter in main folders
- Humans seeing AI-generated noise
- AI hesitating to write in "official" spaces

---

## Solution: .docs Folders

Each main folder gets a `.docs/` subfolder for AI-managed content.

### Structure

```
project-memory/
├── decisions/
│   ├── architectural/
│   │   ├── DEC-001.md          # Human-written ADR
│   │   └── .docs/
│   │       ├── context.md      # AI: Why this matters now
│   │       ├── related.md      # AI: Links to other decisions
│   │       └── evolution.md    # AI: How decision has changed
│   └── ...
│
├── knowledge/
│   ├── architecture/
│   │   ├── system-overview.md  # Human-written
│   │   └── .docs/
│   │       ├── summaries/      # AI: Auto-generated summaries
│   │       ├── patterns/       # AI: Detected patterns
│   │       └── questions.md    # AI: Open questions
│   └── ...
│
├── plans/
│   ├── active/
│   │   ├── epic-name/
│   │   │   ├── epic.md         # Human-written spec
│   │   │   └── .docs/
│   │   │       ├── context.md  # AI: Current epic status
│   │   │       ├── blockers.md # AI: Current blockers
│   │   │       └── next.md     # AI: Recommended next steps
│   │   └── ...
│   └── ...
│
├── tasks/
│   ├── active/
│   │   ├── TASK-001.md         # Task spec
│   │   ├── TASK-001-CONTEXT.md # Pre-gathered context
│   │   └── .docs/
│   │       ├── notes.md        # AI: Working notes
│   │       ├── progress.md     # AI: Progress tracking
│   │       └── learnings.md    # AI: What we learned
│   └── ...
│
└── .docs/                      # Root-level AI docs
    ├── patterns.md             # AI: Detected project patterns
    ├── health.md               # AI: Project health analysis
    ├── recommendations.md      # AI: Suggested improvements
    └── index.md                # AI: Auto-generated index
```

---

## .docs Folder Purposes

### 1. decisions/.docs/

**Purpose**: Context and relationships for decisions

**Files**:
- `context.md` - Why this decision matters in current context
- `related.md` - Links to related decisions (supersedes, depends on, etc.)
- `evolution.md` - How the decision has evolved over time
- `impact.md` - What has changed because of this decision

**Example**:
```markdown
# decisions/architectural/DEC-001/.docs/context.md

## Current Relevance
This decision is critical for the current refactoring work.

## Related Active Work
- Epic: user-profile (uses this pattern)
- Task: TASK-005 (implementing this)

## Questions Arising
- Should we extend this to other domains?
- Is the performance acceptable?
```

---

### 2. knowledge/.docs/

**Purpose**: AI-generated insights from knowledge base

**Files**:
- `summaries/` - Auto-generated summaries of long docs
- `patterns/` - Detected patterns across codebase
- `questions.md` - Open questions that need research
- `connections.md` - Links between knowledge areas

**Example**:
```markdown
# knowledge/architecture/.docs/patterns/authentication.md

## Detected Pattern: Auth Flow

Found in:
- plans/active/user-profile/epic.md
- knowledge/codebase/clerk-integration.md
- decisions/technical/DEC-003-auth.md

## Pattern Summary
1. Clerk for authentication
2. Supabase RLS for authorization
3. Webhook sync for state

## Risks Identified
- Clerk webhook delays (documented in PITFALLS.md)
```

---

### 3. plans/.docs/

**Purpose**: Dynamic epic/feature status

**Files**:
- `context.md` - Current status and blockers
- `dependencies.md` - Current dependency status
- `risks.md` - Updated risk assessment
- `recommendations.md` - AI-suggested next steps

**Example**:
```markdown
# plans/active/user-profile/.docs/context.md

## Current Status (Auto-generated)
- Progress: 50% (planning complete, implementation pending)
- Blockers: GitHub sync task (TASK-005)
- Ready to start: Yes, after GitHub sync

## Recent Changes
- 2026-01-19: All 18 tasks created
- 2026-01-19: Research completed

## Recommended Next Actions
1. Complete TASK-005 (GitHub sync)
2. Start implementation with TASK-006
3. Set up worktree for development
```

---

### 4. tasks/.docs/

**Purpose**: Working notes and progress

**Files**:
- `notes.md` - Working notes during task execution
- `progress.md` - Progress tracking
- `learnings.md` - What was learned
- `blockers.md` - Current blockers and solutions

**Example**:
```markdown
# tasks/active/TASK-005/.docs/notes.md

## 2026-01-19 - Initial Analysis

### Approach
Using the standard GitHub sync workflow.

### Issues Encountered
- Rate limiting on GitHub API
- Solution: Add delays between requests

### Decisions Made
- Will batch issue creation (5 at a time)
- Will use labels: epic, user-profile, priority-high
```

---

### 5. Root .docs/

**Purpose**: Project-wide AI-generated documentation

**Files**:
- `patterns.md` - Detected patterns across project
- `health.md` - Project health analysis
- `recommendations.md` - Suggested improvements
- `index.md` - Auto-generated index of everything
- `siso-internal-patterns.md` - Pattern documentation (this file)
- `ai-template-usage-guide.md` - Template guide (this file)

---

## Rules for .docs/

### What Goes in .docs/

✅ **AI Should Write**:
- Auto-generated summaries
- Cross-references and links
- Progress tracking
- Pattern detection
- Working notes
- Recommendations
- Questions and open issues

### What Stays in Parent Folder

✅ **Humans Write, AI Updates**:
- STATE.yaml
- WORK-LOG.md
- ACTIVE.md
- Task specifications
- Epic specifications
- Decision records
- Research documents

### Never Put in .docs/

❌ **Never**:
- Official decisions
- Final specifications
- Approved PRDs
- Committed code docs
- Human-reviewed content

---

## Workflow Integration

### When AI Creates .docs/ Content

1. **Starting Work**:
   ```bash
   # Read existing .docs/ for context
   cat tasks/active/TASK-005/.docs/notes.md
   ```

2. **During Work**:
   ```bash
   # Update working notes
   echo "## $(date) - Progress" >> tasks/active/TASK-005/.docs/notes.md
   ```

3. **Completing Work**:
   ```bash
   # Summarize learnings
   cat > tasks/active/TASK-005/.docs/learnings.md << 'EOF'
   ## Learnings from TASK-005

   ### What Worked
   - Approach A was successful
   - Pattern B was effective

   ### What Didn't
   - Approach C had issues

   ### For Future Tasks
   - Use pattern B for similar tasks
   EOF
   ```

4. **Project Analysis**:
   ```bash
   # Generate project health
   cat > .docs/health.md << 'EOF'
   ## Project Health Analysis

   ### Task Completion Rate: 85%
   ### Average Task Time: 2.3 days
   ### Blockers: 2 active
   EOF
   ```

---

## Benefits

### For Humans
- **Clean main folders** - Only official documents
- **Clear separation** - Know what's AI-generated
- **Easy review** - Focus on non-.docs/ for approval

### For AI Agents
- **Freedom to write** - No hesitation about "messing up" official docs
- **Context accumulation** - Build up knowledge over time
- **Experimentation** - Try different formats, approaches

### For Project
- **Living documentation** - Automatically updated
- **Pattern detection** - AI can analyze and report patterns
- **Health monitoring** - AI can track and report status

---

## Implementation Plan

### Phase 1: Add .docs/ to Blackbox5
1. Create `.docs/` in each main folder
2. Add README.md explaining the system
3. Document the patterns (this file)

### Phase 2: Populate Initial Content
1. AI generates initial summaries
2. Create cross-reference docs
3. Set up pattern detection

### Phase 3: Integrate into Workflows
1. Update RALF prompt to use .docs/
2. Add .docs/ updates to agent workflows
3. Create automation for health reports

### Phase 4: Template System
1. Create .docs/ templates
2. Document in AI guide
3. Apply to all projects

---

## File Naming Conventions

```
.docs/
├── README.md              # Explains .docs/ system
├── context.md             # Current context
├── summary.md             # Auto-generated summary
├── patterns/
│   ├── pattern-name.md    # Detected patterns
│   └── ...
├── notes/
│   ├── YYYY-MM-DD-notes.md # Dated notes
│   └── ...
└── meta/
    ├── last-updated.md    # Timestamp
    └── generator.md       # What generated this
```

---

## Related

- `ai-template-usage-guide.md` - How to use templates
- `siso-internal-patterns.md` - Patterns from siso-internal
- `../decisions/architectural/` - Where to document this system

---

**Next Step**: Create decision record for .docs/ system adoption
