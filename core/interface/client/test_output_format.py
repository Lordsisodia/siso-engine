#!/usr/bin/env python3
"""
Test the agent output format integration.

Tests that:
1. Base prompt includes output format instructions
2. AgentOutputParser can parse outputs
3. Scripts can use the parser for agent coordination
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from AgentOutputParser import (
    parse_agent_output,
    create_agent_output,
    extract_status,
    extract_deliverables,
    extract_next_steps,
    chain_agent_outputs,
    ParsedAgentOutput,
)


def test_parse_valid_output():
    """Test parsing a valid agent output."""
    print("Testing: parse_agent_output with valid output")

    output = '''<output>
{
  "status": "success",
  "summary": "Created user authentication API",
  "deliverables": ["api/auth.ts", "middleware/jwt.ts"],
  "next_steps": ["test the endpoints", "deploy to staging"],
  "metadata": {
    "agent": "coder",
    "task_id": "task-123",
    "duration_seconds": 180
  }
}
---

I implemented JWT authentication by creating two new files. The auth.ts
file contains the login endpoint that validates credentials and returns
a JWT token. The middleware validates tokens on protected routes.
</output>'''

    parsed = parse_agent_output(output)

    assert parsed.status == "success"
    assert parsed.summary == "Created user authentication API"
    assert len(parsed.deliverables) == 2
    assert "api/auth.ts" in parsed.deliverables
    assert parsed.is_success
    assert not parsed.is_failed
    print("  ✓ Valid output parsed correctly")
    return True


def test_parse_failed_output():
    """Test parsing a failed agent output."""
    print("Testing: parse_agent_output with failed status")

    output = '''<output>
{
  "status": "failed",
  "summary": "Could not implement feature due to missing dependencies",
  "deliverables": [],
  "next_steps": ["install dependencies", "retry"],
  "metadata": {
    "agent": "coder",
    "task_id": "task-456",
    "duration_seconds": 60,
    "error": "Package 'bcrypt' not found"
  }
}
---

Attempted to implement authentication but bcrypt is not installed.
Run: npm install bcrypt
</output>'''

    parsed = parse_agent_output(output)

    assert parsed.status == "failed"
    assert parsed.is_failed
    assert not parsed.is_success
    assert len(parsed.deliverables) == 0
    assert parsed.metadata.get("error") == "Package 'bcrypt' not found"
    print("  ✓ Failed output parsed correctly")
    return True


def test_extract_helpers():
    """Test quick extraction helpers."""
    print("Testing: extract_status, extract_deliverables, extract_next_steps")

    output = '''<output>
{
  "status": "partial",
  "summary": "Core features implemented",
  "deliverables": ["api/users.ts"],
  "next_steps": ["add error handling"]
}
---
Some content here...
'''

    status = extract_status(output)
    assert status == "partial"

    deliverables = extract_deliverables(output)
    assert "api/users.ts" in deliverables

    steps = extract_next_steps(output)
    assert "add error handling" in steps

    print("  ✓ Helper functions work correctly")
    return True


def test_create_agent_output():
    """Test creating a properly formatted output."""
    print("Testing: create_agent_output")

    output = create_agent_output(
        status="success",
        summary="Implemented feature",
        deliverables=["file1.ts", "file2.ts"],
        next_steps=["test it"],
        human_content="Here's what I did...",
        agent_name="coder",
        task_id="task-789",
        duration_seconds=120,
    )

    # Verify it's parseable
    parsed = parse_agent_output(output)
    assert parsed.status == "success"
    assert "file1.ts" in parsed.deliverables

    print("  ✓ create_agent_output generates valid format")
    return True


def test_chain_agent_outputs():
    """Test chaining multiple agent outputs."""
    print("Testing: chain_agent_outputs")

    output1 = create_agent_output(
        status="success",
        summary="Part 1 done",
        deliverables=["file1.ts"],
        next_steps=[],
        human_content="...",
        agent_name="agent1",
        task_id="task-1",
    )

    output2 = create_agent_output(
        status="success",
        summary="Part 2 done",
        deliverables=["file2.ts"],
        next_steps=[],
        human_content="...",
        agent_name="agent2",
        task_id="task-2",
    )

    output3 = create_agent_output(
        status="failed",
        summary="Part 3 failed",
        deliverables=[],
        next_steps=[],
        human_content="...",
        agent_name="agent3",
        task_id="task-3",
    )

    results = chain_agent_outputs([output1, output2, output3])

    assert results["success_count"] == 2
    assert results["failed_count"] == 1
    assert results["total"] == 3
    assert set(results["all_deliverables"]) == {"file1.ts", "file2.ts"}

    print("  ✓ chain_agent_outputs aggregates correctly")
    return True


def test_base_prompt_includes_format():
    """Test that base prompt includes output format instructions."""
    print("Testing: Base prompt includes output format")

    try:
        from AgentClient import create_client

        # Create a client config
        config = create_client(
            project_dir=Path("."),
            agent_type="coder"
        )

        # Check that system_prompt includes output format
        assert "Output Format for Agent Communication" in config["system_prompt"]
        assert "<output>" in config["system_prompt"]
        assert '"status"' in config["system_prompt"]

        print("  ✓ Base prompt includes output format instructions")
        return True

    except ImportError as e:
        print(f"  ⚠ Could not import AgentClient: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Agent Output Format Integration Tests")
    print("=" * 60)
    print()

    tests = [
        test_parse_valid_output,
        test_parse_failed_output,
        test_extract_helpers,
        test_create_agent_output,
        test_chain_agent_outputs,
        test_base_prompt_includes_format,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
