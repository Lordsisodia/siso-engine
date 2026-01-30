"""
Task Management Commands for BlackBox5 CLI

Provides quick access to task context, code locations, and refactor history.
All commands integrate with the project memory system.

Usage:
    bb5 task:where <task-id>
    bb5 task:context <task-id>
    bb5 task:refactor <task-id>
    bb5 code:stats [--domain <name>]
    bb5 domain:info <domain>
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import BaseCommand, CommandError


class TaskWhereCommand(BaseCommand):
    """
    Show where task-related code lives.

    Displays the domain, file paths, existing components, and shared components
    available for a given task.

    Usage: bb5 task:where <task-id>
    Example: bb5 task:where TASK-admin-overview
    """
    name = "task:where"
    description = "Show code locations for a task"
    aliases = ["task:location", "task:find"]

    def execute(self, args: Dict[str, Any]) -> int:
        task_id = args.get("task_id")
        if not task_id:
            raise CommandError("Missing task_id argument", exit_code=2)

        # Load CODE-INDEX
        code_index = self._load_code_index()
        if not code_index:
            print("❌ CODE-INDEX.yaml not found. Run: bb5 generate:code-index")
            return 1

        # Find task in index
        task_info = self._find_task(code_index, task_id)
        if not task_info:
            print(f"❌ Task '{task_id}' not found in CODE-INDEX")
            return 1

        # Display results
        self._display_task_location(task_info, code_index)
        return 0

    def _load_code_index(self) -> Optional[Dict]:
        """Load CODE-INDEX.yaml from project memory"""
        # Try multiple possible locations
        paths = [
            Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal" / "CODE-INDEX.yaml",
            Path.cwd() / ".project-memory" / "CODE-INDEX.yaml",
            Path(__file__).parent.parent.parent.parent.parent / "memory" / "project-memory" / "siso-internal" / "CODE-INDEX.yaml",
        ]

        for path in paths:
            if path.exists():
                with open(path) as f:
                    return yaml.safe_load(f)
        return None

    def _find_task(self, code_index: Dict, task_id: str) -> Optional[Dict]:
        """Find task in CODE-INDEX"""
        # Search in domains
        for domain_name, domain_data in code_index.get("domains", {}).items():
            for page in domain_data.get("pages", []):
                if page.get("task_id") == task_id:
                    return {
                        "task_id": task_id,
                        "domain": domain_name,
                        "page": page,
                        "domain_data": domain_data
                    }
        return None

    def _display_task_location(self, task_info: Dict, code_index: Dict) -> None:
        """Display task location information"""
        domain = task_info["domain"]
        page = task_info["page"]
        domain_data = task_info["domain_data"]

        print(f"\n{'='*70}")
        print(f"📍 Task Location: {task_info['task_id']}")
        print(f"{'='*70}\n")

        print(f"📁 Domain: {domain}")
        print(f"   Path: {domain_data.get('path', 'N/A')}")
        print(f"   Type: {domain_data.get('type', 'N/A')}")
        print(f"   Status: {domain_data.get('status', 'N/A')}")

        print(f"\n📄 Page: {page.get('id', 'N/A')}")
        print(f"   Pages path: {page.get('path', 'N/A')}")
        print(f"   Components path: {page.get('components', 'N/A')}")
        print(f"   Status: {page.get('status', 'N/A')}")

        # Existing files
        files = page.get("files", [])
        if files:
            print(f"\n✅ Existing Files:")
            for f in files:
                print(f"   - {f}")
        else:
            print(f"\n✅ Existing Files: None (ready to create)")

        # Shared components
        component_registry = code_index.get("components", {})
        domain_parts = domain.split("-")[0] if "-" in domain else domain

        shared_components = []
        for comp_name, comp_data in component_registry.items():
            if "used_by" in comp_data and domain in comp_data.get("used_by", []):
                shared_components.append(comp_name)

        if shared_components:
            print(f"\n🔗 Shared Components Available:")
            for comp in shared_components:
                comp_data = component_registry[comp]
                print(f"   - {comp}")
                print(f"     Path: {comp_data.get('path', 'N/A')}")

        # Recent refactors in domain
        refactors = code_index.get("refactors", [])
        domain_refactors = [r for r in refactors if domain in r.get("affected_domains", [])]
        if domain_refactors:
            latest = domain_refactors[0]
            print(f"\n🔄 Last Refactor: {latest.get('date', 'N/A')}")
            print(f"   {latest.get('description', 'N/A')}")

        print(f"\n{'='*70}\n")


class TaskContextCommand(BaseCommand):
    """
    Show full context for a task.

    Displays the complete context hierarchy: project → domain → feature → task
    including first principles, domain context, and competitor information.

    Usage: bb5 task:context <task-id>
    """
    name = "task:context"
    description = "Show full task context hierarchy"
    aliases = ["task:info", "task:detail"]

    def execute(self, args: Dict[str, Any]) -> int:
        task_id = args.get("task_id")
        if not task_id:
            raise CommandError("Missing task_id argument", exit_code=2)

        # Load all contexts
        contexts = self._load_contexts(task_id)
        if not contexts:
            print(f"❌ No context found for task '{task_id}'")
            return 1

        # Display context hierarchy
        self._display_context_hierarchy(contexts)
        return 0

    def _load_contexts(self, task_id: str) -> Optional[Dict]:
        """Load all relevant contexts for a task"""
        # Find task location
        code_index_path = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal" / "CODE-INDEX.yaml"
        if not code_index_path.exists():
            code_index_path = Path.cwd() / ".project-memory" / "CODE-INDEX.yaml"

        if not code_index_path.exists():
            return None

        with open(code_index_path) as f:
            code_index = yaml.safe_load(f)

        # Find task
        for domain_name, domain_data in code_index.get("domains", {}).items():
            for page in domain_data.get("pages", []):
                if page.get("task_id") == task_id:
                    return self._build_contexts(domain_name, page)

        return None

    def _build_contexts(self, domain_name: str, page: Dict) -> Dict:
        """Build context hierarchy"""
        memory_root = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal"
        if not memory_root.exists():
            memory_root = Path.cwd() / ".project-memory"

        docs_root = Path.cwd() / "blackbox5" / "docs"

        contexts = {
            "project": self._load_context(docs_root / "project" / "FIRST-PRINCIPLES.md"),
            "users": self._load_context(docs_root / "project" / "USERS.md"),
            "domain": self._load_context(memory_root / "context" / "domains" / domain_name / "DOMAIN-CONTEXT.md"),
            "feature": self._load_context(memory_root / "context" / "domains" / domain_name / "FEATURES.md"),
            "competitors": self._load_context(docs_root / "competitive" / "COMPETITORS.md"),
        }

        return contexts

    def _load_context(self, path: Path) -> Optional[str]:
        """Load context file"""
        if path.exists():
            with open(path) as f:
                content = f.read()
                # Return first 500 chars as preview
                if len(content) > 500:
                    return content[:500] + "\n... (truncated)"
                return content
        return None

    def _display_context_hierarchy(self, contexts: Dict) -> None:
        """Display full context hierarchy"""
        print(f"\n{'='*70}")
        print(f"📚 Task Context Hierarchy")
        print(f"{'='*70}\n")

        if contexts.get("project"):
            print(f"🎯 Project Context (FIRST-PRINCIPLES)")
            print(f"{'─'*70}")
            print(contexts["project"])
            print()

        if contexts.get("users"):
            print(f"👥 User Context")
            print(f"{'─'*70}")
            print(contexts["users"])
            print()

        if contexts.get("domain"):
            print(f"🏗️  Domain Context")
            print(f"{'─'*70}")
            print(contexts["domain"])
            print()

        if contexts.get("feature"):
            print(f"⚡ Feature Context")
            print(f"{'─'*70}")
            print(contexts["feature"])
            print()

        if contexts.get("competitors"):
            print(f"🎯 Competitor Context")
            print(f"{'─'*70}")
            print(contexts["competitors"])
            print()

        print(f"{'='*70}\n")


class TaskRefactorCommand(BaseCommand):
    """
    Show refactor history relevant to a task's domain.

    Displays past refactors, lessons learned, and gotchas for the domain
    associated with the task.

    Usage: bb5 task:refactor <task-id>
    """
    name = "task:refactor"
    description = "Show refactor history for task's domain"
    aliases = ["task:lessons", "task:history"]

    def execute(self, args: Dict[str, Any]) -> int:
        task_id = args.get("task_id")
        if not task_id:
            raise CommandError("Missing task_id argument", exit_code=2)

        # Load CODE-INDEX
        code_index_path = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal" / "CODE-INDEX.yaml"
        if not code_index_path.exists():
            code_index_path = Path.cwd() / ".project-memory" / "CODE-INDEX.yaml"

        if not code_index_path.exists():
            print("❌ CODE-INDEX.yaml not found")
            return 1

        with open(code_index_path) as f:
            code_index = yaml.safe_load(f)

        # Find task's domain
        domain = None
        for domain_name, domain_data in code_index.get("domains", {}).items():
            for page in domain_data.get("pages", []):
                if page.get("task_id") == task_id:
                    domain = domain_name
                    break
            if domain:
                break

        if not domain:
            print(f"❌ Task '{task_id}' not found")
            return 1

        # Display refactor history
        self._display_refactor_history(domain, code_index)
        return 0

    def _display_refactor_history(self, domain: str, code_index: Dict) -> None:
        """Display refactor history for domain"""
        print(f"\n{'='*70}")
        print(f"🔄 Refactor History: {domain}")
        print(f"{'='*70}\n")

        # Get domain-specific refactor file
        memory_root = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal"
        if not memory_root.exists():
            memory_root = Path.cwd() / ".project-memory"

        refactor_file = memory_root / "context" / "domains" / domain / "REFACTOR-HISTORY.md"

        if refactor_file.exists():
            with open(refactor_file) as f:
                print(f.read())
        else:
            # Show from CODE-INDEX
            refactors = code_index.get("refactors", [])
            domain_refactors = [r for r in refactors if domain in r.get("affected_domains", [])]

            if domain_refactors:
                for refactor in domain_refactors:
                    print(f"📅 {refactor.get('date', 'N/A')}")
                    print(f"   {refactor.get('description', 'N/A')}")
                    print(f"\n   Lessons:")
                    for lesson in refactor.get("lessons", []):
                        print(f"   • {lesson}")
                    print()
            else:
                print(f"✅ No refactor history found for {domain}")

        print(f"{'='*70}\n")


class TaskStartCommand(BaseCommand):
    """
    Start working on a task.

    Creates the task directory structure, loads context, and initializes
    the agent workspace.

    Usage: bb5 task:start <task-id>
    """
    name = "task:start"
    description = "Start working on a task"
    aliases = ["task:begin", "task:open"]

    def execute(self, args: Dict[str, Any]) -> int:
        task_id = args.get("task_id")
        if not task_id:
            raise CommandError("Missing task_id argument", exit_code=2)

        memory_root = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal"
        if not memory_root.exists():
            memory_root = Path.cwd() / ".project-memory"

        task_dir = memory_root / "tasks" / "working" / task_id

        if task_dir.exists():
            print(f"✓ Task directory already exists: {task_dir}")
            print(f"  Use 'bb5 task:where {task_id}' to see details")
            return 0

        # Create task directory structure
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "iterations").mkdir(exist_ok=True)
        (task_dir / "workspace").mkdir(exist_ok=True)
        (task_dir / "artifacts" / "designs").mkdir(parents=True, exist_ok=True)
        (task_dir / "artifacts" / "specs").mkdir(parents=True, exist_ok=True)
        (task_dir / "artifacts" / "tests").mkdir(parents=True, exist_ok=True)

        # Create task.md
        task_md = task_dir / "task.md"
        task_md.write_text(f"""---
id: {task_id}
title: "Task Title"
type: implementation
status: in_progress
created: {datetime.now().isoformat()}
---

# Task: {task_id}

## Overview
[Task description]

## Context
Run `bb5 task:context {task_id}` to see full context

## Location
Run `bb5 task:where {task_id}` to see code locations

## Refactor History
Run `bb5 task:refactor {task_id}` to see relevant refactors
""")

        # Create workspace files
        (task_dir / "workspace" / "insights.md").write_text("# Insights\n\nWhat the agent learns:\n\n")
        (task_dir / "workspace" / "gotchas.md").write_text("# Gotchas\n\nCodebase pitfalls to avoid:\n\n")
        (task_dir / "workspace" / "decisions.md").write_text("# Decisions\n\nTask decisions and rationale:\n\n")
        (task_dir / "workspace" / "data.json").write_text("{}\n")

        print(f"✓ Created task directory: {task_dir}")
        print(f"  - task.md")
        print(f"  - workspace/ (insights.md, gotchas.md, decisions.md, data.json)")
        print(f"  - iterations/")
        print(f"  - artifacts/")
        print(f"\n  Next steps:")
        print(f"    bb5 task:where {task_id}  # See where to work")
        print(f"    bb5 task:context {task_id} # Get full context")
        print(f"    bb5 task:refactor {task_id} # Learn from refactors")

        return 0


class TaskCompleteCommand(BaseCommand):
    """
    Mark a task as complete.

    Moves the task to completed/, generates a final report, and updates
    the CODE-INDEX with new components.

    Usage: bb5 task:complete <task-id>
    """
    name = "task:complete"
    description = "Mark task complete and archive"
    aliases = ["task:done", "task:finish"]

    def execute(self, args: Dict[str, Any]) -> int:
        task_id = args.get("task_id")
        if not task_id:
            raise CommandError("Missing task_id argument", exit_code=2)

        memory_root = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal"
        if not memory_root.exists():
            memory_root = Path.cwd() / ".project-memory"

        task_dir = memory_root / "tasks" / "working" / task_id
        completed_dir = memory_root / "tasks" / "completed" / task_id

        if not task_dir.exists():
            print(f"❌ Task not found: {task_dir}")
            return 1

        # Create final report
        final_report = completed_dir / "final-report.md"
        final_report.parent.mkdir(parents=True, exist_ok=True)

        final_report.write_text(f"""# Final Report: {task_id}

Completed: {datetime.now().isoformat()}

## What Was Accomplished
[Summary of work completed]

## Files Created
[List of files created]

## Lessons Learned
[Key insights from this task]

## Next Steps
[What to do next]
""")

        # Move task directory
        import shutil
        shutil.move(str(task_dir), str(completed_dir))

        print(f"✓ Task completed: {task_id}")
        print(f"  Moved to: {completed_dir}")
        print(f"\n  Don't forget to:")
        print(f"    bb5 generate:code-index  # Update CODE-INDEX with new files")

        return 0


class CodeStatsCommand(BaseCommand):
    """
    Show codebase statistics.

    Displays file counts, component counts, refactor history, and domain status.

    Usage: bb5 code:stats [--domain <name>]
    """
    name = "code:stats"
    description = "Show codebase statistics"
    aliases = ["code:info", "stats"]

    def execute(self, args: Dict[str, Any]) -> int:
        domain = args.get("domain")

        # Load CODE-INDEX
        code_index_path = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal" / "CODE-INDEX.yaml"
        if not code_index_path.exists():
            code_index_path = Path.cwd() / ".project-memory" / "CODE-INDEX.yaml"

        if not code_index_path.exists():
            print("❌ CODE-INDEX.yaml not found. Run: bb5 generate:code-index")
            return 1

        with open(code_index_path) as f:
            code_index = yaml.safe_load(f)

        self._display_stats(code_index, domain)
        return 0

    def _display_stats(self, code_index: Dict, domain: Optional[str]) -> None:
        """Display codebase statistics"""
        print(f"\n{'='*70}")
        print(f"📊 Codebase Statistics")
        print(f"{'='*70}\n")

        if domain:
            # Show specific domain
            if domain not in code_index.get("domains", {}):
                print(f"❌ Domain '{domain}' not found")
                return

            domain_data = code_index["domains"][domain]
            print(f"🏗️  Domain: {domain}")
            print(f"   Path: {domain_data.get('path', 'N/A')}")
            print(f"   Type: {domain_data.get('type', 'N/A')}")
            print(f"   Status: {domain_data.get('status', 'N/A')}")
            print(f"   Pages: {len(domain_data.get('pages', []))}")
            print(f"   Last Refactor: {domain_data.get('last_refactor', 'N/A')}")
        else:
            # Show all domains
            print(f"Total Domains: {len(code_index.get('domains', {}))}")
            print(f"Total Files: {code_index.get('total_files', 'N/A')}")
            print(f"Last Updated: {code_index.get('last_updated', 'N/A')}")
            print()

            print(f"Domains:")
            for domain_name, domain_data in code_index.get("domains", {}).items():
                status_emoji = "🟢" if domain_data.get("status") == "active" else "🟡" if domain_data.get("status") == "partially_complete" else "⚪"
                print(f"  {status_emoji} {domain_name}: {domain_data.get('status', 'N/A')}")

        print(f"\n{'='*70}\n")


class CodeFindCommand(BaseCommand):
    """
    Find code by domain/feature/component.

    Locates files and components based on various search criteria.

    Usage: bb5 code:find --component AdminDashboard
           bb5 code:find --domain admin --page overview
    """
    name = "code:find"
    description = "Find code locations"
    aliases = ["find", "locate"]

    def execute(self, args: Dict[str, Any]) -> int:
        component = args.get("component")
        domain = args.get("domain")
        page = args.get("page")

        # Load CODE-INDEX
        code_index_path = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal" / "CODE-INDEX.yaml"
        if not code_index_path.exists():
            code_index_path = Path.cwd() / ".project-memory" / "CODE-INDEX.yaml"

        if not code_index_path.exists():
            print("❌ CODE-INDEX.yaml not found")
            return 1

        with open(code_index_path) as f:
            code_index = yaml.safe_load(f)

        if component:
            return self._find_component(code_index, component)
        elif domain and page:
            return self._find_page(code_index, domain, page)
        else:
            print("❌ Specify --component or --domain with --page")
            return 1

    def _find_component(self, code_index: Dict, component_name: str) -> int:
        """Find component by name"""
        components = code_index.get("components", {})

        if component_name in components:
            comp = components[component_name]
            print(f"\n📦 Component: {component_name}")
            print(f"   Path: {comp.get('path', 'N/A')}")
            if comp.get("domain"):
                print(f"   Domain: {comp.get('domain', 'N/A')}")
            if comp.get("used_by"):
                print(f"   Used by: {', '.join(comp.get('used_by', []))}")
            if comp.get("depends_on"):
                print(f"   Depends on: {', '.join(comp.get('depends_on', []))}")
            print()
            return 0
        else:
            print(f"❌ Component '{component_name}' not found")
            return 1

    def _find_page(self, code_index: Dict, domain: str, page: str) -> int:
        """Find page by domain and page id"""
        domains = code_index.get("domains", {})

        if domain not in domains:
            print(f"❌ Domain '{domain}' not found")
            return 1

        for p in domains[domain].get("pages", []):
            if p.get("id") == page:
                print(f"\n📄 Page: {p.get('id')}")
                print(f"   Path: {p.get('path', 'N/A')}")
                print(f"   Components: {p.get('components', 'N/A')}")
                print(f"   Status: {p.get('status', 'N/A')}")
                if p.get("files"):
                    print(f"   Files:")
                    for f in p.get("files", []):
                        print(f"     - {f}")
                print()
                return 0

        print(f"❌ Page '{page}' not found in domain '{domain}'")
        return 1


class DomainListCommand(BaseCommand):
    """List all domains in the project."""
    name = "domain:list"
    description = "List all domains"
    aliases = ["domains", "list:domains"]

    def execute(self, args: Dict[str, Any]) -> int:
        code_index_path = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal" / "CODE-INDEX.yaml"
        if not code_index_path.exists():
            code_index_path = Path.cwd() / ".project-memory" / "CODE-INDEX.yaml"

        if not code_index_path.exists():
            print("❌ CODE-INDEX.yaml not found")
            return 1

        with open(code_index_path) as f:
            code_index = yaml.safe_load(f)

        print(f"\n📁 Domains:\n")
        for domain_name, domain_data in code_index.get("domains", {}).items():
            status = domain_data.get("status", "unknown")
            emoji = "🟢" if status == "active" else "🟡" if status == "partially_complete" else "⚪"
            print(f"  {emoji} {domain_name}")
            print(f"     Path: {domain_data.get('path', 'N/A')}")
            print(f"     Type: {domain_data.get('type', 'N/A')}")
            print(f"     Pages: {len(domain_data.get('pages', []))}")
            print()

        return 0


class DomainInfoCommand(BaseCommand):
    """
    Show detailed information about a domain.

    Displays domain context, features, pages, components, and refactor history.

    Usage: bb5 domain:info <domain>
    """
    name = "domain:info"
    description = "Show domain details"
    aliases = ["domain:show", "domain:detail"]

    def execute(self, args: Dict[str, Any]) -> int:
        domain = args.get("domain")
        if not domain:
            raise CommandError("Missing domain argument", exit_code=2)

        # Load CODE-INDEX
        code_index_path = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal" / "CODE-INDEX.yaml"
        if not code_index_path.exists():
            code_index_path = Path.cwd() / ".project-memory" / "CODE-INDEX.yaml"

        if not code_index_path.exists():
            print("❌ CODE-INDEX.yaml not found")
            return 1

        with open(code_index_path) as f:
            code_index = yaml.safe_load(f)

        if domain not in code_index.get("domains", {}):
            print(f"❌ Domain '{domain}' not found")
            return 1

        self._display_domain_info(domain, code_index["domains"][domain], code_index)
        return 0

    def _display_domain_info(self, domain_name: str, domain_data: Dict, code_index: Dict) -> None:
        """Display detailed domain information"""
        print(f"\n{'='*70}")
        print(f"🏗️  Domain: {domain_name}")
        print(f"{'='*70}\n")

        print(f"Path: {domain_data.get('path', 'N/A')}")
        print(f"Type: {domain_data.get('type', 'N/A')}")
        print(f"Status: {domain_data.get('status', 'N/A')}")
        print(f"Last Refactor: {domain_data.get('last_refactor', 'N/A')}")

        print(f"\n📄 Pages:")
        for page in domain_data.get("pages", []):
            status_emoji = "✅" if page.get("status") == "complete" else "🔄" if page.get("status") == "in_progress" else "⏳"
            print(f"  {status_emoji} {page.get('id', 'N/A')}: {page.get('status', 'N/A')}")
            if page.get("task_id"):
                print(f"      Task: {page.get('task_id')}")

        # Load domain context if available
        memory_root = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal"
        if not memory_root.exists():
            memory_root = Path.cwd() / ".project-memory"

        context_file = memory_root / "context" / "domains" / domain_name / "DOMAIN-CONTEXT.md"
        if context_file.exists():
            print(f"\n📚 Domain Context:")
            with open(context_file) as f:
                content = f.read()
                if len(content) > 300:
                    print(f"{content[:300]}...")
                else:
                    print(content)

        print(f"\n{'='*70}\n")


class ContextListCommand(BaseCommand):
    """List all available context files."""
    name = "context:list"
    description = "List all available contexts"
    aliases = ["contexts", "list:contexts"]

    def execute(self, args: Dict[str, Any]) -> int:
        print(f"\n📚 Available Contexts:\n")

        # Project contexts
        docs_root = Path.cwd() / "blackbox5" / "docs"
        memory_root = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal"
        if not memory_root.exists():
            memory_root = Path.cwd() / ".project-memory"

        print("📖 Project Documentation:")
        project_files = [
            ("FIRST-PRINCIPLES", docs_root / "project" / "FIRST-PRINCIPLES.md"),
            ("USERS", docs_root / "project" / "USERS.md"),
            ("ROADMAP", docs_root / "project" / "ROADMAP.md"),
        ]
        for name, path in project_files:
            exists = "✅" if path.exists() else "❌"
            print(f"  {exists} {name}")

        print("\n🎯 Competitive Intelligence:")
        comp_files = [
            ("COMPETITORS", docs_root / "competitive" / "COMPETITORS.md"),
            ("FEATURE-COMPARISON", docs_root / "competitive" / "FEATURE-COMPARISON.md"),
        ]
        for name, path in comp_files:
            exists = "✅" if path.exists() else "❌"
            print(f"  {exists} {name}")

        print("\n🏗️  Domain Contexts:")
        domain_dir = memory_root / "context" / "domains"
        if domain_dir.exists():
            for domain in domain_dir.iterdir():
                if domain.is_dir():
                    context_file = domain / "DOMAIN-CONTEXT.md"
                    exists = "✅" if context_file.exists() else "⏳"
                    print(f"  {exists} {domain.name}")

        print(f"\n💡 Use 'bb5 context:show <name>' to view a specific context\n")
        return 0


class ContextShowCommand(BaseCommand):
    """
    Show a specific context file.

    Displays the full content of a context document.

    Usage: bb5 context:show FIRST-PRINCIPLES
           bb5 context:show COMPETITORS
           bb5 context:show domain:admin
    """
    name = "context:show"
    description = "Show a specific context"
    aliases = ["context:view", "context:get"]

    def execute(self, args: Dict[str, Any]) -> int:
        context_name = args.get("context")
        if not context_name:
            raise CommandError("Missing context argument", exit_code=2)

        # Determine context type
        if context_name.startswith("domain:"):
            return self._show_domain_context(context_name.split(":")[1])
        else:
            return self._show_project_context(context_name)

    def _show_domain_context(self, domain: str) -> int:
        """Show domain context"""
        memory_root = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal"
        if not memory_root.exists():
            memory_root = Path.cwd() / ".project-memory"

        context_file = memory_root / "context" / "domains" / domain / "DOMAIN-CONTEXT.md"

        if not context_file.exists():
            print(f"❌ Domain context not found: {domain}")
            return 1

        with open(context_file) as f:
            print(f.read())

        return 0

    def _show_project_context(self, context_name: str) -> int:
        """Show project context"""
        docs_root = Path.cwd() / "blackbox5" / "docs"

        # Map context names to files
        context_map = {
            "FIRST-PRINCIPLES": docs_root / "project" / "FIRST-PRINCIPLES.md",
            "USERS": docs_root / "project" / "USERS.md",
            "ROADMAP": docs_root / "project" / "ROADMAP.md",
            "COMPETITORS": docs_root / "competitive" / "COMPETITORS.md",
            "FEATURE-COMPARISON": docs_root / "competitive" / "FEATURE-COMPARISON.md",
        }

        if context_name not in context_map:
            print(f"❌ Unknown context: {context_name}")
            print(f"   Run 'bb5 context:list' to see available contexts")
            return 1

        context_file = context_map[context_name]

        if not context_file.exists():
            print(f"❌ Context file not found: {context_file}")
            return 1

        with open(context_file) as f:
            print(f.read())

        return 0


class ContextSearchCommand(BaseCommand):
    """
    Search across all context files.

    Searches for a query string in all available context documents.

    Usage: bb5 context:search "admin dashboard"
    """
    name = "context:search"
    description = "Search across all contexts"
    aliases = ["search:context", "find:context"]

    def execute(self, args: Dict[str, Any]) -> int:
        query = args.get("query", "").lower()
        if not query:
            raise CommandError("Missing query argument", exit_code=2)

        print(f"\n🔍 Searching for: '{query}'\n")

        docs_root = Path.cwd() / "blackbox5" / "docs"
        memory_root = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal"
        if not memory_root.exists():
            memory_root = Path.cwd() / ".project-memory"

        # Search paths
        search_paths = [
            ("Project Docs", docs_root / "project"),
            ("Competitive", docs_root / "competitive"),
            ("Domain Contexts", memory_root / "context" / "domains"),
        ]

        results_found = False

        for category, search_path in search_paths:
            if not search_path.exists():
                continue

            for md_file in search_path.rglob("*.md"):
                try:
                    with open(md_file) as f:
                        content = f.read()
                        if query in content.lower():
                            results_found = True
                            # Find matching lines
                            lines = content.split("\n")
                            matching_lines = []
                            for i, line in enumerate(lines, 1):
                                if query in line.lower():
                                    matching_lines.append((i, line.strip()))

                            print(f"📄 {md_file.relative_to(Path.cwd())}")
                            if matching_lines:
                                for line_num, line in matching_lines[:3]:  # Show first 3 matches
                                    print(f"   {line_num}: {line[:100]}")
                            print()
                except Exception:
                    pass

        if not results_found:
            print(f"❌ No results found for '{query}'")

        return 0


class GotoTaskCommand(BaseCommand):
    """
    Navigate to a task directory.

    Shows the path to a task's working directory.

    Usage: bb5 goto:task <task-id>
    """
    name = "goto:task"
    description = "Navigate to task directory"
    aliases = ["goto:task", "cd:task"]

    def execute(self, args: Dict[str, Any]) -> int:
        task_id = args.get("task_id")
        if not task_id:
            raise CommandError("Missing task_id argument", exit_code=2)

        memory_root = Path.cwd() / "blackbox5" / "memory" / "project-memory" / "siso-internal"
        if not memory_root.exists():
            memory_root = Path.cwd() / ".project-memory"

        # Check working, then completed
        for status in ["working", "completed"]:
            task_path = memory_root / "tasks" / status / task_id
            if task_path.exists():
                print(f"\n📁 Task: {task_id}")
                print(f"   Path: {task_path}")
                print(f"   Status: {status}")
                print()
                print(f"   To navigate:")
                print(f"   cd {task_path}")
                print()
                return 0

        print(f"❌ Task '{task_id}' not found")
        print(f"   Checked: {memory_root / 'tasks'}")
        return 1


class GotoCodeCommand(BaseCommand):
    """
    Navigate to code location.

    Shows the path to a code file or directory.

    Usage: bb5 goto:code <path>
    """
    name = "goto:code"
    description = "Navigate to code location"
    aliases = ["goto:code", "cd:code"]

    def execute(self, args: Dict[str, Any]) -> int:
        code_path = args.get("path")
        if not code_path:
            raise CommandError("Missing path argument", exit_code=2)

        # Resolve path
        full_path = Path.cwd() / "src" / code_path

        if not full_path.exists():
            print(f"❌ Path not found: {full_path}")
            return 1

        print(f"\n📁 Code Location")
        print(f"   Path: {full_path}")
        print(f"\n   To navigate:")
        print(f"   cd {full_path}")
        print()

        return 0


class GotoDomainCommand(BaseCommand):
    """
    Navigate to a domain directory.

    Shows the path to a domain in src/domains/.

    Usage: bb5 goto:domain <domain>
    """
    name = "goto:domain"
    description = "Navigate to domain directory"
    aliases = ["goto:domain", "cd:domain"]

    def execute(self, args: Dict[str, Any]) -> int:
        domain = args.get("domain")
        if not domain:
            raise CommandError("Missing domain argument", exit_code=2)

        domain_path = Path.cwd() / "src" / "domains" / domain

        if not domain_path.exists():
            print(f"❌ Domain not found: {domain_path}")
            return 1

        print(f"\n🏗️  Domain: {domain}")
        print(f"   Path: {domain_path}")
        print(f"\n   To navigate:")
        print(f"   cd {domain_path}")
        print()

        return 0


class GenerateCodeIndexCommand(BaseCommand):
    """
    Generate CODE-INDEX.yaml from the codebase.

    Scans src/domains/ and creates/updates the CODE-INDEX.yaml file
    with all domains, pages, components, and refactor history.

    Usage: bb5 generate:code-index
    """
    name = "generate:code-index"
    description = "Generate CODE-INDEX.yaml from codebase"
    aliases = ["generate:code-index", "index:code", "code:index"]

    def execute(self, args: Dict[str, Any]) -> int:
        import sys
        from pathlib import Path

        # Add engine to path
        engine_dir = Path.cwd() / "blackbox5" / "engine"
        if engine_dir.exists():
            sys.path.insert(0, str(engine_dir))

        try:
            from tools.data_tools.code_indexer import CodeIndexer

            print("\n🔍 Scanning codebase...")

            indexer = CodeIndexer(Path.cwd())
            indexer.generate()

            print("✅ CODE-INDEX.yaml generated successfully")
            return 0

        except ImportError as e:
            print(f"❌ Failed to import code_indexer: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error generating CODE-INDEX: {e}")
            return 1
