# Verifier

> Post-execution verification agent for RALF

## Overview

The Verifier agent validates executor output and decides whether changes should be auto-committed, queued for review, or escalated to human review.

## Files

| File | Purpose |
|------|---------|
| `verifier-v1.md` | Complete verification agent prompt (v1.0.0) |

## Verifier v1

**Role:** Post-Execution Verification Agent
**Core Philosophy:** "Trust but verify. If uncertain, retest."

### 5-Phase Verification Flow

1. **Detect Completion Event** - Monitor events.yaml for executor task completion
2. **Run Verification Suite** - Execute all verification checks
3. **Calculate Confidence Score** - Weighted scoring across 8 checks
4. **Decide Action** - AUTO_COMMIT, QUEUE_REVIEW, or HUMAN_REVIEW
5. **Execute Decision** - Commit, queue, or escalate

### Verification Checks

| Check | Weight | Description |
|-------|--------|-------------|
| File Existence | 0.20 | Verify claimed files exist |
| Code Imports | 0.15 | Verify Python imports work |
| Unit Tests | 0.20 | Run tests for modified modules |
| Integration Tests | 0.15 | Run integration tests if available |
| Linting | 0.10 | Run flake8/eslint |
| Type Checking | 0.10 | Run mypy if configured |
| Documentation | 0.05 | Check THOUGHTS.md, RESULTS.md, DECISIONS.md exist |
| Git State | 0.05 | Verify changes are staged |

### Decision Matrix

| Confidence | Action | Next Step |
|------------|--------|-----------|
| >= 0.85 | AUTO_COMMIT | Commit and push |
| 0.60 - 0.85 | QUEUE_REVIEW | Create review task |
| < 0.60 | HUMAN_REVIEW | Notify human |

### Retest Logic

Trigger retest for transient failures:
- network_timeout
- rate_limit_exceeded
- git_lock_contention
- temporary_service_unavailable

Max retries: 2 with backoff [30s, 60s]

## Usage

```bash
# Run verifier
cat verifier/verifier-v1.md | claude -p
```

The Verifier runs continuously, polling events.yaml every 10 seconds.
