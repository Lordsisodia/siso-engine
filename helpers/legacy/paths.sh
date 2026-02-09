#!/bin/bash
# Path Resolution Library for BlackBox5
# =====================================
#
# Unified path resolution for BlackBox5 bash scripts.
# Eliminates hardcoded paths throughout the codebase.
#
# Usage:
#   source "$(dirname "$0")/../lib/paths.sh"
#
#   # Get common paths
#   bb5_root=$(get_blackbox5_root)
#   engine_path=$(get_engine_path)
#   project_path=$(get_project_path "blackbox5")
#
#   # Build custom paths
#   custom_path=$(bb5_path "custom" "subdir")

# =============================================================================
# Configuration
# =============================================================================

# Allow override via environment
: "${BLACKBOX5_HOME:=${BB5_HOME:-$HOME/.blackbox5}}"
: "${BB5_PROJECT:=blackbox5}"

# Cache for computed paths (using simple variables for bash 3.x compatibility)
# Format: _BB5_CACHE_<key>=value

# =============================================================================
# Core Path Functions
# =============================================================================

# Get BlackBox5 root directory
# Usage: root=$(get_blackbox5_root)
get_blackbox5_root() {
    echo "$BLACKBOX5_HOME"
}

# Get engine root directory
# Usage: engine=$(get_engine_path)
get_engine_path() {
    if [[ -n "${BB5_ENGINE_ROOT:-}" ]]; then
        echo "$BB5_ENGINE_ROOT"
    else
        # Default: 2-engine directory (parent of helpers/legacy)
        local script_dir
        script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        # script_dir is .../helpers/legacy, so go up 2 levels to get to 2-engine
        dirname "$(dirname "$script_dir")"
    fi
}

# Get library directory path
# Usage: lib=$(get_lib_path)
get_lib_path() {
    local engine
    engine=$(get_engine_path)
    echo "$engine/helpers/legacy"
}

# Get engine config directory path
# Usage: config=$(get_config_path)
get_config_path() {
    local engine
    engine=$(get_engine_path)
    echo "$engine/configuration"
}

# Get prompts directory path
# Usage: prompts=$(get_prompts_path)
get_prompts_path() {
    local engine
    engine=$(get_engine_path)
    echo "$engine/instructions"
}

# Get hooks directory path
# Usage: hooks=$(get_hooks_path)
get_hooks_path() {
    local engine
    engine=$(get_engine_path)
    echo "$engine/infrastructure/hooks"
}

# Get bin directory path
# Usage: bin=$(get_bin_path)
get_bin_path() {
    local engine
    engine=$(get_engine_path)
    echo "$engine/executables"
}

# Get templates directory path
# Usage: templates=$(get_templates_path)
get_templates_path() {
    local engine
    engine=$(get_engine_path)
    echo "$engine/infrastructure/templates"
}

# =============================================================================
# Memory/Project Paths
# =============================================================================

# Get project memory root directory (5-project-memory)
# Usage: memory=$(get_memory_root)
get_memory_root() {
    if [[ -n "${BB5_MEMORY_PATH:-}" ]]; then
        echo "$BB5_MEMORY_PATH"
    else
        local root
        root=$(get_blackbox5_root)
        echo "$root/5-project-memory"
    fi
}

# Get documentation root directory (1-docs)
# Usage: docs=$(get_docs_root)
get_docs_root() {
    local root
    root=$(get_blackbox5_root)
    echo "$root/1-docs"
}

# Get tools/bin root directory (bin)
# Usage: bin=$(get_bin_root)
get_bin_root() {
    local root
    root=$(get_blackbox5_root)
    echo "$root/bin"
}

# Get roadmap directory (6-roadmap)
# Usage: roadmap=$(get_roadmap_root)
get_roadmap_root() {
    local root
    root=$(get_blackbox5_root)
    echo "$root/6-roadmap"
}

# Get project directory path
# Usage: project=$(get_project_path [project_name])
get_project_path() {
    local project_name="${1:-$BB5_PROJECT}"
    local memory
    memory=$(get_memory_root)
    echo "$memory/$project_name"
}

# Get project config file path
# Usage: config=$(get_project_config_path [project_name])
get_project_config_path() {
    local project_name="${1:-$BB5_PROJECT}"
    local project_path
    project_path=$(get_project_path "$project_name")
    echo "$project_path/.autonomous/config/project.yaml"
}

# Get runs directory path for a project
# Usage: runs=$(get_runs_path [project_name])
get_runs_path() {
    local project_name="${1:-$BB5_PROJECT}"
    local project_path
    project_path=$(get_project_path "$project_name")
    echo "$project_path/.autonomous/runs"
}

# Get tasks directory path for a project
# Usage: tasks=$(get_tasks_path [project_name] [status])
get_tasks_path() {
    local project_name="${1:-$BB5_PROJECT}"
    local status="${2:-active}"
    local project_path
    project_path=$(get_project_path "$project_name")
    echo "$project_path/.autonomous/tasks/$status"
}

# Get memory directory path for a project
# Usage: memory=$(get_project_memory_path [project_name])
get_project_memory_path() {
    local project_name="${1:-$BB5_PROJECT}"
    local project_path
    project_path=$(get_project_path "$project_name")
    echo "$project_path/.autonomous/memory"
}

# Get analysis directory path for a project
# Usage: analysis=$(get_analysis_path [project_name])
get_analysis_path() {
    local project_name="${1:-$BB5_PROJECT}"
    local project_path
    project_path=$(get_project_path "$project_name")
    echo "$project_path/.autonomous/analysis"
}

# Get timeline directory path for a project
# Usage: timeline=$(get_timeline_path [project_name])
get_timeline_path() {
    local project_name="${1:-$BB5_PROJECT}"
    local project_path
    project_path=$(get_project_path "$project_name")
    echo "$project_path/.autonomous/timeline"
}

# Get routes.yaml file path
# Usage: routes=$(get_routes_path)
get_routes_path() {
    local engine
    engine=$(get_engine_path)
    echo "$engine/configuration/routes.yaml"
}

# =============================================================================
# Specific Run/Task Paths
# =============================================================================

# Get specific run directory path
# Usage: run_dir=$(get_run_path "run-001" [project_name])
get_run_path() {
    local run_id="$1"
    local project_name="${2:-$BB5_PROJECT}"
    local runs_path
    runs_path=$(get_runs_path "$project_name")
    echo "$runs_path/$run_id"
}

# Get specific task directory path
# Usage: task_dir=$(get_task_path "TASK-001" [project_name])
get_task_path() {
    local task_id="$1"
    local project_name="${2:-$BB5_PROJECT}"
    local active_path completed_path

    active_path="$(get_tasks_path "$project_name" active)/$task_id"
    completed_path="$(get_tasks_path "$project_name" completed)/$task_id"

    if [[ -d "$active_path" ]]; then
        echo "$active_path"
    else
        echo "$completed_path"
    fi
}

# =============================================================================
# Path Building Utilities
# =============================================================================

# Build path relative to BlackBox5 root
# Usage: path=$(bb5_path "5-project-memory" "myproject" "file.txt")
bb5_path() {
    local root
    root=$(get_blackbox5_root)
    local path="$root"
    for part in "$@"; do
        path="$path/$part"
    done
    echo "$path"
}

# Build path relative to engine root
# Usage: path=$(engine_path ".autonomous" "lib" "script.py")
engine_path() {
    local engine
    engine=$(get_engine_path)
    local path="$engine"
    for part in "$@"; do
        path="$path/$part"
    done
    echo "$path"
}

# Build path relative to project
# Usage: path=$(project_path "myproject" ".autonomous" "config")
project_path() {
    local project_name="$1"
    shift
    local project_root
    project_root=$(get_project_path "$project_name")
    local path="$project_root"
    for part in "$@"; do
        path="$path/$part"
    done
    echo "$path"
}

# =============================================================================
# Path Validation Utilities
# =============================================================================

# Check if path exists
# Usage: if path_exists "$path"; then ...
path_exists() {
    [[ -e "$1" ]]
}

# Check if directory exists
# Usage: if dir_exists "$path"; then ...
dir_exists() {
    [[ -d "$1" ]]
}

# Check if file exists
# Usage: if file_exists "$path"; then ...
file_exists() {
    [[ -f "$1" ]]
}

# Ensure directory exists (create if not)
# Usage: ensure_dir "$path"
ensure_dir() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
    fi
    echo "$dir"
}

# Get absolute path
# Usage: abs=$(abs_path "./relative/path")
abs_path() {
    local path="$1"
    if [[ -d "$path" ]]; then
        (cd "$path" && pwd)
    else
        local dir
        dir=$(dirname "$path")
        local base
        base=$(basename "$path")
        echo "$(cd "$dir" && pwd)/$base"
    fi
}

# =============================================================================
# Debug/Info Functions
# =============================================================================

# Print all resolved paths (for debugging)
# Usage: bb5_paths_info
bb5_paths_info() {
    echo "BlackBox5 Path Resolution"
    echo "========================="
    echo "BlackBox5 Root: $(get_blackbox5_root)"
    echo "Engine Path: $(get_engine_path)"
    echo "Lib Path: $(get_lib_path)"
    echo "Config Path: $(get_config_path)"
    echo "Memory Root: $(get_memory_root)"
    echo "Docs Root: $(get_docs_root)"
    echo "Bin Root: $(get_bin_root)"
    echo "Roadmap Root: $(get_roadmap_root)"
    echo ""
    echo "Current Project: $BB5_PROJECT"
    echo "Project Path: $(get_project_path)"
    echo "Runs Path: $(get_runs_path)"
    echo "Tasks Path: $(get_tasks_path)"
    echo "Project Memory: $(get_project_memory_path)"
    echo "Analysis Path: $(get_analysis_path)"
    echo "Timeline Path: $(get_timeline_path)"
    echo "Routes Path: $(get_routes_path)"
}

# Export all functions for use in other scripts
export -f get_blackbox5_root
export -f get_engine_path
export -f get_lib_path
export -f get_config_path
export -f get_prompts_path
export -f get_hooks_path
export -f get_bin_path
export -f get_templates_path
export -f get_memory_root
export -f get_docs_root
export -f get_bin_root
export -f get_roadmap_root
export -f get_project_path
export -f get_project_config_path
export -f get_runs_path
export -f get_tasks_path
export -f get_project_memory_path
export -f get_analysis_path
export -f get_timeline_path
export -f get_routes_path
export -f get_run_path
export -f get_task_path
export -f bb5_path
export -f engine_path
export -f project_path
export -f path_exists
export -f dir_exists
export -f file_exists
export -f ensure_dir
export -f abs_path
export -f bb5_paths_info

# If script is run directly, show info
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    bb5_paths_info
fi
