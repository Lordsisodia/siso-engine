#!/usr/bin/env python3
"""
STATE.md Management System Demo

This script demonstrates the STATE.md management system capabilities:
- Creating a new workflow
- Updating workflow progress
- Tracking task completion
- Resuming workflows
- Generating human-readable progress reports
"""

from pathlib import Path
from datetime import datetime
import time

from .state_manager import StateManager, TaskState, WorkflowState


def print_separator(title: str = ""):
    """Print a visual separator."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    else:
        print(f"{'='*60}")


def demo_basic_workflow():
    """Demonstrate basic workflow creation and updates."""
    print_separator("DEMO 1: Basic Workflow Creation")

    # Create a temporary STATE.md for demo
    state_path = Path("/tmp/STATE_demo.md")
    manager = StateManager(state_path=state_path)

    # Define workflow waves
    waves = [
        [
            {"task_id": "planner", "description": "Create project plan", "agent_id": "planner_1"},
            {"task_id": "researcher", "description": "Research requirements", "agent_id": "researcher_1"}
        ],
        [
            {"task_id": "developer", "description": "Implement core feature", "agent_id": "developer_1"},
            {"task_id": "tester", "description": "Write unit tests", "agent_id": "tester_1"}
        ],
        [
            {"task_id": "reviewer", "description": "Code review", "agent_id": "reviewer_1"},
            {"task_id": "deployer", "description": "Deploy to staging", "agent_id": "deployer_1"}
        ]
    ]

    # Initialize workflow
    print("Initializing workflow...")
    manager.initialize(
        workflow_id="demo_workflow_001",
        workflow_name="Feature Development Pipeline",
        total_waves=3,
        all_waves=waves,
        metadata={
            "project": "E-Commerce Platform",
            "version": "2.0.0",
            "team": "Backend Squad"
        }
    )

    print("✓ STATE.md created")
    print("\n" + "-"*60)
    print(state_path.read_text())
    print("-"*60)

    # Simulate completing wave 1
    print_separator("DEMO 2: Completing Wave 1")

    time.sleep(0.5)  # Small delay to show timestamp changes

    manager.update(
        workflow_id="demo_workflow_001",
        workflow_name="Feature Development Pipeline",
        wave_id=1,
        total_waves=3,
        completed_tasks=[
            {
                "task_id": "planner",
                "description": "Create project plan",
                "wave_id": 1,
                "result": {
                    "success": True,
                    "files_modified": ["PLAN.md", "docs/architecture.md"]
                },
                "commit_hash": "a1b2c3d"
            },
            {
                "task_id": "researcher",
                "description": "Research requirements",
                "wave_id": 1,
                "result": {
                    "success": True,
                    "files_modified": ["docs/requirements.md"]
                },
                "commit_hash": "e4f5g6h"
            }
        ],
        current_wave_tasks=[],
        pending_waves=waves[1:],
        notes=["All planning tasks completed successfully", "Requirements validated with stakeholders"]
    )

    print("✓ Wave 1 marked as complete")
    print("\n" + "-"*60)
    print(state_path.read_text())
    print("-"*60)

    # Simulate completing wave 2
    print_separator("DEMO 3: Completing Wave 2")

    time.sleep(0.5)

    manager.update(
        workflow_id="demo_workflow_001",
        workflow_name="Feature Development Pipeline",
        wave_id=2,
        total_waves=3,
        completed_tasks=[
            {
                "task_id": "planner",
                "description": "Create project plan",
                "wave_id": 1,
                "result": {"success": True}
            },
            {
                "task_id": "researcher",
                "description": "Research requirements",
                "wave_id": 1,
                "result": {"success": True}
            }
        ],
        current_wave_tasks=[
            {
                "task_id": "developer",
                "description": "Implement core feature",
                "result": {
                    "success": True,
                    "files_modified": [
                        "src/api/endpoint.py",
                        "src/models/feature.py",
                        "src/services/processor.py"
                    ]
                },
                "commit_hash": "i7j8k9l"
            },
            {
                "task_id": "tester",
                "description": "Write unit tests",
                "result": {
                    "success": True,
                    "files_modified": [
                        "tests/test_endpoint.py",
                        "tests/test_processor.py"
                    ]
                },
                "commit_hash": "m0n1o2p"
            }
        ],
        pending_waves=waves[2:],
        notes=["Implementation completed with 100% test coverage", "Performance benchmarks met"]
    )

    print("✓ Wave 2 marked as complete")
    print("\n" + "-"*60)
    print(state_path.read_text())
    print("-"*60)

    # Complete final wave
    print_separator("DEMO 4: Completing Final Wave")

    time.sleep(0.5)

    manager.update(
        workflow_id="demo_workflow_001",
        workflow_name="Feature Development Pipeline",
        wave_id=3,
        total_waves=3,
        completed_tasks=[
            {
                "task_id": "planner",
                "description": "Create project plan",
                "wave_id": 1,
                "result": {"success": True}
            },
            {
                "task_id": "researcher",
                "description": "Research requirements",
                "wave_id": 1,
                "result": {"success": True}
            },
            {
                "task_id": "developer",
                "description": "Implement core feature",
                "wave_id": 2,
                "result": {"success": True}
            },
            {
                "task_id": "tester",
                "description": "Write unit tests",
                "wave_id": 2,
                "result": {"success": True}
            }
        ],
        current_wave_tasks=[
            {
                "task_id": "reviewer",
                "description": "Code review",
                "result": {
                    "success": True,
                    "files_modified": []
                },
                "commit_hash": "q3r4s5t"
            },
            {
                "task_id": "deployer",
                "description": "Deploy to staging",
                "result": {
                    "success": True,
                    "files_modified": ["deploy/staging.yaml"]
                },
                "commit_hash": "u6v7w8x"
            }
        ],
        pending_waves=[],
        notes=["All code reviews approved", "Successfully deployed to staging environment"]
    )

    print("✓ Wave 3 (final) marked as complete")
    print("\n" + "-"*60)
    print(state_path.read_text())
    print("-"*60)


def demo_workflow_resumption():
    """Demonstrate workflow resumption from STATE.md."""
    print_separator("DEMO 5: Workflow Resumption")

    # Create a temporary STATE.md
    state_path = Path("/tmp/STATE_resume_demo.md")
    manager = StateManager(state_path=state_path)

    # Create an in-progress workflow
    waves = [
        [{"task_id": "task_1", "description": "Initial setup"}],
        [{"task_id": "task_2", "description": "Development"}],
        [{"task_id": "task_3", "description": "Testing"}],
        [{"task_id": "task_4", "description": "Deployment"}]
    ]

    manager.initialize(
        workflow_id="resume_demo",
        workflow_name="Interruptible Workflow",
        total_waves=4,
        all_waves=waves
    )

    # Complete first wave
    manager.update(
        workflow_id="resume_demo",
        workflow_name="Interruptible Workflow",
        wave_id=1,
        total_waves=4,
        completed_tasks=[
            {
                "task_id": "task_1",
                "description": "Initial setup",
                "wave_id": 1,
                "result": {"success": True}
            }
        ],
        current_wave_tasks=[],
        pending_waves=waves[1:]
    )

    print("Workflow interrupted after wave 1...")
    print("\nCurrent STATE.md:")
    print("-"*60)
    print(state_path.read_text())
    print("-"*60)

    # Get resume information
    print("\nGetting resume information...")
    resume_info = manager.get_resume_info()

    print(f"\n✓ Can resume from: Wave {resume_info['resume_wave']}/{resume_info['total_waves']}")
    print(f"  Completed tasks: {', '.join(resume_info['completed_tasks'])}")
    print(f"  Pending tasks: {', '.join(resume_info['pending_tasks'])}")
    print(f"  Started at: {resume_info['started_at']}")

    # Resume workflow
    print("\nResuming workflow from wave 2...")
    manager.update(
        workflow_id="resume_demo",
        workflow_name="Interruptible Workflow",
        wave_id=2,
        total_waves=4,
        completed_tasks=[
            {
                "task_id": "task_1",
                "description": "Initial setup",
                "wave_id": 1,
                "result": {"success": True}
            }
        ],
        current_wave_tasks=[
            {
                "task_id": "task_2",
                "description": "Development",
                "result": {"success": True}
            }
        ],
        pending_waves=waves[2:],
        notes=["Workflow resumed after interruption"]
    )

    print("\n✓ Workflow resumed successfully")
    print("\nUpdated STATE.md:")
    print("-"*60)
    print(state_path.read_text())
    print("-"*60)


def demo_failed_workflow():
    """Demonstrate handling failed tasks."""
    print_separator("DEMO 6: Handling Failed Tasks")

    state_path = Path("/tmp/STATE_failure_demo.md")
    manager = StateManager(state_path=state_path)

    # Create workflow with some failures
    manager.update(
        workflow_id="failure_demo",
        workflow_name="Workflow with Failures",
        wave_id=1,
        total_waves=3,
        completed_tasks=[
            {
                "task_id": "task_1",
                "description": "Successful task",
                "wave_id": 1,
                "result": {"success": True, "files_modified": ["file1.py"]}
            }
        ],
        current_wave_tasks=[
            {
                "task_id": "task_2",
                "description": "Failed task",
                "result": {
                    "success": False,
                    "error": "Database connection timeout after 30s"
                }
            },
            {
                "task_id": "task_3",
                "description": "Successful task",
                "result": {"success": True, "files_modified": ["file3.py"]}
            }
        ],
        pending_waves=[
            [{"task_id": "task_4", "description": "Pending task"}]
        ],
        notes=["Some tasks failed, need to retry"]
    )

    print("Workflow with mixed success/failure:")
    print("\n" + "-"*60)
    print(state_path.read_text())
    print("-"*60)

    # Get resume info to show it handles failures
    resume_info = manager.get_resume_info()
    print(f"\nResume information:")
    print(f"  Current wave: {resume_info['current_wave']}")
    print(f"  Resume wave: {resume_info['resume_wave']}")
    print(f"  Failed tasks: {', '.join(resume_info['failed_tasks'])}")


def demo_manual_state_operations():
    """Demonstrate manual state operations."""
    print_separator("DEMO 7: Manual State Operations")

    state_path = Path("/tmp/STATE_manual_demo.md")
    manager = StateManager(state_path=state_path)

    # Create initial state
    manager.initialize(
        workflow_id="manual_demo",
        workflow_name="Manual Operations Demo",
        total_waves=2,
        all_waves=[
            [{"task_id": "task_1", "description": "Task 1"}],
            [{"task_id": "task_2", "description": "Task 2"}]
        ]
    )

    print("1. Initial STATE.md created")
    print(f"   File exists: {state_path.exists()}")

    # Add a note
    print("\n2. Adding a note...")
    manager.add_note("This is an important observation")
    manager.add_note("Another note for tracking")
    print("   ✓ Notes added")

    # Load and display state
    print("\n3. Loading state...")
    state = manager.load_state()
    print(f"   Workflow: {state.workflow_name}")
    print(f"   Wave: {state.current_wave}/{state.total_waves}")
    print(f"   Notes: {len(state.notes)}")
    for note in state.notes:
        print(f"     - {note}")

    # Clear state
    print("\n4. Clearing STATE.md...")
    manager.clear()
    print(f"   File exists: {state_path.exists()}")
    print("   ✓ STATE.md removed")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("  STATE.md Management System - Complete Demo")
    print("="*60)

    try:
        demo_basic_workflow()
        demo_workflow_resumption()
        demo_failed_workflow()
        demo_manual_state_operations()

        print_separator("Summary")
        print("✓ All demos completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  1. Creating and initializing workflows")
        print("  2. Updating workflow progress wave by wave")
        print("  3. Tracking task completion with commit hashes")
        print("  4. Adding notes and metadata")
        print("  5. Resuming interrupted workflows")
        print("  6. Handling failed tasks")
        print("  7. Manual state operations (load, add_note, clear)")
        print("\nThe STATE.md system provides:")
        print("  • Human-readable progress tracking")
        print("  • Automatic resumption after interruptions")
        print("  • Integration with git commits")
        print("  • Support for notes and metadata")
        print("  • Easy parsing and loading")
        print("\n" + "="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
