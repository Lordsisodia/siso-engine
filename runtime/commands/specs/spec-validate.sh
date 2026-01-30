#!/usr/bin/env bash
# Blackbox4 Spec Validation Wrapper
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/4-scripts/lib/spec-creation/validation.sh" "$@"
