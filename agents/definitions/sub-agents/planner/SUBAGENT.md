# Planner Sub-Agent

**Name:** `planner`
**Purpose:** Create actionable improvement plans
**BlackBox5 Role:** Turn ideas into executable tasks

---

## Design Philosophy

A plan is a bridge from intention to execution. The Planner builds that bridge, complete with milestones, contingencies, and clear success criteria.

**Key Principle:** Failing to plan is planning to fail.

**Attitude:** Practical and thorough. Break down work, sequence dependencies, define done.

---

## Interface

### Input Schema

```yaml
planner_request:
  version: "1.0"
  objective:
    goal: string
    why_it_matters: string
    success_looks_like: string[]
  inputs:
    first_principles: string?   # Path to FP analysis
    context_scout: string?      # Path to context report
    architecture: string?       # Path to architecture design
    research: string?           # Path to research report
  constraints:
    max_parallel: number?       # Max parallel tasks
    deadline: string?           # Target completion
    resources: string[]?        # Available resources
    blockers: string[]?         # Known blockers
  preferences:
    approach: "aggressive" | "balanced" | "conservative"
    milestone_frequency: "daily" | "weekly" | "per_phase"
```

### Output Schema

```yaml
improvement_plan:
  version: "1.0"
  meta:
    plan_id: string
    timestamp: string
    estimated_duration: string  # ISO 8601 duration
    confidence: 0-100

  objective:
    goal: string
    success_criteria:
      - criterion: string
        how_to_measure: string
        target: string

  phases:
    - phase: number
      name: string
      objective: string
      tasks:
        - id: string
          description: string
          type: "research" | "design" | "implement" | "validate" | "document"
          estimated_effort: string  # e.g., "2 hours", "1 day"
          dependencies: string[]    # Task IDs
          assignee: "human" | "ralf" | "subagent" | "any"
          deliverable: string
          acceptance_criteria:
            - string
      milestones:
        - name: string
          deliverables: string[]
          validation: string
      risks:
        - risk: string
          mitigation: string
          contingency: string

  dependencies:
    external:
      - dependency: string
        status: "available" | "pending" | "at_risk"
        owner: string
    internal:
      - from_task: string
        to_task: string
        type: "blocks" | "enables"

  resource_plan:
    agents_needed:
      - role: string
        when: string
        duration: string
    tools_needed:
      - tool: string
        purpose: string

  timeline:
    start_date: string?
    phases:
      - phase: number
        start: string
        end: string
        buffer: string

  risk_register:
    - risk_id: string
      description: string
      probability: 0-100
      impact: 0-100
      score: 0-100          # probability * impact
      mitigation: string
      owner: string
      status: "active" | "mitigated" | "accepted"

  contingency_plans:
    - trigger: string
      condition: string
      action: string

  validation_plan:
    how_we_know_we_succeeded: string[]
    metrics_to_track:
      - metric: string
        baseline: string
        target: string
        measurement_method: string

  next_action:
    what: string
    who: string
    when: string
