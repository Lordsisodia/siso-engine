# 06-Integrations Reorganization Plan

## Executive Summary

The integrations folder has **77 files** across 10 integrations with **3 major issues**:
1. **Duplicate GitHub integrations** (3 different locations)
2. **Inconsistent naming patterns**
3. **Misplaced documentation**

This plan creates a clean, scalable structure using first principles.

---

## Current State Analysis

### File Inventory

| Integration | Files | Status | Issues |
|------------|-------|--------|--------|
| **_template** | 9 | ✅ Template | Should be excluded from production count |
| **cloudflare** | 10 | ✅ Complete | Follows standard pattern |
| **github** | 6 | ⚠️ Duplicate | Basic GitHub API, duplicates core |
| **github-actions** | 6 | ✅ Complete | Separate from github (correct) |
| **mcp** | 2 | ❌ Incomplete | Missing README, types, demo, tests |
| **notion** | 11 | ✅ Complete | Follows standard pattern |
| **obsidian** | 8 | ✅ Complete | Follows standard pattern |
| **supabase** | 10 | ✅ Complete | Follows standard pattern |
| **vercel** | 6 | ✅ Complete | Follows standard pattern |
| **vibe** | 8 | ⚠️ Non-standard | Uses VibeKanbanManager.py instead of manager.py |
| **.docs** | 1 | ❌ Misplaced | Should be in engine/docs |

### Critical Issues

#### 1. DUPLICATE GITHUB INTEGRATIONS 🚨

**3 different GitHub implementations found:**

| Location | Files | Purpose | Recommendation |
|----------|-------|---------|----------------|
| `06-integrations/github/` | 6 files | Basic GitHub API wrapper | **MERGE into unified github/** |
| `01-core/interface/integrations/github/` | 15 files | Advanced GitHub sync with CCPM | **MERGE into unified github/** |
| `07-operations/environment/lib/python/core/integrations/github.py` | 1 file | Operations GitHub script | **DELETE (use unified integration)** |

**Impact:**
- Confusion about which GitHub integration to use
- Duplicated maintenance effort
- Inconsistent implementations
- Potential bugs from diverging code

**Root Cause:**
- `01-core` version was created first (advanced, CCPM-based)
- `06-integrations` version was created later (simpler, requests-based)
- No communication between teams

#### 2. Inconsistent Naming Patterns

| Integration | Current | Should Be |
|------------|---------|-----------|
| **github** | `GitHubManager.py` | `manager.py` |
| **vibe** | `VibeKanbanManager.py` | `manager.py` |
| **mcp** | `MCPIntegration.py` | `manager.py` |
| All others | `manager.py` | ✅ Correct |

#### 3. Misplaced Documentation

- `.docs/README.md` exists at root but should be in `engine/docs/integrations/`

---

## First Principles Analysis

### WHAT (Enabled Capabilities)

| Category | Integrations | Description |
|----------|--------------|-------------|
| **Development Platform** | github, github-actions | Code hosting, CI/CD |
| **Infrastructure** | vercel, supabase, cloudflare | Deployment, database, CDN |
| **Productivity** | notion, obsidian, vibe | Docs, knowledge, tasks |
| **Protocol** | mcp | Model Context Protocol |

### WHO (Users)

| User Type | Integrations | Purpose |
|-----------|--------------|---------|
| **Developers** | All | API access |
| **Agents** | All | Automation |
| **DevOps** | vercel, supabase, cloudflare, github-actions | Deployment |
| **Teams** | notion, vibe, github | Collaboration |

### WHERE (Should Live)

| Current | Recommended | Reason |
|---------|-------------|--------|
| `06-integrations/github/` | ✅ Keep | Unified GitHub integration |
| `01-core/interface/integrations/github/` | ❌ DELETE | Move to 06-integrations |
| `06-integrations/.docs/` | ❌ Move | To engine/docs/integrations |

---

## Proposed Structure

### Option A: Unified by Service (RECOMMENDED) ✅

**Merge duplicates, standardize naming:**

```
06-integrations/
├── _template/           # Integration template (9 files)
│   ├── __init__.py
│   ├── config.py
│   ├── demo.py
│   ├── IMPLEMENTATION-GUIDE.md
│   ├── manager.py       # Standard naming
│   ├── QUICKSTART.md
│   ├── README.md
│   ├── types.py
│   └── tests/test_integration.py
│
├── github/              # UNIFIED GitHub integration (21 files)
│   ├── __init__.py
│   ├── config.py
│   ├── manager.py       # Renamed from GitHubManager.py
│   ├── types.py
│   ├── demo.py
│   ├── README.md        # Unified documentation
│   ├── QUICKSTART.md
│   ├── IMPLEMENTATION-SUMMARY.md
│   ├── providers/       # From 01-core version
│   │   ├── protocol.py
│   │   └── github_provider.py
│   ├── sync/            # From 01-core version
│   │   └── ccpm_sync.py
│   ├── memory/          # From 01-core version
│   │   └── __init__.py
│   ├── examples/        # From 01-core version
│   │   └── ...
│   └── tests/           # Unified tests
│       ├── __init__.py
│       └── test_github.py
│
├── github-actions/      # CI/CD workflows (6 files)
│   └── (unchanged)
│
├── mcp/                 # Model Context Protocol (5 files)
│   ├── __init__.py      # ADD
│   ├── manager.py       # Renamed from MCPIntegration.py
│   ├── types.py         # ADD
│   ├── README.md        # ADD
│   ├── demo.py          # ADD
│   ├── mcp_crash_prevention.py
│   └── tests/           # ADD
│       ├── __init__.py
│       └── test_mcp.py
│
├── cloudflare/          # (unchanged)
├── notion/              # (unchanged)
├── obsidian/            # (unchanged)
├── supabase/            # (unchanged)
├── vercel/              # (unchanged)
└── vibe/                # Standardize naming (8 files)
    ├── __init__.py
    ├── manager.py       # Renamed from VibeKanbanManager.py
    ├── types.py
    ├── demo.py
    ├── README.md
    ├── QUICKSTART.md
    └── tests/
```

**Changes:**
1. ✅ Merge 3 GitHub integrations into 1
2. ✅ Rename all `*Manager.py` to `manager.py`
3. ✅ Complete MCP integration with missing files
4. ✅ Move `.docs/` to `engine/docs/integrations/`
5. ✅ Delete `01-core/interface/integrations/github/`
6. ✅ Delete `07-operations/environment/lib/python/core/integrations/github.py`

---

### Option B: Split by Purpose (NOT RECOMMENDED)

```
06-integrations/
├── api/                 # Pure API wrappers
│   ├── notion/
│   ├── obsidian/
│   └── vibe/
├── dev-platform/        # Development platforms
│   ├── github/          # Merged
│   └── github-actions/
├── infrastructure/      # Infrastructure services
│   ├── vercel/
│   ├── supabase/
│   └── cloudflare/
└── protocols/           # Protocols
    └── mcp/
```

**Why NOT recommended:**
- More complex structure
- Harder to find integrations
- Breaking change for existing code
- No clear benefit over Option A

---

## Implementation Plan

### Phase 1: Merge GitHub Integrations

**1. Create unified github/ folder**

```bash
cd 06-integrations

# Keep current folder structure
cp -r github github-temp

# Merge from 01-core
cp -r ../01-core/interface/integrations/github/* github/

# Organize merged content
github/
├── __init__.py          # Merge both
├── config.py            # From 06-integrations
├── manager.py           # Rename from GitHubManager.py
├── types.py             # Add if missing
├── demo.py              # Merge both
├── README.md            # Unified docs
├── QUICKSTART.md        # Keep
├── IMPLEMENTATION-SUMMARY.md
├── providers/           # From 01-core
├── sync/                # From 01-core
├── memory/              # From 01-core
├── examples/            # From 01-core
└── tests/               # Unified tests
```

**2. Delete duplicate locations**

```bash
# Delete 01-core version
rm -rf ../01-core/interface/integrations/github

# Delete operations script
rm ../07-operations/environment/lib/python/core/integrations/github.py
```

**3. Update imports**

Search for:
```python
from blackbox5.engine.core.interface.integrations.github import ...
```

Replace with:
```python
from blackbox5.engine.integrations.github import ...
```

### Phase 2: Standardize Naming

**1. Rename files**

```bash
# github
mv github/GitHubManager.py github/manager.py

# vibe
mv vibe/VibeKanbanManager.py vibe/manager.py

# mcp
mv mcp/MCPIntegration.py mcp/manager.py
```

**2. Update imports in each integration**

```bash
# Update internal imports
sed -i '' 's/from GitHubManager import/from .manager import/g' github/*.py

sed -i '' 's/from VibeKanbanManager import/from .manager import/g' vibe/*.py

sed -i '' 's/from MCPIntegration import/from .manager import/g' mcp/*.py
```

### Phase 3: Complete MCP Integration

**1. Add missing files**

```bash
cd mcp

# Create __init__.py
cat > __init__.py << 'EOF'
from .manager import MCPManager

__all__ = ['MCPManager']
EOF

# Create types.py
cat > types.py << 'EOF'
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class MCPServer:
    name: str
    status: str
    capabilities: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
EOF

# Create README.md (copy template)
cp ../_template/README.md ./README.md
# Edit with MCP-specific content

# Create demo.py (copy template)
cp ../_template/demo.py ./demo.py
# Edit with MCP-specific demo

# Create tests/
mkdir -p tests
cp ../_template/tests/test_integration.py tests/test_mcp.py
```

**2. Update types.py with actual MCP types**

Edit types.py to include:
- `MCPServer`
- `MCPMessage`
- `MCPResponse`
- `MCPError`

### Phase 4: Move Documentation

```bash
# Move .docs to engine docs
mkdir -p ../../engine/docs/integrations
mv .docs/README.md ../../engine/docs/integrations/README.md

# Remove empty .docs folder
rmdir .docs
```

### Phase 5: Update Root README

Create `06-integrations/README.md` with:

```markdown
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
| [notion/](./notion/) | Documentation | [QUICKSTART](./notion/QUICKSTART.md) |
| [vibe/](./vibe/) | Project Management | [QUICKSTART](./vibe/QUICK-REFERENCE.md) |

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
```

---

## Verification Steps

After implementation, verify:

```bash
cd 06-integrations

# 1. Check structure
tree -L 2 -I '__pycache__|*.pyc'

# 2. Count files
find . -name "*.py" | wc -l    # Should be ~60-70
find . -name "*.md" | wc -l    # Should be ~30

# 3. Check no duplicates
find .. -name "*github*" -type d
# Should only show: 06-integrations/github, 06-integrations/github-actions

# 4. Verify naming patterns
find . -name "*Manager.py"
# Should return: nothing (all renamed to manager.py)

# 5. Check all integrations have required files
for dir in */; do
  if [ "$dir" != "_template/" ] && [ "$dir" != ".docs/" ]; then
    echo "Checking $dir"
    ls "$dir"manager.py 2>/dev/null || echo "❌ Missing manager.py"
    ls "$dir"types.py 2>/dev/null || echo "❌ Missing types.py"
    ls "$dir"README.md 2>/dev/null || echo "❌ Missing README.md"
  fi
done

# 6. Verify no broken imports
python3 -m py_compile github/__init__.py
python3 -m py_compile vibe/__init__.py
python3 -m py_compile mcp/__init__.py
```

---

## Benefits

### Before
- ❌ 3 duplicate GitHub integrations
- ❌ Inconsistent naming (GitHubManager.py, VibeKanbanManager.py)
- ❌ Incomplete MCP integration
- ❌ Misplaced documentation
- ❌ Confusion about which integration to use

### After
- ✅ Single, unified GitHub integration
- ✅ Consistent naming (all manager.py)
- ✅ Complete MCP integration
- ✅ Proper documentation location
- ✅ Clear, standard structure
- ✅ Easy to add new integrations

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing imports | High | High | Search & replace all imports |
| Git merge conflicts | Low | Medium | Use git properly |
| Missing functionality in merge | Medium | High | Test thoroughly before delete |
| Documentation becomes outdated | Low | Low | Update all READMEs |

---

## Rollback Plan

If something goes wrong:

```bash
# Restore from git
git checkout HEAD -- 06-integrations/
git checkout HEAD -- 01-core/interface/integrations/github/
git checkout HEAD -- 07-operations/environment/lib/python/core/integrations/

# Or restore from backup (if created)
cp -r /path/to/backup/06-integrations/* 06-integrations/
```

---

## Next Steps

1. **Review this plan** - Approve before implementation
2. **Create backup** - `cp -r 06-integrations ../06-integrations-backup`
3. **Implement Phase 1** - Merge GitHub integrations
4. **Test Phase 1** - Verify no broken imports
5. **Implement Phase 2** - Standardize naming
6. **Test Phase 2** - Verify imports work
7. **Implement Phase 3** - Complete MCP
8. **Test Phase 3** - Run MCP tests
9. **Implement Phase 4** - Move docs
10. **Final verification** - Run all checks

---

## Questions?

1. Do you approve this plan?
2. Should I implement Option A (unified by service)?
3. Any concerns about merging GitHub integrations?
4. Timeline expectations?
