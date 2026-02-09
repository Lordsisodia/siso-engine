# 06-Integrations

External service integrations for the BlackBox5 Engine.

## Overview

This folder contains all integrations with external services:
- **Development Platforms**: GitHub, GitHub Actions
- **Infrastructure**: Vercel, Supabase, Cloudflare
- **Productivity**: Notion, Obsidian, Vibe
- **Protocols**: Model Context Protocol (MCP)

## Structure

Each integration follows a standard pattern:

```
integration-name/
├── __init__.py       # Package init
├── config.py         # Configuration (if needed)
├── manager.py        # Main integration class
├── types.py          # Type definitions
├── demo.py           # Usage examples
├── README.md         # Full documentation
├── QUICKSTART.md     # Quick start guide
└── tests/            # Integration tests
```

## Quick Reference

| Integration | Purpose | Quickstart |
|-------------|---------|------------|
| [github/](./github/) | GitHub API & Issues | [QUICKSTART](./github/QUICKSTART.md) |
| [github-actions/](./github-actions/) | CI/CD Workflows | [QUICKSTART](./github-actions/QUICKSTART.md) |
| [vercel/](./vercel/) | Deployment | [QUICKSTART](./vercel/QUICKSTART.md) |
| [supabase/](./supabase/) | Database & Auth | [QUICKSTART](./supabase/QUICKSTART.md) |
| [cloudflare/](./cloudflare/) | CDN & Workers | [QUICKSTART](./cloudflare/QUICKSTART.md) |
| [notion/](./notion/) | Documentation | [QUICKSTART](./notion/QUICKSTART.md) |
| [obsidian/](./obsidian/) | Knowledge Management | [QUICKSTART](./obsidian/QUICKSTART.md) |
| [vibe/](./vibe/) | Project Management | [QUICK-REFERENCE](./vibe/QUICK-REFERENCE.md) |
| [mcp/](./mcp/) | Model Context Protocol | [README](./mcp/README.md) |

## Using an Integration

### Basic Usage

```python
from blackbox5.engine.integrations.github import GitHubManager

# Initialize
manager = GitHubManager(token="ghp_xxx", repo="owner/repo")

# Use
manager.create_issue(title="Fix bug", body="Description")
```

### Advanced Usage

See each integration's README.md for detailed documentation.

## Creating New Integrations

Use the `_template/` folder as a starting point:

```bash
cp -r _template my-new-integration
cd my-new-integration

# Edit placeholder files
# Implement manager.py
# Add your types
# Write tests
```

## Standards

All integrations MUST:

1. ✅ Use `manager.py` (not `*Manager.py`)
2. ✅ Include `types.py` with dataclasses
3. ✅ Provide `demo.py` with examples
4. ✅ Have `README.md` with full docs
5. ✅ Have `QUICKSTART.md` for quick reference
6. ✅ Include `tests/test_integration.py`

## Documentation

Full integration documentation: `../../engine/docs/integrations/`

## Related

- Engine code: `../01-core/`, `../02-agents/`
- Operations: `../07-operations/`
- Development: `../08-development/`

## Statistics

- **Total integrations**: 9
- **Total files**: ~85 (excluding template)
- **Categories**: Development, Infrastructure, Productivity, Protocols
