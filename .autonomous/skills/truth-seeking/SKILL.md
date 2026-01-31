---
id: truth-seeking
name: Truth-Seeking Protocol
version: 1.0.0
category: core
description: Validate assumptions and verify facts before acting to ensure correctness
trigger: When confidence is low, before acting on uncertain information
inputs:
  - name: statement
    type: string
    required: true
    description: The assumption or fact to validate
  - name: validation_type
    type: string
    required: false
    description: "assumption | fact | hypothesis"
    default: assumption
  - name: required_confidence
    type: number
    required: false
    description: Confidence threshold (0-100)
    default: 70
outputs:
  - name: validation_report
    type: object
    description: Complete validation results
commands:
  - validate-assumption
  - verify-fact
  - self-correct
---

# Truth-Seeking Protocol

## Purpose

Prevent errors by validating assumptions before acting. Catch mistakes early when they're cheap to fix.

## When to Use

- Before implementing based on an assumption
- When something "feels wrong"
- After 3 steps without validation
- When confidence drops below 70%

## Core Principle

**"Trust but verify"** — Every assumption is guilty until proven innocent.

---

## Command: validate-assumption

### Input
- `statement`: The assumption to validate
- `required_confidence`: Minimum confidence to proceed (default: 70%)

### Process (10-Step Validation Loop)

1. **State the assumption clearly**
   - Write down exactly what you're assuming
   - No ambiguity, no hand-waving

2. **Identify what would falsify it**
   - What evidence would prove this wrong?
   - Look for disconfirming evidence first

3. **Research the facts**
   - Check documentation
   - Read code
   - Query database
   - Use MCP tools as needed

4. **Find corroborating evidence**
   - Multiple sources preferred
   - Primary sources over secondary

5. **Calculate confidence score**
   - 0-100% based on evidence quality
   - Document reasoning

6. **Compare to threshold**
   - If ≥ required_confidence: Proceed
   - If < required_confidence: Research more or escalate

7. **Document in ASSUMPTIONS.md**
   - Assumption statement
   - Evidence found
   - Confidence score
   - Decision (proceed/block)

8. **If blocked: Escalate or research**
   - Spawn sub-agent for deep research
   - Ask for human clarification
   - Mark task blocked

9. **If proceeding: Monitor for contradictions**
   - Watch for evidence that contradicts assumption
   - Be ready to self-correct

10. **Re-validate if context changes**
    - New information may invalidate previous validation

### Output

```yaml
validation_report:
  assumption: "string"
  confidence: 85
  evidence:
    - source: "file path or doc"
      finding: "what was found"
    - source: "database query"
      finding: "result"
  falsification_attempted: true
  contradictions_found: []
  decision: "proceed"  # proceed | block | research-more
  reasoning: "why this decision was made"
```

---

## Command: verify-fact

### Input
- `fact`: The factual claim to verify
- `sources`: Where to look for verification

### Process

1. **Identify primary sources**
   - Code (ground truth)
   - Documentation
   - Database schema
   - API contracts

2. **Check each source**
   - Does the fact match reality?
   - Note any discrepancies

3. **Cross-reference**
   - Multiple sources saying the same thing?
   - Any conflicts between sources?

4. **Report findings**
   - Verified: Fact is correct
   - Partial: Fact is mostly correct with caveats
   - Incorrect: Fact is wrong

### Output

```yaml
verification_report:
  fact: "string"
  status: "verified"  # verified | partial | incorrect
  sources_checked:
    - source: "path"
      finding: "matches | differs | not-found"
  discrepancies: []
  corrected_fact: "string (if needed)"
```

---

## Command: self-correct

### When to Invoke

Every 3 steps, ask:
- "Am I still solving the right problem?"
- "Has my approach drifted from the objective?"
- "Is there a better way to do this?"
- "Am I making progress or spinning?"

### Process

1. **Review original objective**
   - What was the task asking for?
   - What does "done" look like?

2. **Compare to current path**
   - Are you heading toward the goal?
   - Have you deviated?

3. **Check for better approaches**
   - Is there a simpler way?
   - Did you miss something?

4. **Decide: Continue, Pivot, or Halt**
   - Continue: Stay on current path
   - Pivot: Change approach
   - Halt: Stop and reassess

### Output

```yaml
correction_report:
  original_objective: "string"
  current_path: "description"
  drift_detected: false
  decision: "continue"  # continue | pivot | halt
  new_approach: "string (if pivoting)"
  reasoning: "why"
```

---

## Three Validation Gates

### Gate 1: Assumption Gate
**Question:** "What am I assuming?"

**Check:**
- List all assumptions in current step
- Which ones are critical?
- Which ones are unverified?

**Action:** Validate critical unverified assumptions

### Gate 2: Coherence Gate
**Question:** "Does this make sense?"

**Check:**
- Is this consistent with what I know?
- Does this align with the task objective?
- Would a reasonable person agree?

**Action:** If incoherent, re-analyze from first principles

### Gate 3: Evidence Gate
**Question:** "How do I know this is true?"

**Check:**
- What evidence supports this?
- Is the evidence reliable?
- Could there be alternative explanations?

**Action:** Find proof or mark as unverified

---

## Examples

### Example 1: Validating an Assumption

```markdown
**Assumption:** "The user table has an email column"

**Process:**
1. State: "Users table has email column"
2. Falsify: Check schema - if no email column, assumption is wrong
3. Research: Query Supabase for users table schema
4. Evidence: Found email column in schema
5. Confidence: 100% (direct observation)
6. Threshold: 70% required, 100% achieved
7. Document: Added to ASSUMPTIONS.md
8. Decision: Proceed

**Output:**
validation_report:
  assumption: "Users table has email column"
  confidence: 100
  evidence:
    - source: "supabase schema"
      finding: "email column exists, type: varchar(255)"
  decision: "proceed"
```

### Example 2: Self-Correction Triggered

```markdown
**Step 5 of 10:** Implementing OAuth

**Self-Correction Check:**
1. Original objective: "Add user authentication"
2. Current path: Implementing full OAuth2 flow with 5 providers
3. Drift detected: YES - over-engineering
4. Better approach: Start with email/password, add OAuth later
5. Decision: Pivot

**Correction:**
correction_report:
  original_objective: "Add user authentication"
  current_path: "Full OAuth2 with 5 providers"
  drift_detected: true
  decision: "pivot"
  new_approach: "Email/password first, OAuth as phase 2"
  reasoning: "Original scope didn't specify OAuth, over-engineering"
```

---

## Quality Checklist

- [ ] Every assumption validated before acting
- [ ] Self-correction check every 3 steps
- [ ] Confidence score documented
- [ ] Evidence cited
- [ ] Contradictions caught early
- [ ] Course corrections logged
