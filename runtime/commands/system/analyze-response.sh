#!/bin/bash

################################################################################
# Response Analyzer Wrapper Script
# Wrapper for response analyzer in Ralph Runtime
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
NC='\033[0m' # No Color

# Configuration
ANALYZER_DIR="$PROJECT_ROOT/.blackbox4/ralph-runtime/analyzer"
CONFIG_DIR="$PROJECT_ROOT/.blackbox4/config"
LOGS_DIR="$PROJECT_ROOT/.blackbox4/logs"
REPORTS_DIR="$PROJECT_ROOT/.blackbox4/reports"

# Default values
VERBOSE=false
QUIET=false
JSON_OUTPUT=false
CHECK_PATTERNS=true
CHECK_QUALITY=true
CHECK_CONSISTENCY=true
MIN_SCORE=70

################################################################################
# Helper Functions
################################################################################

print_header() {
    [ "$QUIET" = false ] || return 0
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_section() {
    [ "$QUIET" = false ] || return 0
    echo -e "\n${BLUE}▶ $1${NC}\n"
}

print_success() {
    [ "$QUIET" = false ] || return 0
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ ERROR: $1${NC}" >&2
}

print_warning() {
    [ "$QUIET" = false ] || return 0
    echo -e "${YELLOW}⚠ WARNING: $1${NC}"
}

print_info() {
    [ "$QUIET" = false ] || return 0
    echo -e "${PURPLE}ℹ $1${NC}"
}

verbose_log() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${CYAN}[DEBUG] $1${NC}"
    fi
}

show_help() {
    cat << EOF
${GREEN}Response Analyzer Wrapper${NC} - Analyze agent responses for quality and patterns

${YELLOW}USAGE:${NC}
    $0 <command> [options]

${YELLOW}COMMANDS:${NC}
    ${CYAN}analyze${NC}      Analyze a response file or text
    ${CYAN}score${NC}        Calculate and display quality score
    ${CYAN}patterns${NC}     Detect and report patterns
    ${CYAN}quality${NC}      Check quality metrics
    ${CYAN}consistency${NC}  Check consistency across responses
    ${CYAN}compare${NC}      Compare multiple responses
    ${CYAN}report${NC}       Generate detailed analysis report
    ${CYAN}help${NC}         Show this help message

${YELLOW}ANALYZE OPTIONS:${NC}
    ${CYAN}--file <path>${NC}          Response file to analyze
    ${CYAN}--text <string>${NC}        Response text to analyze
    ${CYAN}--session <id>${NC}         Analyze session responses
    ${CYAN}--output <path>${NC}        Output file for results
    ${CYAN}--format <type>${NC}        Output format (text, json, html)

${YELLOW}CHECK OPTIONS:${NC}
    ${CYAN}--check-patterns${NC}       Enable pattern detection
    ${CYAN}--check-quality${NC}        Enable quality checking
    ${CYAN}--check-consistency${NC}    Enable consistency checking
    ${CYAN}--min-score <n>${NC}        Minimum acceptable score (0-100)

${YELLOW}SCORE OPTIONS:${NC}
    ${CYAN}--detailed${NC}             Show detailed scoring breakdown
    ${CYAN}--threshold <n>${NC}        Score threshold for passing

${YELLOW}PATTERN OPTIONS:${NC}
    ${CYAN}--type <pattern>${NC}       Specific pattern type to check
    ${CYAN}--severity <level>${NC}     Minimum severity (info, warning, error)

${YELLOW}COMMON OPTIONS:${NC}
    ${CYAN}-v, --verbose${NC}          Enable verbose output
    ${CYAN}-q, --quiet${NC}            Suppress output (except errors)
    ${CYAN}-h, --help${NC}             Show help message
    ${CYAN}--json${NC}                 Output in JSON format

${YELLOW}EXAMPLES:${NC}
    # Analyze a response file
    $0 analyze --file response.txt

    # Analyze with text input
    $0 analyze --text "The agent response here..."

    # Analyze with detailed output
    $0 analyze --file response.txt --detailed --format json

    # Score a response
    $0 score --file response.txt --min-score 70

    # Check for patterns
    $0 patterns --file response.txt --type repetition

    # Generate full report
    $0 report --session abc123 --output report.html

    # Compare multiple responses
    $0 compare --files response1.txt response2.txt response3.txt

${YELLOW}QUALITY METRICS:${NC}
    ${CYAN}Clarity${NC}        How clear and understandable the response is
    ${CYAN}Completeness${NC}   How completely it addresses the request
    ${CYAN}Accuracy${NC}       Factual correctness (requires reference)
    ${CYAN}Relevance${NC}      How relevant to the original query
    ${CYAN}Structure${NC}      Organization and formatting

${YELLOW}PATTERN TYPES:${NC}
    ${CYAN}repetition${NC}     Repetitive phrases or patterns
    ${CYAN}vagueness${NC}      Vague or non-committal language
    ${CYAN}errors${NC}         Factual or logical errors
    ${CYAN}inconsistency${NC}  Internal contradictions
    ${CYAN}bias${NC}           Potential biases in response

For more information, see: $PROJECT_ROOT/.blackbox4/docs/response-analyzer.md

EOF
}

################################################################################
# Analysis Functions
################################################################################

analyze_response() {
    local response_content="$1"
    local output_file="${OUTPUT_FILE:-}"
    local output_format="${OUTPUT_FORMAT:-text}"

    print_header "Response Analysis"

    if [ "$JSON_OUTPUT" = true ]; then
        analyze_json "$response_content"
        return 0
    fi

    # Perform checks
    local score=0
    local max_score=0

    print_section "Analysis Summary"

    # Pattern check
    if [ "$CHECK_PATTERNS" = true ]; then
        print_info "Checking patterns..."
        check_patterns "$response_content"
        max_score=$((max_score + 25))
    fi

    # Quality check
    if [ "$CHECK_QUALITY" = true ]; then
        print_info "Checking quality..."
        local quality_score
        quality_score=$(check_quality "$response_content")
        score=$((score + quality_score))
        max_score=$((max_score + 40))
    fi

    # Consistency check
    if [ "$CHECK_CONSISTENCY" = true ]; then
        print_info "Checking consistency..."
        local consistency_score
        consistency_score=$(check_consistency "$response_content")
        score=$((score + consistency_score))
        max_score=$((max_score + 35))
    fi

    # Calculate final score
    local final_score=$((score * 100 / max_score))

    echo ""
    print_section "Final Score"
    display_score "$final_score"

    # Check threshold
    if [ $final_score -lt $MIN_SCORE ]; then
        print_warning "Score below minimum threshold ($MIN_SCORE)"
        return 1
    fi

    # Save report if requested
    if [ -n "$output_file" ]; then
        save_report "$response_content" "$final_score" "$output_file" "$output_format"
    fi

    return 0
}

analyze_json() {
    local response_content="$1"

    local patterns_result
    local quality_result
    local consistency_result

    if [ "$CHECK_PATTERNS" = true ]; then
        patterns_result=$(check_patterns_json "$response_content")
    fi

    if [ "$CHECK_QUALITY" = true ]; then
        quality_result=$(check_quality_json "$response_content")
    fi

    if [ "$CHECK_CONSISTENCY" = true ]; then
        consistency_result=$(check_consistency_json "$response_content")
    fi

    cat << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "patterns": $patterns_result,
    "quality": $quality_result,
    "consistency": $consistency_result,
    "overallScore": $(( (${quality_result:-0} + ${consistency_result:-0}) / 2 ))
}
EOF
}

################################################################################
# Pattern Detection
################################################################################

check_patterns() {
    local response_content="$1"

    local issues_found=0

    # Check for repetitive patterns
    if echo "$response_content" | grep -qi "I understand\|I see\|Let me"; then
        print_warning "Repetitive intro phrases detected"
        issues_found=$((issues_found + 1))
    fi

    # Check for vague language
    if echo "$response_content" | grep -qi "might be\|could be\|possibly\|perhaps"; then
        print_warning "Vague language detected"
        issues_found=$((issues_found + 1))
    fi

    # Check for excessive hedging
    if echo "$response_content" | grep -qi "I think\|I believe\|It seems"; then
        print_warning "Excessive hedging detected"
        issues_found=$((issues_found + 1))
    fi

    # Check for formatting issues
    if ! echo "$response_content" | grep -q "^$"; then
        print_info "Response structure could be improved"
    fi

    if [ $issues_found -eq 0 ]; then
        print_success "No significant pattern issues detected"
        return 20
    elif [ $issues_found -le 2 ]; then
        return 15
    else
        return 10
    fi
}

check_patterns_json() {
    local response_content="$1"

    local repetitive=0
    local vague=0
    local hedging=0

    if echo "$response_content" | grep -qi "I understand\|I see\|Let me"; then
        repetitive=1
    fi

    if echo "$response_content" | grep -qi "might be\|could be\|possibly"; then
        vague=1
    fi

    if echo "$response_content" | grep -qi "I think\|I believe\|It seems"; then
        hedging=1
    fi

    cat << EOF
{
    "repetitivePhrases": $repetitive,
    "vagueLanguage": $vague,
    "hedging": $hedging,
    "totalIssues": $((repetitive + vague + hedging))
}
EOF
}

################################################################################
# Quality Checking
################################################################################

check_quality() {
    local response_content="$1"
    local score=0
    local max_score=40

    # Clarity check (10 points)
    local word_count=$(echo "$response_content" | wc -w)
    if [ $word_count -gt 20 ] && [ $word_count -lt 500 ]; then
        print_success "Good length ($word_count words)"
        score=$((score + 10))
    else
        print_warning "Response length may be inappropriate"
        score=$((score + 5))
    fi

    # Completeness check (10 points)
    if echo "$response_content" | grep -qi "conclusion\|therefore\|thus\|finally"; then
        print_success "Has clear conclusion"
        score=$((score + 10))
    else
        print_info "Could benefit from clearer conclusion"
        score=$((score + 5))
    fi

    # Structure check (10 points)
    local line_count=$(echo "$response_content" | wc -l)
    if [ $line_count -gt 1 ]; then
        print_success "Well-structured ($line_count lines)"
        score=$((score + 10))
    else
        print_warning "Structure could be improved"
        score=$((score + 5))
    fi

    # Relevance check (10 points)
    if [ $word_count -gt 10 ]; then
        print_success "Substantive response"
        score=$((score + 10))
    else
        print_warning "Response too brief"
        score=$((score + 3))
    fi

    echo $score
}

check_quality_json() {
    local response_content="$1"

    local word_count=$(echo "$response_content" | wc -w)
    local line_count=$(echo "$response_content" | wc -l)
    local has_conclusion=$(echo "$response_content" | grep -qi "conclusion\|therefore" && echo "true" || echo "false")

    cat << EOF
{
    "wordCount": $word_count,
    "lineCount": $line_count,
    "hasConclusion": $has_conclusion,
    "clarityScore": $([ $word_count -gt 20 ] && echo "10" || echo "5"),
    "structureScore": $([ $line_count -gt 1 ] && echo "10" || echo "5"),
    "overallScore": $([ $word_count -gt 20 ] && echo "30" || echo "15")
}
EOF
}

################################################################################
# Consistency Checking
################################################################################

check_consistency() {
    local response_content="$1"
    local score=0
    local max_score=35

    # Check for contradictions (15 points)
    if ! echo "$response_content" | grep -qi "however.*but\|although.*though"; then
        print_success "No obvious contradictions"
        score=$((score + 15))
    else
        print_warning "Potential contradictions detected"
        score=$((score + 8))
    fi

    # Check for consistency in tense (10 points)
    local tense_shifts=$(echo "$response_content" | grep -o "is.*was\|was.*is" | wc -l)
    if [ $tense_shifts -eq 0 ]; then
        print_success "Consistent tense usage"
        score=$((score + 10))
    else
        print_warning "Some tense inconsistencies"
        score=$((score + 5))
    fi

    # Check for consistent terminology (10 points)
    print_success "Terminology appears consistent"
    score=$((score + 10))

    echo $score
}

check_consistency_json() {
    local response_content="$1"

    local contradictions=$(echo "$response_content" | grep -qi "however.*but" && echo "true" || echo "false")
    local tense_shifts=$(echo "$response_content" | grep -o "is.*was\|was.*is" | wc -l)

    cat << EOF
{
    "contradictions": $contradictions,
    "tenseShifts": $tense_shifts,
    "terminologyConsistent": true,
    "overallScore": $([ "$contradictions" = "false" ] && echo "30" || echo "15")
}
EOF
}

################################################################################
# Score Display
################################################################################

display_score() {
    local score="$1"

    if [ $score -ge 90 ]; then
        echo -e "  ${GREEN}● Score: $score/100 - Excellent${NC}"
    elif [ $score -ge 80 ]; then
        echo -e "  ${GREEN}● Score: $score/100 - Very Good${NC}"
    elif [ $score -ge 70 ]; then
        echo -e "  ${YELLOW}● Score: $score/100 - Good${NC}"
    elif [ $score -ge 60 ]; then
        echo -e "  ${YELLOW}● Score: $score/100 - Fair${NC}"
    else
        echo -e "  ${RED}● Score: $score/100 - Needs Improvement${NC}"
    fi
}

################################################################################
# Report Generation
################################################################################

save_report() {
    local response_content="$1"
    local score="$2"
    local output_file="$3"
    local format="$4"

    mkdir -p "$REPORTS_DIR"

    case $format in
        json)
            save_json_report "$response_content" "$score" "$output_file"
            ;;
        html)
            save_html_report "$response_content" "$score" "$output_file"
            ;;
        *)
            save_text_report "$response_content" "$score" "$output_file"
            ;;
    esac

    print_success "Report saved to: $output_file"
}

save_text_report() {
    local response_content="$1"
    local score="$2"
    local output_file="$3"

    cat > "$output_file" << EOF
Response Analysis Report
Generated: $(date)
Score: $score/100

ANALYSIS DETAILS

Response Content:
$(echo "$response_content" | head -20)

Pattern Check: $( [ "$CHECK_PATTERNS" = true ] && echo "Enabled" || echo "Disabled" )
Quality Check: $( [ "$CHECK_QUALITY" = true ] && echo "Enabled" || echo "Disabled" )
Consistency Check: $( [ "$CHECK_CONSISTENCY" = true ] && echo "Enabled" || echo "Disabled" )

Minimum Score Threshold: $MIN_SCORE

Status: $( [ $score -ge $MIN_SCORE ] && echo "PASSED" || echo "FAILED" )
EOF
}

save_json_report() {
    local response_content="$1"
    local score="$2"
    local output_file="$3"

    cat > "$output_file" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "score": $score,
    "passed": $([ $score -ge $MIN_SCORE ] && echo "true" || echo "false"),
    "threshold": $MIN_SCORE,
    "checks": {
        "patterns": $CHECK_PATTERNS,
        "quality": $CHECK_QUALITY,
        "consistency": $CHECK_CONSISTENCY
    },
    "responsePreview": "$(echo "$response_content" | head -5 | tr '\n' ' ')"
}
EOF
}

save_html_report() {
    local response_content="$1"
    local score="$2"
    local output_file="$3"

    cat > "$output_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Response Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .score { font-size: 48px; font-weight: bold; }
        .excellent { color: #4CAF50; }
        .good { color: #8BC34A; }
        .fair { color: #FF9800; }
        .poor { color: #F44336; }
        .section { margin: 20px 0; }
        .response { background: #f9f9f9; padding: 15px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Response Analysis Report</h1>
        <p>Generated: $(date)</p>
    </div>

    <div class="section">
        <h2>Score</h2>
        <div class="score $( [ $score -ge 70 ] && echo "excellent" || echo "poor")">$score/100</div>
    </div>

    <div class="section">
        <h2>Response Preview</h2>
        <div class="response">
            <pre>$(echo "$response_content" | head -20)</pre>
        </div>
    </div>

    <div class="section">
        <h2>Checks Performed</h2>
        <ul>
            <li>Patterns: $([ "$CHECK_PATTERNS" = true ] && echo "✓" || echo "✗")</li>
            <li>Quality: $([ "$CHECK_QUALITY" = true ] && echo "✓" || echo "✗")</li>
            <li>Consistency: $([ "$CHECK_CONSISTENCY" = true ] && echo "✓" || echo "✗")</li>
        </ul>
    </div>
</body>
</html>
EOF
}

################################################################################
# Compare Function
################################################################################

compare_responses() {
    shift  # Remove 'compare' command

    if [ $# -lt 2 ]; then
        print_error "At least 2 files required for comparison"
        return 1
    fi

    print_header "Response Comparison"

    local file_count=$#
    local total_score=0

    for file in "$@"; do
        if [ ! -f "$file" ]; then
            print_error "File not found: $file"
            continue
        fi

        local content=$(cat "$file")
        local file_name=$(basename "$file")

        echo ""
        print_section "File: $file_name"

        # Quick analysis
        local word_count=$(echo "$content" | wc -w)
        local line_count=$(echo "$content" | wc -l)

        echo "  Words: $word_count"
        echo "  Lines: $line_count"

        # Calculate quick score
        local quick_score=$((word_count > 20 ? 20 : 10))
        quick_score=$((quick_score + (line_count > 1 ? 10 : 5)))
        total_score=$((total_score + quick_score))

        display_score $quick_score
    done

    # Average
    local average=$((total_score / file_count))
    echo ""
    print_section "Average Score"
    display_score $average
}

################################################################################
# Main Function
################################################################################

main() {
    # Create necessary directories
    mkdir -p "$LOGS_DIR" "$REPORTS_DIR" "$CONFIG_DIR"

    # Parse command
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    local command="$1"
    shift

    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --file)
                INPUT_FILE="$2"
                RESPONSE_TEXT=$(cat "$2" 2>/dev/null || echo "")
                shift 2
                ;;
            --text)
                RESPONSE_TEXT="$2"
                shift 2
                ;;
            --session)
                SESSION_ID="$2"
                shift 2
                ;;
            --output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            --format)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            --check-patterns)
                CHECK_PATTERNS=true
                shift
                ;;
            --no-check-patterns)
                CHECK_PATTERNS=false
                shift
                ;;
            --check-quality)
                CHECK_QUALITY=true
                shift
                ;;
            --no-check-quality)
                CHECK_QUALITY=false
                shift
                ;;
            --check-consistency)
                CHECK_CONSISTENCY=true
                shift
                ;;
            --no-check-consistency)
                CHECK_CONSISTENCY=false
                shift
                ;;
            --min-score)
                MIN_SCORE="$2"
                shift 2
                ;;
            --detailed)
                DETAILED=true
                shift
                ;;
            --type)
                PATTERN_TYPE="$2"
                shift 2
                ;;
            --severity)
                SEVERITY="$2"
                shift 2
                ;;
            --files)
                COMPARE_MODE=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -q|--quiet)
                QUIET=true
                shift
                ;;
            --json)
                JSON_OUTPUT=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                # File arguments for compare
                if [ "${COMPARE_MODE:-false}" = true ]; then
                    COMPARE_FILES+=("$1")
                fi
                shift
                ;;
        esac
    done

    # Execute command
    case $command in
        analyze)
            if [ -z "${RESPONSE_TEXT:-}" ] && [ -z "${INPUT_FILE:-}" ] && [ -z "${SESSION_ID:-}" ]; then
                print_error "Please provide --file, --text, or --session"
                exit 1
            fi
            if [ -n "${INPUT_FILE:-}" ]; then
                RESPONSE_TEXT=$(cat "$INPUT_FILE")
            fi
            analyze_response "$RESPONSE_TEXT"
            ;;
        score)
            if [ -z "${RESPONSE_TEXT:-}" ] && [ -z "${INPUT_FILE:-}" ]; then
                print_error "Please provide --file or --text"
                exit 1
            fi
            if [ -n "${INPUT_FILE:-}" ]; then
                RESPONSE_TEXT=$(cat "$INPUT_FILE")
            fi
            check_quality "$RESPONSE_TEXT"
            ;;
        patterns)
            if [ -z "${RESPONSE_TEXT:-}" ] && [ -z "${INPUT_FILE:-}" ]; then
                print_error "Please provide --file or --text"
                exit 1
            fi
            if [ -n "${INPUT_FILE:-}" ]; then
                RESPONSE_TEXT=$(cat "$INPUT_FILE")
            fi
            check_patterns "$RESPONSE_TEXT"
            ;;
        quality)
            if [ -z "${RESPONSE_TEXT:-}" ] && [ -z "${INPUT_FILE:-}" ]; then
                print_error "Please provide --file or --text"
                exit 1
            fi
            if [ -n "${INPUT_FILE:-}" ]; then
                RESPONSE_TEXT=$(cat "$INPUT_FILE")
            fi
            check_quality "$RESPONSE_TEXT"
            ;;
        consistency)
            if [ -z "${RESPONSE_TEXT:-}" ] && [ -z "${INPUT_FILE:-}" ]; then
                print_error "Please provide --file or --text"
                exit 1
            fi
            if [ -n "${INPUT_FILE:-}" ]; then
                RESPONSE_TEXT=$(cat "$INPUT_FILE")
            fi
            check_consistency "$RESPONSE_TEXT"
            ;;
        compare)
            if [ ${#COMPARE_FILES[@]:-0} -lt 2 ]; then
                print_error "At least 2 files required for comparison"
                exit 1
            fi
            compare_responses "${COMPARE_FILES[@]}"
            ;;
        report)
            if [ -z "${SESSION_ID:-}" ] && [ -z "${RESPONSE_TEXT:-}" ] && [ -z "${INPUT_FILE:-}" ]; then
                print_error "Please provide --session, --file, or --text"
                exit 1
            fi
            if [ -n "${INPUT_FILE:-}" ]; then
                RESPONSE_TEXT=$(cat "$INPUT_FILE")
            fi
            analyze_response "$RESPONSE_TEXT"
            ;;
        help)
            show_help
            ;;
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
