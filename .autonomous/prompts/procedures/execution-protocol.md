# Execution Protocol

How Ralph completes a task.

---

## Phase 1: Align (Restate)

Before coding, restate:
```
Task: [What you're doing]
Goal: [What success looks like]
Constraints: [Limitations]
Inputs: [What to read]
Outputs: [What to produce]
```

---

## Phase 2: Plan (Brief)

Create micro-plan for this ONE task:
```
Steps:
1. [First action]
2. [Second action]
3. [Validation]

Success Criteria:
- [ ] Criterion 1
- [ ] Criterion 2
```

---

## Phase 3: Execute (Work)

- Write code following project patterns
- Use bash-first approach (scripts over Python)
- Include tests if required
- Document as you go

**Use Sub-Agents for:**
- File searches (preserve your context)
- Deep research
- Parallel validations

---

## Phase 4: Validate (Verify)

Run quality gates:
- [ ] Tests pass
- [ ] Type checking (if applicable)
- [ ] Supabase connections work
- [ ] No regressions

**If failing:**
- Debug and fix
- Retry max 3 times
- If still failing: mark PARTIAL, document blocker

---

## Phase 5: Document (Record)

Update tracking:
1. Task file → mark complete, add notes
2. STATE.yaml → update status, progress
3. WORK-LOG.md → append activity
4. Commit with descriptive message
