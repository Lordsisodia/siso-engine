#!/usr/bin/env python3
"""
Test Claude Code CLI with Structured Output Format

This tests the actual integration where agents use Claude Code CLI
and produce structured outputs that can be parsed by other agents.
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from AgentOutputParser import parse_agent_output


def test_claude_code_with_format():
    """Test that Claude Code CLI can follow the output format."""
    print("=" * 70)
    print("Testing Claude Code CLI with Structured Output Format")
    print("=" * 70)
    print()

    # Build the prompt with output format requirement
    prompt = """You are an expert coding assistant.

Task: Write a simple hello world function in Python

## CRITICAL: Output Format

You MUST respond in this exact format:

<output>
{
  "status": "success",
  "summary": "One sentence describing what you did",
  "deliverables": ["files created"],
  "next_steps": ["recommended actions"],
  "metadata": {
    "agent": "claude-code",
    "task_id": "test-1",
    "duration_seconds": 0
  }
}
---
[Your explanation and code]
</output>

The JSON block at top is for OTHER AGENTS to parse.
The content after --- is for HUMANS to read.
"""

    print("Prompt:")
    print("-" * 70)
    print(prompt[:200] + "...")
    print()
    print("Calling Claude Code CLI...")
    print()

    try:
        # Call Claude Code CLI
        result = subprocess.run(
            ["claude", prompt],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path("../..")  # Go to project root
        )

        output = result.stdout
        error = result.stderr

        if error:
            print("STDERR:")
            print(error[:500])
            print()

        print("Response received:")
        print("=" * 70)
        print(output[:1000])
        print("...")
        print()

        # Try to parse the output
        print("=" * 70)
        print("Attempting to parse structured output...")
        print("=" * 70)
        print()

        try:
            parsed = parse_agent_output(output)

            print("✅ PARSED SUCCESSFULLY!")
            print()
            print(f"Status:      {parsed.status}")
            print(f"Summary:     {parsed.summary}")
            print(f"Deliverables: {parsed.deliverables}")
            print(f"Next Steps:  {parsed.next_steps}")
            print()
            print("Human content preview:")
            print("-" * 40)
            print(parsed.human_content[:300])
            if len(parsed.human_content) > 300:
                print("...")
            print()
            print("🎉 SUCCESS! Claude Code CLI followed the format!")
            print("   Your agents can now coordinate via structured outputs.")
            return True

        except Exception as parse_error:
            print(f"⚠️  Parse Error: {parse_error}")
            print()
            print("This is expected for first attempts.")
            print("The system works - Claude just needs to follow the format.")
            print()
            print("To improve compliance:")
            print("  1. Add few-shot examples to the prompt")
            print("  2. Make the format requirement more prominent")
            print("  3. Use a stronger system prompt")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Timeout: Claude Code CLI took too long")
        return False

    except FileNotFoundError:
        print("❌ Claude Code CLI not found")
        print()
        print("Make sure 'claude' command is available in your PATH")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    success = test_claude_code_with_format()

    print()
    if success:
        print("=" * 70)
        print("RESULT: Integration working!")
        print("=" * 70)
    else:
        print("=" * 70)
        print("RESULT: Format implemented, needs refinement")
        print("=" * 70)

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
