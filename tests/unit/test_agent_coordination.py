#!/usr/bin/env python3
"""
Real Agent Coordination Test

Tests the new structured output format with a simulated multi-agent workflow:
1. Manager Agent delegates task to Coder Agent
2. Coder Agent implements feature and returns structured output
3. Manager Agent parses Coder's output
4. Manager Agent delegates to Tester Agent
5. Tester Agent validates and returns structured output
6. Manager Agent aggregates all results

This simulates real agent-to-agent communication.
"""

import sys
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from AgentOutputParser import (
    parse_agent_output,
    create_agent_output,
    chain_agent_outputs,
    ParsedAgentOutput,
)


@dataclass
class SimulatedAgent:
    """A simulated agent for testing."""
    name: str
    role: str

    def execute_task(self, task_description: str, context: dict = None) -> str:
        """Execute a task and return structured output."""
        if context is None:
            context = {}

        print(f"  [{self.name}] Executing: {task_description[:50]}...")

        # Simulate work
        time.sleep(0.1)

        # Return appropriate output based on agent role
        if self.role == "coder":
            return self._coder_output(task_description)
        elif self.role == "tester":
            return self._tester_output(task_description, context)
        elif self.role == "manager":
            return self._manager_output(task_description, context)
        else:
            return self._generic_output(task_description)

    def _coder_output(self, task: str) -> str:
        """Simulate coder agent implementing a feature."""
        summary = f"Implemented {task}"
        human_content = """
## Implementation Details

I created a user management API with the following endpoints:

### GET /api/users
Retrieves all users with pagination support.

### POST /api/users
Creates a new user with validation:
- Email must be unique
- Password must be 8+ characters
- Name is required

### PUT /api/users/:id
Updates existing user by ID.

### DELETE /api/users/:id
Deletes user by ID.

### Tests Created
- Test valid user creation
- Test duplicate email rejection
- Test pagination
- Test user deletion
"""

        return create_agent_output(
            status="success",
            summary=summary,
            deliverables=["api/users.ts", "tests/users.test.ts"],
            next_steps=["run tests", "deploy to staging"],
            human_content=human_content,
            agent_name=self.name,
            task_id=f"task-{int(time.time())}",
            duration_seconds=45,
        )

    def _tester_output(self, task: str, context: dict) -> str:
        """Simulate tester agent validating work."""
        files_created = context.get("files", [])
        summary = f"Validated {len(files_created)} files, all tests passing"

        files_list = "\n".join(f"- {f}" for f in files_created)
        human_content = f"""
## Test Results

All tests passing successfully!

### Files Validated
{files_list}

### Test Coverage
- Unit tests: 95% coverage
- Integration tests: All passing
- Edge cases: Covered

### Issues Found
None - implementation is solid.
"""

        return create_agent_output(
            status="success",
            summary=summary,
            deliverables=["test-report.md"],
            next_steps=["deploy to production"],
            human_content=human_content,
            agent_name=self.name,
            task_id=f"test-{int(time.time())}",
            duration_seconds=30,
        )

    def _manager_output(self, task: str, context: dict) -> str:
        """Simulate manager agent coordinating work."""
        subtask_results = context.get("subtask_results", [])
        all_deliverables = []
        all_next_steps = []

        for result in subtask_results:
            try:
                parsed = parse_agent_output(result)
                all_deliverables.extend(parsed.deliverables)
                all_next_steps.extend(parsed.next_steps)
            except Exception as e:
                print(f"  [{self.name}] Warning: Could not parse subtask result: {e}")

        summary = f"Coordinated {len(subtask_results)} agents to complete: {task}"
        unique_deliverables = list(set(all_deliverables))
        deliverables_list = "\n".join(f"- {d}" for d in unique_deliverables)

        human_content = f"""
## Coordination Summary

### Subtasks Completed
{len(subtask_results)} agents executed successfully

### All Deliverables
{deliverables_list}

### Timeline
- Total duration: 75 seconds
- Agents involved: {len(subtask_results)}
- Success rate: 100%
"""

        return create_agent_output(
            status="success",
            summary=summary,
            deliverables=unique_deliverables,
            next_steps=["review final implementation", "deploy to production"],
            human_content=human_content,
            agent_name=self.name,
            task_id=f"coord-{int(time.time())}",
            duration_seconds=75,
            subtask_count=len(subtask_results),
        )

    def _generic_output(self, task: str) -> str:
        """Generic agent output."""
        return create_agent_output(
            status="success",
            summary=f"Completed: {task}",
            deliverables=[],
            next_steps=[],
            human_content=f"Task completed: {task}",
            agent_name=self.name,
            task_id=f"task-{int(time.time())}",
            duration_seconds=10,
        )


def test_agent_to_agent_communication():
    """Test that agents can send and parse each other's outputs."""
    print("=" * 70)
    print("TEST 1: Agent-to-Agent Communication")
    print("=" * 70)
    print()

    coder = SimulatedAgent("coder", "coder")
    tester = SimulatedAgent("tester", "tester")
    manager = SimulatedAgent("manager", "manager")

    # Step 1: Coder produces output
    print("Step 1: Coder Agent creates user API")
    coder_output = coder.execute_task("Create user management API")
    print(f"  Output length: {len(coder_output)} chars")
    print()

    # Step 2: Manager parses Coder's output
    print("Step 2: Manager Agent parses Coder's output")
    try:
        parsed = parse_agent_output(coder_output)
        print(f"  ✓ Parsed successfully")
        print(f"  Status: {parsed.status}")
        print(f"  Deliverables: {parsed.deliverables}")
        print(f"  Next steps: {parsed.next_steps}")
        print()

        # Step 3: Manager uses parsed data to delegate to Tester
        print("Step 3: Manager delegates to Tester with context from Coder")
        tester_context = {
            "files": parsed.deliverables,
            "coder_summary": parsed.summary
        }
        tester_output = tester.execute_task(
            f"Validate {len(parsed.deliverables)} files from Coder",
            context=tester_context
        )
        print()

        # Step 4: Manager parses Tester's output
        print("Step 4: Manager parses Tester's output")
        parsed_tester = parse_agent_output(tester_output)
        print(f"  ✓ Parsed successfully")
        print(f"  Status: {parsed_tester.status}")
        print(f"  Summary: {parsed_tester.summary}")
        print()

        # Step 5: Manager aggregates both outputs
        print("Step 5: Manager aggregates all results")
        manager_output = manager.execute_task(
            "Build user management system",
            context={
                "subtask_results": [coder_output, tester_output]
            }
        )

        parsed_manager = parse_agent_output(manager_output)
        print(f"  ✓ Manager coordination complete")
        print(f"  Total deliverables: {len(parsed_manager.deliverables)}")
        print(f"  Items: {parsed_manager.deliverables}")
        print()

        return True

    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling in agent communication."""
    print("=" * 70)
    print("TEST 2: Error Handling in Agent Communication")
    print("=" * 70)
    print()

    # Simulate a failing agent
    failing_agent = SimulatedAgent("failing-coder", "coder")

    # Create a failed output
    failed_output = create_agent_output(
        status="failed",
        summary="Could not implement feature - missing dependencies",
        deliverables=[],
        next_steps=["install dependencies", "retry"],
        human_content="Attempted to implement but package 'bcrypt' not found.",
        agent_name="failing-coder",
        task_id="task-fail-1",
        duration_seconds=30,
        error_type="DependencyError",
        error_message="Package 'bcrypt' not found"
    )

    print("Step 1: Parse failed output")
    try:
        parsed = parse_agent_output(failed_output)
        print(f"  ✓ Parsed failed output successfully")
        print(f"  Status: {parsed.status}")
        print(f"  Is failed: {parsed.is_failed}")
        print(f"  Error type: {parsed.metadata.get('error_type')}")
        print()

        # Step 2: Handler can react to failure
        print("Step 2: Handler reacts to failure status")
        if parsed.is_failed:
            error = parsed.metadata.get("error_message", "Unknown error")
            print(f"  ✓ Detected failure: {error}")
            print(f"  Suggested recovery: {parsed.next_steps}")
            print()

        return True

    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_partial_success():
    """Test partial success handling."""
    print("=" * 70)
    print("TEST 3: Partial Success (Some Features Working)")
    print("=" * 70)
    print()

    # Simulate partial success
    partial_output = create_agent_output(
        status="partial",
        summary="Implemented core features, edge cases pending",
        deliverables=["api/users.ts"],
        next_steps=["add edge case handling", "write more tests"],
        human_content="Core CRUD operations work, but edge cases not handled.",
        agent_name="coder",
        task_id="task-partial-1",
        duration_seconds=60,
        completion_percentage=80,
        issues=[
            {
                "type": "incomplete",
                "description": "Missing validation for edge cases",
                "impact": "medium",
                "blocking": False
            }
        ]
    )

    print("Step 1: Parse partial success output")
    try:
        parsed = parse_agent_output(partial_output)
        print(f"  ✓ Parsed partial output successfully")
        print(f"  Status: {parsed.status}")
        print(f"  Is partial: {parsed.is_partial}")
        print(f"  Completion: {parsed.metadata.get('completion_percentage')}%")
        print(f"  Issues: {len(parsed.metadata.get('issues', []))}")
        print()

        return True

    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_chain_multiple_agents():
    """Test chaining outputs from multiple agents."""
    print("=" * 70)
    print("TEST 4: Chain Multiple Agent Outputs")
    print("=" * 70)
    print()

    agents = [
        SimulatedAgent("architect", "architect"),
        SimulatedAgent("coder", "coder"),
        SimulatedAgent("tester", "tester"),
        SimulatedAgent("reviewer", "reviewer"),
    ]

    outputs = []
    for agent in agents:
        output = agent.execute_task(f"Task by {agent.name}")
        outputs.append(output)

    print(f"Collected {len(outputs)} agent outputs")
    print()

    print("Step 1: Chain all outputs together")
    try:
        results = chain_agent_outputs(outputs)

        print(f"  ✓ Chained successfully")
        print(f"  Total outputs: {results['total']}")
        print(f"  Success: {results['success_count']}")
        print(f"  Failed: {results['failed_count']}")
        print(f"  Overall status: {results['overall_status']}")
        print(f"  All deliverables: {results['all_deliverables']}")
        print(f"  All next steps: {results['all_next_steps']}")
        print()

        return True

    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_world_scenario():
    """Test a realistic multi-agent workflow."""
    print("=" * 70)
    print("TEST 5: Real-World Scenario - Build REST API Endpoint")
    print("=" * 70)
    print()

    manager = SimulatedAgent("manager", "manager")
    architect = SimulatedAgent("architect", "architect")
    coder = SimulatedAgent("coder", "coder")
    tester = SimulatedAgent("tester", "tester")

    task = "Build a REST API endpoint for user authentication"

    print(f"Task: {task}")
    print()

    # Step 1: Manager asks Architect to design
    print("Step 1: Manager → Architect (Design API)")
    architect_output = architect.execute_task(
        "Design authentication API structure",
        context={"requirements": ["JWT based", "secure", "testable"]}
    )
    parsed_architect = parse_agent_output(architect_output)
    print(f"  ✓ Architect design complete: {parsed_architect.summary}")
    print(f"  Deliverables: {parsed_architect.deliverables}")
    print()

    # Step 2: Manager asks Coder to implement
    print("Step 2: Manager → Coder (Implement based on design)")
    coder_output = coder.execute_task(
        "Implement authentication API",
        context={"design_document": parsed_architect.deliverables[0] if parsed_architect.deliverables else ""}
    )
    parsed_coder = parse_agent_output(coder_output)
    print(f"  ✓ Coder implementation complete: {parsed_coder.summary}")
    print(f"  Files created: {parsed_coder.deliverables}")
    print()

    # Step 3: Manager asks Tester to validate
    print("Step 3: Manager → Tester (Validate implementation)")
    tester_output = tester.execute_task(
        "Test authentication endpoint",
        context={"files_to_test": parsed_coder.deliverables}
    )
    parsed_tester = parse_agent_output(tester_output)
    print(f"  ✓ Tester validation complete: {parsed_tester.summary}")
    print()

    # Step 4: Manager aggregates and produces final output
    print("Step 4: Manager aggregates all results")
    manager_output = manager.execute_task(
        task,
        context={
            "subtask_results": [architect_output, coder_output, tester_output]
        }
    )
    parsed_manager = parse_agent_output(manager_output)
    print(f"  ✓ Manager coordination complete")
    print(f"  Final status: {parsed_manager.status}")
    print(f"  Total deliverables: {len(parsed_manager.deliverables)}")
    print(f"  Deliverables: {', '.join(parsed_manager.deliverables)}")
    print()

    # Show human-readable summary
    print("=" * 70)
    print("HUMAN-READABLE SUMMARY FROM MANAGER:")
    print("=" * 70)
    print(parsed_manager.human_content[:500] + "...")
    print()

    return True


def main():
    """Run all coordination tests."""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "AGENT COORDINATION TEST SUITE" + " " * 24 + "║")
    print("║" + " " * 68 + "║")
    print("║" + "Testing structured output format for agent-to-agent communication  " + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    tests = [
        ("Agent-to-Agent Communication", test_agent_to_agent_communication),
        ("Error Handling", test_error_handling),
        ("Partial Success", test_partial_success),
        ("Chain Multiple Agents", test_chain_multiple_agents),
        ("Real-World Scenario", test_real_world_scenario),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✓ TEST PASSED: {name}")
            else:
                failed += 1
                print(f"✗ TEST FAILED: {name}")
        except Exception as e:
            failed += 1
            print(f"✗ TEST ERROR: {name} - {e}")
            import traceback
            traceback.print_exc()

        print()

    print("=" * 70)
    print(f"FINAL RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    print()

    if failed == 0:
        print("🎉 ALL TESTS PASSED! Agent coordination is working.")
        print()
        print("Key Takeaways:")
        print("  • Agents can produce structured outputs")
        print("  • Agents can parse each other's outputs")
        print("  • Error handling works correctly")
        print("  • Multiple agents can be chained")
        print("  • Real-world workflows are supported")
    else:
        print("⚠️  Some tests failed. Review the output above.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
