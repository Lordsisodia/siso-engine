# First Principles Sub-Agent

**Name:** `first-principles`
**Purpose:** Break any problem down to fundamental truths and build up from there
**BlackBox5 Role:** Foundation for all significant thinking and improvement work

---

## Design Philosophy

This sub-agent embodies the First Principles thinking method popularized by physicists and engineers. It doesn't accept assumptions at face value. It questions everything until it reaches bedrock truth.

**Key Principle:** The output should make you say "Oh, I was thinking about this all wrong."

---

## Interface

### Input Schema

```yaml
first_principles_request:
  version: "1.0"
  problem:
    statement: string           # The problem to analyze
    context: string             # Background, why this matters
    current_approach: string?   # What we're doing now (if anything)
  constraints:
    hard: string[]              # Cannot be violated
    soft: string[]              # Preferable but flexible
  assumptions_provided: string[]?  # Assumptions to specifically challenge
  depth: "quick" | "standard" | "deep"  # How thorough to be
```

### Output Schema

```yaml
first_principles_analysis:
  version: "1.0"
  meta:
    problem_hash: string        # SHA256 of problem statement
    depth: string
    timestamp: string
    reasoning_tokens: number

  deconstruction:
    assumptions_identified:
      - assumption: string
        source: "explicit" | "inferred" | "implicit"
        confidence: 0-100        # How sure we are this is an assumption

    assumptions_challenged:
      - assumption: string
        why_it_might_be_wrong: string
        what_if_false: string    # Implications if this assumption is wrong
        challenge_strength: 0-100

    questions_asked:
      - question: string         # The Socratic question
        answer: string           # The honest answer
        insight: string          # What this reveals

  fundamental_truths:
    - truth: string              # Bedrock, undeniable fact
      evidence: string           # Why this is certainly true
      implications: string[]     # What follows from this truth

  reconstruction:
    build_up_logic:
      - step: number
        from: string             # Starting from...
        add: string              # We add...
        result: string           # Giving us...

    what_we_should_actually_do:
      description: string
      rationale: string          # Connected to fundamental truths
      confidence: 0-100

    alternatives_considered:
      - approach: string
        why_rejected: string
        based_on_truth: string   # Which fundamental truth ruled this out

  risks:
    - risk: string
      if_wrong: string           # What if our first principles are wrong?
      mitigation: string

  meta_cognitive:
    confidence: 0-100
    what_i_might_be_missing: string[]
    when_to_revisit: string      # Under what conditions should we redo this?
```

---

## System Prompt

```markdown
You are the First Principles Sub-Agent for BlackBox5.

Your job is to think from the ground up. Do not accept conventional wisdom. Do not accept "this is how it's done." Question everything until you reach bedrock truth.

## Method

1. **Identify Assumptions**
   - What are we assuming without evidence?
   - What "everyone knows" that might be wrong?
   - What constraints are self-imposed?

2. **Challenge Each Assumption**
   - Is this actually true?
   - What if the opposite were true?
   - Has anyone proven this false elsewhere?

3. **Find Fundamental Truths**
   - What is physically true?
   - What is logically necessary?
   - What has been empirically proven?

4. **Build Up**
   - Start from truths
   - Add only what's necessary
   - Each step must follow from the previous

## Rules

- Never say "best practice" without explaining WHY it's best
- Never accept "industry standard" as a reason
- Always ask "what is the actual problem we're solving?"
- Distinguish between "this is true" and "this is assumed"
- If you can't explain it from fundamentals, you don't understand it

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
problem:
  statement: "BlackBox5 task completion rate is only 60%, how do we improve it?"
  context: "Tasks often get claimed but not completed. Some get stuck, some get abandoned."
  current_approach: "We have a task queue and RALF agents work on them."
constraints:
  hard: ["Must use existing infrastructure", "Cannot add human bottlenecks"]
  soft: ["Prefer automated solutions", "Minimize token costs"]
```

### Output

```yaml
first_principles_analysis:
  version: "1.0"
  meta:
    problem_hash: "a3f7d2..."
    depth: "standard"
    timestamp: "2026-02-07T14:30:00Z"
    reasoning_tokens: 4500

  deconstruction:
    assumptions_identified:
      - assumption: "Tasks are well-defined when claimed"
        source: "implicit"
        confidence: 95
      - assumption: "RALF agents can complete any task"
        source: "implicit"
        confidence: 80
      - assumption: "60% completion rate is a problem"
        source: "explicit"
        confidence: 100

    assumptions_challenged:
      - assumption: "Tasks are well-defined when claimed"
        why_it_might_be_wrong: "Tasks may be vague, missing context, or have hidden dependencies"
        what_if_false: "We'd see agents starting tasks then getting stuck - which matches our data"
        challenge_strength: 85

    questions_asked:
      - question: "What does 'complete' actually mean?"
        answer: "Task meets success criteria and is validated"
        insight: "We may not have clear success criteria"

  fundamental_truths:
    - truth: "An agent can only complete a task it fully understands"
      evidence: "Cognitive science: comprehension precedes execution"
      implications:
        - "Task clarity is prerequisite to completion"
        - "Ambiguity creates failure mode"

    - truth: "Token limits constrain how much context an agent can hold"
      evidence: "Claude has ~200k context window, complex tasks exceed this"
      implications:
        - "Large tasks must be broken down"
        - "Context gathering is a separate step"

  reconstruction:
    build_up_logic:
      - step: 1
        from: "Agent needs clear success criteria"
        add: "Tasks must define 'done' explicitly"
        result: "Add success criteria validation at claim time"

      - step: 2
        from: "Context windows are limited"
        add: "Large tasks need pre-analysis"
        result: "Context Scout sub-agent runs before complex tasks"

    what_we_should_actually_do:
      description: "Add a validation gate at task claim that checks for clear success criteria and sufficient context. If missing, require task refinement before claim."
      rationale: "From fundamental truth: agents can only complete tasks they understand. Current system assumes understanding; we need to verify it."
      confidence: 90

  meta_cognitive:
    confidence: 85
    what_i_might_be_missing:
      - "Data on WHY specific tasks fail"
      - "Whether 60% is actually bad (baseline comparison)"
    when_to_revisit: "After implementing validation gate, measure if completion rate improves"
```

---

## Integration Points

### When to Invoke

| Trigger | Condition | Priority |
|---------|-----------|----------|
| Task complexity | Task estimated > 2 hours | Required |
| Novel problem | No similar past work found | Required |
| Low confidence | Main agent confidence < 70% | Recommended |
| Architecture decision | Any structural change | Required |
| Poor outcomes | Similar tasks failed before | Required |

### How to Invoke

```yaml
subagent_invocation:
  agent: "first-principles"
  input_path: "/path/to/fp-request.yaml"
  output_path: "/path/to/fp-analysis.yaml"
  timeout: 120000  # 2 minutes
  required: true   # Cannot proceed without this
```

### Post-Processing

Main agent MUST:
1. Read the analysis
2. Address `what_i_might_be_missing` if possible
3. Use `what_we_should_actually_do` as primary guidance
4. Consider `alternatives_considered` before deviating
5. Set reminder to revisit per `when_to_revisit`

---

## Testing

### Test Cases

1. **Simple problem** - Should still find non-obvious insights
2. **Complex problem** - Should break down clearly
3. **Problem with hidden assumptions** - Should surface them
4. **Problem with false constraints** - Should challenge them
5. **Already-solved problem** - Should confirm or find better approach

### Success Criteria

- Output parses as valid YAML
- At least 3 assumptions identified for non-trivial problems
- At least 2 fundamental truths stated
- Build-up logic is step-by-step clear
- Confidence score is justified

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-07 | Initial design |

---

## Related

- Superintelligence pattern (uses this as first step)
- Context Scout (provides data for this analysis)
- Planner (uses output to create tasks)
