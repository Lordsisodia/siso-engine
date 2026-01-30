#!/usr/bin/env python3
"""
Handoff with Context Script
Combines bash agent handoff with Swarm-style context variable system

This script integrates the existing agent-handoff.sh bash functionality
with Python-based context variables for more sophisticated agent handoffs.
"""

import sys
import json
import argparse
import importlib.util
from pathlib import Path
from typing import Any, Dict, Optional

# Add lib directory to path for imports
SCRIPT_DIR = Path(__file__).parent.parent
LIB_DIR = SCRIPT_DIR / "lib"
CONTEXT_VARS_DIR = LIB_DIR / "context-variables"

# Import context variables modules directly to avoid naming conflicts
def import_context_modules():
    """Import context variables modules with direct loading"""
    # Load context.py
    spec = importlib.util.spec_from_file_location(
        "bb4_context",
        CONTEXT_VARS_DIR / "context.py"
    )
    context_module = importlib.util.module_from_spec(spec)
    sys.modules['bb4_context'] = context_module
    spec.loader.exec_module(context_module)

    # Load handoff_context.py
    spec2 = importlib.util.spec_from_file_location(
        "bb4_handoff_context",
        CONTEXT_VARS_DIR / "handoff_context.py"
    )
    handoff_module = importlib.util.module_from_spec(spec2)
    sys.modules['bb4_handoff_context'] = handoff_module
    spec2.loader.exec_module(handoff_module)

    return context_module, handoff_module

try:
    context_module, handoff_module = import_context_modules()
    Context = context_module.Context  # Alias for AgentContext
    HandoffContextRaw = handoff_module.HandoffContext
except Exception as e:
    print(f"Error importing context modules: {e}")
    import traceback
    traceback.print_exc()
    print("Ensure the lib/context-variables module is properly installed")
    sys.exit(1)


def HandoffContext(from_agent, to_agent, context_vars=None, message="Handing off work"):
    """
    Wrapper for HandoffContext that injects AgentContext to avoid import issues
    """
    return HandoffContextRaw(
        from_agent=from_agent,
        to_agent=to_agent,
        context_vars=context_vars,
        message=message,
        AgentContext=context_module.AgentContext,
        context_var=context_module.context_var
    )


def handoff_with_context(
    from_agent: str,
    to_agent: str,
    context_vars: Dict[str, Any],
    message: str = "Handing off work",
    context_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute agent handoff with context variables

    Args:
        from_agent: Source agent name
        to_agent: Target agent name
        context_vars: Dictionary of context variables to transfer
        message: Handoff message
        context_dir: Optional context directory path

    Returns:
        Handoff result dictionary
    """
    print(f"[INFO] Initiating handoff: {from_agent} -> {to_agent}")
    print(f"[DEBUG] Context variables: {len(context_vars)} items")

    # Create handoff context
    handoff = HandoffContext(
        from_agent=from_agent,
        to_agent=to_agent,
        context_vars=context_vars,
        message=message
    )

    # Save context file for reference
    try:
        context_file = handoff.save_context_file()
        print(f"[INFO] Context saved: {context_file}")
    except Exception as e:
        print(f"[WARN] Could not save context file: {e}")

    # Execute handoff via bash script
    result = handoff.execute_handoff(context_dir=context_dir)

    if result.get("success"):
        print(f"[SUCCESS] Handoff completed: {from_agent} -> {to_agent}")
        if "bash_output" in result:
            print(result["bash_output"])
    else:
        print(f"[ERROR] Handoff failed: {result.get('error', 'Unknown error')}")
        if "stderr" in result:
            print(f"[STDERR] {result['stderr']}")

    return result


def load_agent(agent_name: str) -> Dict[str, Any]:
    """
    Load agent configuration from Blackbox4 structure

    Args:
        agent_name: Name of agent to load

    Returns:
        Agent configuration dictionary with:
        - name: Agent name
        - exists: Boolean indicating if agent was found
        - path: Path to agent directory (if exists)
        - config: Agent config YAML (if exists)
        - prompt: Agent prompt content (if exists)
        - error: Error message (if not found)
    """
    script_dir = Path(__file__).parent.parent
    agents_dir = script_dir.parent / "1-agents"

    print(f"[INFO] Loading agent: {agent_name}")

    # Check all agent categories
    categories = ["1-core", "2-bmad", "3-research", "4-specialists", "5-enhanced"]

    for category in categories:
        agent_path = agents_dir / category / agent_name

        if agent_path.exists():
            print(f"[INFO] Found agent in: {category}")

            agent_info = {
                "name": agent_name,
                "category": category,
                "path": str(agent_path),
                "exists": True
            }

            # Load agent.yaml if present
            config_file = agent_path / "agent.yaml"
            if config_file.exists():
                try:
                    import yaml
                    with open(config_file, 'r') as f:
                        agent_info["config"] = yaml.safe_load(f)
                    print(f"[INFO] Loaded config: {config_file}")
                except Exception as e:
                    print(f"[WARN] Could not load config: {e}")
                    agent_info["config"] = None

            # Load prompt.md if present
            prompt_file = agent_path / "prompt.md"
            if prompt_file.exists():
                try:
                    with open(prompt_file, 'r') as f:
                        agent_info["prompt"] = f.read()
                    print(f"[INFO] Loaded prompt: {prompt_file}")
                except Exception as e:
                    print(f"[WARN] Could not load prompt: {e}")
                    agent_info["prompt"] = None

            return agent_info

    # Agent not found
    print(f"[WARN] Agent not found: {agent_name}")
    return {
        "name": agent_name,
        "exists": False,
        "error": f"Agent '{agent_name}' not found in any category"
    }


def interactive_handoff():
    """Run interactive handoff wizard"""
    print("\n" + "="*60)
    print("Blackbox4 Agent Handoff with Context")
    print("="*60 + "\n")

    # Get from agent
    from_agent = input("Source agent name: ").strip()
    if not from_agent:
        print("[ERROR] Source agent name required")
        return

    # Get to agent
    to_agent = input("Target agent name: ").strip()
    if not to_agent:
        print("[ERROR] Target agent name required")
        return

    # Get message
    message = input("Handoff message (default: 'Handing off work'): ").strip()
    if not message:
        message = "Handing off work"

    # Collect context variables
    print("\n--- Context Variables ---")
    print("Enter context variables (key=value, empty line to finish):\n")

    context_vars = {}
    while True:
        var_input = input("var> ").strip()
        if not var_input:
            break

        if '=' in var_input:
            key, value = var_input.split('=', 1)
            key = key.strip()
            value = value.strip()

            # Try to parse as JSON for complex types
            try:
                context_vars[key] = json.loads(value)
            except json.JSONDecodeError:
                context_vars[key] = value

            print(f"  Set: {key} = {context_vars[key]}")
        else:
            print("[WARN] Invalid format (use key=value)")

    # Show summary
    print("\n--- Handoff Summary ---")
    print(f"From: {from_agent}")
    print(f"To: {to_agent}")
    print(f"Message: {message}")
    print(f"Context variables: {len(context_vars)}")
    for key, value in context_vars.items():
        print(f"  - {key}: {value}")

    # Confirm
    confirm = input("\nExecute handoff? (y/n): ").strip().lower()
    if confirm == 'y':
        result = handoff_with_context(
            from_agent=from_agent,
            to_agent=to_agent,
            context_vars=context_vars,
            message=message
        )

        if result.get("success"):
            print("\n[SUCCESS] Handoff completed!")
        else:
            print(f"\n[ERROR] Handoff failed: {result.get('error')}")
    else:
        print("[INFO] Handoff cancelled")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Blackbox4 Agent Handoff with Context",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  %(prog)s --interactive

  # Direct handoff with context
  %(prog)s handoff agent-1 agent-2 \\
      --context '{"task": "design", "status": "complete"}' \\
      --message "Design phase complete"

  # Load agent info
  %(prog)s load-agent architect

  # Handoff with context file
  %(prog)s handoff planner dev \\
      --context-file /path/to/context.json

  # Test import
  %(prog)s test-import
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Handoff command
    handoff_parser = subparsers.add_parser('handoff', help='Execute agent handoff')
    handoff_parser.add_argument('from_agent', help='Source agent name')
    handoff_parser.add_argument('to_agent', help='Target agent name')
    handoff_parser.add_argument(
        '--context',
        help='Context variables as JSON string',
        default='{}'
    )
    handoff_parser.add_argument(
        '--context-file',
        help='Load context from JSON file'
    )
    handoff_parser.add_argument(
        '--message',
        help='Handoff message',
        default='Handing off work'
    )
    handoff_parser.add_argument(
        '--context-dir',
        help='Additional context directory path'
    )

    # Load agent command
    load_parser = subparsers.add_parser('load-agent', help='Load agent configuration')
    load_parser.add_argument('agent_name', help='Agent name to load')

    # Interactive command
    subparsers.add_parser('interactive', help='Interactive handoff wizard')

    # Test import command
    subparsers.add_parser('test-import', help='Test context module imports')

    args = parser.parse_args()

    # Handle commands
    if args.command == 'handoff':
        # Load context
        if args.context_file:
            try:
                with open(args.context_file, 'r') as f:
                    context_vars = json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load context file: {e}")
                sys.exit(1)
        else:
            try:
                context_vars = json.loads(args.context)
            except json.JSONDecodeError as e:
                print(f"[ERROR] Invalid JSON in context: {e}")
                sys.exit(1)

        # Execute handoff
        result = handoff_with_context(
            from_agent=args.from_agent,
            to_agent=args.to_agent,
            context_vars=context_vars,
            message=args.message,
            context_dir=args.context_dir
        )

        sys.exit(0 if result.get("success") else 1)

    elif args.command == 'load-agent':
        agent_info = load_agent(args.agent_name)

        print("\n--- Agent Information ---")
        print(json.dumps(agent_info, indent=2, default=str))

        sys.exit(0 if agent_info.get("exists") else 1)

    elif args.command == 'interactive':
        interactive_handoff()

    elif args.command == 'test-import':
        print("Testing context module imports...")
        print(f"Context: {Context}")
        print(f"HandoffContext: {HandoffContextRaw}")
        print(f"AgentContext: {context_module.AgentContext}")
        print(f"context_var: {context_module.context_var}")
        print("\nAll imports successful!")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
