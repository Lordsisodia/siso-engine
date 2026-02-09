#!/usr/bin/env python3
"""
RALF CLI Config Commands
========================

Commands for configuration management:
- get: Get configuration value
- set: Set configuration value (placeholder)
- validate: Validate configuration
- diff: Compare environments (placeholder)

Author: RALF System
Version: 1.0.0 (Feature F-016)
"""

import click
import yaml
from pathlib import Path
from typing import Optional
from ..lib.output import get_formatter
from ..lib.context import get_context


@click.group(name="config")
def config_cli():
    """Configuration management commands."""
    pass


@config_cli.command(name="get")
@click.argument("key", required=False)
@click.option("--environment", "-e", type=click.Choice(["base", "dev", "staging", "prod"]), default="base", help="Environment to read from")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def config_get(key: Optional[str], environment: str, json_mode: bool):
    """Get configuration value. Shows all if no key specified."""
    formatter = get_formatter(json_mode)
    context = get_context()

    # Read config file
    config_file = context.engine_config_dir / f"{environment}.yaml"

    if not config_file.exists():
        formatter.error(f"Config file not found: {config_file}")
        formatter.info(f"Available environments: base, dev, staging, prod")
        return

    try:
        with open(config_file) as f:
            config_data = yaml.safe_load(f)

        if not config_data:
            formatter.warning(f"Config file is empty: {config_file}")
            return

        # Get nested key
        if key:
            keys = key.split(".")
            value = config_data
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    formatter.error(f"Key not found: {key}")
                    return

            if json_mode:
                formatter.json({key: value})
            else:
                formatter.panel(f"Configuration: {key}", border_style="cyan")
                formatter.print(f"{value}")
        else:
            # Show all config
            if json_mode:
                formatter.json(config_data)
            else:
                formatter.panel(f"Configuration: {environment}", border_style="cyan")
                formatter.yaml(config_data)

    except Exception as e:
        formatter.error(f"Failed to read config: {e}")


@config_cli.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option("--environment", "-e", type=click.Choice(["base", "dev", "staging", "prod"]), default="base", help="Environment to update")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def config_set(key: str, value: str, environment: str, json_mode: bool):
    """Set configuration value (placeholder)."""
    formatter = get_formatter(json_mode)

    formatter.info(f"Setting {key} = {value} in {environment} environment")
    formatter.warning("Config set not yet implemented through CLI")
    formatter.info("Use ConfigManagerV2 from Python or edit config files directly")


@config_cli.command(name="validate")
@click.option("--environment", "-e", type=click.Choice(["base", "dev", "staging", "prod"]), default="base", help="Environment to validate")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def config_validate(environment: str, json_mode: bool):
    """Validate configuration."""
    formatter = get_formatter(json_mode)
    context = get_context()

    # Read config file
    config_file = context.engine_config_dir / f"{environment}.yaml"

    if not config_file.exists():
        formatter.error(f"Config file not found: {config_file}")
        return

    try:
        with open(config_file) as f:
            config_data = yaml.safe_load(f)

        if not config_data:
            formatter.warning(f"Config file is empty: {config_file}")
            return

        # Basic validation
        errors = []
        warnings = []

        # Check for required fields
        if "system" not in config_data:
            errors.append("Missing 'system' section")

        if "agents" not in config_data:
            warnings.append("Missing 'agents' section")

        # Report results
        if json_mode:
            result = {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "environment": environment
            }
            formatter.json(result)
        else:
            formatter.panel(f"Configuration Validation: {environment}", border_style="cyan")

            if len(errors) == 0 and len(warnings) == 0:
                formatter.success("Configuration is valid!")
            else:
                if errors:
                    formatter.error(f"Errors ({len(errors)}):")
                    for error in errors:
                        formatter.print(f"  ✗ {error}", color="red")

                if warnings:
                    formatter.warning(f"Warnings ({len(warnings)}):")
                    for warning in warnings:
                        formatter.print(f"  ⚠ {warning}", color="yellow")

    except Exception as e:
        formatter.error(f"Failed to validate config: {e}")


@config_cli.command(name="list")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def config_list(json_mode: bool):
    """List available configuration files."""
    formatter = get_formatter(json_mode)
    context = get_context()

    config_dir = context.engine_config_dir

    if not config_dir.exists():
        formatter.error(f"Config directory not found: {config_dir}")
        return

    try:
        config_files = list(config_dir.glob("*.yaml"))

        if not config_files:
            formatter.info("No configuration files found")
            return

        configs = []
        for config_file in config_files:
            file_stat = config_file.stat()
            configs.append({
                "name": config_file.name,
                "size": f"{file_stat.st_size} bytes",
                "modified": file_stat.st_mtime
            })

        if json_mode:
            formatter.json(configs)
        else:
            formatter.panel("Configuration Files", border_style="cyan")
            formatter.table(configs, columns=["name", "size"])

    except Exception as e:
        formatter.error(f"Failed to list configs: {e}")


@config_cli.command(name="diff")
@click.argument("env1", type=click.Choice(["base", "dev", "staging", "prod"]))
@click.argument("env2", type=click.Choice(["base", "dev", "staging", "prod"]))
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
def config_diff(env1: str, env2: str, json_mode: bool):
    """Compare two environments (placeholder)."""
    formatter = get_formatter(json_mode)

    formatter.info(f"Comparing {env1} vs {env2}...")
    formatter.warning("Config diff not yet implemented through CLI")
    formatter.info("Use diff command directly on config files")


if __name__ == "__main__":
    config_cli()
