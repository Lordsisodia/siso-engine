#!/bin/bash
# Planning Agent CLI
# Invokes the PlanningAgent to create PRDs, epics, and tasks from user requests
#
# Usage: ./plan.sh "Build a REST API for user management" [--kanban] [--output-dir ./plans]

set -e

# Determine paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BLACKBOX5_DIR="$(cd "$ENGINE_DIR/../.." && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Defaults
CREATE_KANBAN=false
OUTPUT_DIR=""
PROJECT_TYPE=""
CONSTRAINTS=""

# Parse arguments
REQUEST=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --kanban)
            CREATE_KANBAN=true
            shift
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --project-type)
            PROJECT_TYPE="$2"
            shift 2
            ;;
        --constraints)
            CONSTRAINTS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./plan.sh \"Your request here\" [options]"
            echo ""
            echo "Options:"
            echo "  --kanban           Create Vibe Kanban cards"
            echo "  --output-dir DIR   Save PRD and artifacts to directory"
            echo "  --project-type TYPE  Specify project type (api, web_app, cli_tool)"
            echo "  --constraints LIST  Comma-separated constraints (e.g., Python,FastAPI)"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            if [ -z "$REQUEST" ]; then
                REQUEST="$1"
            else
                REQUEST="$REQUEST $1"
            fi
            shift
            ;;
    esac
done

if [ -z "$REQUEST" ]; then
    echo "Error: No request provided"
    echo "Usage: ./plan.sh \"Build a REST API for user management\""
    exit 1
fi

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Planning Agent${NC}"
echo -e "${BLUE}  BMAD Framework${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Request: $REQUEST"
echo "Kanban: $CREATE_KANBAN"
if [ -n "$OUTPUT_DIR" ]; then
    echo "Output: $OUTPUT_DIR"
fi
echo ""

# Create Python script to execute planning
PYTHON_SCRIPT=$(cat << 'EOF'
import asyncio
import sys
import json
from pathlib import Path

# Add 2-engine to path
sys.path.insert(0, str(Path("/Users/shaansisodia/.blackbox5/2-engine")))

from core.agents.definitions.planning_agent import PlanningAgent
from core.agents.definitions.core.base_agent import AgentConfig, AgentTask

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("request")
    parser.add_argument("--kanban", action="store_true")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--project-type", default="")
    parser.add_argument("--constraints", default="")
    args = parser.parse_args()

    # Configure agent
    config = AgentConfig(
        name="planner",
        full_name="Planning Agent",
        role="planner",
        category="specialist",
        description="Creates structured plans from user requests",
        capabilities=["planning", "prd_generation", "task_breakdown"],
        metadata={"bmad_enabled": True}
    )

    agent = PlanningAgent(config)

    # Optional: Configure Vibe Kanban
    if args.kanban:
        try:
            from core.agents.definitions.managerial.skills.vibe_kanban_manager import VibeKanbanManager
            vibe_kanban = VibeKanbanManager()
            agent.set_vibe_kanban(vibe_kanban)
            print("✓ Vibe Kanban configured")
        except Exception as e:
            print(f"⚠ Vibe Kanban not available: {e}")

    # Build context
    context = {"create_kanban_cards": args.kanban}
    if args.project_type:
        context["project_type"] = args.project_type
    if args.constraints:
        context["constraints"] = args.constraints.split(",")

    # Create task
    task = AgentTask(
        id=f"plan-{hash(args.request) % 10000}",
        description=args.request,
        type="planning",
        context=context
    )

    print("\n🔄 Analyzing requirements...")
    result = await agent.execute(task)

    if not result.success:
        print(f"\n❌ Planning failed: {result.error}")
        sys.exit(1)

    # Output results
    print(f"\n{result.output}")

    # Show BMAD analysis summary if available
    if result.artifacts.get("bmad_analysis"):
        bmad = result.artifacts["bmad_analysis"]
        print("\n📊 BMAD Analysis Summary:")
        print(f"  Business Goals: {len(bmad.get('business', {}).get('goals', []))}")
        print(f"  Entities: {len(bmad.get('model', {}).get('entities', []))}")
        print(f"  Components: {len(bmad.get('architecture', {}).get('components', []))}")
        print(f"  Phases: {len(bmad.get('development', {}).get('phases', []))}")

    # Show Kanban results
    kanban_results = result.artifacts.get("kanban_results")
    if kanban_results:
        if kanban_results.get("status") == "success":
            print(f"\n✓ Created {kanban_results['created']} Kanban cards")
        elif kanban_results.get("status") == "skipped":
            print(f"\n⚠ Kanban: {kanban_results.get('reason', 'skipped')}")

    # Save artifacts if output dir specified
    if args.output_dir:
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save PRD
        prd = result.artifacts.get("prd", {})
        prd_file = output_path / "PRD.md"
        with open(prd_file, "w") as f:
            f.write(f"# {prd.get('title', 'Product Requirements')}\n\n")
            f.write(f"**Version:** {prd.get('version', '1.0')}\n")
            f.write(f"**Date:** {prd.get('date', '')}\n")
            f.write(f"**Type:** {prd.get('project_type', 'N/A')}\n")
            f.write(f"**Complexity:** {prd.get('complexity', 'N/A')}\n\n")
            f.write(f"## Overview\n\n{prd.get('overview', '')}\n\n")
            f.write("## Objectives\n\n")
            for obj in prd.get('objectives', []):
                f.write(f"- {obj}\n")
            f.write("\n## Key Features\n\n")
            for feat in prd.get('key_features', []):
                f.write(f"- {feat}\n")

        print(f"\n💾 Saved PRD to: {prd_file}")

        # Save epics and tasks
        epics = result.artifacts.get("epics", [])
        tasks = result.artifacts.get("tasks", [])

        tasks_file = output_path / "TASKS.md"
        with open(tasks_file, "w") as f:
            f.write("# Epics and Tasks\n\n")
            for epic in epics:
                f.write(f"## {epic.get('id', 'EPIC')}: {epic.get('title', '')}\n")
                f.write(f"**Priority:** {epic.get('priority', 'N/A')}\n")
                f.write(f"**Effort:** {epic.get('estimated_effort', 'N/A')}\n\n")
                f.write(f"{epic.get('description', '')}\n\n")

                # Find tasks for this epic
                epic_tasks = [t for t in tasks if t.get('epic_id') == epic.get('id')]
                if epic_tasks:
                    f.write("### Tasks\n\n")
                    for task in epic_tasks:
                        f.write(f"- **{task.get('id', 'TASK')}**: {task.get('title', '')}\n")
                    f.write("\n")

        print(f"💾 Saved tasks to: {tasks_file}")

        # Save full artifacts as JSON
        artifacts_file = output_path / "artifacts.json"
        with open(artifacts_file, "w") as f:
            json.dump({
                "prd": prd,
                "epics": epics,
                "tasks": tasks,
                "assignments": result.artifacts.get("assignments", {}),
                "kanban_results": kanban_results,
            }, f, indent=2, default=str)

        print(f"💾 Saved artifacts to: {artifacts_file}")

    print("\n✓ Planning complete!")

if __name__ == "__main__":
    asyncio.run(main())
EOF
)

# Run Python script
python3 -c "$PYTHON_SCRIPT" "$REQUEST" \
    ${CREATE_KANBAN:+--kanban} \
    ${OUTPUT_DIR:+--output-dir "$OUTPUT_DIR"} \
    ${PROJECT_TYPE:+--project-type "$PROJECT_TYPE"} \
    ${CONSTRAINTS:+--constraints "$CONSTRAINTS"}
