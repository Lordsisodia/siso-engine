#!/usr/bin/env bash
# Blackbox4 Spec Analysis Wrapper
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/4-scripts/lib/spec-creation/analyze.py" "$@"
