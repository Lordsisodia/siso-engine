# Configuration

> Unified configuration system for Blackbox5

## Overview

This directory contains all configuration files for the Blackbox5 engine, organized by scope and purpose.

## Structure

```
configuration/
├── agents/              # Agent-specific configurations
│   ├── agent-config.yaml      # Agent behavior settings
│   ├── skill-registry.yaml    # Skill definitions and mappings
│   ├── alert-config.yaml      # Alert thresholds and rules
│   ├── api-config.yaml        # API endpoint configurations
│   ├── cli-config.yaml        # CLI tool settings
│   ├── code-review-config.yaml # Code review rules
│   ├── github-config.yaml     # GitHub integration settings
│   ├── base.yaml              # Base configuration
│   ├── default.yaml           # Default settings
│   ├── dev.yaml               # Development environment
│   ├── staging.yaml           # Staging environment
│   ├── prod.yaml              # Production environment
│   ├── engine.yaml            # Engine-specific settings
│   ├── schema.yaml            # Configuration schema
│   └── MIGRATION-GUIDE.md     # Migration documentation
│
├── mcp/                 # MCP (Model Context Protocol) configurations
│   ├── moltbot/         # Moltbot MCP server config
│   ├── openclaw/        # OpenClaw MCP server config
│   └── system/          # System MCP settings
│
└── system/              # System-wide configurations
    ├── mcp-servers.json # MCP server registry
    └── README.md
```

## Agent Configurations (agents/)

Contains all agent-related configuration files:

### Core Configs

| File | Purpose |
|------|---------|
| base.yaml | Base configuration all agents inherit |
| default.yaml | Default settings for all environments |
| engine.yaml | Engine runtime configuration |
| schema.yaml | Configuration validation schema |

### Environment Configs

| File | Purpose |
|------|---------|
| dev.yaml | Development environment settings |
| staging.yaml | Staging environment settings |
| prod.yaml | Production environment settings |

### Feature Configs

| File | Purpose |
|------|---------|
| agent-config.yaml | Agent behavior and lifecycle |
| skill-registry.yaml | Skill definitions and mappings |
| alert-config.yaml | Alert thresholds and routing |
| api-config.yaml | API endpoints and authentication |
| cli-config.yaml | CLI tool behavior |
| code-review-config.yaml | Code review rules and checks |
| github-config.yaml | GitHub integration settings |

### Schema and Migration

- schema.yaml - Validates all configuration files
- MIGRATION-GUIDE.md - Guide for migrating between config versions

## MCP Configurations (mcp/)

Contains MCP (Model Context Protocol) server configurations:

| Directory | Purpose |
|-----------|---------|
| moltbot/ | Moltbot MCP server settings |
| openclaw/ | OpenClaw MCP server settings |
| system/ | System-wide MCP configuration |

## System Configurations (system/)

Contains system-wide configuration files:

| File | Purpose |
|------|---------|
| mcp-servers.json | Registry of all MCP servers |

## Unified Config System

The configuration system uses a layered approach:

```
base.yaml (lowest priority)
  ↓
default.yaml
  ↓
{environment}.yaml (dev/staging/prod)
  ↓
{feature}-config.yaml (highest priority)
```

### Loading Configuration

```python
from helpers.core.registry import ConfigRegistry

config = ConfigRegistry()
agent_config = config.get("agents", "agent-config")
```

### Environment Selection

The system automatically loads the appropriate environment config based on:
1. BLACKBOX5_ENV environment variable
2. .env file settings
3. Default to dev.yaml

## Usage

### Reading Configuration

```python
# Load agent configuration
from configuration.agents import load_config

config = load_config("agent-config", environment="dev")
```

### Validating Configuration

```python
from configuration.agents.schema import validate

validate("agent-config.yaml")  # Raises on invalid config
```

## Migration Notes

This unified configuration system consolidates configs from:
- core/config/ (old location)
- .config/ (temporary directory)
- config/ (legacy directory)

See agents/MIGRATION-GUIDE.md for details on migrating from old config locations.
