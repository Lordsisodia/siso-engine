---
name: superintelligence-protocol
description: Activate superintelligence for complex problem-solving
category: protocol
agent: Protocol
role: Superintelligence
trigger: Complex tasks, architecture decisions, high uncertainty, novel problems
inputs:
  - name: task
    type: string
    description: Complex task or problem to solve
outputs:
  - name: recommendation
    type: document
    description: Analysis and recommendation with confidence score
---

# Superintelligence Protocol

## When to Use

Activate Superintelligence Protocol when:
- Task involves architecture or system design
- Multiple approaches possible, need to choose best
- High uncertainty or novel problem
- Impact spans multiple components
- Requires deep analysis before implementation
- Keywords: architecture, design, complex, uncertain, redesign, optimize

Do NOT use for:
- Simple bug fixes
- Routine edits
- Well-defined single-file changes
- Information lookups

## Activation Phrase

```
Activate superintelligence protocol for [task]
```

Or shorthand:
```
SP [task]
```

## The 7-Step Process

### Step 1: Context Gathering

Deploy context gatherer sub-agents to scan relevant projects and folders.

**Output:** Structured project summary with key files, dependencies, architecture

### Step 2: First Principles Decomposition

Break the problem down:
- What are the fundamental requirements?
- What constraints are inviolable?
- What are we assuming that might be wrong?
- What would we do if starting from scratch?

**Document:** `FIRST-PRINCIPLES.md`

### Step 3: Information Gap Analysis

Identify what's unknown:
- What do we need to know to decide?
- What could disprove our approach?
- What similar problems have been solved?
- What are best practices in this domain?

### Step 4: Active Information Gathering

Search and verify:
- Search documentation
- Check examples
- Execute tests

### Step 5: Multi-Perspective Analysis

Deploy expert agents:

**Architect Agent:** Analyze system design implications
**Researcher Agent:** Find existing solutions
**Critic Agent:** Challenge assumptions
**Synthesizer Agent:** Integrate perspectives

### Step 6: Meta-Cognitive Check

Ask:
- Do I need more information?
- Am I thinking correctly?

**Halting Conditions:**
- Confidence > 85%
- No critical gaps remain
- Max iterations (5) reached

### Step 7: Synthesis & Output

Produce:
1. **Recommendation** - Clear proposed approach
2. **Confidence Score** - 0-100%
3. **Key Assumptions** - What we're betting on
4. **Risks** - What could go wrong
5. **Alternatives Considered** - Why not those
6. **Implementation Path** - Next steps

## Output Format

```yaml
protocol_execution:
  task: "Original task description"
  timestamp: "2026-01-31T20:00:00Z"
  iterations: 3

synthesis:
  recommendation: "Clear recommendation"
  confidence: 87
  key_assumptions:
    - "Assumption 1"
  risks:
    - "Risk 1: mitigation"
  implementation_path:
    - "Step 1"
    - "Step 2"
```

## Integration with BMAD

After protocol completes, hand off to appropriate BMAD role:
- **Recommendation is architectural** → BMAD Architect (CA)
- **Recommendation is product feature** → BMAD PM (CP)
- **Recommendation is implementation** → BMAD Dev (CD)
- **Recommendation needs testing** → BMAD QA (QA)

## Time Budget

| Phase | Max Time | Token Budget |
|-------|----------|--------------|
| Context Gathering | 2 min | 10K |
| First Principles | 3 min | 15K |
| Information Gathering | 5 min | 20K |
| Expert Analysis | 8 min | 30K |
| Synthesis | 2 min | 10K |
| **Total** | **20 min** | **85K** |

## Example Usage

**Task:** "Design new authentication system"

**Protocol Execution:**
1. Scan current auth implementation
2. Decompose: session management, credential storage, MFA, SSO
3. Research: OAuth2 vs JWT vs Sessions
4. Expert analysis on trade-offs
5. Synthesis: "Use short-lived JWTs (15min) with Redis revocation list"

**Output:** Recommendation with 90% confidence, implementation path
