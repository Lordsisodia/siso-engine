# BlackBox5 Agent-Skill Mappings

**Version:** 1.0
**Date:** 2026-02-08
**Source:** FINAL-LEAN-AGENT-CATALOG.md
**Total Agents:** 28
**Total Skills Mapped:** 40+ (existing + new)

---

## Overview

This document maps each of the 28 BlackBox5 agents to the skills they need to perform their functions. Agents use skills as capabilities/tools - they don't become skills themselves.

**Key Principle:** Skills provide reusable capabilities that multiple agents can leverage.

---

## TIER 1: Core Agents (10)

### 1. bb5-master-orchestrator

```yaml
agent_name: bb5-master-orchestrator
purpose: Routes requests to workflows - single entry point maintaining <15% context
required_skills:
  - skill: workflow-engine
    usage: Coordinate flow execution across different workflow types
  - skill: triage
    usage: Initial classification of incoming requests
  - skill: bmad-sm
    usage: Process coordination and workflow management
  - skill: [new] routing-table
    usage: Decision matrix lookup for workflow selection
  - skill: [new] context-budget-manager
    usage: Monitor and enforce 15% context limit
  - skill: [new] escalation-protocol
    usage: Handle unclear requirements, context overflow, safety concerns
```

### 2. bb5-triage-router

```yaml
agent_name: bb5-triage-router
purpose: Classifies intent and assigns specialists for complex requests
required_skills:
  - skill: bmad-analyst
    usage: Analyze request patterns for classification
  - skill: feedback-triage
    usage: Classification taxonomy and prioritization
  - skill: [new] intent-classifier
    usage: NLP-based intent detection for routing decisions
  - skill: [new] domain-classifier
    usage: Classify requests into frontend-heavy, backend-heavy, security-critical
  - skill: [new] specialist-matcher
    usage: Match classified intents to optimal specialist
```

### 3. bb5-stack-researcher

```yaml
agent_name: bb5-stack-researcher
purpose: Analyze tech stack, dependencies, key libraries
required_skills:
  - skill: git-workflows
    usage: Navigate repository structure
  - skill: bmad-analyst
    usage: Research methodology and analysis
  - skill: [new] tech-stack-parser
    usage: Extract and categorize dependencies from package files
  - skill: [new] library-researcher
    usage: Research key libraries and their usage patterns
  - skill: [new] dependency-graph
    usage: Build and analyze dependency relationships
```

### 4. bb5-architecture-researcher

```yaml
agent_name: bb5-architecture-researcher
purpose: Discover patterns, components, conventions
required_skills:
  - skill: bmad-architect
    usage: Architecture analysis frameworks
  - skill: git-workflows
    usage: Navigate codebase for pattern discovery
  - skill: [new] pattern-detector
    usage: Recognize architectural patterns (MVC, layered, microservices)
  - skill: [new] code-convention-analyzer
    usage: Extract naming, style, and organization conventions
  - skill: [new] component-cataloger
    usage: Build inventory of system components
```

### 5. bb5-planner

```yaml
agent_name: bb5-planner
purpose: Create executable XML task plans
required_skills:
  - skill: bmad-pm
    usage: Product management perspective on task planning
  - skill: bmad-architect
    usage: Architecture input for technical planning
  - skill: bmad-sm
    usage: Sprint planning and task organization
  - skill: [new] xml-plan-generator
    usage: Generate properly formatted XML plans
  - skill: [new] task-decomposer
    usage: Break down requirements into atomic tasks
  - skill: [new] research-package-parser
    usage: Parse research_package.yaml input
```

### 6. bb5-dependency-analyzer

```yaml
agent_name: bb5-dependency-analyzer
purpose: Build DAG, detect cycles, calculate waves for parallel execution
required_skills:
  - skill: bmad-sm
    usage: Task dependency understanding
  - skill: [new] graph-builder
    usage: Build directed acyclic graph from task dependencies
  - skill: [new] cycle-detector
    usage: Detect and report dependency cycles
  - skill: [new] topological-sorter
    usage: Sort tasks into execution order
  - skill: [new] wave-calculator
    usage: Group tasks into parallelizable waves
```

### 7. bb5-executor

```yaml
agent_name: bb5-executor
purpose: Fresh context task execution - the "doer"
required_skills:
  - skill: bmad-dev
    usage: Development best practices and patterns
  - skill: bmad-tea
    usage: Task execution methodology
  - skill: git-workflows
    usage: Git operations for atomic commits
  - skill: testing-patterns
    usage: Verify changes with appropriate tests
  - skill: [new] context-isolator
    usage: Ensure fresh 200k token context for each task
  - skill: [new] xml-task-parser
    usage: Extract task parameters from XML plans
  - skill: [new] implementation-strategist
    usage: Plan implementation approach for each task
```

### 8. bb5-validator

```yaml
agent_name: bb5-validator
purpose: 3-level verification (existence/substantive/wired)
required_skills:
  - skill: bmad-qa
    usage: QA perspective on verification
  - skill: testing-patterns
    usage: Validate test coverage
  - skill: [new] existence-checker
    usage: Verify files exist and are non-empty
  - skill: [new] substantive-analyzer
    usage: Check content is meaningful (not placeholders)
  - skill: [new] integration-verifier
    usage: Verify components connect properly
  - skill: [new] scoring-engine
    usage: Calculate 0-100 validation score
  - skill: [new] validator-report-generator
    usage: Generate validator_report.yaml output
```

### 9. bb5-debugger

```yaml
agent_name: bb5-debugger
purpose: Root cause analysis for failures
required_skills:
  - skill: bmad-dev
    usage: Development expertise for debugging
  - skill: systematic-debugging
    usage: Four-phase debugging methodology
  - skill: [new] log-analyzer
    usage: Parse and analyze error logs
  - skill: [new] hypothesis-generator
    usage: Form potential root cause hypotheses
  - skill: [new] systematic-tester
    usage: Test hypotheses methodically
  - skill: [new] erotetic-reasoning
    usage: Apply question-based reasoning framework
  - skill: [new] root-cause-analyzer
    usage: Apply 5 Whys and other RCA techniques
```

### 10. bb5-scribe

```yaml
agent_name: bb5-scribe
purpose: Documentation and memory persistence
required_skills:
  - skill: bmad-pm
    usage: Documentation standards
  - skill: run-initialization
    usage: File structure and run setup
  - skill: [new] memory-persistence
    usage: Write to 3-tier memory system
  - skill: [new] markdown-formatter
    usage: Format documentation in standard markdown
  - skill: [new] decision-extractor
    usage: Identify and extract decisions from conversations
  - skill: [new] learning-capture
    usage: Capture learnings from execution
  - skill: [new] context-transformer
    usage: Transform chat history to structured context
```

---

## TIER 2: Important Agents (10)

### 11. bb5-research-synthesizer

```yaml
agent_name: bb5-research-synthesizer
purpose: Merge parallel researcher outputs
required_skills:
  - skill: bmad-analyst
    usage: Analysis framework for synthesizing research
  - skill: [new] conflict-resolver
    usage: Resolve conflicting findings between researchers
  - skill: [new] gap-analyzer
    usage: Identify missing information or coverage gaps
  - skill: [new] synthesis-formatter
    usage: Format merged findings into research_package.yaml
  - skill: [new] inconsistency-detector
    usage: Find and flag inconsistencies between sources
```

### 12. bb5-integrator

```yaml
agent_name: bb5-integrator
purpose: Merge results from parallel task execution
required_skills:
  - skill: bmad-dev
    usage: Integration patterns
  - skill: git-workflows
    usage: Handle merge conflicts and integration
  - skill: testing-patterns
    usage: Verify integrated code works correctly
  - skill: [new] conflict-detector
    usage: Detect code conflicts between parallel tasks
  - skill: [new] merge-strategist
    usage: Determine best merge approach
  - skill: [new] parallel-result-aggregator
    usage: Collect and organize wave execution outputs
```

### 13. bb5-ghost-of-past

```yaml
agent_name: bb5-ghost-of-past
purpose: Maintain ADRs (Architecture Decision Records)
required_skills:
  - skill: bmad-architect
    usage: Architecture perspective for ADRs
  - skill: [new] adr-manager
    usage: Create and maintain ADR files
  - skill: [new] decision-capture
    usage: Extract decisions from conversations
  - skill: [new] consequence-tracker
    usage: Track positive and negative consequences
  - skill: [new] decision-significance-evaluator
    usage: Determine if decision warrants ADR
  - skill: [new] adr-template-manager
    usage: Apply consistent ADR formatting
```

### 14. bb5-context-persistence

```yaml
agent_name: bb5-context-persistence
purpose: 3-tier memory management
required_skills:
  - skill: state-management
    usage: Update STATE.yaml with progress
  - skill: [new] tier-1-memory
    usage: Manage run folders and WIP files
  - skill: [new] tier-2-memory
    usage: Manage STATE.yaml and timeline
  - skill: [new] tier-3-memory
    usage: Manage Brain embeddings and ADRs
  - skill: [new] memory-promoter
    usage: Promote memories between tiers
  - skill: [new] state-yaml-manager
    usage: Read and update STATE.yaml
  - skill: [new] brain-embedding-manager
    usage: Interface with vector store
```

### 15. bb5-bookkeeper

```yaml
agent_name: bb5-bookkeeper
purpose: Track organizational hygiene
required_skills:
  - skill: bmad-sm
    usage: Process tracking
  - skill: [new] state-manager
    usage: Update and maintain STATE.yaml
  - skill: [new] archival-system
    usage: Archive completed runs
  - skill: [new] hygiene-checker
    usage: Clean up temp files and orphans
  - skill: [new] metrics-tracker
    usage: Update project metrics
  - skill: [new] metrics-calculator
    usage: Calculate and update project metrics
```

### 16. bb5-risk-researcher

```yaml
agent_name: bb5-risk-researcher
purpose: Identify security risks, pitfalls, anti-patterns
required_skills:
  - skill: bmad-analyst
    usage: Analysis framework for risk assessment
  - skill: bmad-qa
    usage: Risk assessment methodology
  - skill: [new] security-risk-scanner
    usage: Identify security vulnerabilities
  - skill: [new] anti-pattern-detector
    usage: Recognize code anti-patterns
  - skill: [new] edge-case-analyzer
    usage: Identify edge cases and boundary conditions
  - skill: [new] mitigation-planner
    usage: Develop risk mitigation strategies
  - skill: [new] owasp-mapper
    usage: Map findings to OWASP categories
```

### 17. bb5-convention-researcher

```yaml
agent_name: bb5-convention-researcher
purpose: Discover code style, standards, practices
required_skills:
  - skill: git-workflows
    usage: Navigate codebase for convention discovery
  - skill: [new] style-analyzer
    usage: Analyze code style patterns
  - skill: [new] naming-convention-detector
    usage: Identify naming patterns
  - skill: [new] linter-config-extractor
    usage: Extract linter and formatter configs
  - skill: [new] style-guide-generator
    usage: Generate style guide from existing code
```

### 18. bb5-qa-specialist

```yaml
agent_name: bb5-qa-specialist
purpose: Regression testing, test generation
required_skills:
  - skill: bmad-qa
    usage: QA methodology and best practices
  - skill: testing-patterns
    usage: Testing patterns and strategies
  - skill: [new] test-runner
    usage: Execute test suites
  - skill: [new] coverage-analyzer
    usage: Check and report test coverage
  - skill: [new] test-generator
    usage: Generate missing tests
  - skill: [new] regression-detector
    usage: Detect test regressions
  - skill: [new] coverage-gap-analyzer
    usage: Find untested code paths
  - skill: [new] test-strategist
    usage: Determine what tests to generate
```

### 19. bb5-security-guard

```yaml
agent_name: bb5-security-guard
purpose: Vulnerability scanning, OWASP compliance
required_skills:
  - skill: bmad-qa
    usage: Security testing methodology
  - skill: [new] owasp-checker
    usage: Check OWASP Top 10 compliance
  - skill: [new] secret-scanner
    usage: Detect exposed secrets in code
  - skill: [new] injection-detector
    usage: Find SQL, XSS, command injection risks
  - skill: [new] dependency-security-checker
    usage: Check for insecure dependencies
  - skill: [new] static-security-analysis
    usage: Run SAST on code
  - skill: [new] security-report-generator
    usage: Generate security findings report
```

### 20. bb5-performance-profiler

```yaml
agent_name: bb5-performance-profiler
purpose: Efficiency analysis, Big-O detection
required_skills:
  - skill: [new] complexity-analyzer
    usage: Calculate Big-O complexity
  - skill: [new] benchmark-runner
    usage: Run and compare benchmarks
  - skill: [new] query-analyzer
    usage: Analyze database query performance
  - skill: [new] memory-profiler
    usage: Analyze memory usage patterns
  - skill: [new] complexity-calculator
    usage: Determine algorithmic complexity
  - skill: [new] performance-bottleneck-detector
    usage: Find performance issues
```

---

## TIER 3: Specialized Agents (8)

### 21. ArchitectAgent (Alex)

```yaml
agent_name: ArchitectAgent
purpose: System design, scalability, architecture decisions
required_skills:
  - skill: bmad-architect
    usage: Core architecture methodology
  - skill: [new] pattern-library
    usage: Reference catalog of design patterns
  - skill: [new] scalability-calculator
    usage: Calculate scaling requirements
  - skill: [new] diagram-generator
    usage: Generate architecture diagrams
  - skill: [new] architecture-review
    usage: Review and critique designs
  - skill: [new] scalability-assessor
    usage: Evaluate system scalability
```

### 22. AnalystAgent (Mary)

```yaml
agent_name: AnalystAgent
purpose: Research, data analysis, competitive analysis
required_skills:
  - skill: bmad-analyst
    usage: Core analysis methodology
  - skill: web-search
    usage: Research external information
  - skill: [new] data-visualizer
    usage: Create data visualizations
  - skill: [new] competitive-matrix-builder
    usage: Build competitive comparison matrices
  - skill: [new] trend-analysis
    usage: Identify patterns and trends
```

### 23. DeveloperAgent (Amelia)

```yaml
agent_name: DeveloperAgent
purpose: Implementation, debugging, code review, testing
required_skills:
  - skill: bmad-dev
    usage: Core development methodology
  - skill: bmad-tea
    usage: Task execution
  - skill: git-workflows
    usage: Code management and review
  - skill: testing-patterns
    usage: Testing implementation
  - skill: [new] language-specific-patterns
    usage: Language-specific best practices
  - skill: [new] debugging-playbook
    usage: Systematic debugging approaches
  - skill: [new] framework-expertise
    usage: Deep framework knowledge
```

### 24. frontend-specialist

```yaml
agent_name: frontend-specialist
purpose: React/Vue/Angular, UI components, frontend-heavy work
required_skills:
  - skill: [new] react-patterns
    usage: React-specific patterns and best practices
  - skill: [new] vue-patterns
    usage: Vue-specific patterns
  - skill: [new] angular-patterns
    usage: Angular-specific patterns
  - skill: [new] css-architecture
    usage: CSS organization and methodologies
  - skill: [new] frontend-testing
    usage: Frontend testing strategies
  - skill: [new] component-library-usage
    usage: Use design systems
  - skill: [new] frontend-build-tools
    usage: Configure webpack, vite, etc.
```

### 25. backend-specialist

```yaml
agent_name: backend-specialist
purpose: APIs, microservices, server logic, backend-heavy work
required_skills:
  - skill: supabase-operations
    usage: Supabase backend operations
  - skill: [new] api-design-patterns
    usage: REST and GraphQL design patterns
  - skill: [new] microservices-patterns
    usage: Microservices architecture patterns
  - skill: [new] server-optimization
    usage: Backend performance optimization
  - skill: [new] service-architecture
    usage: Design service boundaries
  - skill: [new] backend-frameworks
    usage: Expert in FastAPI, Express, etc.
```

### 26. api-specialist

```yaml
agent_name: api-specialist
purpose: API design, integration, API development
required_skills:
  - skill: [new] rest-design
    usage: RESTful API design principles
  - skill: [new] graphql-design
    usage: GraphQL schema design
  - skill: [new] api-documentation
    usage: OpenAPI/Swagger documentation
  - skill: [new] api-versioning
    usage: API versioning strategies
  - skill: [new] openapi-specification
    usage: Write OpenAPI specs
  - skill: [new] api-testing
    usage: Test APIs thoroughly
```

### 27. database-specialist

```yaml
agent_name: database-specialist
purpose: Schema design, queries, migrations, database work
required_skills:
  - skill: supabase-operations
    usage: Supabase database operations
  - skill: [new] schema-designer
    usage: Database schema design
  - skill: [new] query-optimizer
    usage: SQL query optimization
  - skill: [new] migration-manager
    usage: Database migration management
  - skill: [new] ddl-generation
    usage: Generate DDL statements
  - skill: [new] database-performance-tuning
    usage: Tune database performance
```

### 28. testing-specialist

```yaml
agent_name: testing-specialist
purpose: Test strategy, TDD, coverage, complex testing
required_skills:
  - skill: bmad-qa
    usage: QA methodology
  - skill: testing-patterns
    usage: Testing patterns and practices
  - skill: [new] tdd-workflow
    usage: Test-driven development process
  - skill: [new] coverage-strategy
    usage: Test coverage planning
  - skill: [new] test-automation
    usage: Automated testing pipelines
  - skill: [new] test-pyramid-planning
    usage: Balance test types
  - skill: [new] mutation-testing
    usage: Verify test quality
```

---

## SKILL SUMMARY

### Existing Skills to Leverage (25)

**BMAD Skills (9):**
- bmad-pm, bmad-architect, bmad-analyst, bmad-sm, bmad-ux, bmad-dev, bmad-qa, bmad-quick-flow, bmad-tea

**Development Skills (7):**
- git-workflows, testing-patterns, testing-playbook, feedback-triage, run-initialization, supabase-operations, siso-tasks-cli

**n8n Skills (7):**
- n8n-code-javascript, n8n-code-python, n8n-expression-syntax, n8n-mcp-tools-expert, n8n-node-configuration, n8n-validation-expert, n8n-workflow-patterns

**Integration Skills (2):**
- notifications-local, notion-mcp

### New Skills to Create (56 total)

**Core System Skills:**
- routing-table, context-budget-manager, intent-classifier, specialist-matcher

**Research Skills:**
- tech-stack-parser, library-researcher, dependency-graph, pattern-detector, convention-extractor, conflict-resolver, gap-analyzer, synthesis-formatter

**Planning Skills:**
- xml-plan-generator, task-decomposer, research-package-parser, plan-sequencer

**Dependency Skills:**
- graph-builder, cycle-detector, topological-sorter, wave-calculator

**Execution Skills:**
- context-isolator, xml-task-parser, implementation-strategist

**Verification Skills:**
- existence-checker, substantive-analyzer, integration-verifier, scoring-engine, validator-report-generator

**Debugging Skills:**
- log-analyzer, hypothesis-generator, systematic-tester, erotetic-reasoning, root-cause-analyzer

**Memory Skills:**
- memory-persistence, markdown-formatter, decision-extractor, learning-capture, context-transformer

**ADR Skills:**
- adr-manager, decision-capture, consequence-tracker, decision-significance-evaluator, adr-template-manager

**Persistence Skills:**
- tier-1-memory, tier-2-memory, tier-3-memory, memory-promoter, state-yaml-manager, brain-embedding-manager

**Hygiene Skills:**
- state-manager, archival-system, hygiene-checker, metrics-tracker, metrics-calculator

**Security Skills:**
- security-risk-scanner, owasp-checker, secret-scanner, injection-detector, dependency-security-checker, static-security-analysis, security-report-generator

**Code Quality Skills:**
- style-analyzer, naming-convention-detector, linter-config-extractor, style-guide-generator, anti-pattern-detector

**Testing Skills:**
- test-runner, coverage-analyzer, test-generator, regression-detector, coverage-gap-analyzer, test-strategist, tdd-workflow, coverage-strategy, test-automation, test-pyramid-planning, mutation-testing

**Performance Skills:**
- complexity-analyzer, benchmark-runner, query-analyzer, memory-profiler, complexity-calculator, performance-bottleneck-detector

**Domain Skills:**
- react-patterns, vue-patterns, angular-patterns, css-architecture, frontend-testing, component-library-usage, frontend-build-tools, api-design-patterns, microservices-patterns, server-optimization, service-architecture, backend-frameworks, rest-design, graphql-design, api-documentation, api-versioning, openapi-specification, api-testing, schema-designer, query-optimizer, migration-manager, ddl-generation, database-performance-tuning, pattern-library, scalability-calculator, diagram-generator, architecture-review, scalability-assessor, data-visualizer, competitive-matrix-builder, trend-analysis, language-specific-patterns, debugging-playbook, framework-expertise

---

## CROSS-REFERENCE MATRIX

| Agent | Primary BMAD Skill | Secondary Skills | New Skills Needed |
|-------|-------------------|------------------|-------------------|
| bb5-master-orchestrator | bmad-sm | workflow-engine, triage | routing-table, context-budget-manager |
| bb5-triage-router | bmad-analyst | feedback-triage | intent-classifier, domain-classifier, specialist-matcher |
| bb5-stack-researcher | bmad-analyst | git-workflows | tech-stack-parser, library-researcher, dependency-graph |
| bb5-architecture-researcher | bmad-architect | git-workflows | pattern-detector, convention-analyzer, component-cataloger |
| bb5-planner | bmad-pm, bmad-architect, bmad-sm | - | xml-plan-generator, task-decomposer, research-package-parser |
| bb5-dependency-analyzer | bmad-sm | - | graph-builder, cycle-detector, topological-sorter, wave-calculator |
| bb5-executor | bmad-dev, bmad-tea | git-workflows, testing-patterns | context-isolator, xml-task-parser, implementation-strategist |
| bb5-validator | bmad-qa | testing-patterns | existence-checker, substantive-analyzer, integration-verifier, scoring-engine |
| bb5-debugger | bmad-dev | systematic-debugging | log-analyzer, hypothesis-generator, systematic-tester, erotetic-reasoning, root-cause-analyzer |
| bb5-scribe | bmad-pm | run-initialization | memory-persistence, markdown-formatter, decision-extractor, learning-capture, context-transformer |
| bb5-research-synthesizer | bmad-analyst | - | conflict-resolver, gap-analyzer, synthesis-formatter, inconsistency-detector |
| bb5-integrator | bmad-dev | git-workflows, testing-patterns | conflict-detector, merge-strategist, parallel-result-aggregator |
| bb5-ghost-of-past | bmad-architect | - | adr-manager, decision-capture, consequence-tracker, decision-significance-evaluator, adr-template-manager |
| bb5-context-persistence | - | state-management | tier-1-memory, tier-2-memory, tier-3-memory, memory-promoter, state-yaml-manager, brain-embedding-manager |
| bb5-bookkeeper | bmad-sm | - | state-manager, archival-system, hygiene-checker, metrics-tracker, metrics-calculator |
| bb5-risk-researcher | bmad-analyst, bmad-qa | - | security-risk-scanner, owasp-mapper, anti-pattern-detector, edge-case-analyzer, mitigation-planner |
| bb5-convention-researcher | bmad-analyst | git-workflows | style-analyzer, naming-convention-detector, linter-config-extractor, style-guide-generator |
| bb5-qa-specialist | bmad-qa | testing-patterns | test-runner, coverage-analyzer, test-generator, regression-detector, coverage-gap-analyzer, test-strategist |
| bb5-security-guard | bmad-qa | - | owasp-checker, secret-scanner, injection-detector, dependency-security-checker, static-security-analysis, security-report-generator |
| bb5-performance-profiler | - | - | complexity-analyzer, benchmark-runner, query-analyzer, memory-profiler, complexity-calculator, performance-bottleneck-detector |
| ArchitectAgent | bmad-architect | - | pattern-library, scalability-calculator, diagram-generator, architecture-review, scalability-assessor |
| AnalystAgent | bmad-analyst | web-search | data-visualizer, competitive-matrix-builder, trend-analysis |
| DeveloperAgent | bmad-dev, bmad-tea | git-workflows, testing-patterns | language-specific-patterns, debugging-playbook, framework-expertise |
| frontend-specialist | - | - | react-patterns, vue-patterns, angular-patterns, css-architecture, frontend-testing, component-library-usage, frontend-build-tools |
| backend-specialist | - | supabase-operations | api-design-patterns, microservices-patterns, server-optimization, service-architecture, backend-frameworks |
| api-specialist | - | - | rest-design, graphql-design, api-documentation, api-versioning, openapi-specification, api-testing |
| database-specialist | - | supabase-operations | schema-designer, query-optimizer, migration-manager, ddl-generation, database-performance-tuning |
| testing-specialist | bmad-qa | testing-patterns | tdd-workflow, coverage-strategy, test-automation, test-pyramid-planning, mutation-testing |

---

**Document Version:** 1.0
**Total Agents Mapped:** 28
**Existing Skills Referenced:** 25
**New Skills Identified:** 56
**Coverage:** Complete
