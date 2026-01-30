# Protocol

The Blackbox is a **context-preserving workflow** for turning product/engineering feedback into shipped changes with clean handoffs.

Core idea:

- **Runs** preserve per-batch context (inputs, handoffs, plans, results).
- **Domains** preserve durable architecture knowledge (“how the system works”).
- **Agents** are lightweight packages that use shared prompts/skills and emit consistent outputs.

## Canonical pipeline (agent team management)

1) **Triage + grouping**
   - Input: run `inbox.md`
   - Output: `normalized.md`, `grouping.md`, `handoffs/issue-research.md`

2) **Issue research handoff**
   - Output: per-issue `issue.md` and group handoffs with real file paths

3) **Plans + coordination**
   - Output: per-issue `plan.md` (executable steps, acceptance criteria)

4) **Implementation**
   - Output: code changes + per-issue `implementation.md`

5) **Verification**
   - Output: per-issue `verification.md` + status updates

## Promotion path (turning runs into durable knowledge)

- If it’s durable “how it works”: promote into `domains/<domain>/...`
- If it’s a repeatable method: promote into `.skills/...`
- If it’s a reusable instruction set: promote into `.prompts/...`

## Guardrails

- No secrets in Blackbox files.
- Plans must cite concrete code paths.
- If DB schema changes are required: use `siso-internal-supabase.apply_migration`, then advisors + types regeneration.

