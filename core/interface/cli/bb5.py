#!/usr/bin/env python3
"""
Blackbox 5 CLI - Multi-Agent Orchestration System

Usage:
    bb5 ask "What is 2+2?"
    bb5 ask --agent testing-agent "Write tests"
    bb5 inspect orchestrator
    bb5 agents
    bb5 skills
    bb5 guide "test this code"
"""

import sys
import asyncio
import json
from pathlib import Path
from typing import Optional

import click

# Add engine directory to path to import main
engine_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(engine_dir))
sys.path.insert(0, str(engine_dir / "infrastructure"))

from main import get_blackbox5


@click.group()
@click.version_option(version="5.0.0", prog_name="bb5")
def cli():
    """Blackbox 5 - Multi-Agent Orchestration System"""
    pass


@cli.command()
@click.argument("query", required=True)
@click.option("--session", "-s", help="Session ID for continuity")
@click.option("--agent", "-a", help="Force specific agent")
@click.option("--strategy", "-st",
              type=click.Choice(['auto', 'single_agent', 'multi_agent']),
              default='auto',
              help='Execution strategy')
@click.option("--json", "-j", "as_json", is_flag=True, help="Output as JSON")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def ask(query: str, session: Optional[str], agent: Optional[str],
        strategy: str, as_json: bool, verbose: bool):
    """
    Ask Blackbox 5 a question or give it a task.

    Examples:
        bb5 ask "What is 2+2?"
        bb5 ask --agent testing-agent "Write tests"
        bb5 ask --strategy multi_agent "Design system"
        bb5 ask --session abc123 "Follow-up"
        bb5 ask --json "Output as JSON"
    """
    asyncio.run(_handle_ask(query, session, agent, strategy, as_json, verbose))


async def _handle_ask(query: str, session: Optional[str], agent: Optional[str],
                      strategy: str, as_json: bool, verbose: bool):
    """Handle the ask command asynchronously."""
    try:
        # Import safety checks
        import sys
        from pathlib import Path
        safety_dir = Path(__file__).parent.parent.parent / "safety"
        sys.path.insert(0, str(safety_dir))
        from kill_switch import get_kill_switch
        from constitutional_classifier import get_classifier, ContentType

        # 1. Check kill switch
        ks = get_kill_switch()
        if not ks.is_operational():
            click.echo(f"❌ Kill switch has been triggered", err=True)
            click.echo(f"   Reason: {ks.trigger_reason.value if ks.trigger_reason else 'Unknown'}", err=True)
            click.echo(f"   Message: {ks.trigger_message or 'No message'}", err=True)
            click.echo(f"\n   System is in emergency shutdown mode.", err=True)
            click.echo(f"   Use 'bb5 recover' to resume operations.", err=True)
            sys.exit(1)

        # 2. Check safe mode
        from safe_mode import get_safe_mode
        sm = get_safe_mode()
        if sm.is_safe_mode():
            click.echo(f"⚠️  System is in {sm.current_level.value.upper()} mode", err=True)
            click.echo(f"   Reason: {sm.enter_reason or 'Unknown'}", err=True)
            if not sm.is_operation_allowed("agent_execution"):
                click.echo(f"\n   ❌ Agent execution is not allowed in current mode", err=True)
                click.echo(f"   Allowed operations: {sm.get_limits()['allowed_operations']}", err=True)
                sys.exit(1)

        # 3. Validate input
        classifier = get_classifier()
        input_check = classifier.check_input(query, ContentType.USER_INPUT)
        if not input_check.safe:
            click.echo(f"❌ Input blocked by safety check", err=True)
            click.echo(f"   Reason: {input_check.violation.reason}", err=True)
            click.echo(f"   Violation Type: {input_check.violation.violation_type.value}", err=True)
            if input_check.should_trigger_kill_switch:
                click.echo(f"\n   ⚠️  This violation has been logged and may trigger safety measures.", err=True)
            sys.exit(1)

        # Get Blackbox5 instance
        bb5 = await get_blackbox5()

        # Build context
        context = {}
        if agent:
            context['forced_agent'] = agent
        if strategy != 'auto':
            context['strategy'] = strategy

        # Process request
        click.echo(f"Processing request...", err=True)
        result = await bb5.process_request(query, session, context)

        # 4. Validate output
        if isinstance(result, dict) and 'result' in result:
            result_output = result['result'].get('output', '')
            if isinstance(result_output, str):
                output_check = classifier.check_output(result_output, ContentType.AGENT_OUTPUT)
                if not output_check.safe:
                    click.echo(f"❌ Output blocked by safety check", err=True)
                    click.echo(f"   Reason: {output_check.violation.reason}", err=True)
                    click.echo(f"\n   The agent's response was blocked for safety reasons.", err=True)
                    sys.exit(1)

        # Output result
        if as_json:
            _output_json(result)
        else:
            _output_human_readable(result, verbose)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _output_human_readable(result: dict, verbose: bool):
    """Output result in human-readable format."""
    routing = result.get('routing', {})

    click.echo(f"\n{'='*70}")
    click.echo(f"Strategy: {routing.get('strategy', 'N/A')}")
    click.echo(f"Agent: {routing.get('agent', 'N/A')}")
    click.echo(f"Complexity: {routing.get('complexity', 0):.2f}")
    if verbose and routing.get('confidence'):
        click.echo(f"Confidence: {routing.get('confidence', 0):.2f}")
    click.echo(f"{'='*70}\n")

    # Show result
    result_data = result.get('result', {})
    if result_data.get('success'):
        click.echo("Result:")
        output = result_data.get('output', '')
        if output:
            click.echo(output)

        # Show artifacts if any
        artifacts = result_data.get('artifacts', {})
        if artifacts and verbose:
            click.echo(f"\nArtifacts:")
            for key, value in artifacts.items():
                click.echo(f"  • {key}: {value}")

        # Show metadata if verbose
        if verbose and result_data.get('metadata'):
            click.echo(f"\nMetadata:")
            for key, value in result_data['metadata'].items():
                click.echo(f"  • {key}: {value}")
    else:
        click.echo("Error:", err=True)
        error = result_data.get('error', 'Unknown error')
        click.echo(f"  {error}", err=True)

    # Show guide suggestions
    suggestions = result.get('guide_suggestions', [])
    if suggestions:
        click.echo(f"\nSuggested Actions:")
        for suggestion in suggestions:
            title = suggestion.get('title', '')
            description = suggestion.get('description', '')
            if title:
                click.echo(f"  • {title}")
                if description and verbose:
                    click.echo(f"    {description}")
            elif description:
                click.echo(f"  • {description}")

    # Show session info
    if verbose:
        click.echo(f"\nSession: {result.get('session_id', 'N/A')}")
        click.echo(f"Time: {result.get('timestamp', 'N/A')}")


def _output_json(result: dict):
    """Output result as JSON."""
    click.echo(json.dumps(result, indent=2))


@cli.command()
@click.argument("agent_name", required=True)
@click.option("--json", "-j", "as_json", is_flag=True, help="Output as JSON")
def inspect(agent_name: str, as_json: bool):
    """
    Show agent details.

    Examples:
        bb5 inspect orchestrator
        bb5 inspect testing-agent
    """
    asyncio.run(_handle_inspect(agent_name, as_json))


async def _handle_inspect(agent_name: str, as_json: bool):
    """Handle the inspect command asynchronously."""
    try:
        bb5 = await get_blackbox5()

        agent = bb5._agents.get(agent_name)
        if not agent:
            click.echo(f"Error: Agent '{agent_name}' not found", err=True)
            click.echo("\nAvailable agents:")
            for name in bb5._agents.keys():
                click.echo(f"  • {name}")
            sys.exit(1)

        if as_json:
            agent_info = {
                "name": agent_name,
                "role": agent.role,
                "category": agent.category,
                "description": agent.config.description,
                "capabilities": agent.config.capabilities,
                "tools": agent.config.tools,
                "full_name": agent.config.full_name
            }
            click.echo(json.dumps(agent_info, indent=2))
        else:
            click.echo(f"\n{'='*70}")
            click.echo(f"Agent: {agent_name}")
            click.echo(f"{'='*70}")
            click.echo(f"Full Name: {agent.config.full_name}")
            click.echo(f"Role: {agent.role}")
            click.echo(f"Category: {agent.category}")
            click.echo(f"\nDescription:")
            click.echo(f"  {agent.config.description}")
            click.echo(f"\nCapabilities:")
            for cap in agent.config.capabilities:
                click.echo(f"  • {cap}")
            if agent.config.tools:
                click.echo(f"\nTools: {len(agent.config.tools)} available")
            click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--json", "-j", "as_json", is_flag=True, help="Output as JSON")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def agents(as_json: bool, verbose: bool):
    """
    List all available agents.

    Examples:
        bb5 agents
        bb5 agents --json
        bb5 agents --verbose
    """
    asyncio.run(_handle_agents(as_json, verbose))


async def _handle_agents(as_json: bool, verbose: bool):
    """Handle the agents command asynchronously."""
    try:
        bb5 = await get_blackbox5()

        if as_json:
            agents_list = []
            for name, agent in bb5._agents.items():
                agents_list.append({
                    "name": name,
                    "role": agent.role,
                    "category": agent.category,
                    "description": agent.config.description
                })
            click.echo(json.dumps(agents_list, indent=2))
        else:
            click.echo(f"\n{'='*70}")
            click.echo(f"Available Agents ({len(bb5._agents)})")
            click.echo(f"{'='*70}\n")

            # Group by category
            by_category = {}
            for name, agent in bb5._agents.items():
                cat = agent.category or "general"
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append((name, agent))

            for category, agents in sorted(by_category.items()):
                click.echo(f"{category.upper()}")
                for name, agent in agents:
                    click.echo(f"  • {name}")
                    if verbose:
                        click.echo(f"    Role: {agent.role}")
                        click.echo(f"    Description: {agent.config.description}")
                click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--json", "-j", "as_json", is_flag=True, help="Output as JSON")
@click.option("--category", "-c", help="Filter by category")
def skills(as_json: bool, category: Optional[str]):
    """
    List all available skills.

    Examples:
        bb5 skills
        bb5 skills --category testing
        bb5 skills --json
    """
    asyncio.run(_handle_skills(as_json, category))


async def _handle_skills(as_json: bool, category: Optional[str]):
    """Handle the skills command asynchronously."""
    try:
        bb5 = await get_blackbox5()

        if not bb5._skill_manager:
            click.echo("No skill manager available", err=True)
            sys.exit(1)

        if as_json:
            skills_data = {}
            for cat in bb5._skill_manager.list_categories():
                if category and cat != category:
                    continue
                skills = bb5._skill_manager.get_skills_by_category(cat)
                skills_data[cat] = [
                    {"name": s.name, "description": s.description}
                    for s in skills
                ]
            click.echo(json.dumps(skills_data, indent=2))
        else:
            click.echo(f"\n{'='*70}")
            click.echo(f"Available Skills")
            click.echo(f"{'='*70}\n")

            for cat in sorted(bb5._skill_manager.list_categories()):
                if category and cat != category:
                    continue
                skills = bb5._skill_manager.get_skills_by_category(cat)
                click.echo(f"{cat.upper()} ({len(skills)} skills)")
                for skill in skills:
                    click.echo(f"  • {skill.name}")
                    click.echo(f"    {skill.description}")
                click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("query", required=True)
@click.option("--json", "-j", "as_json", is_flag=True, help="Output as JSON")
def guide(query: str, as_json: bool):
    """
    Find relevant guides for a task.

    Examples:
        bb5 guide "test this code"
        bb5 guide "deploy to production"
    """
    asyncio.run(_handle_guide(query, as_json))


async def _handle_guide(query: str, as_json: bool):
    """Handle the guide command asynchronously."""
    try:
        bb5 = await get_blackbox5()

        if not bb5._guide_registry:
            click.echo("No guide registry available", err=True)
            sys.exit(1)

        # Search for relevant guides
        # This is a simplified implementation
        # Real implementation would query the guide registry
        suggestions = [
            {
                "type": "operation",
                "title": "Code Testing",
                "description": "Comprehensive testing guide for your code",
                "relevance": 0.85
            },
            {
                "type": "workflow",
                "title": "Test-Driven Development",
                "description": "Follow TDD best practices",
                "relevance": 0.75
            }
        ]

        if as_json:
            click.echo(json.dumps(suggestions, indent=2))
        else:
            click.echo(f"\n{'='*70}")
            click.echo(f"Guide Suggestions for: {query}")
            click.echo(f"{'='*70}\n")

            for suggestion in suggestions:
                click.echo(f"{suggestion['title']}")
                click.echo(f"  {suggestion['description']}")
                click.echo(f"  Relevance: {suggestion['relevance']:.0%}")
                click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--json", "-j", "as_json", is_flag=True, help="Output as JSON")
def stats(as_json: bool):
    """
    Show system statistics.

    Examples:
        bb5 stats
        bb5 stats --json
    """
    asyncio.run(_handle_stats(as_json))


@cli.command()
@click.option("--message", "-m", help="Recovery message")
def recover(message: Optional[str]):
    """
    Recover from kill switch and resume operations.

    Examples:
        bb5 recover
        bb5 recover --message "Issue resolved"
    """
    asyncio.run(_handle_recover(message))


async def _handle_recover(message: Optional[str]):
    """Handle the recover command asynchronously."""
    try:
        from safety.kill_switch import get_kill_switch

        ks = get_kill_switch()

        if ks.is_operational():
            click.echo("✅ System is operational. No recovery needed.")
            return

        # Attempt recovery
        recovery_msg = message or "Manual recovery via CLI"
        success = ks.recover(recovery_msg)

        if success:
            click.echo("✅ System recovered successfully")
            click.echo(f"   Message: {recovery_msg}")
        else:
            click.echo("❌ Recovery failed", err=True)
            click.echo(f"   Kill switch is still active", err=True)
            click.echo(f"   Reason: {ks.trigger_reason.value if ks.trigger_reason else 'Unknown'}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--json", "-j", "as_json", is_flag=True, help="Output as JSON")
def status(as_json: bool):
    """
    Show safety system status (kill switch, safe mode, classifier).

    Examples:
        bb5 status
        bb5 status --json
    """
    asyncio.run(_handle_status(as_json))


async def _handle_status(as_json: bool):
    """Handle the status command asynchronously."""
    try:
        from safety.kill_switch import get_kill_switch, KillSwitchReason
        from safety.safe_mode import get_safe_mode, SafeModeLevel

        ks = get_kill_switch()
        sm = get_safe_mode()

        status_data = {
            "kill_switch": {
                "operational": ks.is_operational(),
                "triggered": ks.is_triggered(),
                "trigger_reason": ks.trigger_reason.value if ks.trigger_reason else None,
                "trigger_message": ks.trigger_message,
                "triggered_at": ks.trigger_time.isoformat() if ks.trigger_time else None,
            },
            "safe_mode": {
                "enabled": sm.is_safe_mode(),
                "level": sm.current_level.value if sm.is_safe_mode() else None,
                "enter_reason": sm.enter_reason,
                "enter_time": sm.enter_time.isoformat() if sm.enter_time else None,
                "limits": sm.get_limits() if sm.is_safe_mode() else None,
            },
            "overall_status": "operational" if ks.is_operational() else "emergency_shutdown"
        }

        if as_json:
            click.echo(json.dumps(status_data, indent=2))
        else:
            click.echo(f"\n{'='*70}")
            click.echo(f"Blackbox 5 Safety Status")
            click.echo(f"{'='*70}\n")

            # Overall status
            overall = status_data["overall_status"]
            status_icon = "✅" if overall == "operational" else "❌"
            click.echo(f"{status_icon} Overall Status: {overall.upper()}\n")

            # Kill switch status
            ks_data = status_data["kill_switch"]
            ks_icon = "✅" if ks_data["operational"] else "❌"
            click.echo(f"{ks_icon} Kill Switch: {'Operational' if ks_data['operational'] else 'Triggered'}")
            if not ks_data["operational"]:
                click.echo(f"   Reason: {ks_data['trigger_reason']}")
                click.echo(f"   Message: {ks_data['trigger_message']}")
                if ks_data["triggered_at"]:
                    click.echo(f"   Triggered at: {ks_data['triggered_at']}")

            click.echo()

            # Safe mode status
            sm_data = status_data["safe_mode"]
            if sm_data["enabled"]:
                sm_icon = "⚠️"
                click.echo(f"{sm_icon} Safe Mode: {sm_data['level'].upper()}")
                click.echo(f"   Reason: {sm_data['enter_reason']}")
                if sm_data["enter_time"]:
                    click.echo(f"   Entered at: {sm_data['enter_time']}")
                if sm_data["limits"]:
                    limits = sm_data["limits"]
                    click.echo(f"\n   Limits:")
                    click.echo(f"     Max CPU: {limits.get('max_cpu_percent', 'N/A')}%")
                    click.echo(f"     Max Memory: {limits.get('max_memory_mb', 'N/A')} MB")
                    click.echo(f"     Rate Limit: {limits.get('rate_limit_rpm', 'N/A')} req/min")
                    click.echo(f"     Allowed Ops: {', '.join(limits.get('allowed_operations', []))}")
            else:
                click.echo(f"✅ Safe Mode: Not active")

            click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.group()
def safe_mode():
    """Manage safe mode settings."""
    pass


@safe_mode.command()
@click.argument("level", type=click.Choice(['limited', 'restricted', 'emergency']))
@click.option("--reason", "-r", required=True, help="Reason for entering safe mode")
@click.option("--source", "-s", default="cli", help="Source of the safe mode request")
def enter(level: str, reason: str, source: str):
    """
    Enter safe mode at the specified level.

    Examples:
        bb5 safe-mode enter limited --reason "High CPU usage"
        bb5 safe-mode enter restricted --reason "Maintenance"
        bb5 safe-mode enter emergency --reason "Security incident"
    """
    asyncio.run(_handle_safe_mode_enter(level, reason, source))


async def _handle_safe_mode_enter(level: str, reason: str, source: str):
    """Handle entering safe mode."""
    try:
        from safety.safe_mode import get_safe_mode, SafeModeLevel

        sm = get_safe_mode()

        # Map level string to enum
        level_map = {
            'limited': SafeModeLevel.LIMITED,
            'restricted': SafeModeLevel.RESTRICTED,
            'emergency': SafeModeLevel.EMERGENCY
        }
        safe_level = level_map[level]

        # Enter safe mode
        success = sm.enter_level(safe_level, reason, source)

        if success:
            click.echo(f"✅ Entered {level.upper()} safe mode")
            click.echo(f"   Reason: {reason}")
            click.echo(f"   Source: {source}")
            click.echo(f"   Entered at: {sm.entered_at}")

            # Show limits
            limits = sm.get_limits()
            click.echo(f"\n   Active Limits:")
            click.echo(f"     Max CPU: {limits.get('max_cpu_percent', 'N/A')}%")
            click.echo(f"     Max Memory: {limits.get('max_memory_mb', 'N/A')} MB")
            click.echo(f"     Rate Limit: {limits.get('rate_limit_rpm', 'N/A')} req/min")
            click.echo(f"     Allowed Ops: {', '.join(limits.get('allowed_operations', []))}")
        else:
            click.echo("❌ Failed to enter safe mode", err=True)
            click.echo(f"   Current level: {sm.current_level.value}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@safe_mode.command()
@click.option("--reason", "-r", help="Reason for exiting safe mode")
def exit(reason: Optional[str]):
    """
    Exit safe mode and return to normal operation.

    Examples:
        bb5 safe-mode exit
        bb5 safe-mode exit --reason "Issue resolved"
    """
    asyncio.run(_handle_safe_mode_exit(reason))


async def _handle_safe_mode_exit(reason: Optional[str]):
    """Handle exiting safe mode."""
    try:
        from safety.safe_mode import get_safe_mode

        sm = get_safe_mode()

        if not sm.is_safe_mode():
            click.echo("✅ System is already in normal mode")
            return

        # Exit safe mode
        exit_msg = reason or "Manual exit via CLI"
        success = sm.exit_level(exit_msg)

        if success:
            click.echo("✅ Exited safe mode")
            click.echo(f"   Reason: {exit_msg}")
            click.echo(f"   System now in normal operation")
        else:
            click.echo("❌ Failed to exit safe mode", err=True)
            click.echo(f"   Current level: {sm.current_level.value}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
