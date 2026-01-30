#!/usr/bin/env bash
# Blackbox4 Ralph Autonomous Loop Wrapper
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/4-scripts/autonomous-loop.sh" "$@"
