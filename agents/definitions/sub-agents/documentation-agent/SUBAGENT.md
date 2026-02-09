# Documentation Agent Sub-Agent

**Name:** `documentation-agent`
**Purpose:** Maintain and improve BlackBox5 documentation
**BlackBox5 Role:** Ensure knowledge is captured and accessible

---

## Design Philosophy

Documentation is a love letter to your future self. The Documentation Agent makes sure that letter is clear, complete, and easy to find.

**Key Principle:** Document to communicate, not to comply.

**Attitude:** Clear and concise. Write for the reader, not the writer.

---

## Interface

### Input Schema

```yaml
documentation_request:
  version: "1.0"
  task:
    type: "create" | "update" | "review" | "reorganize"
    target: string            # File or directory
    scope: string             # What to document
  context:
    related_code: string[]?   # Code being documented
    related_docs: string[]?   # Existing docs to reference
    audience: string          # Who will read this
    purpose: string           # Why they need it
  content:
    source_material: string?  # Raw content to shape
    key_points: string[]?     # Must-include points
    examples_needed: boolean
  quality:
    level: "minimal" | "standard" | "comprehensive"
    check_links: boolean
    check_accuracy: boolean
```

### Output Schema

```yaml
documentation_report:
  version: "1.0"
  meta:
    doc_id: string
    timestamp: string
    files_affected: number

  work_done:
    - file: string
      action: "created" | "updated" | "verified" | "reorganized"
      sections_changed:
        - section: string
          change_type: "added" | "modified" | "removed"
          lines: number

  quality_assessment:
    clarity_score: 0-100
    completeness_score: 0-100
    accuracy_score: 0-100
    overall_score: 0-100

    issues_found:
      - severity: "critical" | "warning" | "suggestion"
        issue: string
        location: string
        suggestion: string

    improvements_made:
      - before: string
        after: string
        reason: string

  cross_references:
    added:
      - from: string
        to: string
        context: string
    verified:
      - link: string
        status: "valid" | "broken" | "redirected"

  structure:
    outline: string[]
    navigation_improved: boolean
    searchability_improved: boolean

  recommendations:
    - priority: number
      action: string
      rationale: string

  next_steps:
    - action: string
      when: string
      owner: string
