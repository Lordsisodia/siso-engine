#!/bin/bash
# Error Handler Library for RALF
# Provides graceful error handling and degradation for missing/corrupted BB5 files
#
# Usage: source "$(dirname "$0")/../helpers/legacy/error_handler.sh"

# =============================================================================
# CONFIGURATION
# =============================================================================

# Enable/disable graceful degradation (can be overridden via environment)
: "${RALF_GRACEFUL_DEGRADATION:=true}"
: "${RALF_LOG_LEVEL:=INFO}"  # DEBUG, INFO, WARNING, ERROR
: "${RALF_FALLBACK_TEMP_DIR:=/tmp/ralf-fallback}"

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

# Colors (disable if not terminal)
if [ -t 1 ]; then
    _EH_RED='\033[0;31m'
    _EH_YELLOW='\033[1;33m'
    _EH_GREEN='\033[0;32m'
    _EH_BLUE='\033[0;34m'
    _EH_CYAN='\033[0;36m'
    _EH_NC='\033[0m'
else
    _EH_RED=''
    _EH_YELLOW=''
    _EH_GREEN=''
    _EH_BLUE=''
    _EH_CYAN=''
    _EH_NC=''
fi

# Log levels (numeric for comparison)
_EH_LEVEL_DEBUG=0
_EH_LEVEL_INFO=1
_EH_LEVEL_WARNING=2
_EH_LEVEL_ERROR=3

# Convert log level name to number
_eh_get_level_num() {
    local level=$(echo "$1" | tr '[:lower:]' '[:upper:]')
    case "$level" in
        DEBUG) echo 0 ;;
        INFO) echo 1 ;;
        WARNING|WARN) echo 2 ;;
        ERROR|ERR) echo 3 ;;
        *) echo 1 ;;  # Default to INFO
    esac
}

_eh_should_log() {
    local msg_level=$1
    local current_level
    current_level=$(_eh_get_level_num "$RALF_LOG_LEVEL")
    [ "$msg_level" -ge "$current_level" ]
}

eh_log_debug() {
    if _eh_should_log $_EH_LEVEL_DEBUG; then
        echo -e "${_EH_CYAN}[RALF-DEBUG]${_EH_NC} $1" >&2
    fi
}

eh_log_info() {
    if _eh_should_log $_EH_LEVEL_INFO; then
        echo -e "${_EH_BLUE}[RALF-INFO]${_EH_NC} $1" >&2
    fi
}

eh_log_warning() {
    if _eh_should_log $_EH_LEVEL_WARNING; then
        echo -e "${_EH_YELLOW}[RALF-WARN]${_EH_NC} $1" >&2
    fi
}

eh_log_error() {
    if _eh_should_log $_EH_LEVEL_ERROR; then
        echo -e "${_EH_RED}[RALF-ERROR]${_EH_NC} $1" >&2
    fi
}

# =============================================================================
# FILE EXISTENCE CHECKS
# =============================================================================

# Check if file exists, log warning if not
eh_file_exists() {
    local file="$1"
    local context="${2:-}"

    if [ -f "$file" ]; then
        return 0
    else
        if [ -n "$context" ]; then
            eh_log_warning "File not found: $file (context: $context)"
        else
            eh_log_warning "File not found: $file"
        fi
        return 1
    fi
}

# Check if directory exists, log warning if not
eh_dir_exists() {
    local dir="$1"
    local context="${2:-}"

    if [ -d "$dir" ]; then
        return 0
    else
        if [ -n "$context" ]; then
            eh_log_warning "Directory not found: $dir (context: $context)"
        else
            eh_log_warning "Directory not found: $dir"
        fi
        return 1
    fi
}

# =============================================================================
# GRACEFUL DEGRADATION
# =============================================================================

# Handle missing file with fallback options
eh_handle_missing_file() {
    local primary_path="$1"
    local context="${2:-}"
    shift 2
    local fallback_paths=("$@")

    # Check primary path
    if [ -f "$primary_path" ]; then
        echo "$primary_path"
        return 0
    fi

    eh_log_warning "Primary file not found: $primary_path${context:+ ($context)}"

    # Try fallback paths
    for fallback in "${fallback_paths[@]}"; do
        if [ -f "$fallback" ]; then
            eh_log_info "Using fallback: $fallback"
            echo "$fallback"
            return 0
        fi
    done

    # If graceful degradation is enabled, return empty
    if [ "$RALF_GRACEFUL_DEGRADATION" = "true" ]; then
        eh_log_warning "No fallback available, continuing without file"
        return 1
    else
        eh_log_error "File not found and graceful degradation disabled"
        return 1
    fi
}

# Handle missing directory with fallback options
eh_handle_missing_dir() {
    local primary_path="$1"
    local context="${2:-}"
    shift 2
    local fallback_paths=("$@")

    # Check primary path
    if [ -d "$primary_path" ]; then
        echo "$primary_path"
        return 0
    fi

    eh_log_warning "Primary directory not found: $primary_path${context:+ ($context)}"

    # Try fallback paths
    for fallback in "${fallback_paths[@]}"; do
        if [ -d "$fallback" ]; then
            eh_log_info "Using fallback directory: $fallback"
            echo "$fallback"
            return 0
        fi
    done

    # If graceful degradation is enabled, try to create temp directory
    if [ "$RALF_GRACEFUL_DEGRADATION" = "true" ]; then
        local temp_dir="$RALF_FALLBACK_TEMP_DIR/$(date +%s)"
        mkdir -p "$temp_dir"
        eh_log_warning "Using temporary directory: $temp_dir"
        echo "$temp_dir"
        return 0
    else
        eh_log_error "Directory not found and graceful degradation disabled"
        return 1
    fi
}

# =============================================================================
# YAML FILE HANDLING
# =============================================================================

# Safely read a YAML value with fallback
eh_yaml_get() {
    local file="$1"
    local key="$2"
    local default="${3:-}"

    if [ ! -f "$file" ]; then
        eh_log_warning "Cannot read YAML: file not found: $file"
        echo "$default"
        return 1
    fi

    # Try to extract value using grep/sed
    local value
    value=$(grep -E "^${key}:" "$file" 2>/dev/null | head -1 | cut -d':' -f2- | sed 's/^[ "]*//;s/[ "]*$//' || echo "")

    if [ -z "$value" ]; then
        echo "$default"
        return 1
    fi

    echo "$value"
    return 0
}

# Safely append to YAML file (creates if missing)
eh_yaml_append() {
    local file="$1"
    local content="$2"

    # Ensure directory exists
    local dir
    dir=$(dirname "$file")
    if [ ! -d "$dir" ]; then
        eh_log_warning "Creating missing directory: $dir"
        mkdir -p "$dir" || {
            eh_log_error "Failed to create directory: $dir"
            return 1
        }
    fi

    # Create file if it doesn't exist with header
    if [ ! -f "$file" ]; then
        eh_log_warning "Creating missing YAML file: $file"
        cat > "$file" << EOF
# Auto-generated by RALF error handler
# Created: $(date -Iseconds)
EOF
    fi

    # Append content
    echo "$content" >> "$file"
    return 0
}

# =============================================================================
# LOCK FILE HANDLING
# =============================================================================

# Safely acquire lock with timeout
eh_acquire_lock() {
    local lock_file="$1"
    local timeout="${2:-10}"

    # Ensure directory exists
    local dir
    dir=$(dirname "$lock_file")
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir" || {
            eh_log_error "Cannot create lock directory: $dir"
            return 1
        }
    fi

    # Try to acquire lock
    local count=0
    while [ $count -lt "$timeout" ]; do
        if (set -C; echo $$ > "$lock_file" 2>/dev/null); then
            # Lock acquired
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done

    eh_log_warning "Could not acquire lock: $lock_file (timeout after ${timeout}s)"
    return 1
}

# Release lock
eh_release_lock() {
    local lock_file="$1"
    if [ -f "$lock_file" ]; then
        rm -f "$lock_file"
    fi
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

# Validate YAML file is not corrupted
eh_validate_yaml() {
    local file="$1"

    if [ ! -f "$file" ]; then
        eh_log_warning "YAML validation: file not found: $file"
        return 1
    fi

    # Basic validation: check for balanced braces/brackets
    local open_count
    local close_count

    open_count=$(grep -o '{' "$file" 2>/dev/null | wc -l | tr -d ' ')
    close_count=$(grep -o '}' "$file" 2>/dev/null | wc -l | tr -d ' ')

    if [ "$open_count" != "$close_count" ]; then
        eh_log_warning "YAML validation: unbalanced braces in $file"
        return 1
    fi

    # Check for basic YAML structure
    if ! grep -qE '^[a-zA-Z_][a-zA-Z0-9_]*:' "$file" 2>/dev/null; then
        eh_log_warning "YAML validation: no valid keys found in $file"
        return 1
    fi

    return 0
}

# Validate file is readable and not empty
eh_validate_file() {
    local file="$1"

    if [ ! -f "$file" ]; then
        eh_log_warning "Validation: file not found: $file"
        return 1
    fi

    if [ ! -r "$file" ]; then
        eh_log_warning "Validation: file not readable: $file"
        return 1
    fi

    if [ ! -s "$file" ]; then
        eh_log_warning "Validation: file is empty: $file"
        return 1
    fi

    return 0
}

# =============================================================================
# RECOVERY ACTIONS
# =============================================================================

# Create minimal queue.yaml for recovery
eh_create_minimal_queue() {
    local target_file="$1"

    eh_log_warning "Creating minimal queue.yaml for recovery"

    mkdir -p "$(dirname "$target_file")"

    cat > "$target_file" << 'EOF'
schema:
  version: 1.0.0
  generated: 'auto-recovery'
priority_formula:
  description: (impact / effort) * confidence
tasks: []
queue_metadata:
  derived_from_filesystem: true
  note: Auto-generated recovery file
EOF

    eh_log_info "Created minimal queue at: $target_file"
}

# Create minimal events.yaml for recovery
eh_create_minimal_events() {
    local target_file="$1"

    eh_log_warning "Creating minimal events.yaml for recovery"

    mkdir -p "$(dirname "$target_file")"

    cat > "$target_file" << EOF
# Auto-generated recovery events file
# Created: $(date -Iseconds)

events: []
EOF

    eh_log_info "Created minimal events at: $target_file"
}

# Create minimal heartbeat.yaml for recovery
eh_create_minimal_heartbeat() {
    local target_file="$1"

    eh_log_warning "Creating minimal heartbeat.yaml for recovery"

    mkdir -p "$(dirname "$target_file")"

    cat > "$target_file" << EOF
# Auto-generated recovery heartbeat file
# Created: $(date -Iseconds)

planner:
  status: unknown
  last_seen: '$(date -Iseconds)'
  current_action: recovery_mode
executor:
  status: unknown
  last_seen: '$(date -Iseconds)'
  current_action: recovery_mode
verifier:
  status: unknown
  last_seen: '$(date -Iseconds)'
  current_action: recovery_mode
EOF

    eh_log_info "Created minimal heartbeat at: $target_file"
}

# =============================================================================
# WRAPPER FUNCTIONS FOR COMMON OPERATIONS
# =============================================================================

# Safe source with fallback
eh_safe_source() {
    local file="$1"

    if [ -f "$file" ]; then
        # shellcheck source=/dev/null
        source "$file"
        return 0
    else
        eh_log_warning "Cannot source: file not found: $file"
        return 1
    fi
}

# Safe mkdir with error handling
eh_ensure_dir() {
    local dir="$1"

    if [ -d "$dir" ]; then
        return 0
    fi

    if mkdir -p "$dir" 2>/dev/null; then
        eh_log_debug "Created directory: $dir"
        return 0
    else
        eh_log_error "Failed to create directory: $dir"
        return 1
    fi
}

# Safe write to file with backup
eh_safe_write() {
    local file="$1"
    local content="$2"

    # Ensure directory exists
    local dir
    dir=$(dirname "$file")
    eh_ensure_dir "$dir" || return 1

    # Create backup if file exists
    if [ -f "$file" ]; then
        cp "$file" "$file.bak" 2>/dev/null || true
    fi

    # Write content
    if echo "$content" > "$file"; then
        return 0
    else
        eh_log_error "Failed to write to: $file"
        # Restore backup if available
        if [ -f "$file.bak" ]; then
            mv "$file.bak" "$file"
        fi
        return 1
    fi
}

# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

export -f eh_log_debug eh_log_info eh_log_warning eh_log_error
export -f eh_file_exists eh_dir_exists
export -f eh_handle_missing_file eh_handle_missing_dir
export -f eh_yaml_get eh_yaml_append
export -f eh_acquire_lock eh_release_lock
export -f eh_validate_yaml eh_validate_file
export -f eh_create_minimal_queue eh_create_minimal_events eh_create_minimal_heartbeat
export -f eh_safe_source eh_ensure_dir eh_safe_write
