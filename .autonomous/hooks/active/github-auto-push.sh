#!/bin/bash
# GitHub Auto-Push Hook for BB5
# Hook Type: Stop (fires when session ends)
# Version: 1.0.0
#
# Automatically commits and pushes changes to GitHub when a BB5 session ends.
# Works with claude/[task-slug] branches.
#
# Safety features:
# - Never pushes to main/master directly
# - Never force pushes
# - Checks for merge conflicts before pushing
# - Respects BB5_AUTO_PUSH=false to disable
# - Respects .bb5-no-auto-push file in repo root

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

# Event logging
EVENTS_FILE="${HOME}/.blackbox5/5-project-memory/blackbox5/.autonomous/agents/communications/events.yaml"
LOG_DIR="${HOME}/.blackbox5/2-engine/.autonomous/logs"
LOG_FILE="${LOG_DIR}/github-auto-push.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }

# ============================================================================
# EVENT LOGGING
# ============================================================================

log_event() {
    local type="$1"
    local message="$2"
    local timestamp
    timestamp=$(date '+%Y-%m-%dT%H:%M:%S%z')

    # Create event entry
    local event_entry
    event_entry=$(cat <<EOF

- timestamp: "$timestamp"
  type: "$type"
  agent_type: "github-auto-push"
  agent_id: "${BB5_AGENT_ID:-unknown}"
  parent_task: "${BB5_TASK_ID:-}"
  source: "hook"
  message: "$message"
EOF
)

    # Append to events.yaml if it exists and is writable
    if [ -f "$EVENTS_FILE" ] && [ -w "$EVENTS_FILE" ]; then
        echo "$event_entry" >> "$EVENTS_FILE"
    fi
}

# ============================================================================
# SAFETY CHECKS
# ============================================================================

check_disabled() {
    # Check environment variable
    if [ "${BB5_AUTO_PUSH:-}" = "false" ]; then
        log_info "Auto-push disabled via BB5_AUTO_PUSH=false"
        log_event "auto_push_skipped" "Disabled via environment variable"
        exit 0
    fi

    # Check for .bb5-no-auto-push file in repo root
    if [ -f ".bb5-no-auto-push" ]; then
        log_info "Auto-push disabled via .bb5-no-auto-push file"
        log_event "auto_push_skipped" "Disabled via .bb5-no-auto-push file"
        exit 0
    fi
}

# ============================================================================
# GIT REPOSITORY CHECKS
# ============================================================================

check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_warn "Not in a git repository"
        log_event "auto_push_error" "Not in a git repository"
        exit 0
    fi

    log_info "Git repository detected"
}

get_current_branch() {
    git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown"
}

check_branch() {
    local branch="$1"

    # Never push to main/master directly
    if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
        log_warn "Current branch is $branch - refusing to auto-push to main/master"
        log_event "auto_push_blocked" "Refused to push to $branch branch"
        exit 0
    fi

    # Check if branch follows claude/* pattern
    if [[ ! "$branch" =~ ^claude/ ]]; then
        log_warn "Current branch '$branch' does not match claude/* pattern"
        log_event "auto_push_warning" "Branch '$branch' does not follow claude/* pattern"
        # Continue anyway - user might have different naming convention
    fi

    log_info "Current branch: $branch"
}

check_remote() {
    # Check if remote exists
    if ! git remote get-url origin > /dev/null 2>&1; then
        log_warn "No remote 'origin' configured"
        log_event "auto_push_error" "No remote 'origin' configured"
        exit 0
    fi

    local remote_url
    remote_url=$(git remote get-url origin)
    log_info "Remote origin: $remote_url"
}

# ============================================================================
# CHANGE DETECTION
# ============================================================================

has_uncommitted_changes() {
    # Check for staged or unstaged changes
    if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
        return 0
    fi
    return 1
}

# ============================================================================
# COMMIT MESSAGE GENERATION
# ============================================================================

generate_commit_message() {
    local task_id="${BB5_TASK_ID:-}"
    local run_id="${BB5_RUN_ID:-}"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Get list of changed files
    local changed_files
    changed_files=$(git diff --name-only 2>/dev/null | head -20 | tr '\n' ', ' | sed 's/, $//')

    # Build commit message
    local subject
    if [ -n "$task_id" ]; then
        subject="bb5: ${task_id} Auto-commit session changes"
    else
        subject="bb5: Auto-commit session changes"
    fi

    # Build body
    local body="Changes made during BB5 session"

    if [ -n "$task_id" ]; then
        body="${body}

- Task: ${task_id}"
    fi

    if [ -n "$run_id" ]; then
        body="${body}
- Run: ${run_id}"
    fi

    body="${body}
- Timestamp: ${timestamp}"

    if [ -n "$changed_files" ]; then
        body="${body}
- Files: ${changed_files}"
    fi

    # Output the full message
    echo "$subject"
    echo ""
    echo "$body"
}

# ============================================================================
# MERGE CONFLICT CHECK
# ============================================================================

check_merge_conflicts() {
    # Fetch latest from remote to check for conflicts
    local branch="$1"

    log_info "Fetching latest from origin..."

    if ! git fetch origin "$branch" 2>/dev/null; then
        # Branch might not exist on remote yet - that's OK
        log_info "Branch '$branch' not found on remote (will be created)"
        return 0
    fi

    # Check if we can merge without conflicts
    local merge_base
    merge_base=$(git merge-base HEAD "origin/$branch" 2>/dev/null || echo "")

    if [ -n "$merge_base" ]; then
        local common_ancestor="$merge_base"
        local remote_head
        remote_head=$(git rev-parse "origin/$branch" 2>/dev/null || echo "")

        if [ "$common_ancestor" != "$remote_head" ]; then
            # Remote has changes we don't have
            log_warn "Remote has changes not present locally"

            # Check if merge would conflict
            if ! git merge-tree "$common_ancestor" HEAD "origin/$branch" > /dev/null 2>&1; then
                log_error "Merge conflicts detected - aborting push"
                log_event "auto_push_blocked" "Merge conflicts with origin/$branch"
                return 1
            fi
        fi
    fi

    return 0
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    log_info "=== GitHub Auto-Push Hook Started ==="

    # Safety checks
    check_disabled
    check_git_repo

    # Get current branch
    local branch
    branch=$(get_current_branch)

    # Validate branch
    check_branch "$branch"

    # Check remote
    check_remote

    # Check for uncommitted changes
    if ! has_uncommitted_changes; then
        log_info "No uncommitted changes - nothing to push"
        log_event "auto_push_noop" "No uncommitted changes"
        exit 0
    fi

    log_info "Uncommitted changes detected"

    # Stage all changes
    log_info "Staging all changes..."
    git add -A

    # Generate commit message
    local commit_message
    commit_message=$(generate_commit_message)

    # Create commit
    log_info "Creating commit..."
    if ! git commit -m "$commit_message" > /dev/null 2>&1; then
        log_error "Failed to create commit"
        log_event "auto_push_error" "Failed to create commit"
        exit 1
    fi

    log_info "Commit created successfully"

    # Check for merge conflicts before pushing
    if ! check_merge_conflicts "$branch"; then
        log_error "Cannot push due to potential merge conflicts"
        # Reset the commit to avoid leaving repo in bad state
        git reset --soft HEAD~1
        git reset HEAD > /dev/null 2>&1 || true
        exit 1
    fi

    # Push to origin
    log_info "Pushing to origin/$branch..."

    # Check if branch has upstream tracking
    local upstream
    upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || echo "")

    local push_result=0
    if [ -n "$upstream" ]; then
        # Branch has upstream, push normally (no force)
        if ! git push origin "$branch" 2>&1 >> "$LOG_FILE"; then
            push_result=1
        fi
    else
        # No upstream, set it up
        if ! git push -u origin "$branch" 2>&1 >> "$LOG_FILE"; then
            push_result=1
        fi
    fi

    if [ $push_result -eq 0 ]; then
        log_info "Successfully pushed to origin/$branch"
        log_event "auto_push_success" "Pushed branch $branch to origin"

        # Get commit hash for logging
        local commit_hash
        commit_hash=$(git rev-parse --short HEAD)
        log_info "Commit: $commit_hash"
    else
        log_error "Failed to push to origin/$branch"
        log_event "auto_push_error" "Failed to push branch $branch"
        exit 1
    fi

    log_info "=== GitHub Auto-Push Hook Completed ==="
}

# ============================================================================
# ENTRY POINT
# ============================================================================

# Run main function
main "$@"
