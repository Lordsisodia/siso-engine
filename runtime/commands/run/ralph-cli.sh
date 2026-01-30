#!/bin/bash

################################################################################
# Ralph CLI - Unified CLI for all Ralph Runtime operations
# Comprehensive command-line interface for Ralph Runtime
################################################################################

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
RALPH_CLI_DIR="$PROJECT_ROOT/.blackbox4/ralph-runtime"
CONFIG_DIR="$PROJECT_ROOT/.blackbox4/config"
LOGS_DIR="$PROJECT_ROOT/.blackbox4/logs"
SESSIONS_DIR="$PROJECT_ROOT/.blackbox4/sessions"
STATE_DIR="$PROJECT_ROOT/.blackbox4/state"

# Default values
VERBOSE=false
QUIET=false
DEBUG=false
JSON_OUTPUT=false
INTERACTIVE=false
AUTO_CONFIRM=false

# Current session
CURRENT_SESSION=""

################################################################################
# Helper Functions
################################################################################

print_header() {
    [ "$QUIET" = false ] || return 0
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}${BOLD}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_section() {
    [ "$QUIET" = false ] || return 0
    echo -e "\n${BLUE}${BOLD}▶ $1${NC}\n"
}

print_success() {
    [ "$QUIET" = false ] || return 0
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗ ERROR:${NC} $1" >&2
}

print_warning() {
    [ "$QUIET" = false ] || return 0
    echo -e "${YELLOW}⚠ WARNING:${NC} $1"
}

print_info() {
    [ "$QUIET" = false ] || return 0
    echo -e "${PURPLE}ℹ${NC} $1"
}

verbose_log() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${CYAN}[DEBUG]${NC} $1" >&2
    fi
}

debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${YELLOW}[DEBUG]${NC} $1" >&2
    fi
}

show_version() {
    cat << EOF
${GREEN}Ralph CLI${NC} - Unified Command-Line Interface for Ralph Runtime
${CYAN}Version:${NC} 1.0.0
${CYAN}Project:${NC} Blackbox4 Phase 4
${CYAN}Author:${NC} Black Box Factory
${CYAN}License:${NC} MIT

For more information, run: ralph-cli help
EOF
}

show_help() {
    cat << EOF
${GREEN}Ralph CLI${NC} - Unified CLI for Ralph Runtime operations

${YELLOW}USAGE:${NC}
    ralph-cli <command> [options]

${YELLOW}CORE COMMANDS:${NC}
    ${CYAN}run${NC}           Execute plans or agents
    ${CYAN}status${NC}        Show system status
    ${CYAN}config${NC}        Manage configuration
    ${CYAN}logs${NC}          View logs
    ${CYAN}metrics${NC}       Show metrics

${YELLOW}SESSION COMMANDS:${NC}
    ${CYAN}session${NC}       Manage sessions
    ${CYAN}pause${NC}         Pause a session
    ${CYAN}resume${NC}        Resume a session
    ${CYAN}stop${NC}          Stop a session

${YELLOW}ANALYSIS COMMANDS:${NC}
    ${CYAN}analyze${NC}       Analyze responses
    ${CYAN}test${NC}          Run tests
    ${CYAN}validate${NC}      Validate configurations

${YELLOW}AUTONOMOUS COMMANDS:${NC}
    ${CYAN}auto${NC}          Autonomous execution
    ${CYAN}monitor${NC}       Monitor execution
    ${CYAN}intervene${NC}     Intervene in execution

${YELLOW}SYSTEM COMMANDS:${NC}
    ${CYAN}health${NC}        Check system health
    ${CYAN}doctor${NC}        Diagnose issues
    ${CYAN}clean${NC}         Clean up resources

${YELLOW}UTILITY COMMANDS:${NC}
    ${CYAN}help${NC}          Show help
    ${CYAN}version${NC}       Show version
    ${CYAN}completion${NC}    Generate shell completion

${YELLOW}GLOBAL OPTIONS:${NC}
    ${CYAN}-v, --verbose${NC}         Enable verbose output
    ${CYAN}-q, --quiet${NC}           Suppress output (except errors)
    ${CYAN}-d, --debug${NC}           Enable debug mode
    ${CYAN}-y, --yes${NC}             Auto-confirm prompts
    ${CYAN}-j, --json${NC}            Output in JSON format
    ${CYAN}-i, --interactive${NC}     Interactive mode
    ${CYAN}-h, --help${NC}            Show help message
    ${CYAN}--config <file>${NC}       Use custom config file
    ${CYAN}--profile <name>${NC}      Use configuration profile

${YELLOW}RUN OPTIONS:${NC}
    ${CYAN}--plan <path>${NC}         Plan directory to execute
    ${CYAN}--spec <path>${NC}         Spec file to execute
    ${CYAN}--agent <name>${NC}        Specific agent to run
    ${CYAN}--task <id>${NC}           Specific task ID
    ${CYAN}--autonomous${NC}          Enable autonomous mode
    ${CYAN}--max-iterations <n>${NC}  Maximum iterations
    ${CYAN}--parallel${NC}            Enable parallel execution
    ${CYAN}--dry-run${NC}             Show what would be done

${YELLOW}EXAMPLES:${NC}
    # Run a plan autonomously
    ralph-cli run --plan .plans/my-project --autonomous

    # Check system status
    ralph-cli status

    # View session logs
    ralph-cli logs --session abc123 --tail 50 --follow

    # Analyze a response
    ralph-cli analyze --file response.txt

    # Monitor autonomous execution
    ralph-cli monitor --session abc123

    # Intervene in execution
    ralph-cli intervene --session abc123 --action pause

    # Check system health
    ralph-cli health

    # Interactive mode
    ralph-cli -i run --plan .plans/my-project

${YELLOW}PROFILES:${NC}
    Ralph CLI supports configuration profiles for different environments:
    ${CYAN}default${NC}    Standard configuration
    ${CYAN}development${NC} Development settings (verbose, debug)
    ${CYAN}production${NC} Production settings (optimized, minimal output)
    ${CYAN}testing${NC}    Testing settings (dry-run, verbose)

    Use: ralph-cli --profile development run --plan .plans/my-project

${YELLOW}CONFIGURATION:${NC}
    Config files are loaded from:
    1. $CONFIG_DIR/ralph-cli.yaml
    2. ~/.ralph-cli.yaml
    3. .ralph-cli.yaml (project-specific)
    4. --config <file> (custom override)

${YELLOW}ENVIRONMENT VARIABLES:${NC}
    ${CYAN}RALPH_HOME${NC}           Ralph Runtime directory
    ${CYAN}RALPH_CONFIG_DIR${NC}     Configuration directory
    ${CYAN}RALPH_LOG_LEVEL${NC}      Log level (debug, info, warn, error)
    ${CYAN}RALPH_AUTO_CONFIRM${NC}   Skip confirmation prompts
    ${CYAN}RALPH_PROFILE${NC}        Configuration profile to use

${YELLOW}INTEGRATION:${NC}
    Ralph CLI integrates with:
    • ralph-runtime.sh (core execution)
    • circuit-breaker.sh (failure prevention)
    • analyze-response.sh (quality validation)
    • autonomous-run.sh (autonomous execution)
    • monitor.sh (real-time monitoring)
    • intervene.sh (human intervention)

For detailed help on specific commands:
    ralph-cli <command> --help

For more information, see: $PROJECT_ROOT/.blackbox4/docs/ralph-cli.md

EOF
}

################################################################################
# Completion Functions
################################################################################

generate_completion() {
    local shell="${1:-bash}"

    case $shell in
        bash)
            generate_bash_completion
            ;;
        zsh)
            generate_zsh_completion
            ;;
        fish)
            generate_fish_completion
            ;;
        *)
            print_error "Unsupported shell: $shell"
            print_info "Supported shells: bash, zsh, fish"
            return 1
            ;;
    esac
}

generate_bash_completion() {
    cat << 'EOF'
_ralph-cli_completion() {
    local cur prev words cword
    _init_completion || return

    local commands="run status config logs metrics session pause resume stop analyze test validate auto monitor intervene health doctor clean help version completion"

    case ${prev} in
        ralph-cli|--config)
            _filedir
            return 0
            ;;
        --plan|--spec|--file)
            _filedir -d
            return 0
            ;;
        --profile)
            COMPREPLY=($(compgen -W "default development production testing" -- "${cur}"))
            return 0
            ;;
        run|auto)
            COMPREPLY=($(compgen -W "--plan --spec --agent --task --autonomous --max-iterations --parallel --dry-run" -- "${cur}"))
            return 0
            ;;
        logs)
            COMPREPLY=($(compgen -W "--session --tail --follow" -- "${cur}"))
            return 0
            ;;
        analyze)
            COMPREPLY=($(compgen -W "--file --text --output --format" -- "${cur}"))
            return 0
            ;;
        monitor|session)
            COMPREPLY=($(compgen -W "--session --follow --metrics" -- "${cur}"))
            return 0
            ;;
        intervene)
            COMPREPLY=($(compgen -W "--session --action --input --reason" -- "${cur}"))
            return 0
            ;;
        *)
            ;;
    esac

    if [[ ${cur} == -* ]]; then
        COMPREPLY=($(compgen -W "-v -q -d -y -j -i -h --verbose --quiet --debug --yes --json --interactive --help --config --profile" -- "${cur}"))
    else
        COMPREPLY=($(compgen -W "${commands}" -- "${cur}"))
    fi
}

complete -F _ralph-cli_completion ralph-cli
EOF
}

generate_zsh_completion() {
    cat << 'EOF'
#compdef ralph-cli

_ralph-cli() {
    local -a commands
    commands=(
        'run:Execute plans or agents'
        'status:Show system status'
        'config:Manage configuration'
        'logs:View logs'
        'metrics:Show metrics'
        'session:Manage sessions'
        'pause:Pause a session'
        'resume:Resume a session'
        'stop:Stop a session'
        'analyze:Analyze responses'
        'test:Run tests'
        'validate:Validate configurations'
        'auto:Autonomous execution'
        'monitor:Monitor execution'
        'intervene:Intervene in execution'
        'health:Check system health'
        'doctor:Diagnose issues'
        'clean:Clean up resources'
        'help:Show help'
        'version:Show version'
        'completion:Generate shell completion'
    )

    local -a global_options
    global_options=(
        '--verbose[Enable verbose output]'
        '--quiet[Suppress output]'
        '--debug[Enable debug mode]'
        '--yes[Auto-confirm prompts]'
        '--json[Output in JSON format]'
        '--interactive[Interactive mode]'
        '--help[Show help]'
        '--config[Use custom config file]:file:_files'
        '--profile[Use configuration profile]:(default development production testing)'
    )

    case $words[2] in
        run)
            _arguments -s \
                '--plan[Plan directory]:directory:_directories' \
                '--spec[Spec file]:file:_files' \
                '--agent[Specific agent]:agent:' \
                '--task[Specific task ID]:task:' \
                '--autonomous[Enable autonomous mode]' \
                '--max-iterations[Maximum iterations]:number:' \
                '--parallel[Enable parallel execution]' \
                '--dry-run[Show what would be done]'
            ;;
        logs)
            _arguments -s \
                '--session[Session ID]:session:' \
                '--tail[Number of lines]:number:' \
                '--follow[Follow output]'
            ;;
        *)
            _arguments -s \
                {$global_options} \
                '*:: :->command_and_args' \
                && ret=0

            if (( CURRENT == 2 )); then
                _describe -t commands 'commands' commands
            fi
            ;;
    esac
}

_ralph-cli "$@"
EOF
}

generate_fish_completion() {
    cat << 'EOF'
complete -c ralph-cli -f

complete -c ralph-cli -n __fish_use_subcommand -a run -d 'Execute plans or agents'
complete -c ralph-cli -n __fish_use_subcommand -a status -d 'Show system status'
complete -c ralph-cli -n __fish_use_subcommand -a config -d 'Manage configuration'
complete -c ralph-cli -n __fish_use_subcommand -a logs -d 'View logs'
complete -c ralph-cli -n __fish_use_subcommand -a metrics -d 'Show metrics'
complete -c ralph-cli -n __fish_use_subcommand -a session -d 'Manage sessions'
complete -c ralph-cli -n __fish_use_subcommand -a pause -d 'Pause a session'
complete -c ralph-cli -n __fish_use_subcommand -a resume -d 'Resume a session'
complete -c ralph-cli -n __fish_use_subcommand -a stop -d 'Stop a session'
complete -c ralph-cli -n __fish_use_subcommand -a analyze -d 'Analyze responses'
complete -c ralph-cli -n __fish_use_subcommand -a test -d 'Run tests'
complete -c ralph-cli -n __fish_use_subcommand -a validate -d 'Validate configurations'
complete -c ralph-cli -n __fish_use_subcommand -a auto -d 'Autonomous execution'
complete -c ralph-cli -n __fish_use_subcommand -a monitor -d 'Monitor execution'
complete -c ralph-cli -n __fish_use_subcommand -a intervene -d 'Intervene in execution'
complete -c ralph-cli -n __fish_use_subcommand -a health -d 'Check system health'
complete -c ralph-cli -n __fish_use_subcommand -a doctor -d 'Diagnose issues'
complete -c ralph-cli -n __fish_use_subcommand -a clean -d 'Clean up resources'
complete -c ralph-cli -n __fish_use_subcommand -a help -d 'Show help'
complete -c ralph-cli -n __fish_use_subcommand -a version -d 'Show version'
complete -c ralph-cli -n __fish_use_subcommand -a completion -d 'Generate shell completion'

complete -c ralph-cli -l verbose -s v -d 'Enable verbose output'
complete -c ralph-cli -l quiet -s q -d 'Suppress output'
complete -c ralph-cli -l debug -s d -d 'Enable debug mode'
complete -c ralph-cli -l yes -s y -d 'Auto-confirm prompts'
complete -c ralph-cli -l json -s j -d 'Output in JSON format'
complete -c ralph-cli -l interactive -s i -d 'Interactive mode'
complete -c ralph-cli -l help -s h -d 'Show help'
complete -c ralph-cli -l config -d 'Use custom config file' -r
complete -c ralph-cli -l profile -d 'Use configuration profile' -xa 'default development production testing'
EOF
}

################################################################################
# Core Command Implementations
################################################################################

cmd_run() {
    shift  # Remove 'run' from args

    local plan_path=""
    local spec_path=""
    local agent_name=""
    local task_id=""
    local autonomous=false
    local max_iterations=""
    local parallel=false
    local dry_run=false

    # Parse run-specific options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --plan) plan_path="$2"; shift 2 ;;
            --spec) spec_path="$2"; shift 2 ;;
            --agent) agent_name="$2"; shift 2 ;;
            --task) task_id="$2"; shift 2 ;;
            --autonomous) autonomous=true; shift ;;
            --max-iterations) max_iterations="$2"; shift 2 ;;
            --parallel) parallel=true; shift ;;
            --dry-run) dry_run=true; shift ;;
            *) shift ;;
        esac
    done

    print_header "Ralph CLI - Run"

    # Validate input
    if [ -z "$plan_path" ] && [ -z "$spec_path" ]; then
        print_error "Please specify --plan or --spec"
        return 1
    fi

    # Build command
    local cmd="$SCRIPT_DIR/ralph-runtime.sh run"

    [ -n "$plan_path" ] && cmd="$cmd --plan $plan_path"
    [ -n "$spec_path" ] && cmd="$cmd --spec $spec_path"
    [ -n "$agent_name" ] && cmd="$cmd --agent $agent_name"
    [ -n "$task_id" ] && cmd="$cmd --task $task_id"
    [ "$autonomous" = true ] && cmd="$cmd --autonomous"
    [ -n "$max_iterations" ] && cmd="$cmd --max-iterations $max_iterations"
    [ "$parallel" = true ] && cmd="$cmd --parallel"
    [ "$dry_run" = true ] && cmd="$cmd --dry-run"
    [ "$VERBOSE" = true ] && cmd="$cmd --verbose"

    verbose_log "Executing: $cmd"

    # Execute
    eval $cmd
}

cmd_status() {
    print_header "Ralph CLI - Status"

    # Show Ralph Runtime status
    if [ -f "$SCRIPT_DIR/ralph-runtime.sh" ]; then
        echo ""
        "$SCRIPT_DIR/ralph-runtime.sh" status
    fi

    # Show circuit breaker status
    if [ -f "$SCRIPT_DIR/circuit-breaker.sh" ]; then
        echo ""
        "$SCRIPT_DIR/circuit-breaker.sh" status
    fi

    # Show session count
    if [ -d "$SESSIONS_DIR" ]; then
        local session_count=$(find "$SESSIONS_DIR" -name "metadata.json" -type f 2>/dev/null | wc -l)
        echo ""
        print_section "Sessions"
        echo "  Total Sessions: $session_count"
    fi
}

cmd_config() {
    shift  # Remove 'config' from args

    local action="${1:-show}"

    case $action in
        show)
            print_header "Ralph CLI - Configuration"
            print_section "Current Configuration"
            echo "  Config Directory: $CONFIG_DIR"
            echo "  Log Directory: $LOGS_DIR"
            echo "  Session Directory: $SESSIONS_DIR"
            echo "  State Directory: $STATE_DIR"
            echo ""
            echo "  Verbose: $VERBOSE"
            echo "  Debug: $DEBUG"
            echo "  JSON Output: $JSON_OUTPUT"
            echo "  Interactive: $INTERACTIVE"
            echo "  Auto Confirm: $AUTO_CONFIRM"

            if [ -f "$CONFIG_DIR/ralph-cli.yaml" ]; then
                echo ""
                print_section "Configuration File"
                cat "$CONFIG_DIR/ralph-cli.yaml" | sed 's/^/  /'
            fi
            ;;
        edit)
            local config_file="$CONFIG_DIR/ralph-cli.yaml"
            if [ ! -f "$config_file" ]; then
                mkdir -p "$CONFIG_DIR"
                cat > "$config_file" << EOF
# Ralph CLI Configuration

# General Settings
verbose: false
debug: false
quiet: false
json: false

# Execution Settings
autonomous:
  maxIterations: 100
  interventionEnabled: true

# Circuit Breaker
circuitBreaker:
  enabled: true
  failureThreshold: 5

# Logging
logging:
  level: info
  maxFileSize: 10485760
EOF
            fi

            ${EDITOR:-vi} "$config_file"
            print_success "Configuration file edited"
            ;;
        *)
            print_error "Unknown config action: $action"
            print_info "Available actions: show, edit"
            return 1
            ;;
    esac
}

cmd_logs() {
    shift  # Remove 'logs' from args

    local session_id=""
    local tail_lines=50
    local follow=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --session) session_id="$2"; shift 2 ;;
            --tail) tail_lines="$2"; shift 2 ;;
            --follow) follow=true; shift ;;
            *) shift ;;
        esac
    done

    if [ -n "$session_id" ]; then
        if [ -f "$SESSIONS_DIR/$session_id/session.log" ]; then
            print_header "Session Logs: $session_id"
            if [ "$follow" = true ]; then
                tail -f "$SESSIONS_DIR/$session_id/session.log"
            else
                tail -n "$tail_lines" "$SESSIONS_DIR/$session_id/session.log"
            fi
        else
            print_error "Session log not found: $session_id"
            return 1
        fi
    else
        print_header "Runtime Logs"
        if [ -f "$LOGS_DIR/ralph-runtime.log" ]; then
            if [ "$follow" = true ]; then
                tail -f "$LOGS_DIR/ralph-runtime.log"
            else
                tail -n "$tail_lines" "$LOGS_DIR/ralph-runtime.log"
            fi
        else
            print_warning "Runtime log not found"
        fi
    fi
}

cmd_metrics() {
    print_header "Ralph CLI - Metrics"

    # Show circuit breaker metrics
    if [ -f "$SCRIPT_DIR/circuit-breaker.sh" ]; then
        echo ""
        "$SCRIPT_DIR/circuit-breaker.sh" metrics
    fi

    # Show session metrics
    if [ -d "$SESSIONS_DIR" ]; then
        echo ""
        print_section "Session Metrics"

        local total_sessions=$(find "$SESSIONS_DIR" -name "metadata.json" -type f 2>/dev/null | wc -l)
        local running_sessions=$(grep -l '"status": "running"' "$SESSIONS"/*/metadata.json 2>/dev/null | wc -l)
        local completed_sessions=$(grep -l '"status": "completed"' "$SESSIONS"/*/metadata.json 2>/dev/null | wc -l)
        local failed_sessions=$(grep -l '"status": "failed"' "$SESSIONS"/*/metadata.json 2>/dev/null | wc -l)

        echo "  Total Sessions: $total_sessions"
        echo "  Running: $running_sessions"
        echo "  Completed: $completed_sessions"
        echo "  Failed: $failed_sessions"
    fi
}

cmd_session() {
    shift  # Remove 'session' from args

    local action="${1:-list}"
    local session_id=""

    case $action in
        list)
            print_header "Sessions"

            if [ -d "$SESSIONS_DIR" ]; then
                for session_file in $(find "$SESSIONS_DIR" -name "metadata.json" -type f 2>/dev/null | sort -r); do
                    local session_dir=$(dirname "$session_file")
                    local sid=$(basename "$session_dir")
                    local status=$(grep -o '"status": "[^"]*"' "$session_file" 2>/dev/null | cut -d'"' -f4)

                    echo "  • $sid - $(format_status "$status")"
                done
            else
                print_info "No sessions found"
            fi
            ;;
        info)
            session_id="$2"
            if [ -z "$session_id" ]; then
                print_error "Please specify session ID"
                return 1
            fi

            if [ -f "$SESSIONS_DIR/$session_id/metadata.json" ]; then
                print_header "Session Info: $session_id"
                cat "$SESSIONS_DIR/$session_id/metadata.json"
            else
                print_error "Session not found: $session_id"
                return 1
            fi
            ;;
        *)
            print_error "Unknown session action: $action"
            print_info "Available actions: list, info"
            return 1
            ;;
    esac
}

cmd_analyze() {
    shift  # Remove 'analyze' from args

    local file=""
    local text=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --file) file="$2"; shift 2 ;;
            --text) text="$2"; shift 2 ;;
            *) shift ;;
        esac
    done

    if [ -f "$SCRIPT_DIR/analyze-response.sh" ]; then
        local cmd="$SCRIPT_DIR/analyze-response.sh analyze"

        [ -n "$file" ] && cmd="$cmd --file $file"
        [ -n "$text" ] && cmd="$cmd --text '$text'"
        [ "$JSON_OUTPUT" = true ] && cmd="$cmd --json"

        eval $cmd
    else
        print_error "analyze-response.sh not found"
        return 1
    fi
}

cmd_auto() {
    shift  # Remove 'auto' from args

    if [ -f "$SCRIPT_DIR/autonomous-run.sh" ]; then
        "$SCRIPT_DIR/autonomous-run.sh" "$@"
    else
        print_error "autonomous-run.sh not found"
        return 1
    fi
}

cmd_monitor() {
    shift  # Remove 'monitor' from args

    if [ -f "$SCRIPT_DIR/monitor.sh" ]; then
        "$SCRIPT_DIR/monitor.sh" "$@"
    else
        print_error "monitor.sh not found"
        return 1
    fi
}

cmd_intervene() {
    shift  # Remove 'intervene' from args

    if [ -f "$SCRIPT_DIR/intervene.sh" ]; then
        "$SCRIPT_DIR/intervene.sh" "$@"
    else
        print_error "intervene.sh not found"
        return 1
    fi
}

cmd_health() {
    print_header "Ralph CLI - Health Check"

    local all_healthy=true

    # Check required scripts
    print_section "Script Health"

    local scripts=(
        "ralph-runtime.sh"
        "circuit-breaker.sh"
        "analyze-response.sh"
        "autonomous-run.sh"
    )

    for script in "${scripts[@]}"; do
        if [ -f "$SCRIPT_DIR/$script" ]; then
            print_success "$script"
        else
            print_error "$script not found"
            all_healthy=false
        fi
    done

    # Check directories
    echo ""
    print_section "Directory Health"

    local dirs=("$LOGS_DIR" "$SESSIONS_DIR" "$CONFIG_DIR" "$STATE_DIR")

    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_success "$dir"
        else
            print_warning "$dir not found (will be created)"
        fi
    done

    # Check circuit breaker
    echo ""
    print_section "Circuit Breaker Health"

    if [ -f "$SCRIPT_DIR/circuit-breaker.sh" ]; then
        "$SCRIPT_DIR/circuit-breaker.sh" status --quiet 2>/dev/null || print_warning "Circuit breaker check failed"
    fi

    # Overall status
    echo ""
    if [ "$all_healthy" = true ]; then
        print_success "All systems healthy"
        return 0
    else
        print_error "Some systems unhealthy"
        return 1
    fi
}

cmd_doctor() {
    print_header "Ralph CLI - Doctor"

    print_section "Diagnosing Issues"

    # Check for common issues
    local issues_found=0

    # Check permissions
    if [ ! -w "$LOGS_DIR" ] 2>/dev/null; then
        print_warning "Cannot write to logs directory"
        issues_found=$((issues_found + 1))
    fi

    # Check disk space
    local disk_usage=$(df "$PROJECT_ROOT" | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $disk_usage -gt 90 ]; then
        print_warning "Disk usage high: $disk_usage%"
        issues_found=$((issues_found + 1))
    fi

    # Check for stale sessions
    if [ -d "$SESSIONS_DIR" ]; then
        local stale_sessions=$(find "$SESSIONS_DIR" -name "metadata.json" -mtime +7 -type f 2>/dev/null | wc -l)
        if [ $stale_sessions -gt 0 ]; then
            print_warning "Found $stale_sessions stale sessions (older than 7 days)"
            issues_found=$((issues_found + 1))
        fi
    fi

    if [ $issues_found -eq 0 ]; then
        print_success "No issues found"
    else
        print_warning "Found $issues_found potential issues"
    fi
}

cmd_clean() {
    print_header "Ralph CLI - Clean"

    # Confirm cleanup
    if [ "$AUTO_CONFIRM" != true ]; then
        echo -n "Clean up old sessions and logs? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_info "Clean cancelled"
            return 0
        fi
    fi

    # Clean old sessions (older than 30 days)
    if [ -d "$SESSIONS_DIR" ]; then
        print_section "Cleaning Old Sessions"
        local cleaned=$(find "$SESSIONS_DIR" -type d -mtime +30 -exec rm -rf {} + 2>/dev/null || echo "0")
        print_success "Cleaned old sessions"
    fi

    # Rotate logs if too large
    if [ -f "$LOGS_DIR/ralph-runtime.log" ]; then
        local log_size=$(stat -f%z "$LOGS_DIR/ralph-runtime.log" 2>/dev/null || stat -c%s "$LOGS_DIR/ralph-runtime.log" 2>/dev/null || echo "0")
        if [ $log_size -gt 10485760 ]; then
            print_section "Rotating Large Log File"
            mv "$LOGS_DIR/ralph-runtime.log" "$LOGS_DIR/ralph-runtime.log.old"
            print_success "Log rotated"
        fi
    fi

    print_success "Cleanup complete"
}

format_status() {
    local status="$1"

    case $status in
        running)
            echo -e "${GREEN}$status${NC}"
            ;;
        completed)
            echo -e "${GREEN}$status${NC}"
            ;;
        failed)
            echo -e "${RED}$status${NC}"
            ;;
        paused)
            echo -e "${YELLOW}$status${NC}"
            ;;
        *)
            echo "$status"
            ;;
    esac
}

################################################################################
# Main Function
################################################################################

main() {
    # Create necessary directories
    mkdir -p "$LOGS_DIR" "$SESSIONS_DIR" "$CONFIG_DIR" "$STATE_DIR"

    # Load profile if specified
    local profile=""
    local config_file=""

    # Parse global options first
    while [[ $# -gt 0 ]]; do
        case $1 in
            --profile)
                profile="$2"
                shift 2
                ;;
            --config)
                config_file="$2"
                shift 2
                ;;
            *)
                break
                ;;
        esac
    done

    # Load profile configuration
    if [ -n "$profile" ]; then
        case $profile in
            development)
                VERBOSE=true
                DEBUG=true
                ;;
            production)
                QUIET=true
                ;;
            testing)
                VERBOSE=true
                ;;
        esac
    fi

    # Check for command
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    local command="$1"
    shift

    # Parse remaining options
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--verbose) VERBOSE=true; shift ;;
            -q|--quiet) QUIET=true; shift ;;
            -d|--debug) DEBUG=true; shift ;;
            -y|--yes) AUTO_CONFIRM=true; shift ;;
            -j|--json) JSON_OUTPUT=true; shift ;;
            -i|--interactive) INTERACTIVE=true; shift ;;
            -h|--help) show_help; exit 0 ;;
            *) break ;;
        esac
    done

    # Execute command
    case $command in
        run) cmd_run "$@" ;;
        status) cmd_status ;;
        config) cmd_config "$@" ;;
        logs) cmd_logs "$@" ;;
        metrics) cmd_metrics ;;
        session) cmd_session "$@" ;;
        pause) "$SCRIPT_DIR/ralph-runtime.sh" pause "$@" ;;
        resume) "$SCRIPT_DIR/ralph-runtime.sh" resume "$@" ;;
        stop) "$SCRIPT_DIR/ralph-runtime.sh" stop "$@" ;;
        analyze) cmd_analyze "$@" ;;
        test) print_info "Test command - feature under development" ;;
        validate) print_info "Validate command - feature under development" ;;
        auto) cmd_auto "$@" ;;
        monitor) cmd_monitor "$@" ;;
        intervene) cmd_intervene "$@" ;;
        health) cmd_health ;;
        doctor) cmd_doctor ;;
        clean) cmd_clean ;;
        help) show_help ;;
        version) show_version ;;
        completion) generate_completion "${1:-bash}" ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main
main "$@"
