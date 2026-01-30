#!/usr/bin/env python3
"""
Context Budget Enforcement System for Agent-2.2

Monitors token usage and takes automatic actions at thresholds.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

# Default configuration
DEFAULT_CONFIG = {
    "max_tokens": 100000,
    "warning_threshold": 0.70,  # 70%
    "critical_threshold": 0.85,  # 85%
    "hard_limit": 0.95,  # 95%
    "actions": {
        "at_warning": {
            "action": "summarize_thoughts",
            "description": "Compress THOUGHTS.md to key points"
        },
        "at_critical": {
            "action": "spawn_subagent",
            "description": "Delegate remaining work to sub-agent"
        },
        "at_limit": {
            "action": "force_checkpoint_and_exit",
            "description": "Save state and exit with PARTIAL status"
        }
    }
}


def get_context_usage() -> Tuple[int, int]:
    """
    Get current context usage.
    Returns (used_tokens, max_tokens)
    """
    # In a real implementation, this would query the LLM API
    # For now, we estimate based on file sizes in the run directory
    # This is a placeholder - actual implementation would need API integration

    # Check if there's a context tracking file
    context_file = Path(os.environ.get("RALF_RUN_DIR", ".")) / ".context_usage"
    if context_file.exists():
        data = json.loads(context_file.read_text())
        return data.get("used", 0), data.get("max", DEFAULT_CONFIG["max_tokens"])

    return 0, DEFAULT_CONFIG["max_tokens"]


def calculate_thresholds(max_tokens: int) -> Dict[str, int]:
    """Calculate token thresholds."""
    return {
        "warning": int(max_tokens * DEFAULT_CONFIG["warning_threshold"]),
        "critical": int(max_tokens * DEFAULT_CONFIG["critical_threshold"]),
        "hard_limit": int(max_tokens * DEFAULT_CONFIG["hard_limit"]),
        "max": max_tokens
    }


def get_status(used: int, thresholds: Dict[str, int]) -> Tuple[str, float]:
    """
    Get current context status.
    Returns (status, percentage)
    """
    percentage = used / thresholds["max"]

    if used >= thresholds["hard_limit"]:
        return "HARD_LIMIT", percentage
    elif used >= thresholds["critical"]:
        return "CRITICAL", percentage
    elif used >= thresholds["warning"]:
        return "WARNING", percentage
    else:
        return "OK", percentage


def check_budget(run_dir: str) -> Dict:
    """
    Check context budget and return status.
    """
    used, max_tokens = get_context_usage()
    thresholds = calculate_thresholds(max_tokens)
    status, percentage = get_status(used, thresholds)

    result = {
        "used": used,
        "max": max_tokens,
        "percentage": percentage * 100,
        "status": status,
        "thresholds": thresholds,
        "action_required": None
    }

    # Determine if action is required
    if status == "HARD_LIMIT":
        result["action_required"] = DEFAULT_CONFIG["actions"]["at_limit"]
        result["must_exit"] = True
    elif status == "CRITICAL":
        result["action_required"] = DEFAULT_CONFIG["actions"]["at_critical"]
        result["must_exit"] = False
    elif status == "WARNING":
        result["action_required"] = DEFAULT_CONFIG["actions"]["at_warning"]
        result["must_exit"] = False

    return result


def format_status(result: Dict) -> str:
    """Format status for display."""
    lines = [
        f"Context Budget Status: {result['status']}",
        f"  Usage: {result['used']:,} / {result['max']:,} tokens ({result['percentage']:.1f}%)",
        f"  Thresholds:",
        f"    Warning:  {result['thresholds']['warning']:,} ({DEFAULT_CONFIG['warning_threshold']*100:.0f}%)",
        f"    Critical: {result['thresholds']['critical']:,} ({DEFAULT_CONFIG['critical_threshold']*100:.0f}%)",
        f"    Hard Limit: {result['thresholds']['hard_limit']:,} ({DEFAULT_CONFIG['hard_limit']*100:.0f}%)"
    ]

    if result.get("action_required"):
        action = result["action_required"]
        lines.append(f"")
        lines.append(f"  ACTION REQUIRED: {action['action']}")
        lines.append(f"  Description: {action['description']}")

    if result.get("must_exit"):
        lines.append(f"")
        lines.append(f"  ⚠️  MUST EXIT: Hard limit reached. Save checkpoint and exit with PARTIAL status.")

    return "\n".join(lines)


def init_budget(run_dir: str):
    """Initialize context budget tracking for a run."""
    budget_file = Path(run_dir) / ".context_budget"
    budget_data = {
        "max_tokens": DEFAULT_CONFIG["max_tokens"],
        "thresholds": {
            "warning": int(DEFAULT_CONFIG["max_tokens"] * DEFAULT_CONFIG["warning_threshold"]),
            "critical": int(DEFAULT_CONFIG["max_tokens"] * DEFAULT_CONFIG["critical_threshold"]),
            "hard_limit": int(DEFAULT_CONFIG["max_tokens"] * DEFAULT_CONFIG["hard_limit"])
        },
        "actions": DEFAULT_CONFIG["actions"]
    }
    budget_file.write_text(json.dumps(budget_data, indent=2))

    # Initialize usage tracking
    usage_file = Path(run_dir) / ".context_usage"
    usage_file.write_text(json.dumps({"used": 0, "max": DEFAULT_CONFIG["max_tokens"]}))

    print(f"✓ Context budget initialized")
    print(f"  Max tokens: {DEFAULT_CONFIG['max_tokens']:,}")
    print(f"  Warning at: {budget_data['thresholds']['warning']:,} ({DEFAULT_CONFIG['warning_threshold']*100:.0f}%)")
    print(f"  Critical at: {budget_data['thresholds']['critical']:,} ({DEFAULT_CONFIG['critical_threshold']*100:.0f}%)")
    print(f"  Hard limit at: {budget_data['thresholds']['hard_limit']:,} ({DEFAULT_CONFIG['hard_limit']*100:.0f}%)")


def update_usage(run_dir: str, tokens_used: int):
    """Update context usage."""
    usage_file = Path(run_dir) / ".context_usage"
    if usage_file.exists():
        data = json.loads(usage_file.read_text())
        data["used"] = tokens_used
        usage_file.write_text(json.dumps(data))


def main():
    if len(sys.argv) < 2:
        print("Usage: context_budget.py <command> [options]")
        print("Commands:")
        print("  init --run-dir <run_dir>")
        print("  check [--run-dir <run_dir>]")
        print("  update --tokens <count> --run-dir <run_dir>")
        sys.exit(1)

    command = sys.argv[1]

    # Parse arguments
    args = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i].startswith("--"):
            key = sys.argv[i][2:]
            if i + 1 < len(sys.argv):
                args[key] = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        else:
            i += 1

    run_dir = args.get("run-dir") or args.get("run_dir")

    if command == "init":
        if not run_dir:
            print("Error: --run-dir is required")
            sys.exit(1)
        init_budget(run_dir)

    elif command == "check":
        if not run_dir:
            run_dir = os.environ.get("RALF_RUN_DIR", ".")

        result = check_budget(run_dir)
        print(format_status(result))

        if result.get("must_exit"):
            sys.exit(2)  # Special exit code for hard limit
        elif result.get("action_required"):
            sys.exit(1)  # Action required but can continue
        else:
            sys.exit(0)

    elif command == "update":
        if not run_dir:
            print("Error: --run-dir is required")
            sys.exit(1)

        tokens = int(args.get("tokens", 0))
        update_usage(run_dir, tokens)
        print(f"Updated context usage: {tokens} tokens")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
