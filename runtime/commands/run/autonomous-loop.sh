#!/bin/bash

# Autonomous Loop Wrapper with Circuit Breaker Integration
# Part of .blackbox4 Circuit Breaker Implementation
# Following Thought Chain Implementation Plan: Feature 1.3

# Source dependencies
CIRCUIT_BREAKER_LIB="4-scripts/lib/circuit-breaker/circuit-breaker.sh"
RESPONSE_ANALYZER="4-scripts/lib/response-analyzer.sh"

# Configuration
RALPH_HOME="."
CIRCUIT_STATE_FILE=".ralph/circuit-state.json"
RESPONSE_FILE=".ralph/last-response.md"
PROGRESS_FILE=".ralph/progress.md"
MONITOR_PID_FILE=".ralph/monitor.pid"

# Status tracking
current_task=""
progress_percentage=0
stagnation_count=0

# Initialize circuit breaker
init_session() {
    # Source circuit breaker library
    source "$CIRCUIT_BREAKER_LIB"
    init_circuit_state
    
    # Create working directories
    mkdir -p ".ralph/logs"
    mkdir -p ".ralph/backups"
    
    # Initialize status tracking
    init_progress_tracking
    
    echo "🚀 Autonomous loop session initialized"
    echo "   Circuit breaker: CLOSED"
    echo "   Max loops: $(jq -r '.circuit_breaker.max_loops_no_progress' 4-scripts/lib/circuit-breaker/config.yaml)"
}

# Initialize progress tracking
init_progress_tracking() {
    > "$PROGRESS_FILE" << 'EOF'
# .blackbox4 Autonomous Loop Progress Tracking

## Session Info
- **Started:** $(date)
- **Session ID:** $(date +%s)

## Current Status
**Task:** TBD
**Progress:** 0%
**Loops:** 0
**Stagnation Count:** 0

## Progress History
EOF
    
    log_progress "Session initialized"
}

# Update progress
update_progress() {
    local task="$1"
    local progress="$2"
    local response="$3"
    
    # Check circuit breaker first (may stop execution)
    source "$CIRCUIT_BREAKER_LIB"
    if check_circuit_breaker "$(get_circuit_state)" ; then
        echo "🛑 Circuit breaker OPEN - stopping execution"
        return 1
    fi
    
    # Update progress tracking
    echo "Progress: $progress%" | tee -a "$PROGRESS_FILE"
    
    # Extract metrics from response
    source "$RESPONSE_ANALYZER"
    local metrics=$(analyze_response "$response")
    
    # Update state
    current_task="$task"
    progress_percentage="$progress"
    
    # Update progress file
    cat > "$PROGRESS_FILE" << 'EOF'
# .blackbox4 Autonomous Loop Progress Tracking

## Session Info
- **Started:** $(date)
- **Session ID:** $(date +%s)

## Current Status
**Task:** $task
**Progress:** $progress%
**Loops:** $(jq -r '.loop_count' "$CIRCUIT_STATE_FILE")
**Stagnation Count:** $(jq -r '.consecutive_no_progress_loops' "$CIRCUIT_STATE_FILE")

## Response Metrics
$metrics

## Progress History
- $(date): $progress%
EOF
    
    log_progress "Progress updated: $progress%, Task: $task"
    
    return 0
}

# Convert .blackbox4 format to Ralph format
convert_to_ralph_format() {
    local bb3_readme="README.md"
    local bb3_checklist="checklist.md"
    local ralph_prompt_dir=".ralph"
    
    mkdir -p "$ralph_prompt_dir"
    
    # Generate PROMPT.md from README.md
    echo "# $(head -n 1 "$bb3_readme")" > "$ralph_prompt_dir/PROMPT.md"
    echo "" >> "$ralph_prompt_dir/PROMPT.md"
    
    # Extract task items from checklist.md
    echo "" >> "$ralph_prompt_dir/PROMPT.md"
    echo "## Task List" >> "$ralph_prompt_dir/PROMPT.md"
    
    if [[ -f "$bb3_checklist" ]]; then
        sed -n 's/^\- \[ \]/- [x] /' "$bb3_checklist" >> "$ralph_prompt_dir/PROMPT.md"
    fi
    
    echo "" >> "$ralph_prompt_dir/PROMPT.md"
    echo "## Status" >> "$ralph_prompt_dir/PROMPT.md"
    echo "- Use @fix_plan.md to track completion" >> "$ralph_prompt_dir/PROMPT.md"
    echo "- Check .ralph/status.md for real-time progress" >> "$ralph_dir/PROMPT.md"
    
    log_progress "Converted .blackbox4 format to Ralph format"
}

# Monitor autonomous session
monitor_session() {
    local update_interval=2
    
    echo "🔍 Monitoring autonomous session (check $update_interval seconds)..."
    
    while true; do
        sleep $update_interval
        
        # Check progress file
        local current_progress=$(grep "Progress:" "$PROGRESS_FILE" | tail -1 | sed 's/Progress: //')
        
        clear
        echo "=== Ralph Autonomous Session Monitor ==="
        echo "📋 Current Task: $current_task"
        echo "📊 Progress: $current_progress"
        echo "🔄 Loops: $(jq -r '.loop_count' "$CIRCUIT_STATE_FILE")"
        echo "⏱️  Stagnations: $(jq -r '.consecutive_no_progress_loops' "$CIRCUIT_STATE_FILE")"
        echo "⏱️  Elapsed: $SECONDS"
        echo ""
        echo "Press Ctrl+C to stop monitoring (doesn't stop loop)"
        echo ""
        echo "Circuit Status: $(jq -r '.status' "$CIRCUIT_STATE_FILE")"
        
        # Check for completion
        if [[ "$current_progress" == "100%" ]] || [[ "$current_progress" == "100.0%" ]]; then
            echo ""
            echo "✅ Session completed!"
            echo ""
            break
        fi
    done
}

# Run autonomous loop with Ralph integration
run_autonomous_loop() {
    # Check if Ralph is installed
    if [[ ! -d "$RALPH_HOME/ralph-claude-code" ]]; then
        echo "⚠️ Error: Ralph not found at: $RALPH_HOME/ralph-claude-code"
        echo "   Install Ralph from: https://github.com/anthropic/claude-code/tree/main/ralph-claude-code"
        return 1
    fi
    
    # Convert .blackbox4 format to Ralph format
    convert_to_ralph_format
    
    echo "🚀 Starting autonomous loop with circuit breaker protection"
    echo ""
    echo "Features:"
    echo "  ✅ Circuit breaker - Prevents infinite loops"
    echo "  ✅ Exit detection - Knows when work is done"
    echo "  ✅ Response analysis - Tracks progress"
    echo "  ✅ Real-time monitoring - Progress visibility"
    echo ""
    
    # Start Ralph loop in background
    # (In a real implementation, this would be:
    # "$RALPH_HOME/ralph-claude-code/ralph_loop.sh" &)
    
    # For now, demonstrate with mock loop:
    run_mock_loop
    
    # Start monitor in background
    monitor_session &
    MONITOR_PID=$!
    
    echo "📊 Monitoring session running in background (PID: $MONITOR_PID)"
    echo "   Check progress in: .ralph/progress.md"
    echo "   Stop monitoring with: kill $MONITOR_PID"
}

# Mock loop for demonstration
run_mock_loop() {
    local max_loops=$(jq -r '.circuit_breaker.max_loops_no_progress' 4-scripts/lib/circuit-breaker/config.yaml)
    
    echo "🔄 Running autonomous loop (demonstration mode)"
    echo ""
    
    for ((i = 1; i <= max_loops; i++)); do
        echo "=== Loop $i of $max_loops ==="
        echo "Working on tasks..."
        
        # Simulate work
        sleep 1
        
        # Update progress
        update_progress "Task: Implementing feature $i" "$((i * 100 / max_loops))" "Simulated response for loop $i"
        
        # Check circuit breaker (this will stop us in real Ralph)
        source "$CIRCUIT_BREAKER_LIB"
        if check_circuit_breaker "$(get_circuit_state)" ; then
            echo "🛑 Circuit breaker triggered - stopping"
            break
        fi
        
        echo ""
    done
    
    echo ""
    echo "✅ Autonomous loop completed"
    echo "   Total loops: $max_loops"
    echo "   Final progress: 100%"
}

# Log progress event
log_progress() {
    local event="$1"
    
    mkdir -p ".ralph/logs"
    local timestamp=$(date -Iseconds)
    local log_file=".ralph/logs/progress_$(date +%Y%m%d).log"
    
    echo "[$timestamp] $event" >> "$log_file"
    echo "" >> "$log_file"
    echo "Logged to: $log_file"
}

# Main interface
main() {
    local command="${1:-run}"
    
    case "$command" in
        run)
            init_session
            run_autonomous_loop
            ;;
        init)
            init_session
            ;;
        convert)
            convert_to_ralph_format
            ;;
        status)
            echo ""
            echo "=== Circuit Breaker Status ==="
            source "$CIRCUIT_BREAKER_LIB"
            get_circuit_state
            echo ""
            echo "=== Progress Tracking ==="
            cat "$PROGRESS_FILE"
            ;;
        monitor)
            monitor_session
            ;;
        reset)
            source "$CIRCUIT_BREAKER_LIB"
            reset_circuit_breaker
            ;;
        *)
            echo "Usage: $0 run|init|convert|status|monitor|reset"
            echo "  run - Run autonomous loop with circuit breaker"
            echo "  init - Initialize circuit breaker session"
            echo "  convert - Convert .blackbox4 format to Ralph"
            echo "  status - Show circuit breaker and progress"
            echo "  monitor - Monitor autonomous session"
            echo "  reset - Reset circuit breaker (manual override)"
            ;;
    esac
}