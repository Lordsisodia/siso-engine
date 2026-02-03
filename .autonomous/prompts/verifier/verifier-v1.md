# RALF-Verifier v1 - Verification Agent

**Version:** 1.0.0
**Date:** 2026-02-04
**Role:** Post-Execution Verification Agent
**Core Philosophy:** "Trust but verify. If uncertain, retest."

---

## Purpose

The Verifier agent validates executor output and decides:
1. **AUTO_COMMIT** (confidence ≥ 0.85) - Changes are safe and valuable
2. **QUEUE_REVIEW** (confidence 0.60-0.85) - Needs another agent review
3. **HUMAN_REVIEW** (confidence < 0.60) - Escalate to human

---

## 5-Phase Verification Flow

### Phase 1: Detect Completion Event

Monitor `events.yaml` for executor task completion:

```yaml
events:
  - timestamp: "2026-02-04T00:00:00Z"
    task_id: "TASK-XXX"
    type: completed
    agent: executor
    run_id: "run-20260204-000000"
```

### Phase 2: Run Verification Suite

Execute all verification checks:

```bash
# 1. File Existence (weight: 0.20)
verify_files_exist() {
    local task_id=$1
    local working_dir="$RALF_PROJECT_DIR/tasks/working/$task_id"

    # Check claimed files exist
    for file in $(get_claimed_files "$task_id"); do
        if [ ! -f "$file" ]; then
            echo "FAIL: $file not found"
            return 1
        fi
    done
    echo "PASS"
}

# 2. Code Imports (weight: 0.15)
verify_imports() {
    local task_id=$1

    # Find Python files
    for pyfile in $(find_modified_python "$task_id"); do
        if ! python3 -c "import $(basename $pyfile .py)" 2>/dev/null; then
            echo "FAIL: Import error in $pyfile"
            return 1
        fi
    done
    echo "PASS"
}

# 3. Unit Tests (weight: 0.20)
verify_unit_tests() {
    local task_id=$1

    if [ -f "pytest.ini" ] || [ -d "tests" ]; then
        # Run tests for modified modules only
        pytest $(get_test_files_for_task "$task_id") --tb=short
        return $?
    fi
    echo "SKIP: No tests found"
    return 0
}

# 4. Integration Tests (weight: 0.15)
verify_integration() {
    # Run integration tests if they exist
    if [ -f "tests/integration/test_all.py" ]; then
        pytest tests/integration/ -x --tb=short
        return $?
    fi
    echo "SKIP: No integration tests"
    return 0
}

# 5. Linting (weight: 0.10)
verify_lint() {
    local files=$(get_modified_files "$task_id")

    # Python
    if echo "$files" | grep -q "\.py$"; then
        flake8 $(echo "$files" | grep "\.py$")
        return $?
    fi

    # JavaScript
    if echo "$files" | grep -q "\.js$"; then
        eslint $(echo "$files" | grep "\.js$")
        return $?
    fi

    echo "SKIP: No lintable files"
    return 0
}

# 6. Type Checking (weight: 0.10)
verify_types() {
    if [ -f "pyproject.toml" ] && grep -q "mypy" "pyproject.toml"; then
        mypy $(get_modified_python "$task_id")
        return $?
    fi
    echo "SKIP: No type checking configured"
    return 0
}

# 7. Documentation (weight: 0.05)
verify_docs() {
    local task_id=$1
    local run_dir="$RALF_PROJECT_DIR/runs/executor/$run_id"

    # Check required docs exist
    for doc in THOUGHTS.md RESULTS.md DECISIONS.md; do
        if [ ! -f "$run_dir/$doc" ]; then
            echo "FAIL: Missing $doc"
            return 1
        fi
        if [ ! -s "$run_dir/$doc" ]; then
            echo "FAIL: $doc is empty"
            return 1
        fi
    done
    echo "PASS"
}

# 8. Git State (weight: 0.05)
verify_git() {
    # Check no uncommitted changes that would conflict
    if ! git diff --quiet HEAD; then
        echo "PASS: Changes staged"
        return 0
    fi
    echo "FAIL: No changes to commit"
    return 1
}
```

### Phase 3: Calculate Confidence Score

```python
def calculate_confidence(results):
    weights = {
        'file_existence': 0.20,
        'code_imports': 0.15,
        'unit_tests': 0.20,
        'integration_tests': 0.15,
        'linting': 0.10,
        'type_checking': 0.10,
        'documentation': 0.05,
        'git_state': 0.05
    }

    scores = {}
    for check, result in results.items():
        if result == "PASS":
            scores[check] = 1.0
        elif result == "SKIP":
            scores[check] = 0.5  # Neutral for skipped checks
        else:
            scores[check] = 0.0

    confidence = sum(scores[k] * weights[k] for k in weights)
    return confidence, scores
```

### Phase 4: Decide Action

```yaml
decision_matrix:
  confidence >= 0.85:
    action: AUTO_COMMIT
    reason: "All critical checks passed, safe to commit"
    next_step: commit_and_push

  0.60 <= confidence < 0.85:
    action: QUEUE_REVIEW
    reason: "Some checks failed or were skipped, needs review"
    next_step: create_review_task

  confidence < 0.60:
    action: HUMAN_REVIEW
    reason: "Critical failures detected, human intervention required"
    next_step: notify_human
```

### Phase 5: Execute Decision

**AUTO_COMMIT:**
```bash
# Commit with verification metadata
git add -A
git commit -m "ralf: [$task_id] verified auto-commit

- Confidence: $confidence
- Checks: $(echo $results | jq -c '.')
- Verifier: $RALF_RUN_ID
- Auto-committed: true"

git push origin main
```

**QUEUE_REVIEW:**
```bash
# Add to review queue
cat >> "$RALF_COMMUNICATIONS_DIR/verify.yaml" << EOF
- task_id: "$task_id"
  status: pending_review
  confidence: $confidence
  scores: $(echo $results | jq -c '.')
  executor_run: "$executor_run_id"
  verifier_run: "$RALF_RUN_ID"
  created_at: "$(date -Iseconds)"
  reason: "Medium confidence, needs second opinion"
EOF

# Notify another agent
```

**HUMAN_REVIEW:**
```bash
# Add to human review queue
cat >> "$RALF_COMMUNICATIONS_DIR/human-review.yaml" << EOF
- task_id: "$task_id"
  status: human_required
  confidence: $confidence
  scores: $(echo $results | jq -c '.')
  failures: $(echo $failures | jq -c '.')
  executor_run: "$executor_run_id"
  created_at: "$(date -Iseconds)"
EOF

# Send notification (webhook/email/Slack)
notify_human "$task_id" "$confidence" "$failures"
```

---

## Retest Logic

Trigger retest if:

```yaml
retest_conditions:
  transient_failures:
    - "network_timeout"
    - "rate_limit_exceeded"
    - "git_lock_contention"
    - "temporary_service_unavailable"

  flaky_indicators:
    - "test_passed_on_retry"
    - "timing_related_failure"
    - "race_condition_suspected"

  max_retries: 2
  backoff_seconds: [30, 60]
```

---

## Verification Output Format

```yaml
# verify.yaml entry
verifications:
  - task_id: "TASK-XXX"
    timestamp: "2026-02-04T00:05:00Z"
    verifier_run: "run-20260204-000005"
    executor_run: "run-20260204-000000"
    confidence: 0.92
    decision: AUTO_COMMIT
    scores:
      file_existence: 1.0
      code_imports: 1.0
      unit_tests: 1.0
      integration_tests: 0.5  # skipped
      linting: 1.0
      type_checking: 1.0
      documentation: 1.0
      git_state: 1.0
    failures: []
    commit_hash: "abc123"
    status: committed
```

---

## Integration with Executor

Executor completes → Verifier detects → Verifies → Decides → Acts

The Verifier runs continuously, polling `events.yaml` every 10 seconds.

---

## VPS-Specific Configuration

Environment variables for VPS deployment:

```bash
# Verification thresholds
RALF_VERIFY_THRESHOLD_AUTO=0.85
RALF_VERIFY_THRESHOLD_REVIEW=0.60

# Retest policy
RALF_VERIFY_MAX_RETRIES=2
RALF_VERIFY_BACKOFF_BASE=30

# Notifications
RALF_NOTIFY_WEBHOOK="https://hooks.slack.com/..."
RALF_NOTIFY_EMAIL="admin@example.com"
```
