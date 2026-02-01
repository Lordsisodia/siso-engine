#!/usr/bin/env bash
# =============================================================================
# Create Agent Version Script
# BlackBox5 - Agent Setup Automation
# =============================================================================
# Purpose: Automate agent version setup following the official checklist
# Usage: ./create-agent-version.sh <version> [agent-name]
# Example: ./create-agent-version.sh v2.5 "RALF-Analyzer"
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

error_exit() {
    log_error "$1"
    exit 1
}

# =============================================================================
# Validation Functions
# =============================================================================

validate_version_format() {
    local version="$1"
    if [[ ! "$version" =~ ^v[0-9]+\.[0-9]+$ ]]; then
        error_exit "Version format must be vX.Y (e.g., v2.5)"
    fi
}

detect_previous_version() {
    local current_version="$1"
    local current_minor
    current_minor=$(echo "$current_version" | sed 's/v[0-9]*\.//')

    if [[ "$current_minor" -gt 0 ]]; then
        local prev_minor=$((current_minor - 1))
        echo "v${current_version:1:1}.${prev_minor}"
    else
        echo ""
    fi
}

validate_yaml() {
    local file="$1"
    if command -v yamllint &> /dev/null; then
        yamllint -d relaxed "$file" || log_warning "YAML validation issues in $file"
    else
        log_warning "yamllint not installed, skipping YAML validation"
    fi
}

# =============================================================================
# Setup Functions
# =============================================================================

setup_version_directory() {
    local version="$1"
    local version_dir="$ENGINE_DIR/.autonomous/prompt-progression/versions/$version"

    log_info "Setting up version directory: $version_dir"

    mkdir -p "$version_dir/templates"
    mkdir -p "$version_dir/docs"

    log_success "Version directory created"
}

copy_templates() {
    local prev_version="$1"
    local new_version="$2"
    local prev_dir="$ENGINE_DIR/.autonomous/prompt-progression/versions/$prev_version"
    local new_dir="$ENGINE_DIR/.autonomous/prompt-progression/versions/$new_version"

    if [[ -d "$prev_dir/templates" ]]; then
        log_info "Copying templates from $prev_version"
        cp -r "$prev_dir/templates/"* "$new_dir/templates/" 2>/dev/null || true
        log_success "Templates copied"
    else
        log_warning "Previous version templates not found at $prev_dir/templates"
        log_info "Creating empty templates directory"
    fi
}

create_version_readme() {
    local version="$1"
    local version_dir="$ENGINE_DIR/.autonomous/prompt-progression/versions/$version"
    local today
    today=$(date +%Y-%m-%d)

    log_info "Creating version README"

    cat > "$version_dir/README.md" << EOF
# Agent Version $version

**Release Date:** $today
**Previous Version:** (See changelog)

## What's New

- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

## Breaking Changes

None

## Migration Guide

No migration needed for this version.

## Checklist Status

- [ ] Core components created
- [ ] Supporting infrastructure in place
- [ ] Templates copied from previous version
- [ ] Entry point updated
- [ ] Documentation complete
- [ ] Validation passed
EOF

    log_success "Version README created"
}

create_agent_config() {
    local agent_name="$1"
    local version="$2"
    local agent_dir="$ENGINE_DIR/.autonomous/agents/$agent_name"

    log_info "Creating agent configuration"

    mkdir -p "$agent_dir"

    cat > "$agent_dir/config.yaml" << EOF
agent:
  name: "$agent_name"
  version: "$version"
  type: "executor"
  created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

capabilities:
  - task_execution
  - documentation
  - validation

settings:
  max_context: 80000
  timeout_seconds: 300
  enable_metrics: true
  enable_dashboard: true

metadata:
  setup_script: "create-agent-version.sh"
  setup_date: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
EOF

    validate_yaml "$agent_dir/config.yaml"
    log_success "Agent configuration created"
}

initialize_metrics() {
    local version="$1"
    local agent_name="$2"
    local metrics_file="ralf-metrics.jsonl"

    log_info "Initializing metrics file"

    # Check if metrics file exists
    if [[ ! -f "$metrics_file" ]]; then
        echo "{\"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"type\": \"metadata\", \"version\": \"$version\", \"agent\": \"$agent_name\"}" > "$metrics_file"
        log_success "Metrics file created"
    else
        log_warning "Metrics file already exists, appending new version entry"
        echo "{\"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"type\": \"version_init\", \"version\": \"$version\", \"agent\": \"$agent_name\"}" >> "$metrics_file"
    fi
}

create_context_directories() {
    local agent_name="$1"
    local prompts_dir="$ENGINE_DIR/.autonomous/prompts"

    log_info "Creating context directories"

    mkdir -p "$prompts_dir/context/$agent_name"
    mkdir -p "$prompts_dir/exit/$agent_name"

    log_success "Context directories created"
}

create_agent_prompt_template() {
    local agent_name="$1"
    local version="$2"
    local prompts_dir="$ENGINE_DIR/.autonomous/prompts"

    log_info "Creating agent prompt template"

    cat > "$prompts_dir/$agent_name.md" << EOF
# $agent_name

**Version:** $version
**Role:** Task Execution Agent
**Purpose:** Execute tasks with determinism and quality

---

## Context

You are $agent_name operating on BlackBox5.

## Rules

1. **ONE task only** - Never batch multiple tasks
2. **Read before change** - NEVER propose changes to unread code
3. **Integration required** - Code must work with existing system
4. **Atomic commits** - One logical change per commit
5. **Test everything** - Every change verified before marking complete

## Exit Conditions

- **COMPLETE:** Task finished successfully
- **PARTIAL:** Progress made, more work needed
- **BLOCKED:** Cannot proceed without input

---

*This is a template. Customize based on specific agent requirements.*
EOF

    log_success "Agent prompt template created"
}

# =============================================================================
# Main Script
# =============================================================================

main() {
    # Check arguments
    if [[ $# -lt 1 ]]; then
        echo "Usage: $0 <version> [agent-name]"
        echo "Example: $0 v2.5 \"RALF-Analyzer\""
        echo ""
        echo "Arguments:"
        echo "  version     - Version number (format: vX.Y, e.g., v2.5)"
        echo "  agent-name  - Optional agent name (default: ralf-executor-v{X.Y})"
        exit 1
    fi

    local version="$1"
    local agent_name="${2:-ralf-executor-${version}}"

    # Validate version format
    validate_version_format "$version"

    log_info "Creating agent version: $version"
    log_info "Agent name: $agent_name"

    # Detect previous version
    local prev_version
    prev_version=$(detect_previous_version "$version")

    if [[ -n "$prev_version" ]]; then
        log_info "Previous version detected: $prev_version"
    else
        log_warning "No previous version detected (this appears to be the first version)"
    fi

    # Execute setup steps
    echo ""
    log_info "=== Phase 1: Core Components ==="
    setup_version_directory "$version"
    create_agent_config "$agent_name" "$version"

    echo ""
    log_info "=== Phase 2: Supporting Infrastructure ==="
    initialize_metrics "$version" "$agent_name"
    create_context_directories "$agent_name"

    echo ""
    log_info "=== Phase 3: Version-Specific Components ==="
    if [[ -n "$prev_version" && -d "$ENGINE_DIR/.autonomous/prompt-progression/versions/$prev_version" ]]; then
        copy_templates "$prev_version" "$version"
    else
        log_warning "No previous version to copy templates from"
    fi
    create_version_readme "$version"

    echo ""
    log_info "=== Phase 4: Agent Prompt ==="
    create_agent_prompt_template "$agent_name" "$version"

    echo ""
    log_info "=== Setup Complete ==="
    log_success "Agent version $version created successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Review and customize: $ENGINE_DIR/.autonomous/prompts/$agent_name.md"
    echo "  2. Update entry point (bin/ralf.md) to reference new version"
    echo "  3. Test with: ./bin/ralf --version"
    echo "  4. Validate with: ./bin/ralf-dashboard"
    echo ""
    echo "Files created:"
    echo "  - $ENGINE_DIR/.autonomous/prompts/$agent_name.md"
    echo "  - $ENGINE_DIR/.autonomous/agents/$agent_name/config.yaml"
    echo "  - $ENGINE_DIR/.autonomous/prompt-progression/versions/$version/"
    echo "  - ralf-metrics.jsonl (initialized)"
}

# Run main function
main "$@"
