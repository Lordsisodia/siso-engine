#!/usr/bin/env bash
set -euo pipefail

# Start a long-run validation monitor (good for 10–20 hour runs).
#
# This is a convenience wrapper around validate-loop.sh for long monitoring sessions.
# It runs validation on a configurable interval and can notify on failures.
#
# Run from repo root:
#   ./4-scripts/start-10h-monitor.sh --interval-min 20 --notify-local

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

BOX_ROOT="$(find_box_root)"

interval_min=20
notify_local=false
notify_telegram=false
notify_recovery=true

usage() {
  cat <<'EOF' >&2
Usage:
  start-10h-monitor.sh [--interval-min <n>] [--notify-local] [--notify-telegram]

Start a long-running validation monitor for 10-20 hour sessions.

This is a convenience wrapper around validate-loop.sh for extended monitoring.
It's useful during long agent sessions or overnight builds.

Examples:
  # From .blackbox4 root (recommended)
  ./4-scripts/start-10h-monitor.sh --interval-min 20 --notify-local

  # With Telegram notifications (requires env + notify.sh setup)
  ./4-scripts/start-10h-monitor.sh --interval-min 30 --notify-telegram

  # With both local and Telegram notifications
  ./4-scripts/start-10h-monitor.sh --interval-min 15 --notify-local --notify-telegram

Flags:
  --interval-min <n>     Minutes between checks (default: 20)
  --notify-local         Send desktop notifications on failure
  --notify-telegram      Send Telegram alerts (requires TELEGRAM_BOT_TOKEN env)
  --notify-recovery      Notify when validation recovers (default: true)

Stop with Ctrl+C.

For more options, run validate-loop.sh directly:
  ./4-scripts/validate-loop.sh --help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --interval-min)
      shift
      interval_min="${1:-}"
      shift || true
      ;;
    --notify-local)
      notify_local=true
      shift || true
      ;;
    --notify-telegram)
      notify_telegram=true
      shift || true
      ;;
    --no-notify-recovery)
      notify_recovery=false
      shift || true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      exit 2
      ;;
  esac
done

info "Starting 10-hour monitor (validate loop)"
info "  Interval: ${interval_min} min"
info "  Local notify: ${notify_local}"
info "  Telegram notify: ${notify_telegram}"
info "  Recovery notify: ${notify_recovery}"
echo ""

args=(--interval-min "$interval_min")
if [[ "$notify_local" == "true" ]]; then
  args+=(--notify-local)
fi
if [[ "$notify_telegram" == "true" ]]; then
  args+=(--notify-telegram)
fi
if [[ "$notify_recovery" == "true" ]]; then
  args+=(--notify-recovery)
fi

exec "${SCRIPT_DIR}/validate-loop.sh" "${args[@]}"
