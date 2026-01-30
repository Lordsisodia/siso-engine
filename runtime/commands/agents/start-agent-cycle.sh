#!/usr/bin/env bash
set -euo pipefail

# Start a long-running "agent cycle" run:
# - Creates a new plan folder from template
# - Seeds a cycle file with N prompt slots
# - Leaves everything CLI-only (no API assumptions)
#
# Run from repo root:
#   ./docs/.blackbox/4-scripts/start-agent-cycle.sh --hours 8 --prompts 50 "my goal"
# Or from within docs/:
#   ./.blackbox/4-scripts/start-agent-cycle.sh --hours 8 --prompts 50 "my goal"

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
docs_root="$(cd "$here/../.." && pwd)"

if [[ ! -d "$docs_root/.blackbox" ]]; then
  echo "ERROR: Could not locate docs/.blackbox from: $here" >&2
  exit 1
fi

usage() {
  cat <<'EOF' >&2
Usage:
  start-agent-cycle.sh [--hours <n>] [--prompts <n>] [--checkpoint-every <n>] [--plan <path>] [--resume | --overwrite] [--keep] <goal/title...>

Defaults:
  --hours            8
  --prompts          50
  --checkpoint-every 1

Notes:
  - This is a *scaffolding* script. It does not run an agent by itself.
  - It creates a plan folder and a prompt-by-prompt checklist so you can run an interactive CLI session for hours.
  - If --plan is provided, the cycle file is added to that existing plan folder instead of creating a new one.
  - If agent-cycle.md already exists:
    - use --resume to append new prompt slots
    - use --overwrite to replace it
EOF
}

hours=8
prompts=50
checkpoint_every=1
plan_override=""
resume=false
overwrite=false
keep=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hours)
      shift
      hours="${1:-}"
      shift || true
      ;;
    --prompts)
      shift
      prompts="${1:-}"
      shift || true
      ;;
    --checkpoint-every)
      shift
      checkpoint_every="${1:-}"
      shift || true
      ;;
    --plan)
      shift
      plan_override="${1:-}"
      shift || true
      ;;
    --resume)
      resume=true
      shift || true
      ;;
    --overwrite)
      overwrite=true
      shift || true
      ;;
    --keep)
      keep=true
      shift || true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      break
      ;;
  esac
done

goal="$*"
if [[ -z "$goal" && -z "$plan_override" ]]; then
  usage
  exit 2
fi

if [[ "$resume" == "true" && "$overwrite" == "true" ]]; then
  echo "ERROR: Use only one of --resume or --overwrite." >&2
  exit 2
fi

if ! [[ "$hours" =~ ^[0-9]+$ ]] || [[ "$hours" -lt 1 ]]; then
  echo "ERROR: --hours must be a positive integer (got: $hours)" >&2
  exit 2
fi

if ! [[ "$prompts" =~ ^[0-9]+$ ]] || [[ "$prompts" -lt 1 ]]; then
  echo "ERROR: --prompts must be a positive integer (got: $prompts)" >&2
  exit 2
fi

if ! [[ "$checkpoint_every" =~ ^[0-9]+$ ]] || [[ "$checkpoint_every" -lt 1 ]]; then
  echo "ERROR: --checkpoint-every must be a positive integer (got: $checkpoint_every)" >&2
  exit 2
fi

normalize_plan_rel() {
  local input="$1"
  if [[ "$input" == docs/* ]]; then
    echo "${input#docs/}"
    return 0
  fi
  echo "$input"
}

plan_rel=""
plan_path=""

if [[ -n "$plan_override" ]]; then
  plan_rel="$(normalize_plan_rel "$plan_override")"
  if [[ "$plan_rel" == /* ]]; then
    plan_path="$plan_rel"
    plan_rel="$(python3 -c "import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))" "$plan_path" "$docs_root" 2>/dev/null || true)"
  else
    plan_path="$docs_root/$plan_rel"
  fi
else
  created="$("$docs_root/.blackbox/4-scripts/new-plan.sh" "$goal")"
  plan_rel="$(echo "$created" | sed -n 's/^Created plan: //p')"
  if [[ -z "$plan_rel" ]]; then
    echo "ERROR: Failed to parse plan path from new-plan output:" >&2
    echo "$created" >&2
    exit 1
  fi
  plan_path="$docs_root/$plan_rel"
fi

if [[ ! -d "$plan_path" ]]; then
  echo "ERROR: Plan folder not found after creation: $plan_path" >&2
  exit 1
fi

if [[ "$plan_rel" != .blackbox/.plans/* ]]; then
  echo "WARN: Plan path is not under docs/.blackbox/.plans/: $plan_rel" >&2
fi

if [[ -z "$goal" ]]; then
  goal="$(basename "$plan_rel")"
fi

if [[ "$keep" == "true" ]]; then
  touch "$plan_path/.keep" || true
fi

cycle="$plan_path/agent-cycle.md"

append_prompt_slots() {
  local start_i="$1"
  local end_i="$2"
  local out="$3"

  local i="$start_i"
  while [[ $i -le $end_i ]]; do
    cat >>"$out" <<EOF

### Prompt ${i}
- Time:
- Objective:
- Commands run:
- Files touched:
- Result:
- Next prompt:
EOF
    i=$((i + 1))
  done
}

if [[ -f "$cycle" && "$overwrite" != "true" && "$resume" != "true" ]]; then
  echo "ERROR: ${plan_rel}/agent-cycle.md already exists. Use --resume or --overwrite." >&2
  exit 1
fi

if [[ -f "$cycle" && "$overwrite" == "true" ]]; then
  rm -f "$cycle"
fi

if [[ -f "$cycle" && "$resume" == "true" ]]; then
  last_num="$(grep -E '^### Prompt [0-9]+' "$cycle" | awk '{print $3}' | sort -n | tail -n 1 || true)"
  if [[ -z "$last_num" ]]; then
    last_num=0
  fi
  start=$((last_num + 1))
  end=$((last_num + prompts))
  append_prompt_slots "$start" "$end" "$cycle"

  echo ""
  echo "Agent cycle updated:"
  echo "- plan: $plan_rel"
  echo "- cycle: ${plan_rel}/agent-cycle.md"
  echo "- appended: prompts ${start}..${end}"
  exit 0
fi

cat >"$cycle" <<EOF
# Agent Cycle

Goal: ${goal}
Planned duration: ~${hours}h
Planned prompts: ${prompts}
Created at (local): $(date "+%Y-%m-%d %H:%M")
Plan: ${plan_rel}

## Background safety (recommended)

Run periodic validation in another terminal:

\`\`\`bash
./.blackbox/4-scripts/validate-loop.sh --auto-sync --interval-min 15
\`\`\`

## Operating loop

For each prompt:
1) Decide next micro-goal (small, verifiable)
2) Execute (edits / checks / write-up)
3) Capture artifacts under \`artifacts/\` if needed
4) Record a checkpoint

Checkpointing:
- Every ${checkpoint_every} prompt(s), add a step file:
  - \`./.blackbox/4-scripts/new-step.sh --plan ${plan_rel} "Checkpoint: <what changed>"\`

If context gets long:
- \`./.blackbox/4-scripts/compact-context.sh --plan ${plan_rel}\`

## Prompt log (fill as you go)
EOF

append_prompt_slots 1 "$prompts" "$cycle"

# Seed a shorter actionable queue for the first hour.
queue="$plan_path/work-queue.md"
if [[ -f "$queue" ]]; then
  cat >>"$queue" <<EOF

## Agent cycle (first hour)
- [ ] Establish objective + success criteria
- [ ] Create first checkpoint step
- [ ] Identify top 3 risks / unknowns
- [ ] Complete first 5 prompt log entries
- [ ] Compact context if needed
EOF
fi

echo ""
echo "Agent cycle created:"
echo "- plan: $plan_rel"
echo "- cycle: ${plan_rel}/agent-cycle.md"
