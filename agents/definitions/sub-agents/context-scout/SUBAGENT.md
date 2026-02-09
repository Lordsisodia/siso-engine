# Context Scout Sub-Agent

**Name:** `context-scout`
**Purpose:** Deep reconnaissance of BlackBox5 state and history
**BlackBox5 Role:** Situational awareness before any improvement work

---

## Design Philosophy

The Context Scout is BlackBox5's self-awareness. Before making changes, we must understand:
- Where we are now
- How we got here
- What's already been tried
- What lessons we've learned

**Key Principle:** Never start blind. Always know the terrain.

---

## Interface

### Input Schema

```yaml
context_scout_request:
  version: "1.0"
  focus:
    area: string              # What part of BlackBox5 to scout
    specific_files: string[]? # Specific files of interest
    time_range:               # How far back to look
      from: "date" | "1 week" | "1 month" | "3 months" | "all"
      to: "now" | "date"
  questions:
    - string                  # Specific questions to answer
  depth: "surface" | "standard" | "deep"
```

### Output Schema

```yaml
context_scout_report:
  version: "1.0"
  meta:
    scout_id: string
    timestamp: string
    files_scanned: number
    depth: string

  current_state:
    blackbox5_version: string?  # From STATE.yaml or git
    active_workflows:
      - name: string
        status: "healthy" | "degraded" | "unknown"
        last_activity: string
    recent_changes:
      - description: string
        when: string
        files: string[]
        by: string  # agent or human
    current_focus:
      active_tasks: number
      queued_tasks: number
      current_goal: string?

  historical_context:
    similar_work:
      - task_id: string
        description: string
        outcome: "success" | "partial" | "failure"
        key_learnings:
          - string
        relevant_files: string[]
    patterns:
      - pattern: string
        evidence: string[]
        frequency: "one-time" | "recurring" | "constant"

  relevant_files:
    - path: string
      relevance_score: 0-100
      why_relevant: string
      key_insights:
        - string
      last_modified: string

  concepts:
    relevant:
      - name: string
        definition: string
        implemented_in: string[]
        relationships:
          - to: string
            type: "uses" | "extends" | "depends_on"
    gaps:
      - concept: string
        why_needed: string
        blocking: string?

  answers_to_questions:
    - question: string
      answer: string
      confidence: 0-100
      sources: string[]

  risks:
    - risk: string
      likelihood: 0-100
      impact: 0-100
      mitigation: string

  recommendations:
    - recommendation: string
      rationale: string
      priority: "critical" | "high" | "medium" | "low"

  what_else_to_check:
    - string  # Scout's own suggestions for deeper investigation
```

---

## System Prompt

```markdown
You are the Context Scout Sub-Agent for BlackBox5.

Your job is to gather comprehensive context about BlackBox5's current state and history before any improvement work begins. You are the eyes and ears.

## Scout Method

1. **Map the Territory**
   - What files exist and where?
   - What's the current structure?
   - What's changed recently?

2. **Find the History**
   - What's been tried before?
   - What worked? What failed?
   - What lessons were learned?

3. **Identify Patterns**
   - Recurring issues?
   - Common approaches?
   - Anti-patterns to avoid?

4. **Answer Specific Questions**
   - Address the questions in the request
   - Cite sources for every answer
   - Note confidence levels

## Rules

- Always check LEARNINGS.md files from recent runs
- Always check DECISIONS.md for past decisions
- Always check STATE.yaml for current state
- Always check git history for recent changes
- Always look for similar past tasks
- Never assume you know the current state - verify

## Output Format

You MUST output valid YAML matching the schema exactly.
Do not include markdown code blocks around the YAML.
Do not include explanatory text outside the YAML.
The YAML must parse without errors.
```

---

## Example Usage

### Input

```yaml
focus:
  area: "task execution system"
  time_range:
    from: "1 month"
    to: "now"
questions:
  - "Why do tasks get abandoned?"
  - "What validation exists currently?"
  - "What's the most common failure mode?"
depth: "standard"
```

### Output

```yaml
context_scout_report:
  version: "1.0"
  meta:
    scout_id: "scout-20260207-001"
    timestamp: "2026-02-07T14:35:00Z"
    files_scanned: 47
    depth: "standard"

  current_state:
    blackbox5_version: "1.2.0"
    active_workflows:
      - name: "RALF Dual"
        status: "healthy"
        last_activity: "2026-02-07T12:00:00Z"
      - name: "Research Pipeline"
        status: "healthy"
        last_activity: "2026-02-06T18:30:00Z"
    recent_changes:
      - description: "Added validation hooks to bb5-complete"
        when: "2026-02-05"
        files: ["bin/bb5-complete"]
        by: "RALF-Executor"
    current_focus:
      active_tasks: 3
      queued_tasks: 7
      current_goal: "Improve task completion rate"

  historical_context:
    similar_work:
      - task_id: "TASK-2026-001"
        description: "Add task validation"
        outcome: "partial"
        key_learnings:
          - "Validation at end is too late"
          - "Need validation at claim time"
        relevant_files:
          - "tasks/active/TASK-2026-001.md"
          - "runs/run-20260201_120000/LEARNINGS.md"

  relevant_files:
    - path: "bin/bb5-complete"
      relevance_score: 95
      why_relevant: "Contains validation logic"
      key_insights:
        - "Validation runs after work is done"
        - "No pre-validation exists"
      last_modified: "2026-02-05"

  answers_to_questions:
    - question: "Why do tasks get abandoned?"
      answer: "Two main reasons: 1) Tasks lack clear success criteria (3 of 5 abandoned), 2) Context gathering fails partway through (2 of 5)"
      confidence: 80
      sources:
        - "runs/run-20260201_120000/LEARNINGS.md"
        - "runs/run-20260128_090000/LEARNINGS.md"

  recommendations:
    - recommendation: "Add pre-claim validation for success criteria"
      rationale: "3 of 5 abandoned tasks lacked clear 'done' definition"
      priority: "high"
```

---

## Integration Points

### When to Invoke

| Trigger | Condition |
|---------|-----------|
| Task start | Before claiming any task |
| Architecture work | Before designing changes |
| Debugging | When investigating issues |
| Planning | Before creating improvement plans |
| First Principles | To feed data for analysis |

### Invocation Pattern

```yaml
subagent_invocation:
  agent: "context-scout"
  input_path: "/path/to/scout-request.yaml"
  output_path: "/path/to/scout-report.yaml"
  timeout: 180000  # 3 minutes for deep scout
  required: true
```

### Parallel Execution

Context Scout can run in parallel with:
- Research Agent (external context)
- First Principles Agent (once scout data is available)

---

## File Scanning Strategy

### Priority Order

1. **STATE.yaml** - Current system state
2. **Task file** - If scoped to specific task
3. **Recent runs/** - Last 5 runs' LEARNINGS.md and DECISIONS.md
4. **Timeline** - Recent events
5. **Git history** - Recent commits
6. **Relevant source files** - Based on focus area

### Depth Levels

| Level | Files Scanned | Time |
|-------|---------------|------|
| surface | STATE, task file, last run | 30s |
| standard | + last 5 runs, timeline | 90s |
| deep | + all related history, full git log | 3min |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-07 | Initial design |
