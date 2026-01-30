#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <agent-name...>" >&2
  exit 1
fi

name="$*"
slug="$(slugify "$name")"

dest=".blackbox/agents/${slug}"
template_dir=".blackbox/agents/_template"

if [[ -e "$dest" ]]; then
  echo "Agent already exists: $dest" >&2
  exit 1
fi

mkdir -p "$dest"
cp -R "$template_dir"/. "$dest/"

if [[ -f "$dest/agent.md" ]]; then
  sed_inplace "s/<agent-name>/${name//\//\\/}/g" "$dest/agent.md"
fi
if [[ -f "$dest/prompt.md" ]]; then
  sed_inplace "s/<agent-name>/${name//\//\\/}/g" "$dest/prompt.md"
fi
if [[ -f "$dest/config.yaml" ]]; then
  sed_inplace "s/<agent-id>/${slug}/g" "$dest/config.yaml"
  sed_inplace "s/<agent-name>/${name//\//\\/}/g" "$dest/config.yaml"
fi

echo "Created agent: $dest"
