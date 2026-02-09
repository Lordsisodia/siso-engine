#!/usr/bin/env bash
# intelligent-scout.sh - AI-Powered Improvement Scout
# VERSION: 1.0.0
#
# Purpose: Spawn Claude Code instances to intelligently analyze BlackBox5
#          for improvement opportunities using GLM-4.7 via Z.AI API.
#
# Usage:
#   intelligent-scout.sh [--project-dir DIR] [--output FILE] [--parallel]
#
# This script spawns multiple Claude Code subagents, each analyzing a
# specific aspect of the system, then aggregates findings into a
# prioritized improvement report.

set -euo pipefail

VERSION="1.0.0"

# Source path resolution library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/paths.sh"

SCOUT_DIR="$(get_engine_path)/.autonomous"
PROJECT_DIR="$(get_project_path)"
OUTPUT_DIR="$(get_analysis_path)/scout-reports"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_ID="SCOUT-${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[SCOUT]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SCOUT]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[SCOUT]${NC} $*"
}

log_error() {
    echo -e "${RED}[SCOUT]${NC} $*"
}

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Parse arguments
PARALLEL=false
PROJECT_DIR_OVERRIDE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-dir)
            PROJECT_DIR_OVERRIDE="$2"
            shift 2
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --help|-h)
            echo "Usage: intelligent-scout.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --project-dir DIR    Project directory to analyze"
            echo "  --parallel           Run analyzers in parallel"
            echo "  --help, -h           Show this help"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [[ -n "$PROJECT_DIR_OVERRIDE" ]]; then
    PROJECT_DIR="$PROJECT_DIR_OVERRIDE"
fi

log "Intelligent Scout v${VERSION} starting..."
log "Project: $PROJECT_DIR"
log "Report ID: $REPORT_ID"

# ============================================================================
# PHASE 1: Spawn Specialized Analyzer Agents
# ============================================================================

log "Phase 1: Spawning specialized analyzer agents..."

# Define analyzer agents - each will be a separate Claude Code instance
# These use the Task tool pattern from Ralph

ANALYZERS=(
    "skill-analyzer:Analyze skill effectiveness and identify gaps"
    "process-analyzer:Analyze recent runs for friction patterns"
    "documentation-analyzer:Check for documentation drift and gaps"
    "architecture-analyzer:Identify architectural improvements"
    "code-quality-analyzer:Find code quality issues and anti-patterns"
)

# Create temporary directory for analyzer outputs
ANALYZER_OUTPUT_DIR=$(mktemp -d)
trap "rm -rf $ANALYZER_OUTPUT_DIR" EXIT

# Function to spawn an analyzer subagent
spawn_analyzer() {
    local analyzer_name="$1"
    local analyzer_desc="$2"
    local output_file="${ANALYZER_OUTPUT_DIR}/${analyzer_name}.json"

    log "Spawning ${analyzer_name}..."

    # Create the prompt for this analyzer
    local prompt
    prompt=$(cat <<EOF
You are the ${analyzer_name} for BlackBox5 improvement scouting.

MISSION: ${analyzer_desc}

PROJECT DIRECTORY: ${PROJECT_DIR}

ANALYSIS INSTRUCTIONS:
1. Read relevant files in the project directory
2. Identify specific improvement opportunities
3. Score each opportunity (impact 1-5, effort 1-5, frequency 1-3)
4. Provide concrete evidence for each finding

OUTPUT FORMAT - Return ONLY valid JSON:
{
  "analyzer": "${analyzer_name}",
  "opportunities": [
    {
      "id": "${analyzer_name}-001",
      "title": "Clear, actionable title",
      "description": "What the issue is and why it matters",
      "category": "skills|process|documentation|architecture|code-quality",
      "evidence": "Specific files, metrics, or patterns observed",
      "impact_score": 1-5,
      "effort_score": 1-5,
      "frequency_score": 1-3,
      "files_to_check": ["path/to/file1", "path/to/file2"],
      "suggested_action": "Concrete next step"
    }
  ],
  "patterns": [
    {
      "name": "Pattern name",
      "description": "What this pattern indicates",
      "occurrences": number,
      "severity": "high|medium|low"
    }
  ],
  "summary": "Brief summary of findings"
}

RULES:
- Be specific: include file paths and line numbers where possible
- Be objective: base findings on data, not opinions
- Be actionable: every opportunity needs a clear next step
- Focus on high-value improvements that affect the whole system
EOF
)

    # Use Claude Code CLI to spawn the analyzer
    # This requires ANTHROPIC_API_KEY to be set
    if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
        log_error "ANTHROPIC_API_KEY not set. Cannot spawn intelligent analyzers."
        return 1
    fi

    # Spawn Claude Code in headless mode with the prompt
    # The --output-json flag ensures we get structured output
    claude code \
        --headless \
        --prompt "$prompt" \
        --allowed-tools "Read,Glob,Grep" \
        --output-json \
        > "$output_file" 2>/dev/null || {
            log_warn "${analyzer_name} failed, creating empty output"
            echo '{"analyzer": "'${analyzer_name}'", "opportunities": [], "patterns": [], "summary": "Analysis failed", "error": true}' > "$output_file"
        }

    log_success "${analyzer_name} complete"
}

# Check if we should use parallel execution
if [[ "$PARALLEL" == "true" ]]; then
    log "Running analyzers in parallel..."

    # Spawn all analyzers in background
    for analyzer in "${ANALYZERS[@]}"; do
        IFS=':' read -r name desc <<< "$analyzer"
        spawn_analyzer "$name" "$desc" &
    done

    # Wait for all to complete
    wait
else
    log "Running analyzers sequentially..."

    # Spawn analyzers one at a time
    for analyzer in "${ANALYZERS[@]}"; do
        IFS=':' read -r name desc <<< "$analyzer"
        spawn_analyzer "$name" "$desc"
    done
fi

# ============================================================================
# PHASE 2: Aggregate Results
# ============================================================================

log "Phase 2: Aggregating analyzer results..."

# Combine all analyzer outputs into a single report
python3 << PYTHON_EOF
import json
import os
import sys
from pathlib import Path
from datetime import datetime

analyzer_output_dir = "${ANALYZER_OUTPUT_DIR}"
report_id = "${REPORT_ID}"
project_dir = "${PROJECT_DIR}"

all_opportunities = []
all_patterns = []
analyzer_summaries = []

# Read each analyzer output
for json_file in Path(analyzer_output_dir).glob("*.json"):
    try:
        with open(json_file) as f:
            data = json.load(f)

        analyzer_name = data.get("analyzer", json_file.stem)
        opportunities = data.get("opportunities", [])
        patterns = data.get("patterns", [])
        summary = data.get("summary", "")
        has_error = data.get("error", False)

        # Add analyzer prefix to opportunity IDs
        for opp in opportunities:
            if "id" not in opp:
                opp["id"] = f"{analyzer_name}-{len(all_opportunities)+1:03d}"
            # Calculate total score
            impact = opp.get("impact_score", 3)
            effort = opp.get("effort_score", 3)
            frequency = opp.get("frequency_score", 2)
            opp["total_score"] = (impact * 3) + (frequency * 2) - (effort * 1.5)

        all_opportunities.extend(opportunities)
        all_patterns.extend(patterns)
        analyzer_summaries.append({
            "name": analyzer_name,
            "opportunities_found": len(opportunities),
            "summary": summary,
            "error": has_error
        })
    except Exception as e:
        print(f"Error reading {json_file}: {e}", file=sys.stderr)
        analyzer_summaries.append({
            "name": json_file.stem,
            "opportunities_found": 0,
            "summary": f"Error: {e}",
            "error": True
        })

# Sort opportunities by total score
all_opportunities.sort(key=lambda x: x.get("total_score", 0), reverse=True)

# Identify quick wins (low effort, high impact)
quick_wins = [
    opp for opp in all_opportunities
    if opp.get("effort_score", 5) <= 2 and opp.get("impact_score", 1) >= 3
]

# Generate report
report = {
    "scout_report": {
        "id": report_id,
        "timestamp": datetime.now().isoformat(),
        "scout_version": "1.0.0-intelligent",
        "project_dir": project_dir,
        "analysis_type": "intelligent",
        "analyzers_used": len(analyzer_summaries),
        "summary": {
            "total_opportunities": len(all_opportunities),
            "high_impact": len([o for o in all_opportunities if o.get("impact_score", 0) >= 4]),
            "quick_wins": len(quick_wins),
            "patterns_found": len(all_patterns),
            "analyzers": analyzer_summaries
        },
        "opportunities": all_opportunities,
        "patterns": all_patterns,
        "quick_wins": quick_wins[:5],  # Top 5 quick wins
        "recommendations": [
            {
                "priority": i + 1,
                "opportunity_id": opp["id"],
                "title": opp["title"],
                "total_score": opp["total_score"],
                "rationale": f"Score: {opp['total_score']:.1f} | Impact: {opp['impact_score']}/5 | Effort: {opp['effort_score']}/5"
            }
            for i, opp in enumerate(all_opportunities[:10])
        ]
    }
}

# Write report
output_file = Path("${OUTPUT_DIR}") / f"scout-report-intelligent-{report_id}.json"
with open(output_file, 'w') as f:
    json.dump(report, f, indent=2)

print(f"Report saved to: {output_file}")
print(f"Total opportunities found: {len(all_opportunities)}")
print(f"Quick wins: {len(quick_wins)}")
PYTHON_EOF

# ============================================================================
# PHASE 3: Generate Human-Readable Summary
# ============================================================================

log "Phase 3: Generating human-readable summary..."

# Convert JSON to YAML for easier reading
python3 << PYTHON_EOF
import json
import yaml
from pathlib import Path

report_file = Path("${OUTPUT_DIR}") / f"scout-report-intelligent-${REPORT_ID}.json"
output_yaml = Path("${OUTPUT_DIR}") / f"scout-report-intelligent-${REPORT_ID}.yaml"

with open(report_file) as f:
    report = json.load(f)

with open(output_yaml, 'w') as f:
    yaml.dump(report, f, default_flow_style=False, sort_keys=False)

print(f"YAML report: {output_yaml}")
PYTHON_EOF

# ============================================================================
# Done
# ============================================================================

log_success "Intelligent Scout analysis complete!"
log "Reports saved to: ${OUTPUT_DIR}/"
log "  - JSON: scout-report-intelligent-${REPORT_ID}.json"
log "  - YAML: scout-report-intelligent-${REPORT_ID}.yaml"

# Display top 5 opportunities
echo ""
echo "=========================================="
echo "TOP 5 IMPROVEMENT OPPORTUNITIES"
echo "=========================================="

python3 << PYTHON_EOF
import json
from pathlib import Path

report_file = Path("${OUTPUT_DIR}") / f"scout-report-intelligent-${REPORT_ID}.json"
with open(report_file) as f:
    report = json.load(f)

for i, opp in enumerate(report["scout_report"]["opportunities"][:5], 1):
    print(f"\n{i}. {opp['title']}")
    print(f"   Score: {opp['total_score']:.1f} | Impact: {opp['impact_score']}/5 | Effort: {opp['effort_score']}/5")
    print(f"   Category: {opp['category']}")
    print(f"   Action: {opp['suggested_action'][:80]}...")
PYTHON_EOF

echo ""
echo "Run 'cat ${OUTPUT_DIR}/scout-report-intelligent-${REPORT_ID}.yaml' for full details."
