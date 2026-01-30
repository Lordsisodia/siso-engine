#!/bin/bash
# Dry-run utility library for RALF shell scripts
# Source this file to add --dry-run support to any script
#
# Usage:
#   source "$(dirname "$0")/../lib/dry_run.sh"
#   dry_run_init "$@"
#
#   if dry_run_is_active; then
#       dry_run_echo "Would create directory: $dir"
#   else
#       mkdir -p "$dir"
#   fi
#
#   # Or use the helper:
#   dry_run_exec "mkdir -p $dir" "Create directory $dir"

# Dry-run state
DRY_RUN=false
DRY_RUN_VERBOSE=false

# Colors (can be overridden)
DRY_RUN_COLOR='\033[0;33m'  # Yellow
NC='\033[0m'

# Initialize dry-run mode from command-line arguments
# Usage: dry_run_init "$@"
# Returns: Modified arguments with --dry-run and --verbose removed
dry_run_init() {
    local args=()
    for arg in "$@"; do
        case "$arg" in
            --dry-run)
                DRY_RUN=true
                ;;
            --verbose|-v)
                DRY_RUN_VERBOSE=true
                ;;
            *)
                args+=("$arg")
                ;;
        esac
    done

    if dry_run_is_active; then
        echo -e "${DRY_RUN_COLOR}[DRY-RUN MODE ENABLED]${NC}" >&2
        echo -e "${DRY_RUN_COLOR}This is a simulation. No changes will be made.${NC}" >&2
        echo "" >&2
    fi

    # Return remaining args
    echo "${args[@]}"
}

# Check if dry-run mode is active
# Usage: if dry_run_is_active; then ...
dry_run_is_active() {
    [[ "$DRY_RUN" == "true" ]]
}

# Check if verbose mode is active
dry_run_is_verbose() {
    [[ "$DRY_RUN_VERBOSE" == "true" ]]
}

# Print what would happen
# Usage: dry_run_echo "message"
dry_run_echo() {
    echo -e "${DRY_RUN_COLOR}[DRY-RUN] Would: $1${NC}"
}

# Execute a command or print what would be executed
# Usage: dry_run_exec "command" ["description"]
# If description is provided, it will be shown instead of the raw command
dry_run_exec() {
    local cmd="$1"
    local description="${2:-$1}"

    if dry_run_is_active; then
        dry_run_echo "$description"
        return 0
    else
        eval "$cmd"
        return $?
    fi
}

# Run a command with arguments or print what would be executed
# Usage: dry_run_run description command [args...]
dry_run_run() {
    local description="$1"
    shift

    if dry_run_is_active; then
        dry_run_echo "$description: $*"
        return 0
    else
        "$@"
        return $?
    fi
}

# Create a directory or print what would be created
dry_run_mkdir() {
    local dir="$1"

    if dry_run_is_active; then
        if [[ -d "$dir" ]]; then
            dry_run_echo "mkdir -p $dir (already exists)"
        else
            dry_run_echo "mkdir -p $dir"
        fi
        return 0
    else
        mkdir -p "$dir"
        return $?
    fi
}

# Write to a file or print what would be written
dry_run_write() {
    local file="$1"
    local content="$2"

    if dry_run_is_active; then
        dry_run_echo "Write to $file:"
        if dry_run_is_verbose; then
            echo "$content" | sed 's/^/  /'
        else
            echo "  (content hidden, use --verbose to see)"
        fi
        return 0
    else
        echo "$content" > "$file"
        return $?
    fi
}

# Append to a file or print what would be appended
dry_run_append() {
    local file="$1"
    local content="$2"

    if dry_run_is_active; then
        dry_run_echo "Append to $file:"
        if dry_run_is_verbose; then
            echo "$content" | sed 's/^/  /'
        else
            echo "  (content hidden, use --verbose to see)"
        fi
        return 0
    else
        echo "$content" >> "$file"
        return $?
    fi
}

# Move a file or print what would be moved
dry_run_mv() {
    local src="$1"
    local dst="$2"

    if dry_run_is_active; then
        dry_run_echo "mv $src $dst"
        return 0
    else
        mv "$src" "$dst"
        return $?
    fi
}

# Copy a file or print what would be copied
dry_run_cp() {
    local src="$1"
    local dst="$2"

    if dry_run_is_active; then
        dry_run_echo "cp $src $dst"
        return 0
    else
        cp "$src" "$dst"
        return $?
    fi
}

# Remove a file or print what would be removed
dry_run_rm() {
    local file="$1"

    if dry_run_is_active; then
        dry_run_echo "rm $file"
        return 0
    else
        rm "$file"
        return $?
    fi
}

# Remove a directory recursively or print what would be removed
dry_run_rm_rf() {
    local dir="$1"

    if dry_run_is_active; then
        dry_run_echo "rm -rf $dir"
        return 0
    else
        rm -rf "$dir"
        return $?
    fi
}

# Execute a git command or print what would be executed
dry_run_git() {
    if dry_run_is_active; then
        dry_run_echo "git $*"
        return 0
    else
        git "$@"
        return $?
    fi
}

# Touch a file or print what would be touched
dry_run_touch() {
    local file="$1"

    if dry_run_is_active; then
        dry_run_echo "touch $file"
        return 0
    else
        touch "$file"
        return $?
    fi
}

# Change directory or print what would be changed
dry_run_cd() {
    local dir="$1"

    if dry_run_is_active; then
        dry_run_echo "cd $dir"
        return 0
    else
        cd "$dir"
        return $?
    fi
}

# Source a file or print what would be sourced
dry_run_source() {
    local file="$1"

    if dry_run_is_active; then
        dry_run_echo "source $file"
        return 0
    else
        source "$file"
        return $?
    fi
}

# Print dry-run summary
dry_run_summary() {
    if dry_run_is_active; then
        echo "" >&2
        echo -e "${DRY_RUN_COLOR}[DRY-RUN COMPLETE]${NC}" >&2
        echo -e "${DRY_RUN_COLOR}No changes were made. Run without --dry-run to execute.${NC}" >&2
    fi
}

# Set a trap to print summary on exit
dry_run_set_exit_trap() {
    if dry_run_is_active; then
        trap dry_run_summary EXIT
    fi
}
