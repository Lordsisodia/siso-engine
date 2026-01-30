#!/usr/bin/env python3
"""
Add output format section to all agent.md files in Blackbox5.
Run this script to update all agent.md files with the output format specification.
"""

import re
from pathlib import Path

# The output format section to add to each agent.md
OUTPUT_FORMAT_SECTION = """

## Output Format

This agent follows the Blackbox5 output format specification for agent-to-agent communication.

Every response MUST use this exact format:

```markdown
<output>
{
  "status": "success|partial|failed",
  "summary": "One sentence describing what you did",
  "deliverables": ["file1.ts", "file2.ts", "artifact-name"],
  "next_steps": ["action1", "action2"],
  "metadata": {
    "agent": "your-agent-name",
    "task_id": "from-input",
    "duration_seconds": 0
  }
}

---
[Your full explanation here - code, reasoning, details for humans]
</output>
```

**CRITICAL:**
- The JSON block at top (inside `<output>` tags) is for OTHER AGENTS to parse
- The content after `---` is for HUMANS to read
- Always include both parts - this enables agent coordination
- The status must be exactly: `success`, `partial`, or `failed`
"""

# Pattern to find where to insert the output format section
# Insert before the first ## section after the header, or before ## Example if it exists
INSERT_PATTERN = r'(## Success Criteria|## Example|## Example Workflow)'


def add_output_format_to_agent_file(file_path: Path) -> bool:
    """Add output format section to a single agent.md file."""
    try:
        content = file_path.read_text(encoding='utf-8')

        # Check if output format section already exists
        if '## Output Format' in content:
            print(f"  ✓ {file_path.name}: Already has Output Format section")
            return False

        # Find insertion point (before Success Criteria or Example)
        match = re.search(INSERT_PATTERN, content)

        if match:
            # Insert before the matched section
            insert_pos = match.start()
            new_content = content[:insert_pos] + OUTPUT_FORMAT_SECTION + '\n' + content[insert_pos:]
        else:
            # Append to end if no match found
            new_content = content + OUTPUT_FORMAT_SECTION

        # Write back
        file_path.write_text(new_content, encoding='utf-8')
        print(f"  ✓ {file_path.name}: Added Output Format section")
        return True

    except Exception as e:
        print(f"  ✗ {file_path.name}: Error - {e}")
        return False


def main():
    """Find and update all agent.md files."""
    # Base directory - navigate from script location
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent / "02-agents/implementations"

    if not base_dir.exists():
        print(f"Error: Directory not found: {base_dir}")
        print(f"Script dir: {script_dir}")
        print(f"Looking for: {script_dir.parent.parent}/02-agents/implementations")
        return

    # Find all agent.md files
    agent_files = list(base_dir.rglob("agent.md"))

    print(f"Found {len(agent_files)} agent.md files")
    print(f"Base directory: {base_dir}")
    print()

    updated_count = 0
    for agent_file in agent_files:
        if add_output_format_to_agent_file(agent_file):
            updated_count += 1

    print()
    print(f"Updated {updated_count}/{len(agent_files)} files")


if __name__ == "__main__":
    main()
