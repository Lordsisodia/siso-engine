#!/usr/bin/env python3
"""
Context Budget Management for RALF

Tracks and enforces context usage thresholds with automatic actions.
Part of Agent-2.3 context budget enforcement system.

Thresholds:
- Sub-agent: 40% (80,000 tokens) - NEW: Delegate to sub-agent
- Warning: 70% (140,000 tokens) - Summarize THOUGHTS.md
- Critical: 85% (170,000 tokens) - Spawn sub-agent
- Hard limit: 95% (190,000 tokens) - Force checkpoint and exit
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Callable
import logging

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_MAX_TOKENS = 200000
DEFAULT_THRESHOLDS = {
    "subagent": 40,      # 40% - Early delegation threshold
    "warning": 70,       # 70% - Warning threshold
    "critical": 85,      # 85% - Critical threshold
    "hard_limit": 95     # 95% - Hard stop
}


@dataclass
class BudgetState:
    """Current state of context budget."""
    current_tokens: int
    max_tokens: int
    percentage: float
    threshold_triggered: Optional[str] = None
    action_taken: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            from datetime import timezone
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class ThresholdAction:
    """Action to take when threshold is reached."""
    name: str
    description: str
    callback: Optional[Callable] = None


class ContextBudget:
    """
    Manages context budget with automatic threshold actions.

    Usage:
        budget = ContextBudget(max_tokens=200000, subagent_threshold=40)
        state = budget.check_usage(current_tokens=85000)
        if state.threshold_triggered:
            budget.execute_action(state.threshold_triggered)
    """

    def __init__(
        self,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        thresholds: Optional[Dict[str, int]] = None,
        run_dir: Optional[Path] = None,
        state_file: Optional[str] = None
    ):
        """
        Initialize context budget manager.

        Args:
            max_tokens: Maximum token budget (default: 200000)
            thresholds: Custom thresholds as {name: percentage}
            run_dir: Directory for state files
            state_file: Path to budget state file
        """
        self.max_tokens = max_tokens
        self.thresholds = thresholds or DEFAULT_THRESHOLDS.copy()
        self.run_dir = Path(run_dir) if run_dir else None
        self.state_file = state_file or "context_budget.json"
        self.triggered_thresholds: set = set()

        # Define default actions for each threshold
        self.actions: Dict[str, ThresholdAction] = {
            "subagent": ThresholdAction(
                name="spawn_subagent",
                description="Delegate work to sub-agent to preserve main agent context"
            ),
            "warning": ThresholdAction(
                name="summarize_thoughts",
                description="Compress THOUGHTS.md to key points"
            ),
            "critical": ThresholdAction(
                name="spawn_subagent_critical",
                description="Spawn sub-agent for remaining work"
            ),
            "hard_limit": ThresholdAction(
                name="force_checkpoint",
                description="Save state and exit with PARTIAL status"
            )
        }

        # Track if we've already spawned a sub-agent
        self.subagent_spawned = False

    def check_usage(self, current_tokens: int) -> BudgetState:
        """
        Check current usage against budget and thresholds.

        Args:
            current_tokens: Current token count

        Returns:
            BudgetState with current status and any triggered threshold
        """
        percentage = (current_tokens / self.max_tokens) * 100

        # Determine which threshold we're at
        triggered = None

        # Check thresholds in order of severity
        if percentage >= self.thresholds["hard_limit"]:
            triggered = "hard_limit"
        elif percentage >= self.thresholds["critical"]:
            triggered = "critical"
        elif percentage >= self.thresholds["warning"]:
            triggered = "warning"
        elif percentage >= self.thresholds["subagent"]:
            triggered = "subagent"

        state = BudgetState(
            current_tokens=current_tokens,
            max_tokens=self.max_tokens,
            percentage=round(percentage, 2),
            threshold_triggered=triggered
        )

        # Save state if run_dir is set
        if self.run_dir:
            self._save_state(state)

        return state

    def should_spawn_subagent(self, current_tokens: int) -> bool:
        """
        Check if we should spawn a sub-agent at current usage.

        Args:
            current_tokens: Current token count

        Returns:
            True if sub-agent should be spawned
        """
        percentage = (current_tokens / self.max_tokens) * 100

        # Spawn sub-agent at 40% if not already done
        if percentage >= self.thresholds["subagent"] and not self.subagent_spawned:
            return True

        return False

    def mark_subagent_spawned(self):
        """Mark that a sub-agent has been spawned."""
        self.subagent_spawned = True
        if self.run_dir:
            flag_file = self.run_dir / ".subagent_spawned"
            flag_file.touch()

    def is_subagent_spawned(self) -> bool:
        """Check if sub-agent has already been spawned."""
        if self.subagent_spawned:
            return True

        # Check flag file
        if self.run_dir:
            flag_file = self.run_dir / ".subagent_spawned"
            return flag_file.exists()

        return False

    def execute_action(self, threshold: str) -> str:
        """
        Execute the action for a triggered threshold.

        Args:
            threshold: Name of triggered threshold

        Returns:
            Description of action taken
        """
        if threshold in self.triggered_thresholds:
            return f"Action for {threshold} already executed"

        self.triggered_thresholds.add(threshold)
        action = self.actions.get(threshold)

        if not action:
            return f"No action defined for threshold: {threshold}"

        # Execute callback if defined
        if action.callback:
            try:
                action.callback()
            except Exception as e:
                logger.error(f"Action callback failed for {threshold}: {e}")

        # Special handling for sub-agent spawning
        if threshold == "subagent":
            self.mark_subagent_spawned()

        return action.description

    def get_recommendation(self, state: BudgetState) -> str:
        """
        Get human-readable recommendation based on state.

        Args:
            state: Current budget state

        Returns:
            Recommendation string
        """
        if not state.threshold_triggered:
            return f"Context usage at {state.percentage:.1f}%. Continue normally."

        actions = {
            "subagent": (
                f"Context at {state.percentage:.1f}% (threshold: {self.thresholds['subagent']}%).\n"
                "Recommendation: Delegate remaining work to a sub-agent.\n"
                "The main agent should summarize current state and spawn a sub-agent."
            ),
            "warning": (
                f"Context at {state.percentage:.1f}% (threshold: {self.thresholds['warning']}%).\n"
                "Recommendation: Compress THOUGHTS.md to key points.\n"
                "Remove detailed reasoning, keep only decisions and next steps."
            ),
            "critical": (
                f"Context at {state.percentage:.1f}% (threshold: {self.thresholds['critical']}%).\n"
                "Recommendation: URGENT - Spawn sub-agent immediately.\n"
                "Main agent context is nearly exhausted."
            ),
            "hard_limit": (
                f"Context at {state.percentage:.1f}% (threshold: {self.thresholds['hard_limit']}%).\n"
                "ACTION REQUIRED: Force checkpoint and exit with PARTIAL status.\n"
                "Cannot proceed without risking context overflow."
            )
        }

        return actions.get(state.threshold_triggered, "Unknown threshold triggered")

    def _save_state(self, state: BudgetState):
        """Save budget state to file."""
        if not self.run_dir:
            return

        self.run_dir.mkdir(parents=True, exist_ok=True)
        state_path = self.run_dir / self.state_file

        # Load existing history
        history = []
        if state_path.exists():
            try:
                with open(state_path) as f:
                    data = json.load(f)
                    history = data.get("history", [])
            except Exception:
                pass

        # Add current state to history
        history.append(asdict(state))

        # Save updated state
        with open(state_path, 'w') as f:
            json.dump({
                "config": {
                    "max_tokens": self.max_tokens,
                    "thresholds": self.thresholds
                },
                "current": asdict(state),
                "history": history[-20:]  # Keep last 20 entries
            }, f, indent=2)

    def create_subagent_context(
        self,
        task_description: str,
        current_progress: str,
        files_context: Optional[List[str]] = None
    ) -> str:
        """
        Create compressed context for sub-agent delegation.

        This creates a minimal context that includes only what's needed
        for the sub-agent to continue work, preserving the main agent's
        context budget.

        Args:
            task_description: Description of remaining work
            current_progress: Summary of progress so far
            files_context: List of relevant file paths

        Returns:
            Compressed context string for sub-agent
        """
        context_parts = [
            "# Sub-Agent Delegation Context",
            "",
            "## Task",
            task_description,
            "",
            "## Progress So Far",
            current_progress,
            "",
        ]

        if files_context:
            context_parts.extend([
                "## Relevant Files",
                ""
            ])
            for f in files_context:
                context_parts.append(f"- {f}")
            context_parts.append("")

        context_parts.extend([
            "## Instructions",
            "1. You are a sub-agent spawned to complete specific work.",
            "2. Focus ONLY on the task described above.",
            "3. Report back with: COMPLETE, PARTIAL, or BLOCKED.",
            "4. Do not repeat work already done (see Progress).",
            "5. Preserve context by being concise.",
            ""
        ])

        return "\n".join(context_parts)

    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimate of token count for text.

        This is a simple approximation (1 token ≈ 4 characters).
        For accurate counts, use tiktoken or similar.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4


def main():
    """CLI interface for context budget management."""
    parser = argparse.ArgumentParser(
        description="Context Budget Management for RALF"
    )
    parser.add_argument(
        "command",
        choices=["init", "check", "recommend", "subagent-context"],
        help="Command to execute"
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        help="Run directory for state files"
    )
    parser.add_argument(
        "--tokens",
        type=int,
        help="Current token count (for check command)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Maximum token budget (default: {DEFAULT_MAX_TOKENS})"
    )
    parser.add_argument(
        "--subagent-threshold",
        type=int,
        default=40,
        help="Sub-agent delegation threshold percentage (default: 40)"
    )
    parser.add_argument(
        "--warning-threshold",
        type=int,
        default=70,
        help="Warning threshold percentage (default: 70)"
    )
    parser.add_argument(
        "--critical-threshold",
        type=int,
        default=85,
        help="Critical threshold percentage (default: 85)"
    )
    parser.add_argument(
        "--hard-limit",
        type=int,
        default=95,
        help="Hard limit threshold percentage (default: 95)"
    )
    parser.add_argument(
        "--task",
        help="Task description (for subagent-context command)"
    )
    parser.add_argument(
        "--progress",
        help="Current progress (for subagent-context command)"
    )

    args = parser.parse_args()

    # Build thresholds from arguments
    thresholds = {
        "subagent": args.subagent_threshold,
        "warning": args.warning_threshold,
        "critical": args.critical_threshold,
        "hard_limit": args.hard_limit
    }

    budget = ContextBudget(
        max_tokens=args.max_tokens,
        thresholds=thresholds,
        run_dir=args.run_dir
    )

    if args.command == "init":
        # Initialize budget tracking
        state = budget.check_usage(0)
        print(f"Context budget initialized:")
        print(f"  Max tokens: {args.max_tokens:,}")
        print(f"  Sub-agent threshold: {thresholds['subagent']}% ({int(args.max_tokens * thresholds['subagent'] / 100):,} tokens)")
        print(f"  Warning threshold: {thresholds['warning']}% ({int(args.max_tokens * thresholds['warning'] / 100):,} tokens)")
        print(f"  Critical threshold: {thresholds['critical']}% ({int(args.max_tokens * thresholds['critical'] / 100):,} tokens)")
        print(f"  Hard limit: {thresholds['hard_limit']}% ({int(args.max_tokens * thresholds['hard_limit'] / 100):,} tokens)")

        if args.run_dir:
            print(f"  State file: {args.run_dir / budget.state_file}")

    elif args.command == "check":
        if args.tokens is None:
            print("Error: --tokens required for check command", file=sys.stderr)
            sys.exit(1)

        state = budget.check_usage(args.tokens)

        print(json.dumps({
            "current_tokens": state.current_tokens,
            "max_tokens": state.max_tokens,
            "percentage": state.percentage,
            "threshold_triggered": state.threshold_triggered,
            "subagent_recommended": budget.should_spawn_subagent(args.tokens),
            "subagent_already_spawned": budget.is_subagent_spawned()
        }, indent=2))

        # Exit with non-zero if hard limit reached
        if state.threshold_triggered == "hard_limit":
            sys.exit(2)
        elif state.threshold_triggered == "critical":
            sys.exit(3)

    elif args.command == "recommend":
        if args.tokens is None:
            print("Error: --tokens required for recommend command", file=sys.stderr)
            sys.exit(1)

        state = budget.check_usage(args.tokens)
        print(budget.get_recommendation(state))

    elif args.command == "subagent-context":
        if not args.task:
            print("Error: --task required for subagent-context command", file=sys.stderr)
            sys.exit(1)

        context = budget.create_subagent_context(
            task_description=args.task,
            current_progress=args.progress or "Work started, context delegated to sub-agent.",
            files_context=[]
        )
        print(context)


if __name__ == "__main__":
    main()
