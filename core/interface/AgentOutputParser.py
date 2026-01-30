"""
Agent Output Parser for Blackbox5

Parses structured outputs from agents, extracting JSON metadata
for agent-to-agent communication while preserving human-readable content.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ParsedAgentOutput:
    """
    Parsed agent output with structured metadata and human content.

    Attributes:
        status: success, partial, or failed
        summary: One sentence summary
        deliverables: List of files/artifacts created
        next_steps: List of recommended actions
        metadata: Additional agent metadata
        human_content: Full explanation for humans (after ---)
        raw_output: Original complete output
    """
    status: str
    summary: str
    deliverables: List[str]
    next_steps: List[str]
    metadata: Dict[str, Any]
    human_content: str
    raw_output: str

    @property
    def is_success(self) -> bool:
        """Check if output indicates success."""
        return self.status == "success"

    @property
    def is_partial(self) -> bool:
        """Check if output indicates partial success."""
        return self.status == "partial"

    @property
    def is_failed(self) -> bool:
        """Check if output indicates failure."""
        return self.status == "failed"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status,
            "summary": self.summary,
            "deliverables": self.deliverables,
            "next_steps": self.next_steps,
            "metadata": self.metadata,
            "human_content": self.human_content,
        }


class AgentOutputParserError(Exception):
    """Raised when agent output cannot be parsed."""
    pass


def parse_agent_output(output: str) -> ParsedAgentOutput:
    """
    Parse agent output, extracting JSON metadata and human content.

    Expected format:
    ```markdown
    <output>
    {
      "status": "success|partial|failed",
      "summary": "One sentence",
      "deliverables": ["file1.ts"],
      "next_steps": ["action1"],
      "metadata": {...}
    }
    ---
    [Human-readable content]
    </output>
    ```

    Args:
        output: Raw output string from agent

    Returns:
        ParsedAgentOutput with structured data

    Raises:
        AgentOutputParserError: If output cannot be parsed

    Examples:
        >>> output = '''
        ... <output>
        ... {"status": "success", "summary": "Done", ...}
        ... ---
        ... Full explanation here...
        ... </output>
        ... '''
        >>> parsed = parse_agent_output(output)
        >>> print(parsed.status)
        'success'
        >>> print(parsed.deliverables)
        ['file1.ts']
    """
    if not output or not isinstance(output, str):
        raise AgentOutputParserError("Output must be a non-empty string")

    raw_output = output.strip()

    # Extract content between <output> tags (non-greedy, multiline)
    output_match = re.search(r'<output>([\s\S]*?)</output>', raw_output)

    if not output_match:
        raise AgentOutputParserError(
            "No <output> tags found. Agent must use the standard output format."
        )

    output_content = output_match.group(1).strip()

    # Split on --- to separate JSON from human content
    parts = output_content.split('---', 1)

    if len(parts) != 2:
        raise AgentOutputParserError(
            "Output must contain both JSON metadata and human content separated by ---"
        )

    json_part = parts[0].strip()
    human_content = parts[1].strip()

    # Parse JSON
    try:
        # Remove markdown code blocks if present
        json_part = re.sub(r'^```json\s*', '', json_part)
        json_part = re.sub(r'^```\s*', '', json_part)
        json_part = re.sub(r'\s*```$', '', json_part)

        data = json.loads(json_part)
    except json.JSONDecodeError as e:
        raise AgentOutputParserError(f"Invalid JSON in output: {e}") from e

    # Validate required fields
    required_fields = ["status", "summary", "deliverables", "next_steps", "metadata"]
    missing_fields = [f for f in required_fields if f not in data]

    if missing_fields:
        raise AgentOutputParserError(
            f"Missing required fields: {missing_fields}. Got: {list(data.keys())}"
        )

    # Validate status values
    valid_statuses = ["success", "partial", "failed"]
    if data["status"] not in valid_statuses:
        raise AgentOutputParserError(
            f"Invalid status: {data['status']}. Must be one of: {valid_statuses}"
        )

    # Ensure lists
    if not isinstance(data["deliverables"], list):
        data["deliverables"] = [data["deliverables"]]
    if not isinstance(data["next_steps"], list):
        data["next_steps"] = [data["next_steps"]]
    if not isinstance(data["metadata"], dict):
        raise AgentOutputParserError("metadata must be a dictionary")

    return ParsedAgentOutput(
        status=data["status"],
        summary=data["summary"],
        deliverables=data["deliverables"],
        next_steps=data["next_steps"],
        metadata=data["metadata"],
        human_content=human_content,
        raw_output=raw_output,
    )


def parse_agent_output_lax(output: str) -> Optional[ParsedAgentOutput]:
    """
    Parse agent output with lenient parsing.

    If standard format fails, attempts to extract what it can.
    Returns None if completely unparsable.

    Args:
        output: Raw output string from agent

    Returns:
        ParsedAgentOutput or None if completely unparsable
    """
    try:
        return parse_agent_output(output)
    except AgentOutputParserError:
        pass

    # Try to extract JSON even without proper tags
    try:
        # Look for JSON-like content
        json_match = re.search(r'\{[^{}]*"status"[^{}]*\}', output, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))

            # Fill in missing fields with defaults
            return ParsedAgentOutput(
                status=data.get("status", "partial"),
                summary=data.get("summary", "Output parsed with missing data"),
                deliverables=data.get("deliverables", []),
                next_steps=data.get("next_steps", []),
                metadata=data.get("metadata", {}),
                human_content=output,
                raw_output=output,
            )
    except (json.JSONDecodeError, ValueError):
        pass

    logger.warning("Could not parse agent output even with lax parsing")
    return None


def extract_status(output: str) -> str:
    """
    Quick extraction of status from agent output.

    Args:
        output: Raw output string

    Returns:
        Status: "success", "partial", "failed", or "unknown"
    """
    try:
        parsed = parse_agent_output(output)
        return parsed.status
    except AgentOutputParserError:
        # Try regex fallback
        status_match = re.search(r'"status"\s*:\s*"(\w+)"', output)
        if status_match:
            status = status_match.group(1)
            if status in ["success", "partial", "failed"]:
                return status
        return "unknown"


def extract_deliverables(output: str) -> List[str]:
    """
    Quick extraction of deliverables from agent output.

    Args:
        output: Raw output string

    Returns:
        List of deliverable filenames/artifacts
    """
    try:
        parsed = parse_agent_output(output)
        return parsed.deliverables
    except AgentOutputParserError:
        # Try regex fallback
        deliverables_match = re.search(
            r'"deliverables"\s*:\s*\[(.*?)\]',
            output,
            re.DOTALL
        )
        if deliverables_match:
            try:
                items = json.loads(f"[{deliverables_match.group(1)}]")
                return items if isinstance(items, list) else []
            except json.JSONDecodeError:
                pass
        return []


def extract_next_steps(output: str) -> List[str]:
    """
    Quick extraction of next steps from agent output.

    Args:
        output: Raw output string

    Returns:
        List of next step actions
    """
    try:
        parsed = parse_agent_output(output)
        return parsed.next_steps
    except AgentOutputParserError:
        # Try regex fallback
        steps_match = re.search(
            r'"next_steps"\s*:\s*\[(.*?)\]',
            output,
            re.DOTALL
        )
        if steps_match:
            try:
                items = json.loads(f"[{steps_match.group(1)}]")
                return items if isinstance(items, list) else []
            except json.JSONDecodeError:
                pass
        return []


def create_agent_output(
    status: str,
    summary: str,
    deliverables: List[str],
    next_steps: List[str],
    human_content: str,
    agent_name: str,
    task_id: str,
    duration_seconds: float = 0,
    **extra_metadata
) -> str:
    """
    Create a properly formatted agent output.

    Args:
        status: success, partial, or failed
        summary: One sentence summary
        deliverables: List of files/artifacts
        next_steps: List of next actions
        human_content: Full explanation for humans
        agent_name: Name of the agent
        task_id: Task identifier
        duration_seconds: Time taken
        **extra_metadata: Additional metadata fields

    Returns:
        Formatted output string

    Examples:
        >>> output = create_agent_output(
        ...     status="success",
        ...     summary="Created user API",
        ...     deliverables=["api/users.ts"],
        ...     next_steps=["test the endpoint"],
        ...     human_content="I implemented the user API...",
        ...     agent_name="coder",
        ...     task_id="task-123"
        ... )
        >>> print(output)
        <output>
        {"status": "success", ...}
        ---
        I implemented the user API...
        </output>
    """
    metadata = {
        "agent": agent_name,
        "task_id": task_id,
        "duration_seconds": duration_seconds,
        **extra_metadata
    }

    json_data = {
        "status": status,
        "summary": summary,
        "deliverables": deliverables,
        "next_steps": next_steps,
        "metadata": metadata
    }

    json_str = json.dumps(json_data, indent=2)

    return f"""<output>
{json_str}
---

{human_content}
</output>"""


def validate_agent_output(output: str) -> tuple:
    """
    Validate agent output format.

    Args:
        output: Raw output string

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    try:
        parsed = parse_agent_output(output)

        # Additional validation
        if not parsed.summary:
            errors.append("Summary cannot be empty")

        if parsed.status == "success" and not parsed.deliverables:
            errors.append("Success status should have deliverables")

        if parsed.duration_seconds < 0:
            errors.append("Duration cannot be negative")

    except AgentOutputParserError as e:
        errors.append(str(e))

    return (len(errors) == 0, errors)


# =============================================================================
# Convenience Functions for Agent Coordination
# =============================================================================

def handle_agent_response(
    response: str,
    on_success: callable,
    on_partial: callable = None,
    on_failed: callable = None
) -> Any:
    """
    Handle agent response based on status.

    Args:
        response: Agent output string
        on_success: Callback for success (receives ParsedAgentOutput)
        on_partial: Optional callback for partial success
        on_failed: Optional callback for failure

    Returns:
        Result from callback

    Examples:
        >>> def success_handler(parsed):
        ...     print(f"Created: {parsed.deliverables}")
        >>> def failure_handler(parsed):
        ...     print(f"Error: {parsed.metadata.get('error')}")
        >>> result = handle_agent_response(
        ...     agent_output,
        ...     on_success=success_handler,
        ...     on_failed=failure_handler
        ... )
    """
    parsed = parse_agent_output(response)

    if parsed.is_success and on_success:
        return on_success(parsed)
    elif parsed.is_partial and on_partial:
        return on_partial(parsed)
    elif parsed.is_failed and on_failed:
        return on_failed(parsed)
    elif parsed.is_success:
        return on_success(parsed)  # Default to success handler
    else:
        logger.warning(f"No handler for status: {parsed.status}")
        return None


def chain_agent_outputs(outputs: List[str]) -> Dict[str, Any]:
    """
    Aggregate results from multiple agent outputs.

    Args:
        outputs: List of agent output strings

    Returns:
        Aggregated results with combined deliverables, next_steps, etc.

    Examples:
        >>> results = chain_agent_outputs([output1, output2, output3])
        >>> print(results['all_deliverables'])
        ['file1.ts', 'file2.ts', 'file3.ts']
        >>> print(results['success_count'])
        2
    """
    all_deliverables = []
    all_next_steps = []
    success_count = 0
    partial_count = 0
    failed_count = 0
    errors = []

    for output in outputs:
        try:
            parsed = parse_agent_output(output)

            all_deliverables.extend(parsed.deliverables)
            all_next_steps.extend(parsed.next_steps)

            if parsed.is_success:
                success_count += 1
            elif parsed.is_partial:
                partial_count += 1
            else:
                failed_count += 1
                if "error" in parsed.metadata:
                    errors.append(parsed.metadata["error"])

        except AgentOutputParserError as e:
            failed_count += 1
            errors.append(str(e))

    return {
        "all_deliverables": list(set(all_deliverables)),  # Unique
        "all_next_steps": all_next_steps,
        "success_count": success_count,
        "partial_count": partial_count,
        "failed_count": failed_count,
        "total": len(outputs),
        "errors": errors,
        "overall_status": "success" if failed_count == 0 else "partial" if success_count > 0 else "failed"
    }
