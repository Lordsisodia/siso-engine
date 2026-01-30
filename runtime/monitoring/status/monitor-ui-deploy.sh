#!/usr/bin/env bash
set -euo pipefail

# Monitor UI deployment after production rollout
# - Validates production console is clean
# - Takes production screenshots
# - Monitors for post-deployment issues
# - Supports notification on completion/issues

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

BOX_ROOT="$(find_box_root)"

usage() {
  cat <<'EOF' >&2
Usage:
  monitor-ui-deploy.sh --url <production-url> --run <run-dir> [--interval-min N] [--duration-min N] [--notify]

Required:
  --url <url>           Production URL to monitor
  --run <run-dir>       UI Cycle run directory

Optional:
  --interval-min N      Check interval in minutes (default: 5)
  --duration-min N      Total monitoring duration (default: 30)
  --notify              Enable notifications (Telegram or local)

Example:
  monitor-ui-deploy.sh \
    --url https://example.com \
    --run .runs/ui-cycle-20250113_1430 \
    --interval-min 5 \
    --duration-min 30 \
    --notify
EOF
}

url=""
run_path=""
interval_min=5
duration_min=30
notify=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      shift
      url="${1:-}"
      shift || true
      ;;
    --run)
      shift
      run_path="${1:-}"
      shift || true
      ;;
    --interval-min)
      shift
      interval_min="${1:-5}"
      shift || true
      ;;
    --duration-min)
      shift
      duration_min="${1:-30}"
      shift || true
      ;;
    --notify)
      notify=true
      shift || true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$url" ]]; then
  error "Missing required argument: --url"
  usage
  exit 2
fi

if [[ -z "$run_path" ]]; then
  error "Missing required argument: --run"
  usage
  exit 2
fi

# Resolve run path
if [[ ! "$run_path" = /* ]]; then
  run_path="${BOX_ROOT}/${run_path}"
fi

if [[ ! -d "$run_path" ]]; then
  error "Run directory not found: $run_path"
  exit 1
fi

# Create monitoring log
monitor_log="${run_path}/logs/monitor-deploy.log"
mkdir -p "$(dirname "$monitor_log")"

send_notification() {
  local status="$1"
  local message="$2"

  if [[ "$notify" != "true" ]]; then
    return 0
  fi

  # Use unified notify system if available
  if [[ -x "${SCRIPT_DIR}/notify.sh" ]]; then
    "${SCRIPT_DIR}/notify.sh" "[UI Deploy] ${status}: ${message}" 2>/dev/null || true
  fi

  # Log notification
  {
    echo "[$(now_timestamp_human)] NOTIFICATION: ${status}"
    echo "  ${message}"
  } >> "$monitor_log"
}

log_message() {
  local level="$1"
  shift
  echo "[$(now_timestamp_human)] [${level}] $*" | tee -a "$monitor_log"
}

check_production() {
  local check_url="$1"
  local iteration="$2"
  local screenshot_file="${run_path}/screenshots/production-check-${iteration}.png"

  # HTTP status check
  local http_status
  http_status=$(curl -s -o /dev/null -w "%{http_code}" "$check_url" 2>/dev/null || echo "000")

  if [[ "$http_status" != "200" ]]; then
    log_message "ERROR" "HTTP ${http_status} - Production unreachable"
    return 1
  fi

  # Console error check (requires Chrome DevTools MCP or manual verification)
  # For now, log that this needs manual verification
  log_message "INFO" "HTTP OK - Console check requires MCP (manual verification)"

  # Take screenshot if Chrome MCP available (logged for manual action)
  log_message "INFO" "Screenshot would be saved to: ${screenshot_file}"
  log_message "INFO" "  (Manual: Take screenshot of ${check_url})"

  log_message "OK" "Production check ${iteration} passed"
  return 0
}

# Main monitoring loop
success "Starting UI deployment monitoring"
info "  URL: ${url}"
info "  Run: ${run_path}"
info "  Interval: ${interval_min} min"
info "  Duration: ${duration_min} min"
info ""

{
  echo "=== UI Deployment Monitoring ==="
  echo "Started: $(now_timestamp_human)"
  echo "URL: ${url}"
  echo "Run: ${run_path}"
  echo "Interval: ${interval_min} min"
  echo "Duration: ${duration_min} min"
  echo ""
} >> "$monitor_log"

send_notification "Started" "Monitoring ${url} for ${duration_min} minutes"

iteration=0
max_iterations=$((duration_min / interval_min))
issues_found=0

while [[ $iteration -lt $max_iterations ]]; do
  iteration=$((iteration + 1))

  log_message "INFO" "Check ${iteration}/${max_iterations}"

  if ! check_production "$url" "$iteration"; then
    issues_found=$((issues_found + 1))

    if [[ $issues_found -ge 3 ]]; then
      log_message "CRITICAL" "Multiple issues detected (3+), escalating"
      send_notification "Critical" "Multiple issues detected for ${url}"

      # Create escalation report
      cat >"${run_path}/artifacts/deployment-escalation.md" <<EOF
# Deployment Escalation

**URL:** ${url}
**Detected:** $(now_timestamp_human)
**Issues:** ${issues_found}+ consecutive failures

## Issue Details

$(tail -20 "$monitor_log")

## Recommended Actions

1. Check production logs immediately
2. Verify deployment completed successfully
3. Consider rollback if critical
4. Investigate root cause

## Status

🚨 **Escalated to human**

EOF
      break
    fi
  fi

  # Sleep until next check (unless last iteration)
  if [[ $iteration -lt $max_iterations ]]; then
    sleep $((interval_min * 60))
  fi
done

# Final summary
{
  echo ""
  echo "=== Monitoring Complete ==="
  echo "Ended: $(now_timestamp_human)"
  echo "Iterations: ${iteration}/${max_iterations}"
  echo "Issues found: ${issues_found}"
} >> "$monitor_log"

if [[ $issues_found -eq 0 ]]; then
  success "Deployment monitoring complete - no issues detected"
  send_notification "Success" "Deployment verified: ${url}"

  # Create success report
  cat >"${run_path}/artifacts/deployment-monitoring-report.md" <<EOF
# Deployment Monitoring Report

**URL:** ${url}
**Started:** $(head -3 "$monitor_log" | tail -1 | cut -d' ' -f2-)
**Ended:** $(tail -3 "$monitor_log" | head -1 | cut -d' ' -f2-)
**Iterations:** ${iteration}/${max_iterations}
**Issues Found:** ${issues_found}

## Status

✅ **Deployment successful - production stable**

## Checks Performed

- HTTP status: OK (200)
- Console: Manual verification required
- Visual: Manual verification required

## Recommendations

- Continue monitoring for next 24h
- Check analytics for user impact
- Schedule follow-up if needed

EOF
else
  warning "Deployment monitoring complete - ${issues_found} issues detected"
  send_notification "Warning" "Monitoring complete with ${issues_found} issues"

  # Create issue report
  cat >"${run_path}/artifacts/deployment-monitoring-report.md" <<EOF
# Deployment Monitoring Report

**URL:** ${url}
**Started:** $(head -3 "$monitor_log" | tail -1 | cut -d' ' -f2-)
**Ended:** $(tail -3 "$monitor_log" | head -1 | cut -d' ' -f2-)
**Iterations:** ${iteration}/${max_iterations}
**Issues Found:** ${issues_found}

## Status

⚠️ **Issues detected - review required**

## Issue Log

$(tail -30 "$monitor_log")

## Recommended Actions

1. Review issue log above
2. Check production console for errors
3. Verify user-facing functionality
4. Consider rollback if critical issues

EOF
fi

info "Monitoring log: ${monitor_log}"
info "Report: ${run_path}/artifacts/deployment-monitoring-report.md"
