# Planner+Checker Loop Pattern

**Location:** `2-engine/agents/definitions/claude-native/workflows/planner-checker-loop.md`

**Purpose:** Iterative planning workflow that produces high-quality, verifiable plans through structured feedback loops.

**Source:** GSD (Get-Shit-Done) Framework - adapted for BlackBox5

---

## 1. Overview

### What is the Planner+Checker Loop?

The Planner+Checker loop is a quality assurance pattern for plan generation. Instead of producing a plan in a single pass, it iterates between:

1. **Planner** - Creates/updates the plan
2. **Checker** - Validates the plan against 7 dimensions
3. **Revision** - Planner addresses feedback (max 3 iterations)

### Why Use It?

| Problem | Solution |
|---------|----------|
| Plans missing critical dependencies | Checker verifies completeness |
| Underestimated effort | Checker validates estimates |
| Unverifiable success criteria | Checker ensures testable criteria |
| Scope creep | Checker enforces boundaries |
| Poor sequencing | Checker validates dependencies |

**Result:** Plans that are actionable, complete, and actually executable.

---

## 2. The Loop Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLANNER+CHECKER LOOP                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐     │
│  │   INPUT     │─────▶│   PLANNER   │─────▶│   PLAN      │     │
│  │  (Request)  │      │  (Create)   │      │  (Draft)    │     │
│  └─────────────┘      └─────────────┘      └──────┬──────┘     │
│                                                    │            │
│  ┌─────────────┐      ┌─────────────┐      ┌──────▼──────┐     │
│  │   REVISED   │◀─────│   PLANNER   │◀─────│  CHECKER    │     │
│  │    PLAN     │      │  (Revise)   │      │ (Validate)  │     │
│  └──────┬──────┘      └─────────────┘      └─────────────┘     │
│         │                                                       │
│         └──────────────────────────────────────────┐            │
│                                                    │            │
│                              ┌─────────────────────▼─────┐      │
│                              │   ITERATION < 3?          │      │
│                              │   AND issues found?       │      │
│                              └───────────────────────────┘      │
│                                                    │            │
│                              ┌─────────────────────▼─────┐      │
│                              │   OUTPUT FINAL PLAN       │      │
│                              └───────────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Iteration Rules

| Rule | Description |
|------|-------------|
| **Max 3 iterations** | Prevents infinite loops, forces convergence |
| **Stop on PASS** | If checker returns no issues, exit immediately |
| **Stop on 3rd iteration** | Return best plan even if issues remain |
| **Escalate on block** | If checker finds critical blockers, escalate to human |

### Loop Flow

```python
# Pseudocode for loop execution
plan = planner.create_plan(request)
iteration = 1

while iteration <= 3:
    feedback = checker.validate(plan, request)

    if feedback.status == "PASS":
        return plan  # Success!

    if iteration == 3:
        return plan  # Best effort after 3 tries

    plan = planner.revise(plan, feedback)
    iteration += 1
```

---

## 3. Planner Agent Specification

### Purpose

Transform requirements into actionable, sequenced tasks with clear deliverables and acceptance criteria.

### Input Format

```yaml
---
planner_request:
  version: "1.0"
  objective:
    goal: string                    # One-sentence objective
    context: string                 # Background information
    constraints:                    # Hard constraints
      - string
    non_goals:                      # Explicitly out of scope
      - string

  inputs:
    first_principles: string?       # Path to FP analysis
    context_scout: string?          # Path to context report
    architecture: string?           # Path to architecture doc
    research: string?               # Path to research findings

  requirements:
    functional:                     # What the system must do
      - string
    non_functional:                 # Performance, security, etc.
      - string

  success_criteria:                 # How we know it's done
    - criterion: string
      measurable: boolean
      verification_method: string

  constraints:
    max_parallel: number?           # Max concurrent tasks
    deadline: string?               # Target date (ISO 8601)
    resources: string[]?            # Available resources
    blockers: string[]?             # Known blockers

  preferences:
    approach: "aggressive" | "balanced" | "conservative"
    milestone_frequency: "daily" | "weekly" | "per_phase"
    detail_level: "high" | "medium" | "low"
```

### Output Format

Planner outputs XML with YAML frontmatter:

```xml
---
plan_meta:
  version: "1.0"
  plan_id: "PLAN-XXX"
  timestamp: "2026-02-07T12:00:00Z"
  estimated_duration: "P5D"       # ISO 8601 duration
  confidence: 85                   # 0-100
  iteration: 1                     # Loop iteration number
---

<plan id="PLAN-XXX">
  <objective>
    <goal>Clear one-sentence goal</goal>
    <success_criteria>
      <criterion id="SC-001" testable="true">
        <description>Specific, measurable criterion</description>
        <verification>How to verify this criterion</verification>
      </criterion>
    </success_criteria>
  </objective>

  <phases>
    <phase id="P1" order="1">
      <name>Phase Name</name>
      <objective>What this phase accomplishes</objective>
      <duration>2 days</duration>

      <tasks>
        <task id="T-001" type="research|design|implement|validate|document">
          <title>Task Title</title>
          <description>Clear description of work</description>
          <estimated_effort>4 hours</estimated_effort>
          <assignee>human|ralf|subagent|any</assignee>
          <deliverable>What this task produces</deliverable>

          <dependencies>
            <task_ref id="T-XXX"/>
          </dependencies>

          <acceptance_criteria>
            <criterion>Specific criterion 1</criterion>
            <criterion>Specific criterion 2</criterion>
          </acceptance_criteria>

          <verification>
            <step>How to verify completion</step>
          </verification>
        </task>
      </tasks>

      <milestones>
        <milestone id="M-001">
          <name>Milestone Name</name>
          <deliverables>
            <deliverable>Deliverable 1</deliverable>
          </deliverables>
          <validation>How to validate</validation>
        </milestone>
      </milestones>

      <risks>
        <risk id="R-001" probability="medium" impact="high">
          <description>Risk description</description>
          <mitigation>How to mitigate</mitigation>
          <contingency>Fallback plan</contingency>
        </risk>
      </risks>
    </phase>
  </phases>

  <dependencies>
    <external>
      <dependency id="ED-001" status="available|pending|at_risk">
        <item>External dependency</item>
        <owner>Who owns this</owner>
        <fallback>What to do if blocked</fallback>
      </dependency>
    </external>
    <internal>
      <link from="T-002" to="T-001" type="blocks|enables"/>
    </internal>
  </dependencies>

  <resource_plan>
    <agents>
      <agent role="bmad-architect" when="P1" duration="2 days"/>
    </agents>
    <tools>
      <tool name="docker" purpose="Containerization"/>
    </tools>
  </resource_plan>

  <timeline>
    <start_date>2026-02-07</start_date>
    <phases>
      <phase_ref id="P1" start="2026-02-07" end="2026-02-09" buffer="1 day"/>
    </phases>
  </timeline>

  <risk_register>
    <risk id="R-001" probability="30" impact="80" score="24">
      <description>Risk description</description>
      <mitigation>Mitigation strategy</mitigation>
      <owner>Owner</owner>
      <status>active|mitigated|accepted</status>
    </risk>
  </risk_register>

  <next_action>
    <what>First action to take</what>
    <who>Who should do it</who>
    <when>When to start</when>
  </next_action>
</plan>
```

### Planner Responsibilities

| Responsibility | Description |
|----------------|-------------|
| **Decomposition** | Break work into actionable tasks |
| **Sequencing** | Order tasks by dependencies |
| **Estimation** | Provide realistic effort estimates |
| **Assignment** | Match tasks to appropriate agents |
| **Criteria Definition** | Define testable acceptance criteria |
| **Risk Identification** | Surface risks with mitigations |
| **Dependency Mapping** | Identify internal and external dependencies |

### Revision Mode

When revising based on checker feedback:

```yaml
---
revision_request:
  original_plan: "PLAN-XXX"
  iteration: 2
  checker_feedback:
    status: "NEEDS_REVISION"
    issues:
      - category: "completeness"
        severity: "critical"
        description: "Missing rollback strategy"
        suggestion: "Add rollback section to each phase"
      - category: "estimation"
        severity: "warning"
        description: "Task T-003 underestimated"
        suggestion: "Increase from 2h to 4h"

  revision_focus:
    - "Add rollback strategies"
    - "Adjust T-003 estimate"
```

---

## 4. Checker Agent Specification

### Purpose

Quality gate for plans. Validates against 7 dimensions and provides structured feedback for revision.

### The 7 Verification Dimensions

| Dimension | What It Checks | Critical Issues |
|-----------|----------------|-----------------|
| **1. Completeness** | All requirements covered? | Missing tasks for requirements |
| **2. Sequencing** | Logical task order? | Circular dependencies, impossible orders |
| **3. Estimation** | Realistic time estimates? | Tasks > 8h, unrealistic totals |
| **4. Verifiability** | Testable success criteria? | Vague criteria, no verification method |
| **5. Dependencies** | All dependencies identified? | Missing external deps, orphaned tasks |
| **6. Risk Coverage** | Risks identified with mitigations? | High-impact risks without plans |
| **7. Resource Fit** | Assignees match task types? | Wrong agent for task type |

### Input Format

```yaml
---
checker_request:
  version: "1.0"
  plan_id: "PLAN-XXX"
  plan_path: "/path/to/plan.xml"
  original_request:
    objective:
      goal: "Original goal"
    requirements:
      functional:
        - "Req 1"
      non_functional:
        - "NFR 1"
    success_criteria:
      - "Criterion 1"
  strictness: "standard"  # lenient | standard | strict
```

### Output Format

```yaml
---
checker_report:
  version: "1.0"
  meta:
    report_id: "CHK-XXX"
    timestamp: "2026-02-07T12:30:00Z"
    plan_id: "PLAN-XXX"
    strictness: "standard"
    duration_ms: 45000

  summary:
    status: "PASS" | "NEEDS_REVISION" | "REJECT"
    overall_score: 78                    # 0-100
    critical_issues: 0
    warnings: 2
    infos: 3
    iteration_recommended: true

  dimension_checks:
    - dimension: "completeness"
      status: "PASS" | "PARTIAL" | "FAIL"
      score: 85
      findings:
        - type: "missing"
          severity: "critical"
          description: "No task covers requirement R-003"
          location: "phase P2"
          suggestion: "Add task for database migration"
        - type: "coverage"
          severity: "info"
          description: "All other requirements covered"

    - dimension: "sequencing"
      status: "PASS"
      score: 95
      findings:
        - type: "dependency"
          severity: "info"
          description: "Task order is logical"

    - dimension: "estimation"
      status: "PARTIAL"
      score: 70
      findings:
        - type: "underestimated"
          severity: "warning"
          description: "Task T-005 estimated at 2h but involves complex logic"
          location: "task T-005"
          suggestion: "Increase to 4-6 hours"
        - type: "aggregate"
          severity: "info"
          description: "Total estimate: 5 days (reasonable)"

    - dimension: "verifiability"
      status: "PARTIAL"
      score: 75
      findings:
        - type: "vague_criteria"
          severity: "warning"
          description: "Criterion 'improve performance' is not measurable"
          location: "success_criteria SC-002"
          suggestion: "Change to 'reduce response time to <200ms'"

    - dimension: "dependencies"
      status: "PASS"
      score: 90
      findings:
        - type: "external"
          severity: "info"
          description: "External dependency on API team noted"

    - dimension: "risk_coverage"
      status: "PARTIAL"
      score: 65
      findings:
        - type: "missing_mitigation"
          severity: "warning"
          description: "Risk R-002 (API delay) has no contingency"
          location: "risk R-002"
          suggestion: "Add fallback to mock API for development"

    - dimension: "resource_fit"
      status: "PASS"
      score: 95
      findings:
        - type: "assignment"
          severity: "info"
          description: "All task-agent assignments appropriate"

  requirement_coverage:
    - requirement: "Add user authentication"
      status: "COVERED"
      by_tasks: ["T-001", "T-002"]
    - requirement: "Implement rate limiting"
      status: "NOT_COVERED"
      gap: "No task addresses this requirement"

  criteria_verifiability:
    - criterion: "Users can log in with email/password"
      testable: true
      verification_method: "Integration test + manual QA"
    - criterion: "System is secure"
      testable: false
      issue: "Not measurable - what does 'secure' mean?"

  issues:
    - severity: "critical"
      category: "completeness"
      description: "Missing rollback strategy for database migration"
      location: "phase P2, task T-004"
      fix_suggestion: "Add rollback task or document rollback procedure"
      auto_fixable: false

    - severity: "warning"
      category: "estimation"
      description: "Task T-005 likely underestimated"
      location: "task T-005"
      fix_suggestion: "Increase estimate from 2h to 4h"
      auto_fixable: true

    - severity: "info"
      category: "best_practice"
      description: "Consider adding monitoring task"
      location: "phase P3"
      fix_suggestion: "Add task for setting up alerts"
      auto_fixable: true

  revision_guidance:
    priority_order:
      - "Add task for requirement R-003"
      - "Add rollback strategy to T-004"
      - "Revise success criteria SC-002 to be measurable"
      - "Adjust T-005 estimate"
    focus_areas:
      - "completeness"
      - "verifiability"

  next_steps:
    action: "revise" | "proceed" | "escalate"
    reason: "2 critical issues must be addressed"
    max_iterations_remaining: 2
```

### Severity Levels

| Level | Definition | Action Required |
|-------|------------|-----------------|
| **Critical** | Plan cannot succeed as written | Must fix before proceeding |
| **Warning** | Plan has gaps that reduce confidence | Should fix, but can proceed |
| **Info** | Suggestions for improvement | Optional, nice to have |

### Strictness Modes

| Mode | Critical Threshold | Use Case |
|------|-------------------|----------|
| **Lenient** | Only block on obvious failures | Rapid prototyping, exploration |
| **Standard** | Block on unmet requirements | Normal development |
| **Strict** | Block on any warning | Production, critical systems |

---

## 5. Implementation Example

### Python Implementation

```python
#!/usr/bin/env python3
"""
Planner+Checker Loop Implementation for BlackBox5
"""

import xml.etree.ElementTree as ET
import yaml
from dataclasses import dataclass
from typing import List, Optional, Literal
from enum import Enum

class Status(Enum):
    PASS = "PASS"
    NEEDS_REVISION = "NEEDS_REVISION"
    REJECT = "REJECT"

@dataclass
class LoopConfig:
    max_iterations: int = 3
    strictness: Literal["lenient", "standard", "strict"] = "standard"
    stop_on_pass: bool = True

@dataclass
class PlannerRequest:
    objective: dict
    requirements: dict
    success_criteria: List[dict]
    constraints: Optional[dict] = None

@dataclass
class CheckerReport:
    status: Status
    overall_score: int
    critical_issues: int
    warnings: int
    revision_guidance: dict

def run_planner_checker_loop(
    request: PlannerRequest,
    config: LoopConfig = LoopConfig()
) -> dict:
    """
    Execute the Planner+Checker loop.

    Returns the final plan and loop metadata.
    """

    iteration = 1
    plan = None
    reports = []

    while iteration <= config.max_iterations:
        # Phase 1: Plan (or Revise)
        if iteration == 1:
            plan = planner_create(request)
        else:
            plan = planner_revise(plan, reports[-1])

        # Phase 2: Check
        report = checker_validate(plan, request, config.strictness)
        reports.append(report)

        # Phase 3: Decide
        if report.status == Status.PASS and config.stop_on_pass:
            return {
                "plan": plan,
                "iterations": iteration,
                "reports": reports,
                "status": "PASS",
                "final_score": report.overall_score
            }

        if iteration == config.max_iterations:
            # Best effort - return last plan
            return {
                "plan": plan,
                "iterations": iteration,
                "reports": reports,
                "status": "MAX_ITERATIONS",
                "final_score": report.overall_score,
                "unresolved_issues": report.critical_issues + report.warnings
            }

        if report.status == Status.REJECT:
            return {
                "plan": None,
                "iterations": iteration,
                "reports": reports,
                "status": "REJECTED",
                "reason": "Plan rejected by checker"
            }

        iteration += 1

def planner_create(request: PlannerRequest) -> ET.Element:
    """
    Create initial plan from request.

    In practice, this invokes the Planner sub-agent:

    Task(
        prompt=format_planner_prompt(request),
        subagent_type="bb5-planner"
    )
    """
    # Implementation would invoke sub-agent
    pass

def planner_revise(plan: ET.Element, feedback: CheckerReport) -> ET.Element:
    """
    Revise plan based on checker feedback.

    Task(
        prompt=format_revision_prompt(plan, feedback),
        subagent_type="bb5-planner"
    )
    """
    # Implementation would invoke sub-agent
    pass

def checker_validate(
    plan: ET.Element,
    request: PlannerRequest,
    strictness: str
) -> CheckerReport:
    """
    Validate plan against 7 dimensions.

    Task(
        prompt=format_checker_prompt(plan, request, strictness),
        subagent_type="bb5-checker"
    )
    """
    # Implementation would invoke sub-agent
    pass

# Example usage
if __name__ == "__main__":
    request = PlannerRequest(
        objective={
            "goal": "Implement user authentication system",
            "context": "Web application needs secure login"
        },
        requirements={
            "functional": [
                "Users can register with email/password",
                "Users can log in with credentials",
                "Passwords must be hashed"
            ],
            "non_functional": [
                "Response time < 200ms",
                "Secure against OWASP top 10"
            ]
        },
        success_criteria=[
            {"criterion": "Login endpoint returns JWT", "measurable": True},
            {"criterion": "Registration validates email", "measurable": True}
        ]
    )

    result = run_planner_checker_loop(request)
    print(f"Loop completed in {result['iterations']} iterations")
    print(f"Final status: {result['status']}")
    print(f"Final score: {result['final_score']}")
```

### Bash Implementation

```bash
#!/bin/bash
# Planner+Checker Loop - Bash Implementation

MAX_ITERATIONS=3
STRICTNESS="standard"

run_planner_checker_loop() {
    local request_file="$1"
    local iteration=1
    local plan_file="plan-v1.xml"

    while [ $iteration -le $MAX_ITERATIONS ]; do
        echo "=== Iteration $iteration ==="

        # Phase 1: Plan or Revise
        if [ $iteration -eq 1 ]; then
            echo "Creating initial plan..."
            planner_create "$request_file" > "$plan_file"
        else
            echo "Revising plan based on feedback..."
            planner_revise "$plan_file" "feedback-v$((iteration-1)).yaml" > "plan-v${iteration}.xml"
            plan_file="plan-v${iteration}.xml"
        fi

        # Phase 2: Check
        echo "Running checker..."
        checker_validate "$plan_file" "$request_file" "$STRICTNESS" > "feedback-v${iteration}.yaml"

        # Phase 3: Check result
        local status=$(yq '.summary.status' "feedback-v${iteration}.yaml")
        local score=$(yq '.summary.overall_score' "feedback-v${iteration}.yaml")

        echo "Status: $status, Score: $score"

        if [ "$status" == "PASS" ]; then
            echo "Plan passed validation!"
            cp "$plan_file" "plan-final.xml"
            return 0
        fi

        if [ $iteration -eq $MAX_ITERATIONS ]; then
            echo "Max iterations reached. Using best effort plan."
            cp "$plan_file" "plan-final.xml"
            return 1
        fi

        iteration=$((iteration + 1))
    done
}

planner_create() {
    local request="$1"
    # Invoke planner sub-agent
    claude subagent bb5-planner --input "$request"
}

planner_revise() {
    local plan="$1"
    local feedback="$2"
    # Invoke planner sub-agent in revision mode
    claude subagent bb5-planner --input "$plan" --feedback "$feedback" --mode revise
}

checker_validate() {
    local plan="$1"
    local request="$2"
    local strictness="$3"
    # Invoke checker sub-agent
    claude subagent bb5-checker --input "$plan" --request "$request" --strictness "$strictness"
}

# Usage
run_planner_checker_loop "request.yaml"
```

---

## 6. Integration with BB5

### Using with Architecture Workflows

The Planner+Checker loop integrates with BB5's architecture workflows:

```yaml
# In create-architecture.yaml
steps:
  - name: analyze-requirements
    # ... existing steps

  - name: create-implementation-plan
    title: Create Implementation Plan
    description: Generate detailed implementation plan with Planner+Checker
    actions:
      - Run planner-checker loop
      - Store final plan in artifacts/
    loop:
      enabled: true
      max_iterations: 3
      strictness: standard
    outputs:
      - type: artifact
        location: ./artifacts/implementation-plan.xml
```

### Integration Points

| BB5 Component | Integration |
|---------------|-------------|
| **RALF** | Can spawn planner-checker loop for complex planning tasks |
| **BMAD Skills** | `bmad-planning` skill can use loop internally |
| **Orchestrator** | Thin orchestration - spawns planner and checker agents |
| **Task System** | Plans feed into BB5 task creation |
| **State Management** | Loop state tracked in STATE.yaml |

### Sub-Agent Definitions

Create these sub-agents in your BB5 instance:

**bb5-planner** (`2-engine/agents/definitions/claude-native/planner/bb5-planner.md`):
```yaml
---
name: bb5-planner
description: Creates actionable implementation plans with tasks, dependencies, and acceptance criteria
tools: Read, Write, Edit
model: sonnet
color: blue
---
# [Full planner prompt from Section 3]
```

**bb5-checker** (`2-engine/agents/definitions/claude-native/checker/bb5-checker.md`):
```yaml
---
name: bb5-checker
description: Validates plans against 7 dimensions and provides structured feedback
tools: Read, Grep, Bash
model: sonnet
color: red
---
# [Full checker prompt from Section 4]
```

### Workflow Integration Example

```python
# In an orchestrator workflow
from claude_native import Task

def create_architecture_with_plan(prd_path: str):
    # 1. Run 4 parallel researchers (existing pattern)
    research_tasks = [
        Task(prompt=f"Analyze {prd_path}", subagent_type="bb5-stack-researcher"),
        Task(prompt=f"Analyze {prd_path}", subagent_type="bb5-architecture-researcher"),
        Task(prompt=f"Analyze {prd_path}", subagent_type="bb5-convention-researcher"),
        Task(prompt=f"Analyze {prd_path}", subagent_type="bb5-risk-researcher"),
    ]
    research_results = [t.result() for t in research_tasks]

    # 2. Create architecture (existing pattern)
    architecture = Task(
        prompt=f"Create architecture based on research",
        subagent_type="bb5-architect",
        context=research_results
    ).result()

    # 3. Planner+Checker loop for implementation plan
    plan_result = run_planner_checker_loop(
        request=PlannerRequest(
            objective={"goal": "Implement the architecture"},
            requirements=extract_requirements(architecture),
            success_criteria=extract_criteria(architecture)
        ),
        config=LoopConfig(max_iterations=3, strictness="standard")
    )

    return {
        "architecture": architecture,
        "implementation_plan": plan_result["plan"],
        "plan_quality_score": plan_result["final_score"]
    }
```

---

## 7. When to Use

### Use Planner+Checker Loop When:

| Scenario | Why |
|----------|-----|
| **Complex features** (> 5 tasks) | Ensures completeness and proper sequencing |
| **Cross-team dependencies** | Validates external dependency handling |
| **High-stakes deliverables** | Production releases, customer commitments |
| **Novel problem domains** | Ensures all unknowns are surfaced |
| **Architecture changes** | Validates technical decisions |
| **Multi-phase projects** | Ensures phase transitions are planned |

### Skip the Loop When:

| Scenario | Alternative |
|----------|-------------|
| **Simple bug fixes** (< 30 min) | Direct execution |
| **Clear, single-task work** | bb5-executor directly |
| **Rapid prototyping** | Lenient mode or skip |
| **Emergency fixes** | Speed over planning |
| **Well-understood patterns** | Template-based planning |

### Decision Matrix

```
Complexity │ Dependencies │ Stakes    │ Use Loop?
───────────┼──────────────┼───────────┼──────────
High       │ High         │ High      │ YES - Strict
High       │ High         │ Medium    │ YES - Standard
High       │ Low          │ High      │ YES - Standard
High       │ Low          │ Low       │ MAYBE - Lenient
Medium     │ High         │ High      │ YES - Standard
Medium     │ High         │ Low       │ MAYBE - Lenient
Medium     │ Low          │ Any       │ OPTIONAL
Low        │ Any          │ Any       │ NO
```

### Cost-Benefit Analysis

| Factor | With Loop | Without Loop |
|--------|-----------|--------------|
| **Planning time** | 2-5x longer | Faster initial plan |
| **Plan quality** | Higher | Variable |
| **Execution success** | Higher | Variable |
| **Rework needed** | Lower | Higher |
| **Context usage** | Higher (multiple agents) | Lower |

**Recommendation:** Use the loop when the cost of rework exceeds the cost of planning.

---

## 8. Best Practices

### For the Planner

1. **Be specific** - Vague tasks lead to vague execution
2. **Include verification** - Every task needs a "how do I know it's done"
3. **Surface risks early** - Better to know blockers now than later
4. **Use realistic estimates** - Checkers will flag unrealistic ones
5. **Define done clearly** - Acceptance criteria should be testable

### For the Checker

1. **Be constructive** - Find problems, but suggest fixes
2. **Prioritize issues** - Critical first, info last
3. **Check verifiability** - Criteria must be measurable
4. **Validate dependencies** - Orphaned tasks are red flags
5. **Consider context** - Strictness should match stakes

### For the Loop

1. **Set max iterations** - 3 is usually enough
2. **Stop on PASS** - Don't over-iterate
3. **Escalate blocks** - Human judgment for critical issues
4. **Track metrics** - Score trends over time
5. **Learn from rejections** - Update templates based on common issues

---

## 9. Example: Complete Loop Session

### Request

```yaml
planner_request:
  objective:
    goal: "Add OAuth2 authentication to the API"
    context: "Users need to log in with Google and GitHub"
  requirements:
    functional:
      - "Support Google OAuth"
      - "Support GitHub OAuth"
      - "Generate JWT tokens"
      - "Store user profiles"
    non_functional:
      - "OAuth flow < 5 seconds"
      - "Secure token storage"
  success_criteria:
    - "User can complete Google OAuth flow"
    - "User can complete GitHub OAuth flow"
    - "JWT tokens are valid for 24 hours"
```

### Iteration 1

**Planner Output:** Plan with 5 tasks

**Checker Report:**
```yaml
summary:
  status: "NEEDS_REVISION"
  overall_score: 65
  critical_issues: 1
  warnings: 2

issues:
  - severity: "critical"
    description: "No task for handling OAuth callback errors"
    suggestion: "Add error handling task"
  - severity: "warning"
    description: "Token storage task doesn't specify encryption"
    suggestion: "Add encryption requirement"
```

### Iteration 2

**Planner Output:** Revised plan with 7 tasks (added error handling, encryption)

**Checker Report:**
```yaml
summary:
  status: "NEEDS_REVISION"
  overall_score: 82
  critical_issues: 0
  warnings: 1

issues:
  - severity: "warning"
    description: "Missing rollback strategy if OAuth provider changes API"
    suggestion: "Add monitoring and fallback task"
```

### Iteration 3

**Planner Output:** Final plan with 8 tasks (added monitoring)

**Checker Report:**
```yaml
summary:
  status: "PASS"
  overall_score: 91
  critical_issues: 0
  warnings: 0
```

**Final Output:** High-quality plan ready for execution.

---

## 10. References

- **GSD Framework:** `/Users/shaansisodia/.blackbox5/6-roadmap/_research/external/GitHub/get-shit-done/`
- **Planner Sub-Agent:** `/Users/shaansisodia/.blackbox5/2-engine/agents/definitions/sub-agents/planner/SUBAGENT.md`
- **Validator Sub-Agent:** `/Users/shaansisodia/.blackbox5/2-engine/agents/definitions/sub-agents/validator/SUBAGENT.md`
- **BB5 Executor:** `/Users/shaansisodia/.blackbox5/2-engine/agents/definitions/claude-native/execution/bb5-executor.md`
- **BB5 Verifier:** `/Users/shaansisodia/.blackbox5/2-engine/agents/definitions/claude-native/execution/bb5-verifier.md`
- **Create Architecture Workflow:** `/Users/shaansisodia/.blackbox5/2-engine/instructions/workflows/create-architecture.yaml`

---

## Appendix: XML Schema Definition

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="plan">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="objective" type="ObjectiveType"/>
        <xs:element name="phases" type="PhasesType"/>
        <xs:element name="dependencies" type="DependenciesType" minOccurs="0"/>
        <xs:element name="resource_plan" type="ResourcePlanType" minOccurs="0"/>
        <xs:element name="timeline" type="TimelineType" minOccurs="0"/>
        <xs:element name="risk_register" type="RiskRegisterType" minOccurs="0"/>
        <xs:element name="next_action" type="NextActionType"/>
      </xs:sequence>
      <xs:attribute name="id" type="xs:string" use="required"/>
    </xs:complexType>
  </xs:element>

  <xs:complexType name="ObjectiveType">
    <xs:sequence>
      <xs:element name="goal" type="xs:string"/>
      <xs:element name="success_criteria">
        <xs:complexType>
          <xs:sequence>
            <xs:element name="criterion" maxOccurs="unbounded">
              <xs:complexType>
                <xs:sequence>
                  <xs:element name="description" type="xs:string"/>
                  <xs:element name="verification" type="xs:string"/>
                </xs:sequence>
                <xs:attribute name="id" type="xs:string" use="required"/>
                <xs:attribute name="testable" type="xs:boolean" use="required"/>
              </xs:complexType>
            </xs:element>
          </xs:sequence>
        </xs:complexType>
      </xs:element>
    </xs:sequence>
  </xs:complexType>

  <!-- Additional type definitions... -->
</xs:schema>
```

---

*Document Version: 1.0*
*Last Updated: 2026-02-07*
*Maintainer: BlackBox5 Architecture Team*
