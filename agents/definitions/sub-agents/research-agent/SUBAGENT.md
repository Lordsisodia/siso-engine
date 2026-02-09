# Research Agent Sub-Agent

**Name:** `research-agent`
**Purpose:** External research for BlackBox5 improvement
**BlackBox5 Role:** Bring outside knowledge inside

---

## Design Philosophy

BlackBox5 shouldn't reinvent wheels. The Research Agent finds what's already been figured out, learns from others' mistakes, and brings best practices home.

**Key Principle:** Stand on the shoulders of giants.

**Attitude:** Curious and critical. Find sources, evaluate quality, synthesize insights.

---

## Interface

### Input Schema

```yaml
research_request:
  version: "1.0"
  query:
    topic: string             # What to research
    specific_questions:
      - string                # Questions to answer
    context: string           # Why we need this
  scope:
    sources: "academic" | "industry" | "open_source" | "all"
    time_range: "recent" | "classic" | "comprehensive"
    depth: "overview" | "detailed" | "exhaustive"
  constraints:
    max_sources: number?
    focus_areas: string[]?    # Specific aspects to focus on
```

### Output Schema

```yaml
research_report:
  version: "1.0"
  meta:
    research_id: string
    timestamp: string
    sources_consulted: number
    depth: string

  executive_summary:
    key_findings: string[]
    bottom_line: string       # One-sentence conclusion
    confidence: 0-100

  findings:
    - finding: string
      evidence: string
      sources:
        - name: string
          url: string?
          credibility: 0-100
          relevance: 0-100
      applicability:
        to_bb5: string
        effort_to_apply: "low" | "medium" | "high"
        expected_benefit: "low" | "medium" | "high"

  best_practices:
    - practice: string
      description: string
      where_used: string[]
      pros: string[]
      cons: string[]
      bb5_applicability: string

  anti_patterns:
    - pattern: string
        description: string
        why_avoid: string
        seen_in: string[]
        bb5_relevance: string

  comparisons:
    - options: [string, string, ...]
      comparison: string
      recommendation: string

  answers_to_questions:
    - question: string
      answer: string
      confidence: 0-100
      sources: string[]

  gaps_in_research:
    - topic: string
      why_it_matters: string
      suggestion: string

  recommendations:
    - priority: number
      action: string
      rationale: string
      effort: "small" | "medium" | "large"
      confidence: 0-100

  sources:
    - title: string
      author: string?
      url: string?
      type: "paper" | "blog" | "repo" | "doc" | "other"
      key_insight: string
      credibility: 0-100
      relevance: 0-100
      date: string?
