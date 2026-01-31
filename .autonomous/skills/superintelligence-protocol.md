# Superintelligence Protocol Skill

**Skill ID:** SP
**Agent:** Protocol
**Purpose:** Activate superintelligence for complex problem-solving
**Activation:** "SP <task description>" or automatic for complex tasks

---

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

---

## Activation Phrase

```
Activate superintelligence protocol for [task]
```

Or shorthand:
```
SP [task]
```

---

## The 7-Step Process

### Step 1: Context Gathering
Deploy context gatherer sub-agents:
```bash
# Scan relevant projects
context-gatherer --project blackbox5 --depth 3

# Scan specific folders
context-gatherer --folder 2-engine/core --depth 2
context-gatherer --folder 6-roadmap --depth 2
```

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
```bash
# Search documentation
web-search "best practices [technology]"

# Check examples
find-examples --domain [domain] --technology [tech]

# Execute tests
run-test --hypothesis [hypothesis]
```

### Step 5: Multi-Perspective Analysis
Deploy expert agents:

**Architect Agent:**
```
Analyze system design implications
Identify coupling and cohesion issues
Evaluate scalability and maintainability
```

**Researcher Agent:**
```
Find existing solutions to similar problems
Compare alternative approaches
Identify hidden constraints
```

**Critic Agent:**
```
Challenge all assumptions
Identify failure modes
Find edge cases
```

**Synthesizer Agent:**
```
Integrate all perspectives
Identify conflicts and resolutions
Formulate recommendation
```

### Step 6: Meta-Cognitive Check
Ask:
- Do I need more information? (If yes, return to Step 4)
- What information do I need?
- Am I thinking correctly? (Check for biases)

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

**Document:** `PROTOCOL-OUTPUT.md`

---

## Output Format

```yaml
protocol_execution:
  task: "Original task description"
  timestamp: "2026-01-31T20:00:00Z"
  iterations: 3

context:
  projects_scanned: ["blackbox5"]
  folders_scanned: ["2-engine/core", "6-roadmap"]
  key_files_identified: 12

analysis:
  first_principles:
    - "Requirement 1"
    - "Requirement 2"
  assumptions_challenged:
    - "Assumption 1: [original] → [revised]"

expert_assessments:
  architect:
    recommendation: "..."
    confidence: 90
    concerns: ["..."]
  researcher:
    findings: "..."
    alternatives: ["..."]
  critic:
    risks: ["..."]
    edge_cases: ["..."]

synthesis:
    recommendation: "Clear recommendation"
    confidence: 87
    key_assumptions:
      - "Assumption 1"
      - "Assumption 2"
    risks:
      - "Risk 1: mitigation"
    alternatives_considered:
      - "Alternative 1: why rejected"
    implementation_path:
      - "Step 1"
      - "Step 2"
```

---

## Integration with BMAD

After protocol completes, hand off to appropriate BMAD role:

- **Recommendation is architectural** → BMAD Architect (CA)
- **Recommendation is product feature** → BMAD PM (CP)
- **Recommendation is implementation** → BMAD Dev (CD)
- **Recommendation needs testing** → BMAD QA (QA)

---

## Time Budget

| Phase | Max Time | Token Budget |
|-------|----------|--------------|
| Context Gathering | 2 min | 10K |
| First Principles | 3 min | 15K |
| Information Gathering | 5 min | 20K |
| Expert Analysis | 8 min | 30K |
| Synthesis | 2 min | 10K |
| **Total** | **20 min** | **85K** |

If budget exceeded, create sub-tasks and delegate.

---

## Success Metrics

Track in `PROTOCOL-METRICS.md`:
- Activations per day
- Average confidence score
- Expert roles used
- Time per execution
- Tasks created from protocol

---

## Example Usage

### Example 1: Architecture Decision

**Task:** "Design new authentication system"

**Protocol Execution:**
1. Scan current auth implementation
2. Decompose: session management, credential storage, MFA, SSO
3. Research: OAuth2 vs JWT vs Sessions
4. Expert analysis:
   - Architect: "JWT with refresh tokens, stateless"
   - Researcher: "Industry moving to short-lived JWTs"
   - Critic: "Token revocation is hard"
5. Synthesis: "Use short-lived JWTs (15min) with Redis revocation list"

**Output:** Recommendation with 90% confidence, implementation path

### Example 2: Technology Selection

**Task:** "Choose message queue for event system"

**Protocol Execution:**
1. Scan current event handling
2. Decompose: throughput, latency, durability, ops complexity
3. Research: Kafka vs RabbitMQ vs Redis Streams
4. Expert analysis on each option
5. Synthesis: "Redis Streams for simplicity, migrate to Kafka if scale > 10K msg/s"

---

## Error Handling

If protocol fails:
1. Document failure mode in `PROTOCOL-ERRORS.md`
2. Fall back to standard BMAD workflow
3. Create task to fix protocol issue
4. Reduce confidence score for future similar tasks

---

## Version History

- **v1.0** (2026-01-31) - Initial integration with RALF
